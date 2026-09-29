---
name: database-engineering
description: >-
  Governs database design for ONION_SURE: normalized schemas, migrations,
  foreign keys, indexes, constraints, timestamps, audit fields, soft deletion,
  and transaction integrity. Never change production schema without a migration.
  Activate for any database, schema, or migration task.
---

# Database Engineering Skill

## Purpose

Ensure that all database design and modifications follow disciplined engineering
practices. Every schema change must be versioned, reversible, and auditable.

## When to Use

- Designing or modifying database tables.
- Creating or reviewing migrations.
- Adding indexes or constraints.
- Implementing audit fields.
- Reviewing database performance.
- Handling data integrity issues.

## Required Inputs

- Entity requirements (from `fastapi-backend` or feature specification).
- Existing schema (if modifying).

---

## Schema Design Rules

### Required Fields on Every Table

```sql
-- Every table must have:
id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

-- Tables with user-created records should also have:
created_by      UUID REFERENCES users(id),
updated_by      UUID REFERENCES users(id),

-- Tables supporting soft delete:
is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
deleted_at      TIMESTAMP WITH TIME ZONE,
deleted_by      UUID REFERENCES users(id)
```

### Normalization

- Use at least Third Normal Form (3NF) for transactional data.
- Denormalize only for read-heavy reporting views with documented justification.

### Foreign Keys

- Every relationship MUST have a foreign key constraint.
- Use `ON DELETE` policies explicitly (`RESTRICT`, `CASCADE`, `SET NULL`).
- Default to `ON DELETE RESTRICT` unless there's a documented reason otherwise.

### Indexes

- Primary keys are automatically indexed.
- Add indexes on frequently queried columns (foreign keys, status fields, dates).
- Add composite indexes for common query patterns.
- Document the reason for each index.

### Constraints

- Use `NOT NULL` unless the field is genuinely optional.
- Use `CHECK` constraints for enum-like fields.
- Use `UNIQUE` constraints where business rules require uniqueness.

---

## Migration Rules

### Alembic Workflow

```bash
# Create a new migration
alembic revision --autogenerate -m "descriptive_message"

# Review the generated migration before applying
# NEVER auto-apply without review

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Migration Requirements

1. **Every migration must be reversible** — implement both `upgrade()` and `downgrade()`.
2. **Never modify a deployed migration** — create a new one instead.
3. **Migration messages must be descriptive** — e.g., `add_defect_confidence_to_detection`.
4. **Review auto-generated migrations** — Alembic may miss or misinterpret changes.
5. **Test migrations** — apply and rollback in a test environment before production.
6. **Data migrations separate from schema migrations** — don't mix DDL and DML.

---

## Audit Table

```sql
CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     VARCHAR(100) NOT NULL,
    entity_id       UUID NOT NULL,
    action          VARCHAR(20) NOT NULL,  -- CREATE, UPDATE, DELETE, REVIEW
    changes         JSONB,                 -- {field: {old: x, new: y}}
    performed_by    UUID REFERENCES users(id),
    performed_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ip_address      INET,
    user_agent      TEXT,
    metadata        JSONB
);

CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_user ON audit_log(performed_by);
CREATE INDEX idx_audit_time ON audit_log(performed_at);
```

---

## Transaction Integrity

- Use database transactions for multi-table operations.
- Inspection creation (inspection + images + detections + grades) must be atomic.
- Use `SERIALIZABLE` isolation for grading operations if concurrency is a concern.
- Handle deadlocks with retry logic.

---

## Implementation Rules

1. **Every schema change goes through Alembic** — no manual DDL on production.
2. **Every table has timestamp fields** (`created_at`, `updated_at`).
3. **Every table has a UUID primary key** — not auto-increment integers.
4. **Foreign keys are mandatory** for all relationships.
5. **Soft delete for important entities** — inspections, reports, grade results.
6. **Audit log for all state changes** — who changed what and when.
7. **Index foreign keys** — they're used in JOINs.
8. **Test migrations** — both upgrade and downgrade.

---

## Validation Rules

- ✅ Every migration has both `upgrade()` and `downgrade()`.
- ✅ All tables have `id`, `created_at`, `updated_at`.
- ✅ All relationships have foreign keys.
- ✅ Important entities support soft delete.
- ✅ Audit logging captures all state changes.
- ✅ No schema changes without a migration file.

---

## Forbidden Behavior

- ❌ Modifying production schema without a migration.
- ❌ Dropping tables or columns without a migration and documentation.
- ❌ Using auto-increment integer IDs (use UUIDs).
- ❌ Missing foreign key constraints on relationships.
- ❌ Irreversible migrations without explicit documentation.
- ❌ Hard-deleting records that should be soft-deleted.
- ❌ Skipping the audit log for state changes.
- ❌ Mixing schema and data changes in one migration.

---

## Expected Outputs

1. **Database schema** — normalized, documented, with all constraints.
2. **Alembic migrations** — reversible, tested, descriptive.
3. **Audit table** — capturing all state changes.
4. **Index documentation** — why each index exists.
5. **ERD** — entity relationship diagram (when schema is significant).

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `fastapi-backend` | Defines entities and relationships |
| `security` | Credential storage, access patterns |
| `testing` | Database migration and integrity tests |
| `devops` | Migration execution in deployment |
