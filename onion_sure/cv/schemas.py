"""
Computer Vision Schemas and Domain Models

Defines unified inference schema, detection items, measurements,
and image quality validation data structures.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum


class QualityStatus(str, Enum):
    PASSED = "PASSED"
    WARNING = "WARNING"
    REJECTED = "REJECTED"


class DefectCategory(str, Enum):
    HEALTHY = "HEALTHY"
    DAMAGED = "DAMAGED"
    ROTTEN = "ROTTEN"
    SPROUTED = "SPROUTED"
    UNKNOWN = "UNKNOWN"


class MeasurementState(str, Enum):
    MEASURED = "measured"
    MEASUREMENT_UNAVAILABLE = "measurement_unavailable"


@dataclass
class BoundingBox:
    """Normalized [0, 1] bounding box [x_min, y_min, width, height]."""
    x: float
    y: float
    width: float
    height: float

    def to_list(self) -> List[float]:
        return [round(self.x, 4), round(self.y, 4), round(self.width, 4), round(self.height, 4)]

    def to_pixel_box(self, img_width: int, img_height: int) -> Dict[str, int]:
        return {
            "x_min": int(self.x * img_width),
            "y_min": int(self.y * img_height),
            "x_max": int((self.x + self.width) * img_width),
            "y_max": int((self.y + self.height) * img_height),
        }


@dataclass
class ImageQualityResult:
    """Optical image validation assessment."""
    status: str                       # PASSED, WARNING, REJECTED
    blur_variance: float              # Laplacian variance
    is_blurry: bool
    mean_brightness: float            # 0.0 - 255.0
    contrast_std: float
    is_underexposed: bool
    is_overexposed: bool
    reasons: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnionMeasurementResult:
    """Calibrated physical measurement with strict fallback."""
    measurement_id: str
    status: str                       # measured, measurement_unavailable
    diameter_mm: Optional[float]
    diameter_min_mm: Optional[float] = None
    diameter_max_mm: Optional[float] = None
    diameter_pixels: float = 0.0
    calibration_method: Optional[str] = None
    calibration_confidence: float = 0.0
    pixels_per_mm: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnionInferenceItem:
    """Single onion detection, defect prediction, and measurement result."""
    onion_id: str
    bbox: List[float]                  # [x, y, w, h] normalized
    segmentation: Optional[List[List[float]]] = None  # Polygon contour or bounding vertices
    defect: str = DefectCategory.HEALTHY.value
    defect_confidence: float = 0.0
    all_class_probabilities: Dict[str, float] = field(default_factory=dict)
    diameter_mm: Optional[float] = None
    measurement_confidence: float = 0.0
    measurement_status: str = MeasurementState.MEASUREMENT_UNAVAILABLE.value
    quality_status: str = QualityStatus.PASSED.value
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UnifiedInferenceResult:
    """
    Unified top-level inference result schema.
    Independent of FastAPI and Flutter.
    """
    inspection_id: str
    image_id: str
    image_path: str
    timestamp: str
    model_version: str
    quality_status: str
    quality_details: ImageQualityResult
    calibration_detected: bool
    onions: List[OnionInferenceItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inspection_id": self.inspection_id,
            "image_id": self.image_id,
            "image_path": self.image_path,
            "timestamp": self.timestamp,
            "model_version": self.model_version,
            "quality_status": self.quality_status,
            "quality_details": self.quality_details.to_dict(),
            "calibration_detected": self.calibration_detected,
            "onions": [onion.to_dict() for onion in self.onions],
            "metadata": self.metadata,
        }
