"""
ONION_SURE — Computer Vision Subsystem

"""

from .schemas import (
    BoundingBox,
    ImageQualityResult,
    OnionMeasurementResult,
    OnionInferenceItem,
    UnifiedInferenceResult,
    QualityStatus,
    DefectCategory,
    MeasurementState,
)
from .quality import ImageQualityValidator
from .measurement import CalibrationEngine
from .detection import OnionDetector, DetectedInstance
from .classifier import (
    BaseDefectClassifier,
    ProductionDefectClassifier,
    FeatureExtractor,
)
from .pipeline import VisionPipeline
from .training import train_classifier
from .evaluation import evaluate_model

__all__ = [
    "BoundingBox",
    "ImageQualityResult",
    "OnionMeasurementResult",
    "OnionInferenceItem",
    "UnifiedInferenceResult",
    "QualityStatus",
    "DefectCategory",
    "MeasurementState",
    "ImageQualityValidator",
    "CalibrationEngine",
    "OnionDetector",
    "DetectedInstance",
    "BaseDefectClassifier",
    "ProductionDefectClassifier",
    "FeatureExtractor",
    "VisionPipeline",
    "train_classifier",
    "evaluate_model",
]
