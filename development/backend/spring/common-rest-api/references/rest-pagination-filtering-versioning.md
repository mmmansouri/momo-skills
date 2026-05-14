# REST Pagination, Filtering & Versioning

## Table of Contents

1. [Pagination Strategies](#pagination-strategies) — offset vs cursor, decision matrix
2. [Sorting & Filtering](#sorting--filtering) — query-param conventions, sparse fieldsets
3. [API Versioning Strategies](#api-versioning-strategies) — URI / query / header / media type

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
