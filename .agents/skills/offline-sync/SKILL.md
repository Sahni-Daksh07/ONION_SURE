---
name: offline-sync
description: >-
  Governs offline-first architecture for the ONION_SURE mobile app. Defines
  local persistence, sync queue, retry with idempotency, conflict resolution,
  and state machine for sync items. Prevents duplicate inspections from retries.
  Activate when any task involves offline capability, data synchronization,
  or network resilience.
---

# Offline Sync Skill

## Purpose

Ensure the ONION_SURE mobile app can perform full inspection workflows without
network connectivity, and reliably synchronize data when connectivity returns.
Field procurement centers may have unreliable or no internet access.

## When to Use

- Implementing offline data persistence.
- Building the sync queue and retry mechanism.
- Handling conflict resolution.
- Implementing upload status tracking.
- Testing offline workflows.
- Debugging sync issues.

## Required Inputs

- Data entities to be synced (inspections, images, results).
- API contract for sync endpoints (from `api-integration`).
- Conflict resolution policy.

---

## Sync State Machine

Every syncable record has a sync status:

```
                  ┌──────────────┐
          Create  │              │
     ────────────►│   PENDING    │
                  │              │
                  └──────┬───────┘
                         │ Start sync
                  ┌──────▼───────┐
                  │              │
                  │   SYNCING    │
                  │              │
                  └──┬───┬───┬───┘
           Success │   │   │ Conflict
        ┌──────────┘   │   └──────────┐
        │         Fail │              │
  ┌─────▼─────┐  ┌─────▼─────┐  ┌────▼────────────┐
  │           │  │           │  │                  │
  │  SYNCED   │  │  FAILED   │  │    CONFLICT      │
  │           │  │           │  │                  │
  └───────────┘  └─────┬─────┘  └────┬─────────────┘
                       │ Retry       │ Resolve
                  ┌────▼────┐   ┌────▼────────────┐
                  │         │   │                  │
                  │ SYNCING │   │ REQUIRES_ACTION  │
                  │ (retry) │   │                  │
                  └─────────┘   └──────────────────┘
```

### States

| State | Description |
|:---|:---|
| `PENDING` | Created locally, waiting to sync |
| `SYNCING` | Currently being uploaded |
| `SYNCED` | Successfully synchronized with server |
| `FAILED` | Sync attempt failed (will retry) |
| `CONFLICT` | Server has conflicting data |
| `REQUIRES_ACTION` | User intervention needed |

---

## Sync Queue Architecture

```
┌─────────────────────────┐
│  Local Database          │
│  (SQLite / Hive)         │
│                          │
│  ┌────────────────────┐  │
│  │ Inspections        │  │
│  │ Images (file refs) │  │
│  │ Detections         │  │
│  │ Grade Results      │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ Sync Queue         │  │
│  │ - entity_type      │  │
│  │ - entity_id        │  │
│  │ - operation (CRUD) │  │
│  │ - sync_status      │  │
│  │ - retry_count      │  │
│  │ - idempotency_key  │  │
│  │ - created_at       │  │
│  │ - last_attempt_at  │  │
│  │ - error_message    │  │
│  └────────────────────┘  │
└────────────┬────────────┘
             │
             ▼ (when online)
┌────────────────────────┐
│  Sync Manager           │
│  - Process queue FIFO   │
│  - Respect dependencies │
│  - Handle retries       │
│  - Resolve conflicts    │
│  - Update status        │
└────────────┬────────────┘
             │
             ▼
┌────────────────────────┐
│  Backend API            │
│  /api/v1/sync/          │
└────────────────────────┘
```

---

## Idempotency (Critical)

### The Rule

**The same inspection must NEVER be created twice on the server due to a
retry.**

### Implementation

1. Every syncable entity gets a UUID `idempotency_key` at creation time.
2. The server checks the idempotency key before creating records.
3. If the key already exists, the server returns the existing record (200, not 409).
4. The client uses the server response to update local sync status.

```python
# Server-side
@router.post("/api/v1/sync/inspections")
async def sync_inspection(data: SyncInspectionRequest):
    existing = await repo.get_by_idempotency_key(data.idempotency_key)
    if existing:
        return existing  # Already synced — return existing
    return await repo.create(data)
```

```dart
// Client-side
class SyncQueueItem {
  final String idempotencyKey;  // UUID generated at creation
  final String entityType;
  final String entityId;
  final SyncStatus status;
  final int retryCount;
  final int maxRetries;
  final DateTime createdAt;
  final DateTime? lastAttemptAt;
  final String? errorMessage;
}
```

---

## Offline Workflow

### Inspection Without Network

```
1. Operator opens app (offline mode detected)
2. Creates inspection from cached farmer/lot data
3. Captures onion images → stored locally
4. Runs on-device inference (if TFLite model available)
   OR marks images for server-side inference
5. Records results locally
6. Queue items added with PENDING status
7. UI shows "Pending Sync" indicator
```

### When Network Returns

```
1. Connectivity detected
2. Sync Manager starts processing queue
3. Items processed in dependency order:
   a. Inspections first
   b. Images second (linked to inspection)
   c. Detection results third
   d. Grade results fourth
4. Each item: PENDING → SYNCING → SYNCED/FAILED
5. Failed items: exponential backoff retry
6. UI updates sync progress
```

---

## Retry Strategy

```yaml
retry:
  max_retries: 5
  initial_delay_seconds: 5
  backoff_multiplier: 2
  max_delay_seconds: 300
  retry_on:
    - network_timeout
    - server_5xx
    - connection_refused
  no_retry_on:
    - 400_bad_request
    - 401_unauthorized
    - 403_forbidden
    - 422_validation_error
```

---

## Conflict Resolution

| Scenario | Resolution |
|:---|:---|
| Server has newer data | Flag as CONFLICT, show both versions |
| Client data is newer | Upload client data (last-write-wins) |
| Duplicate detection | Use idempotency key to resolve |
| Schema mismatch | Flag as REQUIRES_ACTION |

---

## Implementation Rules

1. **Every syncable entity has an idempotency key** — UUID assigned at creation.
2. **Sync queue is persisted locally** — survives app restart.
3. **Process queue in dependency order** — parents before children.
4. **Exponential backoff on retries** — don't hammer a down server.
5. **Don't retry client errors** (4xx) — they won't succeed on retry.
6. **Show sync status in UI** — users must know what's pending.
7. **Handle partial sync** — some items synced, some pending.
8. **Log all sync attempts** — for debugging.

---

## Validation Rules

- ✅ No duplicate records created by retries (idempotency verified).
- ✅ Sync queue survives app restart.
- ✅ Dependencies are respected (inspection before images).
- ✅ Failed items are retried with backoff.
- ✅ Conflicts are surfaced to the user.
- ✅ UI reflects current sync state.

---

## Forbidden Behavior

- ❌ Creating duplicate server records from retries.
- ❌ Silently dropping unsynced data.
- ❌ Retrying client errors (400, 401, 403, 422).
- ❌ Processing queue out of dependency order.
- ❌ Blocking the UI during sync operations.
- ❌ Ignoring conflict states.

---

## Expected Outputs

1. **Local database** — offline-capable data persistence.
2. **Sync queue** — persistent, ordered, with status tracking.
3. **Sync manager** — handles upload, retry, conflict resolution.
4. **UI indicators** — sync status on all relevant screens.
5. **Idempotency** — verified no-duplicate guarantee.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `flutter-mobile` | UI integration, local storage |
| `api-integration` | Sync API contract |
| `fastapi-backend` | Server-side idempotency handling |
| `database-engineering` | Local database schema |
| `testing` | Offline and sync tests |
