# Custom Fixtures in Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

The `base.extend<T>({ ... })` mechanism, built-in fixtures (`page`, `context`,
`request`), the setup → `use()` → teardown lifecycle, and fixture dependency
resolution are native Playwright knowledge — see the official fixtures docs. This
reference keeps only the house fixtures: the **two-tier authenticated page**, the
**test-vs-worker scope** decision, and the **cleanup** convention.

## Table of Contents

- [Test vs Worker Scope](#test-vs-worker-scope)
- [Authenticated Page Fixture (Two-Tier Auth)](#authenticated-page-fixture-two-tier-auth)
- [Cleanup Fixtures](#cleanup-fixtures)
- [Testcontainers Database Fixtures](#testcontainers-database-fixtures)

---

## Test vs Worker Scope

| Scope | Runs | Cleanup | Use for |
|-------|------|---------|---------|
| `test` (default) | Once per test | After each test | Isolated state: page objects, per-test data |
| `worker` | Once per worker | After all tests in the worker | Expensive shared setup: DB container, admin account |

### 🔴 BLOCKING

- **Test-scoped** for anything a test mutates (page, cart, per-test entities).
- **Worker-scoped** only for expensive read-mostly setup. Worker fixtures share
  one instance across every test in the worker, so they must never hold state a
  test can corrupt.

---

## Authenticated Page Fixture (Two-Tier Auth)

House auth is two-tier OAuth2 (`client_credentials` grant, then `password`
grant, both on `/oauth/token`). An `AuthHelper` performs both grants over the API
and drops the resulting token into `localStorage`, so tests start already logged
in without paying the UI login cost on every spec.

```typescript
// fixtures/auth.fixture.ts
import { test as base, Page } from '@playwright/test';
import { ApiHelper } from '../utils/api-helper';

type AuthFixtures = {
  apiHelper: ApiHelper;
  authenticatedPage: Page;   // logged in as a customer
  adminPage: Page;           // logged in as an admin
};

export const test = base.extend<AuthFixtures>({
  apiHelper: async ({ request }, use) => {
    await use(new ApiHelper(request));
  },

  authenticatedPage: async ({ page, apiHelper }, use) => {
    // Two-tier: client_credentials grant, then password grant.
    const token = await apiHelper.loginAsCustomer('john.doe@example.com', 'password123');
    await page.goto('/');
    await page.evaluate(t => localStorage.setItem('access_token', t), token);

    await use(page);

    await page.evaluate(() => localStorage.clear());
  },

  adminPage: async ({ page, apiHelper }, use) => {
    const token = await apiHelper.loginAsAdmin('admin@example.com', 'admin123');
    await page.goto('/');
    await page.evaluate(t => localStorage.setItem('access_token', t), token);

    await use(page);

    await page.evaluate(() => localStorage.clear());
  },
});

export { expect } from '@playwright/test';
```

**Usage:**

```typescript
import { test, expect } from './fixtures/auth.fixture';

test('should access dashboard as customer', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/dashboard');
  await expect(authenticatedPage.getByText('Welcome, John')).toBeVisible();
});

test('should access admin panel', async ({ adminPage }) => {
  await adminPage.goto('/admin/users');
  await expect(adminPage.getByRole('heading', { name: 'User Management' })).toBeVisible();
});
```

The `AuthHelper.loginViaApi` implementation (the two `/oauth/token` POSTs) lives
in [page-objects-playwright.md](page-objects-playwright.md#two-tier-authentication-integration).

---

## Cleanup Fixtures

### 🔴 BLOCKING

Every fixture that creates data cleans it up **after `use()`** — teardown runs
even when the test fails, so entities never leak between tests.

```typescript
export const test = base.extend<{ testProduct: Product }>({
  testProduct: async ({ apiHelper }, use) => {
    const product = await apiHelper.createProduct({ name: `Test ${Date.now()}`, price: 99.99 });
    await use(product);
    await apiHelper.deleteProduct(product.id);   // runs even on failure
  },
});
```

Never share a mutable entity through a module-level variable — create a fresh one
per test (test scope) so the suite stays parallelizable. Data-factory fixtures
are covered in [test-data.md](test-data.md).

---

## Testcontainers Database Fixtures

When a test needs to assert directly against the database, a **worker-scoped**
Testcontainers Postgres fixture (`new GenericContainer('postgres:15')`, exposed
port 5432, one `pg` `Pool`) starts the container once per worker and stops it in
teardown. Reach for it only when API/UI assertions cannot express the check —
it is the slowest strategy.
