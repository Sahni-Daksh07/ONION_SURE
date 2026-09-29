---
name: ml-training-evaluation
description: >-
  Governs all ML training pipelines, evaluation, experiment tracking, model
  versioning, reproducibility, and metrics for ONION_SURE. Enforces train/test
  isolation, requires comprehensive metrics (confusion matrix, precision,
  recall, F1, mAP), and mandates model artifacts with full provenance.
  Activate for any model training, evaluation, or experiment task.
---

# ML Training and Evaluation Skill

## Purpose

Ensure rigorous, reproducible machine learning workflows for onion quality
assessment models. Every model must be traceable from dataset to deployment.

## When to Use

- Training any ML model (classification, detection, segmentation).
- Evaluating model performance.
- Comparing model versions.
- Setting up experiment tracking.
- Creating training pipelines.
- Validating model readiness for deployment.

## Required Inputs

- Prepared dataset with manifest (from `dataset-engineering` skill).
- Training configuration (architecture, hyperparameters, augmentation).
- Evaluation criteria (metrics, thresholds).

---

## Training Pipeline Architecture

```
Dataset (versioned, split)
  → Data Loading & Augmentation
  → Model Architecture Selection
  → Training Loop
      → Training metrics logging
      → Validation metrics per epoch
      → Checkpoint saving
  → Best Model Selection
  → Test Set Evaluation (FINAL, one-time)
  → Model Artifact Packaging
  → Model Card Generation
```

---

## Experiment Configuration

Every training run MUST have a complete configuration:

```yaml
experiment:
  name: "onion_defect_classifier_v1"
  description: "EfficientNet-B0 classifier for onion defect detection"
  date: "2026-XX-XX"
  author: "team_member"

dataset:
  version: "1.0.0"
  manifest_path: "data/manifests/v1.0.0.json"
  train_count: 16800
  val_count: 3600
  test_count: 3600
  classes: ["HEALTHY", "DAMAGED", "ROTTEN", "SPROUTED", "UNKNOWN"]

model:
  architecture: "efficientnet_b0"
  pretrained: true
  pretrained_source: "imagenet"
  num_classes: 5
  input_size: [224, 224]

training:
  optimizer: "adamw"
  learning_rate: 0.001
  weight_decay: 0.01
  scheduler: "cosine_annealing"
  epochs: 50
  batch_size: 32
  early_stopping_patience: 10
  random_seed: 42

augmentation:
  horizontal_flip: true
  vertical_flip: false
  rotation_range: 15
  color_jitter: { brightness: 0.2, contrast: 0.2, saturation: 0.2 }
  normalize:
    mean: [0.485, 0.456, 0.406]
    std: [0.229, 0.224, 0.225]

environment:
  python_version: "3.10"
  pytorch_version: "2.x"
  gpu: "NVIDIA T4"  # or whatever is used
  cuda_version: "12.x"
```

---

## Required Metrics

### Classification Metrics (per-class AND overall)

| Metric | Required | Description |
|:---|:---|:---|
| **Accuracy** | ✅ | Overall correct predictions / total |
| **Precision** | ✅ | Per-class: TP / (TP + FP) |
| **Recall** | ✅ | Per-class: TP / (TP + FN) |
| **F1 Score** | ✅ | Per-class: harmonic mean of precision & recall |
| **Confusion Matrix** | ✅ | Full N×N matrix |
| **ROC-AUC** | Optional | Per-class area under ROC curve |
| **PR-AUC** | Optional | Per-class area under precision-recall curve |

### Detection Metrics (if using detection model)

| Metric | Required | Description |
|:---|:---|:---|
| **mAP@0.5** | ✅ | Mean average precision at IoU 0.5 |
| **mAP@0.5:0.95** | ✅ | Mean average precision at IoU range |
| **Per-class AP** | ✅ | Average precision per defect class |

### PS26031-Specific Metrics

