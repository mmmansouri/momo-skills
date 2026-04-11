# Investigation Checklist

> Per-project investigation patterns for the feature-planning workflow. Use this checklist during Step 2 (Investigate Codebase) to systematically map existing architecture.

---

## Backend Investigation (buy-nature-back)

### Package Structure Discovery

```
src/main/java/com/buynature/
├── <domain>/
│   ├── domain/           # Entities, Repository interfaces, Domain services
│   ├── application/      # Application services (use cases)
│   └── infrastructure/
│       ├── persistence/  # JPA repositories, adapters
│       └── web/          # Controllers, DTOs
│           └── dto/      # *CreationRequest, *UpdateRequest, *RetrievalResponse
```

### What to Investigate

| Area | Grep Pattern | Purpose |
|------|-------------|---------|
| Entities | `@Entity` in domain package | Existing domain model |
| Repositories | `interface.*Repository` | Data access patterns |
| Services | `@Service` or `@Transactional` | Business logic patterns |
| Controllers | `@RestController` | API endpoint patterns |
| DTOs | `record.*Request\|record.*Response` | DTO naming/structure |
| Migrations | `ls db/changelog/changes/` | Liquibase changelog naming |
| Tests | `*E2ETest.java`, `*JpaAdapterTest.java` | Test patterns |

### Key Patterns to Note

- DTO naming: `{Entity}CreationRequest`, `{Entity}UpdateRequest`, `{Entity}RetrievalResponse`
- Repository 3-layer: `{Entity}Repository` (interface) → `{Entity}JpaRepository` (Spring Data) → `{Entity}JpaAdapter` (implementation)
- API paths: `/api/*` for public, `/api/admin/*` for admin
- Entity base: UUIDs for IDs, `Instant` for timestamps

### Grep Commands

```bash
# Find entities in a domain
grep -r "@Entity" buy-nature-back/src/main/java/com/buynature/<domain>/

# Find all controllers
grep -rn "@RestController" buy-nature-back/src/main/java/

# Find DTOs for a domain
grep -rn "record.*Request\|record.*Response" buy-nature-back/src/main/java/com/buynature/<domain>/

# Find existing migrations
ls buy-nature-back/src/main/resources/db/changelog/changes/

# Find test patterns
grep -rn "class.*E2ETest\|class.*JpaAdapterTest" buy-nature-back/src/test/
```

---

## Frontend Investigation (buy-nature-front)

### Folder Structure Discovery

```
src/app/
├── pages/<feature>/         # Feature components (smart/presentational)
├── services/                # API services
├── store/<feature>/         # NgRx: actions, reducer, effects, selectors
├── models/                  # TypeScript interfaces
└── app.routes.ts            # Route definitions
```

### What to Investigate

| Area | Location | Purpose |
|------|----------|---------|
| Feature pages | `src/app/pages/<related>/` | Existing component patterns |
| Services | `src/app/services/<related>.service.ts` | API call patterns |
| NgRx store | `src/app/store/<related>/` | State management patterns |
| Models | `src/app/models/<related>.model.ts` | Interface definitions |
| Routes | `src/app/app.routes.ts` | Routing patterns, lazy loading |
| Shared components | `src/app/components/` | Reusable UI components |

### Key Patterns to Note

- State: NgRx with Signals (`selectSignal`, `toSignal()`)
- Inputs/outputs: Signal-based (`input()`, `output()`)
- Control flow: `@if`, `@for`, `@switch` (not `*ngIf`, `*ngFor`)
- Dependency injection: `inject()` function (not constructor)
- Routes: Lazy-loaded per feature

### Grep Commands

```bash
# Find feature components
ls buy-nature-front/src/app/pages/<feature>/

# Find services
grep -rn "class.*Service" buy-nature-front/src/app/services/

# Find NgRx actions
grep -rn "createAction\|createActionGroup" buy-nature-front/src/app/store/

# Find route definitions
grep -rn "loadComponent" buy-nature-front/src/app/app.routes.ts

# Find model interfaces
grep -rn "interface\|type " buy-nature-front/src/app/models/
```

---

## Backoffice Investigation (buy-nature-back-office)

### Folder Structure Discovery

```
src/app/
├── pages/<feature>/         # Feature pages (list, form, detail)
├── services/                # API services
├── stores/<feature>.store.ts # Signal-based stores
├── models/                  # TypeScript interfaces
└── app.routes.ts            # Route definitions
```

### What to Investigate

| Area | Location | Purpose |
|------|----------|---------|
| Feature pages | `src/app/pages/<related>/` | CRUD page patterns |
| Services | `src/app/services/<related>.service.ts` | Admin API call patterns |
| Signal stores | `src/app/stores/<related>.store.ts` | Store patterns |
| Models | `src/app/models/<related>.model.ts` | Interface definitions |
| Routes | `src/app/app.routes.ts` | Admin routing patterns |

### Key Patterns to Note

- State: Signal stores (NOT NgRx) — private writable + public readonly
- CRUD pattern: list page → form page (create/edit) → card component
- API prefix: `/api/admin/*`
- Auth: Two-tier (client token + admin JWT)

### Grep Commands

```bash
# Find feature pages
ls buy-nature-back-office/src/app/pages/<feature>/

# Find signal stores
grep -rn "signal\|computed\|Injectable" buy-nature-back-office/src/app/stores/

# Find services
grep -rn "class.*Service" buy-nature-back-office/src/app/services/

# Find admin routes
grep -rn "loadComponent" buy-nature-back-office/src/app/app.routes.ts
```

---

## E2E Investigation

### What to Check

| Project | Location | Purpose |
|---------|----------|---------|
| `buy-nature-e2e-front` | `tests/` | Customer-facing E2E tests |
| `buy-nature-e2e-backoffice` | `tests/` | Admin E2E tests |

### Key Patterns

- Page Object pattern for UI abstraction
- Test data factories for isolation
- Locator strategies (test IDs preferred)

```bash
# Find similar E2E tests
ls buy-nature-e2e-front/tests/<feature>/
ls buy-nature-e2e-backoffice/tests/<feature>/

# Find page objects
grep -rn "class.*Page" buy-nature-e2e-front/page-objects/
```

---

## Domain Mapping

Common Buy Nature domains and their typical locations:

| Domain | Backend Package | Frontend Folder | Backoffice Folder |
|--------|----------------|-----------------|-------------------|
| Item/Product | `com.buynature.item` | `pages/items/` | `pages/items/` |
| Category | `com.buynature.category` | `pages/categories/` | `pages/categories/` |
| Order | `com.buynature.order` | `pages/orders/` | `pages/orders/` |
| Customer | `com.buynature.customer` | `pages/account/` | `pages/customers/` |
| Stock | `com.buynature.stock` | — | `pages/stock-management/` |
| Auth | `com.buynature.auth` | `services/auth/` | `services/auth/` |
| Delivery | `com.buynature.delivery` | `pages/delivery/` | `pages/delivery/` |

---

## Investigation Summary Template

After investigating, summarize findings in this format for the user:

```
### Investigation Results

**Affected Projects:** backend, frontend, backoffice

**Backend:**
- Related entities: [list existing entities]
- Similar patterns: [reference existing domain as template]
- API conventions: [note any relevant patterns]

**Frontend:**
- Related components: [list existing components]
- State management: [NgRx store structure]
- Similar features: [reference for patterns]

**Backoffice:**
- Related pages: [list existing pages]
- Signal stores: [existing store patterns]
- Similar CRUD: [reference for patterns]

**Risks/Concerns:**
- [Any architectural concerns or open questions]
```
