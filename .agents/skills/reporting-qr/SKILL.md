---
name: reporting-qr
description: >-
  Governs quality report generation, PDF creation, QR code verification, and
  report content standards for ONION_SURE. Reports must include all PS26031
  required fields, model/policy versions, and a QR code for independent
  verification that does not expose private information. Activate for any
  report, PDF, or QR verification task.
---

# Reporting and QR Verification Skill

## Purpose

Define the report generation, content standards, PDF creation, and QR code
verification system for ONION_SURE quality inspection reports.

## When to Use

- Generating quality inspection reports.
- Creating PDF documents.
- Implementing QR code generation.
- Implementing QR code verification.
- Defining report templates.
- Testing report accuracy.

## Required Inputs

- Completed inspection with grading results (from `grading-engine`).
- Lot and farmer metadata.
- Model and policy version information.

---

## Report Content Requirements

### Mandatory Fields

Every quality report MUST contain:

| Field | Description | Source |
|:---|:---|:---|
| **Report ID** | Unique report identifier (UUID) | Generated |
| **Inspection ID** | Linked inspection | Inspection entity |
| **Lot ID** | Onion lot/batch identifier | Lot entity |
| **Farmer** | Farmer/supplier name and ID | Farmer entity |
| **Procurement Centre** | Center name and location | Centre entity |
| **Operator** | Inspector who performed the assessment | User entity |
| **Date/Time** | Inspection timestamp (ISO 8601) | Inspection entity |
| **Sample Size** | Number of onions assessed | Inspection |
| **Grade A %** | Percentage of Grade A onions | LotGradeSummary |
| **URS %** | Percentage of URS onions | LotGradeSummary |
| **Reject %** | Percentage of rejected onions | LotGradeSummary |
| **Defect Distribution** | Breakdown by defect type | LotGradeSummary |
| **Size Distribution** | Breakdown by size category | LotGradeSummary |
| **Model Version** | AI model used for detection | ModelVersion |
| **Grading Policy Version** | Policy applied for grading | GradingPolicy |
| **Evidence Summary** | Key images and detection results | InspectionImages |
| **Review Information** | Manual review notes (if any) | ManualReview |
| **Verification ID** | Unique ID for QR verification | Generated |

---

## Report Format

### Digital Report Structure

```json
{
  "report_id": "uuid",
  "verification_id": "short-verification-code",
  "inspection_id": "uuid",
  "lot_id": "uuid",
  "farmer": {
    "id": "uuid",
    "name": "Farmer Name",
    "registration_number": "REG-XXXX"
  },
  "procurement_centre": {
    "id": "uuid",
    "name": "Centre Name",
    "location": "City, State"
  },
  "operator": {
    "id": "uuid",
    "name": "Operator Name",
    "role": "operator"
  },
  "inspection_datetime": "2026-XX-XXTXX:XX:XX+05:30",
  "sample_size": 50,
  "grading_summary": {
    "grade_a_count": 35,
    "grade_a_percentage": 70.0,
    "urs_count": 10,
    "urs_percentage": 20.0,
    "reject_count": 3,
    "reject_percentage": 6.0,
    "manual_review_count": 2,
    "manual_review_percentage": 4.0
  },
  "defect_distribution": {
    "HEALTHY": 35,
    "DAMAGED": 8,
    "ROTTEN": 2,
    "SPROUTED": 1,
    "UNKNOWN": 4
  },
  "size_distribution": {
    "ACCEPTABLE_SIZE": 40,
    "UNDERSIZED": 3,
    "UNDETERMINED": 7
  },
  "model_version": "1.0.0",
  "grading_policy_version": "1.0.0",
  "evidence_images": ["image_id_1", "image_id_2"],
  "review_notes": "Manual review performed on 2 flagged onions",
  "generated_at": "2026-XX-XXTXX:XX:XX+05:30",
  "qr_code_data": "https://onionsure.example.com/verify/SHORT-CODE"
}
```

---

## PDF Generation

### PDF Layout

