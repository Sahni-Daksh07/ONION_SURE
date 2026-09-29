"""
Deterministic Grading Engine Implementation

Rules:
1. Purely deterministic and auditable.
2. Step-by-step decision trace logged for every evaluation.
3. Machine-readable reason codes accompanied by human-readable explanations.
4. Absolutely NO LLM / generative AI in grading decisions.
5. All rules driven exclusively by versioned GradingPolicy parameters.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .models import (
    GradeType,
    DefectClass,
    SizeStatus,
    MeasurementStatus,
    OnionObservation,
    GradeResult,
    LotGradeSummary,
    GradingPolicy,
    REASON_CODES,
)
from .registry import policy_registry

default_policy_v1 = policy_registry.get_default_policy()


class DeterministicGradingEngine:
    """Core deterministic, auditable grading policy engine for PS26031."""

    def __init__(self, policy: Optional[GradingPolicy] = None):
        self.policy = policy or default_policy_v1

    def grade(
        self,
        obs: OnionObservation,
        policy: Optional[GradingPolicy] = None,
        model_version: str = "cv-v1.0.0",
    ) -> GradeResult:
        active_policy = policy or self.policy
        decision_trace: List[Dict[str, Any]] = []
        reason_codes: List[str] = []
        step = 1

        # Step 1: Image Quality Validation
        if not obs.image_quality_passed:
            decision_trace.append({
                "step": step,
                "check": "image_quality",
                "result": "FAILED",
                "detail": "Input image failed minimum quality validation threshold",
            })
            reason_codes.append("IMAGE_REJECTED")
            return self._build_result(
                obs=obs,
                grade=GradeType.UNAVAILABLE.value,
                reason_codes=reason_codes,
                confidence=0.0,
                decision_trace=decision_trace,
                active_policy=active_policy,
                model_version=model_version,
                requires_review=True,
            )

        decision_trace.append({
            "step": step,
            "check": "image_quality",
            "result": "PASSED",
        })
        step += 1

        # Step 2: Detection Confidence Check
        if obs.detection_confidence < active_policy.minimum_detection_confidence:
            decision_trace.append({
                "step": step,
                "check": "detection_confidence",
                "result": "LOW_CONFIDENCE",
                "confidence": obs.detection_confidence,
                "threshold": active_policy.minimum_detection_confidence,
            })
            reason_codes.append("LOW_CONFIDENCE_DETECTION")
            return self._build_result(
                obs=obs,
                grade=GradeType.MANUAL_REVIEW.value,
                reason_codes=reason_codes,
                confidence=obs.detection_confidence,
                decision_trace=decision_trace,
                active_policy=active_policy,
                model_version=model_version,
                requires_review=True,
            )

        decision_trace.append({
            "step": step,
            "check": "detection_confidence",
            "result": "PASSED",
            "confidence": obs.detection_confidence,
        })
        step += 1

        # Step 3: Defect Confidence Check
        if obs.defect_confidence < active_policy.manual_review_below:
            decision_trace.append({
                "step": step,
                "check": "defect_confidence",
                "result": "LOW_CONFIDENCE",
                "confidence": obs.defect_confidence,
                "threshold": active_policy.manual_review_below,
            })
            reason_codes.append("LOW_CONFIDENCE_DEFECT")
            return self._build_result(
                obs=obs,
                grade=GradeType.MANUAL_REVIEW.value,
                reason_codes=reason_codes,
                confidence=obs.defect_confidence,
                decision_trace=decision_trace,
                active_policy=active_policy,
                model_version=model_version,
                requires_review=True,
            )

        decision_trace.append({
            "step": step,
            "check": "defect_confidence",
            "result": "PASSED",
            "confidence": obs.defect_confidence,
        })
        step += 1

        # Step 4: Unknown Defect Classification Check
        if obs.defect_class == DefectClass.UNKNOWN.value:
            decision_trace.append({
                "step": step,
                "check": "defect_classification",
                "result": "UNKNOWN_DEFECT",
            })
            reason_codes.append("UNKNOWN_DEFECT")
            return self._build_result(
                obs=obs,
                grade=GradeType.MANUAL_REVIEW.value,
                reason_codes=reason_codes,
                confidence=obs.defect_confidence,
                decision_trace=decision_trace,
                active_policy=active_policy,
                model_version=model_version,
                requires_review=True,
            )

        # Step 5: Critical Defect Rejection Rules
        if obs.defect_class in active_policy.reject_defects:
            reason = "ROTTEN_DETECTED" if obs.defect_class == "ROTTEN" else "SPROUTED_DETECTED"
            decision_trace.append({
                "step": step,
                "check": "defect_classification",
                "result": f"{obs.defect_class}_CRITICAL_DEFECT",
                "action": "REJECT",
            })
            reason_codes.append(reason)
            return self._build_result(
                obs=obs,
                grade=GradeType.REJECT.value,
                reason_codes=reason_codes,
                confidence=obs.defect_confidence,
                decision_trace=decision_trace,
                active_policy=active_policy,
                model_version=model_version,
                requires_review=False,
            )

        # Step 6: Physical Size Assessment
        is_undersized = (
            obs.size_status == SizeStatus.UNDERSIZED.value
            or (obs.diameter_mm is not None and obs.diameter_mm < active_policy.undersized_max_diameter_mm)
        )
        if is_undersized:
            decision_trace.append({
                "step": step,
                "check": "size_measurement",
                "result": "UNDERSIZED",
                "diameter_mm": obs.diameter_mm,
                "threshold_mm": active_policy.undersized_max_diameter_mm,
            })
            reason_codes.append("UNDERSIZED")
            return self._build_result(
                obs=obs,
                grade=GradeType.REJECT.value,
                reason_codes=reason_codes,
                confidence=obs.defect_confidence,
                decision_trace=decision_trace,
                active_policy=active_policy,
                model_version=model_version,
                requires_review=False,
            )

        step += 1

        # Step 7: Damaged Defect Evaluation (URS vs Reject based on policy)
        if obs.defect_class == DefectClass.DAMAGED.value:
            if obs.defect_confidence >= active_policy.severe_damage_confidence_threshold:
                decision_trace.append({
                    "step": step,
                    "check": "defect_severity",
                    "result": "SEVERE_DAMAGE",
                    "confidence": obs.defect_confidence,
                    "threshold": active_policy.severe_damage_confidence_threshold,
                })
                reason_codes.append("SEVERE_DAMAGE")
                return self._build_result(
                    obs=obs,
                    grade=GradeType.REJECT.value,
                    reason_codes=reason_codes,
                    confidence=obs.defect_confidence,
                    decision_trace=decision_trace,
                    active_policy=active_policy,
                    model_version=model_version,
                    requires_review=False,
                )
            elif active_policy.minor_damage_urs_allowed:
                decision_trace.append({
                    "step": step,
                    "check": "defect_severity",
                    "result": "MINOR_DAMAGE_URS_QUALIFIED",
                    "confidence": obs.defect_confidence,
                })
                reason_codes.append("MINOR_DAMAGE")
                return self._build_result(
                    obs=obs,
                    grade=GradeType.URS.value,
                    reason_codes=reason_codes,
                    confidence=obs.defect_confidence,
                    decision_trace=decision_trace,
                    active_policy=active_policy,
                    model_version=model_version,
                    requires_review=False,
                )
            else:
                decision_trace.append({
                    "step": step,
                    "check": "defect_severity",
                    "result": "DAMAGE_NOT_PERMITTED_IN_POLICY",
                })
                reason_codes.append("SEVERE_DAMAGE")
                return self._build_result(
                    obs=obs,
                    grade=GradeType.REJECT.value,
                    reason_codes=reason_codes,
                    confidence=obs.defect_confidence,
                    decision_trace=decision_trace,
                    active_policy=active_policy,
                    model_version=model_version,
                    requires_review=False,
                )

        step += 1

        # Step 8: Healthy Onion Grading
        if obs.defect_class == DefectClass.HEALTHY.value:
            # Calibrated physical size meets or exceeds requirement
            if (
                obs.measurement_status == MeasurementStatus.MEASURED.value
                and obs.size_status == SizeStatus.ACCEPTABLE_SIZE.value
                and (obs.diameter_mm is None or obs.diameter_mm >= active_policy.undersized_max_diameter_mm)
            ):
                decision_trace.append({
                    "step": step,
                    "check": "grade_evaluation",
                    "result": "GRADE_A_QUALIFIED",
                    "detail": "Healthy onion with acceptable verified diameter",
                })
                reason_codes.append("HEALTHY_FULL_SIZE")
                return self._build_result(
                    obs=obs,
                    grade=GradeType.GRADE_A.value,
                    reason_codes=reason_codes,
                    confidence=obs.defect_confidence,
                    decision_trace=decision_trace,
                    active_policy=active_policy,
                    model_version=model_version,
                    requires_review=False,
                )

            # Measurement unavailable / uncalibrated
            if (
                obs.measurement_status == MeasurementStatus.MEASUREMENT_UNAVAILABLE.value
                or obs.size_status == SizeStatus.UNDETERMINED.value
            ):
                if active_policy.healthy_urs_allowed_when_unmeasured:
                    decision_trace.append({
                        "step": step,
                        "check": "grade_evaluation",
                        "result": "URS_QUALIFIED",
                        "detail": "Healthy onion with uncalibrated diameter permitted under URS",
                    })
                    reason_codes.append("HEALTHY_SIZE_UNDETERMINED")
                    return self._build_result(
                        obs=obs,
                        grade=GradeType.URS.value,
                        reason_codes=reason_codes,
                        confidence=obs.defect_confidence,
                        decision_trace=decision_trace,
                        active_policy=active_policy,
                        model_version=model_version,
                        requires_review=False,
                    )
                else:
                    decision_trace.append({
                        "step": step,
                        "check": "grade_evaluation",
                        "result": "MEASUREMENT_MANDATORY_IN_POLICY",
                        "detail": "Policy requires verified physical measurement for Grade A or URS",
                    })
                    reason_codes.append("HEALTHY_SIZE_UNDETERMINED")
                    return self._build_result(
                        obs=obs,
                        grade=GradeType.MANUAL_REVIEW.value,
                        reason_codes=reason_codes,
                        confidence=obs.defect_confidence,
                        decision_trace=decision_trace,
                        active_policy=active_policy,
                        model_version=model_version,
                        requires_review=True,
                    )

        # Fallback / Boundary edge case -> Manual Review
        decision_trace.append({
            "step": step,
            "check": "grade_evaluation",
            "result": "UNRESOLVED_EDGE_CASE",
        })
        reason_codes.append("CONFLICTING_EVIDENCE")
        return self._build_result(
            obs=obs,
            grade=GradeType.MANUAL_REVIEW.value,
            reason_codes=reason_codes,
            confidence=obs.defect_confidence,
            decision_trace=decision_trace,
            active_policy=active_policy,
            model_version=model_version,
            requires_review=True,
        )

    def aggregate_lot(
        self,
        lot_id: str,
        inspection_id: str,
        results: List[GradeResult],
        model_version: str = "cv-v1.0.0",
        policy: Optional[GradingPolicy] = None,
    ) -> LotGradeSummary:
        """Aggregates per-onion grading results into an audited lot-level summary."""
        active_policy = policy or self.policy
        total = len(results)

        if total == 0:
            return LotGradeSummary(
                lot_id=lot_id,
                inspection_id=inspection_id,
                total_onions=0,
                graded_onions=0,
                grade_a_count=0,
                grade_a_percentage=0.0,
                urs_count=0,
                urs_percentage=0.0,
                reject_count=0,
                reject_percentage=0.0,
                manual_review_count=0,
                manual_review_percentage=0.0,
                unavailable_count=0,
                unavailable_percentage=0.0,
                defect_distribution={},
                size_distribution={},
                model_version=model_version,
                policy_version=active_policy.version,
                timestamp=datetime.now(timezone.utc).isoformat(),
                lot_decision="EMPTY_LOT",
                decision_reason="No onion samples provided for lot evaluation.",
            )

        grade_counts = {g.value: 0 for g in GradeType}
        defects: Dict[str, int] = {}
        sizes: Dict[str, int] = {}

        for r in results:
            grade_counts[r.grade] = grade_counts.get(r.grade, 0) + 1
            defects[r.defect_class] = defects.get(r.defect_class, 0) + 1
            sizes[r.size_status] = sizes.get(r.size_status, 0) + 1

        calc_pct = lambda cnt: round((cnt / total) * 100.0, 2)
        grade_a_pct = calc_pct(grade_counts[GradeType.GRADE_A.value])
        urs_pct = calc_pct(grade_counts[GradeType.URS.value])
        reject_pct = calc_pct(grade_counts[GradeType.REJECT.value])
        review_pct = calc_pct(grade_counts[GradeType.MANUAL_REVIEW.value])
        unavail_pct = calc_pct(grade_counts[GradeType.UNAVAILABLE.value])

        # Evaluate policy lot acceptance decision
        if reject_pct > active_policy.reject_tolerance_percent:
            lot_decision = "REJECTED"
            reason = f"Reject percentage ({reject_pct}%) exceeds policy tolerance threshold ({active_policy.reject_tolerance_percent}%)."
        elif urs_pct > active_policy.urs_tolerance_percent:
            lot_decision = "CONDITIONAL_URS"
            reason = f"URS percentage ({urs_pct}%) exceeds standard tolerance ({active_policy.urs_tolerance_percent}%)."
        elif review_pct > 15.0:
            lot_decision = "REQUIRES_SUPERVISOR_REVIEW"
            reason = f"High manual review rate ({review_pct}%) requires senior inspector audit."
        else:
            lot_decision = "ACCEPTABLE"
            reason = f"Lot satisfies specification standards under Policy {active_policy.version}."

        return LotGradeSummary(
            lot_id=lot_id,
            inspection_id=inspection_id,
            total_onions=total,
            graded_onions=total - grade_counts[GradeType.UNAVAILABLE.value],
            grade_a_count=grade_counts[GradeType.GRADE_A.value],
            grade_a_percentage=grade_a_pct,
            urs_count=grade_counts[GradeType.URS.value],
            urs_percentage=urs_pct,
            reject_count=grade_counts[GradeType.REJECT.value],
            reject_percentage=reject_pct,
            manual_review_count=grade_counts[GradeType.MANUAL_REVIEW.value],
            manual_review_percentage=review_pct,
            unavailable_count=grade_counts[GradeType.UNAVAILABLE.value],
            unavailable_percentage=unavail_pct,
            defect_distribution=defects,
            size_distribution=sizes,
            model_version=model_version,
            policy_version=active_policy.version,
            timestamp=datetime.now(timezone.utc).isoformat(),
            lot_decision=lot_decision,
            decision_reason=reason,
        )

    def _build_result(
        self,
        obs: OnionObservation,
        grade: str,
        reason_codes: List[str],
        confidence: float,
        decision_trace: List[Dict[str, Any]],
        active_policy: GradingPolicy,
        model_version: str,
        requires_review: bool,
    ) -> GradeResult:
        descriptions = [REASON_CODES.get(code, code) for code in reason_codes]
        return GradeResult(
            grade_id=f"grd-{uuid.uuid4().hex[:12]}",
            detection_id=obs.detection_id,
            grade=grade,
            reason_codes=reason_codes,
            reason_descriptions=descriptions,
            confidence=round(confidence, 3),
            decision_trace=decision_trace,
            policy_version=active_policy.version,
            model_version=model_version,
            timestamp=datetime.now(timezone.utc).isoformat(),
            defect_class=obs.defect_class,
            defect_confidence=obs.defect_confidence,
            size_status=obs.size_status,
            measurement_status=obs.measurement_status,
            diameter_mm=obs.diameter_mm,
            requires_review=requires_review,
        )
