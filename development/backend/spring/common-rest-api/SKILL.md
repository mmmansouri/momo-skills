---
name: common-rest-api
description: >-
  REST API design and implementation best practices (HTTP semantics, RFC 7807
  Problem Details, pagination, versioning, OpenAPI, Spring Boot 4 / Spring
  Framework 7 controllers and clients). Use this skill whenever the user
  designs an endpoint, picks a status code, builds a controller or client,
  models a resource URI, paginates or filters a collection, defines a request /
  response DTO, validates a request body, handles a REST exception, versions
  an API, documents one with OpenAPI / Swagger, migrates from RestTemplate
  to RestClient / @HttpExchange, or reviews a PR touching controllers, DTOs,
  request validation, exception handlers, or REST endpoints — even when they
  don't say "REST". Do NOT use
  for GraphQL, gRPC, SOAP, or message-broker integrations (Kafka, RabbitMQ);
  for Spring Boot configuration pitfalls (YAML, profiles, AOP) use
  common-spring-boot-config; for Spring Security use common-security.
---

# REST API Developer Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## When Designing Resource URIs

### 🔴 BLOCKING — URIs name resources (nouns), never actions (verbs)

**Why** : the HTTP method already encodes the action. Putting a verb in the URI (`/getOrder`, `/createOrder`) breaks REST's uniform-interface contract — the same resource ends up with multiple URIs depending on what you do to it, killing cacheability and link-ability.

```
✅ CORRECT                    🔴 WRONG
GET    /orders                GET  /getOrders
POST   /orders                POST /createOrder
GET    /orders/123            GET  /getOrderById?id=123
PUT    /orders/123            POST /updateOrder
DELETE /orders/123            POST /deleteOrder
```

### 🔴 BLOCKING — Collection URIs use plural nouns

**Why** : `/orders/123` reads naturally as "order 123 inside the orders collection". `/order/123` reads as "the singleton 'order' resource has a sub-thing called 123" — which becomes incoherent the moment you add `GET /orders` for the collection.

```
✅ /customers · /orders · /products
🔴 /customer  · /order  · /product
```

### 🟡 URI cosmetics — lowercase, hyphens, no extensions, no trailing slash

```
✅ /user-profiles · /order-items · /orders/123
🔴 /UserProfiles  · /order_items · /orders/123.json · /orders/
```

### 🟡 Limit nesting depth to 2-3 levels

Beyond two levels, prefer top-level resources with query parameters over deeper paths.

```
✅ /customers/5/orders
✅ /reviews?orderId=99&itemId=42

🔴 /customers/5/orders/99/items/42/reviews   (too deep)
```

### 🟢 Use query parameters for filtering, sorting, field selection

```
GET /orders?status=pending&minTotal=100
GET /products?sort=-createdAt,+name
GET /products?fields=id,name,price
```

---

## When Choosing HTTP Methods and Status Codes

### 🔴 BLOCKING — Method must match its semantics (safety + idempotence)

**Why** : caches, proxies, retry logic, and crawlers all assume HTTP method semantics. A `GET` with side effects gets re-executed by a retrying proxy; a non-idempotent `PUT` breaks at-least-once delivery. Deviating from the spec corrupts data through infrastructure you don't control.

| Method | Action | Idempotent | Safe | Body |
|--------|--------|------------|------|------|
| GET    | Retrieve            | Yes  | Yes | No |
| POST   | Create / non-idempotent action | No   | No  | Yes |
| PUT    | Replace             | Yes  | No  | Yes |
| PATCH  | Partial update      | No\* | No  | Yes |
| DELETE | Remove              | Yes  | No  | Optional |

\*PATCH can be made idempotent with the right patch document format.

### 🔴 BLOCKING — Status codes must reflect outcomes, not just success/failure

**Why** : clients route on status codes (200 vs 201 vs 204; 400 vs 409 vs 422). Returning 200 for everything forces clients to parse the body to know what happened, defeating the entire point of HTTP status codes.

Key rules to keep in mind without re-reading the full reference:
- **POST that creates a resource → 201 Created + `Location` header** (not 200)
- **DELETE → 204 No Content** (no body)
- **GET / PUT / PATCH that returns no body → 204 No Content**
- **400 = malformed request** ; **422 = valid syntax but semantic error** ; **409 = business-rule conflict**
- **401 = not authenticated** ; **403 = authenticated but forbidden**

Status codes beyond these cases follow standard RFC 9110 semantics — intentionally not restated here.

---

## When Choosing a Spring Boot 4 HTTP Client

📚 **When configuring `RestClient` / `@HttpExchange` / `WebClient`, comparing client trade-offs, or enabling virtual threads on Java 21+ for high-concurrency blocking I/O → read [spring-rest-clients.md](references/spring-rest-clients.md).**

| Client          | Status            | Use case |
|-----------------|-------------------|----------|
| `RestTemplate`  | Maintenance mode  | Legacy code only — don't rewrite for the sake of rewriting |
| `RestClient`    | ✅ Preferred      | New simple HTTP calls, fluent API |
| `@HttpExchange` | ✅ Preferred      | Multi-endpoint clients defined as interfaces (Feign-style, native Spring) |
| `WebClient`     | Reactive          | Non-blocking / streaming workloads |

