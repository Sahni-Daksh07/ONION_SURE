"""
Unit and Integration Tests for Computer Vision Subsystem

Verifies:
1. Image Quality Validator (blur, brightness, contrast, size)
2. Calibration Engine (with and without physical reference)
3. Onion Instance Detector & Unique ID Assignment
4. Defect Classifier & Probabilities
5. End-to-End Vision Pipeline to Unified Inference Schema
6. CV-to-Grading Engine integration bridge
"""

import pytest
import numpy as np
from PIL import Image

from onion_sure.cv.schemas import (
    UnifiedInferenceResult,
    QualityStatus,
    MeasurementState,
    DefectCategory,
)
from onion_sure.cv.quality import ImageQualityValidator
from onion_sure.cv.measurement import CalibrationEngine
from onion_sure.cv.detection import OnionDetector
from onion_sure.cv.classifier import ProductionDefectClassifier, FeatureExtractor
from onion_sure.cv.pipeline import VisionPipeline
from onion_sure.grading.engine import DeterministicGradingEngine


@pytest.fixture
def synthetic_sample_image():
    """Generates a 400x400 synthetic image with a centered colored bulb."""
    arr = np.full((400, 400, 3), 200, dtype=np.uint8)  # neutral light background
    # Centered onion bulb (purplish-red ellipse, radius ~80px -> diameter ~160px)
    y, x = np.ogrid[:400, :400]
    dist = ((x - 200) ** 2) / (75 ** 2) + ((y - 200) ** 2) / (85 ** 2)
    mask = dist <= 1.0
    arr[mask] = [170, 45, 80]  # onion reddish-purple
    return Image.fromarray(arr)


def test_image_quality_validator_clear(synthetic_sample_image):
    validator = ImageQualityValidator()
    res = validator.validate(synthetic_sample_image)
    assert res.status in [QualityStatus.PASSED.value, QualityStatus.WARNING.value]
    assert res.blur_variance > 0
    assert not res.is_underexposed
    assert not res.is_overexposed


def test_image_quality_validator_tiny():
    validator = ImageQualityValidator(min_dimension_px=200)
    tiny_img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    res = validator.validate(tiny_img)
    assert res.status == QualityStatus.REJECTED.value
    assert any("below minimum requirement" in r for r in res.reasons)


def test_calibration_engine_with_reference():
    engine = CalibrationEngine(default_marker_size_mm=50.0)
    # 500 pixels for 50mm -> 10 pixels/mm
    calib_ref = (True, 10.0, 0.98, "aruco_marker")
    bbox_px = {"x_min": 100, "y_min": 100, "x_max": 600, "y_max": 600}  # 500x500 px
    meas = engine.measure_onion(bbox_px, calib_ref)

    assert meas.status == MeasurementState.MEASURED.value
    assert meas.diameter_mm is not None
    assert pytest.approx(meas.diameter_mm, rel=1e-1) == 50.0
    assert meas.diameter_min_mm < meas.diameter_mm < meas.diameter_max_mm
    assert engine.is_undersized(meas) == "ACCEPTABLE_SIZE"


def test_calibration_engine_without_reference():
    engine = CalibrationEngine()
    calib_ref = (False, None, 0.0, None)
    bbox_px = {"x_min": 100, "y_min": 100, "x_max": 600, "y_max": 600}
    meas = engine.measure_onion(bbox_px, calib_ref)

    assert meas.status == MeasurementState.MEASUREMENT_UNAVAILABLE.value
    assert meas.diameter_mm is None
    assert meas.diameter_pixels > 0
    assert engine.is_undersized(meas) == "UNDETERMINED"


def test_onion_detector(synthetic_sample_image):
    detector = OnionDetector()
    instances = detector.detect_onions(synthetic_sample_image)

    assert len(instances) >= 1
    inst = instances[0]
    assert inst.onion_id.startswith("onion_")
    assert inst.confidence > 0.5
    assert len(inst.bbox.to_list()) == 4
    assert len(inst.segmentation) >= 4


def test_feature_extractor_and_classifier(synthetic_sample_image):
    classifier = ProductionDefectClassifier()
    top_class, conf, probs = classifier.predict_patch(synthetic_sample_image)

    assert top_class in [c.value for c in DefectCategory]
    assert 0.0 <= conf <= 1.0
    assert isinstance(probs, dict)
    assert len(probs) >= 2


def test_vision_pipeline_end_to_end(synthetic_sample_image):
    pipeline = VisionPipeline()
    result = pipeline.process_image(
        img=synthetic_sample_image,
        inspection_id="INSP-SIH-2026",
        image_id="IMG-001",
        explicit_marker_pixels=500.0,  # simulate 50mm ArUco marker at 500px -> 10 px/mm
    )

    assert isinstance(result, UnifiedInferenceResult)
    assert result.inspection_id == "INSP-SIH-2026"
    assert result.image_id == "IMG-001"
    assert result.calibration_detected is True
    assert len(result.onions) >= 1

    first_onion = result.onions[0]
    assert first_onion.diameter_mm is not None
    assert first_onion.measurement_status == MeasurementState.MEASURED.value
    assert first_onion.defect in [c.value for c in DefectCategory]

    # Test bridge to Deterministic Grading Engine
    grading_obs = pipeline.to_grading_observations(result)
    assert len(grading_obs) == len(result.onions)

    grading_engine = DeterministicGradingEngine()
    grade_res = grading_engine.grade(grading_obs[0])
    assert grade_res.grade in ["GRADE_A", "URS", "REJECT", "MANUAL_REVIEW"]
    assert len(grade_res.decision_trace) > 0