```
┌─────────────────────────────────────────┐
│  ONION_SURE Quality Inspection Report   │
│  Report ID: XXXX-XXXX                   │
│  Date: XXXX-XX-XX                       │
├─────────────────────────────────────────┤
│  Inspection Details                      │
│  - Lot: XXXX                            │
│  - Farmer: XXXX                         │
│  - Centre: XXXX                         │
│  - Operator: XXXX                       │
│  - Sample Size: XX                      │
├─────────────────────────────────────────┤
│  Grading Results                         │
│  ┌─────────┬───────┬──────────┐         │
│  │ Grade   │ Count │ Percent  │         │
│  ├─────────┼───────┼──────────┤         │
│  │ Grade A │  35   │  70.0%   │         │
│  │ URS     │  10   │  20.0%   │         │
│  │ Reject  │   3   │   6.0%   │         │
│  │ Review  │   2   │   4.0%   │         │
│  └─────────┴───────┴──────────┘         │
├─────────────────────────────────────────┤
│  Defect Distribution                     │
│  [Bar chart or table]                    │
├─────────────────────────────────────────┤
│  Model: v1.0.0  Policy: v1.0.0          │
│                      ┌────────┐          │
│  Verification:       │ QR     │          │
│  SHORT-CODE          │ Code   │          │
│                      └────────┘          │
└─────────────────────────────────────────┘
```

### PDF Libraries

- Backend: `reportlab`, `weasyprint`, or `fpdf2`
- Ensure consistent rendering across environments.

---

## QR Code Verification

### QR Code Content

The QR code encodes a verification URL:

```
https://onionsure.example.com/verify/{verification_id}
```

### Privacy Rule

The QR code and verification URL must NOT expose:

- ❌ Farmer personal details
- ❌ Financial information
- ❌ Raw image data
- ❌ Internal database IDs
- ❌ Operator personal details

The verification endpoint returns ONLY:

```json
{
  "verification_status": "VALID",
  "report_id": "XXXX-XXXX",
  "inspection_date": "2026-XX-XX",
  "lot_id": "LOT-XXXX",
  "grade_a_percentage": 70.0,
  "urs_percentage": 20.0,
  "reject_percentage": 6.0,
  "model_version": "1.0.0",
  "policy_version": "1.0.0"
}
```

### Verification States

| State | Description |
|:---|:---|
| `VALID` | Report exists and is authentic |
| `INVALID` | Verification ID not found |
| `EXPIRED` | Report is older than retention period |
| `REVOKED` | Report was invalidated |

---

## Implementation Rules

1. **All mandatory fields must be present** in every report.
2. **Model and policy versions are always included** for auditability.
3. **QR code links to verification endpoint** — not raw data.
4. **Verification does not expose private data.**
5. **PDF renders consistently** across different environments.
6. **Reports are immutable** after generation — create new versions, don't edit.
7. **Verification IDs are short, human-readable** — not full UUIDs.

---

## Validation Rules

- ✅ All mandatory fields are present in the report.
- ✅ Percentages sum to 100% (within rounding tolerance).
- ✅ Model and policy versions are populated.
- ✅ QR code encodes a valid verification URL.
- ✅ Verification endpoint does not expose private information.
- ✅ PDF is readable and well-formatted.
- ✅ Report ID is unique.

---

## Forbidden Behavior

- ❌ Generating reports with missing mandatory fields.
- ❌ Exposing private information through QR verification.
- ❌ Fabricating grading percentages.
- ❌ Generating reports without model/policy version references.
- ❌ Allowing report modification after generation.
- ❌ Using internal database IDs in QR codes.

---

## Expected Outputs

1. **Digital report** — JSON with all mandatory fields.
2. **PDF report** — formatted, printable document.
3. **QR code** — encoded verification URL.
4. **Verification endpoint** — privacy-safe report validation.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `grading-engine` | Provides grade results and lot summary |
| `fastapi-backend` | Report generation and verification endpoints |
| `flutter-mobile` | Report display and QR scanning |
| `security` | QR verification privacy |
| `testing` | Report accuracy tests |
| `ps26031-requirements` | Defines required report content |
