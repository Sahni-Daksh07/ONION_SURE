---
name: code-review
description: >-
  Defines code review standards for ONION_SURE: correctness, architecture,
  security, performance, maintainability, tests, error handling, backward
  compatibility, duplication, hardcoded values, fake implementations, logging,
  and documentation. Flags high-risk changes. Activate before approving any
  code change, PR, or merge.
---

# Code Review Skill

## Purpose

Ensure every code change meets ONION_SURE quality standards before merging.
Prevent regressions, security issues, architectural violations, and fake
implementations from entering the codebase.

## When to Use

- Reviewing pull requests or code changes.
- Before merging any branch.
- After significant refactoring.
- When evaluating external contributions.
- During self-review before committing.

## Required Inputs

- Code diff or changed files.
- Context about what the change is trying to accomplish.
- Related skills that should be checked.

---

## Review Checklist

### 1. Correctness

- [ ] Does the code do what it claims to do?
- [ ] Are edge cases handled?
- [ ] Are boundary conditions checked?
- [ ] Is the logic sound and verifiable?

### 2. Architecture

- [ ] Does this follow the established architecture? (Clean architecture, separation of concerns)
- [ ] Is the code in the right module/layer?
- [ ] Does it introduce unnecessary coupling?
- [ ] Is it consistent with existing patterns?

### 3. Security

- [ ] No secrets, API keys, or credentials in code?
- [ ] Input validation present?
- [ ] File uploads validated?
- [ ] Authentication/authorization enforced?
- [ ] SQL injection prevention (parameterized queries)?
- [ ] No sensitive data in logs?

### 4. Performance

- [ ] No unnecessary database queries (N+1 problem)?
- [ ] Appropriate use of indexes?
- [ ] Image processing not blocking the main thread?
- [ ] Batch operations where appropriate?

### 5. Maintainability

- [ ] Code is readable and well-named?
- [ ] Functions are focused (single responsibility)?
- [ ] No magic numbers or strings (use constants)?
- [ ] Complex logic is commented?
- [ ] Consistent code style?

### 6. Tests

- [ ] New functionality has tests?
- [ ] Existing tests still pass?
- [ ] Grading logic changes have grading tests?
- [ ] Edge cases are tested?
- [ ] Tests are meaningful (not always-pass)?

### 7. Error Handling

- [ ] Errors are caught and handled?
- [ ] Error messages are meaningful?
- [ ] Failures are logged?
- [ ] User-facing errors are friendly?
- [ ] No silent exception swallowing?

### 8. Backward Compatibility

- [ ] API changes are backward-compatible (or versioned)?
- [ ] Database changes have migrations?
- [ ] Configuration changes are documented?
- [ ] Existing functionality preserved?

### 9. Duplication

- [ ] No copy-paste code?
- [ ] Shared logic extracted to utilities?
- [ ] No reimplementation of existing functionality?

### 10. Hardcoded Values

- [ ] No hardcoded URLs, paths, or credentials?
- [ ] Configuration values from environment?
- [ ] Thresholds and policies in configuration files?

### 11. Fake Implementations

- [ ] No fabricated AI predictions?
- [ ] No fabricated grading results?
- [ ] No fabricated metrics?
- [ ] Mocks clearly marked as mocks (not in production paths)?
- [ ] No `TODO: implement later` in production code paths?

### 12. Logging

- [ ] Important operations are logged?
- [ ] Log levels are appropriate?
- [ ] No sensitive data in logs?
- [ ] Structured logging format used?

### 13. Documentation

- [ ] Public APIs are documented?
- [ ] Complex logic has inline comments?
- [ ] README updated if needed?
- [ ] Architecture docs updated if needed?

---

## High-Risk Change Indicators

Flag the following for extra scrutiny:

| Indicator | Risk | Action |
|:---|:---|:---|
| Grading logic changes | Grade calculation affected | Require grading tests |
| Database schema changes | Data integrity risk | Require migration review |
| Authentication changes | Security risk | Security review |
| AI model changes | Prediction quality affected | Evaluation results required |
| Offline sync changes | Data loss risk | Idempotency tests required |
| File handling changes | Security risk | Upload validation review |
| Environment config changes | Deployment risk | All environments checked |
| Dependency updates | Compatibility risk | Test suite must pass |

---

## Review Outcomes

| Outcome | Description |
|:---|:---|
| **Approve** | All checks pass, safe to merge |
| **Request Changes** | Issues found, must be addressed |
| **Needs Discussion** | Architectural or design concerns to discuss |
| **Block** | Critical issue (security, data integrity, fabrication) |

### Blocking Issues (Immediate Block)

- Committed secrets or credentials
- Fabricated AI results or metrics
- LLM used as grading engine
- Test set used for training
- Production data exposed
- Database schema changed without migration
- Silent data deletion

---

## Implementation Rules

1. **Every change is reviewed** — no direct commits to main.
2. **High-risk changes get extra scrutiny.**
3. **Blocking issues must be resolved before merge.**
4. **Tests must pass before review is complete.**
5. **Architecture violations are discussed, not silently approved.**

---

## Forbidden Behavior

- ❌ Approving changes with committed secrets.
- ❌ Approving fabricated AI results or metrics.
- ❌ Approving changes without tests for critical logic.
- ❌ Approving database changes without migrations.
- ❌ Rubber-stamping reviews without reading the code.
- ❌ Ignoring blocking issues.

---

## Expected Outputs

1. **Review decision** — Approve, Request Changes, Needs Discussion, or Block.
2. **Review comments** — specific, actionable feedback.
3. **Risk assessment** — high-risk items flagged.
4. **Checklist completion** — all items verified.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `testing` | Verify test coverage |
| `security` | Security review criteria |
| `grading-engine` | Grading logic review |
| `database-engineering` | Migration review |
| `computer-vision` | AI model change review |
| `documentation` | Documentation review |
