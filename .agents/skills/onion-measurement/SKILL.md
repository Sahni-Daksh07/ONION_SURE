---
name: onion-measurement
description: >-
  Governs physical size measurement of onions from images. Strictly requires
  calibration (ArUco marker, reference object, or known physical reference)
  for any pixel-to-mm conversion. Returns measurement_unavailable when
  calibration is absent. Activate when any task involves onion size, diameter,
  or undersized determination.
---

# Onion Measurement Skill

## Purpose

Ensure accurate, calibrated physical measurements of onions from images.
Physical size is critical for PS26031 undersized determination, but MUST NOT
be guessed from raw pixel counts without calibration.

## When to Use

- Estimating onion diameter or size from images.
- Determining if an onion is undersized.
- Implementing calibration workflows.
- Integrating measurement into the grading pipeline.
- Setting up reference marker detection.

## Required Inputs

- Onion image with visible calibration reference (ArUco marker, coin, ruler, etc.).
- Calibration configuration (reference object dimensions, camera parameters).
- OR explicit acknowledgment that calibration is unavailable.

---

## The Fundamental Rule

```
❌ FORBIDDEN:  pixel_count → diameter_mm  (without calibration)
❌ FORBIDDEN:  "this onion is 45mm"       (without calibration evidence)
❌ FORBIDDEN:  estimate_size(image)        (magic function without calibration)

✅ CORRECT:   calibrated_pixel_ratio → diameter_mm  (with documented method)
✅ CORRECT:   measurement_unavailable               (when no calibration)
✅ CORRECT:   relative_size_comparison               (comparing onions in same image)
```

---

## Calibration Methods

### Method 1: ArUco Marker (Recommended)

```
Image with ArUco marker
  → Detect ArUco marker corners
  → Calculate pixel-per-mm ratio from known marker size
  → Correct for perspective distortion
  → Apply ratio to onion bounding box / segmentation
  → Estimate diameter with confidence interval
```

Configuration:
```yaml
calibration:
  method: "aruco"
  marker_dictionary: "DICT_4X4_50"
  marker_id: 0
  marker_size_mm: 50.0
  perspective_correction: true
```

### Method 2: Known Physical Reference

```
Image with reference object (coin, ruler, card)
  → Detect reference object
  → Calculate pixel-per-mm ratio from known dimensions
  → Apply ratio to onion measurements
```

### Method 3: Fixed Camera Setup

```
Camera at known distance with known focal length
  → Pre-calibrated pixel-per-mm ratio
  → Apply ratio (valid only for this specific setup)
```

**Warning:** This method is fragile. Any change in camera position, zoom, or
distance invalidates the calibration.

---

## Measurement Output Format

Every measurement MUST follow this structure:

```python
@dataclass
class OnionMeasurement:
    measurement_id: str
    detection_id: str              # Links to OnionDetection
    status: str                    # "measured" | "measurement_unavailable"
    
    # Present only when status == "measured"
    diameter_mm: Optional[float]
    diameter_min_mm: Optional[float]   # Confidence interval lower bound
    diameter_max_mm: Optional[float]   # Confidence interval upper bound
    area_mm2: Optional[float]
    
    # Always present
    diameter_pixels: float             # Raw pixel measurement (always available)
    
    # Calibration info
    calibration_method: Optional[str]  # "aruco" | "reference_object" | "fixed_camera"
    calibration_confidence: Optional[float]  # 0.0 to 1.0
    pixels_per_mm: Optional[float]
    
    # Metadata
    unit: str                          # "mm"
    measurement_metadata: dict
```

### When Calibration is Unavailable

```python
OnionMeasurement(
    measurement_id="...",
    detection_id="...",
    status="measurement_unavailable",
    diameter_mm=None,
    diameter_min_mm=None,
    diameter_max_mm=None,
    area_mm2=None,
    diameter_pixels=150.0,  # Raw pixel value is always available
    calibration_method=None,
    calibration_confidence=None,
    pixels_per_mm=None,
    unit="mm",
    measurement_metadata={
        "reason": "No calibration reference detected in image",
        "recommendation": "Include ArUco marker in frame"
    }
)
```

---

## Undersized Determination

### With Calibration

```python
def is_undersized(measurement: OnionMeasurement, threshold_mm: float) -> str:
    if measurement.status == "measurement_unavailable":
        return "UNDETERMINED"
    if measurement.diameter_mm < threshold_mm:
        return "UNDERSIZED"
    return "ACCEPTABLE_SIZE"
```

### Without Calibration

```python
# Returns UNDETERMINED — never guess
return "UNDETERMINED"
```

### Configurable Thresholds

```yaml
size_thresholds:
  undersized_max_diameter_mm: 40.0    # Below this = undersized
  grade_a_min_diameter_mm: 50.0       # Above this = Grade A size
  policy_version: "1.0.0"
```

---

## Implementation Rules

1. **Never convert pixels to mm without calibration.** This is the primary rule.
2. **Always report calibration method and confidence.**
3. **Always provide confidence intervals** on physical measurements.
4. **Return `measurement_unavailable`** instead of guessing.
5. **Store raw pixel measurements** even when calibration is unavailable.
6. **Support multiple calibration methods** via configuration.
7. **Document the calibration setup** used for any measurement.
8. **Validate calibration quality** — reject if marker detection is unreliable.

---

## Validation Rules

- ✅ No measurement claims physical units without calibration evidence.
- ✅ Measurement output follows the structured format.
- ✅ Confidence intervals are provided for calibrated measurements.
- ✅ `measurement_unavailable` is returned when calibration is absent.
- ✅ Calibration method is documented in every measurement.
- ✅ Pixel-to-mm ratio is validated (sanity check on reasonable values).

---

## Forbidden Behavior

- ❌ Converting raw pixel counts to millimeters without calibration.
- ❌ Claiming an onion is undersized without calibrated measurement.
- ❌ Fabricating measurement values.
- ❌ Using a magic constant for pixel-to-mm conversion.
- ❌ Ignoring perspective distortion when a marker is available.
- ❌ Reporting measurements without confidence intervals.

---

## Expected Outputs

1. **Calibration report** — detected reference, pixel-per-mm ratio, confidence.
2. **Measurement results** — structured `OnionMeasurement` objects.
3. **Size classification** — undersized / acceptable / undetermined.
4. **Measurement visualization** — annotated image showing measurement overlay.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `computer-vision` | Provides onion detection and segmentation |
| `grading-engine` | Consumes size classification for grading |
| `ps26031-requirements` | Defines undersized threshold requirements |
| `ml-training-evaluation` | Evaluates measurement error metric |
