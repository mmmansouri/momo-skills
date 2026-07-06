# REST Hypermedia, Async & Rate Limiting

## Table of Contents

1. [HATEOAS (Hypermedia)](#hateoas-hypermedia) — HAL format, link relations
2. [Async Operations](#async-operations) — long-running ops, webhooks
3. [Rate Limiting](#rate-limiting) — `X-RateLimit-*` headers, 429 response

---

## HATEOAS (Hypermedia)

### Link Relations

| Relation | Purpose |
|----------|---------|
| self | Link to the resource itself |
| collection | Link to parent collection |
| next/prev | Pagination links |
| first/last | First/last page links |
| create | Link to create related resource |
| edit | Link to update resource |
| delete | Link to delete resource |

### HAL Format (Hypertext Application Language)

```json
{
  "id": "123",
  "status": "pending",
  "total": 99.99,
  "_links": {
    "self": { "href": "/orders/123" },
    "collection": { "href": "/orders" },
    "customer": { "href": "/customers/456" },
    "items": { "href": "/orders/123/items" }
  }
}
```

For the Spring implementation (`EntityModel`, `CollectionModel`, `PagedModel`) see `spring-pagination-hateoas.md`.

---

## Async Operations

### Long-Running Operations

```http
POST /orders/123/export
→ 202 Accepted
Location: /jobs/456

GET /jobs/456
→ 200 OK
{
  "status": "processing",
  "progress": 45,
  "links": {
    "cancel": { "href": "/jobs/456", "method": "DELETE" }
  }
}

GET /jobs/456
→ 303 See Other
Location: /exports/789
```

### Webhooks for Completion

```http
POST /orders/123/export
Content-Type: application/json

{
  "callbackUrl": "https://client.example.com/webhooks/export-complete"
}

→ 202 Accepted
```

---

## Rate Limiting

### Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 998
X-RateLimit-Reset: 1640000000
Retry-After: 60
```

### 429 Response

```json
{
  "type": "https://api.example.com/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "You have exceeded the rate limit of 1000 requests per hour",
  "retryAfter": 60
}
```
