---
name: testing
description: >-
  Defines testing standards for ONION_SURE across all components: unit tests,
  integration tests, API tests, ML evaluation tests, grading-policy tests,
  database tests, Flutter tests, offline-sync tests, and end-to-end tests.
  Includes mandatory grading test cases for PS26031 compliance. Activate for
  any testing, quality assurance, or test-writing task.
---

# Testing Skill

## Purpose

Ensure comprehensive, meaningful test coverage across all ONION_SURE
components. Tests are not optional — they are required for grading logic,
AI evaluation, API endpoints, and critical workflows.

## When to Use

- Writing tests for new features.
- Reviewing test coverage.
- Implementing CI test pipelines.
- Validating grading logic correctness.
- Evaluating ML model performance.
- Testing offline sync workflows.
- End-to-end demo validation.

## Required Inputs

- Feature or component to test.
- Expected behavior and edge cases.
- Test data (or instructions to create it).

---

## Test Categories

### 1. Unit Tests

Test individual functions and classes in isolation.

| Component | Framework | Location |
|:---|:---|:---|
| Backend (Python) | `pytest` | `backend/tests/unit/` |
| Grading Engine | `pytest` | `backend/tests/unit/test_grading_engine.py` |
| ML Inference | `pytest` | `backend/tests/unit/test_inference.py` |
| Measurement | `pytest` | `backend/tests/unit/test_measurement.py` |
| Flutter (Dart) | `flutter_test` | `mobile/test/unit/` |

### 2. Integration Tests

Test component interactions.

| Test | Description |
|:---|:---|
| API + Database | Endpoint creates/reads correct DB records |
| API + AI Inference | Inspection endpoint triggers real inference |
| Grading + CV | Structured observations produce correct grades |
| Sync + API | Offline sync correctly uploads to server |

### 3. API Tests

Test every API endpoint.

```python
# Using httpx with FastAPI TestClient
async def test_create_inspection(client, auth_headers):
    response = await client.post(
        "/api/v1/inspections",
        json={"lot_id": "...", "images": [...]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "inspection_id" in data["data"]
```

### 4. ML Evaluation Tests

Test model performance against thresholds.

```python
def test_model_minimum_accuracy():
    """Model must meet minimum accuracy on test set."""
    results = evaluate_model(model, test_dataset)
    assert results["accuracy"] >= 0.80, f"Accuracy {results['accuracy']} below 0.80"

def test_model_per_class_recall():
    """Every defect class must have minimum recall."""
    results = evaluate_model(model, test_dataset)
    for class_name, recall in results["per_class_recall"].items():
        assert recall >= 0.70, f"{class_name} recall {recall} below 0.70"
```

### 5. Grading Policy Tests (MANDATORY)

These are the most critical tests. The grading engine must be deterministic
and independently testable.

```python
class TestGradingEngine:
    """Test every grading scenario required by PS26031."""

    def test_grade_a_healthy_full_size(self):
        """Healthy onion with acceptable size → Grade A."""
        observation = OnionObservation(
            defect_class="HEALTHY",
            defect_confidence=0.95,
            size_status="ACCEPTABLE_SIZE",
            diameter_mm=55.0,
            measurement_status="measured",
        )
        result = grading_engine.grade(observation, policy_v1)
        assert result.grade == "GRADE_A"
        assert "HEALTHY_FULL_SIZE" in result.reason_codes

    def test_undersized_onion(self):
        """Onion below size threshold → Reject (undersized)."""
        observation = OnionObservation(
            defect_class="HEALTHY",
            defect_confidence=0.90,
            size_status="UNDERSIZED",
            diameter_mm=35.0,
            measurement_status="measured",
        )
        result = grading_engine.grade(observation, policy_v1)
        assert result.grade in ["REJECT", "URS"]
        assert "UNDERSIZED" in result.reason_codes

    def test_rotten_onion(self):
        """Rotten onion → Reject."""
        observation = OnionObservation(
            defect_class="ROTTEN",
            defect_confidence=0.88,
            size_status="ACCEPTABLE_SIZE",
            diameter_mm=50.0,
            measurement_status="measured",
        )
        result = grading_engine.grade(observation, policy_v1)
        assert result.grade == "REJECT"
        assert "ROTTEN_DETECTED" in result.reason_codes

    def test_sprouted_onion(self):
        """Sprouted onion → Reject."""
        observation = OnionObservation(
            defect_class="SPROUTED",
            defect_confidence=0.85,
            size_status="ACCEPTABLE_SIZE",
            diameter_mm=52.0,
            measurement_status="measured",
        )
        result = grading_engine.grade(observation, policy_v1)
        assert result.grade == "REJECT"
        assert "SPROUTED_DETECTED" in result.reason_codes

    def test_damaged_onion(self):
        """Damaged onion → URS or Reject depending on severity."""
        observation = OnionObservation(
            defect_class="DAMAGED",
            defect_confidence=0.82,
            size_status="ACCEPTABLE_SIZE",
            diameter_mm=48.0,
            measurement_status="measured",
        )
        result = grading_engine.grade(observation, policy_v1)
        assert result.grade in ["URS", "REJECT"]

    def test_low_confidence_triggers_manual_review(self):
        """Low confidence → Manual Review."""
        observation = OnionObservation(
            defect_class="HEALTHY",
            defect_confidence=0.35,
            size_status="ACCEPTABLE_SIZE",
            diameter_mm=50.0,
            measurement_status="measured",
        )
        result = grading_engine.grade(observation, policy_v1)
        assert result.grade == "MANUAL_REVIEW"
        assert result.requires_review is True

    def test_unavailable_measurement(self):
        """No calibration → measurement unavailable, handled gracefully."""
        observation = OnionObservation(
            defect_class="HEALTHY",
            defect_confidence=0.90,
            size_status="UNDETERMINED",
            diameter_mm=None,
            measurement_status="measurement_unavailable",
        )
        result = grading_engine.grade(observation, policy_v1)
        # Should be URS (healthy but size unverified) or Manual Review
        assert result.grade in ["URS", "MANUAL_REVIEW"]

    def test_conflicting_evidence(self):
        """Conflicting signals → Manual Review."""
        observation = OnionObservation(
            defect_class="HEALTHY",
            defect_confidence=0.51,  # Barely healthy
            size_status="UNDERSIZED",
            diameter_mm=38.0,
            measurement_status="measured",
        )
        result = grading_engine.grade(observation, policy_v1)
        assert result.grade == "MANUAL_REVIEW"

    def test_manual_override_logged(self):
        """Human override is recorded with reason."""
        result = grading_engine.grade(observation, policy_v1)
        overridden = grading_engine.apply_override(
            result,
            new_grade="GRADE_A",
            reviewer_id="reviewer-uuid",
            reason="Visual inspection confirms healthy, large onion",
        )
        assert overridden.grade == "GRADE_A"
        assert overridden.reviewed_by == "reviewer-uuid"
        assert overridden.review_reason is not None

    def test_deterministic_grading(self):
        """Same input + same policy → same output, always."""
        observation = OnionObservation(
            defect_class="HEALTHY",
            defect_confidence=0.90,
            size_status="ACCEPTABLE_SIZE",
            diameter_mm=55.0,
            measurement_status="measured",
        )
        results = [grading_engine.grade(observation, policy_v1) for _ in range(100)]
        grades = {r.grade for r in results}
        assert len(grades) == 1, "Grading is not deterministic!"
```

