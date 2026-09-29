"""
ONION_SURE — Phase 7 Digital Quality Reporting & Verification Comprehensive Test Suite
Smart India Hackathon 2026 - Problem Statement PS26031

Tests:
1. Professional report generation for finalized inspection.
2. Report includes all required fields:
   - Report ID & Inspection ID
   - Lot ID & Farmer & Procurement Centre & Operator
   - Date/time & Sample size
   - Grade A %, URS %, Reject %
   - Defect distribution & Size distribution & Average diameter
   - Evidence images & AI model version & Grading policy version
   - Manual review history
3. PDF generation with ReportLab & download endpoint.
4. Unique verification ID generation.
5. QR code PNG generation encoding verification URL.
6. Public, read-only verification endpoint that does NOT expose sensitive personal information.
7. Verification by verification ID, QR hash, and rejection of invalid certificates.
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
    Inspection, InspectionImage, OnionDetection, DefectResult,
    Measurement, GradeResult, GradingPolicy, GradingPolicyVersion,
    ModelVersion, ManualReview, Report
)
from onion_sure.backend.main import app
from onion_sure.backend.database import get_db
from onion_sure.backend.security import hash_password, create_access_token
from onion_sure.backend.services.report_service import ReportService


@pytest.fixture(scope="module")
def report_test_engine(tmp_path_factory):
    """File-backed SQLite test engine configured with PRAGMA foreign_keys = ON."""
    db_file = tmp_path_factory.mktemp("report_db") / "test_phase7_reporting.db"
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
def test_client(report_test_engine):
    """FastAPI TestClient with overridden get_db dependency."""
    SessionLocal = sessionmaker(bind=report_test_engine, expire_on_commit=False, future=True)

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
def auth_headers(report_test_engine):
    """Generates valid JWT auth headers for inspector user."""
    SessionLocal = sessionmaker(bind=report_test_engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        user = session.query(User).filter_by(email="inspector.reporting@mandi.gov.in").first()
        if not user:
            role = session.query(Role).filter_by(name="INSPECTOR").first()
            user = User(
                email="inspector.reporting@mandi.gov.in",
                full_name="Inspector S. K. Shinde",
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
def full_inspection_setup(report_test_engine):
    """Sets up a complete inspection with farmer, centre, images, measurements, defects, and manual review."""
    uid = uuid.uuid4().hex[:6].upper()
    SessionLocal = sessionmaker(bind=report_test_engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        # 1. Procurement Centre
        centre = ProcurementCentre(
            name="Pimpalgaon Baswant APMC Market",
            centre_code=f"PIMP-{uid}",
            district="Nashik",
            state="Maharashtra",
            is_active=True,
        )
        session.add(centre)
        session.flush()

        # 2. Farmer (with sensitive PII to verify privacy protection)
        farmer = Farmer(
            name="Kisanrao Dnyaneshwar Bhor",
            farmer_code=f"FARM-MAH-{uid}",
            phone="9876543210",  # Sensitive phone
            village="Chandwad",
            district="Nashik",
            state="Maharashtra",
            aadhaar_masked="XXXX-XXXX-1234",  # Sensitive Aadhaar
        )
        session.add(farmer)
        session.flush()

        # 3. Lot
        lot = Lot(
            lot_number=f"LOT-2026-NASHIK-{uid}",
            farmer_id=farmer.id,
            procurement_centre_id=centre.id,
            variety="Garwa Red Onion",
            quantity_quintals=65.0,
            bag_count=130,
            status="INSPECTING",
        )
        session.add(lot)
        session.flush()

        # 4. Inspector & Reviewer Users
        insp_role = session.query(Role).filter_by(name="INSPECTOR").first()
        rev_role = session.query(Role).filter_by(name="REVIEWER").first()

        inspector = User(
            email=f"operator_{uid.lower()}@onionsure.gov.in",
            full_name="Operator Vitthal Gite",
            hashed_password=hash_password("Pass123!"),
            is_active=True,
        )
        session.add(inspector)
        session.flush()
        session.add(UserRole(user_id=inspector.id, role_id=insp_role.id))

        reviewer = User(
            email=f"reviewer_{uid.lower()}@onionsure.gov.in",
            full_name="Senior Reviewer Dr. A. Joshi",
            hashed_password=hash_password("Pass123!"),
            is_active=True,
        )
        session.add(reviewer)
        session.flush()
        session.add(UserRole(user_id=reviewer.id, role_id=rev_role.id))
        session.flush()

        # 5. Inspection
        inspection = Inspection(
            inspection_code=f"INSP-DOCA-2026-{uid}",
            lot_id=lot.id,
            inspector_id=inspector.id,
            sample_size=50,
            status="CAPTURING",
            total_onions_evaluated=50,
            grade_a_count=42,
            grade_a_percentage=84.0,
            urs_count=6,
            urs_percentage=12.0,
            reject_count=2,
            reject_percentage=4.0,
            manual_review_count=1,
            lot_decision="ACCEPT_GRADE_A",
            decision_reason="Conforming: Grade A exceeds 80%, critical rot below 2%.",
        )
        session.add(inspection)
        session.flush()

        # 6. Model Version & Policy Version (retrieve or create)
        model_ver = session.query(ModelVersion).filter_by(version="v2.1.0-resnet50").first()
        if not model_ver:
            model_ver = ModelVersion(
                model_name="onion_defect_classifier",
                version="v2.1.0-resnet50",
                model_type="classifier",
                artifact_reference="/models/classifier_v2.1.0.pt",
            )
            session.add(model_ver)
            session.flush()

        policy = session.query(GradingPolicy).filter_by(code="DOCA_STANDARD_2026").first()
        if not policy:
            policy = GradingPolicy(
                code="DOCA_STANDARD_2026",
                name="Department of Consumer Affairs Onion Standard",
                crop="Onion",
                is_active=True,
            )
            session.add(policy)
            session.flush()

        policy_ver = session.query(GradingPolicyVersion).filter_by(policy_id=policy.id, version="v1.2.0-mandi").first()
        if not policy_ver:
            policy_ver = GradingPolicyVersion(
                policy_id=policy.id,
                version="v1.2.0-mandi",
                configuration={"min_grade_a": 80.0, "max_reject": 5.0, "min_diameter_mm": 45.0},
            )
            session.add(policy_ver)
            session.flush()

        # 7. Evidence Images
        image1 = InspectionImage(
            inspection_id=inspection.id,
            storage_key="/storage/inspections/tray_top_view_01.jpg",
            filename="tray_top_view_01.jpg",
            content_type="image/jpeg",
            file_size_bytes=2048576,
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            quality_status="PASSED",
            blur_variance=210.5,
            mean_brightness=135.2,
            calibration_detected=True,
            pixels_per_mm=5.4,
            calibration_method="ARUCO_4X4_50",
        )
        session.add(image1)
        session.flush()

        # 8. Onion Detections, Measurements, Defect Results & Grade Results
        # Create a few representative onions:
        # Onion 1: Healthy, 55mm -> Grade A
        det1 = OnionDetection(image_id=image1.id, onion_index="onion_001", bbox_x=0.1, bbox_y=0.1, bbox_w=0.15, bbox_h=0.15, detection_confidence=0.96)
        session.add(det1)
        session.flush()
        session.add(DefectResult(detection_id=det1.id, defect_class="HEALTHY", confidence=0.96, model_version_id=model_ver.id))
        session.add(Measurement(detection_id=det1.id, status="measured", diameter_mm=55.0, diameter_pixels=297.0, pixels_per_mm=5.4))
        gr1 = GradeResult(
            inspection_id=inspection.id,
            detection_id=det1.id,
            grade="GRADE_A",
            confidence=0.96,
            reason_codes=["FULL_SIZE_HEALTHY"],
            decision_trace=[{"step": 1, "check": "healthy", "pass": True}],
            grading_policy_version_id=policy_ver.id,
            model_version_id=model_ver.id,
        )
        session.add(gr1)

        # Onion 2: Rotten, 50mm -> Reject
        det2 = OnionDetection(image_id=image1.id, onion_index="onion_002", bbox_x=0.3, bbox_y=0.1, bbox_w=0.15, bbox_h=0.15, detection_confidence=0.92)
        session.add(det2)
        session.flush()
        session.add(DefectResult(detection_id=det2.id, defect_class="ROTTEN", confidence=0.92, model_version_id=model_ver.id))
        session.add(Measurement(detection_id=det2.id, status="measured", diameter_mm=50.0, diameter_pixels=270.0, pixels_per_mm=5.4))
        gr2 = GradeResult(
            inspection_id=inspection.id,
            detection_id=det2.id,
            grade="REJECT",
            confidence=0.92,
            reason_codes=["CRITICAL_ROT_DETECTED"],
            decision_trace=[{"step": 1, "check": "rot", "pass": False}],
            grading_policy_version_id=policy_ver.id,
            model_version_id=model_ver.id,
        )
        session.add(gr2)

        # Onion 3: Sprouted, 48mm -> URS (Overridden from Reject to URS by manual review)
        det3 = OnionDetection(image_id=image1.id, onion_index="onion_003", bbox_x=0.5, bbox_y=0.1, bbox_w=0.15, bbox_h=0.15, detection_confidence=0.88)
        session.add(det3)
        session.flush()
        session.add(DefectResult(detection_id=det3.id, defect_class="SPROUTED", confidence=0.88, model_version_id=model_ver.id))
        session.add(Measurement(detection_id=det3.id, status="measured", diameter_mm=48.0, diameter_pixels=259.2, pixels_per_mm=5.4))
        gr3 = GradeResult(
            inspection_id=inspection.id,
            detection_id=det3.id,
            grade="URS",
            confidence=0.88,
            reason_codes=["MINOR_SPROUT_SURFACE_ONLY"],
            decision_trace=[{"step": 1, "check": "manual_review_override"}],
            grading_policy_version_id=policy_ver.id,
            model_version_id=model_ver.id,
        )
        session.add(gr3)
        session.flush()

        # 9. Manual Review Record
        review = ManualReview(
            inspection_id=inspection.id,
            grade_result_id=gr3.id,
            reviewer_id=reviewer.id,
            original_grade="REJECT",
            reviewed_grade="URS",
            reason="MINOR_SPROUTING",
            comments="Surface sprout negligible, interior bulb remains sound for immediate processing.",
            status="APPROVED",
        )
        session.add(review)
        session.commit()

        return {
            "inspection_id": inspection.id,
            "inspection_code": inspection.inspection_code,
            "farmer_phone": farmer.phone,
            "farmer_aadhaar": farmer.aadhaar_masked,
            "lot_number": lot.lot_number,
        }


# ============================================================================
# Phase 7 Comprehensive Tests
# ============================================================================

def test_report_service_aggregation_completeness(report_test_engine, full_inspection_setup):
    """
    Verify report service aggregates all mandatory PS26031 fields:
    - Report ID / Inspection ID / Lot ID / Farmer / Centre / Operator / Dates
    - Sample size / Grade A % / URS % / Reject %
    - Defect distribution / Size distribution / Average diameter
    - Evidence images / Model version / Policy version / Manual review history
    - Verification ID & QR URL
    """
    SessionLocal = sessionmaker(bind=report_test_engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        data = ReportService.aggregate_inspection_report_data(session, full_inspection_setup["inspection_id"])

        # Identifiers
        assert "REP-" in data["report_code"]
        assert data["inspection_id"] == full_inspection_setup["inspection_id"]
        assert data["lot_number"] == full_inspection_setup["lot_number"]
        assert data["verification_id"].startswith("VER-")
        assert "https://onionsure.doca.gov.in/verify/" in data["verification_url"]
        assert len(data["qr_verification_hash"]) == 64

        # Procurement & Farmer
        assert data["farmer_name"] == "Kisanrao Dnyaneshwar Bhor"
        assert "Pimpalgaon" in data["centre_name"]
        assert "Vitthal Gite" in data["operator_name"]

        # Quality Metrics
        assert data["sample_size"] == 50
        assert data["grade_a_percentage"] == 84.0
        assert data["urs_percentage"] == 12.0
        assert data["reject_percentage"] == 4.0
        assert data["lot_decision"] == "ACCEPT_GRADE_A"

        # Defect Distribution
        assert "HEALTHY" in data["defect_distribution"]
        assert "ROTTEN" in data["defect_distribution"]
        assert "SPROUTED" in data["defect_distribution"]

        # Sizing & Diameter
        assert "ACCEPTABLE_SIZE" in data["size_distribution"]
        assert data["average_diameter_mm"] is not None
        assert data["average_diameter_mm"] > 40.0

        # Model & Policy
        assert "v2.1.0-resnet50" in data["model_version"]
        assert "v1.2.0-mandi" in data["grading_policy_version"]

        # Evidence Images & Manual Reviews
        assert len(data["evidence_images"]) >= 1
        assert len(data["manual_review_history"]) >= 1
        assert data["manual_review_history"][0]["reviewed_grade"] == "URS"


def test_qr_code_generation():
    """Verify QR code PNG generation produces a valid, readable PNG binary."""
    test_url = "https://onionsure.doca.gov.in/verify/VER-TEST-1234"
    qr_png = ReportService.generate_qr_code_image(test_url)
    assert isinstance(qr_png, bytes)
    assert len(qr_png) > 100
    # PNG Magic Bytes: \x89PNG\r\n\x1a\n
    assert qr_png.startswith(b"\x89PNG\r\n\x1a\n")


def test_pdf_report_generation(report_test_engine, full_inspection_setup):
    """Verify ReportLab PDF generation creates a publication-quality PDF starting with %PDF-."""
    SessionLocal = sessionmaker(bind=report_test_engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        data = ReportService.aggregate_inspection_report_data(session, full_inspection_setup["inspection_id"])
        qr_png = ReportService.generate_qr_code_image(data["verification_url"])
        pdf_bytes = ReportService.generate_pdf_document(data, qr_png)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        # Standard PDF magic header
        assert pdf_bytes.startswith(b"%PDF-")


def test_finalize_inspection_endpoint(test_client, auth_headers, full_inspection_setup):
    """
    Test POST /api/v1/inspections/{id}/finalize:
    - Finalizes inspection
    - Generates report with PDF and QR hash
    - Returns ReportResponse
    """
    insp_id = full_inspection_setup["inspection_id"]
    res = test_client.post(f"/api/v1/inspections/{insp_id}/finalize", headers=auth_headers)
    assert res.status_code == 200, f"Finalize failed: {res.text}"
    report_json = res.json()

    assert report_json["inspection_id"] == insp_id
    assert report_json["is_finalized"] is True
    assert "REP-" in report_json["report_code"]
    assert len(report_json["qr_verification_hash"]) == 64
    assert report_json["pdf_storage_key"] is not None

    summary = report_json["summary_metrics"]
    assert summary["verification_id"].startswith("VER-")
    assert summary["lot_decision"] == "ACCEPT_GRADE_A"
    assert summary["grade_a_percentage"] == 84.0
    assert summary["defect_distribution"] is not None
    assert summary["size_distribution"] is not None


def test_pdf_download_endpoint(test_client, auth_headers, full_inspection_setup):
    """
    Test GET /api/v1/reports/{id}/pdf:
    - Returns 200 OK with application/pdf header
    - Content is a valid PDF
    """
    insp_id = full_inspection_setup["inspection_id"]
    # Ensure finalized
    rep_res = test_client.post(f"/api/v1/inspections/{insp_id}/finalize", headers=auth_headers)
    rep_id = rep_res.json()["id"]

    pdf_res = test_client.get(f"/api/v1/reports/{rep_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert "inline; filename=" in pdf_res.headers["content-disposition"]
    assert pdf_res.content.startswith(b"%PDF-")


def test_qr_code_download_endpoint(test_client, auth_headers, full_inspection_setup):
    """
    Test GET /api/v1/reports/{id}/qr:
    - Returns 200 OK with image/png header
    - Content is a valid PNG
    """
    insp_id = full_inspection_setup["inspection_id"]
    rep_res = test_client.post(f"/api/v1/inspections/{insp_id}/finalize", headers=auth_headers)
    assert rep_res.status_code == 200
    rep_id = rep_res.json()["id"]

    qr_res = test_client.get(f"/api/v1/reports/{rep_id}/qr")
    assert qr_res.status_code == 200
    assert qr_res.headers["content-type"] == "image/png"
    assert qr_res.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_public_qr_verification_and_privacy_guarantee(test_client, auth_headers, full_inspection_setup):
    """
    Test GET /api/v1/reports/verify/{identifier}:
    - Verifies by QR verification hash
    - Verifies by human-readable Verification ID
    - PRIVACY RULE: Validates that sensitive personal data (phone, aadhaar) is NOT exposed
    - Returns lot decision, grade percentages, model and policy versions
    """
    insp_id = full_inspection_setup["inspection_id"]
    rep_res = test_client.post(f"/api/v1/inspections/{insp_id}/finalize", headers=auth_headers)
    assert rep_res.status_code == 200
    report = rep_res.json()

    qr_hash = report["qr_verification_hash"]
    verification_id = report["summary_metrics"]["verification_id"]

    # 1. Verify using SHA-256 QR Hash
    v_res1 = test_client.get(f"/api/v1/reports/verify/{qr_hash}")
    assert v_res1.status_code == 200
    data1 = v_res1.json()
    assert data1["is_valid"] is True
    assert data1["verification_status"] == "VALID"
    assert data1["lot_number"] == full_inspection_setup["lot_number"]
    assert data1["lot_decision"] == "ACCEPT_GRADE_A"
    assert data1["grade_a_percentage"] == 84.0
    assert data1["urs_percentage"] == 12.0
    assert data1["reject_percentage"] == 4.0
    assert "DoCA Official Verification Registry" in data1["verification_source"]

    # 2. Verify using human-readable Verification ID
    v_res2 = test_client.get(f"/api/v1/reports/verify/{verification_id}")
    assert v_res2.status_code == 200
    data2 = v_res2.json()
    assert data2["is_valid"] is True
    assert data2["verification_id"] == verification_id

    # 3. STRICT PRIVACY ENFORCEMENT: Ensure NO sensitive PII is returned
    raw_response_text = v_res1.text + v_res2.text
    assert full_inspection_setup["farmer_phone"] not in raw_response_text, "Privacy leak: Farmer phone exposed!"
    assert full_inspection_setup["farmer_aadhaar"] not in raw_response_text, "Privacy leak: Aadhaar exposed!"
    assert "password_hash" not in raw_response_text
    assert "hashed_password" not in raw_response_text


def test_invalid_qr_verification_returns_404(test_client):
    """Verify that an invalid or fabricated verification ID is rejected with 404."""
    invalid_hash = "fake-non-existent-verification-hash-0000"
    res = test_client.get(f"/api/v1/reports/verify/{invalid_hash}")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
