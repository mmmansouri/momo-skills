---
name: spec-content
description: >-
  Content & quality guidance for Jira Epics and Stories. Use when: writing or
  auditing the body of an Epic / Story description, checking INVEST criteria,
  writing Acceptance Criteria, splitting a large User Story, choosing the right
  Jira labels (étiquettes), or running a quality gate before pushing to Jira.
  Project-agnostic: WHAT to write and how to judge it, not WHERE to write it
  (that's `jira-adf` for ADF format and the project's own `*-jira` skill for project specifics).
  Make sure to use this skill whenever the user mentions specs, user stories,
  acceptance criteria, story points, INVEST, story splitting, étiquettes,
  composant cible, or Jira labels — even if they don't say "spec-content"
  explicitly.
---

# Spec Content

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
> **Companion skills:** `spec-workflow` (HOW) · `jira-adf` (FORMAT) · `<project>-jira` (project-specific labels & conventions)

This skill defines **what to write** in Jira tickets and **how to judge quality**.
It is intentionally project-agnostic: it never lists concrete project labels,
DTO suffixes, or app names — those live in the project's own `<project>-jira` skill.

📚 **When writing or auditing the body of an Epic description (Context, Scope, Technical Approach, Story Breakdown, Dependencies, Open Questions) → read [epic-sections-guide.md](references/epic-sections-guide.md).**

📚 **When writing or auditing the body of a refined Story description (Context, Functional Spec, Technical Spec, Acceptance Criteria, Technical Notes, Out of Scope, Dependencies) → read [story-sections-guide.md](references/story-sections-guide.md).**

📚 **When choosing the AC format (checklist vs Given/When/Then) and writing testable bullets with proper coverage → read [acceptance-criteria-patterns.md](references/acceptance-criteria-patterns.md).**

---

## Document Types

| Document | Created by | Sections guide |
|---|---|---|
| Epic description | feature-planning workflow | `epic-sections-guide.md` |
| Refined Story description | story-refinement workflow | `story-sections-guide.md` |
| Draft Story | feature-planning workflow | Minimal (Context + "To be refined" panel) |
| E2E companion Story | both workflows | Test Scenarios mapped to source ACs |

---

## When Writing a User Story

### INVEST Criteria

Every User Story must satisfy all 6 criteria:

| Criterion | Question | Fail signal |
|---|---|---|
| **I**ndependent | Can it be delivered without other Stories? | "After STORY-XX is done..." |
| **N**egotiable | Can scope be discussed? | Over-specified implementation details |
| **V**aluable | Does it deliver user or business value? | Pure technical task with no user impact |
| **E**stimable | Can the team estimate it? | Unknown technology or vague scope |
| **S**mall | Fits in one sprint? | More than 8 ACs or ≥ 13 story points (see `common-story-sizing` Rule 2) |
| **T**estable | Can you write a test for it? | "System should be user-friendly" |

### 🔴 BLOCKING — INVEST Compliance

