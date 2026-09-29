"""
Pydantic Request and Response Schemas
Smart India Hackathon 2026 - Problem Statement PS26031

Comprehensive schemas covering:
- Authentication & RBAC (Users, Roles, Tokens)
- Farmers & Procurement Centres
- Lots & Inspections
- Image storage metadata & Optical quality
- AI results (Detections, Defect results, Measurements)
- Grade results, Grading policies, & Policy versions
- Model versions & Manual reviews
- Reports & QR verification
- Audit logs & Offline sync queue
- Generic pagination wrappers
"""

from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict


T = TypeVar("T")


# ==============================================================================
# PAGINATION & GENERIC API RESPONSES
# ==============================================================================

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


# ==============================================================================
# HEALTH SCHEMA
# ==============================================================================

class HealthResponse(BaseModel):
    status: str = "ok"
    database: str = "connected"
    timestamp: datetime
    version: str = "1.0.0"
    details: Dict[str, Any] = Field(default_factory=dict)


# ==============================================================================
# AUTHENTICATION & RBAC SCHEMAS
# ==============================================================================

class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserRegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    procurement_centre_id: Optional[str] = None
    role_names: List[str] = Field(default_factory=lambda: ["INSPECTOR"])


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user_id: str
    email: str
    full_name: str
    roles: List[str]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    procurement_centre_id: Optional[str] = None
    is_active: bool
    is_superuser: bool
    roles: List[RoleResponse] = Field(default_factory=list)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# FARMER & PROCUREMENT CENTRE SCHEMAS
# ==============================================================================

class FarmerCreate(BaseModel):
    farmer_code: str = Field(..., json_schema_extra={"example": "FARM-MH-2026-001"})
    name: str = Field(..., json_schema_extra={"example": "Ramesh Patil"})
    phone: str = Field(..., json_schema_extra={"example": "9876543210"})
    village: str = Field(..., json_schema_extra={"example": "Lasalgaon"})
    district: str = Field(..., json_schema_extra={"example": "Nashik"})
    state: str = Field(..., json_schema_extra={"example": "Maharashtra"})
    aadhaar_masked: Optional[str] = Field(None, json_schema_extra={"example": "XXXXXXXX1234"})


class FarmerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    aadhaar_masked: Optional[str] = None


class FarmerResponse(FarmerCreate):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProcurementCentreCreate(BaseModel):
    centre_code: str = Field(..., json_schema_extra={"example": "PC-NAS-01"})
    name: str = Field(..., json_schema_extra={"example": "Lasalgaon APMC Sub-Centre"})
    district: str = Field(..., json_schema_extra={"example": "Nashik"})
    state: str = Field(..., json_schema_extra={"example": "Maharashtra"})


class ProcurementCentreResponse(ProcurementCentreCreate):
    id: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# LOT SCHEMAS
# ==============================================================================

class LotCreate(BaseModel):
    lot_number: str = Field(..., json_schema_extra={"example": "LOT-2026-09-001"})
    farmer_id: str
    procurement_centre_id: str
    variety: str = "Red Onion"
    quantity_quintals: float = Field(..., gt=0, json_schema_extra={"example": 50.0})
    bag_count: Optional[int] = Field(None, json_schema_extra={"example": 100})


class LotUpdate(BaseModel):
    variety: Optional[str] = None
    quantity_quintals: Optional[float] = Field(None, gt=0)
    bag_count: Optional[int] = None
    status: Optional[str] = None


