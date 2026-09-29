---
name: repository-audit
description: >-
  Performs a comprehensive audit of the ONION_SURE repository before any code
  modification. Inspects structure, source code, configuration, dependencies,
  models, tests, documentation, and datasets. Produces an audit report with
  current state, gaps, risks, and recommended next steps. Must be activated
  before any task that modifies existing code.
---

# Repository Audit Skill

## Purpose

Ensure that every agent inspects and understands the current state of the
ONION_SURE repository before making any modifications. Prevents blind rewrites,
accidental deletions, and architectural violations.

## When to Use

- **ALWAYS** before the first code modification in a session.
- Before adding new features — understand what already exists.
- Before refactoring — identify dependencies and risks.
- Before fixing bugs — understand the surrounding code.
- When onboarding to the project — get a complete picture.
- Periodically — to track technical debt accumulation.

## Required Inputs

- Access to the repository root directory.
- No additional inputs required — the skill inspects the repository directly.

---

## Audit Workflow

### Step 1: Repository Structure Scan

Inspect and document the directory tree:

```
ONION_SURE/
├── .agents/              # Agent skills and rules
├── .git/                 # Version control
├── .gitignore            # Ignore rules
├── README.md             # Project documentation
├── Red and White Onion Dataset/  # SOURCE DATA — DO NOT MODIFY
│   └── New Onion/
│       ├── Bulb/
│       │   ├── Healthy/    # ~12,367 images
│       │   └── Unhealthy/  # ~5,461 images
│       └── Leaves/
│           ├── Healthy/    # ~3,104 images
│           └── Unhealthy/  # ~3,068 images
├── backend/              # FastAPI backend (if exists)
├── mobile/               # Flutter app (if exists)
├── ml/                   # ML training and models (if exists)
├── data/                 # Processed/derived datasets (if exists)
├── docs/                 # Documentation (if exists)
├── tests/                # Test suites (if exists)
├── docker/               # Docker configuration (if exists)
└── scripts/              # Utility scripts (if exists)
```

### Step 2: Component Inspection

For each component that exists, inspect:

| Component | What to Check |
|:---|:---|
| **Source Code** | Languages, frameworks, architecture patterns, code quality |
| **Configuration** | Environment files, Docker configs, CI/CD, settings |
| **Dependencies** | Package manifests (`requirements.txt`, `pubspec.yaml`, `pyproject.toml`) |
| **Models** | Trained model files, model configs, model versions |
| **Notebooks** | Jupyter notebooks, training experiments |
| **Scripts** | Utility scripts, data processing scripts |
| **Tests** | Test files, test coverage, test configuration |
| **Documentation** | README, docs/, inline documentation |
| **Dataset** | Original dataset integrity, derived datasets |
| **Environment** | `.env` files, secrets handling, environment variables |
| **Docker** | Dockerfiles, docker-compose, build configs |
| **Mobile Code** | Flutter project structure, state management, API integration |
| **Backend Code** | API routes, models, migrations, services |
| **ML Code** | Training pipelines, evaluation, inference, data loading |

### Step 3: Produce Audit Report

The audit report MUST contain these sections:

1. **Current Architecture** — What exists and how it's organized.
2. **Existing Implementation** — What is actually implemented and working.
3. **Missing Implementation** — What PS26031 requires but is not yet built.
4. **Duplicate Code** — Any redundant implementations found.
5. **Technical Debt** — Code quality issues, outdated dependencies, missing tests.
6. **Risks** — Security issues, data integrity risks, architectural concerns.
7. **Dependencies** — External dependencies and their versions/status.
8. **Recommended Next Step** — The single most impactful next action.

---

## Implementation Rules

1. **Read-only by default.** The audit does not modify any files.
2. **Be thorough.** Check every directory and major file.
3. **Be honest.** Report what actually exists, not what should exist.
4. **Distinguish implemented from planned.** Do not report planned features as existing.
5. **Check the dataset.** Verify the original dataset is intact and unmodified.
6. **Check for secrets.** Flag any committed credentials, API keys, or tokens.
7. **Check .gitignore.** Verify that sensitive files and large binaries are excluded.

---

## Validation Rules

The audit is valid if:

- ✅ Every directory in the repository root was inspected.
- ✅ The original dataset integrity was verified (not modified/deleted).
- ✅ Existing code was identified with its actual functionality (not assumed).
- ✅ Missing PS26031 requirements were identified.
- ✅ No files were modified during the audit.
- ✅ Security risks (committed secrets) were checked.

---

## Forbidden Behavior

- ❌ Modifying any file during an initial audit (unless explicitly instructed).
- ❌ Deleting or moving the original dataset.
- ❌ Reporting a feature as "implemented" when it is only stubbed or mocked.
- ❌ Skipping the dataset inspection.
- ❌ Ignoring test coverage gaps.
- ❌ Assuming code works without checking.

---

## Expected Outputs

1. **Audit Report** — structured document with all 8 sections above.
2. **Risk Summary** — critical issues requiring immediate attention.
3. **Gap Analysis** — mapping of PS26031 requirements to implementation status.
4. **Recommended Action** — what to build/fix next, with justification.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `ps26031-requirements` | Use to evaluate gaps against PS26031 requirements |
| `dataset-engineering` | Use for detailed dataset inspection |
| `security` | Use to evaluate security posture |
| `documentation` | Use to evaluate documentation completeness |
