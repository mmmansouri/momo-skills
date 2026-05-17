# Acceptance Criteria Patterns

> Format examples and coverage patterns for writing testable Acceptance Criteria.
> For the structural rules and quality gate, see `spec-content/SKILL.md` §"When Writing Acceptance Criteria".

## Table of Contents

- [Format 1: Checklist (recommended)](#format-1-checklist-recommended)
- [Format 2: Given/When/Then (BDD)](#format-2-givenwhenthen-bdd)
- [Backend AC Example (REST API)](#backend-ac-example-rest-api)
- [Frontend AC Example (UI Behavior)](#frontend-ac-example-ui-behavior)
- [Admin AC Example (CRUD)](#admin-ac-example-crud)
- [E2E Companion AC Example](#e2e-companion-ac-example)
- [AC Quality Checklist](#ac-quality-checklist)
- [Common Vague Terms to Avoid](#common-vague-terms-to-avoid)

---

## Format 1: Checklist (recommended)

Primary format for most User Stories. Each AC has a numbered ID, a title, and specific bullet points.

```
### AC1: Product Search
- Supports search by product name (partial match, case-insensitive)
- Supports filter by category
- Returns paginated results (default 20 per page)
- Empty search returns all products
- Returns 200 with empty list when no matches (not 404)
```

**When to use:** Most Stories — especially CRUD features, UI behavior, API endpoints.

---

## Format 2: Given/When/Then (BDD)

For complex behavioral scenarios with preconditions, actions, and expected outcomes.

```
### AC3: Cart total updates on item removal
- Given: User has 3 items in cart totaling EUR 45.00
- When: User removes 1 item priced EUR 15.00
- Then: Cart total updates to EUR 30.00 and item count shows 2
```

**When to use:** Complex state transitions, edge cases, workflows with strict preconditions.

---

## Backend AC Example (REST API)

```
### AC1: GET /api/products endpoint
- Returns paginated product list (default page size: 20)
- Supports query parameters: name, categoryId, minPrice, maxPrice
- Response includes: id, name, description, price, categoryName, imageUrl
- Returns 200 with empty content array when no matches
- Returns 400 with RFC 7807 Problem Details for invalid parameters

### AC2: Product price validation
- Price must be > 0 and <= 99999.99
- Price stored with 2 decimal precision
- Returns 422 with field-level error when price is invalid
```

---

## Frontend AC Example (UI Behavior)

```
### AC1: Product search bar
- Search input with debounce (300ms) triggers API call
- Loading spinner shown during API call
- Results displayed in grid layout (3 columns desktop, 1 column mobile)
- "No results found" message when API returns empty list
- Search input preserves value on page navigation (back button)

### AC2: Product card display
- Shows product image, name, price, and "Add to cart" button
- Price formatted as "XX.XX EUR"
- Truncates product name at 50 characters with ellipsis
- Image placeholder shown when imageUrl is null
```

---

## Admin AC Example (CRUD)

```
### AC1: Product list view
- Displays all products in a sortable table (name, price, category, status)
- Supports bulk actions: activate, deactivate, delete
- Pagination with configurable page size (10/25/50)
- Search by name with server-side filtering

### AC2: Product edit form
- Pre-fills all fields with current product data
- Validates required fields: name, price, category
- Shows confirmation dialog before saving changes
- Redirects to product list on successful save with success toast
```

---

## E2E Companion AC Example

```
### AC1: Product search E2E flow
- User types "organic" in search bar
- Product list updates to show only matching products
- User clicks on first result
- Product detail page displays correct information

### AC2: Empty search results
- User searches for "xyznonexistent"
- "No results found" message is displayed
- User clears search
- All products are shown again
```

---

## AC Quality Checklist

| Question | If "No"... |
|---|---|
| Can you write an automated test for this AC? | Rewrite with specific, measurable criteria |
| Is every term unambiguous? | Replace vague words ("fast", "user-friendly", "properly") |
| Does it cover the error / edge case? | Add error scenarios |
| Is it independent of implementation? | Remove technical details ("use Redis", "call API X") |
| Does it state WHAT, not HOW? | Focus on observable behavior |

---

## Common Vague Terms to Avoid

| Vague | Specific Replacement |
|---|---|
| "Works correctly" | "Returns 200 with product list containing 3 items" |
| "Handles errors" | "Returns 400 with error message when email format is invalid" |
| "Fast response" | "Response time < 500ms for 95th percentile" |
| "User-friendly" | "Form shows inline validation errors below each field" |
| "Secure" | "Requires authenticated JWT token, returns 401 without it" |
| "Responsive" | "Layout switches to single column below 768px viewport width" |
