# Fixtures Guide for Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

Fixtures are reusable setups that provide initialized objects to tests. Playwright's fixture system allows dependency injection, automatic cleanup, and shared state management.

**Benefits:**
- DRY: Define setup once, reuse across tests
- Automatic cleanup: Teardown happens even if test fails
- Dependency injection: Fixtures can depend on other fixtures
- Type-safe: Full TypeScript support

---

## Built-in Fixtures

### 🔴 BLOCKING - Core Fixtures

Playwright provides these fixtures out of the box:

```typescript
import { test, expect } from '@playwright/test';

test('example test', async ({ page, context, browser, request }) => {
  // page: Fresh browser page for this test
  await page.goto('/products');

  // context: Browser context (isolated session)
  const newPage = await context.newPage();

  // browser: Browser instance
  const browserVersion = browser.version();

  // request: API request context
  const response = await request.get('/api/products');
});
```

**Common Built-in Fixtures:**

| Fixture | Type | Description |
|---------|------|-------------|
| `page` | `Page` | Isolated browser page |
| `context` | `BrowserContext` | Browser context (cookies, storage) |
| `browser` | `Browser` | Browser instance |
| `request` | `APIRequestContext` | HTTP client for API calls |
| `browserName` | `string` | Current browser name |

---

## Custom Fixtures

### 🔴 BLOCKING - Creating Fixtures

```typescript
// fixtures/index.ts
import { test as base } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { CatalogPage } from '../pages/catalog.page';

// Define custom fixture types
type MyFixtures = {
  loginPage: LoginPage;
  catalogPage: CatalogPage;
};

// Extend base test with custom fixtures
export const test = base.extend<MyFixtures>({
  loginPage: async ({ page }, use) => {
    // Setup: Create page object
    const loginPage = new LoginPage(page);

    // Provide to test
    await use(loginPage);

    // Teardown: Optional cleanup
    // (automatically runs even if test fails)
  },

  catalogPage: async ({ page }, use) => {
    const catalogPage = new CatalogPage(page);
    await catalogPage.goto(); // Navigate before test
    await use(catalogPage);
  },
});

export { expect } from '@playwright/test';
```

**Usage:**
```typescript
import { test, expect } from './fixtures';

test('should login', async ({ loginPage }) => {
  await loginPage.goto();
  await loginPage.login('user@test.com', 'password');
  await expect(loginPage.page).toHaveURL('/dashboard');
});
```

---

## Fixture Lifecycle

### Setup → Use → Teardown Pattern

```typescript
export const test = base.extend<{ tempFile: string }>({
  tempFile: async ({}, use) => {
    console.log('SETUP: Creating temp file');
    const filePath = '/tmp/test-data.json';
    await fs.writeFile(filePath, JSON.stringify({ test: true }));

    console.log('USE: Test is running');
    await use(filePath);

    console.log('TEARDOWN: Cleaning up temp file');
    await fs.unlink(filePath);
  },
});
```

**Execution Order:**
```
1. SETUP: Creating temp file
2. USE: Test is running
3. (Test code executes)
4. TEARDOWN: Cleaning up temp file (even if test fails)
```

---

## Fixture Dependencies

### 🔴 BLOCKING - Fixtures Can Depend on Other Fixtures

```typescript
type MyFixtures = {
  apiHelper: ApiHelper;
  authenticatedPage: Page;
  testUser: User;
};

export const test = base.extend<MyFixtures>({
  // Simple fixture
  apiHelper: async ({ request }, use) => {
    const helper = new ApiHelper(request);
    await use(helper);
  },

  // Fixture depending on apiHelper
  testUser: async ({ apiHelper }, use) => {
    const user = await apiHelper.createUser({
      email: 'test@example.com',
      password: 'Test123!',
    });
    await use(user);

    // Cleanup
    await apiHelper.deleteUser(user.id);
  },

  // Fixture depending on testUser and page
  authenticatedPage: async ({ page, testUser, apiHelper }, use) => {
    const token = await apiHelper.login(testUser.email, 'Test123!');
    await page.goto('/');
    await page.evaluate(t => localStorage.setItem('token', t), token);
    await use(page);

    // Cleanup
    await page.evaluate(() => localStorage.clear());
  },
});
```

**Dependency Graph:**
```
authenticatedPage
├── page (built-in)
├── testUser
│   └── apiHelper
│       └── request (built-in)
└── apiHelper
```

---

## Worker-Scoped Fixtures

### 🔴 BLOCKING - Share State Across Tests

Worker-scoped fixtures run once per worker process, shared across all tests in that worker.

```typescript
type WorkerFixtures = {
  adminUser: User;
};

export const test = base.extend<{}, WorkerFixtures>({
  adminUser: [
    async ({ browser }, use) => {
      console.log('Creating admin user (once per worker)');
      const user = await createUserInDatabase({
        email: 'admin@test.com',
        role: 'ADMIN',
      });

      await use(user);

      console.log('Deleting admin user');
      await deleteUserFromDatabase(user.id);
    },
    { scope: 'worker' },
  ],
});
```

