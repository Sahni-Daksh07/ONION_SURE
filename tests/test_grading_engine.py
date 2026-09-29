"""
Comprehensive Unit and Edge-Case Tests for Deterministic Grading Engine

Mandatory Suite as specified in .agents/skills/testing/SKILL.md
and .agents/skills/grading-engine/SKILL.md:
- Deterministic rule verification (Grade A, URS, Reject, Manual Review, Unavailable)
- Policy versioning and hot-swapping (Standard v1.0.0 vs Strict v1.1.0 vs Relaxed v1.2.0)
- Boundary condition checks (diameters, confidence thresholds)
- Human review override audit trail
- Lot-level aggregation math & acceptance decisions
"""

import pytest
from onion_sure.grading.models import (
    GradeType,
    DefectClass,
    SizeStatus,
    MeasurementStatus,
    OnionObservation,
    GradeResult,
    GradingPolicy,
)
from onion_sure.grading.registry import policy_registry
from onion_sure.grading.engine import DeterministicGradingEngine


@pytest.fixture
def engine():
    return DeterministicGradingEngine()


@pytest.fixture
def policy_standard():
    return policy_registry.get_policy("1.0.0")


@pytest.fixture
def policy_strict():
    return policy_registry.get_policy("1.1.0_strict")


@pytest.fixture
def policy_relaxed():
    return policy_registry.get_policy("1.2.0_relaxed")


# --- 1. Mandatory Core Rule Tests ---

def test_grade_a_healthy_full_size(engine, policy_standard):
    """Healthy onion with acceptable verified size -> Grade A."""
    obs = OnionObservation(
        detection_id="det-001",
        detection_confidence=0.95,
        defect_class=DefectClass.HEALTHY.value,
        defect_confidence=0.92,
        size_status=SizeStatus.ACCEPTABLE_SIZE.value,
        diameter_mm=55.0,
        measurement_status=MeasurementStatus.MEASURED.value,
    )
    result = engine.grade(obs, policy=policy_standard)
    assert result.grade == GradeType.GRADE_A.value
    assert "HEALTHY_FULL_SIZE" in result.reason_codes
    assert result.requires_review is False
    assert result.policy_version == "1.0.0"


def test_undersized_onion_rejection(engine, policy_standard):
    """Onion below size threshold (< 40mm) -> Reject (undersized)."""
    obs = OnionObservation(
        detection_id="det-002",
        detection_confidence=0.90,
        defect_class=DefectClass.HEALTHY.value,
        defect_confidence=0.91,
        size_status=SizeStatus.UNDERSIZED.value,
        diameter_mm=38.5,
        measurement_status=MeasurementStatus.MEASURED.value,
    )
    result = engine.grade(obs, policy=policy_standard)
    assert result.grade == GradeType.REJECT.value
    assert "UNDERSIZED" in result.reason_codes


def test_rotten_onion_critical_rejection(engine, policy_standard):
    """Rotten onion -> Immediate Reject."""
    obs = OnionObservation(
        detection_id="det-003",
        detection_confidence=0.88,
        defect_class=DefectClass.ROTTEN.value,
        defect_confidence=0.85,
        size_status=SizeStatus.ACCEPTABLE_SIZE.value,
        diameter_mm=52.0,
        measurement_status=MeasurementStatus.MEASURED.value,
    )
    result = engine.grade(obs, policy=policy_standard)
    assert result.grade == GradeType.REJECT.value
    assert "ROTTEN_DETECTED" in result.reason_codes


def test_sprouted_onion_critical_rejection(engine, policy_standard):
    """Sprouted onion -> Immediate Reject."""
    obs = OnionObservation(
        detection_id="det-004",
        detection_confidence=0.92,
        defect_class=DefectClass.SPROUTED.value,
        defect_confidence=0.89,
        size_status=SizeStatus.ACCEPTABLE_SIZE.value,
        diameter_mm=50.0,
        measurement_status=MeasurementStatus.MEASURED.value,
    )
    result = engine.grade(obs, policy=policy_standard)
    assert result.grade == GradeType.REJECT.value
    assert "SPROUTED_DETECTED" in result.reason_codes


