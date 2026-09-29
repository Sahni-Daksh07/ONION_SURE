"""
Unified Computer Vision Inference Pipeline

Orchestrates:
1. Image Quality Validation (Blur, Lighting, Exposure)
2. Onion Instance Detection & Unique ID Assignment
3. Defect Classification & Confidence Scoring
4. Physical Size Calibration & Diameter Estimation
5. Unified Inference Schema Production
6. Direct Bridge to Deterministic Grading Engine
"""

import uuid
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image

from .schemas import (
    UnifiedInferenceResult,
    OnionInferenceItem,
    ImageQualityResult,
    QualityStatus,
    MeasurementState,
)
from .quality import ImageQualityValidator
from .detection import OnionDetector, DetectedInstance
from .classifier import BaseDefectClassifier, ProductionDefectClassifier
from .measurement import CalibrationEngine
from onion_sure.grading.models import OnionObservation, SizeStatus, MeasurementStatus


class VisionPipeline:
    """End-to-end computer vision inference engine for ONION_SURE."""

    def __init__(
        self,
        quality_validator: Optional[ImageQualityValidator] = None,
        detector: Optional[OnionDetector] = None,
        classifier: Optional[BaseDefectClassifier] = None,
        calibration_engine: Optional[CalibrationEngine] = None,
    ):
        self.quality_validator = quality_validator or ImageQualityValidator()
        self.detector = detector or OnionDetector()
        self.classifier = classifier or ProductionDefectClassifier()
        self.calibration_engine = calibration_engine or CalibrationEngine()

    def process_image(
        self,
        img: Image.Image,
        inspection_id: Optional[str] = None,
        image_id: Optional[str] = None,
        image_path: str = "memory://captured_frame.jpg",
        explicit_marker_pixels: Optional[float] = None,
        explicit_reference_size_mm: Optional[float] = None,
    ) -> UnifiedInferenceResult:
        """
        Executes complete inference workflow on a PIL image.
        """
        insp_id = inspection_id or f"insp-{uuid.uuid4().hex[:8]}"
        img_id = image_id or f"img-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Step 1: Image Quality Validation
        quality_res = self.quality_validator.validate(img)

        # Step 2: Calibration Reference Check
        calib_ref = self.calibration_engine.detect_calibration_reference(
            img=img,
            explicit_marker_pixels=explicit_marker_pixels,
            explicit_reference_size_mm=explicit_reference_size_mm,
        )
        has_calib, ppm, calib_conf, _ = calib_ref

        # Step 3: Onion Instance Detection
        detected_instances = self.detector.detect_onions(img)

        # Step 4: Per-Onion Processing (Cropping, Classification, Measurement)
        onions: List[OnionInferenceItem] = []

        width, height = img.size

        for inst in detected_instances:
            # Crop onion patch for defect classifier
            x_min = max(0, min(width - 1, inst.pixel_bbox["x_min"]))
            y_min = max(0, min(height - 1, inst.pixel_bbox["y_min"]))
            x_max = max(x_min + 1, min(width, inst.pixel_bbox["x_max"]))
            y_max = max(y_min + 1, min(height, inst.pixel_bbox["y_max"]))

            patch = img.crop((x_min, y_min, x_max, y_max))

            # Classify defect
            defect_class, defect_conf, all_probs = self.classifier.predict_patch(patch)

            # Measure calibrated diameter
            meas = self.calibration_engine.measure_onion(
                bbox_pixels=inst.pixel_bbox,
                calibration_ref=calib_ref,
            )

            onion_item = OnionInferenceItem(
                onion_id=inst.onion_id,
                bbox=inst.bbox.to_list(),
                segmentation=inst.segmentation,
                defect=defect_class,
                defect_confidence=defect_conf,
                all_class_probabilities=all_probs,
                diameter_mm=meas.diameter_mm,
                measurement_confidence=meas.calibration_confidence,
                measurement_status=meas.status,
                quality_status=quality_res.status,
                metadata={
                    "detection_confidence": inst.confidence,
                    "diameter_pixels": meas.diameter_pixels,
                    "pixels_per_mm": meas.pixels_per_mm,
                    "measurement_metadata": meas.metadata,
                },
            )
            onions.append(onion_item)

        return UnifiedInferenceResult(
            inspection_id=insp_id,
            image_id=img_id,
            image_path=image_path,
            timestamp=timestamp,
            model_version=self.classifier.model_version,
            quality_status=quality_res.status,
            quality_details=quality_res,
            calibration_detected=has_calib,
            onions=onions,
            metadata={
                "image_width": width,
                "image_height": height,
                "total_onions_detected": len(onions),
            },
        )

    def process_file(
        self,
        filepath: Path,
        inspection_id: Optional[str] = None,
        image_id: Optional[str] = None,
        explicit_marker_pixels: Optional[float] = None,
    ) -> UnifiedInferenceResult:
        with Image.open(filepath) as img:
            return self.process_image(
                img=img,
                inspection_id=inspection_id,
                image_id=image_id,
                image_path=filepath.as_posix(),
                explicit_marker_pixels=explicit_marker_pixels,
            )

    @staticmethod
    def to_grading_observations(result: UnifiedInferenceResult) -> List[OnionObservation]:
        """
        Converts unified CV inference items into structured OnionObservations
        for the Deterministic Grading Engine.
        """
        observations = []
        is_quality_passed = result.quality_status != QualityStatus.REJECTED.value

        for onion in result.onions:
            det_conf = onion.metadata.get("detection_confidence", 0.90)

            # Determine size status
            if onion.measurement_status == MeasurementState.MEASURED.value and onion.diameter_mm is not None:
                size_status = (
                    SizeStatus.UNDERSIZED.value if onion.diameter_mm < 40.0
                    else SizeStatus.ACCEPTABLE_SIZE.value
                )
                meas_status = MeasurementStatus.MEASURED.value
            else:
                size_status = SizeStatus.UNDETERMINED.value
                meas_status = MeasurementStatus.MEASUREMENT_UNAVAILABLE.value

            obs = OnionObservation(
                detection_id=f"{result.image_id}_{onion.onion_id}",
                detection_confidence=det_conf,
                defect_class=onion.defect,
                defect_confidence=onion.defect_confidence,
                size_status=size_status,
                diameter_mm=onion.diameter_mm,
                measurement_status=meas_status,
                image_quality_passed=is_quality_passed,
                metadata={
                    "image_id": result.image_id,
                    "onion_id": onion.onion_id,
                    "bbox": onion.bbox,
                    "probabilities": onion.all_class_probabilities,
                },
            )
            observations.append(obs)

        return observations
