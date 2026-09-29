---
name: devops
description: >-
  Governs DevOps practices for ONION_SURE: Docker configuration, development
  and test environments, production configuration, environment variables,
  migration execution, health checks, logging, monitoring hooks, and CI/CD
  readiness. No hardcoded environment-specific values. Activate for any
  deployment, Docker, CI/CD, or environment configuration task.
---

# DevOps Skill

## Purpose

Define infrastructure, deployment, and operational standards for ONION_SURE.
Ensure consistent environments, automated deployment readiness, and
operational observability.

## When to Use

- Setting up Docker containers.
- Configuring development environments.
- Preparing for deployment.
- Setting up CI/CD pipelines.
- Implementing health checks.
- Configuring logging and monitoring.
- Managing environment-specific configuration.

## Required Inputs

- Target environment (development, test, staging, production).
- Service requirements (backend, database, storage, ML model).

---

## Docker Architecture

```
docker/
├── docker-compose.yml          # Development environment
├── docker-compose.test.yml     # Test environment
├── docker-compose.prod.yml     # Production overrides
├── backend/
│   ├── Dockerfile              # Backend service
│   └── entrypoint.sh           # Startup script
├── ml/
│   └── Dockerfile              # ML inference service (if separate)
└── nginx/
    ├── Dockerfile
    └── nginx.conf              # Reverse proxy
```

### docker-compose.yml (Development)

```yaml
version: "3.8"
services:
  backend:
    build:
      context: ../backend
      dockerfile: ../docker/backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/onionsure
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - MODEL_PATH=/app/models
      - ENVIRONMENT=development
    volumes:
      - ../backend:/app           # Hot reload
      - model_data:/app/models
      - upload_data:/app/uploads
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=onionsure
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d onionsure"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  model_data:
  upload_data:
```

---

## Environment Configuration

### The Rule

```
❌ NEVER hardcode environment-specific values in code:
   - Database URLs
   - API URLs
   - File paths
   - Port numbers
   - Secret keys
   - Model paths

✅ ALWAYS use environment variables loaded from:
   - .env files (development)
   - Docker environment (containers)
   - Secret managers (production)
```

### Environment Hierarchy

| Environment | Config Source | Purpose |
|:---|:---|:---|
| Development | `.env` + `docker-compose.yml` | Local development |
| Test | `.env.test` + `docker-compose.test.yml` | Automated testing |
| Staging | Environment variables + secrets | Pre-production validation |
| Production | Environment variables + secret manager | Live deployment |

---

## Health Checks

### Backend Health Endpoint

```python
@router.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": await check_db_connection(),
        "model_loaded": inference_service.is_model_loaded(),
        "timestamp": datetime.utcnow().isoformat(),
    }
```

### Docker Health Checks

Every service must have a health check:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## CI/CD Readiness

### Pipeline Stages

```
1. Lint        → Code style checks (flake8, dart analyze)
2. Unit Test   → pytest, flutter test
3. Build       → Docker image build
4. Integration → API tests against Docker environment
5. ML Eval     → Model evaluation tests (if model changed)
6. Security    → Secret scanning, dependency audit
7. Deploy      → Push to registry, deploy to environment
```

### CI Configuration (.github/workflows/ci.yml)

```yaml
name: CI
on: [push, pull_request]
jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: onionsure_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/
  
  flutter-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
      - run: flutter test
        working-directory: mobile/
```

---

## Logging

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "inspection_created",
    inspection_id=str(inspection.id),
    lot_id=str(inspection.lot_id),
    user_id=str(current_user.id),
    timestamp=datetime.utcnow().isoformat(),
)
```

### Log Levels

| Level | Usage |
|:---|:---|
| `DEBUG` | Detailed debugging (not in production) |
| `INFO` | Normal operations (requests, completions) |
| `WARNING` | Unexpected but handled situations |
| `ERROR` | Failures requiring attention |
| `CRITICAL` | System-level failures |

---

## Migration Execution

```bash
# Development: run migrations on startup
alembic upgrade head

# Production: run migrations as a separate step before deployment
# NEVER auto-migrate in production startup
docker-compose exec backend alembic upgrade head
```

---

## Implementation Rules

1. **No hardcoded environment values** — use environment variables.
2. **Docker Compose for local development** — one command to start.
3. **Health checks on all services** — automated monitoring.
4. **Structured logging** — JSON format for parsing.
5. **Migrations run explicitly** — not automatically in production.
6. **CI/CD pipeline defined** — automated testing on every push.
7. **Multi-stage Docker builds** — minimize image size.
8. **`.dockerignore` configured** — exclude unnecessary files.

---

## Forbidden Behavior

- ❌ Hardcoding database URLs, API endpoints, or paths in code.
- ❌ Running production without health checks.
- ❌ Auto-applying migrations on production startup.
- ❌ Committing `.env` files with real credentials.
- ❌ Using `latest` tag for production Docker images.
- ❌ Skipping CI tests.

---

## Expected Outputs

1. **Docker configuration** — Compose files for dev/test/prod.
2. **Environment templates** — `.env.example` with all variables.
3. **Health endpoints** — for all services.
4. **CI/CD configuration** — automated pipeline definition.
5. **Logging setup** — structured, leveled, parseable.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `fastapi-backend` | Backend service containerization |
| `database-engineering` | Migration execution in pipelines |
| `security` | Secret management in deployment |
| `testing` | CI test execution |
| `documentation` | Deployment guide |