### 6. Database Tests

```python
def test_migration_upgrade_downgrade():
    """All migrations can be applied and rolled back."""
    alembic_upgrade("head")
    alembic_downgrade("base")
    alembic_upgrade("head")

def test_audit_log_created_on_inspection():
    """Creating an inspection generates an audit log entry."""
    inspection = create_inspection(...)
    audit = get_audit_logs(entity_type="inspection", entity_id=inspection.id)
    assert len(audit) == 1
    assert audit[0].action == "CREATE"
```

### 7. Flutter Tests

```dart
// Unit test
test('GradingResult correctly parses JSON', () {
  final json = {'grade': 'GRADE_A', 'confidence': 0.95};
  final result = GradingResult.fromJson(json);
  expect(result.grade, equals('GRADE_A'));
  expect(result.confidence, equals(0.95));
});

// Widget test
testWidgets('InspectionPage shows loading state', (tester) async {
  await tester.pumpWidget(InspectionPage());
  expect(find.byType(CircularProgressIndicator), findsOneWidget);
});
```

### 8. Offline Sync Tests

```python
def test_no_duplicate_on_retry():
    """Retrying a sync does not create duplicate records."""
    item = create_sync_item(idempotency_key="test-key-123")
    sync_result_1 = sync_manager.process(item)
    sync_result_2 = sync_manager.process(item)  # Retry
    assert count_server_records(idempotency_key="test-key-123") == 1

def test_sync_respects_dependency_order():
    """Images sync after their parent inspection."""
    ...
```

### 9. End-to-End Tests

```python
def test_full_inspection_workflow():
    """Complete PS26031 workflow from login to report."""
    # Login
    token = login("operator", "password")
    # Create inspection
    inspection = create_inspection(lot_id, token)
    # Upload image
    upload_image(inspection.id, "test_onion.jpg", token)
    # Run inference
    results = run_inference(inspection.id, token)
    assert len(results) > 0
    # Check grading
    summary = get_lot_summary(inspection.id, token)
    assert summary.grade_a_percentage + summary.urs_percentage + summary.reject_percentage == approx(100.0)
    # Generate report
    report = generate_report(inspection.id, token)
    assert report.verification_id is not None
    # Verify via QR
    verification = verify_report(report.verification_id)
    assert verification.status == "VALID"
```

---

## Implementation Rules

1. **Grading tests are mandatory** — the grading engine must have comprehensive tests.
2. **Tests must be automated** — runnable via `pytest` / `flutter test`.
3. **Tests must not depend on external services** — use mocks/fixtures for DB, API.
4. **Tests must not fabricate passing results** — test real logic.
5. **ML evaluation tests have minimum thresholds** — not just "it runs."
6. **Offline sync tests verify idempotency** — no duplicate records.
7. **API tests cover success, error, and auth cases.**

---

## Forbidden Behavior

- ❌ Skipping tests for grading logic.
- ❌ Writing tests that always pass regardless of implementation.
- ❌ Mocking the grading engine in grading tests (test the real engine).
- ❌ Fabricating test results or metrics.
- ❌ Deleting failing tests instead of fixing them.
- ❌ Testing against production data or databases.

---

## Expected Outputs

1. **Test suites** — for each component.
2. **Test coverage report** — showing coverage percentage.
3. **CI configuration** — automated test execution.
4. **Test data fixtures** — reproducible test inputs.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `grading-engine` | Mandatory grading policy tests |
| `fastapi-backend` | API test targets |
| `flutter-mobile` | Flutter test targets |
| `ml-training-evaluation` | ML evaluation tests |
| `offline-sync` | Sync and idempotency tests |
| `database-engineering` | Migration and integrity tests |
| `computer-vision` | Inference tests |
