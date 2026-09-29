---
name: computer-vision
description: >-
  Governs all computer vision tasks for ONION_SURE: onion detection,
  segmentation, defect detection/classification, image preprocessing, quality
  validation, confidence estimation, inference, and visualization. Requires
  confidence scores on every prediction and prohibits fabricating results.
  Activate for any CV, detection, classification, or image analysis task.
---

# Computer Vision Skill

## Purpose

Define and enforce the computer vision architecture for onion quality
assessment. All CV components must produce structured, confidence-scored
outputs that feed into the deterministic grading engine.

## When to Use

- Building or modifying onion detection models.
- Building or modifying defect classification models.
- Implementing image preprocessing pipelines.
- Implementing image quality validation.
- Running inference on onion images.
- Integrating CV models into the backend or mobile app.
- Visualizing detection/classification results.

## Required Inputs

- Onion image(s) for processing.
- Model artifacts (weights, configuration) for inference.
- Task specification (detect, classify, segment, preprocess, validate).

---

## CV Pipeline Architecture

```
Raw Image
  → Image Quality Validation
      → Pass/Fail (blur, exposure, resolution)
  → Preprocessing
      → Normalization, resizing, color correction
  → Onion Detection
      → Bounding boxes with confidence scores
  → Per-Onion Processing
      → Defect Classification (with confidence)
      → Segmentation (optional, for measurement)
  → Structured Observations
      → Detection results, defect labels, confidence, metadata
  → [Grading Engine] (separate skill)
```

---

## Defect Categories

### Initial Categories (MVP)

| Category | Code | Description |
|:---|:---|:---|
| Healthy | `HEALTHY` | No visible defects |
| Damaged | `DAMAGED` | Cuts, bruises, compression marks |
| Rotten | `ROTTEN` | Decay, fungal/bacterial rot, soft spots |
| Sprouted | `SPROUTED` | Visible sprout growth |
| Unknown | `UNKNOWN` | Cannot classify with sufficient confidence |

### Extensibility Requirement

The architecture MUST support adding new defect classes without restructuring:

- Use a configurable class registry (not hardcoded if/else chains).
- Model output dimension should be configurable.
- Grading engine must handle unknown/new categories gracefully.

---

## Structured Observation Format

Every CV inference result MUST produce a structured observation:

```python
@dataclass
class OnionDetection:
    detection_id: str
    image_id: str
    bounding_box: BoundingBox        # x, y, width, height (normalized or pixel)
    detection_confidence: float      # 0.0 to 1.0
    defect_class: str                # HEALTHY, DAMAGED, ROTTEN, SPROUTED, UNKNOWN
    defect_confidence: float         # 0.0 to 1.0
    all_class_probabilities: dict    # {class_name: probability}
    segmentation_mask: Optional[...]  # If segmentation is available
    model_version: str               # Model that produced this result
    inference_timestamp: str          # ISO 8601
    metadata: dict                   # Additional info (preprocessing params, etc.)
```

### Mandatory Fields

Every detection MUST include:

- `detection_confidence` — how certain the model is that this is an onion.
- `defect_confidence` — how certain the model is about the defect classification.
- `model_version` — which model version produced this result.
- `all_class_probabilities` — full probability distribution across all classes.

---

## Image Quality Validation

Before running inference, validate:

| Check | Criteria | Action on Fail |
|:---|:---|:---|
| **Resolution** | Minimum 224×224 (configurable) | Reject with message |
| **Blur** | Laplacian variance > threshold | Warn or reject |
| **Exposure** | Mean brightness within range | Warn or reject |
| **Format** | Valid JPEG/PNG | Reject |
| **File Size** | Within upload limits | Reject |

Return a structured quality report:

```python
@dataclass
class ImageQualityReport:
    image_id: str
    is_acceptable: bool
    resolution: Tuple[int, int]
    blur_score: float
    brightness_score: float
    issues: List[str]
```

---

## Model Integration Requirements

### Model Artifacts

Every deployed model must have:

```
models/
└── v1.0.0/
    ├── model.onnx          # or .pt, .tflite
    ├── config.yaml         # Model configuration
    ├── classes.json         # Class names and indices
    ├── preprocessing.yaml  # Preprocessing parameters
    ├── evaluation.json     # Evaluation metrics on test set
    └── README.md           # Model card
```

### Model Card (README.md)

Every model must have a model card documenting:

- Model architecture
- Training dataset version
- Training configuration
- Evaluation metrics (per-class precision, recall, F1)
- Known limitations
- Input requirements
- Output format

### Inference Configuration

```yaml
model_version: "1.0.0"
input_size: [224, 224]
normalization:
  mean: [0.485, 0.456, 0.406]
  std: [0.229, 0.224, 0.225]
confidence_threshold: 0.5
nms_threshold: 0.45  # If using detection model
classes: ["HEALTHY", "DAMAGED", "ROTTEN", "SPROUTED", "UNKNOWN"]
```

---

## Implementation Rules

1. **Every prediction includes confidence.** No exceptions.
2. **Full probability distribution is preserved.** Not just the top class.
3. **Model version is tagged on every result.** For auditability.
4. **Image quality is validated before inference.** Bad images are rejected early.
5. **Preprocessing is deterministic and documented.** Same input → same preprocessing.
6. **New defect classes can be added via configuration.** Not code changes.
7. **Inference is separate from grading.** CV produces observations; grading engine produces grades.
8. **ONNX or TFLite for deployment.** Ensure cross-platform compatibility.
9. **Batch inference is supported.** For lot-level processing.

---

## Validation Rules

- ✅ Every detection result has a confidence score.
- ✅ Every detection result has a model version.
- ✅ Image quality is checked before inference.
- ✅ Class probabilities sum to ~1.0.
- ✅ Results use the structured observation format.
- ✅ Model artifacts include evaluation metrics.
- ✅ Preprocessing parameters are documented and versioned.

---

## Forbidden Behavior

- ❌ Fabricating predictions or confidence scores.
- ❌ Returning hard labels without confidence.
- ❌ Using a model without documented evaluation metrics.
- ❌ Hardcoding class names in inference code (use configuration).
- ❌ Running inference without image quality validation.
- ❌ Coupling CV inference logic with grading logic.
- ❌ Deploying a model without a model card.
- ❌ Using different preprocessing in training vs inference.

---

## Expected Outputs

1. **Structured detections** — list of `OnionDetection` objects per image.
2. **Image quality report** — pass/fail with metrics.
3. **Visualization** — annotated images showing detections and labels.
4. **Model card** — documentation for every model version.
5. **Inference configuration** — reproducible inference parameters.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `dataset-engineering` | Provides training/evaluation data |
| `ml-training-evaluation` | Trains and evaluates models |
| `onion-measurement` | Uses segmentation for size estimation |
| `grading-engine` | Consumes structured observations |
| `ps26031-requirements` | Defines required defect categories |
