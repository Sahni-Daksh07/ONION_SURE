---
name: dataset-engineering
description: >-
  Manages the onion image dataset lifecycle: inspection, cleaning, corruption
  detection, duplicate detection, class distribution analysis, quality metrics,
  train/val/test splitting, annotation management, versioning, and leakage
  prevention. Critically, this skill prohibits fabricating labels — existing
  Healthy/Unhealthy labels must NOT be silently converted to PS26031-specific
  defect types without evidence. Activate for any dataset-related task.
---

# Dataset Engineering Skill

## Purpose

Manage the ONION_SURE image dataset with rigorous engineering discipline.
Ensure data quality, prevent leakage, maintain provenance, and correctly
identify annotation gaps required for PS26031 compliance.

## When to Use

- Inspecting or analyzing the existing dataset.
- Cleaning, filtering, or validating images.
- Creating train/validation/test splits.
- Detecting duplicates or corrupted images.
- Managing annotations or labels.
- Versioning dataset changes.
- Preparing data for model training.
- Auditing dataset quality.

## Required Inputs

- Path to the dataset directory (default: `Red and White Onion Dataset/`).
- Task specification (inspect, clean, split, annotate, version, etc.).

---

## Current Dataset Structure

```
Red and White Onion Dataset/        ← SOURCE DATA — DO NOT MODIFY
└── New Onion/
    ├── Bulb/
    │   ├── Healthy/      # ~12,367 images
    │   └── Unhealthy/    # ~5,461 images
    └── Leaves/
        ├── Healthy/      # ~3,104 images
        └── Unhealthy/    # ~3,068 images
```

**Total:** ~24,000 JPG images (~2.34 GB)

---

## Critical Label Mapping Warning

### Existing Labels

The dataset has TWO labels per category:
- `Healthy`
- `Unhealthy`

### PS26031 Required Labels

PS26031 requires SPECIFIC defect identification:
- `healthy`
- `damaged`
- `rotten`
- `sprouted`
- `undersized` (requires physical measurement)
- `unknown/other`

### THE RULE

```
❌ FORBIDDEN: Healthy → healthy, Unhealthy → rotten  (automatic mapping)
❌ FORBIDDEN: Unhealthy → damaged  (assumption without evidence)
❌ FORBIDDEN: Unhealthy → sprouted  (assumption without evidence)

✅ CORRECT: Healthy → healthy  (reasonable mapping)
✅ CORRECT: Unhealthy → needs_manual_annotation  (honest assessment)
✅ CORRECT: Unhealthy images individually reviewed → specific defect label
```

The `Unhealthy` label is a SUPERSET that may contain damaged, rotten, sprouted,
and other conditions. These sub-categories MUST be identified through:

1. Manual annotation by domain experts, OR
2. Visual inspection and evidence-based labeling, OR
3. A separate annotation pipeline with quality control.

**Never fabricate fine-grained labels from coarse labels.**

---

## Workflow

### 1. Dataset Inspection

```
→ Count images per class
→ Verify file integrity (readable, valid JPG)
→ Measure image dimensions (width × height distribution)
→ Analyze image quality metrics
→ Detect corrupted files
→ Generate inspection report
```

### 2. Quality Analysis

| Metric | Description |
|:---|:---|
| **Corruption** | Files that cannot be opened/decoded |
| **Dimensions** | Width × height distribution, outliers |
| **Brightness** | Mean pixel intensity, over/under-exposed |
| **Blur** | Laplacian variance, out-of-focus detection |
| **Color** | Color channel statistics, grayscale detection |
| **File size** | Anomalously small or large files |

### 3. Duplicate Detection

- **Exact duplicates:** File hash (MD5/SHA256) comparison.
- **Perceptual duplicates:** Perceptual hashing (pHash, dHash) with threshold.
- **Near-duplicates:** Feature similarity (optional, resource-intensive).
- Duplicates must be flagged, not silently deleted.

### 4. Train/Validation/Test Splitting

