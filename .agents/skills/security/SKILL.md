---
name: security
description: >-
  Enforces security standards for ONION_SURE: secret management, authentication,
  authorization, RBAC, password hashing, token expiration, input validation,
  file validation, upload limits, SQL injection protection, and audit logging.
  Never commit API keys, passwords, tokens, or secrets. Activate for any
  security, auth, or credential-related task.
---

# Security Skill

## Purpose

Enforce comprehensive security practices across all ONION_SURE components:
backend, mobile app, database, and deployment.

## When to Use

- Implementing authentication or authorization.
- Managing secrets and credentials.
- Handling file uploads.
- Validating user input.
- Reviewing code for security issues.
- Setting up deployment security.
- Implementing RBAC.

## Required Inputs

- Security requirements for the feature being implemented.
- Current security posture (from `repository-audit`).

---

## Secret Management

### ABSOLUTE RULE

```
❌ NEVER commit to version control:
   - API keys
   - Passwords
   - Database credentials
   - JWT secrets
   - Private keys
   - Service account credentials
   - Production connection strings
   - Any token or credential

✅ ALWAYS use:
   - Environment variables
   - .env files (in .gitignore)
   - Secret managers (in production)
   - .env.example (template without real values)
```

### .gitignore Requirements

```gitignore
# Secrets
.env
.env.local
.env.production
*.pem
*.key
credentials.json
service-account.json
```

### .env.example Template

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/onionsure
DATABASE_TEST_URL=postgresql://user:password@localhost:5432/onionsure_test

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=10

# AI Model
MODEL_PATH=/app/models/current
```

---

## Authentication

### JWT Token Flow

```
Login (username + password)
  → Verify credentials
  → Generate access token (short-lived: 15-30 min)
  → Generate refresh token (longer-lived: 7 days)
  → Return both tokens

API Request
  → Extract access token from Authorization header
  → Validate token (signature, expiration)
  → Extract user ID and role
  → Proceed with request

Token Refresh
  → Validate refresh token
  → Invalidate old refresh token (single-use)
  → Generate new access + refresh tokens
```

### Password Requirements

- Hash with `bcrypt` (cost factor ≥ 12).
- Never store plaintext passwords.
- Never log passwords.
- Enforce minimum password complexity.

---

## Authorization (RBAC)

### Roles

| Role | Permissions |
|:---|:---|
| `admin` | Full system access, user management |
| `operator` | Create inspections, capture images, view reports |
| `reviewer` | Review flagged onions, override grades |
| `viewer` | View reports and history (read-only) |

### Enforcement

```python
# Every endpoint explicitly declares required permissions
@router.post("/inspections", dependencies=[Depends(require_role("operator"))])
async def create_inspection(...):
    ...

@router.post("/manual-review/{id}", dependencies=[Depends(require_role("reviewer"))])
async def submit_review(...):
    ...
```

---

## Input Validation

### API Input

- All inputs validated by Pydantic models.
- String lengths constrained.
- Numeric ranges validated.
- Email format validated.
- SQL injection prevented by parameterized queries (SQLAlchemy handles this).

### File Upload Validation

```python
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MIN_IMAGE_DIMENSION = 224  # pixels

def validate_upload(file: UploadFile) -> None:
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")
    
    # Check file size
    if file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(400, "File too large")
    
    # Validate it's actually an image (magic bytes)
    header = file.file.read(16)
    file.file.seek(0)
    if not is_valid_image_header(header):
        raise HTTPException(400, "Invalid image file")
```

---

## Audit Logging

Every security-relevant action must be logged:

| Event | Logged Data |
|:---|:---|
| Login success | User ID, timestamp, IP |
| Login failure | Username attempted, timestamp, IP |
| Token refresh | User ID, timestamp |
| Permission denied | User ID, endpoint, timestamp |
| Grade override | User ID, grade before/after, reason |
| Report generation | User ID, report ID, timestamp |
| User creation | Admin ID, new user ID |
| Role change | Admin ID, user ID, old/new role |

---

## Implementation Rules

1. **All secrets in environment variables** — never in code.
2. **JWT with short-lived access tokens** and refresh token rotation.
3. **bcrypt for password hashing** — cost factor ≥ 12.
4. **RBAC on every endpoint** — no unprotected endpoints (except health check).
5. **File uploads validated** — type, size, content.
6. **Parameterized queries only** — via SQLAlchemy ORM.
7. **Audit log all security events.**
8. **HTTPS in production** — never plain HTTP.
9. **CORS configured properly** — not wildcard in production.

---

## Validation Rules

- ✅ No secrets in version control.
- ✅ `.env.example` exists with placeholder values.
- ✅ Authentication required on all endpoints (except health).
- ✅ RBAC enforced with explicit role checks.
- ✅ Passwords hashed with bcrypt.
- ✅ File uploads validated for type, size, content.
- ✅ Security events are audit-logged.

---

## Forbidden Behavior

- ❌ Committing any secrets, keys, passwords, or tokens.
- ❌ Storing plaintext passwords.
- ❌ Logging passwords or tokens.
- ❌ Unprotected API endpoints (except health check).
- ❌ Raw SQL queries (use ORM / parameterized queries).
- ❌ Wildcard CORS in production.
- ❌ Accepting file uploads without validation.
- ❌ Disabling authentication "temporarily" and forgetting to re-enable.

---

## Expected Outputs

1. **Authentication system** — JWT with refresh rotation.
2. **RBAC system** — role-based endpoint protection.
3. **Secret management** — .env + .env.example pattern.
4. **Input validation** — Pydantic + file validation.
5. **Audit logging** — all security events captured.
6. **Security documentation** — setup and configuration guide.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `fastapi-backend` | Authentication and authorization integration |
| `flutter-mobile` | Secure credential storage on device |
| `database-engineering` | Audit log table, user/role tables |
| `devops` | Production secret management |
| `testing` | Security tests |
