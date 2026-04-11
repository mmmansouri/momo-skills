---
name: spec-templates
description: >-
  Content guidance for Epic and Story descriptions in Buy Nature Jira tickets.
  Use when: writing Epic context/scope/technical approach sections, writing
  Story functional/technical specs, defining Acceptance Criteria, or ensuring
  specification completeness. Defines WHAT to write (not HOW to format — that's
  buy-nature-jira-writer).
---

# Spec Templates

> **Purpose:** Content guidance for each section of Epics and Stories.
> **Formatting:** See `buy-nature-jira-writer` for ADF format rules.
> **References:** See `references/` for detailed section guides.

---

## Document Types

| Document | Created By | Sections Guide |
|----------|-----------|----------------|
| Epic description | `spec-workflow-feature-planning` | `references/epic-sections-guide.md` |
| Refined Story description | `spec-workflow-story-refinement` | `references/story-sections-guide.md` |
| Draft Story | `spec-workflow-feature-planning` | Minimal (Context + "To be refined" panel) |
| E2E companion Story | Both workflows | Test Scenarios mapped to source ACs |

---

## Quality Principles

### Completeness

- Every required section is present and non-empty
- No placeholder text left in final output ("TBD", "TODO", "to be completed")
- Out of Scope is always explicit (prevents scope creep)

### Specificity

- ACs use concrete values, not vague language
- Technical spec includes actual class names, endpoints, field types
- Dependencies reference real BNAT-XXX tickets, not generic statements

### Testability

- Every AC can be verified by a test (manual or automated)
- No subjective criteria ("looks good", "works correctly", "handles errors properly")
- Error cases and edge cases are covered alongside happy paths

### Consistency

- Follows Buy Nature naming conventions (see project coding guides)
- Uses correct DTO suffixes (`*CreationRequest`, `*UpdateRequest`, `*RetrievalResponse`)
- References correct API prefixes (`/api/*` for frontend, `/api/admin/*` for backoffice)

---

## Section Inventory

### Epic Sections

| # | Section | Required | Content Summary |
|---|---------|----------|-----------------|
| 1 | Context | Yes | Business need, problem, who benefits |
| 2 | Scope | Yes | In Scope (features) + Out of Scope (exclusions) |
| 3 | Technical Approach | Yes | Affected projects, architecture, key decisions |
| 4 | Story Breakdown | Yes | Table: title, labels, dependencies, parallelizable |
| 5 | Dependencies | Yes | External systems, blocking work |
| 6 | Open Questions | If any | Unresolved decisions |

### Refined Story Sections

| # | Section | Required | Content Summary |
|---|---------|----------|-----------------|
| 1 | Context | Yes | Parent Epic ref, current state, why needed |
| 2 | Functional Spec | Yes | Business rules, user behavior, data requirements |
| 3 | Technical Spec | Yes | API endpoints, data model, component design |
| 4 | Acceptance Criteria | Yes | AC1-ACn with numbered IDs, testable bullets |
| 5 | Technical Notes | If any | Implementation hints, patterns, constraints |
| 6 | Out of Scope | Yes | Explicit exclusions |
| 7 | Dependencies | If any | Blocking BNAT-XXX tickets |

---

## Quick Quality Checklist

Before submitting any spec to Jira:

- [ ] Context explains **WHY**, not just **WHAT**
- [ ] All ACs have **numbered IDs** (AC1, AC2...)
- [ ] Each AC has **specific, verifiable bullets**
- [ ] ACs cover **happy path AND error/edge cases**
- [ ] No vague language ("works correctly", "handles errors properly")
- [ ] Technical spec has **concrete file paths** and class names
- [ ] API endpoints have **method + path + request/response DTOs**
- [ ] Data model has **field names + types + constraints**
- [ ] Dependencies are **linked BNAT-XXX tickets**
- [ ] Out of Scope is **explicit**

---

## Related Skills

- `buy-nature-jira-writer` — ADF formatting, Jira hierarchy, scripts
- `buy-nature-jira-us-creator` — INVEST criteria, AC patterns, E2E companion pattern
- `spec-workflow-feature-planning` — Epic planning workflow
- `spec-workflow-story-refinement` — Story refinement workflow