| Split | Proportion | Purpose |
|:---|:---|:---|
| **Train** | ~70% | Model training |
| **Validation** | ~15% | Hyperparameter tuning, early stopping |
| **Test** | ~15% | Final evaluation ONLY |

**Splitting Rules:**

- Stratified by class to maintain distribution.
- Split at the image level (no augmented variants across splits).
- Test set is FROZEN after creation — never used for training or tuning.
- Split assignments recorded in a manifest file.
- Random seed must be fixed and documented for reproducibility.

### 5. Leakage Prevention

- ✅ No image appears in more than one split.
- ✅ Augmented versions of a training image never appear in validation or test.
- ✅ Split manifest is version-controlled.
- ✅ Test set is never used for hyperparameter decisions.

### 6. Dataset Manifest

Every processed dataset version must have a manifest:

```json
{
  "dataset_version": "1.0.0",
  "created_at": "2026-XX-XXTXX:XX:XXZ",
  "source": "Red and White Onion Dataset/New Onion/",
  "total_images": 24000,
  "splits": {
    "train": { "count": 16800, "path": "data/splits/train/" },
    "val": { "count": 3600, "path": "data/splits/val/" },
    "test": { "count": 3600, "path": "data/splits/test/" }
  },
  "class_distribution": { ... },
  "random_seed": 42,
  "excluded_images": [ ... ],
  "corruption_report": "data/reports/corruption.json",
  "duplicate_report": "data/reports/duplicates.json"
}
```

### 7. Annotation Management

When PS26031-specific annotations are created:

- Store annotations separately from original images.
- Use a structured format (JSON, COCO, or similar).
- Track annotator, date, and confidence.
- Support multi-label annotations (an onion can be both damaged AND sprouted).
- Version annotations independently from the dataset.

### 8. Dataset Versioning

- Use semantic versioning: `MAJOR.MINOR.PATCH`.
- MAJOR: New annotation scheme or significant restructuring.
- MINOR: New images added, classes added.
- PATCH: Bug fixes, corrupt image removal, metadata corrections.

---

## Implementation Rules

1. **Never modify the source dataset.** All derived data goes to `data/` or equivalent.
2. **Never fabricate labels.** See the Critical Label Mapping Warning above.
3. **Always verify file integrity** before including images in splits.
4. **Always use stratified splitting** to maintain class balance.
5. **Always fix random seeds** for reproducibility.
6. **Always generate a manifest** for every dataset version.
7. **Store split assignments** in a version-controlled file, not just in memory.

---

## Validation Rules

- ✅ Source dataset (`Red and White Onion Dataset/`) is unmodified.
- ✅ No image appears in multiple splits.
- ✅ Class distribution is documented.
- ✅ Corrupted images are excluded and documented.
- ✅ Duplicates are flagged and documented.
- ✅ Labels match actual evidence (no fabrication).
- ✅ Manifest exists for every dataset version.
- ✅ Random seed is documented.

---

## Forbidden Behavior

- ❌ Modifying or deleting the original `Red and White Onion Dataset/` directory.
- ❌ Automatically converting `Unhealthy` → specific defect type without evidence.
- ❌ Fabricating annotation labels.
- ❌ Using test set images for training or hyperparameter tuning.
- ❌ Creating splits without a manifest.
- ❌ Deleting images without documentation.
- ❌ Ignoring corrupted or unreadable images (they must be flagged and excluded).

---

## Expected Outputs

1. **Inspection report** — image counts, dimensions, quality metrics.
2. **Corruption report** — list of unreadable/corrupted files.
3. **Duplicate report** — exact and perceptual duplicates.
4. **Split manifest** — train/val/test assignments with metadata.
5. **Annotation gap report** — what PS26031 labels are missing.
6. **Dataset version record** — version, provenance, configuration.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `ps26031-requirements` | Defines required label categories |
| `ml-training-evaluation` | Consumes prepared splits for training |
| `repository-audit` | Verifies dataset integrity during audits |
