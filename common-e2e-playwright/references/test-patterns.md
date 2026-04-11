# Test Patterns with Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

Well-structured tests are readable, maintainable, and reliable. This guide covers proven patterns for writing Playwright E2E tests.

---

## AAA Pattern (Arrange-Act-Assert)

### 🔴 BLOCKING

Every test should follow the AAA structure:
1. **Arrange**: Set up test data and preconditions
2. **Act**: Perform the action being tested
3. **Assert**: Verify the expected outcome

```typescript
test('should add item to cart', async ({ page }) => {
  // Arrange - Set up initial state
  const productPage = new ProductPage(page);
  await productPage.goto('product-123');

  // Act - Perform action
  await productPage.addToCart();

  // Assert - Verify outcome
  await expect(page.getByText('Item added to cart')).toBeVisible();
  await expect(page.getByTestId('cart-count')).toHaveText('1');
});
```

### 🔴 WRONG - Mixed Concerns

```typescript
test('should add item to cart', async ({ page }) => {
  // ❌ No clear separation
  const productPage = new ProductPage(page);
  await productPage.goto('product-123');
  await expect(page.getByTestId('product-title')).toBeVisible();
  await productPage.addToCart();
  await expect(page.getByText('Item added')).toBeVisible();
  await page.goto('/cart');
  await expect(page.getByTestId('cart-item')).toHaveCount(1);
  // Hard to tell what's being tested
});
```

---

## Test Organization

### 🔴 BLOCKING - Describe Blocks

```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';

test.describe('Login', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('should login with valid credentials', async ({ page }) => {
    await loginPage.login('user@test.com', 'password123');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should show error with invalid credentials', async () => {
    await loginPage.login('invalid@test.com', 'wrong');
    await expect(loginPage.errorMessage).toBeVisible();
  });

  test('should disable submit button during login', async () => {
    const loginPromise = loginPage.login('user@test.com', 'password123');
    await expect(loginPage.submitButton).toBeDisabled();
    await loginPromise;
  });
});
```

### Nested Describe Blocks

```typescript
test.describe('Cart', () => {
  test.describe('Add items', () => {
    test('should add single item', async ({ page }) => {
      // ...
    });

    test('should add multiple items', async ({ page }) => {
      // ...
    });
  });

  test.describe('Remove items', () => {
    test.beforeEach(async ({ page }) => {
      // Add items before each remove test
      await addItemsToCart(page, 3);
    });

    test('should remove single item', async ({ page }) => {
      // ...
    });

    test('should clear all items', async ({ page }) => {
      // ...
    });
  });
});
```

---

## Test Isolation

### 🔴 BLOCKING - Each Test Independent

```typescript
// ✅ CORRECT - Each test creates its own data
test('should create order', async ({ page }) => {
  // Create user for this test
  const user = await createTestUser();

  // Login and create order
  await loginAsUser(page, user);
  await createOrder(page);

  await expect(page.getByText('Order created')).toBeVisible();
});

test('should cancel order', async ({ page }) => {
  // Create different user and order for this test
  const user = await createTestUser();
  const order = await createTestOrder(user);

  await loginAsUser(page, user);
  await cancelOrder(page, order.id);

  await expect(page.getByText('Order cancelled')).toBeVisible();
});

// 🔴 WRONG - Tests depend on each other
let globalOrderId: string;

test('should create order', async ({ page }) => {
  await createOrder(page);
  globalOrderId = await getOrderId(page);  // ❌ Shared state
});

test('should cancel order', async ({ page }) => {
  await cancelOrder(page, globalOrderId);  // ❌ Depends on previous test
});
```

---

## BeforeEach & AfterEach

### 🔴 BLOCKING - Shared Setup

```typescript
test.describe('Product catalog', () => {
  let catalogPage: CatalogPage;

  test.beforeEach(async ({ page }) => {
    // Runs before each test
    catalogPage = new CatalogPage(page);
    await catalogPage.goto();
  });

  test.afterEach(async ({ page }) => {
    // Runs after each test (even if test fails)
    await cleanupTestData();
  });

  test('should filter by category', async () => {
    await catalogPage.selectCategory('Electronics');
    await expect(catalogPage.products).toHaveCount(10);
  });

  test('should search products', async () => {
    await catalogPage.search('laptop');
    await expect(catalogPage.products.first()).toBeVisible();
  });
});
```

### BeforeAll & AfterAll

