---
name: fastapi-backend
description: >-
  Governs the FastAPI backend for ONION_SURE: REST API design, Pydantic models,
  PostgreSQL with SQLAlchemy ORM, migrations, authentication, authorization,
  RBAC, audit logging, file handling, and all backend entities. Activate for
  any backend, API, or server-side task.
---

# FastAPI Backend Skill

## Purpose

Define and enforce the backend architecture for ONION_SURE using FastAPI,
PostgreSQL, and SQLAlchemy. The backend serves the Flutter mobile app, runs
AI inference, manages data, and generates reports.

## When to Use

- Creating or modifying API endpoints.
- Defining or updating database models.
- Implementing authentication/authorization.
- Managing file uploads and storage.
- Integrating AI inference into the API.
- Creating or updating migrations.
- Implementing business logic services.

## Required Inputs

- Feature specification or API endpoint requirements.
- Database schema changes (if any).
- Security requirements (authentication, RBAC).

---

## Technology Stack

| Component | Technology |
|:---|:---|
| **Framework** | FastAPI (Python 3.10+) |
| **Validation** | Pydantic v2 |
| **Database** | PostgreSQL 15+ |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Migrations** | Alembic |
| **Authentication** | JWT (access + refresh tokens) |
| **File Storage** | Local filesystem or S3-compatible |
| **Task Queue** | Celery or background tasks (for AI inference) |
| **Testing** | pytest + httpx |

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application factory
│   ├── config.py               # Settings from environment variables
│   ├── dependencies.py         # Dependency injection
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # Main v1 router
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── users.py        # User management
│   │   │   ├── farmers.py      # Farmer endpoints
│   │   │   ├── lots.py         # Lot management
│   │   │   ├── inspections.py  # Inspection endpoints
│   │   │   ├── grading.py      # Grading endpoints
│   │   │   ├── reports.py      # Report generation
│   │   │   └── sync.py         # Offline sync endpoints
│   │   └── deps.py             # Shared API dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── farmer.py
│   │   ├── lot.py
│   │   ├── inspection.py
│   │   ├── detection.py
│   │   ├── grading.py
│   │   ├── report.py
│   │   ├── audit.py
│   │   └── sync.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # Pydantic schemas
│   │   ├── farmer.py
│   │   ├── inspection.py
│   │   ├── grading.py
│   │   └── report.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── inspection_service.py
│   │   ├── inference_service.py
│   │   ├── grading_service.py
│   │   ├── report_service.py
│   │   └── sync_service.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # Password hashing, JWT
│   │   ├── database.py         # DB connection, session
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── logging.py          # Structured logging
│   └── ml/
│       ├── __init__.py
│       ├── inference.py        # Model inference
│       ├── measurement.py      # Size measurement
│       └── grading_engine.py   # Deterministic grading
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/               # Migration files
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_inspections.py
│   ├── test_grading.py
│   └── test_reports.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Backend Entities

| Entity | Purpose |
|:---|:---|
| `User` | System users (operators, admins, reviewers) |
| `Role` | RBAC roles (admin, operator, reviewer, viewer) |
| `Farmer` | Farmer/supplier information |
| `ProcurementCentre` | Procurement center details |
| `Lot` | Onion lot/batch for inspection |
| `Inspection` | Quality inspection session |
| `InspectionImage` | Individual images within an inspection |
| `OnionDetection` | AI detection results per onion |
| `DefectResult` | Defect classification results |
| `Measurement` | Size measurement results |
| `GradeResult` | Final grading decisions |
| `GradingPolicy` | Versioned grading policy configuration |
| `ModelVersion` | Tracked ML model versions |
| `ManualReview` | Human review overrides |
| `Report` | Generated quality reports |
| `AuditLog` | System-wide audit trail |
| `SyncQueue` | Offline sync queue items |

---

## API Design Rules

### Versioning

All endpoints are versioned: `/api/v1/...`

### Request/Response Patterns

```python
# Standard success response
class APIResponse(BaseModel):
    success: bool = True
    data: Any
    message: Optional[str] = None

# Standard error response
class APIError(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: Optional[dict] = None

# Paginated response
class PaginatedResponse(BaseModel):
    success: bool = True
    data: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
```

### HTTP Status Codes

| Code | Usage |
|:---|:---|
| 200 | Success |
| 201 | Created |
| 400 | Bad request / validation error |
| 401 | Unauthorized |
| 403 | Forbidden (insufficient role) |
| 404 | Not found |
| 409 | Conflict (idempotency violation) |
| 422 | Unprocessable entity |
| 500 | Internal server error |

### Authentication & Authorization

- JWT-based authentication (access token + refresh token).
- Access tokens: short-lived (15–30 minutes).
- Refresh tokens: longer-lived, single-use.
- RBAC with roles: `admin`, `operator`, `reviewer`, `viewer`.
- Every endpoint has explicit permission requirements.

---

## Implementation Rules

1. **Use Pydantic v2** for all request/response validation.
2. **Use async SQLAlchemy** for database operations.
3. **Use Alembic** for all schema migrations.
4. **Use dependency injection** for database sessions, auth, and services.
5. **Separate concerns:** routers → services → repositories → models.
6. **Log all API requests** with request ID, user, timestamp.
7. **Audit all state changes** to the `AuditLog` table.
8. **Validate file uploads** — check type, size, and content.
9. **Use environment variables** for all configuration.
10. **Handle errors consistently** with structured error responses.
11. **Paginate list endpoints** by default.
12. **Use transactions** for multi-step operations.

---

## Validation Rules

- ✅ All endpoints have request/response schemas.
- ✅ All endpoints have authentication requirements.
- ✅ All state changes are audited.
- ✅ File uploads are validated.
- ✅ Pagination is implemented for list endpoints.
- ✅ Error responses follow the standard format.
- ✅ Database changes go through migrations.
- ✅ No secrets in code — environment variables only.

---

## Forbidden Behavior

- ❌ Committing secrets, API keys, or passwords in source code.
- ❌ Raw SQL without parameterization (SQL injection risk).
- ❌ Modifying the database schema without Alembic migrations.
- ❌ Business logic inside route handlers (use services).
- ❌ Unvalidated file uploads.
- ❌ Endpoints without authentication (except health check).
- ❌ Swallowing exceptions without logging.
- ❌ Hardcoding environment-specific values.

---

## Expected Outputs

1. **API endpoints** — versioned, documented, tested.
2. **Database models** — with migrations.
3. **Service layer** — business logic separated from API layer.
4. **Authentication/authorization** — JWT + RBAC.
5. **Audit logging** — all state changes tracked.
6. **API documentation** — auto-generated via FastAPI (Swagger/OpenAPI).

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `database-engineering` | Database schema and migration rules |
| `security` | Authentication, authorization, secret management |
| `computer-vision` | AI inference integration |
| `grading-engine` | Grading logic integration |
| `reporting-qr` | Report generation endpoints |
| `api-integration` | API contract with Flutter |
| `testing` | API test requirements |
| `devops` | Docker, deployment configuration |
