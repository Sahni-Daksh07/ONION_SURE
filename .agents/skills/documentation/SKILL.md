---
name: documentation
description: >-
  Governs documentation standards for ONION_SURE: README, architecture docs,
  API docs, setup guide, ML training guide, dataset guide, annotation guide,
  deployment guide, troubleshooting, and demo guide. Documentation must describe
  actual implementation — never document planned features as if they exist.
  Activate for any documentation or knowledge management task.
---

# Documentation Skill

## Purpose

Maintain accurate, honest documentation that reflects the actual state of the
ONION_SURE project. Documentation must help developers, reviewers, and demo
evaluators understand what is implemented, what is missing, and how to use the
system.

## When to Use

- Creating or updating documentation.
- Adding new features (document them).
- Reviewing documentation accuracy.
- Preparing for demos or evaluations.
- Onboarding new team members.

## Required Inputs

- Current implementation status (from `repository-audit`).
- Feature or component to document.

---

## Required Documents

### 1. README.md (Root)

The main project README must contain:

- Project name and description
- PS26031 problem statement summary
- Current implementation status (honest)
- Architecture overview
- Technology stack
- Quick start guide
- Team information
- License

### 2. docs/architecture.md

- System architecture diagram
- Component descriptions (backend, mobile, ML, grading engine)
- Data flow diagrams
- Integration points
- Technology decisions with rationale

### 3. docs/api.md

- API endpoint reference (auto-generated from FastAPI is preferred)
- Authentication flow
- Request/response examples
- Error codes and handling

### 4. docs/setup.md

- Prerequisites (Python, Flutter, Docker, PostgreSQL)
- Step-by-step local setup
- Environment variable configuration
- Database migration instructions
- Running the development server
- Running tests

### 5. docs/ml-training.md

- Dataset preparation steps
- Training pipeline usage
- Experiment configuration
- Evaluation procedure
- Model export for deployment

### 6. docs/dataset.md

- Dataset description and statistics
- Directory structure
- Label definitions (including gaps)
- Annotation guidelines reference
- Versioning scheme

### 7. docs/annotation-guide.md

- How to annotate onion images for PS26031
- Defect category definitions with visual examples
- Annotation tool recommendations
- Quality control process
- Label format specification

### 8. docs/deployment.md

- Docker deployment steps
- Environment configuration
- Database migration in production
- Health check verification
- Monitoring setup
- Rollback procedure

### 9. docs/troubleshooting.md

- Common issues and solutions
- Database connection problems
- Model loading failures
- Sync issues
- Image processing errors

### 10. docs/demo-guide.md

- Demo prerequisites
- Step-by-step demo script
- What to show and explain at each step
- Known limitations to acknowledge
- Q&A preparation

---

## The Honesty Rule

### ABSOLUTE REQUIREMENT

```
❌ NEVER document a feature as "implemented" when it is:
   - Only planned
   - Only mocked
   - Only partially built
   - Not tested

✅ ALWAYS clearly state:
   - What IS implemented and working
   - What is IN PROGRESS (with current status)
   - What is NOT YET IMPLEMENTED
   - What is a KNOWN LIMITATION
```

### Implementation Status Template

```markdown
## Feature Status

| Feature | Status | Notes |
|:---|:---|:---|
| Image capture | ✅ Implemented | Camera integration working |
| Onion detection | ✅ Implemented | YOLOv8 model deployed |
| Defect classification | 🔧 In Progress | Training on expanded dataset |
| Size measurement | ⏳ Not Started | Requires ArUco marker integration |
| Grading engine | ✅ Implemented | Policy v1.0.0 |
| QR verification | ⏳ Not Started | — |
```

---

## Documentation Standards

### Writing Style

- Use clear, concise language.
- Include code examples where helpful.
- Use diagrams for architecture and workflows.
- Keep documents focused — one topic per document.
- Include a "Last Updated" date.

### Formatting

- Use Markdown for all documentation.
- Use headers for navigation.
- Use tables for structured data.
- Use code blocks for commands and examples.
- Use Mermaid diagrams where supported.

### Versioning

- Documentation lives in `docs/` directory.
- Documentation is version-controlled with the code.
- Major changes require a documentation review.

---

## Implementation Rules

1. **Update documentation when code changes.** Don't let docs drift.
2. **Be honest about implementation status.** Use the status template.
3. **Include setup instructions that actually work.** Test them.
4. **Document architecture decisions.** Why, not just what.
5. **Document known limitations.** Don't hide them.
6. **Include troubleshooting guidance.** For common issues.
7. **Keep the README current.** It's the first thing people see.

---

## Validation Rules

- ✅ README accurately reflects current project state.
- ✅ Setup guide works for a new developer (test it).
- ✅ API documentation matches actual endpoints.
- ✅ Feature status table is honest and current.
- ✅ No planned features documented as implemented.
- ✅ Known limitations are documented.

---

## Forbidden Behavior

- ❌ Documenting planned features as if they are implemented.
- ❌ Leaving setup instructions that don't work.
- ❌ Omitting known limitations or bugs.
- ❌ Writing documentation that contradicts the code.
- ❌ Deleting documentation without replacement.
- ❌ Using screenshots of fake UI or fabricated results.

---

## Expected Outputs

1. **Updated README** — current project overview.
2. **Architecture documentation** — system design.
3. **API documentation** — endpoint reference.
4. **Setup guide** — working local setup instructions.
5. **Feature status** — honest implementation status.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `repository-audit` | Current implementation status |
| `ps26031-requirements` | Feature requirements and priorities |
| `fastapi-backend` | API documentation |
| `flutter-mobile` | Mobile app documentation |
| `ml-training-evaluation` | ML training documentation |
| `dataset-engineering` | Dataset documentation |
| `demo-validation` | Demo guide |