### 🟢 Migration path
- **Existing `RestTemplate` code** → keep as-is
- **New simple HTTP call** → `RestClient`
- **New multi-endpoint integration** → `@HttpExchange`
- **High-concurrency blocking I/O on Java 21+** → enable virtual threads

---

## When Handling Errors

📚 **When implementing the RFC 7807 envelope details, building a `@RestControllerAdvice` exception-handler skeleton, or mapping custom exceptions to `ProblemDetail` → read [spring-exception-handling.md](references/spring-exception-handling.md).**

📚 **When needing the full RFC 7807 field reference or worked examples of problem types → read [rest-errors-rfc7807.md](references/rest-errors-rfc7807.md).**

### 🔴 BLOCKING — Error responses use RFC 7807 Problem Details

**Why** : without a standard error envelope, every client writes a custom parser per service, and consistency drifts as the API grows. RFC 7807 (`application/problem+json`) is the IETF-blessed shape that Spring's `ProblemDetail` class and most modern clients understand out of the box.

```json
{
  "type": "https://api.example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 400,
  "detail": "The request contains invalid fields",
  "instance": "/orders/123",
  "errors": [
    { "field": "email",    "message": "must be a valid email address" },
    { "field": "quantity", "message": "must be greater than 0" }
  ]
}
```

### 🔴 BLOCKING — Never expose internal details (stack traces, SQL, framework class names)

**Why** : stack traces and SQL errors leak implementation details that map directly to known CVEs (database version, ORM version, table names). They also expose the internal data model to attackers and confuse legitimate clients.

```json
// 🔴 WRONG — leaks PostgreSQL driver and internal SQL
{ "error": "org.postgresql.util.PSQLException: duplicate key value..." }

// ✅ CORRECT — domain-level message
{ "type": "...", "title": "Email Already Exists", "status": 409,
  "detail": "A user with this email already exists" }
```

---

## When Implementing Pagination

📚 **When implementing offset or cursor pagination with Spring Data `Pageable` / a custom `PageResponse` → read [spring-pagination-hateoas.md](references/spring-pagination-hateoas.md).**

📚 **When designing sort / filter / sparse-fieldset query-param conventions, or shaping offset / cursor response envelopes → read [rest-pagination-filtering.md](references/rest-pagination-filtering.md).**

### 🔴 BLOCKING — Never return unbounded collections

**Why** : a collection that grows to 100k rows kills the server (memory), the network (payload size), and the client (parse time) the day a single tenant crosses the threshold. Pagination must be the default, not an opt-in.

Set sensible defaults (e.g., `size=20`) and a hard maximum (e.g., `size<=100`).

### 🟢 Offset vs cursor — pick by dataset size and consistency requirements

| Approach | Example                                | Best for |
|----------|----------------------------------------|----------|
| Offset   | `GET /orders?page=2&size=20`           | Small / static datasets, random access |
| Cursor   | `GET /orders?limit=20&after=eyJpZCI6…` | Large / dynamic datasets, infinite scroll, stability under concurrent writes |

Rule of thumb: under 10k rows → offset is fine ; over 10k or real-time feed → cursor.

---

## When Versioning APIs

📚 **When wiring Spring Framework 7's `@ApiVersion` / `ApiVersionConfigurer` → read [spring-rest-clients.md](references/spring-rest-clients.md).**

### 🟡 Pick one strategy and stay with it

| Strategy   | Example                              | Trade-off |
|------------|--------------------------------------|-----------|
| URI path   | `/v1/orders`                         | Simple, explicit, cache-friendly — **default choice** |
| Header     | `Api-Version: 1`                     | Clean URIs, less discoverable |
| Media type | `Accept: application/vnd.api.v1+json`| REST-pure, complex, rare |
| Query      | `/orders?version=1`                  | Easy to forget, breaks some caches |

**Default**: URI path. **Escape hatch**: media type for content-negotiated APIs that already use rich `Accept` headers.

Spring Framework 7 ships first-class versioning support (`@ApiVersion`, `ApiVersionConfigurer`).

---

## When Designing Request / Response DTOs

### 🔴 BLOCKING — Controllers expose DTOs, never JPA entities

**Why** : returning an entity couples your wire format to your database schema (any column rename becomes a breaking API change), triggers lazy-loading inside Jackson serialization (`LazyInitializationException` / N+1), and exposes fields you never meant to publish (audit columns, internal flags).

```java
// 🔴 WRONG — entity leaks to the wire
@GetMapping("/{id}")
public Order getOrder(@PathVariable UUID id) {
    return orderRepository.findById(id).orElseThrow();
}

// ✅ CORRECT — DTO at the boundary
@GetMapping("/{id}")
public OrderResponse getOrder(@PathVariable UUID id) {
    return OrderResponse.from(orderService.findById(id));
}
```

### 🟢 Separate DTOs for create / update / response

