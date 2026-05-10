---
name: spec-workflow-feature-planning
description: >-
  Feature planning workflow for Buy Nature. Use when: user asks to plan a feature,
  create an Epic, decompose a feature into stories, or start specification work
  for a new capability. Produces a Jira Epic with rich ADF description and draft
  Stories ready for later refinement.
---

# Feature Planning Workflow

> **Trigger:** "planifie", "plan", "feature", "epic", "nouvelle feature", "create epic"
> **Output:** 1 Jira Epic + N draft Stories + E2E companion Stories
> **Duration:** 4 steps with user checkpoints

---

## Workflow Overview

| Step | Name | Goal | User Interaction |
|------|------|------|-----------------|
| 1 | Understand Need | Parse request, identify scope, clarify | Max 3 clarifying questions |
| 2 | Investigate Codebase | Read existing code, map architecture | Show findings, ask if more to check |
| 3 | Design Epic | Write Epic content, plan story decomposition | Present for approval/iteration |
| 4 | Create Jira Tickets | Create Epic + draft Stories + links in Jira | Report created ticket keys |

---

## Step 1: Understand Need

### Actions

1. **Parse the feature request** from user message
2. **Identify affected projects:**
   - Backend (`buy-nature-back`) — new entities, APIs, services?
   - Frontend (`buy-nature-front`) — new pages, components, customer-facing UI?
   - Backoffice (`buy-nature-back-office`) — new admin panels, management UI?
   - Email (`email-system`) — new email templates, notifications?
