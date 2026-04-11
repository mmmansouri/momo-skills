# Test Data Management

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

Test data management is critical for reliable, maintainable E2E tests. This guide covers strategies for creating, managing, and cleaning up test data.

**Principles:**
1. **Isolation**: Each test creates its own data
2. **Uniqueness**: Avoid data collisions between tests
3. **Cleanup**: Clean up after tests complete
4. **Speed**: Fast data creation (prefer API over UI)

---

## Test Data Strategies

### 🔴 BLOCKING - Choose the Right Strategy

| Strategy | Speed | Stability | Use Case |
|----------|-------|-----------|----------|
| **API seeding** | ⚡⚡⚡ | ✅✅✅ | Fastest, most reliable |
| **UI seeding** | ⚡ | ✅ | Testing create flows |
| **Database seeding** | ⚡⚡⚡ | ✅✅ | Complex data setup |
| **Static fixtures** | ⚡⚡⚡ | ✅ | Reference data |

---

## API-Based Test Data

### 🔴 BLOCKING - Preferred Method

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

## Factory Pattern

### 🔴 BLOCKING - Unique Data Per Test

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

## Database Seeding

### 🟡 WARNING - Use for Complex Setup

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

## Static Fixtures

### 🟢 BEST PRACTICE - Reference Data

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

## Cleanup Strategies

### 🔴 BLOCKING - Always Clean Up

#### 1. Test-Level Cleanup (Preferred)

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

#### 2. Fixture-Based Cleanup (Best)

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

#### 3. Global Cleanup (Last Resort)

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

## Buy Nature Examples

### Customer Registration Flow

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

### Checkout Flow with Multiple Products

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

### Admin Product Management

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

## Quick Reference

### Test Data Checklist

#### 🔴 BLOCKING
- [ ] Each test creates its own unique data
- [ ] Data created via API (fastest)
- [ ] Data cleaned up after test (even on failure)
- [ ] No hard-coded IDs or emails
- [ ] Factory pattern for consistent data generation

#### 🟡 WARNING
- [ ] Database seeding only for complex setup
- [ ] UI seeding only when testing create flows
- [ ] Static fixtures for reference data only
- [ ] Unique timestamps/counters prevent collisions

#### 🟢 BEST PRACTICE
- [ ] Fixtures for automatic cleanup
- [ ] Global teardown as safety net
- [ ] Test data factories with overrides
- [ ] Meaningful test data (not random strings)

---

## Common Patterns

### Pattern: Test Data Builder

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
  .withEmail('admin@buynature.com')
  .withRole('ADMIN')
  .build();
```

### Pattern: Test Data Repository

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

## Anti-Patterns

### 🔴 WRONG - Shared Test Data

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

### ✅ CORRECT - Isolated Test Data

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
