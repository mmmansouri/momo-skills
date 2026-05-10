# Refinement Quality Checklist

> Use this checklist during Step 3 (Write Spec) to validate the story specification before updating Jira.

---

## Content Completeness

### Required Sections

- [ ] **Context** — Present and explains why this story is needed
- [ ] **Functional Spec** — Business rules, user behavior, data requirements
- [ ] **Technical Spec** — API endpoints, data model, component design (as applicable)
- [ ] **Acceptance Criteria** — At least 2 ACs with numbered IDs
- [ ] **Out of Scope** — Explicit exclusions (even if short)

### Optional Sections (include if relevant)

- [ ] **Technical Notes** — Implementation hints, patterns to follow
- [ ] **Dependencies** — Blocking BNAT-XXX tickets

---

## Context Quality

- [ ] References parent Epic (BNAT-XXX) with title
- [ ] Explains what exists today in the codebase
- [ ] Explains what this story delivers (the delta)
- [ ] A reader unfamiliar with the Epic can understand the story

---

## Functional Spec Quality

- [ ] Business rules are explicit (not implied)
- [ ] Validation rules have concrete values (max lengths, ranges, formats)
- [ ] Error scenarios are described (what happens when X fails?)
- [ ] Data requirements list all fields with types and constraints

---

## Technical Spec Quality

### API Endpoints (Backend)

- [ ] Table with Method, Path, Request DTO, Response DTO
- [ ] DTO names follow convention: `*CreationRequest`, `*UpdateRequest`, `*RetrievalResponse`
- [ ] API paths follow convention: `/api/*` (public) or `/api/admin/*` (admin)
- [ ] Pagination specified where applicable

### Data Model (Backend)

- [ ] Table with Field, Type, Constraints
- [ ] JPA relationships identified (`@ManyToOne`, `@OneToMany`)
- [ ] Liquibase changeset mentioned (new table/columns)
- [ ] Database naming follows snake_case

### Component Design (Frontend/Backoffice)

- [ ] Component names with full file paths
- [ ] Signal inputs/outputs specified
- [ ] Service dependencies identified
- [ ] Store interactions described

### File Paths

- [ ] All files to create marked **[NEW]**
- [ ] All files to modify marked **[MODIFY]**
- [ ] Paths are relative to project root
- [ ] Grouped by layer (entity → service → controller → DTO)

---

## Acceptance Criteria Quality

### Structure

- [ ] Each AC has a **numbered ID** (AC1, AC2, AC3...)
- [ ] Each AC has a **descriptive title** (not just "AC1")
- [ ] Bullets under each AC are specific and testable

### Coverage

- [ ] **Happy path** covered (main success scenario)
- [ ] **Input validation** covered (required fields, format, limits)
- [ ] **Error cases** covered (not found, conflict, unauthorized, bad request)
- [ ] **Edge cases** covered (empty list, max values, boundaries)
- [ ] **Pagination/sorting** covered (if applicable)

### Language Quality

- [ ] No vague phrases: "works correctly", "handles errors properly", "functions as expected"
- [ ] Concrete values: HTTP codes (201, 400, 404, 409), field names, limits
- [ ] No implementation details in ACs (describe WHAT, not HOW)
- [ ] Each bullet can be answered with "yes, it does" or "no, it doesn't"

---

## E2E Companion Quality

- [ ] Title: "E2E tests for [story topic]"
- [ ] Context references source Story (BNAT-YYY)
- [ ] Each user-facing AC has a corresponding test scenario
- [ ] Test scenarios include navigation steps and assertions
- [ ] Error scenarios have E2E coverage (not just happy path)
- [ ] Labels match source Story labels
- [ ] Parent Epic is the same as source Story

---

## Anti-Patterns to Avoid

| Anti-Pattern | Example | Fix |
|-------------|---------|-----|
| Vague AC | "System handles errors properly" | "Invalid rating returns 400 with validation message" |
| No error coverage | Only happy path ACs | Add AC for each error scenario |
| Implementation in AC | "Use ReviewJpaRepository to query" | "GET endpoint returns filtered results" |
| Missing constraints | "Rating field is required" | "Rating: integer, 1-5, not null" |
| Scope creep | AC covers features not in this story | Move to Out of Scope |
| No file paths | "Create a new controller" | "[NEW] `src/main/.../ReviewController.java`" |
| Placeholder text | "TBD", "TODO", "to be completed" | Fill in or explicitly mark as Open Question |

---

## Final Validation

Before submitting to Jira, read the entire spec and verify:

1. **Could a developer implement this without asking questions?**
   - If no → add missing details
2. **Could a tester write tests from the ACs alone?**
   - If no → make ACs more specific
3. **Is anything ambiguous or open to interpretation?**
   - If yes → clarify or move to Open Questions
4. **Does the spec match the Epic's scope for this story?**
   - If not → adjust scope or flag with user
