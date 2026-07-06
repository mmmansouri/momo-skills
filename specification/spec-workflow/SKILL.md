---
name: spec-workflow
description: >-
  Generic specification workflow for Jira-based projects. Use when: planning a new
  feature (creating an Epic with draft Stories), refining an existing Story (turning
  a draft into a detailed spec with Acceptance Criteria), decomposing features into
  Stories, or producing any structured Jira planning artifact. Provides the step
  sequence (HOW). For content guidance (WHAT to write) load `spec-content`. For ADF
  formatting load `jira-adf`. For project-specific labels/scripts load the project's
  own `*-jira` skill (e.g. `buy-nature-jira`).
---

# Spec Workflow

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
> **Companion skills:** `spec-content` (WHAT) · `jira-adf` (FORMAT) · `<project>-jira` (auth + scripts + labels)

This skill describes the **ordering of steps** for two complementary specification
workflows. It is intentionally project-agnostic: every reference to a label,
script path, status name or DTO convention is delegated to the project's own
`<project>-jira` skill. Load that skill in parallel.

---

## When Planning a New Feature

📚 **When investigating the codebase during Step 2 (mapping existing entities, services, components, stores, routes, tests) → read [investigation-checklist.md](references/investigation-checklist.md).**

**Trigger phrases:** "plan", "planifie", "feature", "epic", "new epic",
"nouvelle feature", "decompose", "create epic".

**Output:** 1 Jira Epic + N draft Stories + E2E companion Stories.

### Step 1 — Understand the Need