```typescript
test.describe('Admin panel', () => {
  let adminUser: User;

  test.beforeAll(async () => {
    // Runs once before all tests in this describe
    adminUser = await createAdminUser();
  });

  test.afterAll(async () => {
    // Runs once after all tests in this describe
    await deleteUser(adminUser.id);
  });

  test.beforeEach(async ({ page }) => {
    // Login before each test using shared admin user
    await loginAsUser(page, adminUser);
  });

  test('should view users', async ({ page }) => {
    await page.goto('/admin/users');
    await expect(page.getByRole('heading', { name: 'Users' })).toBeVisible();
  });

  test('should create user', async ({ page }) => {
    await page.goto('/admin/users');
    await createUser(page, 'newuser@test.com');
    await expect(page.getByText('User created')).toBeVisible();
  });
});
```

---

## Test Naming Conventions

### 🔴 BLOCKING - Descriptive Names

```typescript
// ✅ CORRECT - Clear, specific names
test('should display error when email is invalid', async ({ page }) => {});
test('should add product to cart and update cart count', async ({ page }) => {});
test('should redirect to login when accessing protected page', async ({ page }) => {});

// 🔴 WRONG - Vague names
test('test 1', async ({ page }) => {});
test('it works', async ({ page }) => {});
test('email', async ({ page }) => {});
```

### Pattern: "should [expected behavior] when [condition]"

```typescript
test.describe('Checkout', () => {
  test('should calculate total when items are in cart', async ({ page }) => {});
  test('should show error when payment fails', async ({ page }) => {});
  test('should clear cart when order is placed', async ({ page }) => {});
  test('should apply discount when coupon is valid', async ({ page }) => {});
});
```

---

## Test Data Management

### 🔴 BLOCKING - Factories

```typescript
// fixtures/factories.ts
let userCounter = 0;
let orderCounter = 0;

export function createTestUser(overrides?: Partial<User>): User {
  userCounter++;
  return {
    email: `user${userCounter}@test.com`,
    password: 'Test123!',
    name: `Test User ${userCounter}`,
    ...overrides,
  };
}

export function createTestProduct(overrides?: Partial<Product>): Product {
  return {
    id: `product-${Date.now()}`,
    name: 'Test Product',
    price: 99.99,
    stock: 10,
    ...overrides,
  };
}

export function createTestOrder(user: User, products: Product[]): Order {
  orderCounter++;
  return {
    id: `order-${orderCounter}`,
    userId: user.id,
    items: products.map(p => ({ productId: p.id, quantity: 1 })),
    total: products.reduce((sum, p) => sum + p.price, 0),
  };
}
```

**Usage:**
```typescript
test('should create order', async ({ page }) => {
  // Arrange - Create unique test data
  const user = createTestUser();
  const products = [
    createTestProduct({ name: 'Laptop', price: 999 }),
    createTestProduct({ name: 'Mouse', price: 25 }),
  ];

  // Act
  await loginAsUser(page, user);
  for (const product of products) {
    await addToCart(page, product.id);
  }
  await checkout(page);

  // Assert
  await expect(page.getByText('Order total: $1,024')).toBeVisible();
});
```

---

## Parameterized Tests

### 🔴 BLOCKING - Test Multiple Cases

```typescript
const testCases = [
  { email: 'invalid', password: 'test123', error: 'Invalid email format' },
  { email: 'test@test.com', password: '123', error: 'Password too short' },
  { email: 'test@test.com', password: '', error: 'Password required' },
];

for (const { email, password, error } of testCases) {
  test(`should show "${error}" for email="${email}" password="${password}"`, async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(email, password);

    await expect(page.getByText(error)).toBeVisible();
  });
}
```

### Using test.describe.configure

```typescript
const browsers = ['chromium', 'firefox', 'webkit'];

for (const browser of browsers) {
  test.describe(`Payment on ${browser}`, () => {
    test.use({ browserName: browser as any });

    test('should process credit card payment', async ({ page }) => {
      // Test runs on specified browser
    });
  });
}
```

---

## Conditional Tests

### Skip Tests

```typescript
// Skip specific test
test.skip('WIP: new feature not ready', async ({ page }) => {
  // ...
});

// Skip conditionally
test('should upload file', async ({ page, browserName }) => {
  test.skip(browserName === 'webkit', 'File upload broken in WebKit');
  // ...
});

// Skip entire suite
test.describe.skip('Legacy features', () => {
  test('old feature 1', async ({ page }) => {});
  test('old feature 2', async ({ page }) => {});
});
```

### Only Run Specific Tests

```typescript
// Run only this test (useful for debugging)
test.only('should debug this test', async ({ page }) => {
  // ...
});

// 🔴 BLOCKING - Never commit test.only
// Use forbidOnly: !!process.env.CI in config to prevent this
```

### Fixme (Skip with Intent)

```typescript
// Mark as known failure, will skip
test.fixme('should fix flaky test', async ({ page }) => {
  // Known to be flaky, skip until fixed
});
```

---

## Buy Nature Test Patterns

