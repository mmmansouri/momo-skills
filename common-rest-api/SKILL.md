---
name: common-rest-api
description: >-
  REST API design best practices. Use when: designing endpoints (resource naming,
  HTTP methods), implementing pagination (offset vs cursor), handling errors
  (RFC 7807 Problem Details), versioning APIs, documenting with OpenAPI, or
  building REST controllers with Spring Boot 4 / Spring Framework 7.
---

# REST API Developer Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## When Designing Resource URIs

📚 **References:** [rest-api-fundamentals.md](references/rest-api-fundamentals.md)

### 🔴 Use Nouns, Not Verbs

```
✅ CORRECT                    🔴 WRONG
GET  /orders                  GET  /getOrders
POST /orders                  POST /createOrder
GET  /orders/123              GET  /getOrderById?id=123
PUT  /orders/123              POST /updateOrder
DELETE /orders/123            POST /deleteOrder
```

### 🔴 Use Plural Nouns for Collections

```
✅ CORRECT                    🔴 WRONG
/customers                    /customer
/orders                       /order
/products                     /product
```

### 🔴 Model Relationships via Nesting

```
GET  /customers/5/orders      # Orders for customer 5
POST /customers/5/orders      # Create order for customer 5
GET  /orders/99/items         # Items in order 99
```

### 🟡 Limit Nesting Depth to 2-3 Levels

```
✅ CORRECT
/customers/5/orders           # Then use order ID separately
/orders/99/items

🔴 WRONG - Too deep
/customers/5/orders/99/items/42/reviews
```

### 🟢 Use Query Parameters for Filtering

```
GET /orders?status=pending&minTotal=100
GET /products?category=electronics&inStock=true
GET /users?role=admin&createdAfter=2025-01-01
```

---

## When Choosing HTTP Methods

📚 **References:** [rest-api-fundamentals.md](references/rest-api-fundamentals.md)

### 🔴 Method Semantics

| Method | Action | Idempotent | Safe | Request Body |
|--------|--------|------------|------|--------------|
| GET | Retrieve resource(s) | Yes | Yes | No |
| POST | Create resource | No | No | Yes |
| PUT | Replace resource | Yes | No | Yes |
| PATCH | Partial update | No* | No | Yes |
| DELETE | Remove resource | Yes | No | Optional |

*PATCH can be idempotent depending on implementation.

### 🔴 Standard Status Codes by Method

**GET:**
| Status | When |
|--------|------|
| 200 OK | Resource found |
| 204 No Content | Collection empty |
| 404 Not Found | Resource doesn't exist |

**POST:**
| Status | When |
|--------|------|
| 201 Created | Resource created (include Location header) |
| 200 OK | Action performed, no resource created |
| 400 Bad Request | Validation failed |
| 409 Conflict | Duplicate resource |

**PUT:**
| Status | When |
|--------|------|
| 200 OK | Updated and returning body |
| 204 No Content | Updated, no body |
| 201 Created | Resource created (upsert) |
| 404 Not Found | Resource doesn't exist |

**PATCH:**
| Status | When |
|--------|------|
| 200 OK | Updated and returning body |
| 204 No Content | Updated, no body |
| 400 Bad Request | Invalid patch document |
| 409 Conflict | Cannot apply patch |

**DELETE:**
| Status | When |
|--------|------|
| 204 No Content | Successfully deleted |
| 404 Not Found | Resource doesn't exist |
| 409 Conflict | Cannot delete (dependencies) |

---

## When Using Spring Boot 4 REST Features

📚 **References:** [spring-rest-api.md](references/spring-rest-api.md) — RestClient, HTTP Interface Clients, Virtual Threads, comparison table

| Feature | RestTemplate | RestClient | HTTP Interface |
|---------|--------------|------------|----------------|
| **Release** | Spring 3.0 (2009) | Spring 6.1 / Boot 3.2 | Spring 6.0 / Boot 3.0 |
| **API Style** | Imperative, verbose | Fluent, modern | Declarative |
| **Type Safety** | ⚠️ Weak | ✅ Strong | ✅ Strong |
| **Status** | Maintenance mode | ✅ Preferred | ✅ Preferred |
| **Use Case** | Legacy code | New code, fluent API | Interface-driven, clean |

