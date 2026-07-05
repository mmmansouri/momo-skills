# Epic Sections Guide

> Content guidance for each section of an Epic description.
> For ADF formatting, see `jira-adf`. For section inventory + quality rules, see `spec-content/SKILL.md`.

## Table of Contents

- [Section 1: Context](#section-1-context)
- [Section 2: Scope](#section-2-scope)
- [Section 3: Technical Approach](#section-3-technical-approach)
- [Section 4: Story Breakdown](#section-4-story-breakdown)
- [Section 5: Dependencies](#section-5-dependencies)
- [Section 6: Open Questions](#section-6-open-questions)

---

## Section 1: Context

**H2 heading:** `Context`

### What to Write

- **Business need:** What problem does this feature solve? Who experiences the pain?
- **Current state:** What exists today? What's missing or broken?
- **Target users:** Who benefits from this feature? (end-users, admins, internal team)
- **Business value:** Why is this worth building now?

### Quality Criteria

- Explains WHY, not just WHAT.
- A reader unfamiliar with the project understands the motivation.
- No implementation details (save those for Technical Approach).

### Example

> Buy Nature currently has no way for customers to share feedback on purchased products. Customer reviews are a proven mechanism to build trust, increase conversion rates, and surface product quality issues. Competitors offer review functionality, and customer surveys indicate this is a top-requested feature.

---

## Section 2: Scope

**H2 heading:** `Scope`
**H3 sub-headings:** `In Scope`, `Out of Scope`

### In Scope

Bullet list of features/capabilities included in this Epic:

- Each bullet is a concrete deliverable.
- Group by component if multi-component (backend, frontend, admin, …).
- Be specific enough that a reader knows what's included.

### Out of Scope

Bullet list of explicit exclusions:

- Things that could reasonably be expected but are NOT part of this Epic.
- Prevents scope creep during implementation.
- Each exclusion explains briefly why (deferred, separate epic, not needed).

### Example

**In Scope:**

- Review entity and CRUD API endpoints (backend)
- Review submission form on product detail page (frontend)
- Review moderation panel in admin dashboard (admin)
- Email notification when a review is submitted (email-system, cross-cutting)

**Out of Scope:**

- Review analytics dashboard (separate future epic)
- Photo / video attachments on reviews (phase 2)
- AI-powered review summarization (not planned)

---

## Section 3: Technical Approach

**H2 heading:** `Technical Approach`

### What to Write

- **Affected components:** List which components are impacted (with their routing labels).
- **Architecture decisions:** High-level approach (new entity? new module? extend existing?).
- **Key technical choices:** Database design direction, API design approach, state management strategy.
- **Integration points:** How components interact (API contracts, shared models).

### Quality Criteria

- References the project's existing conventions (package structure, DTO patterns, store patterns) by name.
- Identifies architectural risks or trade-offs.
- Does **NOT** include implementation details (class names, method signatures) — those belong in Story refinement.

### Example

> **Affected components:** backend, frontend, admin
>
> The Review domain follows the project's hexagonal layout with a new `review` package in the backend. Reviews link to Items via a ManyToOne relationship. The frontend uses a new feature store for reviews. The admin uses a Signal store following the existing `CategoryStore` pattern.
>
> API design follows the existing item/category patterns: public endpoints under the customer prefix, admin endpoints under the admin prefix.

---

## Section 4: Story Breakdown

**H2 heading:** `Story Breakdown`

### Format

ADF table with **5 columns** — this schema is a locked contract read back by
planning tooling (`jira-adf/references/adf-templates.md` §12 "Epic Template
Convention"), not a suggestion:

| Story | Labels | Depends On | Parallel | E2E |
|-------|--------|------------|----------|-----|

### What to Include

- **Story:** Full Story title including any `[<app>]` prefix — the exact summary POSTed to Jira when the row is created.
- **Labels:** Comma-separated; the first label is the routing label (one per component), cross-cutting labels follow.
- **Depends On:** Comma-separated 1-based row indices, or `Story N`, or an empty sentinel (`None`, `-`, `—`, `n/a`).
- **Parallel:** `Yes` / `No` — can this story be worked on simultaneously with others?
- **E2E:** Comma-separated E2E companion routing labels (e.g. `e2e-front`, `e2e-backoffice`); for a deliberate skip, an annotated `no-E2E: <rationale>` (never blank — see `common-story-sizing` Rule 5).

### Decomposition Guidelines

- Split by **component** first (one routing label per Story).
- Within a component, split by **CRUD operation** or **functional area**.
- Each Story should be **independently deliverable** (INVEST).
- Backend API Stories typically come first (frontend depends on API).
- E2E companions are declared in the `E2E` column — never as separate rows. They are created as tickets separately (routing rules in the project's `<project>-jira` skill).

### Example

| Story | Labels | Depends On | Parallel | E2E |
|---|---|---|---|---|
| Review entity + CRUD API | backend | None | Yes | no-E2E: API-only, user scenario covered by row 2 |
| Review submission form | frontend | 1 | No | e2e-front |
| Review moderation panel | admin | 1 | No | e2e-backoffice |
| Review email notification | backend, email-system | 1 | Yes | no-E2E: no user-facing scenario |

---

## Section 5: Dependencies

**H2 heading:** `Dependencies`

### What to Write

- External systems or APIs required.
- Blocking work from other teams or epics.
- Required assets (designs, copy, credentials).
- Infrastructure requirements (new database, new service).

### Quality Criteria

- Each dependency is actionable (who provides it? when?).
- Internal dependencies reference Story / Epic keys where possible.
- If no dependencies, write "None identified".

---

## Section 6: Open Questions

**H2 heading:** `Open Questions`

### What to Write

- Unresolved design or business decisions.
- Questions that need stakeholder input.
- Technical uncertainties that affect Story scope.

### Quality Criteria

- Each question is specific and answerable.
- Include who should answer (if known).
- If no open questions, omit this section entirely.
