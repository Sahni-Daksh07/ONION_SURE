---
name: api-integration
description: >-
  Governs the API contract between Flutter mobile, FastAPI backend, AI inference,
  database, object storage, and reports. Enforces typed schemas, API versioning,
  consistent error handling, timeout/retry policies, idempotency, and
  authentication across all integration points. Activate for any cross-component
  integration or API contract task.
---

# API Integration Skill

## Purpose

Define and enforce the API contracts and integration patterns between all
ONION_SURE components: Flutter ↔ FastAPI ↔ AI Inference ↔ Database ↔
Object Storage ↔ Reports.

## When to Use

- Defining or modifying API contracts between components.
- Implementing API client code (Flutter side).
- Implementing API endpoints (FastAPI side).
- Handling cross-component error propagation.
- Setting up retry/timeout policies.
- Ensuring consistent request/response formats.

## Required Inputs

- Feature requiring cross-component communication.
- Existing API contracts (if modifying).
- Error handling requirements.

---

## Integration Map

```
┌───────────────┐     REST/JSON      ┌──────────────────┐
│               │ ◄──────────────── │                  │
│  Flutter App  │ ─────────────────►│  FastAPI Backend  │
│  (Android)    │                    │                  │
└───────────────┘                    └──────┬───────────┘
                                           │
                              ┌────────────┼────────────┐
                              │            │            │
                        ┌─────▼────┐ ┌─────▼────┐ ┌────▼──────┐
                        │ AI       │ │ Database │ │ Object    │
                        │ Inference│ │ Postgres │ │ Storage   │
                        └──────────┘ └──────────┘ └───────────┘
```

---

## API Versioning

All API endpoints are versioned under `/api/v1/`.

```
/api/v1/auth/login
/api/v1/auth/refresh
/api/v1/inspections
/api/v1/inspections/{id}
/api/v1/inspections/{id}/images
/api/v1/inspections/{id}/results
/api/v1/inspections/{id}/report
/api/v1/lots
/api/v1/farmers
/api/v1/reports/{id}
/api/v1/verify/{verification_id}
/api/v1/sync/push
/api/v1/sync/status
/api/v1/health
```

When breaking changes are required, create `/api/v2/` — never modify v1 semantics.

---

## Request/Response Contract

### Standard Success

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message"
}
```

### Standard Error

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable error message",
    "details": {
      "field": "lot_id",
      "reason": "Lot not found"
    }
  }
}
```

### Paginated List

```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "total": 150,
    "page": 1,
    "page_size": 20,
    "total_pages": 8
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|:---|:---|:---|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required or invalid |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Duplicate or conflicting request |
| `UNPROCESSABLE` | 422 | Semantically invalid request |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | AI model or dependency unavailable |

---

## Typed Schemas

### Flutter (Dart)

```dart
// Every API response has a typed model
class ApiResponse<T> {
  final bool success;
  final T? data;
  final String? message;
  final ApiError? error;
}

class InspectionResponse {
  final String inspectionId;
  final String lotId;
  final String status;
  final DateTime createdAt;
  
  factory InspectionResponse.fromJson(Map<String, dynamic> json) { ... }
}
```

### FastAPI (Python)

```python
# Every endpoint has Pydantic request/response models
class CreateInspectionRequest(BaseModel):
    lot_id: UUID
    notes: Optional[str] = None

class InspectionResponse(BaseModel):
    inspection_id: UUID
    lot_id: UUID
    status: str
    created_at: datetime
```

---

## Timeout and Retry Policy

```yaml
client_config:
  connect_timeout_seconds: 10
  read_timeout_seconds: 30
  upload_timeout_seconds: 120   # For image uploads
  inference_timeout_seconds: 60  # For AI processing

retry_policy:
  max_retries: 3
  retry_on: [500, 502, 503, 504, "timeout", "connection_error"]
  no_retry_on: [400, 401, 403, 404, 409, 422]
  backoff:
    initial_delay_ms: 500
    multiplier: 2
    max_delay_ms: 10000
```

---

## Idempotency

For state-changing operations that may be retried:

- Client generates an `Idempotency-Key` header (UUID).
- Server stores the key and result.
- On duplicate key, server returns the original result.
- Keys expire after 24 hours.

```
POST /api/v1/inspections
Headers:
  Authorization: Bearer <token>
  Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
  Content-Type: application/json
```

---

## Authentication Flow

```
1. POST /api/v1/auth/login { username, password }
   → { access_token, refresh_token, expires_in }

2. All API calls include:
   Authorization: Bearer <access_token>

3. On 401 response:
   POST /api/v1/auth/refresh { refresh_token }
   → { access_token, refresh_token, expires_in }
   → Retry original request

4. On refresh failure:
   → Redirect to login screen
```

---

## Implementation Rules

1. **Every endpoint has a typed request and response model.**
2. **Error responses follow the standard format** — always.
3. **API versioning is mandatory** — `/api/v1/`.
4. **Timeouts are configured** — never use infinite timeouts.
5. **Retry only on server errors and timeouts** — not client errors.
6. **Idempotency keys for state-changing operations.**
7. **Authentication on every request** (except health check and verification).
8. **Log all API calls** — request ID, endpoint, status, duration.

---

## Validation Rules

- ✅ Flutter and FastAPI share compatible type definitions.
- ✅ All error responses use the standard error format.
- ✅ Timeouts are configured for all HTTP calls.
- ✅ Retries respect the no-retry list.
- ✅ Idempotency keys prevent duplicate operations.
- ✅ Authentication tokens are refreshed automatically.

---

## Forbidden Behavior

- ❌ Untyped API responses (raw `Map` or `dict` without schema).
- ❌ Inconsistent error formats across endpoints.
- ❌ Infinite timeouts.
- ❌ Retrying 400/401/403/422 errors.
- ❌ Missing authentication on endpoints.
- ❌ Breaking v1 API semantics without creating v2.

---

## Expected Outputs

1. **API contract documentation** — OpenAPI/Swagger spec.
2. **Typed client models** — Dart classes matching API schemas.
3. **Typed server schemas** — Pydantic models for all endpoints.
4. **Error handling** — consistent across all integration points.
5. **Retry/timeout configuration** — documented and tested.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `fastapi-backend` | Server-side implementation |
| `flutter-mobile` | Client-side implementation |
| `offline-sync` | Sync API endpoints |
| `security` | Authentication flow |
| `testing` | API integration tests |
