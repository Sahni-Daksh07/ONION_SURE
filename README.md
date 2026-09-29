# ONION_SURE 🧅

[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH-2026-orange.svg)](https://sih.gov.in/)
[![Problem Statement](https://img.shields.io/badge/PS26031-AI--Based%20Onion%20Grading-blue.svg)](#)
[![Ministry](https://img.shields.io/badge/Ministry-Consumer%20Affairs%2C%20Food%20%26%20Public%20Distribution-green.svg)](#)
[![Department](https://img.shields.io/badge/Department-Consumer%20Affairs%20(DoCA)-blueviolet.svg)](#)
[![Tests Passing](https://img.shields.io/badge/Tests-62%2F62%20Passed-brightgreen.svg)](#)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20PostgreSQL-teal.svg)](#)
[![Flutter](https://img.shields.io/badge/Mobile-Flutter%203.x-02569B.svg)](#)

> **Autonomous AI-Powered Onion Quality Assessment, Deterministic Grading, and Tamper-Evident Digital Reporting System** engineered for the **Department of Consumer Affairs (DoCA)** under **Smart India Hackathon 2026 (Problem Statement PS26031)**.

---

## 📌 Problem Context & Vision

During procurement and buffer stocking of onions across national mandis (e.g., Lasalgaon, Pimpalgaon), quality assessment has historically relied on manual, subjective visual appraisal. This causes:
- Disputes between farmers and procurement officials regarding fair grading.
- Inconsistent identification of physiological defects (sprouting, rotting, mechanical cuts).
- Inaccurate estimation of **Grade A** versus **Under-Regulation Size (URS)** lots.
- Absence of verifiable digital audit trails at mandi intake points.

**ONION_SURE** provides an end-to-end automated platform that:
1. Validates optical quality and captures multi-onion sample trays via mobile devices.
2. Detects individual onions and isolates defects using deep vision inference.
3. Enforces **strict physical calibration** (ArUco reference marker) for accurate millimeter sizing.
4. Calculates lot grades through a **100% deterministic, auditable grading policy engine** (zero LLM hallucinations in the grading path).
5. Functions seamlessly in **offline mandi environments** with a 5-state idempotent sync queue.
6. Synthesizes **government-standard digital inspection certificates** with cryptographically secure, privacy-preserving QR code verification.

---

## 🏛️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   FIELD TIER: FLUTTER MOBILE APP                       │
│  • Procurement Intake  • Real-time Camera Guidance & Optical Quality    │
│  • Offline SQLite DB   • Idempotent Sync Queue (5-State Lifecycle)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS / REST (Multipart)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  SERVICE TIER: FASTAPI BACKEND API                     │
│  • OAuth2 / JWT Auth  • 4-Tier RBAC (SuperAdmin, CentreAdmin, etc.)   │
│  • Entity Repositories• Tamper-Evident Public Verification Endpoint    │
└──────────────┬────────────────────┬────────────────────┬───────────────┘
               │                    │                    │
               ▼                    ▼                    ▼
┌────────────────────────┐ ┌──────────────────┐ ┌────────────────────────┐
│ COMPUTER VISION ENGINE │ │ DETERMINISTIC    │ │ DIGITAL REPORTING      │
│ • Blur/Lighting Filter │ │ GRADING ENGINE   │ │ • ReportLab PDF Cert   │
│ • BBox Detection       │ │ • Versioned Rule │ │ • ISO/IEC 18004 QR Gen │
│ • Defect Extraction    │ │ • Grade A / URS  │ │ • Zero-PII Public      │
│ • ArUco Calibration    │ │ • Reason Traces  │ │   Verification Registry│
└────────────────────────┘ └──────────────────┘ └────────────────────────┘
               │                    │                    │
               └────────────────────┼────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     DATA TIER: PERSISTENCE & STORAGE                   │
│  • PostgreSQL / SQLite with SQLAlchemy 2.0 ORM & Alembic Migrations    │
│  • Abstract Storage Provider (Local File System / AWS S3 Compatible)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Modules & Capabilities

### 1. Computer Vision & Physical Calibration (`onion_sure/vision/`)
- **Optical Pre-Validation:** Evaluates blur using Laplacian variance ($\ge 50.0$) and luminance thresholds before inference.
- **Onion Detection & Segmentation:** Isolates individual bulbs with high-confidence bounding coordinates and area metrics.
- **Defect Classifier:** Analyzes healthy tissue, rotting, mechanical lesions, and shoot sprouting.
- **Non-Negotiable Sizing Invariant:** Adheres strictly to PS26031 rules: if no physical ArUco calibration marker or known reference is detected, size is marked `measurement_unavailable` ($0.0$ fake measurements). When calibrated, computes exact millimeter diameter.

### 2. Deterministic Grading Engine (`onion_sure/grading/`)
- **No LLM in Grading Path:** Grading is 100% rule-based, reproducible, and verifiable.
- **DoCA Grade Classifications:**
  - **Grade A:** Healthy bulbs, diameter $\ge 45\text{ mm}$, minor defect $\le 5\%$.
  - **URS (Under-Regulation Size):** Bulbs $< 45\text{ mm}$ or minor defects between $5\% - 15\%$.
  - **Reject:** Critical rotting, severe sprouting, or total defects $> 20\%$.
  - **Manual Review:** Triggered automatically when AI detection confidence falls below the threshold ($< 0.70$).
- **Audit Trace:** Every single onion decision records explicit reason codes (e.g., `DEFECT_SPROUTED_CRITICAL`, `HEALTHY_FULL_SIZE`).

### 3. Enterprise FastAPI Backend (`onion_sure/backend/`)
- **Authentication & Security:** Argon2 / Bcrypt password hashing, JWT bearer tokens, and granular 4-tier Role-Based Access Control (`SUPER_ADMIN`, `CENTRE_ADMIN`, `OPERATOR`, `AUDITOR`).
- **Complete Entity Relational Schema:** Farmers, Procurement Centres, Mandi Lots, Inspections, Image Evidences, AI Detections, and Audit Logs.
- **Byte-Safe Error Sanitization:** Resilient exception handlers sanitize raw binary inputs to prevent server crashes on malformed uploads.

### 4. Offline-First Mobile Application (`mobile/`)
- **18 Production Screens:** Complete mandi workflow from login, lot intake, guided camera capture, real-time quality feedback, to lot results and PDF preview.
- **Offline Persistence:** Local SQLite database caches inspections created in remote mandis without cellular coverage.
- **Idempotent Synchronization:** 5-state sync lifecycle (`PENDING` $\rightarrow$ `SYNCING` $\rightarrow$ `SYNCED` / `FAILED` / `REQUIRES ACTION`) with client-generated UUID keys to prevent duplicate database writes on retries.

### 5. Digital Reporting & Zero-PII QR Verification (`onion_sure/reports/`)
- **Official Inspection Certificates:** Multi-page ReportLab PDF including lot metrics, Grade A % vs URS %, defect distribution charts, and evidence thumbnails.
- **Cryptographic Verification:** SHA-256 digital verification hash embedded into an ISO/IEC 18004 high-density QR code.
- **Public Verification Registry:** Public endpoint allows anyone scanning the physical sack label to verify authenticity without leaking farmer phone numbers or Aadhaar details.

---

## ⚡ Live Performance Benchmarks

Audited on September 30, 2026 using the official `scripts/audit_production_readiness.py` benchmark suite on real 576×768 onion images:

| Operation / Component | Live Benchmark | SLA Requirement | Headroom Margin |
|:---|:---|:---|:---|
| **Image Quality Validation** | **4.20 ms** | $< 100\text{ ms}$ | **95.8%** |
| **Onion Object Detection** | **16.33 ms** | $< 500\text{ ms}$ | **96.7%** |
| **Defect Feature Classification** | **1.18 ms** | $< 200\text{ ms}$ | **99.4%** |
| **Total Vision Pipeline** | **21.25 ms** | $< 1000\text{ ms}$ | **97.8%** |
| **Deterministic Grading Engine** | **0.08 ms** | $< 10\text{ ms}$ | **99.2%** |
| **End-to-End AI + Grading** | **21.33 ms** | $< 1500\text{ ms}$ | **98.5%** |
| **Auth Register / Login** | **225.69 ms / 211.12 ms**| $< 500\text{ ms}$ | **54.8%** |
| **Report Finalization + PDF** | **78.83 ms** | $< 1000\text{ ms}$ | **92.1%** |
| **Public QR Verification Lookup** | **9.58 ms** | $< 100\text{ ms}$ | **90.4%** |

---

## 🛠️ Quickstart Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.11 / 3.14)
- Git
- Flutter 3.x (for mobile application)
- PostgreSQL (or SQLite for local development)

### 1. Repository Setup & Environment

```bash
# Clone the repository
git clone https://github.com/Sahni-Daksh07/ONION_SURE.git
cd ONION_SURE

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
# Apply Alembic database migrations
alembic upgrade head
```

### 3. Launch the Backend Server

```bash
# Start FastAPI application with live reloading
uvicorn onion_sure.backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative ReDoc Interface: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 4. Run the Production-Readiness Benchmark

```bash
# Run the complete end-to-end benchmark suite
python scripts/audit_production_readiness.py
```

### 5. Run the Automated Test Suite

```bash
# Execute all 62 unit, integration, and E2E tests
pytest -v
```

### 6. Run the Flutter Mobile Application

```bash
cd mobile
flutter pub get
flutter run
```

---

## 🧪 Test Suite Summary (62/62 Passed)

```text
tests/test_backend_api.py .............. [ 11%] (Auth, RBAC, Lot intake, Sync Idempotency)
tests/test_computer_vision.py .......... [ 22%] (Quality check, BBox detection, Invariants)
tests/test_database_integration.py ..... [ 40%] (Traceability, Rollbacks, Repositories)
tests/test_dataset_engineering.py ...... [ 46%] (DHash duplicates, Leakage-free splits)
tests/test_digital_quality_reporting.py  [ 59%] (ReportLab PDF, QR generation, Zero-PII API)
tests/test_grading_engine.py ........... [ 82%] (DoCA Grade A/URS logic, Reason trace)
tests/test_mobile_application.py ....... [ 91%] (18 Screens, App router, Permissions)
tests/test_offline_inspection_flow.py .. [100%] (Airplane mode flow, Sync queue states)
============================== 62 passed in 118.18s ==============================
```

---

## 📂 Repository Directory Layout

```text
ONION_SURE/
├── alembic/                       # Database migration configurations
├── mobile/                        # Flutter Android-first mobile application
│   ├── lib/
│   │   ├── app.dart               # App router with all 18 registered screens
│   │   ├── core/                  # Design tokens, theme, API constants
│   │   └── features/              # Feature modules (camera, sync, review, etc.)
│   └── pubspec.yaml               # Flutter package dependencies
├── onion_sure/                    # Core Python application packages
│   ├── backend/                   # FastAPI application, routers, schemas, services
│   ├── db/                        # SQLAlchemy models, sessions, base classes
│   ├── grading/                   # Deterministic grading policy engine
│   ├── reports/                   # PDF synthesis & ISO/IEC 18004 QR generation
│   └── vision/                    # Quality validation, detector, calibration
├── scripts/
│   ├── audit_production_readiness.py # Complete empirical benchmark & stress runner
│   ├── create_splits.py           # Leakage-free dataset splitter
│   └── dataset_pipeline.py        # Dataset analysis & manifest pipeline
├── tests/                         # Pytest automated test suite (62 tests)
├── README.md                      # Comprehensive system documentation
└── requirements.txt               # Pinned Python package dependencies
```

---

## 📜 Compliance & Ethical AI Disclosure

- **Non-Fabrication Invariant:** Raw dataset classes (`Healthy` vs `Unhealthy`) were not artificially transformed into specific defect types without ground-truth annotations.
- **Physical Calibration Invariant:** Metric diameter estimations require physical calibration (ArUco / reference scale); absent reference markers return `measurement_unavailable`.
- **Zero-LLM Grading Invariant:** Grading decisions are strictly rule-based and auditable.
- **Privacy Assurance:** Public verification certificates mask personal farmer identifiers in full compliance with the Digital Personal Data Protection (DPDP) Act.

---

## 👥 Contributors & Acknowledgements

Developed for **Smart India Hackathon 2026** under Problem Statement **PS26031** for the **Department of Consumer Affairs (DoCA)**, Ministry of Consumer Affairs, Food & Public Distribution, Government of India.