**Usage:**
```typescript
test('admin can view users', async ({ page, adminUser }) => {
  // adminUser is shared across all tests in this worker
  await loginAs(page, adminUser);
  await page.goto('/admin/users');
});

test('admin can create user', async ({ page, adminUser }) => {
  // Same adminUser instance as previous test
  await loginAs(page, adminUser);
  await createUser(page, 'newuser@test.com');
});
```

### Scope Comparison

| Scope | Runs | Cleanup | Use Case |
|-------|------|---------|----------|
| `test` (default) | Once per test | After each test | Isolated state (page, test data) |
| `worker` | Once per worker | After all tests in worker | Shared state (database, user accounts) |

---

## Authenticated Page Fixture (Buy Nature)

### 🔴 BLOCKING - Two-Tier Authentication

```typescript
// fixtures/auth.fixture.ts
import { test as base, Page } from '@playwright/test';
import { ApiHelper } from '../utils/api-helper';

type AuthFixtures = {
  apiHelper: ApiHelper;
  authenticatedPage: Page;
  adminPage: Page;
};

export const test = base.extend<AuthFixtures>({
  apiHelper: async ({ request }, use) => {
    const helper = new ApiHelper(request);
    await use(helper);
  },

  authenticatedPage: async ({ page, apiHelper }, use) => {
    // Two-tier auth:
    // 1. Client credentials (OAuth2)
    // 2. User login (password grant)
    const token = await apiHelper.loginAsCustomer(
      'john.doe@example.com',
      'Str0ngP@ssword123!'
    );

    // Store token in browser
    await page.goto('/');
    await page.evaluate(t => {
      localStorage.setItem('access_token', t);
    }, token);

    await use(page);

    // Cleanup
    await page.evaluate(() => localStorage.clear());
  },

  adminPage: async ({ page, apiHelper }, use) => {
    const token = await apiHelper.loginAsAdmin('admin@buynature.com', 'admin123');

    await page.goto('/');
    await page.evaluate(t => {
      localStorage.setItem('access_token', t);
    }, token);

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

---

## Test Data Fixtures

### 🔴 BLOCKING - Factory-Based Test Data

```typescript
// fixtures/test-data.fixture.ts
type TestDataFixtures = {
  testProduct: Product;
  testProducts: Product[];
  testOrder: Order;
};

export const test = base.extend<TestDataFixtures>({
  testProduct: async ({ apiHelper }, use) => {
    const product = await apiHelper.createProduct({
      name: `Test Product ${Date.now()}`,
      price: 99.99,
      stock: 10,
    });

    await use(product);

    // Cleanup
    await apiHelper.deleteProduct(product.id);
  },

  testProducts: async ({ apiHelper }, use) => {
    const products = await Promise.all([
      apiHelper.createProduct({ name: 'Product 1', price: 10 }),
      apiHelper.createProduct({ name: 'Product 2', price: 20 }),
      apiHelper.createProduct({ name: 'Product 3', price: 30 }),
    ]);

    await use(products);

    // Cleanup all
    await Promise.all(products.map(p => apiHelper.deleteProduct(p.id)));
  },

  testOrder: async ({ apiHelper, testProduct, authenticatedPage }, use) => {
    // Create order for test product
    const order = await apiHelper.createOrder({
      userId: 'test-user-id',
      items: [{ productId: testProduct.id, quantity: 1 }],
    });

    await use(order);

    await apiHelper.deleteOrder(order.id);
  },
});
```

**Usage:**
```typescript
test('should display product details', async ({ page, testProduct }) => {
  await page.goto(`/products/${testProduct.id}`);
  await expect(page.getByText(testProduct.name)).toBeVisible();
  await expect(page.getByTestId('product-price')).toHaveText(`€${testProduct.price}`);
});

test('should list products', async ({ page, testProducts }) => {
  await page.goto('/products');
  for (const product of testProducts) {
    await expect(page.getByText(product.name)).toBeVisible();
  }
});
```

---

## Database Fixtures with Testcontainers

### 🔴 BLOCKING - Worker-Scoped Database

```typescript
import { GenericContainer, StartedTestContainer } from 'testcontainers';
import { Pool } from 'pg';

type DatabaseFixtures = {
  dbContainer: StartedTestContainer;
  dbPool: Pool;
};