1. Parse the request and identify the **target users** (end-user, admin, internal team).
2. Identify the **affected components** (one or several — see the project's label mapping in `<project>-jira/references/<project>-labels.md`).
3. Ask **at most 3 clarifying questions** if scope, users, or priority remain ambiguous.

**Output of Step 1:** clear understanding of what the feature does, who it's for, which components are affected.

### Step 2 — Investigate the Codebase

1. Read each affected component's `CLAUDE.md` (root + per-app if applicable).
2. Investigate existing code by layer (entities/models, services, controllers, components, stores, routes, tests). Use the project's package or folder conventions.
3. Search for related Jira tickets (avoid duplicating in-flight work).
4. Present findings to the user: existing architecture, patterns to follow, risks, anything else to check.

**Output of Step 2:** architecture understanding that informs decomposition and technical approach.

### Step 3 — Design the Epic

📚 **When writing the body of the Epic description (Context, Scope, Technical Approach, Story Breakdown, Dependencies, Open Questions) → load the `spec-content` skill and read its references/epic-sections-guide.md.**

1. Write the Epic description section by section (content guidance in `spec-content`).
2. **Decompose into Stories** — sizing and splitting are owned by the
   `common-story-sizing` skill (load it): apply its six BLOCKING rules
   (vertical slice, SP caps, demoable-in-isolation, Story-count band,
   1 E2E per macro-Story, runner-budget) and its SPIDR / Lawrence split
   catalogue. Never split mechanically by component / layer / CRUD
   operation — that yields horizontal slices that fail its Rules 1 and 3.
   - One label per Story still holds (`spec-content` §"When Setting Labels");
     when a genuinely vertical slice spans two components, split it along
     the component seam into linked Stories.
   - Each Story must satisfy INVEST (`spec-content` §"When Writing a User Story").
   - Order Stories by **dependency** (API Stories before UI Stories that consume them).
   - Mark each Story as **parallelizable** or **blocked-by**.
3. **Plan E2E companion Stories** following the project's E2E routing rules (`<project>-jira`).
4. Present Epic content + Story decomposition table + E2E plan → wait for user approval.

**Output of Step 3:** approved Epic content and Story plan ready for Jira creation.

### Step 4 — Create Jira Tickets (Envelope + Story Breakdown Loop)

📚 **When building the ADF JSON for Epic/Story descriptions (panels, tables, code blocks, advanced node structures) → load the `jira-adf` skill and read its references/adf-templates.md — §12 (Epic Description Template) locks the Brief Source panel + 5-column Story Breakdown table that this step depends on.**

> 🔴 **Stories created here are DRAFTS — by design, with no escape hatch in this workflow.** The default Story body is the "Draft - refinement pending" panel. **Do not** attempt to push a refined body from here, even if the user supplied detailed scope. If detailed scope was given, finish this workflow first (Epic + drafts + companions + links), then run the *Story Refinement* workflow once per Story to upgrade each draft into a fully refined spec before transitioning to "Ready". **Why:** this separation is what makes the workflow drift-resistant: the planning agent never types Story titles or labels as CLI args after the envelope is committed.

1. **Bootstrap the planning workspace.** Resolve a per-brief workspace via the
   project's workspace module (`<project>-jira` §"Spec Workspaces"). The
   workspace slug is derived deterministically from the verbatim brief (a
   sha256 prefix in Buy Nature's case), so the same brief always lands on the
   same directory. Run the project's housekeeping CLI first to evict expired
   workspaces.

2. **Author the envelope, once.** Write a single `envelope.json` to the
   workspace containing the Epic's `title`, routing `labels`, and the full
   `description` ADF document. The ADF **must** include a Brief Source info
   panel (verbatim brief text) and a 5-column Story Breakdown table
   (`Story | Labels | Depends On | Parallel | E2E`) whose rows define every
   Story to be created.

3. **Create the Epic via the envelope script.** The project's
   `jira_create_epic` script (path varies per project — see `<project>-jira`
   §"Quick Reference") takes `--envelope <ws>/envelope.json` and:
   - validates the envelope shape,
   - parses the Story Breakdown table out of the ADF,
   - extracts the Brief Source panel text and cross-checks its slug against
     the workspace (mismatch = refuses to POST, prevents paraphrase drift),
   - applies idempotency (exact-summary JQL search before POST).

4. **Create draft Stories index-by-index from the Story Breakdown.** The
   project's `jira_create_us --from-epic <EPIC> --index N` script re-reads
   the table from the Epic description and constructs the Story title + label
   from row N. The agent **does not** pass a title or label as a CLI
   argument — drift between plan and execution becomes physically impossible.

5. **Create E2E companion Stories.** Use the `--e2e-companion <STORY> --app <e2e-app>`
   mode of `jira_create_us` per the row's E2E column (project-specific
   routing — see `<project>-jira`). Companions are linked to their source
   Story automatically; if the project's script does not auto-link, follow
   with `jira_link_issues ... "Relates"`.

6. **Link blocking dependencies** between Stories using link type **"Blocks"**
   per the `Depends On` column.

7. **Report results** to the user: Epic key, every Story key with its title
   (re-fetched from Jira to prove no drift), E2E companion keys, links
   created. Explicitly state that Stories are drafts and refinement happens
   via the project's Story Refinement workflow.

---

## When Refining a Story

📚 **When self-checking the in-progress draft for completeness, AC coverage, technical-spec precision, and E2E companion quality → read [refinement-checklist.md](references/refinement-checklist.md).**

**Trigger phrases:** "refine", "affine", "spec", "detaille", "raffine",
or a direct Story key reference (e.g. `BNAT-123`, `PROJ-456`).

**Output:** updated Story description in Jira + E2E companion Story.

### Step 1 — Load Context

1. Fetch the Story from Jira (`jira_get` script). Extract title, description, labels, parent Epic key.
2. Fetch the **parent Epic**. Extract Context, Scope, Technical Approach, Story Breakdown.
3. Map the Story's labels to affected components (see `<project>-jira` label mapping).
4. Read the relevant `CLAUDE.md` files.
5. Confirm scope with the user (title, Epic reference, affected components, any adjustment needed).

### Step 2 — Deep Investigation

Story refinement is a **focused deep dive** on the exact code touched by this Story (unlike feature-planning, which surveys broadly).

For each affected component, read the relevant existing code :
- **Backend-style components** : entities/models, services, controllers, DTOs, migration files, repository or query patterns, test fixtures.
- **Frontend-style components** : pages/components, services (HTTP calls), state management (NgRx, Signal stores, Redux, Pinia…), routes, guards, shared UI library.
- **Other components** : test patterns (E2E, integration), infra-as-code, CI pipelines, etc. (Adapt to the project's tech stack.)

For each file you'll touch, decide :
- **[NEW]** create
- **[MODIFY]** modify (and how)

Present investigation results: existing patterns found, files to create/modify, references to similar features, open questions.

**Output of Step 2:** complete map of what to build and how, with concrete file paths.

### Step 3 — Write the Spec

📚 **When writing the body of the refined Story (Context, Functional Spec, Technical Spec, Acceptance Criteria, Technical Notes, Out of Scope, Dependencies) → load the `spec-content` skill and read its references/story-sections-guide.md.**

1. Draft the Story description section by section (content guidance in `spec-content`).
2. Write Acceptance Criteria following `spec-content` §"When Writing Acceptance Criteria" :
   - Numbered ID + descriptive title per AC.
   - Specific, testable bullets — concrete values, HTTP codes, field names.
   - Cover happy path **AND** error/edge cases.
3. Design E2E companion **Test Scenarios** mapped one-to-one to user-facing ACs.
4. Validate quality of the draft against the [refinement-checklist.md](references/refinement-checklist.md).
5. Present the spec to the user → wait for approval.

### Step 4 — Update Jira

1. Build the refined ADF JSON for the Story description (write to temp file).
2. Update the Story description via the project's `jira_update_us_description` script.
3. Transition the Story to the project's "Ready" status (or equivalent — see `<project>-jira` §"Workflow Statuses").
4. If no E2E companion exists yet, create it via `jira_create_us` and link it to the source Story with **"Relates"**.
5. Report results to the user (updated key, status transition, E2E companion key, links).

---

## Quality Gates

Before any Jira write (Step 4 of either workflow) :

🔴 **Use the matching checklist** :
- Feature planning Step 4 → `spec-content` §"Quality Checklist for Epics" + `<project>-jira` label validation.
- Story refinement Step 4 → [refinement-checklist.md](references/refinement-checklist.md) (this skill) **and** `spec-content` §"Quality Checklist for Stories".

**Why:** the checklist is the last deterministic gate before an irreversible Jira write; skipping it ships structural defects (missing ACs, no routing label) that the downstream orchestrator can't dispatch on.

🔴 **User approval is mandatory** before any Jira mutation. Show the full content
(Epic body, Story body, AC list, decomposition table) and wait for explicit "go".

**Why:** a Jira write is outward-facing and awkward to unwind; the user is the sole authority on scope, so an explicit go prevents publishing a spec they would reject.

---

## Project Adaptation

This skill is project-agnostic. The following items are **always** delegated to `<project>-jira` :

| Concept | Where to find it |
|---|---|
| Valid labels (component → label mapping) | `<project>-jira/references/<project>-labels.md` |
| Workflow statuses + transition IDs | `<project>-jira` §"Workflow Statuses" |
| Script paths (`jira_create_us`, `jira_create_epic`, …) | `<project>-jira` §"Quick Reference" |
| Auth setup (env detection, credentials) | `<project>-jira` §"Authentication" |
| E2E companion routing rules | `<project>-jira` §"When Labelling a Story" |
| DTO conventions, API prefixes, package layout | `<project>-jira` §"When Specifying ..." (if present) |
| Workspace lifecycle (workspace module + housekeeping CLI + envelope schema) | `<project>-jira` §"Spec Workspaces" |
| Brief Source panel + Story Breakdown table schema (ADF) | `jira-adf/references/adf-templates.md` §12 |

If a referenced item is missing from `<project>-jira`, treat it as a project setup gap — flag it to the user and propose the addition rather than improvising.

---

## Error Handling

| Error | Recovery |
|---|---|
| Jira API 401 | Refresh token via `<project>-jira` setup scripts |
| Epic creation fails | Show the error, ask user to verify Jira access, retry after fix |
| Story creation fails mid-batch | Continue with remaining Stories, report failures explicitly |
| Link creation fails | Report failed links, suggest manual fallback |
| Story has no parent Epic | Ask the user for Epic context or proceed without (flag as Open Question) |

---

## Related Skills

- `spec-content` — WHAT to write (sections inventory, INVEST, AC quality, splitting, labels rule)
- `jira-adf` — ADF format details (node types, marks, Epic/Story ADF templates)
- `<project>-jira` — project-specific runtime (auth, scripts, labels mapping, statuses)
