---
name: spec-workflow-story-refinement
description: >-
  Story refinement workflow for Buy Nature. Use when: user asks to refine, spec,
  or detail a Jira Story (BNAT-XXX), produce functional/technical specifications,
  write Acceptance Criteria, or create E2E companion stories. Updates the Story
  description in Jira with rich ADF content.
---

# Story Refinement Workflow

> **Trigger:** "affine", "refine", "spec", "detaille", "BNAT-XXX" (story reference)
> **Output:** Updated Story description in Jira + E2E companion Story
> **Duration:** 4 steps with user checkpoints

---

## Workflow Overview

| Step | Name | Goal | User Interaction |
|------|------|------|-----------------|
| 1 | Load Context | Read Story + Epic from Jira, identify scope | Confirm scope |
| 2 | Deep Investigation | Read exact files to modify/create, map patterns | Show investigation results |
| 3 | Write Spec | Produce detailed specification with ACs | Present for approval/iteration |
| 4 | Update Jira | Update Story, create E2E companion, link issues | Report updated tickets |

---

## Step 1: Load Context

### Actions

1. **Read the Story from Jira:**
   ```bash
   python3 ./skills/buy-nature-jira/scripts/jira_get.py BNAT-YYY
   ```
   Extract: title, description, labels, parent Epic key

2. **Read the parent Epic:**
   ```bash
   python3 ./skills/buy-nature-jira/scripts/jira_get.py BNAT-XXX
   ```
   Extract: Epic description (context, scope, technical approach, story breakdown)

3. **Identify scope from labels:**
   | Label | Project | Investigation Focus |
   |-------|---------|-------------------|
   | `backend` | `buy-nature-back` | Entities, services, controllers, DTOs, migrations |
   | `frontend` | `buy-nature-front` | Components, services, NgRx stores, routes |
   | `backoffice` | `buy-nature-back-office` | Components, services, Signal stores, routes |
   | `email-system` | `buy-nature-back` | Email templates, notification services |

4. **Read CLAUDE.md** for each affected project

5. **Confirm scope with user:**
   - Story title and context
   - Parent Epic reference
   - Affected projects
   - Any adjustments needed?

### Output

Clear understanding of story scope, parent Epic context, and affected projects.

---

## Step 2: Deep Investigation

### Actions

Unlike feature-planning (broad investigation), story refinement does a **focused deep dive** on the exact code relevant to this story.

1. **Backend deep dive** (if label `backend`):

   **Entities:**
   - Read existing entity classes in the relevant domain
   - Check JPA relationships, field types, constraints
   - Read existing Liquibase changelogs for table structure

   **Services:**
   - Read application service for the domain
   - Identify patterns (validation, error handling, pagination)
   - Check for existing query methods to reuse

   **Controllers:**
   - Read existing controller in the domain
   - Note endpoint patterns (path, HTTP method, request/response)
   - Check auth requirements (public vs admin)

   **DTOs:**
   - Read existing DTO records in the domain
   - Note naming conventions, validation annotations
   - Identify DTO mapper patterns

   **Tests:**
   - Read existing E2E tests for the domain
   - Read JPA adapter tests for repository patterns
   - Note test data factory patterns

2. **Frontend deep dive** (if label `frontend`):

   **Components:**
   - Read components in the relevant feature folder
   - Note input/output patterns (signal-based)
   - Check template patterns (`@if`, `@for`, forms)

   **Services:**
   - Read API service for the feature
   - Note HTTP call patterns, error handling
   - Check pagination patterns

   **NgRx Store:**
   - Read actions, reducer, effects, selectors
   - Note state shape, action patterns
   - Check effect error handling patterns

   **Routes:**
   - Read route configuration for the feature
   - Note lazy loading patterns
   - Check guard usage

3. **Backoffice deep dive** (if label `backoffice`):

   **CRUD Pattern:**
   - Read list component, form component, card component
   - Note the existing CRUD workflow pattern
   - Check Signal store pattern (private writable → public readonly)

   **Services:**
   - Read admin API service patterns
   - Note `/api/admin/*` endpoint patterns

4. **Map exact files:**
   - List every file to **create** (NEW) or **modify** (MODIFY)
   - Include full relative paths from project root
   - Group by layer (entity → service → controller → DTO)

5. **Present investigation results:**
   - Existing patterns found
   - Files to create/modify
   - Patterns to follow (reference specific existing files)
   - Any concerns or open questions

### Output

Complete understanding of what to build and how, with concrete file paths and patterns.

---

## Step 3: Write Spec

### Actions

