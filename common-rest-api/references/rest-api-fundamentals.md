# REST API Fundamentals Reference

## Richardson Maturity Model

| Level | Description | Example |
|-------|-------------|---------|
| 0 | Single URI, single verb | POST /api with action in body |
| 1 | Multiple URIs (resources) | /orders, /customers |
| 2 | HTTP verbs | GET /orders, POST /orders |
| 3 | HATEOAS (hypermedia) | Links in responses |

Most public APIs target Level 2. Level 3 provides maximum discoverability.

---

## Resource Naming Conventions

### URI Structure

```
https://api.example.com/v1/{collection}/{id}/{sub-collection}/{sub-id}
```

### Rules

| Rule | Good | Bad |
|------|------|-----|
| Use nouns | `/orders` | `/getOrders` |
| Use plurals | `/customers` | `/customer` |
| Use lowercase | `/user-profiles` | `/UserProfiles` |
| Use hyphens | `/order-items` | `/order_items` |
| No file extensions | `/orders/123` | `/orders/123.json` |
| No trailing slashes | `/orders` | `/orders/` |

### Hierarchical Resources

```
/customers/{customerId}
/customers/{customerId}/orders
/customers/{customerId}/orders/{orderId}
/customers/{customerId}/orders/{orderId}/items
```

### Avoid Deep Nesting

After 2-3 levels, use top-level resources with query parameters:

```
# Instead of this (too deep):
GET /customers/5/orders/99/items/42/reviews

# Use this:
GET /reviews?orderId=99&itemId=42
```

---

## HTTP Methods in Detail

### GET - Retrieve Resources

```http
# Collection
GET /orders
→ 200 OK with array of orders

# Single resource
GET /orders/123
→ 200 OK with order
→ 404 Not Found if doesn't exist

# With filtering
GET /orders?status=pending&customerId=456
→ 200 OK with filtered results
```

**Rules:**
- Must be safe (no side effects)
- Must be idempotent
- Should be cacheable
- Never include request body

### POST - Create Resources

```http
POST /orders
Content-Type: application/json

{
  "customerId": "456",
  "items": [...]
}

→ 201 Created
Location: /orders/789
```

**Rules:**
- Not idempotent (each call creates new resource)
- Return 201 with Location header for created resources
- Return created resource in body (optional but recommended)

### PUT - Replace Resources

```http
PUT /orders/123
Content-Type: application/json

{
  "customerId": "456",
  "items": [...],
  "status": "confirmed"
}

→ 200 OK (updated)
→ 201 Created (if upsert created new resource)
→ 204 No Content (updated, no body returned)
```

**Rules:**
- Must be idempotent
- Must include complete resource representation
- Use for full replacement only

### PATCH - Partial Update

```http
PATCH /orders/123
Content-Type: application/merge-patch+json

{
  "status": "shipped"
}

→ 200 OK
```

**Patch Formats:**

**JSON Merge Patch (RFC 7396):**
```json
{
  "price": 12,
  "color": null,    // Delete field
  "size": "small"   // Add field
}
```

**JSON Patch (RFC 6902):**
```json
[
  { "op": "replace", "path": "/price", "value": 12 },
  { "op": "remove", "path": "/color" },
  { "op": "add", "path": "/size", "value": "small" }
]
```

### DELETE - Remove Resources

```http
DELETE /orders/123
→ 204 No Content
→ 404 Not Found (optional - can return 204 for idempotency)
```

**Rules:**
- Should be idempotent
- Typically returns 204 No Content
- Consider soft delete for audit trails

---

## HTTP Status Codes

### 2xx Success

| Code | Name | When to Use |
|------|------|-------------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST that creates resource |
| 202 | Accepted | Async operation started |
| 204 | No Content | Successful DELETE, PUT/PATCH without body |

### 3xx Redirection

| Code | Name | When to Use |
|------|------|-------------|
| 301 | Moved Permanently | Resource has new permanent URI |
| 302 | Found | Temporary redirect |
| 303 | See Other | Redirect after POST (async result) |
| 304 | Not Modified | Conditional GET, resource unchanged |

### 4xx Client Errors

| Code | Name | When to Use |
|------|------|-------------|
| 400 | Bad Request | Malformed request, validation error |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 405 | Method Not Allowed | HTTP method not supported |
| 406 | Not Acceptable | Cannot produce requested content type |
| 409 | Conflict | Business rule violation, duplicate |
| 410 | Gone | Resource permanently deleted |
| 415 | Unsupported Media Type | Request content type not supported |
| 422 | Unprocessable Entity | Valid syntax but semantic error |
| 429 | Too Many Requests | Rate limit exceeded |

### 5xx Server Errors

| Code | Name | When to Use |
|------|------|-------------|
| 500 | Internal Server Error | Unexpected server error |
| 501 | Not Implemented | Feature not implemented |
| 502 | Bad Gateway | Upstream service error |
| 503 | Service Unavailable | Maintenance or overload |
| 504 | Gateway Timeout | Upstream service timeout |

