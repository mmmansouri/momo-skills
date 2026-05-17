---
name: jira-adf
description: >-
  Atlassian Document Format (ADF) reference for Jira Cloud REST API. Use when:
  building Epic descriptions, Story descriptions, comments, or any rich-text field
  that goes through the Jira Cloud API (which only accepts ADF JSON, not markdown
  or plain text). Provides node types, marks, hierarchy rules, and ready-to-fill
  ADF structures for Epics, draft Stories, refined Stories, E2E companion Stories,
  and issue linking. Make sure to use this skill whenever the user mentions Jira
  Cloud API, ADF, Atlassian Document Format, Jira description JSON, panels, ADF
  tables, or "rich text in Jira" — even if they don't say "ADF" explicitly.
---

# Jira ADF

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
> **Companion skills:** `spec-workflow` (HOW) · `spec-content` (WHAT) · `<project>-jira` (scripts that send the ADF to Jira)

This skill covers **how to format** rich content for Jira Cloud's REST API. The
API field `description` (on Epics, Stories, Tasks, Bugs, and comments) only
accepts JSON in **Atlassian Document Format (ADF)** — never markdown, never
plain text. Get the format wrong and the API silently swallows your formatting.

📚 **When you need ready-to-fill JSON templates (Epic, draft Story, refined Story, E2E companion, tables, panels, code blocks) → read [adf-templates.md](references/adf-templates.md).**

---

## Jira Hierarchy

Default issue type hierarchy used in most Jira Cloud setups:

```
Epic (feature-level work)
  └─ Story (deliverable unit, INVEST criteria)
      └─ (Sub-tasks on premium plans; free plan uses Tasks under Epic)
```

| Issue Type | Use for | Parent |
|---|---|---|
| **Epic** | Feature-level planning (rich description with tech spec or PRD) | None (top-level) |
| **Story** | Deliverable work unit with Acceptance Criteria | Epic (via `parent.key`) |
| **Task** | Technical work without user value (migrations, refactor) | Epic (via `parent.key`) |
| **Bug** | Defect report | Epic (optional) |

Project-specific issue types or hierarchy adjustments → see `<project>-jira`.

---

## When Building ADF for Jira API

### 🔴 BLOCKING — Always Use ADF for API Calls

Jira Cloud REST API **only accepts ADF JSON** for description fields. Never send plain text or markdown.

**Why:** sending markdown silently strips your formatting and inserts a raw text node, producing unreadable tickets. ADF is the only contract the API honors.

**Root structure:**

```json
{
  "type": "doc",
  "version": 1,
  "content": [ ... ]
}
```

### ADF Node Types

| Node | Renders as | Use for |
|---|---|---|
| `heading` (level 2) | **H2** | Major sections (Context, Requirements, ACs) |
| `heading` (level 3) | **H3** | Sub-sections (AC1, AC2, Technical Spec) |
| `paragraph` | Text block | Regular content |
| `bulletList` > `listItem` | Bullet list | Requirements, ACs, dependencies |
| `orderedList` > `listItem` | Numbered list | Sequential steps, implementation phases |
| `rule` | Horizontal line | Section separators |
| `table` | Data table | API contracts, field mappings, story breakdowns |
| `panel` | Callout box | Warnings, notes, important info |
| `codeBlock` | Code block | Code examples, file paths, commands |

### Text Marks (Inline Formatting)

| Mark | Effect | Use for |
|---|---|---|
| `strong` | **Bold** | Key terms, field names, emphasis |
| `em` | *Italic* | Secondary emphasis |
| `code` | `inline code` | Class names, endpoints, file paths, field names |
| `link` | [hyperlink] | Jira ticket references, documentation links |
| `strike` | ~~strikethrough~~ | Deprecated items |

Marks can be combined: `"marks": [{ "type": "strong" }, { "type": "code" }]` → **`bold code`**.

---

## When Building an Epic Description