### Customer Login Flow

```typescript
// tests/auth/customer-login.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/login.page';

test.describe('Customer Login', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('should login with valid customer credentials', async ({ page }) => {
    // Arrange
    const email = 'john.doe@example.com';
    const password = 'Str0ngP@ssword123!';

    // Act
    await loginPage.login(email, password);

    // Assert - Two-tier auth successful
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome, John')).toBeVisible();
  });

  test('should handle invalid credentials', async () => {
    // Act
    await loginPage.login('invalid@test.com', 'wrongpassword');

    // Assert
    await expect(loginPage.errorMessage).toBeVisible();
    await expect(loginPage.errorMessage).toContainText('Invalid credentials');
  });

  test('should persist session after page reload', async ({ page }) => {
    // Arrange
    await loginPage.login('john.doe@example.com', 'Str0ngP@ssword123!');
    await expect(page).toHaveURL('/dashboard');

    // Act - Reload page
    await page.reload();

    // Assert - Still authenticated
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome, John')).toBeVisible();
  });
});
```

### Admin Backoffice Flow

```typescript
// tests/admin/product-management.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/login.page';
import { ProductListPage } from '../../pages/admin/product-list.page';
import { createTestProduct } from '../../fixtures/factories';

test.describe('Product Management', () => {
  let productListPage: ProductListPage;

  test.beforeEach(async ({ page }) => {
    // Login as admin
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('admin@buynature.com', 'admin123');

    productListPage = new ProductListPage(page);
    await productListPage.goto();
  });

  test('should create new product', async ({ page }) => {
    // Arrange
    const product = createTestProduct({
      name: 'New Eco-Friendly Product',
      price: 49.99,
    });

    // Act
    await productListPage.openCreateDialog();
    await productListPage.fillProductForm(product);
    await productListPage.submitForm();

    // Assert
    await expect(page.getByText('Product created successfully')).toBeVisible();
    await expect(productListPage.getProductRow(product.name)).toBeVisible();
  });

  test('should delete product', async ({ page }) => {
    // Arrange - Create product first
    const product = createTestProduct({ name: 'Product to Delete' });
    await createProductViaAPI(product);
    await page.reload();

    // Act
    await productListPage.deleteProduct(product.name);
    await productListPage.confirmDelete();

    // Assert
    await expect(page.getByText('Product deleted')).toBeVisible();
    await expect(productListPage.getProductRow(product.name)).not.toBeVisible();
  });
});
```

---

## Quick Reference

### Test Structure Checklist

#### 🔴 BLOCKING
- [ ] Each test follows AAA pattern (Arrange-Act-Assert)
- [ ] Tests are independent (no shared state)
- [ ] Test names describe expected behavior
- [ ] No `test.only` committed to repo
- [ ] Test data created per test (factories)

#### 🟡 WARNING
- [ ] BeforeEach/AfterEach used for shared setup
- [ ] Tests organized in describe blocks by feature
- [ ] Parameterized tests for multiple similar cases
- [ ] Conditional skips documented with reason

#### 🟢 BEST PRACTICE
- [ ] Comments explain "why" not "what"
- [ ] Complex setup extracted to helper functions
- [ ] Test data factories with unique values
- [ ] Cleanup in afterEach (even on failure)

---

## Common Patterns

### Pattern: Test Helper Functions

```typescript
// tests/helpers/cart-helpers.ts
import { Page } from '@playwright/test';

export async function addItemsToCart(page: Page, count: number): Promise<void> {
  const catalogPage = new CatalogPage(page);
  await catalogPage.goto();

  for (let i = 0; i < count; i++) {
    await catalogPage.products.nth(i).click();
    await page.getByRole('button', { name: 'Add to Cart' }).click();
    await page.goBack();
  }
}

export async function getCartItemCount(page: Page): Promise<number> {
  const cartCount = await page.getByTestId('cart-count').textContent();
  return parseInt(cartCount || '0', 10);
}
```

**Usage:**
```typescript
test('should add 3 items to cart', async ({ page }) => {
  await addItemsToCart(page, 3);
  const count = await getCartItemCount(page);
  expect(count).toBe(3);
});
```

### Pattern: Custom Matchers

```typescript
// tests/helpers/custom-matchers.ts
import { expect } from '@playwright/test';

expect.extend({
  async toHaveCartCount(page: Page, expected: number) {
    const actual = await getCartItemCount(page);
    const pass = actual === expected;
    return {
      message: () => `Expected cart count to be ${expected}, but was ${actual}`,
      pass,
    };
  },
});

// Usage
test('should update cart count', async ({ page }) => {
  await addItemsToCart(page, 5);
  await expect(page).toHaveCartCount(5);
});
```
