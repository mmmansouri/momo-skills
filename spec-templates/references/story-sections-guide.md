# Story Sections Guide

> Content guidance for each section of a refined Story description. For ADF formatting, see `buy-nature-jira-writer`.

---

## Section 1: Context

**H2 heading:** `Context`

### What to Write

- **Parent Epic reference:** Link to Epic (BNAT-XXX) with title
- **Current state:** What exists in the codebase today related to this story?
- **Why this story:** What does it deliver? What gap does it fill?
- **Scope summary:** 1-2 sentences describing the deliverable

### Quality Criteria

- Reader understands the story without reading the full Epic
- References concrete existing code (entities, services, components)
- Clearly states what will exist AFTER this story is done

### Example

> Part of Epic **BNAT-200: Product Reviews**. Currently, the backend has no review domain — no entity, no API endpoints, no database table. This story creates the Review entity, Liquibase migration, and CRUD API endpoints so that customers can submit and read product reviews.

---

## Section 2: Functional Spec

**H2 heading:** `Functional Spec`

### What to Write

- **User-facing behavior:** What can the user do? What do they see?
- **Business rules:** Validation rules, constraints, calculations
- **Data requirements:** Required fields, optional fields, formats, limits
- **Error handling:** What happens on invalid input? Edge cases?

### Backend Stories

Focus on API behavior:
- Endpoint behavior (input → output)
- Validation rules per field
- Error responses (HTTP codes, error messages)
- Pagination, sorting, filtering rules

### Frontend Stories

Focus on UI behavior:
- Component behavior (user interactions → visual feedback)
- Form validation (client-side rules)
- Loading states, empty states, error states
- Responsive behavior (mobile, tablet, desktop)

### Example (Backend)

> **Review submission:**
> - Authenticated customers can submit one review per product
> - Review requires: rating (1-5 integer), comment (1-2000 characters)
> - Optional: title (max 100 characters)
> - Duplicate review (same customer + product) returns 409 Conflict
>
> **Review listing:**
> - Public endpoint (no auth required)
> - Paginated (default 10, max 50 per page)
> - Sorted by creation date descending (newest first)
> - Response includes average rating for the product

---

## Section 3: Technical Spec

**H2 heading:** `Technical Spec`
**H3 sub-headings:** `API Endpoints`, `Data Model`, `Component Design`

### API Endpoints (Backend Stories)

ADF table with columns: **Method**, **Path**, **Request DTO**, **Response DTO**

For each endpoint, include:
- HTTP method and full path
- Request DTO class name (following Buy Nature conventions: `*CreationRequest`, `*UpdateRequest`)
- Response DTO class name (`*RetrievalResponse`)
- Key fields in request/response (as bullet list below table if needed)

### Data Model (Backend Stories)

ADF table with columns: **Field**, **Type**, **Constraints**

For each entity field:
- Field name (Java naming: camelCase)
- Java/SQL type
- Constraints (not null, unique, max length, foreign key)

Also mention:
- JPA relationships (`@ManyToOne`, `@OneToMany`)
- Liquibase changeset requirements (new table, add column, index)
- Database naming (snake_case table/column names)

### Component Design (Frontend/Backoffice Stories)

Bullet list of components to create/modify:
- Component name with path (`src/app/pages/reviews/review-list.component.ts`)
- Inputs/outputs (signal-based)
- Template structure (key sections)
- Services to inject
- Store interactions

### File Paths

Bullet list of files to create or modify:
- Use full relative paths from project root
- Mark each as **[NEW]** or **[MODIFY]**
- Group by layer (entity → service → controller → DTO for backend)

### Example (Backend)

**API Endpoints:**

| Method | Path | Request DTO | Response DTO |
|--------|------|-------------|-------------|
| `POST` | `/api/reviews` | `ReviewCreationRequest` | `ReviewRetrievalResponse` |
| `GET` | `/api/items/{itemId}/reviews` | — (query params) | `Page<ReviewRetrievalResponse>` |
| `DELETE` | `/api/admin/reviews/{id}` | — | 204 No Content |

**Data Model (Review entity):**

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | `UUID` | PK, auto-generated |
| `rating` | `Integer` | 1-5, not null |
| `title` | `String` | max 100, nullable |
| `comment` | `String` | max 2000, not null |
| `item` | `Item` | ManyToOne, not null |
| `customer` | `Customer` | ManyToOne, not null |
| `createdAt` | `Instant` | not null, auto-set |

