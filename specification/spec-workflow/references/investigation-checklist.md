# Investigation Checklist

> Per-component investigation patterns for the feature-planning workflow (Step 2).
> Use this checklist to systematically map existing architecture before designing
> a new Epic.

## Table of Contents

- [General Investigation Approach](#general-investigation-approach)
- [Backend-style Components](#backend-style-components)
- [Frontend-style Components](#frontend-style-components)
- [Admin / Backoffice Components](#admin--backoffice-components)
- [E2E / Integration Test Components](#e2e--integration-test-components)
- [Domain Mapping](#domain-mapping)
- [Investigation Summary Template](#investigation-summary-template)
- [Real-World Example: Buy Nature](#real-world-example-buy-nature)

---

## General Investigation Approach

For every component touched by the future Epic, answer four questions:

1. **What exists today** in this domain? (entities, services, components, stores, tests)
2. **What patterns** are followed? (naming, layering, error handling, validation)
3. **What can be reused** vs **what must be created**?
4. **What risks** does this introduce? (breaking changes, performance, security)

Read `CLAUDE.md` for each affected component first — it usually documents the
conventions you need. Then use grep / glob to confirm patterns on actual code.

---

## Backend-style Components

### What to Investigate

| Area | Typical signal | Purpose |
|------|----------------|---------|
| Entities / Domain models | `@Entity`, `@Table`, ORM annotations | Existing domain model |
| Repositories / DAOs | `interface .*Repository`, `Dao`, `extends JpaRepository` | Data access patterns |
| Services / Use cases | `@Service`, `@Transactional`, `UseCase` suffix | Business logic patterns |
| Controllers / Resources | `@RestController`, `@Path`, `Resource` suffix | API endpoint patterns |
| Request/Response DTOs | naming conventions (`*Request`, `*Response`, `*Dto`) | Wire-format conventions |
| Database migrations | Liquibase / Flyway changelog folder | Migration naming |
| Tests | `*E2ETest`, `*IntegrationTest`, `*JpaAdapterTest` | Test pattern conventions |

### Key Patterns to Note

- DTO naming convention (look it up in the project's coding-guide skill).
- Repository pattern (single layer vs port/adapter / hexagonal vs simple Spring Data).
- API path conventions (public vs admin, versioning, naming style).
- Identifier strategy (UUID, auto-increment, snowflake).
- Timestamp strategy (`Instant`, `LocalDateTime`, `Timestamp`).
- Validation layer (Bean Validation, custom validators, schema).

### Useful Grep Commands

```bash
# Existing entities in a domain
grep -rn "@Entity" path/to/backend/src/main/java/<root-package>/<domain>/

# All REST controllers
grep -rn "@RestController" path/to/backend/src/main/java/

# DTOs for a domain
grep -rn "record .*Request\|record .*Response" path/to/backend/src/main/java/<domain>/

# Migration files
ls path/to/backend/src/main/resources/db/changelog/changes/

# Test patterns
grep -rn "class .*E2ETest\|class .*IntegrationTest" path/to/backend/src/test/
```

Adapt the paths to your project layout.

---

## Frontend-style Components

### What to Investigate

| Area | Typical location | Purpose |
|------|------------------|---------|
| Pages / Routed components | `pages/<feature>/`, `routes/<feature>/` | Existing component patterns |
| API services | `services/`, `api/` | HTTP call patterns |
| State management | `store/`, `state/`, NgRx / Redux / Zustand / Pinia folder | State patterns |
| Models / Interfaces | `models/`, `types/` | Interface definitions |
| Routes | `app.routes.ts`, `router.tsx`, etc. | Routing + lazy loading patterns |
| Shared UI components | `components/`, `ui/` | Reusable component library |

### Key Patterns to Note

- Reactive primitive (Signals, RxJS Observables, useState hooks…).
- Control flow syntax (Angular new `@if`/`@for` vs structural directives ; React JSX patterns).
- Dependency injection style (`inject()` vs constructor vs context).
- Routing style (lazy-loaded, eager, file-based).
- Form library and validation.

### Useful Commands

```bash
ls path/to/frontend/src/app/pages/<feature>/
grep -rn "class .*Service" path/to/frontend/src/app/services/
grep -rn "createAction\|createReducer\|createSlice" path/to/frontend/src/app/store/
grep -rn "loadComponent\|lazy(" path/to/frontend/src/app/app.routes.ts
```

---

## Admin / Backoffice Components

Admin apps often share the frontend stack but with different conventions:

| Area | What's different from customer-facing |
|------|---------------------------------------|
| State management | Often lighter (Signal stores, simple services) since less reactive composition |
| API prefix | Frequently `/api/admin/*` or similar |
| Auth | Two-tier (client token + admin JWT) is common |
| CRUD pages | Standardized list → form → detail / card pattern |

Investigate the same axes as a frontend (pages, services, store, routes) but **always
look for the existing CRUD pattern** — most admin features should clone it rather
than invent.

---

## E2E / Integration Test Components

For each E2E project (web, mobile, API):

| What to check | Typical location |
|---|---|
| Existing tests in the related domain | `tests/<feature>/`, `e2e/<feature>/`, `specs/<feature>/` |
| Page objects / helpers | `page-objects/`, `helpers/`, `fixtures/` |
| Test data factories | `factories/`, `fixtures/`, `seeds/` |
| Selectors strategy | data-testid / role-based / CSS — grep `data-testid` |

### Key Patterns

- Page Object pattern for UI abstraction.
- Test data factories for isolation between tests.
- Locator strategies — prefer stable selectors (`data-testid`) over brittle CSS.

---

## Domain Mapping

For projects with a clear domain layer, list the existing domains and their
location in each component. Example template:

| Domain | Backend package | Frontend folder | Admin folder |
|--------|-----------------|-----------------|--------------|
| Domain A | `com.example.domaina` | `pages/domain-a/` | `pages/domain-a/` |
| Domain B | `com.example.domainb` | — | `pages/domain-b/` |

When a new Epic touches an **existing** domain, follow its conventions. When it
introduces a **new** domain, design it consistently with the most similar
existing one.

---

## Investigation Summary Template

After investigating, summarize findings to the user before designing the Epic:

```
### Investigation Results

**Affected components:** <list of labels mapped to components>

**<Component 1>:**
- Related entities/files: [list]
- Similar patterns: [reference existing X as template]
- Conventions to follow: [naming / layering / validation]

**<Component 2>:**
- ...

**Risks / open questions:**
- [Anything that needs clarification before designing the Epic]
```

---

## Real-World Example: Buy Nature

The Buy Nature project (the original consumer of this skill) uses:

- Backend: Spring Boot / Java / hexagonal layout `domain → application → infrastructure`
  - DTO suffixes `*CreationRequest`, `*UpdateRequest`, `*RetrievalResponse`
  - API prefixes `/api/*` (customer) and `/api/admin/*` (admin)
  - Migrations in `src/main/resources/db/changelog/changes/`
- Frontend (customer): Angular 21 + NgRx + Signal-based inputs/outputs + new control flow
- Backoffice (admin): Angular 21 + Signal stores (no NgRx) + standardized CRUD pattern
- E2E: Playwright with Page Object pattern and `data-testid` selectors

See `buy-nature-jira/SKILL.md` and `buy-nature-<component>-coding-guide` skills
for the full project-specific details.