1. **Write Story description** following `spec-templates/references/story-sections-guide.md`:

   | Section | Content Source |
   |---------|--------------|
   | Context | Story context + Epic reference |
   | Functional Spec | Business rules from Epic scope + user clarifications |
   | Technical Spec | Investigation findings (endpoints, data model, components) |
   | Acceptance Criteria | Derived from functional spec, covering happy + error paths |
   | Technical Notes | Patterns to follow, implementation hints from investigation |
   | Out of Scope | Exclusions within this story |
   | Dependencies | Blocking BNAT-XXX tickets |

2. **Write Acceptance Criteria:**

   **For each AC:**
   - Numbered ID and descriptive title (AC1: Create Review, AC2: Validate Input...)
   - Specific, testable bullets (concrete values, HTTP codes, field names)
   - Cover happy path AND error/edge cases
   - Use checklist format (default) or Given/When/Then (complex state transitions)

   **AC coverage checklist:**
   - [ ] Main success scenario
   - [ ] Input validation (required fields, format, limits)
   - [ ] Error scenarios (not found, conflict, unauthorized)
   - [ ] Edge cases (empty list, max values, concurrent access)
   - [ ] Pagination/sorting (if applicable)

3. **Design E2E companion** test scenarios:
   - Map each user-facing AC to E2E test scenario
   - Include navigation steps, assertions, error verification
   - Reference page objects to create

4. **Validate quality** using `references/refinement-checklist.md`

5. **Present spec to user:**
   - Full story content (section by section)
   - AC list
   - E2E companion plan
   - Ask for approval or iteration

### Output

Approved Story specification and E2E companion plan ready for Jira update.

---

## Step 4: Update Jira

### Actions

1. **Build ADF JSON** for Story description:
   - Follow `buy-nature-jira-writer` formatting rules
   - Use ADF templates from `buy-nature-jira-writer/references/adf-advanced-templates.md`
   - Write ADF to temp file

2. **Update Story description** in Jira:
   ```bash
   python3 ./skills/buy-nature-jira-us-creator/scripts/jira_update_us_description.py \
     BNAT-YYY \
     /tmp/refined-story-adf.json
   ```

3. **Transition Story to Ready** (refined = ready for development):
   ```bash
   python3 ./skills/buy-nature-jira/scripts/jira_move.py BNAT-YYY "Ready"
   ```
   > The story moves from Backlog → Ready, signaling it is fully specced and can be picked up by a developer.

4. **Create E2E companion Story** (if not already created):
   ```bash
   E2E_KEY=$(python3 ./skills/buy-nature-jira-us-creator/scripts/jira_create_us.py \
     "E2E tests for [story topic]" \
     "$EPIC_KEY" \
     "backend" \
     /tmp/e2e-companion-adf.json)
   ```

   E2E companion ADF content:
   - Context referencing source Story
   - Test Scenarios mapped to source Story ACs

5. **Link E2E companion** to source Story:
   ```bash
   python3 ./skills/buy-nature-jira-writer/scripts/jira_link_issues.py \
     BNAT-YYY "$E2E_KEY" "Relates"
   ```

6. **Report results** to user:
   - Updated Story key with confirmation
   - Status transition (Backlog → Ready)
   - E2E companion key (if created)
   - Links created
   - Summary of what was updated/created

### Output

Story description updated in Jira with full specification. E2E companion created and linked.

---

## Error Handling

| Error | Recovery |
|-------|----------|
| Story not found in Jira | Verify key, ask user for correct ticket |
| No parent Epic found | Ask user for Epic context or proceed without |
| Jira API 401 | Run token refresh via `buy-nature-jira` skill scripts (auto-detected) |
| Description update fails | Show error, offer to write ADF to file for manual paste |
| E2E companion already exists | Skip creation, link if not already linked |

---

## Quality Checklist (Before Step 4)

Before updating Jira, verify using `references/refinement-checklist.md`:

- [ ] Context explains WHY, not just WHAT
- [ ] All ACs have numbered IDs (AC1, AC2...)
- [ ] Each AC has specific, testable bullets
- [ ] ACs cover happy path AND error/edge cases
- [ ] No vague language ("works correctly", "handles errors properly")
- [ ] Technical spec has concrete file paths
- [ ] API endpoints have method + path + request/response DTOs
- [ ] Data model has field names + types + constraints
- [ ] Dependencies are linked BNAT-XXX tickets
- [ ] Out of Scope is explicit
- [ ] E2E companion covers all user-facing ACs
- [ ] User has approved the specification

---

## Related Skills

- `spec-templates` — Content guidance for each section
- `buy-nature-jira-writer` — ADF formatting and Jira scripts
- `buy-nature-jira-us-creator` — Story update patterns
- `buy-nature-jira` — Jira auth and get/search scripts
- `spec-workflow-feature-planning` — Previous step: creating the Epic and draft stories
