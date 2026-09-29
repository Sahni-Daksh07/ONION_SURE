"""
Pydantic Request and Response Schemas
Smart India Hackathon 2026 - Problem Statement PS26031
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict


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
# GRADING PERSISTENCE SCHEMAS
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
