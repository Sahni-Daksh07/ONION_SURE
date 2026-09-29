"""
Grading Persistence Bridge Service
Smart India Hackathon 2026 - Problem Statement PS26031

Connects the Phase 3 Deterministic Grading Engine to the PostgreSQL Database:
- Preserves full auditability and decision traces in database tables
- Ensures historical grading policies and model versions are immutable
- Executes atomic transaction updating detections, measurements, grades, and lot aggregates
"""

from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..models import (
    Inspection,
    OnionDetection,
    DefectResult,
    Measurement,
    GradeResult as DBGradeResult,
    GradingPolicy as DBGradingPolicy,
    GradingPolicyVersion as DBGradingPolicyVersion,
    ModelVersion as DBModelVersion,
)
from .audit_service import AuditService
from onion_sure.grading.models import (
    OnionObservation,
    GradeResult as DomainGradeResult,
    GradingPolicy as DomainGradingPolicy,
)
from onion_sure.grading.registry import policy_registry
from onion_sure.grading.engine import DeterministicGradingEngine


class GradingPersistenceService:
    @staticmethod
    def get_or_create_policy_version(db: Session, policy_version_str: str) -> DBGradingPolicyVersion:
        """Retrieves or registers grading policy and policy version in the database."""
        db_pv = (
            db.query(DBGradingPolicyVersion)
            .filter(DBGradingPolicyVersion.version == policy_version_str)
            .first()
        )
        if db_pv:
            return db_pv

        # Load from domain registry
        domain_policy = policy_registry.get_policy(policy_version_str)

        # Get or create parent policy
        db_policy = db.query(DBGradingPolicy).filter(DBGradingPolicy.code == "DOCA_ONION").first()
        if not db_policy:
            db_policy = DBGradingPolicy(
                code="DOCA_ONION",
                name=domain_policy.name,
                crop="Onion",
                is_active=True,
            )
            db.add(db_policy)
            db.flush()

        db_pv = DBGradingPolicyVersion(
            policy_id=db_policy.id,
            version=domain_policy.version,
            configuration=domain_policy.to_dict(),
            effective_from=datetime.now(timezone.utc),
        )
        db.add(db_pv)
        db.flush()
        return db_pv

    @staticmethod
    def get_or_create_model_version(db: Session, model_version_str: str) -> DBModelVersion:
        """Retrieves or registers model version in the database."""
        db_mv = (
            db.query(DBModelVersion)
            .filter(DBModelVersion.version == model_version_str)
            .first()
        )
        if db_mv:
            return db_mv

        db_mv = DBModelVersion(
            model_name="onion_defect_classifier",
            version=model_version_str,
            model_type="LogisticRegression (balanced class weights)",
            artifact_reference=f"ml/weights/{model_version_str}.joblib",
            dataset_version="1.0.0",
            status="ACTIVE",
        )
        db.add(db_mv)
        db.flush()
        return db_mv

    @classmethod
    def evaluate_and_persist_inspection(
        cls,
        db: Session,
        inspection_id: str,
        observations_data: List[Dict[str, Any]],
        policy_version_str: str = "1.0.0",
        model_version_str: str = "classifier-v1.0.0",
        actor_id: str = None,
    ) -> Tuple[Inspection, List[DBGradeResult]]:
        """
        Executes deterministic grading on all observations and atomically persists
        detections, defect results, measurements, grade results, and lot aggregates.
        """
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if not inspection:
            raise ValueError(f"Inspection '{inspection_id}' not found.")

        # Ensure policy and model versions exist
        db_policy_version = cls.get_or_create_policy_version(db, policy_version_str)
        db_model_version = cls.get_or_create_model_version(db, model_version_str)

        # Domain grading engine and policy
        domain_policy = policy_registry.get_policy(policy_version_str)
        engine = DeterministicGradingEngine(policy=domain_policy)

        domain_results: List[DomainGradeResult] = []
        db_grade_results: List[DBGradeResult] = []

        for obs_item in observations_data:
            # 1. Persist Onion Detection
            detection = OnionDetection(
                image_id=obs_item["image_id"],
                onion_index=obs_item.get("onion_index", "onion_001"),
                bbox_x=obs_item["bbox_x"],
                bbox_y=obs_item["bbox_y"],
                bbox_w=obs_item["bbox_w"],
                bbox_h=obs_item["bbox_h"],
                segmentation_polygon=obs_item.get("segmentation_polygon"),
                detection_confidence=obs_item.get("detection_confidence", 0.90),
            )
            db.add(detection)
            db.flush()

            # 2. Persist Defect Result
            defect = DefectResult(
                detection_id=detection.id,
                defect_class=obs_item.get("defect_class", "HEALTHY"),
                confidence=obs_item.get("defect_confidence", 0.90),
                all_probabilities=obs_item.get("all_probabilities", {}),
                model_version_id=db_model_version.id,
            )
            db.add(defect)

            # 3. Persist Measurement
            measurement = Measurement(
                detection_id=detection.id,
                status=obs_item.get("measurement_status", "measurement_unavailable"),
                diameter_mm=obs_item.get("diameter_mm"),
                diameter_pixels=obs_item.get("diameter_pixels", 150.0),
                calibration_method=obs_item.get("calibration_method"),
                calibration_confidence=obs_item.get("calibration_confidence", 0.0),
                pixels_per_mm=obs_item.get("pixels_per_mm"),
            )
            db.add(measurement)

            # 4. Invoke Deterministic Grading Engine
            norm_defect_class = defect.defect_class.upper()
            is_measured = (
                measurement.diameter_mm is not None
                and measurement.status != "measurement_unavailable"
            )
            norm_meas_status = "measured" if is_measured else "measurement_unavailable"

            domain_obs = OnionObservation(
                detection_id=detection.id,
                detection_confidence=detection.detection_confidence,
                defect_class=norm_defect_class,
                defect_confidence=defect.confidence,
                size_status="UNDERSIZED" if (measurement.diameter_mm and measurement.diameter_mm < domain_policy.undersized_max_diameter_mm) else ("ACCEPTABLE_SIZE" if measurement.diameter_mm else "UNDETERMINED"),
                diameter_mm=measurement.diameter_mm,
                measurement_status=norm_meas_status,
                image_quality_passed=obs_item.get("image_quality_passed", True),
            )
            grade_res = engine.grade(domain_obs, policy=domain_policy, model_version=model_version_str)
            domain_results.append(grade_res)

            # 5. Persist Grade Result
            db_grade = DBGradeResult(
                inspection_id=inspection.id,
                detection_id=detection.id,
                grade=grade_res.grade,
                reason_codes=grade_res.reason_codes,
                confidence=grade_res.confidence,
                decision_trace=grade_res.decision_trace,
                grading_policy_version_id=db_policy_version.id,
                model_version_id=db_model_version.id,
                requires_review=grade_res.requires_review,
            )
            db.add(db_grade)
            db_grade_results.append(db_grade)

        # 6. Aggregate Lot Decision
        lot_summary = engine.aggregate_lot(
            lot_id=inspection.lot_id,
            inspection_id=inspection.id,
            results=domain_results,
            model_version=model_version_str,
            policy=domain_policy,
        )

        # 7. Update Inspection
        inspection.total_onions_evaluated = lot_summary.total_onions
        inspection.grade_a_count = lot_summary.grade_a_count
        inspection.grade_a_percentage = lot_summary.grade_a_percentage
        inspection.urs_count = lot_summary.urs_count
        inspection.urs_percentage = lot_summary.urs_percentage
        inspection.reject_count = lot_summary.reject_count
        inspection.reject_percentage = lot_summary.reject_percentage
        inspection.manual_review_count = lot_summary.manual_review_count
        inspection.lot_decision = lot_summary.lot_decision
        inspection.decision_reason = lot_summary.decision_reason
        inspection.status = "REVIEW_REQUIRED" if lot_summary.manual_review_count > 0 else "COMPLETED"

        # 8. Audit Log
        AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="EVALUATE_AND_PERSIST_GRADING",
            entity_type="Inspection",
            entity_id=inspection.id,
            new_values={
                "total_onions": lot_summary.total_onions,
                "grade_a_pct": lot_summary.grade_a_percentage,
                "urs_pct": lot_summary.urs_percentage,
                "reject_pct": lot_summary.reject_percentage,
                "lot_decision": lot_summary.lot_decision,
                "policy_version": policy_version_str,
            },
        )

        db.commit()
        db.refresh(inspection)
        return inspection, db_grade_results