**Files:**
- **[NEW]** `src/main/java/com/buynature/review/domain/Review.java`
- **[NEW]** `src/main/java/com/buynature/review/domain/ReviewRepository.java`
- **[NEW]** `src/main/java/com/buynature/review/application/ReviewService.java`
- **[NEW]** `src/main/java/com/buynature/review/infrastructure/ReviewJpaRepository.java`
- **[NEW]** `src/main/java/com/buynature/review/infrastructure/web/ReviewController.java`
- **[NEW]** `src/main/java/com/buynature/review/infrastructure/web/dto/ReviewCreationRequest.java`
- **[NEW]** `src/main/java/com/buynature/review/infrastructure/web/dto/ReviewRetrievalResponse.java`
- **[NEW]** `src/main/resources/db/changelog/changes/XXXX-create-review-table.yaml`

---

## Section 4: Acceptance Criteria

**H2 heading:** `Acceptance Criteria`
**H3 per AC:** `AC{N}: {Descriptive Title}`

### Format

Each AC has:
1. **Numbered ID and descriptive title** as H3 heading
2. **Bullet list** of specific, testable requirements

### Supported Styles

| Style | When to Use | Example |
|-------|-------------|---------|
| **Checklist** (default) | Most ACs | `- POST /api/reviews with valid payload returns 201` |
| **Given/When/Then** | Complex state transitions | `- Given customer has a review, When submitting another for same product, Then 409 Conflict` |

### Quality Rules

- Each AC is **independently verifiable**
- Covers **happy path** AND **error/edge cases**
- Uses **concrete values** (status codes, field names, limits)
- No implementation details (describe WHAT, not HOW)
- No vague language ("works correctly", "handles errors properly")
- Error ACs specify the **exact HTTP code and error condition**

### Example

**AC1: Submit Review**
- POST `/api/reviews` with valid `{ rating: 4, comment: "Great product" }` returns 201
- Response contains the created review with generated `id` and `createdAt`
- Review is persisted and visible via GET endpoint
- Missing `rating` field returns 400 with validation error
- Rating outside 1-5 range returns 400 with validation error
- Comment exceeding 2000 characters returns 400 with validation error

**AC2: Prevent Duplicate Reviews**
- Given customer has already reviewed product X
- When submitting another review for product X
- Then API returns 409 Conflict with message "Review already exists for this product"

**AC3: List Product Reviews**
- GET `/api/items/{id}/reviews` returns paginated reviews (default page size: 10)
- Reviews are sorted by `createdAt` descending
- Response includes `averageRating` computed from all reviews
- Non-existent product ID returns 404

---

## Section 5: Technical Notes

**H2 heading:** `Technical Notes`

### What to Write

- **Patterns to follow:** Reference existing similar implementations in the codebase
- **Constraints:** Performance requirements, security considerations
- **Implementation hints:** Non-obvious technical details the developer should know
- **Migration notes:** Liquibase changeset naming, data backfill requirements

### Quality Criteria

- Only include notes that add value (not obvious from the spec)
- Reference concrete files/classes as examples to follow
- If no notes needed, omit this section

### Example

> - Follow the `Category` domain pattern for package structure
> - Use `ReviewJpaRepository` extending `JpaRepository<Review, UUID>` with custom query for duplicate check
> - Liquibase changeset: `YYYYMMDD-create-review-table.yaml` following existing naming in `db/changelog/changes/`
> - Index on `(item_id, customer_id)` for duplicate check and listing queries

---

## Section 6: Out of Scope

**H2 heading:** `Out of Scope`

### What to Write

- Features that are part of the Epic but NOT this story
- Extensions that could be assumed but are explicitly excluded
- Each exclusion with brief reason (deferred, separate story, not needed)

### Quality Criteria

- Always present (even if short)
- Prevents scope creep during implementation
- Clear enough that a developer knows where to stop

### Example

> - Review editing (separate story BNAT-XXX)
> - Photo/video attachments (phase 2, out of Epic scope)
> - Admin reply to reviews (separate backoffice story)
> - Review helpfulness voting (not planned)

---

## Section 7: Dependencies

**H2 heading:** `Dependencies`

### What to Write

- **Blocking stories:** BNAT-XXX tickets that must be completed first
- **Required APIs:** Endpoints from other stories this one depends on
- **Required infrastructure:** Database tables, services, configurations

### Quality Criteria

- Each dependency links to a real BNAT-XXX ticket
- Explains what is needed from each dependency
- If no dependencies, write "None — this story can start independently"

### Example

> - **BNAT-201** — Review entity and API must be deployed before frontend can integrate
> - **BNAT-198** — Customer authentication flow must support the `customerId` claim in JWT
