"""
Grading Engine Domain Models and Schemas
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
from pathlib import Path


class GradeType(str, Enum):
    GRADE_A = "GRADE_A"
    URS = "URS"  # Under Relaxed Specifications
    REJECT = "REJECT"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    UNAVAILABLE = "UNAVAILABLE"


class DefectClass(str, Enum):
    HEALTHY = "HEALTHY"
    DAMAGED = "DAMAGED"
    ROTTEN = "ROTTEN"
    SPROUTED = "SPROUTED"
    UNKNOWN = "UNKNOWN"


class SizeStatus(str, Enum):
    ACCEPTABLE_SIZE = "ACCEPTABLE_SIZE"
    UNDERSIZED = "UNDERSIZED"
    UNDETERMINED = "UNDETERMINED"


class MeasurementStatus(str, Enum):
    MEASURED = "measured"
    MEASUREMENT_UNAVAILABLE = "measurement_unavailable"


REASON_CODES: Dict[str, str] = {
    "HEALTHY_FULL_SIZE": "Onion is healthy with acceptable size",
    "HEALTHY_SIZE_UNDETERMINED": "Onion is healthy but size could not be measured",
    "MINOR_DAMAGE": "Minor damage detected, acceptable under URS",
    "ROTTEN_DETECTED": "Rot detected on onion",
    "SPROUTED_DETECTED": "Sprout growth detected",
    "SEVERE_DAMAGE": "Significant damage detected",
    "UNDERSIZED": "Onion diameter below minimum threshold",
    "LOW_CONFIDENCE_DEFECT": "Defect classification confidence below threshold",
    "LOW_CONFIDENCE_DETECTION": "Onion detection confidence below threshold",
    "CONFLICTING_EVIDENCE": "Conflicting signals between detection and measurement",
    "UNKNOWN_DEFECT": "Defect type could not be classified",
    "INFERENCE_FAILED": "AI inference did not complete successfully",
    "IMAGE_REJECTED": "Image quality too low for reliable inference",
    "NO_ONION_DETECTED": "No onion was detected in the image",
    "HUMAN_OVERRIDE": "Grade overridden by authorized human inspector",
}


@dataclass
class GradingPolicy:
    """Configurable, versioned policy driving deterministic grading rules."""
    version: str = "1.0.0"
    name: str = "Standard Procurement Specification"
    effective_date: str = "2026-01-01"
    description: str = "Standard deterministic grading rules for SIH 2026 PS26031."
    
    # Confidence Thresholds
    minimum_detection_confidence: float = 0.70
    minimum_defect_confidence: float = 0.60
    manual_review_below: float = 0.50
    
    # Size Thresholds (in mm)
    undersized_max_diameter_mm: float = 40.0
    grade_a_min_diameter_mm: float = 50.0
    
    # Defect Rules
    reject_defects: List[str] = field(default_factory=lambda: ["ROTTEN", "SPROUTED"])
    severe_damage_confidence_threshold: float = 0.80
    minor_damage_urs_allowed: bool = True
    healthy_urs_allowed_when_unmeasured: bool = True

    # Lot Tolerances
    urs_tolerance_percent: float = 10.0
    reject_tolerance_percent: float = 2.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GradingPolicy":
        """Instantiates policy from nested or flat dictionary."""
        conf_thresh = data.get("confidence_thresholds", {})
        size_thresh = data.get("size_thresholds", {})
        defect_rules = data.get("defect_rules", {})
        lot_rules = data.get("lot_aggregation_rules", {})

        return cls(
            version=data.get("version", "1.0.0"),
            name=data.get("name", "Standard Procurement Specification"),
            effective_date=data.get("effective_date", "2026-01-01"),
            description=data.get("description", ""),
            minimum_detection_confidence=conf_thresh.get("minimum_detection_confidence", data.get("minimum_detection_confidence", 0.70)),
            minimum_defect_confidence=conf_thresh.get("minimum_defect_confidence", data.get("minimum_defect_confidence", 0.60)),
            manual_review_below=conf_thresh.get("manual_review_below", data.get("manual_review_below", 0.50)),
            undersized_max_diameter_mm=size_thresh.get("undersized_max_diameter_mm", data.get("undersized_max_diameter_mm", 40.0)),
            grade_a_min_diameter_mm=size_thresh.get("grade_a_min_diameter_mm", data.get("grade_a_min_diameter_mm", 50.0)),
            reject_defects=defect_rules.get("reject_defects", data.get("reject_defects", ["ROTTEN", "SPROUTED"])),
            severe_damage_confidence_threshold=defect_rules.get("severe_damage_confidence_threshold", data.get("severe_damage_confidence_threshold", 0.80)),
            minor_damage_urs_allowed=defect_rules.get("minor_damage_urs_allowed", data.get("minor_damage_urs_allowed", True)),
            healthy_urs_allowed_when_unmeasured=defect_rules.get("healthy_urs_allowed_when_unmeasured", data.get("healthy_urs_allowed_when_unmeasured", True)),
            urs_tolerance_percent=lot_rules.get("urs_tolerance_percent", data.get("urs_tolerance_percent", 10.0)),
            reject_tolerance_percent=lot_rules.get("reject_tolerance_percent", data.get("reject_tolerance_percent", 2.0)),
        )

    @classmethod
    def from_json_file(cls, filepath: Path) -> "GradingPolicy":
        """Loads and parses policy from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnionObservation:
    detection_id: str = "det-default"
    detection_confidence: float = 0.95
    defect_class: str = DefectClass.HEALTHY.value
    defect_confidence: float = 0.90
    size_status: str = SizeStatus.ACCEPTABLE_SIZE.value
    diameter_mm: Optional[float] = 55.0
    measurement_status: str = MeasurementStatus.MEASURED.value
    image_quality_passed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GradeResult:
    grade_id: str
    detection_id: str
    grade: str  # GradeType value
    reason_codes: List[str]
    reason_descriptions: List[str]
    confidence: float
    decision_trace: List[Dict[str, Any]]
    policy_version: str
    model_version: str
    timestamp: str

    # Input evidence mirrors
    defect_class: str
    defect_confidence: float
    size_status: str
    measurement_status: str
    diameter_mm: Optional[float]

    # Human Review & Audit
    requires_review: bool
    reviewed_by: Optional[str] = None
    review_override: Optional[str] = None
    review_reason: Optional[str] = None
    review_timestamp: Optional[str] = None

    def apply_human_override(
        self,
        reviewer_id: str,
        override_grade: str,
        reason: str,
    ) -> None:
        """Applies human review override while keeping AI trace intact for auditability."""
        self.reviewed_by = reviewer_id
        self.review_override = override_grade
        self.review_reason = reason
        self.review_timestamp = datetime.now(timezone.utc).isoformat()
        self.grade = override_grade
        self.requires_review = False
        if "HUMAN_OVERRIDE" not in self.reason_codes:
            self.reason_codes.append("HUMAN_OVERRIDE")
            self.reason_descriptions.append(f"Overridden by {reviewer_id}: {reason}")
        self.decision_trace.append({
            "step": len(self.decision_trace) + 1,
            "check": "human_review_override",
            "reviewer_id": reviewer_id,
            "override_grade": override_grade,
            "reason": reason,
            "timestamp": self.review_timestamp,
        })

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LotGradeSummary:
    lot_id: str
    inspection_id: str
    total_onions: int
    graded_onions: int

    grade_a_count: int
    grade_a_percentage: float
    urs_count: int
    urs_percentage: float
    reject_count: int
    reject_percentage: float
    manual_review_count: int
    manual_review_percentage: float
    unavailable_count: int
    unavailable_percentage: float

    defect_distribution: Dict[str, int]
    size_distribution: Dict[str, int]

    model_version: str
    policy_version: str
    timestamp: str
    
    # Lot Assessment Decision
    lot_decision: str = "ACCEPTABLE"  # ACCEPTABLE, REJECTED, CONDITIONAL_URS, REQUIRES_SUPERVISOR_REVIEW
    decision_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