class LotResponse(LotCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# INSPECTION SCHEMAS
# ==============================================================================

class InspectionCreate(BaseModel):
    lot_id: str
    inspector_id: str
    inspection_code: Optional[str] = None
    sample_size: int = Field(default=0, ge=0)


class InspectionStatusUpdate(BaseModel):
    status: str  # DRAFT, CAPTURING, PROCESSING, REVIEW_REQUIRED, COMPLETED, FAILED


class InspectionResponse(BaseModel):
    id: str
    inspection_code: str
    lot_id: str
    inspector_id: str
    sample_size: int
    status: str
    total_onions_evaluated: int
    grade_a_count: int
    grade_a_percentage: float
    urs_count: int
    urs_percentage: float
    reject_count: int
    reject_percentage: float
    manual_review_count: int
    lot_decision: Optional[str] = None
    decision_reason: Optional[str] = None
    finalized_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# IMAGE & CV EVIDENCE SCHEMAS
# ==============================================================================

class ImageMetadataCreate(BaseModel):
    inspection_id: str
    storage_key: str
    filename: str
    file_size_bytes: int
    content_type: str = "image/jpeg"
    sha256_hash: Optional[str] = None
    quality_status: str = "PASSED"
    blur_variance: Optional[float] = None
    mean_brightness: Optional[float] = None
    contrast_std: Optional[float] = None
    quality_reasons: List[str] = Field(default_factory=list)
    calibration_detected: bool = False
    pixels_per_mm: Optional[float] = None
    calibration_method: Optional[str] = None


class ImageMetadataResponse(ImageMetadataCreate):
    id: str
    bucket: str
    captured_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# AI RESULTS SCHEMAS (DETECTIONS, DEFECTS, MEASUREMENTS)
# ==============================================================================

class OnionDetectionResponse(BaseModel):
    id: str
    image_id: str
    onion_index: str
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    detection_confidence: float
    segmentation_polygon: Optional[List[Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DefectResultResponse(BaseModel):
    id: str
    detection_id: str
    defect_class: str
    confidence: float
    all_probabilities: Dict[str, float] = Field(default_factory=dict)
    model_version_id: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MeasurementResponse(BaseModel):
    id: str
    detection_id: str
    status: str
    diameter_mm: Optional[float] = None
    diameter_min_mm: Optional[float] = None
    diameter_max_mm: Optional[float] = None
    diameter_pixels: float
    calibration_method: Optional[str] = None
    calibration_confidence: float
    pixels_per_mm: Optional[float] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# GRADING PERSISTENCE & RESULTS
# ==============================================================================

class PersistGradingObservation(BaseModel):
    image_id: str
    onion_index: str = "onion_001"
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    detection_confidence: float = 0.90
    defect_class: str = "HEALTHY"
    defect_confidence: float = 0.90
    diameter_mm: Optional[float] = None
    measurement_status: str = "measured"
    pixels_per_mm: Optional[float] = None


class PersistGradeResultRequest(BaseModel):
    inspection_id: str
    policy_version: str = "1.0.0"
    model_version: str = "classifier-v1.0.0"
    observations: List[PersistGradingObservation]


class GradeResultResponse(BaseModel):
    id: str
    inspection_id: str
    detection_id: Optional[str]
    grade: str
    reason_codes: List[str]
    confidence: float
    decision_trace: List[Dict[str, Any]]
    grading_policy_version_id: str
    model_version_id: Optional[str]
    requires_review: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# GRADING POLICY & VERSIONING SCHEMAS
# ==============================================================================

class GradingPolicyCreate(BaseModel):
    code: str
    name: str
    crop: str = "Onion"
    is_active: bool = True


class GradingPolicyResponse(GradingPolicyCreate):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GradingPolicyVersionCreate(BaseModel):
    policy_id: str
    version: str
    configuration: Dict[str, Any]
    effective_from: Optional[datetime] = None


class GradingPolicyVersionResponse(BaseModel):
    id: str
    policy_id: str
    version: str
    configuration: Dict[str, Any]
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# MODEL VERSIONING SCHEMAS
# ==============================================================================

class ModelVersionCreate(BaseModel):
    model_name: str
    version: str
    model_type: str
    artifact_reference: str
    dataset_version: str = "1.0.0"
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)
    status: str = "ACTIVE"


class ModelVersionResponse(ModelVersionCreate):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# MANUAL REVIEW & REPORT SCHEMAS
# ==============================================================================

class ManualReviewCreate(BaseModel):
    grade_result_id: str
    reviewer_id: str
    reviewed_grade: str
    reason: str
    comments: Optional[str] = None


class ManualReviewResponse(BaseModel):
    id: str
    inspection_id: str
    grade_result_id: str
    reviewer_id: str
    original_grade: str
    reviewed_grade: str
    reason: str
    comments: Optional[str]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReportResponse(BaseModel):
    id: str
    report_code: str
    inspection_id: str
    qr_verification_hash: str
    summary_metrics: Dict[str, Any]
    pdf_storage_key: Optional[str]
    is_finalized: bool
    generated_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReportVerifyResponse(BaseModel):
    is_valid: bool
    report_code: str
    inspection_id: str
    qr_verification_hash: str
    generated_at: datetime
    summary_metrics: Dict[str, Any]
    verification_source: str = "DoCA Official Verification Registry"


# ==============================================================================
# AUDIT LOG SCHEMAS
# ==============================================================================

class AuditLogResponse(BaseModel):
    id: str
    actor_id: Optional[str]
    action: str
    entity_type: str
    entity_id: str
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    correlation_id: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# OFFLINE SYNC SCHEMAS
# ==============================================================================

class SyncItemCreate(BaseModel):
    client_id: str
    sync_key: str  # Client-side idempotency UUID
    entity_type: str  # Inspection, InspectionImage, GradeResult
    entity_id: str
    payload: Dict[str, Any]


class SyncItemResponse(BaseModel):
    sync_key: str
    entity_type: str
    entity_id: str
    status: str  # SYNCED, CONFLICT, FAILED
    synced_at: datetime
    error_details: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SyncBatchRequest(BaseModel):
    client_id: str
    items: List[SyncItemCreate]


class SyncBatchResponse(BaseModel):
    client_id: str
    processed_count: int
    success_count: int
    failed_count: int
    results: List[SyncItemResponse]
