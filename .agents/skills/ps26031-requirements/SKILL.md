---
name: ps26031-requirements
description: >-
  Keeps every development decision aligned with Smart India Hackathon 2026
  Problem Statement PS26031. Defines mandatory MVP scope, PS26031-specific
  concepts (Grade A, URS, defect types), and prevents scope creep into
  unrelated features. Activate this skill before any architectural decision,
  feature addition, or scope discussion.
---

# PS26031 Requirements Skill

## Purpose

Ensure that every development decision, feature, and architectural choice is
aligned with Problem Statement PS26031: AI-based quality assessment and grading
of onions for the Ministry of Consumer Affairs, Food & Public Distribution.

## When to Use

- Before adding any new feature — verify it is required by PS26031.
- Before any architectural decision — check alignment with the core workflow.
- When discussing scope — distinguish MVP from future features.
- When reviewing PRs — ensure changes serve PS26031.
- When prioritizing work — MVP items come first.

## Required Inputs

- The proposed feature, change, or decision to evaluate.
- Current implementation status (from `repository-audit` skill).

---

## PS26031 Problem Statement

**ID:** 26031

**Problem:** Quality assessment and grading of onions are often subjective and
vary across procurement centers, resulting in disputes and inconsistencies.

**Expected Solution:** Develop an AI-based mobile application that:

1. Uses image processing to assess onion quality.
2. Identifies damaged, rotten, sprouted, or undersized onions.
3. Estimates Grade A and URS percentages.
4. Generates a digital quality report instantly.
5. Reduces human bias and improves transparency.

**Organization:** Ministry of Consumer Affairs, Food & Public Distribution  
**Department:** Department of Consumer Affairs (DoCA)  
**Category:** Software  
**Theme:** Smart Automation

---

## Core MVP Workflow

The minimum viable product must implement this end-to-end workflow:

```
Image Capture
  → Image Validation (quality, blur, lighting)
  → Onion Detection (localize onions in image)
  → Defect Identification (damaged, rotten, sprouted, healthy)
  → Size Assessment (undersized detection with calibration)
  → Grading (deterministic: Grade A, URS, Reject, Manual Review)
  → Lot-level Percentages (Grade A %, URS %, Reject %)
  → Human Review (where confidence is low or evidence conflicts)
  → Digital Quality Report (PDF, unique ID, QR code)
  → Verification / Auditability (QR scan → verify report)
```

---

## PS26031 Concepts

### Defect Types (Mandatory)

| Defect | Description | PS26031 Reference |
|:---|:---|:---|
| **Damaged** | Physical damage: cuts, bruises, compression marks | Explicitly required |
| **Rotten** | Decay, fungal/bacterial rot, soft spots | Explicitly required |
| **Sprouted** | Visible sprout growth from the bulb | Explicitly required |
| **Undersized** | Below minimum diameter threshold (requires calibration) | Explicitly required |
| **Healthy** | No visible defects, meets size requirements | Implied baseline |

### Grading Categories (Mandatory)

| Grade | Description |
|:---|:---|
| **Grade A** | Meets all quality criteria: healthy, properly sized, no defects |
| **URS (Under Relaxed Specifications)** | Minor defects but still acceptable under relaxed criteria |
| **Reject** | Does not meet minimum quality — rotten, severely damaged, etc. |
| **Manual Review** | AI confidence too low for automated grading |
| **Unavailable** | Measurement or classification could not be completed |

### Percentage Estimation

- Per-lot Grade A percentage
- Per-lot URS percentage
- Per-lot Reject percentage
- Defect distribution breakdown
- Size distribution breakdown

### Digital Report Requirements

- Unique Report ID
- Inspection metadata (date, time, location, operator)
- Sample composition and size
- Grade percentages with evidence
- Model version and grading policy version
- QR code for independent verification
- PDF generation

### Transparency Requirements

- Every grade must have a traceable reason.
- Every AI prediction must include confidence.
- Every measurement must include calibration status.
- Human review must be logged.
- Grading policy must be versioned and auditable.

---

## Mandatory MVP Features

These MUST be implemented:

1. **Mobile image capture** with quality validation
2. **Onion detection** in captured images
3. **Defect classification** (damaged, rotten, sprouted, healthy)
4. **Size assessment** (with calibration requirement)
5. **Deterministic grading engine** (not LLM-based)
6. **Lot-level percentage calculation** (Grade A%, URS%, Reject%)
7. **Human review workflow** for low-confidence results
8. **Digital quality report** with unique ID
9. **QR code** for report verification
10. **Offline capability** for field use without connectivity
11. **User authentication** and role-based access
12. **Audit trail** for all grading decisions

---

## NOT MVP — Forbidden Unless Explicitly Requested

Do NOT implement these during MVP development:

- ❌ Marketplace / auction features
- ❌ Payment / billing processing
- ❌ Logistics / supply chain tracking
- ❌ Insurance integration
- ❌ Weather data integration
- ❌ Price prediction / forecasting
- ❌ Blockchain / distributed ledger
- ❌ Social features / messaging
- ❌ Gamification
- ❌ Multi-crop support (onions only for PS26031)
- ❌ International market features
- ❌ Consumer-facing features (PS26031 is procurement-focused)

---

## Validation Rules

Before accepting any feature or change:

1. ✅ Does this feature directly serve the PS26031 workflow?
2. ✅ Is this feature in the Mandatory MVP list?
3. ✅ Does this maintain the deterministic grading architecture?
4. ✅ Does this preserve auditability and transparency?
5. ✅ Does this work offline for field deployment?

If any answer is NO, the feature should be deferred or rejected.

---

## Forbidden Behavior

- ❌ Adding features unrelated to PS26031 without explicit user approval.
- ❌ Replacing deterministic grading with LLM-based grading.
- ❌ Claiming PS26031 compliance without implementing the core workflow.
- ❌ Skipping defect types required by PS26031.
- ❌ Omitting percentage estimation from the grading output.
- ❌ Generating reports without unique verification IDs.
- ❌ Ignoring the transparency requirement.

---

## Expected Outputs

When this skill is activated, produce:

1. **Feature alignment assessment** — does the proposed work serve PS26031?
2. **MVP priority** — is this mandatory or deferrable?
3. **Missing MVP items** — what required features are still unimplemented?
4. **Scope warning** — flag any scope creep toward non-PS26031 features.
5. **Recommendation** — proceed, defer, or reject with justification.
