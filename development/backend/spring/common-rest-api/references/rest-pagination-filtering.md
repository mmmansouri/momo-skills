# REST Pagination & Filtering

## Table of Contents

1. [Pagination Envelopes](#pagination-envelopes) — offset and cursor response shapes
2. [Sorting & Filtering](#sorting--filtering) — query-param conventions, sparse fieldsets

> Offset-vs-cursor selection and the versioning-strategy table live in the SKILL.md — this file holds the wire conventions only.

---

## Pagination Envelopes

### Offset-Based

```
GET /orders?page=2&size=20
```

```json
{
  "content": [...],
  "page": { "number": 2, "size": 20, "totalElements": 156, "totalPages": 8 }
}
```

### Cursor-Based

```
GET /orders?limit=20&after=eyJpZCI6MTAwfQ
```

```json
{
  "data": [...],
  "cursors": { "before": "eyJpZCI6ODJ9", "after": "eyJpZCI6MTAxfQ" },
  "hasMore": true
}
```

**Cursor implementation** — keyset, uses the index; cursor must be opaque (encoded):

```sql
SELECT * FROM orders
WHERE id > :lastSeenId
ORDER BY id ASC
LIMIT 20
```

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
