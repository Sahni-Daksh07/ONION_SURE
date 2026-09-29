---
name: grading-engine
description: >-
  Defines the deterministic, auditable grading engine for ONION_SURE. The
  grading engine takes structured CV observations and applies versioned
  grading policies to produce Grade A, URS, Reject, Manual Review, or
  Unavailable results. LLMs are NEVER allowed in the grading path. The
  engine must be independently testable with configurable thresholds,
  reason codes, decision traces, and audit history. Activate for any
  grading, policy, or quality assessment task.
---

# Grading Engine Skill

## Purpose

Implement and maintain the deterministic grading engine — the most critical
component of ONION_SURE. This engine converts structured computer vision
observations into auditable quality grades.

## When to Use

- Implementing or modifying grading logic.
- Defining or updating grading policies.
- Testing grading decisions.
- Auditing grade results.
- Configuring grading thresholds.
- Reviewing the decision pipeline.

## Required Inputs

- Structured observations from `computer-vision` skill (OnionDetection).
- Measurement results from `onion-measurement` skill (OnionMeasurement).
- Grading policy configuration.

---

## Architecture: The Sacred Pipeline

```
┌─────────────────────┐
│  Computer Vision    │  → OnionDetection (defect class, confidence)
│  (AI Model)         │
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Onion Measurement  │  → OnionMeasurement (diameter, calibration status)
│  (Calibration)      │
└────────┬────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  STRUCTURED OBSERVATIONS                         │
│  - defect_class + confidence                     │
│  - size_classification + calibration_status      │
│  - image_quality_report                          │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  GRADING POLICY ENGINE (Deterministic)           │
│  - Rule evaluation                               │
│  - Confidence thresholds                         │
│  - Policy version                                │
│  - Decision trace                                │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  GRADE RESULT                                    │
│  - grade: GRADE_A | URS | REJECT |               │
│           MANUAL_REVIEW | UNAVAILABLE            │
│  - reason_codes: [...]                           │
│  - decision_trace: [...]                         │
│  - confidence: float                             │
│  - policy_version: str                           │
└─────────────────────────────────────────────────┘
```

### WHAT IS ABSOLUTELY FORBIDDEN

```
┌─────────────────┐
│  LLM / ChatGPT  │  → "This onion is Grade A"     ❌ NEVER
│  / Any GenAI    │
└─────────────────┘

┌─────────────────┐
│  Hardcoded       │  → if image_name == "abc.jpg"  ❌ NEVER
│  Results         │     return "Grade A"
└─────────────────┘

┌─────────────────┐
│  Random /        │  → grade = random.choice(...)   ❌ NEVER
│  Fabricated      │
└─────────────────┘
```

---

## Grade Definitions

| Grade | Code | Description | Criteria |
|:---|:---|:---|:---|
| **Grade A** | `GRADE_A` | Premium quality | Healthy, properly sized, no defects, high confidence |
| **URS** | `URS` | Under Relaxed Specifications | Minor defects, acceptable under relaxed criteria |
| **Reject** | `REJECT` | Does not meet minimum quality | Rotten, severely damaged, or multiple defects |
| **Manual Review** | `MANUAL_REVIEW` | Requires human inspection | Low confidence, conflicting evidence, edge cases |
| **Unavailable** | `UNAVAILABLE` | Cannot determine grade | Missing data, failed inference, no calibration |

---

## Grading Policy Configuration

```yaml
grading_policy:
  version: "1.0.0"
  effective_date: "2026-XX-XX"
  
  confidence_thresholds:
    minimum_detection_confidence: 0.7
    minimum_defect_confidence: 0.6
    manual_review_below: 0.5
  
  size_thresholds:
    undersized_max_diameter_mm: 40.0
    grade_a_min_diameter_mm: 50.0
  
  grade_rules:
    grade_a:
      defect_class: "HEALTHY"
      min_defect_confidence: 0.7
      size_status: ["ACCEPTABLE_SIZE"]
      measurement_required: true
    
    urs:
      defect_class: ["HEALTHY", "DAMAGED"]
      conditions:
        - "HEALTHY with UNDETERMINED size"
        - "DAMAGED with defect_confidence < 0.8"
        - "minor damage below severity threshold"
    
    reject:
      defect_class: ["ROTTEN", "SPROUTED"]
      conditions:
        - "any ROTTEN classification"
        - "any SPROUTED classification"
        - "DAMAGED with defect_confidence >= 0.8"
        - "UNDERSIZED below threshold"
    
    manual_review:
      conditions:
        - "detection_confidence < minimum_detection_confidence"
        - "defect_confidence < manual_review_below"
        - "conflicting evidence between detection and measurement"
        - "UNKNOWN defect class"
    
    unavailable:
      conditions:
        - "inference failed"
        - "image quality rejected"
        - "no onion detected"
```

