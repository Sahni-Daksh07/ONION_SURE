# ONION_SURE — Production Deployment Plan 🧅🚀
**Smart India Hackathon 2026 — Problem Statement PS26031**  
*Autonomous AI-Powered Onion Quality Assurance, Sizing Calibration, and Digital Reporting Platform*

---

## 📑 Table of Contents
1. [Executive Summary & System Architecture](#1-executive-summary--system-architecture)
2. [Target Deployment Topologies](#2-target-deployment-topologies)
3. [Infrastructure Sizing & System Prerequisites](#3-infrastructure-sizing--system-prerequisites)
4. [Step-by-Step Production Deployment Runbook](#4-step-by-step-production-deployment-runbook)
5. [Mandi Edge Appliance Deployment (Offline Mandis)](#5-mandi-edge-appliance-deployment-offline-mandis)
6. [Flutter Mobile App Release & Distribution](#6-flutter-mobile-app-release--distribution)
7. [Database Migrations, Seeding & Backup Strategy](#7-database-migrations-seeding--backup-strategy)
8. [Storage & Tamper-Evident Artifact Management](#8-storage--tamper-evident-artifact-management)
9. [Security Hardening & Zero-PII Compliance](#9-security-hardening--zero-pii-compliance)
10. [Observability, Health Probes & Monitoring](#10-observability-health-probes--monitoring)
11. [Disaster Recovery & Rollback Playbook](#11-disaster-recovery--rollback-playbook)
12. [Pre-Flight Verification Checklist](#12-pre-flight-verification-checklist)

---

## 1. Executive Summary & System Architecture

ONION_SURE is an enterprise agricultural AI grading system built to eliminate visual subjectivity in national onion procurement (NAFED, NCCF, DoCA). The platform combines:
1. **Edge/Mobile Inference & Optical Guidance:** Flutter client capturing high-resolution tray images with ArUco calibration and Laplacian blur filtering.
2. **FastAPI Service Tier:** High-performance REST APIs handling auth, RBAC, lot lifecycle, deterministic grading, and PDF report generation.
3. **Deterministic Grading Engine:** Zero-LLM, strictly verifiable rule execution adhering to Department of Consumer Affairs (DoCA) Grade A vs URS standards.
4. **Offline Sync Queue:** 5-state idempotent synchronization engine (`PENDING` $\rightarrow$ `SYNCING` $\rightarrow$ `SYNCED` / `FAILED` / `REQUIRES_ACTION`).
5. **Zero-PII Public Verification:** Privacy-safe ISO/IEC 18004 QR code verification endpoint for verifying physical mandi sack tags without leaking farmer personal data.

### Architectural Layout

```text
               ┌────────────────────────────────────────────────────────┐
               │           CLIENT TIER (MANDI & PUBLIC ACCESS)          │
               │  • Flutter Android App (Operators & Mandi Intake)      │
               │  • Web Dashboard (Centres, DoCA Admins, Auditors)     │
               │  • Public QR Scanner (Wholesalers, Logistics, Public)  │
               └───────────────────────────┬────────────────────────────┘
                                           │ HTTPS (Port 443)
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │         GATEWAY & PROXY TIER (NGINX / CLOUDFLARE)      │
               │  • SSL/TLS Termination • Gzip • Security Headers       │
               │  • Rate Limiting (Auth: 5 req/s | API: 30 req/s)       │
               │  • Static Caching (/dashboard/ static assets)          │
               └───────────────────────────┬────────────────────────────┘
                                           │ Reverse Proxy (Port 8000)
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │             APPLICATION TIER (DOCKER / FASTAPI)        │
               │  • 4 Uvicorn Workers • OpenCV Headless CV Pipeline     │
               │  • Deterministic Rule Engine • ReportLab PDF Generator │
               │  • Zero-PII Public Verification Registry               │
               └───────────────┬────────────────────────┬───────────────┘
                               │                        │
                 SQLAlchemy 2.0│                        │ Blob Storage API
                               ▼                        ▼
               ┌────────────────────────┐      ┌────────────────────────┐
               │      DATABASE TIER     │      │      STORAGE TIER      │
               │ PostgreSQL 16 (Alpine) │      │ Local Volume / AWS S3  │
               │ Connection Pool (25+15)│      │ Encrypted Inspection   │
               │ Automated WAL Backups  │      │ Images & PDF Reports   │
               └────────────────────────┘      └────────────────────────┘
```

---

## 2. Target Deployment Topologies

The system supports two complementary deployment models:

### Topology A: Central Cloud Production Hub
- **Purpose:** Centralized headquarters, public QR verification, inter-mandi analytics, DoCA oversight, and master farmer registry.
- **Hosting Targets:** MeghRaj (Government of India Cloud), NIC Cloud, AWS (Mumbai `ap-south-1`), Azure (Central India), or Linux Bare-Metal VPS.
- **Components:** Containerized FastAPI backend, Managed PostgreSQL, Nginx reverse proxy with SSL, and Object Storage (S3 / MinIO).

### Topology B: Mandi Edge Mini-Server (Offline/Intermittent Connectivity)
- **Purpose:** On-premise deployment at remote APMC Mandis (e.g., Lasalgaon, Pimpalgaon) where cellular connectivity is unstable.
- **Hardware:** Ruggedized Mini-PC (Intel Core i5, 16GB RAM) running Docker Compose locally.
- **Local Wi-Fi:** Creates a local Mandi Wi-Fi AP allowing field operators' mobile tablets to run full optical grading locally and buffer sync records until internet connectivity is restored.

---

## 3. Infrastructure Sizing & System Prerequisites

### Minimum Hardware Sizing Guidelines

| Component | Cloud Production Hub (Central) | Mandi Edge Mini-PC (Local APMC) |
|:---|:---|:---|
| **CPU** | 4 vCPUs (x86_64, modern Intel/AMD) | 4 Cores (Intel Core i5 / AMD Ryzen 5) |
| **RAM** | 8 GB RAM (16 GB recommended) | 8 GB - 16 GB RAM |
| **Storage** | 100 GB NVMe SSD (ext4) + S3 Storage | 256 GB NVMe SSD |
| **Network** | 100 Mbps symmetric bandwidth | Local Gigabit Wi-Fi AP + 4G SIM fallback |
| **OS** | Ubuntu 22.04 LTS / Debian 12 / RHEL 9 | Ubuntu 22.04 LTS (Headless) |
| **Docker** | Docker Engine 26.x + Docker Compose v2 | Docker Engine 26.x + Docker Compose v2 |

---

## 4. Step-by-Step Production Deployment Runbook

### Phase 1: Server Provisioning & OS Hardening

1. **Update and Secure the OS:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   sudo apt-get install -y ufw fail2ban curl git unattended-upgrades
   ```

2. **Configure Firewall (UFW):**
   ```bash
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   sudo ufw allow 22/tcp comment "SSH Management"
   sudo ufw allow 80/tcp comment "HTTP (Certbot & Redirect)"
   sudo ufw allow 443/tcp comment "HTTPS Production Traffic"
   sudo ufw enable
   ```

3. **Install Docker Engine & Docker Compose Plugin:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   # Log out and log back in to apply group changes
   ```

---

### Phase 2: DNS & Domain Configuration

Configure DNS `A` records pointing to the public production IP:
- `onionsure.gov.in` $\rightarrow$ Production Load Balancer / Server IP
- `api.onionsure.gov.in` $\rightarrow$ Production Backend API
- (Optional) Cloudflare proxy enabled for DDoS protection and web application firewalling.

---

### Phase 3: Repository Setup & Secret Injection

1. **Clone the Project Repository:**
   ```bash
   sudo mkdir -p /opt/onionsure
   sudo chown -R $USER:$USER /opt/onionsure
   cd /opt/onionsure
   git clone https://github.com/Sahni-Daksh07/ONION_SURE.git .
   ```

2. **Configure Production Environment (`.env`):**
   ```bash
   cp deploy/.env.production.example .env
   ```

3. **Generate Cryptographically Secure Secrets:**
   ```bash
   # Generate 64-char JWT secret key
   SECRET_KEY=$(openssl rand -hex 32)
   # Generate strong DB password
   DB_PASS=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)
   
   # Update .env
   sed -i "s/replace-with-ultra-secure-randomly-generated-32-byte-hex-string/$SECRET_KEY/g" .env
   sed -i "s/replace-with-strong-db-password-at-least-20-chars/$DB_PASS/g" .env
   ```

---

### Phase 4: Containerized Stack Deployment

1. **Build and Launch the Stack:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

2. **Verify Container Health:**
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```
   *Expected Output:*
   - `onion_sure_prod_postgres` (healthy)
   - `onion_sure_prod_backend` (healthy)
   - `onion_sure_prod_nginx` (running)

---

### Phase 5: Database Migrations & Initial Seeding

1. **Apply Alembic Migrations:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

2. **Verify Database Connectivity and Tables:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend python -c "
   from onion_sure.backend.database import check_database_connection
   print('Database connection OK:', check_database_connection())
   "
   ```

3. **Seed Initial System Roles & Baseline Grading Policies:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend python -m onion_sure.backend.seed
   ```

---

### Phase 6: SSL/TLS Certificate Provisioning (Let's Encrypt / Certbot)

1. **Obtain SSL Certificate using Certbot:**
   ```bash
   sudo apt-get install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d onionsure.gov.in -d api.onionsure.gov.in
   ```

2. **Verify Automatic Renewal:**
   ```bash
   sudo certbot renew --dry-run
   ```

---

## 5. Mandi Edge Appliance Deployment (Offline Mandis)

For remote mandis with unreliable 4G/fiber backhauls:

1. **Standalone Appliance Mode:**
   - Deploy Docker Compose on an edge mini-PC configured with static IP `192.168.10.1`.
   - Configure local DNS / hosts to point `mandi.local` to `192.168.10.1`.
2. **Wi-Fi Hotspot Integration:**
   - Field operators connect mobile devices to the secure Wi-Fi SSID: `ONION_SURE_MANDI_INSPECTION`.
   - The Flutter mobile app communicates directly with `http://mandi.local/api/v1`.
3. **Upstream Synchronization:**
   - Once the edge appliance detects active internet connectivity, a scheduled synchronization daemon pushes verified lots and inspection records to the Central Cloud Hub idempotently.

---

## 6. Flutter Mobile App Release & Distribution

### Step 1: Secure Keystore Setup
Generate Android release signing key:
```bash
keytool -genkey -v -keystore android-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias onionsure
```

### Step 2: Configure Environment Injection
Build the APK or Android App Bundle (AAB) with production endpoints passed via `--dart-define`:
```bash
cd mobile

flutter build apk --release \
  --dart-define=API_BASE_URL=https://api.onionsure.gov.in/api/v1 \
  --dart-define=APP_ENV=production \
  --dart-define=ENABLE_OFFLINE_CACHE=true
```

### Step 3: Distribution Channels
- **Government MDM (Mobile Device Management):** Deploy `.apk` directly to government-provisioned inspection tablets.
- **Private Play Store / Enterprise Track:** Distribute to authorized Mandi operators via Google Play Console internal test track.

---

## 7. Database Migrations, Seeding & Backup Strategy

### Automated Nightly PostgreSQL Backup
Create a daily automated backup script at `/opt/onionsure/scripts/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/onionsure/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

docker compose -f /opt/onionsure/docker-compose.prod.yml exec -T postgres \
  pg_dump -U onion_sure_app -d onion_sure -F c > "$BACKUP_DIR/onion_sure_$TIMESTAMP.dump"

# Retain backups for 30 days
find "$BACKUP_DIR" -type f -name "*.dump" -mtime +30 -exec rm {} \;
```

Set up Cron job:
```bash
crontab -e
# Runs daily at 02:00 AM
0 2 * * * /opt/onionsure/scripts/backup_db.sh > /dev/null 2>&1
```

---

## 8. Storage & Tamper-Evident Artifact Management

- **Local Storage Volume:** `/app/uploads` is mounted to `uploads_data` Docker volume.
- **Cloud S3 Compatibility:** For enterprise deployments, set `STORAGE_TYPE=s3` in `.env` to route image evidences and PDF certificates directly to an encrypted AWS S3 or MinIO bucket.
- **Retention Policy:**
  - High-resolution raw images: 90 days.
  - Calibrated cropped onion bounding boxes: 1 year.
  - Digital PDF Certificates & QR Hashes: 5 years (audit retention requirement).

---

## 9. Security Hardening & Zero-PII Compliance

In accordance with India's **Digital Personal Data Protection (DPDP) Act 2023**:
1. **Public QR Verification (`/api/v1/reports/verify/{token}`):**
   - Returns ONLY lot number, procurement centre, grade breakdown (Grade A %, URS %, Reject %), and timestamp.
   - Farmer names, Aadhaar numbers, phone numbers, and land parcels are **strictly excluded** from public outputs.
2. **Password & Token Security:**
   - Passwords hashed with Bcrypt (cost factor 12).
   - JWT tokens signed with HS256, strictly expiring in 120 minutes.
3. **Binary Exception Sanitization:**
   - The FastAPI exception handler explicitly intercepts and sanitizes malformed binary uploads, preventing memory leakage and stack-trace exposure.

---

## 10. Observability, Health Probes & Monitoring

### Standard Endpoints
- **Health Check:** `GET /health` (monitors DB readiness and memory allocation).
- **Swagger Documentation:** `GET /docs` (disabled or authenticated in public production).
- **Web Dashboard:** `GET /dashboard/` (secured by JWT local storage).

### Structured Log Monitoring
View real-time logs with request latency:
```bash
docker compose -f docker-compose.prod.yml logs -f --tail=100 backend
```

---

## 11. Disaster Recovery & Rollback Playbook

### Scenario A: Corrupt Deployment / Failed Release
```bash
# Rollback to previous git commit or image tag
git checkout HEAD~1
docker compose -f docker-compose.prod.yml up -d --build
```

### Scenario B: Database Restoration from Backup
```bash
# Restore specific dump
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_restore -U onion_sure_app -d onion_sure -c /backups/onion_sure_YYYYMMDD_HHMMSS.dump
```

---

## 12. Pre-Flight Verification Checklist

Before opening the system for live mandi procurement:

- [ ] `docker compose -f docker-compose.prod.yml ps` shows all services healthy.
- [ ] Pytest suite passes: `pytest -v` (62/62 passed).
- [ ] Live benchmark executed: `python scripts/audit_production_readiness.py` passed with SLA headroom >90%.
- [ ] Database migrations applied: `alembic upgrade head`.
- [ ] Initial users, centres, and grading policies seeded.
- [ ] SSL/TLS certificate active on `https://onionsure.gov.in`.
- [ ] High-density QR code scans successfully on mobile camera and loads public verification screen.
- [ ] Nginx rate limiting verified on `/api/v1/auth/login`.
- [ ] Automated backup cron job verified.
