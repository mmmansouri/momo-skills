# Test Data Strategy

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Per-test isolation, uniqueness, cleanup-even-on-failure, and "prefer API over
UI" are stated in `SKILL.md` (§ When Managing Test Data). This reference keeps
the strategy comparison, a condensed **ApiHelper** + **factory**, the cleanup
convention, and the static-fixtures shape.

## Table of Contents

- [Strategy Comparison](#strategy-comparison)
- [API Helper (Preferred)](#api-helper-preferred)
- [Factory Pattern](#factory-pattern)
- [Cleanup](#cleanup)
- [Static Fixtures](#static-fixtures)

---

## Strategy Comparison

| Strategy | Speed | Stability | Use for |
|----------|-------|-----------|---------|
| **API seeding** | ⚡⚡⚡ | ✅✅✅ | Default — fastest, most reliable |
| **UI seeding** | ⚡ | ✅ | Only when the create-flow *is* the test |
| **DB seeding** | ⚡⚡⚡ | ✅✅ | Complex pre-state; tightest coupling |
| **Static fixtures** | ⚡⚡⚡ | ✅ | Reference data only (drifts vs schema) |

---

## API Helper (Preferred)

Wrap the API in a helper the tests and fixtures share. Throw on non-OK so a
seeding failure surfaces immediately.

```typescript
// utils/api-helper.ts
import { APIRequestContext } from '@playwright/test';

export class ApiHelper {
  constructor(private request: APIRequestContext) {}

  async createProduct(product: Partial<Product>): Promise<Product> {
    const response = await this.request.post('/api/products', {
      data: {
        name: product.name ?? 'Test Product',
        price: product.price ?? 99.99,
        stock: product.stock ?? 10,
        category: product.category ?? 'Electronics',
      },
    });
    if (!response.ok()) throw new Error(`createProduct failed: ${response.status()}`);
    return response.json();
  }

  async deleteProduct(id: string): Promise<void> {
    await this.request.delete(`/api/products/${id}`);
  }
}
```

---

## Factory Pattern

Generate unique data per test (counter + timestamp) with `overrides` for the
fields a test cares about — no hard-coded IDs or emails.

```typescript
// fixtures/test-data-factory.ts
let productCounter = 0;

export class TestDataFactory {
  static createProduct(overrides?: Partial<Product>): Product {
    productCounter++;
    return {
      id: `product-${Date.now()}-${productCounter}`,
      name: `Test Product ${productCounter}`,
      price: 99.99,
      stock: 10,
      category: 'Electronics',
      ...overrides,
    };
  }
}
```

---

## Cleanup

### 🔴 BLOCKING — always clean up, even on failure

Prefer a **fixture** (automatic teardown after `use()`):

```typescript
export const test = base.extend<{ testProduct: Product }>({
  testProduct: async ({ request }, use) => {
    const apiHelper = new ApiHelper(request);
    const product = await apiHelper.createProduct(TestDataFactory.createProduct());
    await use(product);
    await apiHelper.deleteProduct(product.id);   // even on failure
  },
});
```

Inside a spec, use `try/finally`. A **global teardown** that deletes by pattern
(`email LIKE '%@test.com'`) is a last-resort safety net, not the primary path.

---

## Static Fixtures

Reference data only — seed it via the API helper, then clean up.

```json
// fixtures/products.json
[
  {
    "id": "eco-water-bottle",
    "name": "Eco-Friendly Water Bottle",
    "price": 24.99,
    "stock": 50,
    "category": "Eco"
  },
  {
    "id": "bamboo-toothbrush",
    "name": "Bamboo Toothbrush Set",
    "price": 12.99,
    "stock": 100,
    "category": "Eco"
  }
]
```