export const test = base.extend<{}, DatabaseFixtures>({
  dbContainer: [
    async ({}, use) => {
      console.log('Starting PostgreSQL container...');
      const container = await new GenericContainer('postgres:15')
        .withEnvironment({
          POSTGRES_USER: 'test',
          POSTGRES_PASSWORD: 'test',
          POSTGRES_DB: 'testdb',
        })
        .withExposedPorts(5432)
        .start();

      await use(container);

      console.log('Stopping PostgreSQL container...');
      await container.stop();
    },
    { scope: 'worker' },
  ],

  dbPool: [
    async ({ dbContainer }, use) => {
      const pool = new Pool({
        host: dbContainer.getHost(),
        port: dbContainer.getMappedPort(5432),
        user: 'test',
        password: 'test',
        database: 'testdb',
      });

      await use(pool);

      await pool.end();
    },
    { scope: 'worker' },
  ],
});
```

**Usage:**
```typescript
test('should save user to database', async ({ page, dbPool }) => {
  // Create user via UI
  await page.goto('/signup');
  await page.getByLabel('Email').fill('user@test.com');
  await page.getByRole('button', { name: 'Sign Up' }).click();

  // Verify in database
  const result = await dbPool.query('SELECT * FROM users WHERE email = $1', [
    'user@test.com',
  ]);
  expect(result.rows).toHaveLength(1);
  expect(result.rows[0].email).toBe('user@test.com');
});
```

---

## Fixture Options

### 🟢 BEST PRACTICE - Configurable Fixtures

```typescript
type OptionsFixture = {
  loginPage: LoginPage;
  locale: 'en' | 'fr';
};

export const test = base.extend<OptionsFixture>({
  locale: ['en', { option: true }], // Default value

  loginPage: async ({ page, locale }, use) => {
    // Use locale option
    await page.goto(`/${locale}/login`);
    const loginPage = new LoginPage(page);
    await use(loginPage);
  },
});
```

**Usage:**
```typescript
test('should login in French', async ({ loginPage }) => {
  test.use({ locale: 'fr' });
  await loginPage.login('user@test.com', 'password');
  await expect(loginPage.page.getByText('Bienvenue')).toBeVisible();
});
```

---

## Quick Reference

### Fixtures Checklist

#### 🔴 BLOCKING
- [ ] Use fixtures for repeated setup
- [ ] Provide cleanup in fixture teardown
- [ ] Worker-scoped for expensive setup (database, containers)
- [ ] Test-scoped for isolated state (page objects, test data)
- [ ] Export custom `test` and `expect` from fixtures file

#### 🟡 WARNING
- [ ] Fixtures don't have side effects (idempotent)
- [ ] Dependencies declared explicitly
- [ ] Cleanup runs even if test fails
- [ ] Avoid complex fixture dependency chains

#### 🟢 BEST PRACTICE
- [ ] Type-safe fixture definitions
- [ ] Page objects as fixtures
- [ ] API helpers as fixtures
- [ ] Test data factories as fixtures
- [ ] Authenticated pages as fixtures

---

## Common Patterns

### Pattern: Fixture Composition

```typescript
// Base fixtures
export const baseTest = base.extend<{ apiHelper: ApiHelper }>({
  apiHelper: async ({ request }, use) => {
    await use(new ApiHelper(request));
  },
});

// Auth fixtures (extends base)
export const authTest = baseTest.extend<{ authenticatedPage: Page }>({
  authenticatedPage: async ({ page, apiHelper }, use) => {
    const token = await apiHelper.login('user@test.com', 'password');
    await page.goto('/');
    await page.evaluate(t => localStorage.setItem('token', t), token);
    await use(page);
  },
});

// Test data fixtures (extends auth)
export const test = authTest.extend<{ testOrder: Order }>({
  testOrder: async ({ apiHelper }, use) => {
    const order = await apiHelper.createOrder({ items: [] });
    await use(order);
    await apiHelper.deleteOrder(order.id);
  },
});
```

### Pattern: Conditional Fixtures

```typescript
export const test = base.extend<{ slowOperation: string }>({
  slowOperation: async ({}, use, testInfo) => {
    // Skip fixture for tests tagged @fast
    if (testInfo.tags.includes('@fast')) {
      await use('skipped');
      return;
    }

    // Run expensive operation
    const result = await expensiveSetup();
    await use(result);
    await expensiveCleanup(result);
  },
});
```

---

## Anti-Patterns

### 🔴 WRONG - Shared Mutable State

```typescript
// ❌ Don't do this
let sharedUser: User;

export const test = base.extend<{ user: User }>({
  user: async ({}, use) => {
    sharedUser = await createUser(); // ❌ Shared across tests
    await use(sharedUser);
  },
});
```

### ✅ CORRECT - Isolated State

```typescript
// ✅ Do this instead
export const test = base.extend<{ user: User }>({
  user: async ({}, use) => {
    const user = await createUser(); // ✅ New user per test
    await use(user);
    await deleteUser(user.id);
  },
});
```

### 🔴 WRONG - Missing Cleanup

```typescript
// ❌ Don't do this
export const test = base.extend<{ tempData: TempData }>({
  tempData: async ({}, use) => {
    const data = await createTempData();
    await use(data);
    // ❌ No cleanup - data leaks
  },
});
```

### ✅ CORRECT - Always Cleanup

```typescript
// ✅ Do this instead
export const test = base.extend<{ tempData: TempData }>({
  tempData: async ({}, use) => {
    const data = await createTempData();
    await use(data);
    await cleanupTempData(data); // ✅ Cleanup
  },
});
```