3. **Identify domain(s):** order, product, customer, category, stock, delivery, auth, review, etc.
4. **Ask clarifying questions** (max 3):
   - Scope boundaries (what's in/out?)
   - Target users (customers, admins, both?)
   - Priority or dependencies on existing work?

### Output

Clear understanding of:
- What the feature does
- Who it's for
- Which projects are affected
- Any constraints or prerequisites

---

## Step 2: Investigate Codebase

### Actions

1. **Read CLAUDE.md files** for each affected project:
   - `buy-nature-back/CLAUDE.md` for backend
   - `buy-nature-front/CLAUDE.md` for frontend
   - `buy-nature-back-office/CLAUDE.md` for backoffice

2. **Investigate existing code** using `references/investigation-checklist.md`:

   **Backend investigation:**
   - Existing entities in the related domain
   - Existing services, repositories, controllers
   - DTO patterns (naming, structure)
   - Liquibase changelog structure
   - Similar domain patterns to follow

   **Frontend investigation:**
   - Existing components in related features
   - NgRx store structure (actions, reducers, effects, selectors)
   - Route configuration and lazy loading
   - Service patterns for API calls

   **Backoffice investigation:**
   - Existing pages and CRUD patterns
   - Signal store patterns
   - Route configuration
   - Service patterns

3. **Check existing Jira tickets** for related work:
   ```bash
   python3 ./skills/buy-nature-jira/scripts/jira_search.py "project = BNAT AND text ~ 'keyword' AND status != Done"
   ```

4. **Present findings** to user:
   - Existing architecture summary
   - Patterns to follow
   - Any concerns or risks
   - Ask if anything else to investigate

### Output

Architecture understanding that informs story decomposition and technical approach.

---

## Step 3: Design Epic

### Actions

1. **Write Epic description** following `spec-templates/references/epic-sections-guide.md`:

   | Section | Content Source |
   |---------|--------------|
   | Context | User's feature request + clarifications |
   | Scope (In/Out) | Investigation findings + user boundaries |
   | Technical Approach | Codebase investigation results |
   | Story Breakdown | Decomposition analysis (see below) |
   | Dependencies | Investigation findings |
   | Open Questions | Unresolved decisions |

2. **Decompose into Stories:**

   **Decomposition rules:**
   - Split by **project** first (backend, frontend, backoffice)
   - Within a project, split by **functional area** or **CRUD operation**
   - Each story must be **independently deliverable** (INVEST: Independent, Valuable)
   - Backend API stories come before frontend stories (dependency order)
   - Identify which stories can be **parallelized**

   **For each story, determine:**
   - Title (descriptive, action-oriented)
   - Labels (backend, frontend, backoffice, email-system)
   - Dependencies (which other stories must complete first)
   - Whether it's parallelizable

3. **Identify E2E companion stories:**
   - Backend stories → E2E companion in `buy-nature-e2e-front` and/or `buy-nature-e2e-backoffice`
   - Frontend stories → E2E companion in `buy-nature-e2e-front`
   - Backoffice stories → E2E companion in `buy-nature-e2e-backoffice`

4. **Present to user** for approval:
   - Full Epic content (section by section)
   - Story decomposition table
   - E2E companion plan
   - Ask for approval or iteration

### Output

Approved Epic content and story plan ready for Jira creation.

---

## Step 4: Create Jira Tickets

### Actions

1. **Build ADF JSON** for Epic description:
   - Follow `buy-nature-jira-writer` formatting rules
   - Use ADF templates from `buy-nature-jira-writer/references/adf-advanced-templates.md`
   - Write ADF to temp file

2. **Create Epic** in Jira:
   ```bash
   EPIC_KEY=$(python3 ./skills/buy-nature-jira-writer/scripts/jira_create_epic.py \
     "Epic Title" \
     "backend,frontend" \
     /tmp/epic-adf.json)
   ```

3. **Create draft Stories** under the Epic:
   ```bash
   # For each story in the decomposition
   STORY_KEY=$(python3 ./skills/buy-nature-jira-us-creator/scripts/jira_create_us.py \
     "Story Title" \
     "$EPIC_KEY" \
     "backend" \
     /tmp/draft-story-adf.json)
   ```

   Draft story ADF content (minimal):
   - Context paragraph referencing parent Epic
   - "To be refined" panel note

4. **Create E2E companion Stories:**
   ```bash
   E2E_KEY=$(python3 ./skills/buy-nature-jira-us-creator/scripts/jira_create_us.py \
     "E2E tests for [feature]" \
     "$EPIC_KEY" \
     "backend" \
     /tmp/e2e-story-adf.json)
   ```

5. **Link E2E companions** to their source stories:
   ```bash
   python3 ./skills/buy-nature-jira-writer/scripts/jira_link_issues.py \
     "$STORY_KEY" "$E2E_KEY" "Relates"
   ```

6. **Link blocking dependencies** between stories:
   ```bash
   # If story B depends on story A
   python3 ./skills/buy-nature-jira-writer/scripts/jira_link_issues.py \
     "$STORY_A_KEY" "$STORY_B_KEY" "Blocks"
   ```

7. **Report results** to user:
   - Epic key and title
   - All story keys with titles
   - E2E companion keys
   - Links created
   - Summary of what was created

### Output

All Jira tickets created and linked. User has ticket keys for tracking.

---

## Error Handling

| Error | Recovery |
|-------|----------|
| Jira API returns 401 | Run token refresh via `buy-nature-jira` skill scripts (auto-detected) |
| Epic creation fails | Show error, ask user to verify Jira access |
| Story creation fails | Continue with remaining stories, report failures |
| Link creation fails | Report failed links, user can create manually |

---

## Quality Checklist (Before Step 4)

Before creating tickets, verify:

- [ ] Epic Context explains business value (WHY, not just WHAT)
- [ ] Scope has explicit Out of Scope section
- [ ] Technical Approach references Buy Nature conventions
- [ ] Story Breakdown table shows dependencies and parallelization
- [ ] Each story has at least one label
- [ ] Backend stories have planned E2E companions
- [ ] No story is too large (should be completable in 1-3 days)
- [ ] User has approved the Epic content and story plan

---

## Related Skills

- `spec-templates` — Content guidance for each section
- `buy-nature-jira-writer` — ADF formatting and Jira scripts
- `buy-nature-jira-us-creator` — Story creation patterns
- `buy-nature-jira` — Jira auth and search scripts
- `spec-workflow-story-refinement` — Next step: refining draft stories
