# ONION_SURE — Cross-Skill Rules and Agent Behavior

## Project Identity

- **Project:** ONION_SURE
- **Competition:** Smart India Hackathon 2026
- **Problem Statement:** PS26031 — AI-based onion quality assessment and grading
- **Organization:** Ministry of Consumer Affairs, Food & Public Distribution
- **Department:** Department of Consumer Affairs (DoCA)
- **Theme:** Smart Automation

---

## Mandatory Cross-Skill Rules

Every agent working on this repository MUST follow these rules regardless of the task:

1. **Inspect before modifying.** Read existing code, configuration, and structure before making any change.
2. **Preserve existing working code.** Do not blindly rewrite files. Modify surgically.
3. **Never fabricate data.** Do not invent dataset samples, labels, or annotations.
4. **Never fabricate AI predictions.** Do not generate fake inference results or confidence scores.
5. **Never fabricate metrics.** Do not invent accuracy, precision, recall, F1, or any evaluation metric.
6. **Never fabricate model accuracy.** Do not claim a model achieves a performance level without evaluation evidence.
7. **Never fabricate labels.** Do not convert `Healthy/Unhealthy` into `Rotten/Damaged/Sprouted/Undersized` without evidence-based annotation.
8. **Never claim a feature is implemented when it is only mocked.** Clearly mark mocks, stubs, and placeholders.
9. **Never use an LLM as the authoritative grading engine.** Grading must be deterministic, rule-based, and auditable.
10. **Never claim physical measurements without calibration.** If no reference marker or calibration is available, return `measurement_unavailable`.
11. **Never hardcode secrets.** Use environment variables or secret managers for API keys, passwords, tokens, and credentials.
12. **Never bypass tests.** Do not skip, delete, or ignore failing tests without explicit justification and approval.
13. **Never silently change database schema.** All schema changes must go through migrations.
14. **Never silently delete data.** Use soft-delete where appropriate. Document any data removal.
15. **Record important architectural decisions.** Use ADRs or documented comments for non-obvious choices.
16. **Prefer modular implementations.** Avoid monolithic files. Keep concerns separated.
17. **Keep ML, backend, mobile, and grading logic separable.** Each domain must be independently testable.
18. **Make failures explicit.** Never swallow exceptions silently. Log and surface errors.
19. **Use meaningful error messages.** Include context about what failed and why.
20. **Maintain reproducibility.** Pin dependencies, seed random generators, version datasets and models.

---

## Dataset Protection

- The `Red and White Onion Dataset/` directory is **source data** and must NOT be modified or deleted.
- Any derived datasets (cleaned, split, augmented) must be stored in separate directories.
- The existing `Healthy/Unhealthy` labels are the original labels. They must not be silently relabeled.

---

## Skill Activation Rule

When a task is received, the agent MUST first determine which project skills apply before writing any code.

Read the relevant `SKILL.md` files from `.agents/skills/` before proceeding.

### Activation Matrix

| Task Type | Primary Skills | Conditional Skills |
|:---|:---|:---|
| Dataset task | `dataset-engineering`, `ml-training-evaluation` | `ps26031-requirements` |
| AI / Computer Vision task | `computer-vision`, `ml-training-evaluation` | `onion-measurement` (if size involved) |
| Grading task | `grading-engine`, `computer-vision`, `onion-measurement` | `testing` |
| Flutter / Mobile task | `flutter-mobile`, `api-integration` | `offline-sync` (if offline involved) |
| Backend task | `fastapi-backend`, `database-engineering`, `security`, `testing` | `api-integration` |
| Report task | `reporting-qr`, `fastapi-backend`, `testing` | `security` |
| Database task | `database-engineering`, `security` | `testing` |
| Security task | `security` | `fastapi-backend`, `flutter-mobile` |
| Testing task | `testing` | All relevant implementation skills |
| DevOps task | `devops` | `security`, `database-engineering` |
| Documentation task | `documentation` | `ps26031-requirements` |
| Code review task | `code-review` | All relevant implementation skills |
| Demo / presentation task | `demo-validation`, `testing` | All relevant implementation skills |
| Any task modifying code | `repository-audit` (first) | Task-specific skills |

### Activation Procedure

1. Identify the task type from the user's request.
2. Look up the activation matrix above.
3. Read the `SKILL.md` for each applicable skill.
4. Follow the workflow, rules, and constraints in each skill.
5. If multiple skills apply, satisfy ALL their constraints — they do not override each other.

---

## MVP vs Future Features

### MANDATORY MVP (PS26031)

These are required by the problem statement:

- Image capture and validation
- Onion detection in images
- Defect identification (damaged, rotten, sprouted)
- Size assessment (undersized detection)
- Deterministic grading (Grade A, URS)
- Grade A / URS percentage estimation per lot
- Human review capability
- Digital quality report generation
- QR-code-based verification
- Auditability and transparency

### NOT MVP — Do Not Build Unless Explicitly Requested

- Marketplace / auction features
- Payment processing
- Logistics / supply chain tracking
- Insurance integration
- Weather data integration
- Price prediction
- Blockchain
- Social features
- Gamification
- Any feature not described in PS26031

---

## Architecture Invariants

1. **Grading is deterministic.** CV model → structured observations → grading policy → grade. No LLM in the grading path.
2. **Measurement requires calibration.** No pixel-to-mm conversion without a physical reference.
3. **AI confidence is always reported.** Every detection/classification result includes a confidence score.
4. **Offline-first mobile.** The app must function without network connectivity for core inspection workflows.
5. **Reports are verifiable.** Every report has a unique ID and QR code for independent verification.
6. **Models are versioned.** Every inference result is traceable to a specific model version.
7. **Grading policies are versioned.** Every grade is traceable to a specific policy version.
