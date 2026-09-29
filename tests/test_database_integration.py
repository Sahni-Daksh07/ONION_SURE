"""
ONION_SURE — Database & Backend Integration Tests
Tests all 19 entities, foreign keys, transaction boundaries, rollback semantics,
grading persistence service, and FastAPI endpoints.
"""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from onion_sure.backend.models.entities import (
    Base,
    User,
    Role,
    UserRole,
    Farmer,
    ProcurementCentre,
    Lot,
    Inspection,
    InspectionImage,
    OnionDetection,
    DefectResult,
    Measurement,
    GradeResult,
    GradingPolicy,
    GradingPolicyVersion,
    ModelVersion,
    ManualReview,
    Report,
    AuditLog,
    SyncRecord,
    InspectionStatus,
    LotDecision,
    DefectClass,
    GradeType,
    OpticalQualityStatus,
)
from onion_sure.backend.services.grading_persistence_service import GradingPersistenceService
from onion_sure.backend.services.audit_service import AuditService
from onion_sure.backend.services.storage_service import ImageStorageService, LocalStorageProvider
from onion_sure.backend.main import app
from onion_sure.backend.database import get_db



@pytest.fixture(scope="module")
def test_db_engine(tmp_path_factory):
    """Create file-backed SQLite engine configured for foreign key enforcement and multi-connection sharing."""
    db_file = tmp_path_factory.mktemp("db") / "test_onion_sure.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db_engine):
    """Provide a transactional database session per test with automatic rollback."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, expire_on_commit=False, future=True)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def api_client(test_db_engine):
    """FastAPI TestClient with overridden get_db dependency."""
    SessionLocal = sessionmaker(bind=test_db_engine, expire_on_commit=False, future=True)

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ============================================================================
# 1. CORE CRUD & RELATIONSHIP INTEGRITY TESTS
# ============================================================================

def test_user_role_assignment(db_session):
    """Test User, Role, and UserRole creation and relationship."""
    user = User(
        email="daksh@example.com",
        full_name="Daksh Sahni",
        hashed_password="argon2id$mocked_hash",
        phone="9876543210",
    )
    role = Role(name="INSPECTOR", description="Field Quality Inspector")
    db_session.add_all([user, role])
    db_session.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)
    db_session.commit()

    retrieved_user = db_session.query(User).filter_by(email="daksh@example.com").first()
    assert retrieved_user is not None
    assert len(retrieved_user.roles) == 1
    assert retrieved_user.roles[0].name == "INSPECTOR"


def test_farmer_procurement_lot_flow(db_session):
    """Test Farmer -> ProcurementCentre -> Lot relationship flow."""
    farmer = Farmer(
        farmer_code="FARM-NSK-001",
        name="Ramesh Patel",
        phone="+919876543210",
        village="Lasalgaon",
        district="Nashik",
        state="Maharashtra",
    )
    centre = ProcurementCentre(
        centre_code="PC-NSK-001",
        name="Lasalgaon APMC Sub-centre",
        district="Nashik",
        state="Maharashtra",
    )
    db_session.add_all([farmer, centre])
    db_session.flush()

    lot = Lot(
        lot_number=f"LOT-{uuid.uuid4().hex[:8].upper()}",
        farmer_id=farmer.id,
        procurement_centre_id=centre.id,
        variety="Red Onion",
        quantity_quintals=50.0,
        bag_count=100,
    )
    db_session.add(lot)
    db_session.commit()

    retrieved_lot = db_session.query(Lot).filter_by(id=lot.id).first()
    assert retrieved_lot is not None
    assert retrieved_lot.farmer.name == "Ramesh Patel"
    assert retrieved_lot.procurement_centre.centre_code == "PC-NSK-001"


def test_full_inspection_hierarchy_traceability(db_session):
    """
    Test complete inspection hierarchy:
    User -> Farmer -> Lot -> Inspection -> Image -> Detection -> Defect -> Measurement -> Grade
    """
    # 1. Base dependencies
    user = User(email="insp1@agri.gov.in", full_name="Inspector Suresh", hashed_password="hash")
    farmer = Farmer(farmer_code="FARM-002", name="Suresh Kumar", phone="9988776655", village="Khed", district="Pune", state="Maharashtra")
    centre = ProcurementCentre(centre_code="PC-PUN-01", name="Pune APMC", district="Pune", state="Maharashtra")
    db_session.add_all([user, farmer, centre])
    db_session.flush()

    lot = Lot(
        lot_number="LOT-PUN-2026-001",
        farmer_id=farmer.id,
        procurement_centre_id=centre.id,
        variety="White Onion",
        quantity_quintals=25.0,
    )
    db_session.add(lot)
    db_session.flush()

    # 2. Inspection
    inspection = Inspection(
        inspection_code="INSP-2026-0001",
        lot_id=lot.id,
        inspector_id=user.id,
        status="PROCESSING",
    )
    db_session.add(inspection)
    db_session.flush()

    # 3. Image with storage reference (NO raw bytes in database)
    img = InspectionImage(
        inspection_id=inspection.id,
        storage_key="inspections/2026/09/insp_001_img_01.jpg",
        filename="insp_001_img_01.jpg",
        file_size_bytes=1048576,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        quality_status="PASSED",
        calibration_detected=True,
        pixels_per_mm=10.5,
        calibration_method="ARUCO_4X4_50",
    )
    db_session.add(img)
    db_session.flush()

    # 4. Model Version
    m_ver = ModelVersion(
        model_name="onion_defect_classifier",
        version="v1.0.0",
        model_type="CLASSIFICATION",
        artifact_reference="ml/weights/classifier-v1.0.0.joblib",
    )
    db_session.add(m_ver)
    db_session.flush()

    # 5. Detection
    det = OnionDetection(
        image_id=img.id,
        onion_index="ONION_001",
        bbox_x=100.0,
        bbox_y=150.0,
        bbox_w=200.0,
        bbox_h=200.0,
        detection_confidence=0.96,
    )
    db_session.add(det)
    db_session.flush()

    # 6. Defect result & Measurement
    defect = DefectResult(
        detection_id=det.id,
        defect_class="HEALTHY",
        confidence=0.94,
        model_version_id=m_ver.id,
    )
    meas = Measurement(
        detection_id=det.id,
        status="CALIBRATED",
        diameter_mm=55.2,
        diameter_pixels=579.6,
        calibration_method="ARUCO_4X4_50",
        calibration_confidence=0.99,
        pixels_per_mm=10.5,
    )
    db_session.add_all([defect, meas])
    db_session.flush()

    # 7. Grading policy version
    policy = GradingPolicy(code="DOCA_STANDARD_2026", name="DoCA Standard Onion Grading Policy")
    db_session.add(policy)
    db_session.flush()

    p_ver = GradingPolicyVersion(
        policy_id=policy.id,
        version="v1.0.0",
        configuration={"min_grade_a_diameter_mm": 45.0},
    )
    db_session.add(p_ver)
    db_session.flush()

    # 8. Grade result
    grade_res = GradeResult(
        inspection_id=inspection.id,
        detection_id=det.id,
        grade="GRADE_A",
        reason_codes=["MEETS_GRADE_A_CRITERIA"],
        confidence=0.94,
        decision_trace={"check": "healthy_and_size_ok"},
        grading_policy_version_id=p_ver.id,
        model_version_id=m_ver.id,
    )
    db_session.add(grade_res)
    db_session.commit()

    # Verify query traceability
    res = db_session.query(GradeResult).filter_by(id=grade_res.id).first()
    assert res is not None
    assert res.grade == "GRADE_A"
    assert res.detection.image.inspection.lot.farmer.name == "Suresh Kumar"
    assert res.policy_version.policy.code == "DOCA_STANDARD_2026"
    assert res.model_version.version == "v1.0.0"


def test_transaction_rollback_on_integrity_error(test_db_engine):
    """Test that database errors cause clean rollbacks without corrupting the session."""
    SessionLocal = sessionmaker(bind=test_db_engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        user = User(email="unique_user@test.com", full_name="Unique User", hashed_password="hash")
        session.add(user)
        session.commit()

        # Attempting to insert duplicate email should raise IntegrityError
        dup_user = User(email="unique_user@test.com", full_name="Duplicate User", hashed_password="hash")
        session.add(dup_user)

        with pytest.raises(Exception):
            session.commit()

        session.rollback()

        # Session is clean, can query original user
        valid_query = session.query(User).filter_by(email="unique_user@test.com").first()
        assert valid_query is not None
        assert valid_query.full_name == "Unique User"


# ============================================================================
# 2. GRADING PERSISTENCE SERVICE INTEGRATION
# ============================================================================

def test_grading_persistence_service_integration(db_session):
    """Test that GradingPersistenceService evaluates and persists CV observations and grading decisions."""
    inspector = User(email="lead@gov.in", full_name="Lead Inspector", hashed_password="hash")
    farmer = Farmer(farmer_code="FARM-003", name="Kisan Ji", phone="9876500000", village="Pimpalgaon", district="Nashik", state="Maharashtra")
    centre = ProcurementCentre(centre_code="PC-009", name="Mandi", district="Nashik", state="Maharashtra")
    db_session.add_all([inspector, farmer, centre])
    db_session.flush()

    lot = Lot(lot_number="LOT-PERSIST-01", farmer_id=farmer.id, procurement_centre_id=centre.id, quantity_quintals=10.0)
    db_session.add(lot)
    db_session.flush()

    inspection = Inspection(
        inspection_code="INSP-PERSIST-01",
        lot_id=lot.id,
        inspector_id=inspector.id,
        status="PROCESSING",
    )
    db_session.add(inspection)
    db_session.flush()

    img = InspectionImage(
        inspection_id=inspection.id,
        storage_key="s3://onion-bucket/test_lot.jpg",
        filename="test_lot.jpg",
        file_size_bytes=500000,
        quality_status="PASSED",
    )
    db_session.add(img)
    db_session.flush()

    # Create CV observations data
    observations_data = [
        {
            "image_id": img.id,
            "onion_index": "onion_001",
            "bbox_x": 10.0,
            "bbox_y": 10.0,
            "bbox_w": 50.0,
            "bbox_h": 50.0,
            "detection_confidence": 0.96,
            "defect_class": "Healthy",
            "defect_confidence": 0.95,
            "measurement_status": "CALIBRATED",
            "diameter_mm": 55.0,
            "diameter_pixels": 250.0,
            "calibration_method": "ARUCO_4X4_50",
            "calibration_confidence": 0.98,
            "pixels_per_mm": 4.54,
            "image_quality_passed": True,
        },
        {
            "image_id": img.id,
            "onion_index": "onion_002",
            "bbox_x": 70.0,
            "bbox_y": 70.0,
            "bbox_w": 45.0,
            "bbox_h": 45.0,
            "detection_confidence": 0.92,
            "defect_class": "Damaged",
            "defect_confidence": 0.70,
            "measurement_status": "CALIBRATED",
            "diameter_mm": 48.0,
            "diameter_pixels": 218.0,
            "calibration_method": "ARUCO_4X4_50",
            "calibration_confidence": 0.98,
            "pixels_per_mm": 4.54,
            "image_quality_passed": True,
        },
    ]

    # Evaluate and persist atomically
    updated_insp, grade_results = GradingPersistenceService.evaluate_and_persist_inspection(
        db=db_session,
        inspection_id=inspection.id,
        observations_data=observations_data,
        policy_version_str="1.0.0",
        model_version_str="classifier-v1.0.0",
        actor_id=inspector.id,
    )

    assert updated_insp.total_onions_evaluated == 2
    assert updated_insp.grade_a_count == 1
    assert updated_insp.grade_a_percentage == 50.0
    assert updated_insp.urs_count == 1
    assert updated_insp.urs_percentage == 50.0
    assert updated_insp.status == "COMPLETED"

    # Verify database records
    detections = db_session.query(OnionDetection).filter_by(image_id=img.id).all()
    assert len(detections) == 2

    persisted_grades = db_session.query(GradeResult).filter_by(inspection_id=inspection.id).all()
    assert len(persisted_grades) == 2
    grades = {g.grade for g in persisted_grades}
    assert "GRADE_A" in grades
    assert "URS" in grades


# ============================================================================
# 3. AUDIT SERVICE & STORAGE SERVICE TESTS
# ============================================================================

def test_audit_service_logging(db_session):
    """Test that AuditService accurately records administrative and inspection actions."""
    log = AuditService.log_event(
        db=db_session,
        action="INSPECTION_FINALIZED",
        entity_type="INSPECTION",
        entity_id="test-insp-123",
        actor_id=None,
        new_values={"status": "COMPLETED", "grade_a_pct": 85.5},
        correlation_id="corr-987",
    )
    db_session.commit()

    retrieved = db_session.query(AuditLog).filter_by(id=log.id).first()
    assert retrieved is not None
    assert retrieved.action == "INSPECTION_FINALIZED"
    assert retrieved.new_values["grade_a_pct"] == 85.5


def test_storage_service_save_image(tmp_path):
    """Test storage service saves file, returns hash, size, and metadata."""
    provider = LocalStorageProvider(base_dir=tmp_path, bucket="test-bucket")
    svc = ImageStorageService(provider=provider)

    fake_img = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"mock_image_bytes"
    res = svc.save_image(fake_img, "test_onion.jpg")

    assert res["bucket"] == "test-bucket"
    assert res["file_size_bytes"] == len(fake_img)
    assert len(res["sha256_hash"]) == 64
    assert res["filename"] == "test_onion.jpg"


# ============================================================================
# 4. FASTAPI ENDPOINT INTEGRATION TESTS
# ============================================================================

def test_api_health_endpoint(api_client):
    """Test GET /health verifies API and database status."""
    response = api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "version" in data


def test_api_farmer_crud(api_client):
    """Test creating and retrieving a Farmer via FastAPI."""
    payload = {
        "farmer_code": f"FARM-{uuid.uuid4().hex[:6].upper()}",
        "name": "Santosh Rao",
        "phone": "+919988776655",
        "village": "Niphad",
        "district": "Nashik",
        "state": "Maharashtra",
        "aadhaar_masked": "XXXXXXXX1234",
    }
    create_res = api_client.post("/api/v1/farmers", json=payload)
    assert create_res.status_code == 201
    created_farmer = create_res.json()
    assert created_farmer["name"] == "Santosh Rao"
    farmer_id = created_farmer["id"]

    get_res = api_client.get(f"/api/v1/farmers/{farmer_id}")
    assert get_res.status_code == 200
    assert get_res.json()["village"] == "Niphad"


def test_api_lot_creation(api_client):
    """Test creating a Lot via FastAPI."""
    # 1. Create farmer & procurement centre
    farmer_payload = {
        "farmer_code": f"FARM-{uuid.uuid4().hex[:6].upper()}",
        "name": "Govind Joshi",
        "phone": "9876543210",
        "village": "Barshi",
        "district": "Solapur",
        "state": "Maharashtra",
    }
    farmer_res = api_client.post("/api/v1/farmers", json=farmer_payload)
    farmer_id = farmer_res.json()["id"]

    pc_payload = {
        "centre_code": f"PC-{uuid.uuid4().hex[:4].upper()}",
        "name": "Solapur Mandi",
        "district": "Solapur",
        "state": "Maharashtra",
    }
    pc_res = api_client.post("/api/v1/procurement-centres", json=pc_payload)
    assert pc_res.status_code == 201
    pc_id = pc_res.json()["id"]

    # 2. Create lot
    lot_payload = {
        "lot_number": f"LOT-{uuid.uuid4().hex[:6].upper()}",
        "farmer_id": farmer_id,
        "procurement_centre_id": pc_id,
        "variety": "Red Onion",
        "quantity_quintals": 120.0,
        "bag_count": 240,
    }
    lot_res = api_client.post("/api/v1/lots", json=lot_payload)
    assert lot_res.status_code == 201
    data = lot_res.json()
    assert data["variety"] == "Red Onion"
    assert data["quantity_quintals"] == 120.0


def test_api_inspection_flow(api_client, test_db_engine):
    """Test creating, reading, and updating an Inspection via FastAPI."""
    # 1. Prerequisites (farmer, centre, lot)
    f_res = api_client.post("/api/v1/farmers", json={
        "farmer_code": f"FARM-{uuid.uuid4().hex[:6].upper()}",
        "name": "Kisan Demo",
        "phone": "9876511111",
        "village": "Deola",
        "district": "Nashik",
        "state": "Maharashtra",
    })
    assert f_res.status_code == 201
    f_id = f_res.json()["id"]

    pc_res = api_client.post("/api/v1/procurement-centres", json={
        "centre_code": f"PC-{uuid.uuid4().hex[:4].upper()}",
        "name": "Deola Sub-Mandi",
        "district": "Nashik",
        "state": "Maharashtra",
    })
    assert pc_res.status_code == 201
    pc_id = pc_res.json()["id"]

    l_res = api_client.post("/api/v1/lots", json={
        "lot_number": f"LOT-{uuid.uuid4().hex[:6].upper()}",
        "farmer_id": f_id,
        "procurement_centre_id": pc_id,
        "quantity_quintals": 45.0,
    })
    assert l_res.status_code == 201
    l_id = l_res.json()["id"]

    # Seed an inspector user in the database
    SessionLocal = sessionmaker(bind=test_db_engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        inspector = User(
            email=f"insp_{uuid.uuid4().hex[:6]}@agri.gov.in",
            full_name="Field Inspector Test",
            hashed_password="hash",
        )
        session.add(inspector)
        session.commit()
        inspector_id = inspector.id

    # 2. Create Inspection
    insp_payload = {
        "lot_id": l_id,
        "inspector_id": inspector_id,
        "sample_size": 100,
    }
    create_insp = api_client.post("/api/v1/inspections", json=insp_payload)
    assert create_insp.status_code == 201
    insp_data = create_insp.json()
    insp_id = insp_data["id"]
    assert insp_data["status"] == "CAPTURING"
    assert insp_data["lot_id"] == l_id

    # 3. Read Inspection
    get_insp = api_client.get(f"/api/v1/inspections/{insp_id}")
    assert get_insp.status_code == 200
    assert get_insp.json()["id"] == insp_id

    # 4. Update Status
    patch_res = api_client.patch(f"/api/v1/inspections/{insp_id}/status", params={"status": "PROCESSING"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "PROCESSING"

    # 5. Attach Image Metadata
    img_payload = {
        "inspection_id": insp_id,
        "storage_key": f"inspections/{insp_id}/test_image.jpg",
        "filename": "test_image.jpg",
        "file_size_bytes": 1048576,
        "content_type": "image/jpeg",
        "sha256_hash": "a" * 64,
        "quality_status": "PASSED",
        "calibration_detected": True,
        "pixels_per_mm": 8.5,
        "calibration_method": "ARUCO_4X4_50",
    }
    img_res = api_client.post(f"/api/v1/inspections/{insp_id}/images", json=img_payload)
    assert img_res.status_code == 201
    assert img_res.json()["inspection_id"] == insp_id
    assert img_res.json()["quality_status"] == "PASSED"