def test_damaged_onion_severity_split(engine, policy_standard):
    """Minor damage -> URS; Severe damage (>= 0.80) -> REJECT."""
    obs_minor = OnionObservation(
        detection_id="det-005a",
        defect_class=DefectClass.DAMAGED.value,
        defect_confidence=0.72,
        diameter_mm=48.0,
    )
    obs_severe = OnionObservation(
        detection_id="det-005b",
        defect_class=DefectClass.DAMAGED.value,
        defect_confidence=0.85,
        diameter_mm=48.0,
    )
    res_minor = engine.grade(obs_minor, policy=policy_standard)
    res_severe = engine.grade(obs_severe, policy=policy_standard)

    assert res_minor.grade == GradeType.URS.value
    assert "MINOR_DAMAGE" in res_minor.reason_codes

    assert res_severe.grade == GradeType.REJECT.value
    assert "SEVERE_DAMAGE" in res_severe.reason_codes


# --- 2. Boundary Condition & Threshold Tests ---

def test_boundary_diameter_threshold(engine, policy_standard):
    """Exact boundary diameter testing (39.9mm vs 40.0mm)."""
    # 39.9mm is undersized (< 40.0mm)
    obs_under = OnionObservation(
        defect_class=DefectClass.HEALTHY.value,
        size_status=SizeStatus.UNDERSIZED.value,
        diameter_mm=39.9,
    )
    # 40.0mm meets minimum size requirement
    obs_valid = OnionObservation(
        defect_class=DefectClass.HEALTHY.value,
        size_status=SizeStatus.ACCEPTABLE_SIZE.value,
        diameter_mm=40.0,
    )
    res_under = engine.grade(obs_under, policy=policy_standard)
    res_valid = engine.grade(obs_valid, policy=policy_standard)

    assert res_under.grade == GradeType.REJECT.value
    assert "UNDERSIZED" in res_under.reason_codes

    assert res_valid.grade == GradeType.GRADE_A.value
    assert "HEALTHY_FULL_SIZE" in res_valid.reason_codes


def test_boundary_confidence_thresholds(engine, policy_standard):
    """Confidence 0.499 (< 0.50) triggers MANUAL_REVIEW."""
    obs_low = OnionObservation(
        defect_class=DefectClass.HEALTHY.value,
        defect_confidence=0.499,
        diameter_mm=50.0,
    )
    obs_pass = OnionObservation(
        defect_class=DefectClass.HEALTHY.value,
        defect_confidence=0.501,
        diameter_mm=50.0,
    )
    res_low = engine.grade(obs_low, policy=policy_standard)
    res_pass = engine.grade(obs_pass, policy=policy_standard)

    assert res_low.grade == GradeType.MANUAL_REVIEW.value
    assert res_low.requires_review is True
    assert "LOW_CONFIDENCE_DEFECT" in res_low.reason_codes

    assert res_pass.grade == GradeType.GRADE_A.value


def test_detection_confidence_boundary(engine, policy_standard):
    """Detection confidence < 0.70 triggers MANUAL_REVIEW."""
    obs = OnionObservation(
        detection_confidence=0.69,
        defect_confidence=0.90,
    )
    res = engine.grade(obs, policy=policy_standard)
    assert res.grade == GradeType.MANUAL_REVIEW.value
    assert "LOW_CONFIDENCE_DETECTION" in res.reason_codes


# --- 3. Edge Cases: Unknown Classes & Unavailable Data ---

def test_unknown_defect_triggers_manual_review(engine, policy_standard):
    """Unknown defect category must require manual review."""
    obs = OnionObservation(
        defect_class=DefectClass.UNKNOWN.value,
        defect_confidence=0.80,
    )
    res = engine.grade(obs, policy=policy_standard)
    assert res.grade == GradeType.MANUAL_REVIEW.value
    assert "UNKNOWN_DEFECT" in res.reason_codes
    assert res.requires_review is True


def test_optical_quality_rejected_triggers_unavailable(engine, policy_standard):
    """Rejected optical quality -> UNAVAILABLE."""
    obs = OnionObservation(image_quality_passed=False)
    res = engine.grade(obs, policy=policy_standard)
    assert res.grade == GradeType.UNAVAILABLE.value
    assert "IMAGE_REJECTED" in res.reason_codes


