# REST URIs, HTTP Methods & Status Codes

## Table of Contents

1. [Richardson Maturity Model](#richardson-maturity-model)
2. [Resource Naming Conventions](#resource-naming-conventions) — URI structure, rules, hierarchical resources
3. [HTTP Methods in Detail](#http-methods-in-detail) — GET, POST, PUT, PATCH, DELETE
4. [HTTP Status Codes](#http-status-codes) — full 2xx / 3xx / 4xx / 5xx catalog

---

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
