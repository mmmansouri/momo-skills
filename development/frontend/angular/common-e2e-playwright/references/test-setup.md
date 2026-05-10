# Test Setup: Data and Fixtures

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

## Table of Contents

- [Test Data Strategy](#test-data-strategy)
  - [Data Overview](#data-overview)
  - [Test Data Strategies](#test-data-strategies)
  - [API-Based Test Data](#api-based-test-data)
  - [Factory Pattern](#factory-pattern)
  - [Database Seeding](#database-seeding)
  - [Static Fixtures](#static-fixtures)
  - [Cleanup Strategies](#cleanup-strategies)
  - [Example Data Scenarios](#example-data-scenarios)
  - [Test Data Quick Reference](#test-data-quick-reference)
  - [Test Data Common Patterns](#test-data-common-patterns)
  - [Test Data Anti-Patterns](#test-data-anti-patterns)
- [Custom Fixtures](#custom-fixtures)
  - [Fixtures Overview](#fixtures-overview)
  - [Built-in Fixtures](#built-in-fixtures)
  - [Creating Custom Fixtures](#creating-custom-fixtures)
  - [Fixture Lifecycle](#fixture-lifecycle)
  - [Fixture Dependencies](#fixture-dependencies)
  - [Worker-Scoped Fixtures](#worker-scoped-fixtures)
  - [Authenticated Page Fixture](#authenticated-page-fixture)
  - [Test Data Fixtures](#test-data-fixtures)
  - [Database Fixtures with Testcontainers](#database-fixtures-with-testcontainers)
  - [Fixture Options](#fixture-options)
  - [Fixtures Quick Reference](#fixtures-quick-reference)
  - [Fixtures Common Patterns](#fixtures-common-patterns)
  - [Fixtures Anti-Patterns](#fixtures-anti-patterns)

---

## Test Data Strategy

### Data Overview

Test data management is critical for reliable, maintainable E2E tests. This guide covers strategies for creating, managing, and cleaning up test data.

**Principles:**
1. **Isolation**: Each test creates its own data
2. **Uniqueness**: Avoid data collisions between tests
3. **Cleanup**: Clean up after tests complete
4. **Speed**: Fast data creation (prefer API over UI)

---

### Test Data Strategies

#### 🔴 BLOCKING - Choose the Right Strategy

| Strategy | Speed | Stability | Use Case |
|----------|-------|-----------|----------|
| **API seeding** | ⚡⚡⚡ | ✅✅✅ | Fastest, most reliable |
| **UI seeding** | ⚡ | ✅ | Testing create flows |
| **Database seeding** | ⚡⚡⚡ | ✅✅ | Complex data setup |
| **Static fixtures** | ⚡⚡⚡ | ✅ | Reference data |

---

### API-Based Test Data

#### 🔴 BLOCKING - Preferred Method

```typescript
// utils/api-helper.ts
import { APIRequestContext } from '@playwright/test';

export class ApiHelper {
  constructor(private request: APIRequestContext) {}

  async createProduct(product: Partial<Product>): Promise<Product> {
    const response = await this.request.post('/api/products', {
      data: {
        name: product.name || 'Test Product',
        price: product.price || 99.99,
        stock: product.stock || 10,
        category: product.category || 'Electronics',
      },
    });

    if (!response.ok()) {
      throw new Error(`Failed to create product: ${response.status()}`);
    }

    return await response.json();
  }

  async deleteProduct(id: string): Promise<void> {
    await this.request.delete(`/api/products/${id}`);
  }

  async createUser(user: Partial<User>): Promise<User> {
    const response = await this.request.post('/api/users', {
      data: {
        email: user.email || `user-${Date.now()}@test.com`,
        password: user.password || 'Test123!',
        name: user.name || 'Test User',
      },
    });

    return await response.json();
  }

  async deleteUser(id: string): Promise<void> {
    await this.request.delete(`/api/users/${id}`);
  }
}
```

**Usage:**
```typescript
import { test, expect } from '@playwright/test';
import { ApiHelper } from '../utils/api-helper';

test('should display product details', async ({ page, request }) => {
  const apiHelper = new ApiHelper(request);

  // Create test product via API (fast)
  const product = await apiHelper.createProduct({
    name: 'Eco-Friendly Water Bottle',
    price: 24.99,
  });

  // Navigate to product page
  await page.goto(`/products/${product.id}`);

  // Verify UI displays correct data
  await expect(page.getByTestId('product-name')).toHaveText('Eco-Friendly Water Bottle');
  await expect(page.getByTestId('product-price')).toHaveText('€24.99');

  // Cleanup
  await apiHelper.deleteProduct(product.id);
});
```

---

### Factory Pattern

#### 🔴 BLOCKING - Unique Data Per Test

```typescript
// fixtures/test-data-factory.ts
let userCounter = 0;
let productCounter = 0;
let orderCounter = 0;

export class TestDataFactory {
  /**
   * Create a unique test user
   */
  static createUser(overrides?: Partial<User>): User {
    userCounter++;
    return {
      id: `user-${Date.now()}-${userCounter}`,
      email: `user-${Date.now()}-${userCounter}@test.com`,
      password: 'Test123!',
      name: `Test User ${userCounter}`,
      role: 'CUSTOMER',
      ...overrides,
    };
  }

  /**
   * Create a unique test product
   */
  static createProduct(overrides?: Partial<Product>): Product {
    productCounter++;
    return {
      id: `product-${Date.now()}-${productCounter}`,
      name: `Test Product ${productCounter}`,
      description: `Description for test product ${productCounter}`,
      price: 99.99,
      stock: 10,
      category: 'Electronics',
      ...overrides,
    };
  }

  /**
   * Create a unique test order
   */
  static createOrder(userId: string, items: OrderItem[], overrides?: Partial<Order>): Order {
    orderCounter++;
    const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);

    return {
      id: `order-${Date.now()}-${orderCounter}`,
      userId,
      items,
      total,
      status: 'PENDING',
      createdAt: new Date().toISOString(),
      ...overrides,
    };
  }

  /**
   * Reset all counters (call in global teardown)
   */
  static reset(): void {
    userCounter = 0;
    productCounter = 0;
    orderCounter = 0;
  }
}
```

**Usage:**
```typescript
test('should create order', async ({ page, request }) => {
  const apiHelper = new ApiHelper(request);

  // Create unique test data
  const user = TestDataFactory.createUser();
  const product1 = TestDataFactory.createProduct({ name: 'Laptop', price: 999 });
  const product2 = TestDataFactory.createProduct({ name: 'Mouse', price: 25 });

  // Seed data via API
  await apiHelper.createUser(user);
  await apiHelper.createProduct(product1);
  await apiHelper.createProduct(product2);

  // Test the UI
  await loginAs(page, user);
  await addToCart(page, product1.id);
  await addToCart(page, product2.id);
  await checkout(page);

  await expect(page.getByText(`Total: €${999 + 25}`)).toBeVisible();

  // Cleanup
  await apiHelper.deleteUser(user.id);
  await apiHelper.deleteProduct(product1.id);
  await apiHelper.deleteProduct(product2.id);
});
```

---

### Database Seeding

#### 🟡 WARNING - Use for Complex Setup

```typescript
// utils/db-helper.ts
import { Pool } from 'pg';

export class DbHelper {
  constructor(private pool: Pool) {}

  async seedProducts(products: Product[]): Promise<void> {
    const client = await this.pool.connect();

    try {
      await client.query('BEGIN');

      for (const product of products) {
        await client.query(
          `INSERT INTO products (id, name, price, stock, category)
           VALUES ($1, $2, $3, $4, $5)`,
          [product.id, product.name, product.price, product.stock, product.category]
        );
      }

      await client.query('COMMIT');
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  async cleanupProducts(productIds: string[]): Promise<void> {
    await this.pool.query('DELETE FROM products WHERE id = ANY($1)', [productIds]);
  }

  async cleanupUsers(userIds: string[]): Promise<void> {
    await this.pool.query('DELETE FROM users WHERE id = ANY($1)', [userIds]);
  }
}
```

**Usage:**
```typescript
test('should display 100 products', async ({ page }) => {
  const dbHelper = new DbHelper(dbPool);

  // Seed 100 products directly to database (very fast)
  const products = Array.from({ length: 100 }, (_, i) =>
    TestDataFactory.createProduct({ name: `Product ${i + 1}` })
  );
  await dbHelper.seedProducts(products);

  await page.goto('/products');
  await expect(page.getByTestId('product-card')).toHaveCount(100);

  // Cleanup
  await dbHelper.cleanupProducts(products.map(p => p.id));
});
```

---

### Static Fixtures

#### 🟢 BEST PRACTICE - Reference Data

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

**Usage:**
```typescript
import products from '../fixtures/products.json';

test('should display featured products', async ({ page, request }) => {
  const apiHelper = new ApiHelper(request);

  // Seed static reference data
  for (const product of products) {
    await apiHelper.createProduct(product);
  }

  await page.goto('/');
  await expect(page.getByText('Eco-Friendly Water Bottle')).toBeVisible();

  // Cleanup
  for (const product of products) {
    await apiHelper.deleteProduct(product.id);
  }
});
```

---

### Cleanup Strategies

#### 🔴 BLOCKING - Always Clean Up

##### 1. Test-Level Cleanup (Preferred)

```typescript
test('should create order', async ({ page, request }) => {
  const apiHelper = new ApiHelper(request);
  const user = TestDataFactory.createUser();
  const product = TestDataFactory.createProduct();

  try {
    // Create test data
    await apiHelper.createUser(user);
    await apiHelper.createProduct(product);

    // Run test
    await loginAs(page, user);
    await addToCart(page, product.id);
    await checkout(page);

    await expect(page.getByText('Order created')).toBeVisible();
  } finally {
    // Cleanup runs even if test fails
    await apiHelper.deleteUser(user.id);
    await apiHelper.deleteProduct(product.id);
  }
});
```

##### 2. Fixture-Based Cleanup (Best)

```typescript
// fixtures/test-data.fixture.ts
type TestDataFixtures = {
  testProduct: Product;
};

export const test = base.extend<TestDataFixtures>({
  testProduct: async ({ request }, use) => {
    const apiHelper = new ApiHelper(request);
    const product = TestDataFactory.createProduct();

    // Setup
    await apiHelper.createProduct(product);

    // Provide to test
    await use(product);

    // Cleanup (automatic, even on failure)
    await apiHelper.deleteProduct(product.id);
  },
});

// Usage
test('should display product', async ({ page, testProduct }) => {
  await page.goto(`/products/${testProduct.id}`);
  await expect(page.getByText(testProduct.name)).toBeVisible();
  // testProduct automatically cleaned up
});
```

##### 3. Global Cleanup (Last Resort)

```typescript
// global-teardown.ts
import { Pool } from 'pg';

async function globalTeardown() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });

  // Delete all test data
  await pool.query(`DELETE FROM users WHERE email LIKE '%@test.com'`);
  await pool.query(`DELETE FROM products WHERE name LIKE 'Test Product%'`);
  await pool.query(`DELETE FROM orders WHERE id LIKE 'order-%'`);

  await pool.end();
}

export default globalTeardown;
```

---

### Example Data Scenarios

#### Customer Registration Flow

```typescript
test('should register new customer', async ({ page, request }) => {
  const apiHelper = new ApiHelper(request);
  const user = TestDataFactory.createUser({
    email: 'newcustomer@test.com',
    password: 'NewPass123!',
  });

  try {
    // Test registration via UI
    await page.goto('/register');
    await page.getByLabel('Email').fill(user.email);
    await page.getByLabel('Password').fill(user.password);
    await page.getByLabel('Confirm Password').fill(user.password);
    await page.getByRole('button', { name: 'Sign Up' }).click();

    // Verify account created
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText(`Welcome, ${user.name}`)).toBeVisible();
  } finally {
    // Cleanup user account
    await apiHelper.deleteUser(user.id);
  }
});
```

#### Checkout Flow with Multiple Products

```typescript
test('should checkout with multiple products', async ({ page, request }) => {
  const apiHelper = new ApiHelper(request);

  // Create test data
  const user = TestDataFactory.createUser();
  const products = [
    TestDataFactory.createProduct({ name: 'Laptop', price: 999 }),
    TestDataFactory.createProduct({ name: 'Mouse', price: 25 }),
    TestDataFactory.createProduct({ name: 'Keyboard', price: 75 }),
  ];

  try {
    // Seed data via API
    await apiHelper.createUser(user);
    for (const product of products) {
      await apiHelper.createProduct(product);
    }

    // Login
    await loginAs(page, user);

    // Add all products to cart
    for (const product of products) {
      await page.goto(`/products/${product.id}`);
      await page.getByRole('button', { name: 'Add to Cart' }).click();
    }

    // Checkout
    await page.goto('/cart');
    await page.getByRole('button', { name: 'Checkout' }).click();

    // Fill checkout form
    await page.getByLabel('Shipping Address').fill('123 Main St');
    await page.getByRole('combobox', { name: 'Payment Method' }).selectOption('credit-card');
    await page.getByLabel('Card Number').fill('4242 4242 4242 4242');
    await page.getByRole('button', { name: 'Place Order' }).click();

    // Verify total
    const expectedTotal = products.reduce((sum, p) => sum + p.price, 0);
    await expect(page.getByText(`Total: €${expectedTotal}`)).toBeVisible();
  } finally {
    // Cleanup
    await apiHelper.deleteUser(user.id);
    for (const product of products) {
      await apiHelper.deleteProduct(product.id);
    }
  }
});
```

#### Admin Product Management

```typescript
test('should create product in backoffice', async ({ page, request }) => {
  const apiHelper = new ApiHelper(request);
  const admin = TestDataFactory.createUser({ role: 'ADMIN' });
  const product = TestDataFactory.createProduct();

  try {
    // Create admin user
    await apiHelper.createUser(admin);

    // Login as admin
    await page.goto('/admin/login');
    await page.getByLabel('Email').fill(admin.email);
    await page.getByLabel('Password').fill(admin.password);
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Create product via backoffice UI
    await page.getByRole('link', { name: 'Products' }).click();
    await page.getByRole('button', { name: 'Add Product' }).click();

    await page.getByLabel('Product Name').fill(product.name);
    await page.getByLabel('Price').fill(product.price.toString());
    await page.getByLabel('Stock').fill(product.stock.toString());
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByText('Product created successfully')).toBeVisible();
  } finally {
    // Cleanup
    await apiHelper.deleteUser(admin.id);
    await apiHelper.deleteProduct(product.id);
  }
});
```

---

### Test Data Quick Reference

#### Test Data Checklist

##### 🔴 BLOCKING
- [ ] Each test creates its own unique data
- [ ] Data created via API (fastest)
- [ ] Data cleaned up after test (even on failure)
- [ ] No hard-coded IDs or emails
- [ ] Factory pattern for consistent data generation

##### 🟡 WARNING
- [ ] Database seeding only for complex setup
- [ ] UI seeding only when testing create flows
- [ ] Static fixtures for reference data only
- [ ] Unique timestamps/counters prevent collisions

##### 🟢 BEST PRACTICE
- [ ] Fixtures for automatic cleanup
- [ ] Global teardown as safety net
- [ ] Test data factories with overrides
- [ ] Meaningful test data (not random strings)

---

### Test Data Common Patterns

#### Pattern: Test Data Builder

```typescript
class UserBuilder {
  private user: Partial<User> = {};

  withEmail(email: string): this {
    this.user.email = email;
    return this;
  }

  withRole(role: 'ADMIN' | 'CUSTOMER'): this {
    this.user.role = role;
    return this;
  }

  withName(name: string): this {
    this.user.name = name;
    return this;
  }

  build(): User {
    return TestDataFactory.createUser(this.user);
  }
}

// Usage
const admin = new UserBuilder()
  .withEmail('admin@example.com')
  .withRole('ADMIN')
  .build();
```

#### Pattern: Test Data Repository

```typescript
class TestDataRepository {
  private createdUsers: string[] = [];
  private createdProducts: string[] = [];

  async createUser(apiHelper: ApiHelper, user: Partial<User>): Promise<User> {
    const created = await apiHelper.createUser(user);
    this.createdUsers.push(created.id);
    return created;
  }

  async createProduct(apiHelper: ApiHelper, product: Partial<Product>): Promise<Product> {
    const created = await apiHelper.createProduct(product);
    this.createdProducts.push(created.id);
    return created;
  }

  async cleanup(apiHelper: ApiHelper): Promise<void> {
    for (const userId of this.createdUsers) {
      await apiHelper.deleteUser(userId);
    }
    for (const productId of this.createdProducts) {
      await apiHelper.deleteProduct(productId);
    }
    this.createdUsers = [];
    this.createdProducts = [];
  }
}
```

---

### Test Data Anti-Patterns

#### 🔴 WRONG - Shared Test Data

```typescript
// ❌ Don't use shared data across tests
const SHARED_USER = { email: 'shared@test.com', password: 'password' };

test('test 1', async ({ page }) => {
  await loginAs(page, SHARED_USER); // ❌ Breaks if another test modifies user
});

test('test 2', async ({ page }) => {
  await loginAs(page, SHARED_USER); // ❌ Race condition
});
```

#### ✅ CORRECT - Isolated Test Data

```typescript
// ✅ Each test creates its own user
test('test 1', async ({ page, request }) => {
  const user = TestDataFactory.createUser();
  await new ApiHelper(request).createUser(user);
  await loginAs(page, user);
});

test('test 2', async ({ page, request }) => {
  const user = TestDataFactory.createUser(); // Different user
  await new ApiHelper(request).createUser(user);
  await loginAs(page, user);
});
```

---

## Custom Fixtures

### Fixtures Overview

Fixtures are reusable setups that provide initialized objects to tests. Playwright's fixture system allows dependency injection, automatic cleanup, and shared state management.

**Benefits:**
- DRY: Define setup once, reuse across tests
- Automatic cleanup: Teardown happens even if test fails
- Dependency injection: Fixtures can depend on other fixtures
- Type-safe: Full TypeScript support

---

### Built-in Fixtures

#### 🔴 BLOCKING - Core Fixtures

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

### Creating Custom Fixtures

#### 🔴 BLOCKING - Creating Fixtures

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

### Fixture Lifecycle

#### Setup → Use → Teardown Pattern

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

### Fixture Dependencies

#### 🔴 BLOCKING - Fixtures Can Depend on Other Fixtures

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

### Worker-Scoped Fixtures

#### 🔴 BLOCKING - Share State Across Tests

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

#### Scope Comparison

| Scope | Runs | Cleanup | Use Case |
|-------|------|---------|----------|
| `test` (default) | Once per test | After each test | Isolated state (page, test data) |
| `worker` | Once per worker | After all tests in worker | Shared state (database, user accounts) |

---

### Authenticated Page Fixture

#### 🔴 BLOCKING - Two-Tier Authentication

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
      'password123'
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
    const token = await apiHelper.loginAsAdmin('admin@example.com', 'admin123');

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

### Test Data Fixtures

#### 🔴 BLOCKING - Factory-Based Test Data

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

### Database Fixtures with Testcontainers

#### 🔴 BLOCKING - Worker-Scoped Database

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

### Fixture Options

#### 🟢 BEST PRACTICE - Configurable Fixtures

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

### Fixtures Quick Reference

#### Fixtures Checklist

##### 🔴 BLOCKING
- [ ] Use fixtures for repeated setup
- [ ] Provide cleanup in fixture teardown
- [ ] Worker-scoped for expensive setup (database, containers)
- [ ] Test-scoped for isolated state (page objects, test data)
- [ ] Export custom `test` and `expect` from fixtures file

##### 🟡 WARNING
- [ ] Fixtures don't have side effects (idempotent)
- [ ] Dependencies declared explicitly
- [ ] Cleanup runs even if test fails
- [ ] Avoid complex fixture dependency chains

##### 🟢 BEST PRACTICE
- [ ] Type-safe fixture definitions
- [ ] Page objects as fixtures
- [ ] API helpers as fixtures
- [ ] Test data factories as fixtures
- [ ] Authenticated pages as fixtures

---

### Fixtures Common Patterns

#### Pattern: Fixture Composition

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

#### Pattern: Conditional Fixtures

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

### Fixtures Anti-Patterns

#### 🔴 WRONG - Shared Mutable State

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

#### ✅ CORRECT - Isolated State

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

#### 🔴 WRONG - Missing Cleanup

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

#### ✅ CORRECT - Always Cleanup

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
