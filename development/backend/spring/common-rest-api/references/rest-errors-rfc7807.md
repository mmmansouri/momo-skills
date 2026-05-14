# REST Error Response Format (RFC 7807)

## Table of Contents

1. [Standard Fields](#standard-fields) — RFC 7807 envelope reference
2. [Example: Validation Error](#example-validation-error)
3. [Example: Business Rule Violation](#example-business-rule-violation)
4. [Example: Not Found](#example-not-found)

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