### 🟢 Migration Path

- **Existing code:** Keep `RestTemplate` (don't rewrite)
- **New simple HTTP calls:** Use `RestClient`
- **New multi-endpoint interfaces:** Use `@HttpExchange` clients
- **Virtual threads (Java 21+):** Enable for high-concurrency blocking I/O

---

## When Configuring Spring Boot Applications

📚 **References:** [spring-boot-config-pitfalls.md](references/spring-boot-config-pitfalls.md)

### 🔴 BLOCKING
- **No duplicate YAML root keys** → Each root key (`spring:`, `server:`, etc.) must appear only ONCE per file. Duplicates silently override the first block.

### 🟡 WARNING
- **No dev defaults in base config** → `cache: false`, debug flags, test mail servers belong in profile-specific files only
- **No stacking AOP annotations on same method** → `@Async` + `@Retry` creates unpredictable proxy ordering. Use delegation between beans.
- **Resilience4j retry exceptions must match** → If catch-and-rethrow wraps the original exception, retry config targeting the original type never triggers
- **Springdoc OpenAPI minimum** for Spring Boot 4: `2.6.0` (recommended: `2.8.5`)

### 🟢 BEST PRACTICE
- **No unused YAML properties** → Every property must be referenced by `@Value`, `@ConfigurationProperties`, or Spring auto-config
- **No orphan template files** → Every template must be referenced in code

---

## When Handling Errors

📚 **References:** [rest-api-fundamentals.md](references/rest-api-fundamentals.md), [spring-rest-api.md](references/spring-rest-api.md)

### 🔴 Use RFC 7807 Problem Details

```json
{
  "type": "https://api.example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 400,
  "detail": "The request contains invalid fields",
  "instance": "/orders/123",
  "errors": [
    { "field": "email", "message": "must be a valid email address" },
    { "field": "quantity", "message": "must be greater than 0" }
  ]
}
```

### 🔴 Standard Error Status Codes

| Code | Meaning | Use Case |
|------|---------|----------|
| 400 | Bad Request | Validation error, malformed request |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Business rule violation, duplicate |
| 422 | Unprocessable Entity | Semantic error (valid syntax) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

### 🟡 Never Expose Internal Details

```json
// 🔴 WRONG - Exposes internal details
{ "error": "org.postgresql.util.PSQLException: duplicate key value..." }

// ✅ CORRECT - User-friendly message
{ "type": "...", "title": "Email Already Exists", "status": 409, "detail": "A user with this email already exists" }
```

---

## When Implementing Pagination

📚 **References:** [rest-api-fundamentals.md](references/rest-api-fundamentals.md)

### 🔴 Always Paginate Collections

Never return unbounded lists. Set reasonable defaults and maximums.

### 🟢 Offset vs Cursor Pagination

| Approach | Example | Best For |
|----------|---------|----------|
| **Offset** | `GET /orders?page=2&size=20` | Small/static datasets, random access |
| **Cursor** | `GET /orders?limit=20&after=eyJpZCI6MTAwfQ` | Large/dynamic datasets, consistency |

---

## When Versioning APIs

📚 **References:** [rest-api-fundamentals.md](references/rest-api-fundamentals.md), [spring-rest-api.md](references/spring-rest-api.md)

### 🟡 Versioning Strategies

| Strategy | Example | Pros | Cons |
|----------|---------|------|------|
| **URI Path** | `/v1/orders` | Simple, explicit | Breaks REST purity |
| **Query Param** | `/orders?version=1` | Flexible | Can be missed |
| **Header** | `Api-Version: 1` | Clean URIs | Less discoverable |
| **Media Type** | `Accept: application/vnd.api.v1+json` | REST-compliant | Complex |

### 🟢 Recommended: URI Path (Most Common)

```java
@RestController
@RequestMapping("/api/v1/orders")
public class OrderControllerV1 { }
```

---

## When Implementing Sorting & Filtering

📚 **References:** [rest-api-fundamentals.md](references/rest-api-fundamentals.md)

### 🟢 Query Parameter Conventions

```
# Filtering
GET /products?category=electronics&minPrice=100&maxPrice=500

# Sorting (+ ascending, - descending)
GET /products?sort=-createdAt,+name

# Field selection (sparse fieldsets)
GET /products?fields=id,name,price
```

---

## When Designing Request/Response Bodies

📚 **References:** [spring-rest-api.md](references/spring-rest-api.md)

### 🔴 Use DTOs, Never Entities

```java
// 🔴 WRONG - Exposing entity
@GetMapping("/{id}")
public Order getOrder(@PathVariable UUID id) {
    return orderRepository.findById(id).orElseThrow();
}

// ✅ CORRECT - Using DTO
@GetMapping("/{id}")
public OrderResponse getOrder(@PathVariable UUID id) {
    Order order = orderService.findById(id);
    return OrderResponse.from(order);
}
```

### 🟢 Separate DTOs for Create/Update/Response

| DTO Type | Purpose | Annotations |
|----------|---------|-------------|
| `*CreationRequest` | POST body — required fields only | `@NotNull`, `@NotEmpty` |
| `*UpdateRequest` | PUT body — all mutable fields optional | `@Size`, `@Min` |
| `*RetrievalResponse` | GET response — full representation | `static from()` factory |

---

## When Validating Requests

📚 **References:** [spring-rest-api.md](references/spring-rest-api.md)

### 🔴 Validate at Controller Level

```java
@PostMapping
public ResponseEntity<OrderResponse> createOrder(
        @Valid @RequestBody OrderCreationRequest request) {
    Order order = orderService.create(request);
    return ResponseEntity.created(URI.create("/orders/" + order.getId()))
        .body(OrderResponse.from(order));
}
```

### 🔴 Use Bean Validation Annotations

| Annotation | Use Case |
|------------|----------|
| `@NotNull` | Field must not be null |
| `@NotEmpty` | String/Collection must not be empty |
| `@NotBlank` | String must have non-whitespace content |
| `@Size(min, max)` | Length/size constraints |
| `@Min`, `@Max` | Numeric bounds |
| `@Email` | Valid email format |
| `@Valid` | Cascade validation to nested objects |

---

## When Documenting APIs

📚 **References:** [spring-rest-api.md](references/spring-rest-api.md)

### 🔴 Use OpenAPI 3 (Springdoc)

- Annotate controllers with `@Operation` (summary + description)
- Use `@ApiResponses` for all possible status codes
- Use `@Schema` on DTOs for model documentation

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] Resource URIs use nouns (not verbs)
- [ ] HTTP methods match semantics (GET read, POST create, etc.)
- [ ] Status codes reflect outcomes (201 Created, 404 Not Found)
- [ ] DTOs used instead of entities
- [ ] Request validation with @Valid
- [ ] Error responses follow RFC 7807
- [ ] No duplicate YAML root keys in application config files

### 🟡 WARNING
- [ ] Collections are paginated
- [ ] Nested URIs limited to 2-3 levels
- [ ] No internal details in error messages
- [ ] API versioning strategy defined
- [ ] No dev-only defaults in base `application.yml`
- [ ] No stacking `@Async` + `@Retry` on same method

### 🟢 BEST PRACTICE
- [ ] OpenAPI documentation complete
- [ ] Sorting and filtering supported
- [ ] HATEOAS links for discoverability (see [rest-api-fundamentals.md](references/rest-api-fundamentals.md#hateoas-hypermedia))
- [ ] Cursor pagination for large datasets
- [ ] Location header on POST 201

---

## Related Skills

- `common-java-developer` — Modern Java patterns
- `common-java-jpa` — Entity-DTO mapping
- `common-security` — REST API security, OAuth2
- `common-architecture` — API design principles
- `buy-nature-backend-coding-guide` — Buy Nature REST conventions
