---
name: demo-validation
description: >-
  Validates that the ONION_SURE demo proves the actual PS26031 workflow using
  real inference and data. Defines the minimum demo flow from login through
  report generation and QR verification. Prohibits hiding missing functionality
  behind fake UI. Activate before any demo, presentation, or evaluation.
---

# Demo Validation Skill

## Purpose

Ensure that the ONION_SURE demo authentically demonstrates the PS26031
workflow using real AI inference and data. The demo must prove the system
works, not just look like it works.

## When to Use

- Preparing for hackathon demo or presentation.
- Validating demo readiness.
- Rehearsing the demo flow.
- Identifying demo gaps.
- Building demo-specific tooling (scripts, sample data).

## Required Inputs

- Current implementation status (from `repository-audit`).
- Demo environment setup.
- Sample data for demonstration.

---

## Minimum Demo Flow

The demo MUST demonstrate this complete PS26031 workflow:

```
Step 1: LOGIN
  → Operator authenticates
  → Dashboard loads

Step 2: CREATE INSPECTION
  → Select/create farmer
  → Select/create lot
  → Start new inspection

Step 3: CAPTURE ONION IMAGE
  → Open camera
  → Capture image of onion(s)
  → Image quality validation (pass/fail feedback)

Step 4: AI DETECTION
  → Submit image for AI processing
  → Show detection results (bounding boxes on onions)
  → Show confidence scores

Step 5: DEFECT DETECTION
  → Per-onion defect classification
  → Show defect type and confidence
  → Show probability distribution

Step 6: SIZE ASSESSMENT
  → Size measurement (with calibration, or "unavailable")
  → Show measurement result and method

Step 7: GRADING
  → Deterministic grading applied
  → Show grade (Grade A, URS, Reject, Manual Review)
  → Show reason codes and decision trace

Step 8: LOT SUMMARY
  → Grade A percentage
  → URS percentage
  → Reject percentage
  → Defect distribution
  → Size distribution

Step 9: REVIEW (if applicable)
  → Show manual review queue for low-confidence items
  → Demonstrate review override with reason

Step 10: REPORT GENERATION
  → Generate digital quality report
  → Show report with all mandatory fields
  → Generate PDF

Step 11: QR VERIFICATION
  → Show QR code on report
  → Scan QR code
  → Verify report authenticity
  → Show verification result
```

---

## Demo Integrity Rules

### What MUST Be Real

| Component | Requirement |
|:---|:---|
| **AI Detection** | Real model inference on the captured image |
| **Defect Classification** | Real model prediction with confidence |
| **Grading** | Real deterministic engine with decision trace |
| **Percentages** | Calculated from actual AI results |
| **Report** | Generated from actual inspection data |
| **QR Verification** | Actually verifies against stored report |

### What CAN Be Simulated

| Component | Condition |
|:---|:---|
| **Farmer/Lot data** | Pre-populated sample data is acceptable |
| **Network conditions** | Can demonstrate offline mode with airplane mode |
| **Multiple onions** | Can process multiple images sequentially |

### What MUST NOT Be Faked

```
❌ Pre-determined AI results that ignore the actual image
❌ Hardcoded grading outcomes
❌ Fabricated percentage values
❌ Fake QR verification (always returns "valid")
❌ Mock API responses in the demo path
❌ Hidden buttons that skip to results
❌ Pre-generated reports that don't match the inspection
```

---

## Demo Preparation Checklist

### Environment

- [ ] Backend server running and healthy
- [ ] Database migrated and seeded with sample data
- [ ] AI model loaded and ready for inference
- [ ] Flutter app installed on demo device
- [ ] Network connectivity verified (or offline mode ready)
- [ ] Camera permissions granted

### Data

- [ ] Sample farmer and lot records exist
- [ ] Onion images available for demo (or real onions for live demo)
- [ ] ArUco marker available (if demonstrating calibrated measurement)

### Functionality

- [ ] Login works with demo credentials
- [ ] Image capture and upload work
- [ ] AI inference completes within acceptable time
- [ ] Grading produces correct results for known inputs
- [ ] Report generates successfully
- [ ] QR verification works end-to-end
- [ ] Offline mode works (if demonstrating)

### Fallbacks

- [ ] What to do if AI inference is slow?
- [ ] What to do if camera doesn't work?
- [ ] What to do if network drops?
- [ ] What to show if something fails? (honest error, not hidden)

---

## Demo Script Template

### Opening (1 min)

"ONION_SURE is an AI-based mobile application that solves PS26031 — reducing
subjectivity in onion quality assessment at procurement centers."

### Problem (1 min)

"Currently, onion grading varies across procurement centers, leading to
disputes. Our system uses computer vision and deterministic grading to
provide transparent, verifiable quality reports."

### Live Demo (5-7 min)

Walk through Steps 1–11 above with real interaction.

### Architecture (1-2 min)

"The system uses [model architecture] for detection, a deterministic grading
engine (not AI-based grading), and generates verifiable digital reports."

### Closing (1 min)

"Key differentiators: deterministic grading, calibrated measurement,
offline capability, QR verification, full audit trail."

---

## Known Limitation Disclosure

During the demo, be transparent about:

- What features are fully implemented.
- What features are in progress.
- What measurements require calibration.
- What the AI model's actual accuracy is.
- What defect types the model currently handles.

```
✅ "Our model currently classifies healthy vs unhealthy with X% accuracy.
   We are expanding to specific defect types."

❌ "Our system perfectly identifies all defect types with 99% accuracy."
   (if this is not true)
```

---

## Validation Rules

- ✅ Every demo step uses real functionality (not mocked).
- ✅ AI inference runs on the actual captured image.
- ✅ Grading follows the deterministic engine.
- ✅ Report contains actual inspection data.
- ✅ QR verification validates against stored data.
- ✅ Known limitations are disclosed honestly.
- ✅ Demo script is rehearsed.

---

## Forbidden Behavior

- ❌ Demonstrating fake AI results.
- ❌ Hiding errors behind polished UI.
- ❌ Claiming features exist that are not implemented.
- ❌ Using pre-baked results instead of live inference.
- ❌ Fabricating accuracy or performance claims.
- ❌ Skipping broken features without acknowledgment.
- ❌ Showing a video recording instead of live demo (unless explicitly allowed).

---

## Expected Outputs

1. **Demo readiness report** — all checklist items verified.
2. **Demo script** — step-by-step narration.
3. **Known limitations document** — honest capability assessment.
4. **Fallback plan** — what to do if something breaks.
5. **Q&A preparation** — anticipated questions and answers.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `ps26031-requirements` | Demo must cover PS26031 workflow |
| `computer-vision` | AI detection and classification |
| `grading-engine` | Deterministic grading |
| `onion-measurement` | Size assessment |
| `reporting-qr` | Report and QR verification |
| `flutter-mobile` | Mobile app demo |
| `fastapi-backend` | Backend services |
| `testing` | Pre-demo validation tests |
| `documentation` | Demo guide |