def test_unmeasured_healthy_across_policies(engine, policy_standard, policy_strict):
    """
    Standard Policy (v1.0.0) permits unmeasured healthy onions under URS.
    Strict Policy (v1.1.0_strict) mandates physical measurement and routes unmeasured to MANUAL_REVIEW.
    """
    obs_unmeasured = OnionObservation(
        defect_class=DefectClass.HEALTHY.value,
        defect_confidence=0.90,
        diameter_mm=None,
        measurement_status=MeasurementStatus.MEASUREMENT_UNAVAILABLE.value,
        size_status=SizeStatus.UNDETERMINED.value,
    )

    res_std = engine.grade(obs_unmeasured, policy=policy_standard)
    res_strict = engine.grade(obs_unmeasured, policy=policy_strict)

    # Standard policy allows URS
    assert res_std.grade == GradeType.URS.value
    assert "HEALTHY_SIZE_UNDETERMINED" in res_std.reason_codes

    # Strict export policy mandates measurement -> Manual Review
    assert res_strict.grade == GradeType.MANUAL_REVIEW.value
    assert res_strict.policy_version == "1.1.0_strict"
    assert res_strict.requires_review is True


# --- 4. Human Review & Audit Trail ---

def test_human_review_override_audit():
    """Human review override updates grade while preserving AI trace."""
    obs = OnionObservation(
        defect_class=DefectClass.HEALTHY.value,
        defect_confidence=0.45,  # Low confidence -> Manual Review
    )
    engine = DeterministicGradingEngine()
    result = engine.grade(obs)
    assert result.grade == GradeType.MANUAL_REVIEW.value
    assert result.requires_review is True

    # Supervisor reviews sample and overrides to Grade A
    result.apply_human_override(
        reviewer_id="insp_sharma_07",
        override_grade=GradeType.GRADE_A.value,
        reason="Visual confirmation on re-examination shows clear bulb without rot",
    )

    assert result.grade == GradeType.GRADE_A.value
    assert result.requires_review is False
    assert result.reviewed_by == "insp_sharma_07"
    assert "HUMAN_OVERRIDE" in result.reason_codes
    assert any(step["check"] == "human_review_override" for step in result.decision_trace)


# --- 5. Lot-Level Aggregation & Policy Decisions ---

def test_lot_level_decision_logic(engine, policy_standard):
    """Verifies lot acceptance, conditional URS, and rejection thresholds."""
    # Lot A: 90 Grade A, 10 URS -> 10% URS <= 10.0% tolerance -> ACCEPTABLE
    lot_a_results = (
        [GradeResult("1", "d", GradeType.GRADE_A.value, [], [], 0.9, [], "1.0.0", "m", "", "HEALTHY", 0.9, "A", "m", 50, False)] * 90
        + [GradeResult("2", "d", GradeType.URS.value, [], [], 0.8, [], "1.0.0", "m", "", "DAMAGED", 0.7, "A", "m", 50, False)] * 10
    )
    summary_a = engine.aggregate_lot("LOT-A", "INSP-01", lot_a_results, policy=policy_standard)
    assert summary_a.lot_decision == "ACCEPTABLE"
    assert summary_a.grade_a_percentage == 90.0
    assert summary_a.urs_percentage == 10.0

    # Lot B: Exceeds reject tolerance (> 2.0%)
    lot_b_results = (
        [GradeResult("1", "d", GradeType.GRADE_A.value, [], [], 0.9, [], "1.0.0", "m", "", "HEALTHY", 0.9, "A", "m", 50, False)] * 95
        + [GradeResult("2", "d", GradeType.REJECT.value, [], [], 0.9, [], "1.0.0", "m", "", "ROTTEN", 0.9, "A", "m", 50, False)] * 5
    )
    summary_b = engine.aggregate_lot("LOT-B", "INSP-02", lot_b_results, policy=policy_standard)
    assert summary_b.lot_decision == "REJECTED"
    assert summary_b.reject_percentage == 5.0
    assert "exceeds policy tolerance threshold" in summary_b.decision_reason


def test_empty_lot_handling(engine):
    """Empty lot returns 0 counts and EMPTY_LOT decision without crashing."""
    summary = engine.aggregate_lot("EMPTY-LOT", "INSP-00", [])
    assert summary.total_onions == 0
    assert summary.grade_a_count == 0
    assert summary.grade_a_percentage == 0.0
    assert summary.lot_decision == "EMPTY_LOT"