- Every Story must deliver clear value (user-facing or business-enabling).
- **Why:** developer stories ("Refactor X") that deliver no observable behaviour are work items, not Stories. They belong as Tasks under an Epic, not Stories.
- Every Story must be testable with specific, measurable criteria.
- Every Story must fit in one sprint — if too large, split it (see [When Splitting a Large Story](#when-splitting-a-large-story)).

### Story Title Formats

Both formats are acceptable:

```
# Format A: Descriptive (preferred for technical / infrastructure Stories)
Email Template Design
Product Search API

# Format B: User-story phrasing (preferred for feature Stories)
Customer can filter products by category
Admin can export order reports as CSV
```

### Examples

```
🔴 WRONG — Not a Story, just a task:
"Implement product API"
"Refactor email service"
"Add database index"

✅ CORRECT — Clear value:
"Product Search API" (enables customer search feature)
"Customer can track order delivery status"
"Admin can bulk-update product prices"
```

---

## When Structuring an Epic

📚 **When writing the content of each Epic section → read [epic-sections-guide.md](references/epic-sections-guide.md).**

Every Epic has the same six sections:

| # | Section | Required | Content |
|---|---|---|---|
| 1 | **Context** | 🔴 Yes | Business need, problem, who benefits, current state |
| 2 | **Scope** | 🔴 Yes | In Scope (bullet list) + Out of Scope (explicit exclusions) |
| 3 | **Technical Approach** | 🔴 Yes | Affected components, high-level architecture, key technical choices |
| 4 | **Story Breakdown** | 🔴 Yes | 5-column table (Story / Labels / Depends On / Parallel / E2E) — locked schema, see epic-sections-guide.md §4 |
| 5 | **Dependencies** | 🔴 Yes | External systems, blocking work, required APIs / assets (or "None") |
| 6 | **Open Questions** | 🟡 If any | Unresolved decisions |

### 🔴 BLOCKING — Epic Quality

- **Context must explain WHY**, not just WHAT.
- **Out of Scope must be explicit** — even if short. **Why:** prevents scope creep during implementation; the cost of arguing later is higher than the cost of writing it now.
- **Story Breakdown table must show dependencies, parallelization and E2E companions** — feeds the orchestration / sprint planning that comes after.

---

## When Structuring a Refined Story

📚 **When writing the content of each refined-Story section → read [story-sections-guide.md](references/story-sections-guide.md).**

Every refined Story has the same seven sections:

| # | Section | Required | Content |
|---|---|---|---|
| 1 | **Context** | 🔴 Yes | Parent Epic ref, what exists today, why this story is needed |
| 2 | **Functional Spec** | 🔴 Yes | User-facing behavior, business rules, data requirements |
| 3 | **Technical Spec** | 🔴 Yes | API endpoints, data model, component design, file paths |
| 4 | **Acceptance Criteria** | 🔴 Yes | AC1-ACn with numbered IDs and testable bullets |
| 5 | **Technical Notes** | 🟡 If any | Implementation hints, patterns to follow, constraints |
| 6 | **Out of Scope** | 🔴 Yes | Explicit exclusions |
| 7 | **Dependencies** | 🟡 If any | Blocking Story keys |

### Draft Story (minimal)

Stories created during feature-planning are drafts — they will be refined later. A draft contains only:

- **Context**: 1-2 sentences referencing the parent Epic and what this story will deliver.
- **Panel "To be refined"**: explicit status marker.

---

## When Writing Acceptance Criteria

📚 **When writing the AC bullets and picking a format (checklist vs Given/When/Then) → read [acceptance-criteria-patterns.md](references/acceptance-criteria-patterns.md).**

### 🔴 BLOCKING — AC Structure

- Each AC has a **numbered ID and descriptive title** (`AC1: Product search`, not just `AC1`).
- Each AC has **specific, verifiable bullets**.
- ACs cover **happy path AND error / edge cases**.
- **No vague language** ("works correctly", "handles errors properly", "is fast").

**Why:** an AC without a numbered ID and concrete, verifiable bullets can't be mapped to a test or to diff evidence during functional review, so the Story ships with unprovable scope.

### 🟡 WARNING — AC Quality

- ACs describe **WHAT** (observable behavior), not **HOW** (implementation).
  - Avoid: "Use Redis for caching"
  - Prefer: "Response cached for 5 minutes"

### Supported Formats

| Format | Use when | Example |
|---|---|---|
| **Checklist** (default) | Most ACs | `- Supports search by name (partial, case-insensitive)` |
| **Given / When / Then** | Complex state transitions | `Given user has items in cart, When removing last item, Then cart shows empty state` |

### Examples

```
🔴 WRONG — Vague, untestable:
### AC1: Search
- Search should work correctly
- Handle errors properly
- Be fast enough

✅ CORRECT — Specific, testable:
### AC1: Product Search
- Supports search by name (partial match, case-insensitive)
- Supports filter by category ID
- Returns paginated results (default 20 per page)
- Returns 200 with empty list when no matches (not 404)
- Returns 400 with RFC 7807 error for invalid parameters
```

---

## When Splitting a Large Story

📚 **When a Story trips the size ceiling (> 8 ACs or ≥ 13 SP) and you need the full sizing & splitting playbook → load the `common-story-sizing` skill (5 BLOCKING rules — vertical slice / 13 SP warning / demoable in isolation / 6-10 per Epic / E2E per macro-Story — plus SPIDR, Richard Lawrence's 9 patterns, the worked anti-pattern catalog, and the pre-push self-check).**

If a Story has more than **8 ACs** or estimates at **≥ 13 story points**
(Fibonacci-warning convention — see `common-story-sizing` Rule 2), try to split it
using a **vertical** technique (SPIDR or Lawrence patterns). If no vertical split
exists, keep it at 13 SP — never force a horizontal split.

### Splitting Strategies — Quick Reference

| Strategy | Description | Example |
|---|---|---|
| **By workflow step** | Split along process steps | Checkout: address → payment → confirmation |
| **By data variation** | Split by entity type | CRUD products vs CRUD categories |
| **By operation** | Split CRUD operations | Create product, Update product, Delete product |
| **By user role** | Split by actor | Customer views orders vs Admin manages orders |
| **By component** | Split by app / codebase | Backend API vs Frontend UI vs Admin UI |

These five high-level strategies stay project-agnostic. For the deeper toolbox
(SPIDR — Spike / Path / Interface / Data / Rules — and Lawrence's nine patterns)
load `common-story-sizing`.

### 🔴 BLOCKING — Splitting Quality

- Each resulting Story must still satisfy INVEST independently.
- Each split Story must be a **vertical slice** (touches all layers needed to
  deliver observable behaviour). Horizontal splits ("rewrite DTOs", "add
  migration", "rename entity") are forbidden — see `common-story-sizing` Rule 1.
- Each split Story must be **demoable in isolation** on the day its PR merges —
  no "wait until Story B is also merged" demos. See `common-story-sizing` Rule 3.
- Each split Story must deliver value on its own (avoid "Part 1 / Part 2 / Part 3" if Part 1 alone delivers nothing observable).

**Why:** a horizontal split leaves each fragment un-demoable and mutually blocking, so the Epic can't ship incrementally — the whole point of splitting is to release value Story by Story.

---

## When Setting Labels (Étiquettes Jira)

### 🔴 BLOCKING — Every Story and Epic must have at least one routing label

Each Story and Epic must carry **at least one étiquette** (Jira label) that identifies
the **target component** — the app, layer or sub-system that owns the work.

**Why:** the orchestrator that delegates implementation reads this label to route
the task to the right codebase (and the right `.claude/skills/` configuration).
Without a routing label, the orchestrator cannot decide where to run the
implementation. **A Story without a routing label is a planning gap.**

### Rules

1. **One routing label = one component = one codebase.**
   A Story should ideally touch a single component. If it inevitably crosses
   several, prefer **splitting** (see [When Splitting a Large Story](#when-splitting-a-large-story) — "By component" strategy) and linking the resulting Stories with `Relates`.
2. **Cross-cutting labels are additional**, not substitutes.
   A label like `email-system`, `i18n`, `security`, or `performance` describes a
   concern that spans components. It always comes **in addition to** a routing
   label, never instead of it.
3. **Epics may carry multiple labels** — one per component covered by their child Stories.
4. **The list of valid labels for the current project lives in the project's `<project>-jira` skill** (e.g. `buy-nature-jira/references/buy-nature-labels.md`). This skill (`spec-content`) only encodes the rule, never the values.

### 🔴 BLOCKING — When choosing a label

- **Always read the project's label mapping first** (`<project>-jira/references/<project>-labels.md`). Do not invent labels.
- If no mapping exists in the project skill, treat that as a project-setup gap and flag it to the user.
- If a Story genuinely touches a component that has no mapping, do **not** apply an
  approximate label — propose adding the missing entry to the project's mapping
  and wait for the user's decision.

**Why:** the orchestrator dispatches on the exact label string, so an invented or approximate label silently routes the implementation to the wrong codebase (or nowhere).

### Worked Example (project-agnostic)

Suppose a project ships three components — `backend`, `frontend`, `admin` — and their
labels are defined in `myproject-jira/references/myproject-labels.md`:

```
| Component | Étiquette | App path |
|-----------|-----------|----------|
| Backend   | backend   | myproject-back |
| Frontend  | frontend  | myproject-front |
| Admin     | admin     | myproject-admin |
```

A Story "Add product search endpoint" → label `backend` (single routing label).
A Story "Display product search results on landing page" → label `frontend` (single routing label).
A cross-cutting Story "Localize search error messages" touching both → **split** into one Story per component, both also carrying `i18n` as additional cross-cutting label.

### Quick Self-Check

Before saving the Story:

- [ ] At least one routing label is set.
- [ ] The label exists in `<project>-jira/references/<project>-labels.md`.
- [ ] If multiple routing labels are set, the Story has been re-evaluated for splitting.
- [ ] Cross-cutting labels (if any) come in addition to a routing label, not instead.

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| **Developer Story** | "Refactor X" has no user value | Reframe: what user benefit does the refactor enable? Or convert to a Task under the Epic. |
| **Vague ACs** | "Should work properly" | Replace with specific, testable criteria |
| **Giant Story** | 10+ ACs, cannot finish in one sprint | Split using strategies above |
| **Missing dependencies** | Blocked mid-sprint | List all dependencies in description |
| **Missing routing label** | Orchestrator can't dispatch the work | Add a label from `<project>-jira/references/<project>-labels.md` |
| **Multiple routing labels** | Story touches several codebases at once | Split by component and link with "Relates" |
| **No E2E companion** | Missing test coverage | Create companion E2E Story (routing rule lives in `<project>-jira`) |
| **Implementation in ACs** | "Use Redis", "Add index" | Focus on observable behavior, not implementation |

---

## Quality Checklist

Single source of truth — use this before pushing any Epic or Story to Jira.

### 🔴 BLOCKING

- [ ] Title is clear and descriptive
- [ ] Description has **Context** section explaining WHY (not just WHAT)
- [ ] For Stories: at least **2 Acceptance Criteria** with numbered IDs (AC1, AC2...)
- [ ] Each AC has **specific, verifiable** bullets
- [ ] ACs cover **happy path AND error / edge cases**
- [ ] **Out of Scope** is explicit (Epics and refined Stories)
- [ ] **At least one routing label** set (see [When Setting Labels](#when-setting-labels-étiquettes-jira))
- [ ] Label exists in `<project>-jira/references/<project>-labels.md`
- [ ] Story is **linked to its parent Epic**
- [ ] E2E companion created when required by the project's routing rules (`<project>-jira`)

### 🟡 WARNING

- [ ] No more than 8 ACs per Story (split if more)
- [ ] No implementation details in ACs
- [ ] Dependencies section present if there are blockers
- [ ] Technical spec has concrete file paths and class names
- [ ] API endpoints have method + path + request / response DTO
- [ ] Data model has field names + types + constraints

### 🟢 BEST PRACTICE

- [ ] Story points estimated (1 / 2 / 3 / 5 / 8 / 13 — re-assess for vertical split at ≥ 13; see `common-story-sizing` Rule 2)
- [ ] Priority set appropriately
- [ ] Technical Notes for non-obvious constraints
- [ ] Companion E2E Story linked with "Relates"

---

## Related Skills

- `spec-workflow` — HOW (4-step planning + 4-step refinement workflows)
- `jira-adf` — FORMAT (ADF nodes, marks, Epic/Story ADF templates)
- `<project>-jira` — PROJECT (auth, scripts, label mapping, statuses, DTO conventions)
