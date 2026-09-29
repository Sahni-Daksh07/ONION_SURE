"""
ONION_SURE — Phase 4 Backend API Comprehensive Test Suite
Tests:
- Authentication & JWT Token Lifecycle
- RBAC (Role-Based Access Control)
- Farmers & Procurement Centres (CRUD, Pagination, Filters)
- Lots (intake, validation, status)
- Inspections & Multipart File Uploads (Storage Abstraction)
- AI Observation Grading & Decision Traces
- Manual Review Overrides
- Reports & Public Cryptographic QR Verification
- Audit Trail Logging
- Offline Sync Idempotency
"""

import uuid
import io
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from onion_sure.backend.models.entities import Base, User, Role, UserRole
from onion_sure.backend.main import app
from onion_sure.backend.database import get_db
from onion_sure.backend.security import hash_password, create_access_token


@pytest.fixture(scope="module")
def api_test_engine(tmp_path_factory):
    """File-backed SQLite test engine configured with PRAGMA foreign_keys = ON."""
    db_file = tmp_path_factory.mktemp("db") / "test_backend_phase4.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
    Base.metadata.create_all(bind=engine)

    # Seed core roles
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with Session() as session:
        for r_name in ["ADMIN", "INSPECTOR", "OFFICER", "REVIEWER"]:
            if not session.query(Role).filter_by(name=r_name).first():
                session.add(Role(name=r_name, description=f"{r_name} Role"))
        session.commit()

    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(api_test_engine):
    """FastAPI TestClient with overridden get_db dependency."""
    SessionLocal = sessionmaker(bind=api_test_engine, expire_on_commit=False, future=True)

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(api_test_engine):
    """Creates an admin user and returns a signed access token."""
    SessionLocal = sessionmaker(bind=api_test_engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        admin_role = session.query(Role).filter_by(name="ADMIN").first()
        admin_user = User(
            email=f"admin_{uuid.uuid4().hex[:6]}@onionsure.gov.in",
            full_name="System Administrator",
            hashed_password=hash_password("admin_secret_123"),
            is_active=True,
            is_superuser=True,
        )
        session.add(admin_user)
        session.flush()
        session.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
        session.commit()
        return create_access_token(subject=admin_user.id, roles=["ADMIN"])


@pytest.fixture
def inspector_auth(api_test_engine):
    """Creates a regular inspector user and returns (user_id, token)."""
    SessionLocal = sessionmaker(bind=api_test_engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        insp_role = session.query(Role).filter_by(name="INSPECTOR").first()
        insp_user = User(
            email=f"inspector_{uuid.uuid4().hex[:6]}@onionsure.gov.in",
            full_name="Mandi Field Inspector",
            hashed_password=hash_password("insp_secret_123"),
            is_active=True,
        )
        session.add(insp_user)
        session.flush()
        session.add(UserRole(user_id=insp_user.id, role_id=insp_role.id))
        session.commit()
        token = create_access_token(subject=insp_user.id, roles=["INSPECTOR"])
        return insp_user.id, token


# ==============================================================================
# 1. AUTHENTICATION & RBAC TESTS
# ==============================================================================

def test_auth_registration_and_login_flow(client):
    """Test user registration, duplicate validation, login, and profile retrieval."""
    email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    reg_payload = {
        "email": email,
        "full_name": "Test Officer",
        "password": "Password123!",
        "role_names": ["INSPECTOR"],
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == email

    # Duplicate registration fails
    dup_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 400

    # Successful login
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data

    # Profile retrieval with Bearer token
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

    # Refresh token
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": token_data["refresh_token"]})
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()


def test_rbac_access_restrictions(client, inspector_auth, admin_token):
    """Test RBAC enforcement: inspector cannot access admin-only endpoints, admin can."""
    _, insp_token = inspector_auth
    insp_headers = {"Authorization": f"Bearer {insp_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Inspector attempts to list system users -> Forbidden (403)
    forbidden_res = client.get("/api/v1/users", headers=insp_headers)
    assert forbidden_res.status_code == 403

    # Admin lists system users -> OK (200)
    allowed_res = client.get("/api/v1/users", headers=admin_headers)
    assert allowed_res.status_code == 200
    assert "items" in allowed_res.json()


# ==============================================================================
# 2. FARMERS & PROCUREMENT CENTRES (PAGINATION & FILTERS)
# ==============================================================================

def test_procurement_centre_and_farmer_crud(client):
    """Test creating procurement centre and farmer with pagination and filtering."""
    # Create Centre
    pc_code = f"PC-TEST-{uuid.uuid4().hex[:4].upper()}"
    pc_res = client.post(
        "/api/v1/procurement-centres",
        json={"centre_code": pc_code, "name": "Lasalgaon Mandi", "district": "Nashik", "state": "Maharashtra"},
    )
    assert pc_res.status_code == 201
    centre_id = pc_res.json()["id"]

    # Filter Centre
    pc_list = client.get("/api/v1/procurement-centres?district=Nashik")
    assert pc_list.status_code == 200
    assert any(c["id"] == centre_id for c in pc_list.json())

    # Create Farmer
    f_code = f"FARM-{uuid.uuid4().hex[:6].upper()}"
    f_res = client.post(
        "/api/v1/farmers",
        json={
            "farmer_code": f_code,
            "name": "Balu Patil",
            "phone": "9822001122",
            "village": "Vinchur",
            "district": "Nashik",
            "state": "Maharashtra",
        },
    )
    assert f_res.status_code == 201
    farmer_id = f_res.json()["id"]

    # Update Farmer profile
    patch_res = client.patch(f"/api/v1/farmers/{farmer_id}", json={"phone": "9822998877"})
    assert patch_res.status_code == 200
    assert patch_res.json()["phone"] == "9822998877"

    # Paginated Farmers query
    paginated_farmers = client.get("/api/v1/farmers?page=1&page_size=10&district=Nashik")
    assert paginated_farmers.status_code == 200
    data = paginated_farmers.json()
    assert "items" in data
    assert data["page"] == 1


# ==============================================================================
# 3. LOTS, INSPECTIONS, AND IMAGE FILE UPLOADS
# ==============================================================================

def test_lot_intake_and_filtering(client):
    """Test Lot creation, filtering by farmer and status, and updating."""
    # 1. Dependencies
    f_res = client.post(
        "/api/v1/farmers",
        json={"farmer_code": f"FARM-{uuid.uuid4().hex[:6]}", "name": "Kisan Ram", "phone": "9100000000", "village": "A", "district": "Nashik", "state": "MH"},
    )
    farmer_id = f_res.json()["id"]

    pc_res = client.post(
        "/api/v1/procurement-centres",
        json={"centre_code": f"PC-{uuid.uuid4().hex[:4]}", "name": "Centre A", "district": "Nashik", "state": "MH"},
    )
    centre_id = pc_res.json()["id"]

    # 2. Create Lot
    lot_code = f"LOT-{uuid.uuid4().hex[:6].upper()}"
    lot_res = client.post(
        "/api/v1/lots",
        json={
            "lot_number": lot_code,
            "farmer_id": farmer_id,
            "procurement_centre_id": centre_id,
            "variety": "Red Onion",
            "quantity_quintals": 80.0,
            "bag_count": 160,
        },
    )
    assert lot_res.status_code == 201
    lot_id = lot_res.json()["id"]

    # 3. Filter Lots
    filter_res = client.get(f"/api/v1/lots?farmer_id={farmer_id}&status=REGISTERED")
    assert filter_res.status_code == 200
    lots = filter_res.json()
    assert any(l["id"] == lot_id for l in lots)


def test_inspection_multipart_image_upload_and_grading(client, inspector_auth):
    """Test full workflow: create inspection, upload multipart image file, grade observations, and finalize."""
    inspector_id, _ = inspector_auth

    # Prerequisites
    f_res = client.post(
        "/api/v1/farmers",
        json={"farmer_code": f"FARM-{uuid.uuid4().hex[:6]}", "name": "Kisan Sham", "phone": "9200000000", "village": "B", "district": "Pune", "state": "MH"},
    )
    farmer_id = f_res.json()["id"]

    pc_res = client.post(
        "/api/v1/procurement-centres",
        json={"centre_code": f"PC-{uuid.uuid4().hex[:4]}", "name": "Pune APMC", "district": "Pune", "state": "MH"},
    )
    centre_id = pc_res.json()["id"]

    lot_res = client.post(
        "/api/v1/lots",
        json={"lot_number": f"LOT-{uuid.uuid4().hex[:6]}", "farmer_id": farmer_id, "procurement_centre_id": centre_id, "quantity_quintals": 20.0},
    )
    lot_id = lot_res.json()["id"]

    # 1. Create Inspection
    insp_res = client.post(
        "/api/v1/inspections",
        json={"lot_id": lot_id, "inspector_id": inspector_id, "sample_size": 50},
    )
    assert insp_res.status_code == 201
    insp_id = insp_res.json()["id"]

    # 2. Upload Multipart Image File (Verified storage abstraction, no binary in DB)
    fake_jpeg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"onion_inspection_sample_bytes"
    upload_res = client.post(
        f"/api/v1/inspections/{insp_id}/upload-image",
        files={"file": ("onion_lot_photo.jpg", io.BytesIO(fake_jpeg_content), "image/jpeg")},
        data={"calibration_detected": "true", "pixels_per_mm": "5.2", "calibration_method": "ARUCO_4X4_50"},
    )
    assert upload_res.status_code == 201
    img_data = upload_res.json()
    image_id = img_data["id"]
    assert img_data["inspection_id"] == insp_id
    assert img_data["storage_key"].endswith(".jpg")
    assert len(img_data["sha256_hash"]) == 64

    # 3. Retrieve Inspection Images list
    images_list = client.get(f"/api/v1/inspections/{insp_id}/images")
    assert images_list.status_code == 200
    assert len(images_list.json()) == 1

    # 4. Feed CV observations into Deterministic Grading Engine
    grade_req = {
        "inspection_id": insp_id,
        "policy_version": "1.0.0",
        "model_version": "classifier-v1.0.0",
        "observations": [
            {
                "image_id": image_id,
                "onion_index": "onion_001",
                "bbox_x": 10.0,
                "bbox_y": 10.0,
                "bbox_w": 50.0,
                "bbox_h": 50.0,
                "detection_confidence": 0.95,
                "defect_class": "HEALTHY",
                "defect_confidence": 0.94,
                "diameter_mm": 55.0,
                "measurement_status": "measured",
                "pixels_per_mm": 5.2,
            },
            {
                "image_id": image_id,
                "onion_index": "onion_002",
                "bbox_x": 70.0,
                "bbox_y": 70.0,
                "bbox_w": 40.0,
                "bbox_h": 40.0,
                "detection_confidence": 0.91,
                "defect_class": "ROTTEN",
                "defect_confidence": 0.92,
                "diameter_mm": 48.0,
                "measurement_status": "measured",
                "pixels_per_mm": 5.2,
            },
        ],
    }
    grade_res = client.post(f"/api/v1/inspections/{insp_id}/grade", json=grade_req)
    assert grade_res.status_code == 200
    results = grade_res.json()
    assert len(results) == 2
    grades = {r["grade"] for r in results}
    assert "GRADE_A" in grades
    assert "REJECT" in grades

    # 5. Check Inspection State after grading
    insp_check = client.get(f"/api/v1/inspections/{insp_id}")
    assert insp_check.status_code == 200
    check_data = insp_check.json()
    assert check_data["total_onions_evaluated"] == 2
    assert check_data["grade_a_count"] == 1
    assert check_data["reject_count"] == 1

    # 6. Apply Manual Review Override
    rotten_result = next(r for r in results if r["grade"] == "REJECT")
    review_res = client.post(
        f"/api/v1/inspections/{insp_id}/manual-review",
        json={
            "grade_result_id": rotten_result["id"],
            "reviewer_id": inspector_id,
            "reviewed_grade": "URS",
            "reason": "Surface mud mistakenly classified as rot on visual inspection",
            "comments": "Reviewed by senior APMC inspector",
        },
    )
    assert review_res.status_code == 200
    assert review_res.json()["reviewed_grade"] == "URS"

    # 7. Finalize Inspection and Generate Verifiable Report
    final_res = client.post(f"/api/v1/inspections/{insp_id}/finalize", params={"actor_id": inspector_id})
    assert final_res.status_code == 200
    report_data = final_res.json()
    assert report_data["inspection_id"] == insp_id
    qr_hash = report_data["qr_verification_hash"]
    assert len(qr_hash) == 64

    # 8. Public QR Verification Endpoint
    verify_res = client.get(f"/api/v1/reports/verify/{qr_hash}")
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert verify_data["inspection_id"] == insp_id


# ==============================================================================
# 4. AUDIT LOGGING & OFFLINE SYNC IDEMPOTENCY
# ==============================================================================

def test_audit_logs_query(client, admin_token):
    """Test retrieving system audit trail (Admin only)."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    audit_res = client.get("/api/v1/audit-logs", headers=headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    # At least USER_REGISTERED, USER_LOGIN, LOT_REGISTERED etc. have been recorded
    assert len(logs) > 0


def test_offline_sync_idempotency(client):
    """Test offline sync batch upload and idempotency prevention of duplicate processing."""
    client_uuid = str(uuid.uuid4())
    sync_key_1 = str(uuid.uuid4())
    sync_key_2 = str(uuid.uuid4())

    batch_payload = {
        "client_id": client_uuid,
        "items": [
            {
                "client_id": client_uuid,
                "sync_key": sync_key_1,
                "entity_type": "Inspection",
                "entity_id": str(uuid.uuid4()),
                "payload": {"notes": "Captured in rural area offline"},
            },
            {
                "client_id": client_uuid,
                "sync_key": sync_key_2,
                "entity_type": "InspectionImage",
                "entity_id": str(uuid.uuid4()),
                "payload": {"filename": "img_offline.jpg"},
            },
        ],
    }

    # 1. First sync -> processed
    first_sync = client.post("/api/v1/sync/batch", json=batch_payload)
    assert first_sync.status_code == 200
    data = first_sync.json()
    assert data["processed_count"] == 2
    assert data["success_count"] == 2

    # 2. Resync with same sync_keys -> acknowledges without duplication
    resync = client.post("/api/v1/sync/batch", json=batch_payload)
    assert resync.status_code == 200
    resync_data = resync.json()
    assert resync_data["success_count"] == 2
    assert all(r["status"] == "SYNCED" for r in resync_data["results"])

    # 3. Check client sync status records
    status_res = client.get(f"/api/v1/sync/status/{client_uuid}")
    assert status_res.status_code == 200
    assert len(status_res.json()) == 2
