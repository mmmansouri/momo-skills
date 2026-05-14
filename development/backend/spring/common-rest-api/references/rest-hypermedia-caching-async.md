# REST Hypermedia, Caching, Async & Rate Limiting

## Table of Contents

1. [HATEOAS (Hypermedia)](#hateoas-hypermedia) — HAL format, link relations
2. [Content Negotiation](#content-negotiation) — Accept / Content-Type, media types
3. [Caching](#caching) — Cache-Control, ETag, conditional GET
4. [Async Operations](#async-operations) — long-running ops, webhooks
5. [Rate Limiting](#rate-limiting) — `X-RateLimit-*` headers, 429 response

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
  },
  "_embedded": {
    "items": [
      {
        "productId": "prod-1",
        "quantity": 2,
        "_links": {
          "product": { "href": "/products/prod-1" }
        }
      }
    ]
  }
}
```

### Collection with Pagination Links

```json
{
  "_embedded": {
    "orders": [...]
  },
  "_links": {
    "self": { "href": "/orders?page=2" },
    "first": { "href": "/orders?page=1" },
    "prev": { "href": "/orders?page=1" },
    "next": { "href": "/orders?page=3" },
    "last": { "href": "/orders?page=8" }
  },
  "page": {
    "size": 20,
    "totalElements": 156,
    "totalPages": 8,
    "number": 2
  }
}
```

---

## Content Negotiation

### Request Headers

```http
Accept: application/json
Accept: application/xml
Accept: application/json, application/xml;q=0.9
```

### Response Headers

```http
Content-Type: application/json; charset=utf-8
Content-Type: application/problem+json
```

### Media Types

| Type | Use Case |
|------|----------|
| `application/json` | Standard JSON |
| `application/problem+json` | RFC 7807 errors |
| `application/hal+json` | HAL hypermedia |
| `application/vnd.api+json` | JSON:API format |
| `text/csv` | CSV exports |
| `application/pdf` | PDF documents |

---

## Caching

### Cache Headers

```http
# Response
Cache-Control: max-age=3600, public
ETag: "abc123"
Last-Modified: Tue, 15 Jan 2025 12:00:00 GMT

# Conditional Request
If-None-Match: "abc123"
If-Modified-Since: Tue, 15 Jan 2025 12:00:00 GMT

# Response (not modified)
304 Not Modified
```

### Cache-Control Directives

| Directive | Meaning |
|-----------|---------|
| `public` | Can be cached by any cache |
| `private` | Only browser cache |
| `no-cache` | Revalidate before using |
| `no-store` | Don't cache at all |
| `max-age=N` | Cache for N seconds |
| `must-revalidate` | Must check after expiry |

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
