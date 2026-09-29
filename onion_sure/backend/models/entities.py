"""
Normalized PostgreSQL Relational Database Schema
Smart India Hackathon 2026 - Problem Statement PS26031

Full Relational Entities:
1. users
2. roles
3. user_roles
4. farmers
5. procurement_centres
6. lots
7. inspections
8. inspection_images
9. onion_detections
10. defect_results
11. measurements
12. grade_results
13. grading_policies
14. grading_policy_versions
15. model_versions
16. manual_reviews
17. reports
18. audit_logs
19. sync_records
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from ..database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


import enum


class InspectionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CAPTURING = "CAPTURING"
    PROCESSING = "PROCESSING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class LotDecision(str, enum.Enum):
    ACCEPTABLE = "ACCEPTABLE"
    REJECTED = "REJECTED"
    CONDITIONAL_URS = "CONDITIONAL_URS"


class DefectClass(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DAMAGED = "DAMAGED"
    ROTTEN = "ROTTEN"
    SPROUTED = "SPROUTED"
    UNKNOWN = "UNKNOWN"


class GradeType(str, enum.Enum):
    GRADE_A = "GRADE_A"
    URS = "URS"
    REJECT = "REJECT"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    UNAVAILABLE = "UNAVAILABLE"


class OpticalQualityStatus(str, enum.Enum):
    PASSED = "PASSED"
    WARNING = "WARNING"
    REJECTED = "REJECTED"


# ==============================================================================
# 1. USER, ROLE, AND ACCESS CONTROL
# ==============================================================================

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), unique=True, nullable=False, index=True)  # inspector, officer, supervisor, admin
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    users = relationship("User", secondary="user_roles", back_populates="roles")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    procurement_centre_id = Column(String(36), ForeignKey("procurement_centres.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    roles = relationship("Role", secondary="user_roles", back_populates="users")
    procurement_centre = relationship("ProcurementCentre", back_populates="staff")
    inspections = relationship("Inspection", back_populates="inspector")


# ==============================================================================
# 2. FARMERS AND PROCUREMENT CENTRES
# ==============================================================================

class ProcurementCentre(Base):
    __tablename__ = "procurement_centres"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    centre_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    staff = relationship("User", back_populates="procurement_centre")
    lots = relationship("Lot", back_populates="procurement_centre")


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    farmer_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    village = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    aadhaar_masked = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    lots = relationship("Lot", back_populates="farmer")


# ==============================================================================
# 3. LOTS AND INSPECTIONS
# ==============================================================================

class Lot(Base):
    __tablename__ = "lots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lot_number = Column(String(100), unique=True, nullable=False, index=True)
    farmer_id = Column(String(36), ForeignKey("farmers.id", ondelete="RESTRICT"), nullable=False, index=True)
    procurement_centre_id = Column(String(36), ForeignKey("procurement_centres.id", ondelete="RESTRICT"), nullable=False, index=True)
    variety = Column(String(50), default="Red Onion", nullable=False)  # Red Onion, White Onion
    quantity_quintals = Column(Float, nullable=False)
    bag_count = Column(Integer, nullable=True)
    status = Column(String(50), default="REGISTERED", nullable=False)  # REGISTERED, INSPECTING, GRADED, DISPATCHED
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    farmer = relationship("Farmer", back_populates="lots")
    procurement_centre = relationship("ProcurementCentre", back_populates="lots")
    inspections = relationship("Inspection", back_populates="lot")


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_code = Column(String(100), unique=True, nullable=False, index=True)
    lot_id = Column(String(36), ForeignKey("lots.id", ondelete="RESTRICT"), nullable=False, index=True)
    inspector_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    sample_size = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False)  # DRAFT, CAPTURING, PROCESSING, REVIEW_REQUIRED, COMPLETED, FAILED
    
    # Lot-level aggregated grade percentages
    total_onions_evaluated = Column(Integer, default=0, nullable=False)
    grade_a_count = Column(Integer, default=0, nullable=False)
    grade_a_percentage = Column(Float, default=0.0, nullable=False)
    urs_count = Column(Integer, default=0, nullable=False)
    urs_percentage = Column(Float, default=0.0, nullable=False)
    reject_count = Column(Integer, default=0, nullable=False)
    reject_percentage = Column(Float, default=0.0, nullable=False)
    manual_review_count = Column(Integer, default=0, nullable=False)
    
    lot_decision = Column(String(50), nullable=True)  # ACCEPTABLE, REJECTED, CONDITIONAL_URS
    decision_reason = Column(Text, nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    lot = relationship("Lot", back_populates="inspections")
    inspector = relationship("User", back_populates="inspections")
    images = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan")
    grade_results = relationship("GradeResult", back_populates="inspection", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="inspection", uselist=False)
    manual_reviews = relationship("ManualReview", back_populates="inspection")


# ==============================================================================
# 4. IMAGES AND CV EVIDENCE (DETECTIONS, DEFECTS, MEASUREMENTS)
# ==============================================================================

class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_id = Column(String(36), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_key = Column(String(500), nullable=False)  # Object storage key or local path
    bucket = Column(String(100), default="onion-sure-inspections", nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(50), default="image/jpeg", nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=True, index=True)
    
    # Optical Quality Validation
    quality_status = Column(String(50), default="PASSED", nullable=False)  # PASSED, WARNING, REJECTED
    blur_variance = Column(Float, nullable=True)
    mean_brightness = Column(Float, nullable=True)
    contrast_std = Column(Float, nullable=True)
    quality_reasons = Column(JSON, default=list)
    
    # Calibration Info
    calibration_detected = Column(Boolean, default=False, nullable=False)
    pixels_per_mm = Column(Float, nullable=True)
    calibration_method = Column(String(50), nullable=True)
    
    captured_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    inspection = relationship("Inspection", back_populates="images")
    detections = relationship("OnionDetection", back_populates="image", cascade="all, delete-orphan")


class OnionDetection(Base):
    __tablename__ = "onion_detections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    image_id = Column(String(36), ForeignKey("inspection_images.id", ondelete="CASCADE"), nullable=False, index=True)
    onion_index = Column(String(50), nullable=False)  # onion_001, onion_002
    
    # Normalized Bounding Box [x, y, w, h]
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_w = Column(Float, nullable=False)
    bbox_h = Column(Float, nullable=False)
    
    # Segmentation Contour Vertices
    segmentation_polygon = Column(JSON, nullable=True)
    detection_confidence = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    image = relationship("InspectionImage", back_populates="detections")
    defect_result = relationship("DefectResult", back_populates="detection", uselist=False, cascade="all, delete-orphan")
    measurement = relationship("Measurement", back_populates="detection", uselist=False, cascade="all, delete-orphan")
    grade_result = relationship("GradeResult", back_populates="detection", uselist=False)


class DefectResult(Base):
    __tablename__ = "defect_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    detection_id = Column(String(36), ForeignKey("onion_detections.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    defect_class = Column(String(50), nullable=False, index=True)  # HEALTHY, DAMAGED, ROTTEN, SPROUTED, UNKNOWN
    confidence = Column(Float, nullable=False)
    all_probabilities = Column(JSON, default=dict)
    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    detection = relationship("OnionDetection", back_populates="defect_result")
    model_version = relationship("ModelVersion")


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    detection_id = Column(String(36), ForeignKey("onion_detections.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False)  # measured, measurement_unavailable
    diameter_mm = Column(Float, nullable=True)
    diameter_min_mm = Column(Float, nullable=True)
    diameter_max_mm = Column(Float, nullable=True)
    diameter_pixels = Column(Float, nullable=False)
    calibration_method = Column(String(50), nullable=True)
    calibration_confidence = Column(Float, default=0.0)
    pixels_per_mm = Column(Float, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    detection = relationship("OnionDetection", back_populates="measurement")


# ==============================================================================
# 5. MODEL AND POLICY VERSIONING
# ==============================================================================

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), unique=True, nullable=False, index=True)
    model_type = Column(String(50), nullable=False)  # classifier, yolo_detector, segmentation
    artifact_reference = Column(String(500), nullable=False)
    dataset_version = Column(String(50), default="1.0.0", nullable=False)
    metrics_summary = Column(JSON, default=dict)
    status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, DEPRECATED, EXPERIMENTAL
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class GradingPolicy(Base):
    __tablename__ = "grading_policies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    crop = Column(String(50), default="Onion", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    versions = relationship("GradingPolicyVersion", back_populates="policy", cascade="all, delete-orphan")


class GradingPolicyVersion(Base):
    __tablename__ = "grading_policy_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    policy_id = Column(String(36), ForeignKey("grading_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(50), nullable=False, index=True)  # 1.0.0, 1.1.0_strict
    configuration = Column(JSON, nullable=False)
    effective_from = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_until = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (UniqueConstraint("policy_id", "version", name="uq_policy_version"),)

    policy = relationship("GradingPolicy", back_populates="versions")
    grade_results = relationship("GradeResult", back_populates="policy_version")


# ==============================================================================
# 6. GRADE RESULTS, MANUAL REVIEW, AND REPORTS
# ==============================================================================

class GradeResult(Base):
    __tablename__ = "grade_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_id = Column(String(36), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    detection_id = Column(String(36), ForeignKey("onion_detections.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    grade = Column(String(50), nullable=False, index=True)  # GRADE_A, URS, REJECT, MANUAL_REVIEW, UNAVAILABLE
    reason_codes = Column(JSON, default=list, nullable=False)
    confidence = Column(Float, nullable=False)
    decision_trace = Column(JSON, nullable=False)  # Immutable audit log of deterministic rule evaluation
    
    grading_policy_version_id = Column(String(36), ForeignKey("grading_policy_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    requires_review = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    inspection = relationship("Inspection", back_populates="grade_results")
    detection = relationship("OnionDetection", back_populates="grade_result")
    policy_version = relationship("GradingPolicyVersion", back_populates="grade_results")
    model_version = relationship("ModelVersion")
    manual_review = relationship("ManualReview", back_populates="grade_result", uselist=False)


class ManualReview(Base):
    __tablename__ = "manual_reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_id = Column(String(36), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    grade_result_id = Column(String(36), ForeignKey("grade_results.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    original_grade = Column(String(50), nullable=False)
    reviewed_grade = Column(String(50), nullable=False)
    reason = Column(String(255), nullable=False)
    comments = Column(Text, nullable=True)
    status = Column(String(50), default="APPROVED", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    inspection = relationship("Inspection", back_populates="manual_reviews")
    grade_result = relationship("GradeResult", back_populates="manual_review")
    reviewer = relationship("User")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_code = Column(String(100), unique=True, nullable=False, index=True)
    inspection_id = Column(String(36), ForeignKey("inspections.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    qr_verification_hash = Column(String(64), unique=True, nullable=False, index=True)
    summary_metrics = Column(JSON, nullable=False)
    pdf_storage_key = Column(String(500), nullable=True)
    is_finalized = Column(Boolean, default=True, nullable=False)
    generated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    inspection = relationship("Inspection", back_populates="report")


# ==============================================================================
# 7. AUDIT LOGGING AND OFFLINE SYNCHRONIZATION
# ==============================================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # CREATE_INSPECTION, MANUAL_OVERRIDE, FINALIZE_REPORT
    entity_type = Column(String(100), nullable=False, index=True)  # Inspection, GradeResult, Policy
    entity_id = Column(String(36), nullable=False, index=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    correlation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    actor = relationship("User")


class SyncRecord(Base):
    __tablename__ = "sync_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(100), nullable=False, index=True)  # Mobile device UUID
    sync_key = Column(String(100), unique=True, nullable=False, index=True)  # Idempotency token
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(36), nullable=False)
    status = Column(String(50), default="SYNCED", nullable=False)  # PENDING, SYNCED, CONFLICT, FAILED
    error_details = Column(Text, nullable=True)
    synced_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