📚 **For the ready-to-fill ADF template (full Epic with all 6 sections including Story Breakdown table) → read [adf-templates.md §Epic Description Template](references/adf-templates.md#epic-description-template).**

### 🔴 BLOCKING — Required Section Structure

Every Epic description must contain these ADF sections (content rules → see `spec-content/references/epic-sections-guide.md`):

| Section | H2 heading | ADF node |
|---|---|---|
| 1 | **Context** | `heading` L2 + `paragraph` |
| 2 | **Scope** | `heading` L2 + sub-headings L3 `In Scope` / `Out of Scope` + `bulletList` per sub |
| 3 | **Technical Approach** | `heading` L2 + `paragraph` (+ bullet list if needed) |
| 4 | **Story Breakdown** | `heading` L2 + `table` (4 columns: Story / Labels / Dependencies / Parallel?) |
| 5 | **Dependencies** | `heading` L2 + `bulletList` |
| 6 | **Open Questions** | `heading` L2 + `bulletList` (omit section if none) |

### 🟢 BEST PRACTICE — Readability

- Insert `rule` nodes between major sections for visual separation.
- Use `strong` for table headers and field labels.
- Use `code` mark for technical references (`ReviewController`, `/api/reviews`).

---

## When Building a Story Description

### Draft Story (Feature Planning Output)

📚 **For the ready-to-fill ADF template (minimal draft with "To be refined" panel) → read [adf-templates.md §Draft Story Template](references/adf-templates.md#draft-story-template).**

Minimal content:

- `heading` L2 `Context` + 1-2 paragraphs referencing the parent Epic.
- `panel` `note` with text `Status: To be refined`.

### Refined Story (Story Refinement Output)

📚 **For the full ready-to-fill ADF template (Context, Functional Spec, Technical Spec with API Endpoints + Data Model tables, ACs, Technical Notes, Out of Scope, Dependencies) → read [adf-templates.md §Refined Story Template](references/adf-templates.md#refined-story-template).**

### 🔴 BLOCKING — Required Section Structure

| Section | H2 heading | ADF node |
|---|---|---|
| 1 | **Context** | `heading` L2 + `paragraph` (with link to parent Epic) |
| 2 | **Functional Spec** | `heading` L2 + `paragraph` / `bulletList` |
| 3 | **Technical Spec** | `heading` L2 + sub-headings L3 (`API Endpoints` `table`, `Data Model` `table`, `Component Design` `bulletList`) |
| 4 | **Acceptance Criteria** | `heading` L2 + per-AC `heading` L3 + `bulletList` |
| 5 | **Technical Notes** | `heading` L2 + `bulletList` (omit if empty) |
| 6 | **Out of Scope** | `heading` L2 + `bulletList` |
| 7 | **Dependencies** | `heading` L2 + `bulletList` with `link` marks (omit if empty) |

### E2E Companion Story

📚 **For the ready-to-fill ADF template (Context + Test Scenarios mapped 1:1 to source Story ACs) → read [adf-templates.md §E2E Companion Story Template](references/adf-templates.md#e2e-companion-story-template).**

Minimal content:

- `heading` L2 `Context` + paragraph referencing the source Story via `link` mark.
- `heading` L2 `Test Scenarios` + per-scenario `heading` L3 `AC{N}: ...` mapping source ACs + `bulletList`.

---

## When Building Acceptance Criteria (ADF)

### 🔴 BLOCKING — AC Block Pattern

Every AC follows the same ADF pattern:

```
heading L3  → "AC{N}: {Descriptive Title}"
bulletList:
  - listItem with paragraph: "Specific, testable requirement"
  - listItem with paragraph: "Another specific requirement"
  - listItem with paragraph: "Error / edge case handling"
```

📚 **For multiple AC examples (checklist, Given/When/Then, error cases, edge cases) → read [adf-templates.md §AC Templates](references/adf-templates.md#ac-block-template).**

### Quality Rules

(Defined in `spec-content` §"When Writing Acceptance Criteria" — this skill only encodes the ADF form.)

---

## When Linking Issues

Jira link types control how issues relate. The most common ones in spec workflows:

| Link type | Use when | Direction |
|---|---|---|
| `Relates` | E2E companion Stories, related features | Symmetric |
| `Blocks` | Dependency order (A must complete before B starts) | Directional (inwardIssue blocks outwardIssue) |

### Issue Link JSON

```json
{
  "type": { "name": "Relates" },
  "inwardIssue": { "key": "PROJ-101" },
  "outwardIssue": { "key": "PROJ-102" }
}
```

Endpoint: `POST /rest/api/3/issueLink`.

The script that wraps this call lives in the project's `<project>-jira` skill
(e.g. `jira_link_issues.py` in `buy-nature-jira/scripts/`).

---

## ADF Best Practices

### 🟢 BEST PRACTICE — Readability

- Use `rule` (horizontal line) between major sections for visual separation.
- Use `heading` level 2 for main sections, level 3 for sub-sections only — do not nest deeper.
- Use `strong` mark for field names in tables: **Endpoint**, **Method**.
- Use `code` mark for technical references: `ReviewController`, `/api/reviews`, `review.entity.ts`.
- Keep paragraphs short (2-3 sentences max).
- Use bullet lists over long paragraphs.

### 🟡 WARNING — Common Pitfalls

- **Never use markdown** in API calls — Jira REST API silently ignores it (you'll get raw text rendered as plain).
- **Character limit:** ADF descriptions have ~32,767 character limit. For larger specs, link to Confluence / external doc.
- **Table cells** must contain at least one `paragraph` node (even if empty). An empty `tableCell.content: []` is invalid.
- **Panel types:** `info` (blue), `note` (yellow), `warning` (orange), `error` (red), `success` (green).
- **Always validate ADF** structure before sending to API. The error response on malformed ADF is cryptic.

### 🟢 BEST PRACTICE — Building ADF Programmatically

When building ADF JSON for API calls:

1. Build the ADF JSON in memory or write to a temp file.
2. Pass the file path to the project's creation / update script.
3. The script handles auth and the API call.

```bash
# Example workflow with the project's wrapper scripts
EPIC_KEY=$(python3 ./<path-to-project-jira>/scripts/jira_create_epic.py \
  "Epic Title" "<labels>" /tmp/epic-adf.json)
```

---

## Related Skills

- `spec-workflow` — HOW (step-by-step planning and refinement workflows)
- `spec-content` — WHAT (sections inventory, INVEST, AC quality, labels rule)
- `<project>-jira` — PROJECT (scripts that POST the ADF to the API + auth + labels mapping)