---

## Error Response Format (RFC 7807)

### Standard Fields

| Field | Type | Description |
|-------|------|-------------|
| type | URI | Identifier for error type |
| title | string | Short human-readable summary |
| status | integer | HTTP status code |
| detail | string | Human-readable explanation |
| instance | URI | URI of specific occurrence |

### Example: Validation Error

```json
{
  "type": "https://api.example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 400,
  "detail": "The request body contains invalid fields",
  "instance": "/orders",
  "errors": [
    {
      "field": "email",
      "message": "must be a valid email address",
      "rejectedValue": "invalid-email"
    },
    {
      "field": "quantity",
      "message": "must be greater than 0",
      "rejectedValue": -5
    }
  ]
}
```

### Example: Business Rule Violation

```json
{
  "type": "https://api.example.com/errors/insufficient-stock",
  "title": "Insufficient Stock",
  "status": 409,
  "detail": "Cannot complete order: Product 'Widget' has only 5 units in stock, but 10 were requested",
  "instance": "/orders/123",
  "productId": "widget-001",
  "availableStock": 5,
  "requestedQuantity": 10
}
```

### Example: Not Found

```json
{
  "type": "https://api.example.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Order with ID '550e8400-e29b-41d4-a716-446655440000' was not found",
  "instance": "/orders/550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Pagination Strategies

### Offset-Based Pagination

**Request:**
```
GET /orders?page=2&size=20
GET /orders?offset=40&limit=20
```

**Response:**
```json
{
  "content": [...],
  "page": {
    "number": 2,
    "size": 20,
    "totalElements": 156,
    "totalPages": 8
  }
}
```

**Pros:**
- Simple to implement
- Allows random page access
- Easy to understand

**Cons:**
- Performance degrades with large offsets (O(offset + limit))
- Inconsistent with concurrent modifications
- Database must scan skipped rows

### Cursor-Based Pagination

**Request:**
```
GET /orders?limit=20&after=eyJpZCI6MTAwfQ
```

**Response:**
```json
{
  "data": [...],
  "cursors": {
    "before": "eyJpZCI6ODJ9",
    "after": "eyJpZCI6MTAxfQ"
  },
  "hasMore": true
}
```

**Cursor Implementation:**
```sql
-- Efficient: uses index
SELECT * FROM orders
WHERE id > :lastSeenId
ORDER BY id ASC
LIMIT 20
```

**Pros:**
- Consistent performance (O(limit))
- Stable with concurrent modifications
- Works well with infinite scroll

**Cons:**
- No random page access
- More complex to implement
- Cursor must be opaque (encoded)

### Best Practices

| Dataset Size | Recommended |
|--------------|-------------|
| < 10,000 rows | Offset OK |
| > 10,000 rows | Cursor preferred |
| Real-time feeds | Cursor required |
| Reports/exports | Offset OK |

---

## Sorting & Filtering

### Sorting

**Single Field:**
```
GET /products?sort=price           # Ascending (default)
GET /products?sort=-price          # Descending
GET /products?sort=price,asc
GET /products?sort=price,desc
```

**Multiple Fields:**
```
GET /products?sort=-createdAt,+name
GET /products?sort=category,asc&sort=price,desc
```

### Filtering

**Equality:**
```
GET /products?category=electronics
GET /products?status=active
```

**Comparison:**
```
GET /products?minPrice=100&maxPrice=500
GET /products?createdAfter=2025-01-01
GET /products?price[gt]=100&price[lt]=500
```

**Multiple Values (OR):**
```
GET /products?status=active,pending
GET /products?category=electronics&category=clothing
```

**Search:**
```
GET /products?q=wireless+headphones
GET /products?search=wireless+headphones
```

### Field Selection (Sparse Fieldsets)

```
GET /products?fields=id,name,price
GET /products?fields=id,name,category.name
```

---

## API Versioning Strategies

### 1. URI Path Versioning (Most Common)

```
https://api.example.com/v1/orders
https://api.example.com/v2/orders
```

**Pros:** Simple, explicit, cache-friendly
**Cons:** Breaks REST principle (URIs should be permanent)

### 2. Query Parameter Versioning

```
https://api.example.com/orders?version=1
https://api.example.com/orders?api-version=2
```

**Pros:** Clean URIs, flexible
**Cons:** Easy to miss, breaks some caches

### 3. Header Versioning

```http
GET /orders
Api-Version: 1
X-Api-Version: 2
```

**Pros:** Clean URIs, REST-compliant
**Cons:** Less discoverable, requires custom headers

### 4. Media Type Versioning (Content Negotiation)

```http
GET /orders
Accept: application/vnd.example.v1+json

→ Content-Type: application/vnd.example.v1+json
```

**Pros:** REST-compliant, supports multiple formats
**Cons:** Complex, less common

### Versioning Best Practices

- Version from day one (even v1)
- Support at least 2 versions concurrently
- Deprecate with warnings before removal
- Document breaking changes clearly
- Use semantic versioning for APIs

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