Distinct shapes prevent **over-posting** (writes accepting read-only fields) and **under-specifying** (responses missing computed fields). Typical separation:

- **Create body** — fields required at insertion time only (validation: `@NotNull`, `@NotEmpty`)
- **Update body** — mutable fields only (validation: `@Size`, `@Min`)
- **Read response** — full server-side representation, often with a `static from(Entity)` / `from(Domain)` factory

Pick suffixes deliberately and apply them consistently across the codebase — e.g. `*Request` / `*Response`, `*Dto`, `*CreationRequest` / `*UpdateRequest` / `*RetrievalResponse`, etc. Document the chosen convention in your project's coding-guide skill so the rule is enforceable in review.

---

## When Validating Requests

📚 **When picking Bean Validation annotations, writing a custom validator, or using validation groups → read [spring-validation.md](references/spring-validation.md).**

### 🔴 BLOCKING — Validate at the controller boundary with `@Valid`

**Why** : pushing validation into services duplicates checks, leaks business logic across layers, and produces inconsistent error shapes. Bean Validation at the controller produces uniform 400 responses with field-level details and runs *before* any service code touches bad input.

```java
@PostMapping
public ResponseEntity<OrderResponse> createOrder(
        @Valid @RequestBody OrderCreationRequest request) {
    Order order = orderService.create(request);
    return ResponseEntity.created(URI.create("/orders/" + order.getId()))
        .body(OrderResponse.from(order));
}
```

---

## When Documenting APIs

📚 **When wiring Springdoc, annotating controllers with `@Operation` / `@ApiResponses` / `@Schema`, or producing a worked OpenAPI controller example → read [spring-openapi-testing.md](references/spring-openapi-testing.md).**

📚 **When writing MockMvc / `@RestClientTest` tests for REST controllers and clients → read [spring-openapi-testing.md](references/spring-openapi-testing.md).**

### 🔴 BLOCKING — Every public endpoint is documented in OpenAPI 3 (Springdoc)

**Why** : an endpoint without an OpenAPI spec is invisible to client codegen, API gateways, contract tests, and external integrators. The cost of documenting at write-time is one annotation; the cost of retrofitting is days of archeology.

Minimum:
- `@Operation(summary, description)` on every handler method
- `@ApiResponses` listing every status code the handler can return
- `@Schema` on every DTO field that needs explanation, example, or constraint
- Springdoc dependency: `springdoc-openapi-starter-webmvc-ui` ≥ `2.6.0` (Spring Boot 4)

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] Resource URIs use plural nouns, no verbs
- [ ] HTTP method matches semantics (safety + idempotence)
- [ ] Status code reflects the outcome (201 + Location on POST-create, 204 on DELETE, 422 vs 400 vs 409)
- [ ] DTOs at controller boundary — no entities exposed
- [ ] Request bodies validated with `@Valid` + Bean Validation
- [ ] Error responses use RFC 7807 (`ProblemDetail` / `application/problem+json`)
- [ ] No internal details (stack traces, SQL, class names) leaked in error bodies
- [ ] Collections are paginated with sensible default + hard maximum
- [ ] Public endpoints have OpenAPI annotations (`@Operation`, `@ApiResponses`, `@Schema`)

### 🟡 WARNING
- [ ] Nested URIs ≤ 3 levels
- [ ] Versioning strategy chosen and applied consistently
- [ ] `Location` header set on `201 Created`
- [ ] Cursor pagination used for collections > 10k rows or real-time feeds
- [ ] New code uses `RestClient` / `@HttpExchange`, not `RestTemplate`

### 🟢 BEST PRACTICE
- [ ] Sorting and filtering supported with documented query-param conventions
- [ ] HATEOAS links for discoverability
- [ ] ETag + `Cache-Control` on cacheable GETs
- [ ] Rate-limit headers (`X-RateLimit-*`, `Retry-After`) on 429 responses

📚 **When adding HATEOAS links, async `202 Accepted` job endpoints, or `X-RateLimit-*` / `Retry-After` headers → read [rest-hypermedia-async.md](references/rest-hypermedia-async.md).**

📚 **When implementing HATEOAS with Spring (`EntityModel`, `CollectionModel`, `PagedModel`), ETag caching, or async endpoints → read [spring-pagination-hateoas.md](references/spring-pagination-hateoas.md).**

📚 **When configuring content negotiation in a Spring controller (multiple representations: JSON / XML / CSV) → read [spring-controllers.md](references/spring-controllers.md).**

---

## Related Skills

- `common-java-developer` — Modern Java patterns (records, sealed types, virtual threads)
- `common-java-jpa` — Entity ↔ DTO mapping, repository design
- `common-java-testing` — MockMvc / `@RestClientTest` / Testcontainers integration tests
- `common-security` — Spring Security 7, OAuth2, JWT, securing the REST surface
- `common-spring-boot-config` — Spring Boot YAML / profiles / AOP / `@ConditionalOnProperty` pitfalls
- `common-architecture` — Bounded contexts, hexagonal layering around the REST adapter