---

## Grade Result Format

```python
@dataclass
class GradeResult:
    grade_id: str
    detection_id: str
    grade: str                    # GRADE_A, URS, REJECT, MANUAL_REVIEW, UNAVAILABLE
    reason_codes: List[str]       # Machine-readable reasons
    reason_descriptions: List[str]  # Human-readable explanations
    confidence: float             # Overall grading confidence
    decision_trace: List[dict]    # Step-by-step decision log
    policy_version: str           # Which policy version was applied
    model_version: str            # Which CV model produced the observations
    timestamp: str                # ISO 8601
    
    # Input evidence
    defect_class: str
    defect_confidence: float
    size_status: str              # ACCEPTABLE_SIZE, UNDERSIZED, UNDETERMINED
    measurement_status: str       # measured, measurement_unavailable
    
    # Review
    requires_review: bool
    reviewed_by: Optional[str]
    review_override: Optional[str]
    review_reason: Optional[str]
```

### Reason Codes

```python
REASON_CODES = {
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
}
```

### Decision Trace Example

```json
[
  {"step": 1, "check": "image_quality", "result": "PASS", "detail": "blur=0.85, brightness=0.62"},
  {"step": 2, "check": "onion_detection", "result": "DETECTED", "confidence": 0.92},
  {"step": 3, "check": "defect_classification", "result": "HEALTHY", "confidence": 0.88},
  {"step": 4, "check": "size_measurement", "result": "ACCEPTABLE_SIZE", "diameter_mm": 55.2},
  {"step": 5, "check": "policy_evaluation", "rule": "grade_a", "result": "MATCH"},
  {"step": 6, "check": "final_grade", "grade": "GRADE_A", "confidence": 0.88}
]
```

---

## Lot-Level Aggregation

```python
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
    
    defect_distribution: dict     # {defect_class: count}
    size_distribution: dict       # {size_category: count}
    
    model_version: str
    policy_version: str
    timestamp: str
```

---

## Implementation Rules

1. **Grading logic is centralized.** One module, one source of truth.
2. **Policy is configuration, not code.** Thresholds and rules live in YAML/JSON.
3. **Every grade has a decision trace.** Full auditability.
4. **Every grade has reason codes.** Machine-readable explanations.
5. **Policy is versioned.** Every result references a policy version.
6. **The engine is independently testable.** Given observations → verify grade.
7. **Manual review is a valid output.** The system admits uncertainty.
8. **Unavailable is a valid output.** The system admits missing data.
9. **Human overrides are logged.** With reviewer ID, timestamp, and reason.

---

## Validation Rules

- ✅ Same observations + same policy → same grade (deterministic).
- ✅ Every grade result has a complete decision trace.
- ✅ Every grade result references a policy version.
- ✅ Every grade result references a model version.
- ✅ Manual review is triggered for low-confidence results.
- ✅ Unavailable is returned for missing data.
- ✅ Reason codes are present and meaningful.
- ✅ Lot-level percentages sum to 100%.

---

## Forbidden Behavior

- ❌ Using an LLM to determine grades.
- ❌ Hardcoding grades for specific images.
- ❌ Fabricating grade results.
- ❌ Scattering grading rules across multiple modules.
- ❌ Grading without a policy version reference.
- ❌ Skipping the decision trace.
- ❌ Silently modifying grading thresholds without policy version bump.
- ❌ Returning `GRADE_A` for an onion with detected defects.
- ❌ Returning `GRADE_A` without size verification (or documenting size as undetermined).
- ❌ Ignoring the `MANUAL_REVIEW` pathway.

---

## Expected Outputs

1. **Per-onion grade result** — structured `GradeResult` with full trace.
2. **Lot-level summary** — `LotGradeSummary` with percentages.
3. **Grading policy document** — versioned, configurable policy.
4. **Audit log entries** — for every grading decision.
5. **Manual review queue** — onions flagged for human inspection.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `computer-vision` | Provides structured observations (input) |
| `onion-measurement` | Provides size classification (input) |
| `ps26031-requirements` | Defines Grade A, URS, required defect types |
| `testing` | Grading policy tests are mandatory |
| `reporting-qr` | Consumes grade results for reports |
| `database-engineering` | Stores grade results and audit history |