| Metric | Required | Description |
|:---|:---|:---|
| **Grading Agreement** | ✅ | Agreement between AI grade and human grade |
| **Measurement Error** | ✅ | Error in size estimation vs ground truth |
| **False Reject Rate** | ✅ | Healthy onions incorrectly classified as defective |
| **False Accept Rate** | ✅ | Defective onions incorrectly classified as healthy |

---

## Leakage Prevention (Critical)

### ABSOLUTE RULES

1. **Test set is NEVER used during training or hyperparameter tuning.**
2. **Augmented variants of training images NEVER appear in validation or test.**
3. **Validation set is used for hyperparameter tuning and early stopping ONLY.**
4. **Test set evaluation happens ONCE per model version — for final reporting.**
5. **Split assignments are loaded from the dataset manifest, not regenerated.**

### Leakage Detection Checklist

Before every training run, verify:

- [ ] Train/val/test splits loaded from manifest (not randomly re-split).
- [ ] No image ID appears in more than one split.
- [ ] Augmentation is applied ONLY to training data.
- [ ] Validation metrics are NOT used to modify training data.
- [ ] Test set has not been previously used for this model version.

---

## Model Artifact Package

Every trained model MUST produce:

```
models/
└── <model_name>_v<version>/
    ├── model.pt                  # PyTorch checkpoint
    ├── model.onnx                # ONNX export (for deployment)
    ├── model.tflite              # TFLite export (for mobile, if applicable)
    ├── config.yaml               # Full training configuration
    ├── classes.json              # Class name → index mapping
    ├── preprocessing.yaml        # Exact preprocessing pipeline
    ├── evaluation_results.json   # All metrics on test set
    ├── confusion_matrix.png      # Visualization
    ├── training_curves.png       # Loss and accuracy curves
    ├── model_card.md             # Human-readable model documentation
    └── checksum.sha256           # Integrity verification
```

---

## Model Versioning

Use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR:** New architecture, new class set, breaking API change.
- **MINOR:** Retraining with new data, hyperparameter changes, improved metrics.
- **PATCH:** Bug fixes, minor preprocessing adjustments.

Every model version must record:

- Dataset version used for training.
- Previous model version (if this is an iteration).
- Reason for new version.
- Comparison with previous version's metrics.

---

## Implementation Rules

1. **Fix all random seeds** — Python, NumPy, PyTorch, CUDA.
2. **Log all hyperparameters** — nothing should be undocumented.
3. **Save checkpoints** — at minimum, best validation and last epoch.
4. **Export to ONNX/TFLite** — for deployment compatibility.
5. **Evaluate on test set only once** per model version.
6. **Compare with previous version** — quantify improvement or regression.
7. **Document negative results** — models that didn't work are also valuable.
8. **Use reproducible data loading** — deterministic shuffling with fixed seed.

---

## Validation Rules

- ✅ Training configuration is complete and documented.
- ✅ Dataset version is recorded.
- ✅ No train/test leakage detected.
- ✅ All required metrics are computed and saved.
- ✅ Confusion matrix is generated.
- ✅ Model artifact package is complete.
- ✅ Model card is written.
- ✅ Random seeds are fixed and documented.

---

## Forbidden Behavior

- ❌ Training on test data.
- ❌ Tuning hyperparameters using test metrics.
- ❌ Fabricating evaluation metrics.
- ❌ Deploying a model without evaluation results.
- ❌ Using non-deterministic data loading without documenting the seed.
- ❌ Overwriting a previous model version without incrementing the version.
- ❌ Claiming model performance without evidence.
- ❌ Ignoring class imbalance without documentation.

---

## Expected Outputs

1. **Trained model artifact** — complete package as specified above.
2. **Evaluation report** — all metrics on the test set.
3. **Training log** — loss curves, validation metrics per epoch.
4. **Model card** — human-readable documentation.
5. **Comparison report** — vs. previous model version (if applicable).

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `dataset-engineering` | Provides versioned, split datasets |
| `computer-vision` | Defines model architecture and inference format |
| `grading-engine` | Evaluates grading agreement metric |
| `onion-measurement` | Evaluates measurement error metric |
| `testing` | ML evaluation tests |
