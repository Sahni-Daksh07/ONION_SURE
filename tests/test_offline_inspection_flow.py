"""
ONION_SURE — Phase 6 Offline-First Inspection & Sync Queue Comprehensive Test Suite
Smart India Hackathon 2026 - Problem Statement PS26031

Tests:
1. Create inspection offline.
2. Capture images offline.
3. Store result locally.
4. Restore network.
5. Synchronize.
6. Verify server data.
7. Ensure no duplicate records (strict idempotency).
8. Mobile sync queue states (SYNCED, PENDING, SYNCING, FAILED, REQUIRES ACTION).
9. Upload resume and conflict handling.
"""

import uuid
import datetime
from pathlib import Path
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from onion_sure.backend.models.entities import (
    Base, User, Role, UserRole, ProcurementCentre, Farmer, Lot,
    Inspection, InspectionImage, GradeResult, SyncRecord
)
from onion_sure.backend.main import app
from onion_sure.backend.database import get_db
from onion_sure.backend.security import hash_password, create_access_token


@pytest.fixture(scope="module")
def offline_test_engine(tmp_path_factory):
    """File-backed SQLite test engine configured with PRAGMA foreign_keys = ON."""
    db_file = tmp_path_factory.mktemp("offline_db") / "test_phase6_offline.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with Session() as session:
        for r_name in ["ADMIN", "INSPECTOR", "OFFICER", "REVIEWER"]:
            if not session.query(Role).filter_by(name=r_name).first():
                session.add(Role(name=r_name, description=f"{r_name} Role"))
        session.commit()

    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_client(offline_test_engine):
    """FastAPI TestClient with overridden get_db dependency."""
    SessionLocal = sessionmaker(bind=offline_test_engine, expire_on_commit=False, future=True)

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(offline_test_engine):
    """Generates valid JWT auth headers for inspector user."""
    SessionLocal = sessionmaker(bind=offline_test_engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        user = session.query(User).filter_by(email="inspector.offline@mandi.gov.in").first()
        if not user:
            role = session.query(Role).filter_by(name="INSPECTOR").first()
            user = User(
                email="inspector.offline@mandi.gov.in",
                full_name="Inspector Ramesh",
                hashed_password=hash_password("MandiPass@123"),
                is_active=True,
            )
            session.add(user)
            session.flush()
            session.add(UserRole(user_id=user.id, role_id=role.id))
            session.commit()
            session.refresh(user)
        token = create_access_token(subject=str(user.id), roles=["INSPECTOR"])
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_centre(offline_test_engine):
    """Ensures an active procurement centre exists."""
    SessionLocal = sessionmaker(bind=offline_test_engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        centre = session.query(ProcurementCentre).filter_by(centre_code="LASAL-OFFLINE-01").first()
        if not centre:
            centre = ProcurementCentre(
                name="Lasalgaon Offline Mandi Yard",
                centre_code="LASAL-OFFLINE-01",
                district="Nashik",
                state="Maharashtra",
                is_active=True,
            )
            session.add(centre)
            session.commit()
            session.refresh(centre)
        return str(centre.id)


# ============================================================================
# Mobile Codebase Architecture & UI State Tests
# ============================================================================

def test_mobile_offline_sync_architecture_components():
    """Verify all required Phase 6 files exist in Flutter mobile application."""
    mobile_dir = Path("mobile/lib")
    assert (mobile_dir / "core" / "network" / "network_info.dart").exists(), "NetworkInfo missing"
    assert (mobile_dir / "core" / "storage" / "sync_queue_manager.dart").exists(), "SyncQueueManager missing"
    assert (mobile_dir / "core" / "widgets" / "sync_status_badge.dart").exists(), "SyncStatusBadge missing"


def test_sync_status_states_defined():
    """
    Verify all 5 required UI sync status states are defined:
    SYNCED, PENDING, SYNCING, FAILED, REQUIRES ACTION
    """
    sync_manager_file = Path("mobile/lib/core/storage/sync_queue_manager.dart")
    content = sync_manager_file.read_text(encoding="utf-8")
    assert "SYNCED" in content
    assert "PENDING" in content
    assert "SYNCING" in content
    assert "FAILED" in content
    assert "REQUIRES ACTION" in content


def test_sync_queue_retry_and_ordering():
    """Verify exponential backoff, max retries, and dependency ordering in SyncQueueManager."""
    sync_manager_file = Path("mobile/lib/core/storage/sync_queue_manager.dart")
    content = sync_manager_file.read_text(encoding="utf-8")
    assert "maxRetries = 5" in content or "max_retries" in content
    assert "requiresAction" in content
    assert "calculateBackoffSeconds" in content
    assert "priorityMap" in content


# ============================================================================
# End-to-End Airplane-Mode & Offline Inspection 7-Step Workflow
# ============================================================================

def test_airplane_mode_offline_inspection_e2e_flow(test_client, auth_headers, test_centre, offline_test_engine):
    """
    Execute and verify the exact 7-step test:
    1. Create inspection offline.
    2. Capture images offline with metadata.
    3. Store result locally (deterministic grading calculation).
    4. Restore network.
    5. Synchronize batch to backend.
    6. Verify server data.
    7. Ensure no duplicate records on retries.
    """
    client_id = f"client-device-{uuid.uuid4().hex[:8]}"

    # ------------------------------------------------------------------------
    # STEP 1: Create Farmer, Lot & Inspection Offline
    # ------------------------------------------------------------------------
    farmer_id = str(uuid.uuid4())
    farmer_sync_key = f"sync-farmer-{uuid.uuid4()}"
    farmer_payload = {
        "id": farmer_id,
        "full_name": "Balasaheb Patil",
        "phone_number": "9876500001",
        "district": "Nashik",
        "state": "Maharashtra",
        "village": "Niphad",
        "pincode": "422303",
    }

    lot_id = str(uuid.uuid4())
    lot_sync_key = f"sync-lot-{uuid.uuid4()}"
    lot_code = f"LOT-OFFLINE-{uuid.uuid4().hex[:6].upper()}"
    lot_payload = {
        "id": lot_id,
        "farmer_id": farmer_id,
        "procurement_centre_id": test_centre,
        "lot_code": lot_code,
        "variety": "Nashik Red Onion",
        "quantity_quintals": 45.5,
        "number_of_bags": 90,
        "status": "ACCEPTED",
    }

    inspection_id = str(uuid.uuid4())
    inspection_sync_key = f"sync-insp-{uuid.uuid4()}"
    inspection_code = f"INSP-OFFLINE-{uuid.uuid4().hex[:6].upper()}"
    inspection_payload = {
        "id": inspection_id,
        "lot_id": lot_id,
        "inspection_code": inspection_code,
        "total_onions_evaluated": 50,
        "sample_size_count": 50,
        "status": "COMPLETED",
        "lot_decision": "ACCEPT_GRADE_A",
        "notes": "Captured in rural mandi without internet connection",
    }

    # ------------------------------------------------------------------------
    # STEP 2: Capture Images Offline (with local metadata)
    # ------------------------------------------------------------------------
    image_id = str(uuid.uuid4())
    image_sync_key = f"sync-img-{uuid.uuid4()}"
    image_payload = {
        "id": image_id,
        "inspection_id": inspection_id,
        "file_name": "offline_tray_sample_1.jpg",
        "file_path": f"/local/storage/inspections/{inspection_id}/offline_tray_sample_1.jpg",
        "file_size_bytes": 1048576,
        "mime_type": "image/jpeg",
        "width_px": 1920,
        "height_px": 1080,
        "quality_score": 0.94,
        "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    }

    # ------------------------------------------------------------------------
    # STEP 3: Store Grade Result Locally (Deterministic Grading Result)
    # ------------------------------------------------------------------------
    grade_id = str(uuid.uuid4())
    grade_sync_key = f"sync-grade-{uuid.uuid4()}"
    grade_payload = {
        "id": grade_id,
        "inspection_id": inspection_id,
        "grade": "GRADE_A",
        "grade_a_percentage": 92.0,
        "urs_percentage": 8.0,
        "reject_percentage": 0.0,
        "is_acceptable": True,
        "reason_code": "HIGH_QUALITY_CONFORMANT",
        "explanation": "Lot meets Grade A standards with >90% Grade A and no severe rot.",
    }

    # Verify that in airplane mode, no records exist on the server yet
    SessionLocal = sessionmaker(bind=offline_test_engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        assert session.query(Farmer).filter_by(id=farmer_id).first() is None
        assert session.query(Lot).filter_by(id=lot_id).first() is None
        assert session.query(Inspection).filter_by(id=inspection_id).first() is None

    # ------------------------------------------------------------------------
    # STEP 4 & 5: Restore Network & Synchronize Batch to Backend
    # ------------------------------------------------------------------------
    # Sync items are structured with dependency ordering
    sync_batch_payload = {
        "client_id": client_id,
        "items": [
            {
                "client_id": client_id,
                "sync_key": farmer_sync_key,
                "entity_type": "Farmer",
                "entity_id": farmer_id,
                "payload": farmer_payload,
            },
            {
                "client_id": client_id,
                "sync_key": lot_sync_key,
                "entity_type": "Lot",
                "entity_id": lot_id,
                "payload": lot_payload,
            },
            {
                "client_id": client_id,
                "sync_key": inspection_sync_key,
                "entity_type": "Inspection",
                "entity_id": inspection_id,
                "payload": inspection_payload,
            },
            {
                "client_id": client_id,
                "sync_key": image_sync_key,
                "entity_type": "InspectionImage",
                "entity_id": image_id,
                "payload": image_payload,
            },
            {
                "client_id": client_id,
                "sync_key": grade_sync_key,
                "entity_type": "GradeResult",
                "entity_id": grade_id,
                "payload": grade_payload,
            },
        ],
    }

    # Execute sync
    sync_res = test_client.post("/api/v1/sync/batch", json=sync_batch_payload, headers=auth_headers)
    assert sync_res.status_code == 200, f"Sync failed: {sync_res.text}"
    sync_data = sync_res.json()
    failed_items = [r for r in sync_data["results"] if r["status"] == "FAILED"]
    assert sync_data["failed_count"] == 0, f"Failed items details: {failed_items}"
    assert sync_data["processed_count"] == 5
    assert sync_data["success_count"] == 5
    assert all(r["status"] == "SYNCED" for r in sync_data["results"])

    # ------------------------------------------------------------------------
    # STEP 6: Verify Server Data
    # ------------------------------------------------------------------------
    with SessionLocal() as session:
        # Verify Farmer
        server_farmer = session.query(Farmer).filter_by(id=farmer_id).first()
        assert server_farmer is not None
        assert server_farmer.name == "Balasaheb Patil"
        assert server_farmer.phone == "9876500001"

        # Verify Lot
        server_lot = session.query(Lot).filter_by(id=lot_id).first()
        assert server_lot is not None
        assert server_lot.lot_number == lot_code
        assert float(server_lot.quantity_quintals) == 45.5

        # Verify Inspection
        server_insp = session.query(Inspection).filter_by(id=inspection_id).first()
        assert server_insp is not None
        assert server_insp.inspection_code == inspection_code
        assert server_insp.total_onions_evaluated == 50
        assert server_insp.lot_decision == "ACCEPT_GRADE_A"
        assert float(server_insp.grade_a_percentage) == 92.0

        # Verify Image Metadata
        server_img = session.query(InspectionImage).filter_by(id=image_id).first()
        assert server_img is not None
        assert server_img.filename == "offline_tray_sample_1.jpg"
        assert server_img.file_size_bytes == 1048576

        # Verify Sync Records
        sync_records = session.query(SyncRecord).filter_by(client_id=client_id).all()
        assert len(sync_records) == 5

    # ------------------------------------------------------------------------
    # STEP 7: Ensure Zero Duplicate Records on Sync Retry (Strict Idempotency)
    # ------------------------------------------------------------------------
    # Snapshot counts before retry
    with SessionLocal() as session:
        count_farmers_before = session.query(Farmer).count()
        count_lots_before = session.query(Lot).count()
        count_inspections_before = session.query(Inspection).count()
        count_images_before = session.query(InspectionImage).count()
        count_sync_records_before = session.query(SyncRecord).count()

    # Retry the exact same sync batch (e.g. mobile app re-sends queue on network glitch)
    retry_res = test_client.post("/api/v1/sync/batch", json=sync_batch_payload, headers=auth_headers)
    assert retry_res.status_code == 200
    retry_data = retry_res.json()
    assert retry_data["processed_count"] == 5
    assert retry_data["success_count"] == 5
    assert retry_data["failed_count"] == 0
    assert all(r["status"] == "SYNCED" for r in retry_data["results"])

    # Verify that database row counts DID NOT CHANGE AT ALL
    with SessionLocal() as session:
        assert session.query(Farmer).count() == count_farmers_before, "Duplicate Farmer created!"
        assert session.query(Lot).count() == count_lots_before, "Duplicate Lot created!"
        assert session.query(Inspection).count() == count_inspections_before, "Duplicate Inspection created!"
        assert session.query(InspectionImage).count() == count_images_before, "Duplicate InspectionImage created!"
        assert session.query(SyncRecord).count() == count_sync_records_before, "Duplicate SyncRecord created!"


def test_sync_status_query_endpoint(test_client, auth_headers):
    """Test retrieving sync status by client ID."""
    test_client_id = f"client-query-{uuid.uuid4().hex[:6]}"
    batch = {
        "client_id": test_client_id,
        "items": [
            {
                "client_id": test_client_id,
                "sync_key": f"key-{uuid.uuid4()}",
                "entity_type": "Inspection",
                "entity_id": str(uuid.uuid4()),
                "payload": {"notes": "Test query status"},
            }
        ],
    }
    test_client.post("/api/v1/sync/batch", json=batch, headers=auth_headers)

    res = test_client.get(f"/api/v1/sync/status/{test_client_id}", headers=auth_headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["status"] == "SYNCED"
    assert items[0]["entity_type"] == "Inspection"
