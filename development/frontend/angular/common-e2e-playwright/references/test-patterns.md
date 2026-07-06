# Test Patterns with Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Test foundations — Arrange–Act–Assert, isolation, `beforeEach`/`afterEach`,
descriptive naming, parameterized cases, `skip`/`only`/`fixme`, factories — are
owned by `common-developer` (§ When Writing Tests) and `SKILL.md`, and factories
live in [test-data.md](test-data.md). This reference keeps the two house **spec
skeletons** that anchor two-tier auth and the naming convention end-to-end.

## Table of Contents

- [Customer Login Flow](#customer-login-flow)
- [Admin Backoffice Flow](#admin-backoffice-flow)

---

## Customer Login Flow

`describe` per feature, `beforeEach` for shared navigation, `should …` names,
assertions in the spec (not the page object). The two-tier OAuth2 login succeeds
when the dashboard renders; session must survive a reload.

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
    const password = 'password123';

    // Act
    await loginPage.login(email, password);

    // Assert — two-tier auth succeeded
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome, John')).toBeVisible();
  });

  test('should handle invalid credentials', async () => {
    await loginPage.login('invalid@test.com', 'wrongpassword');

    await expect(loginPage.errorMessage).toBeVisible();
    await expect(loginPage.errorMessage).toContainText('Invalid credentials');
  });

  test('should persist session after page reload', async ({ page }) => {
    await loginPage.login('john.doe@example.com', 'password123');
    await expect(page).toHaveURL('/dashboard');

    await page.reload();

    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome, John')).toBeVisible();
  });
});
```

---

## Admin Backoffice Flow

Admin specs log in as an admin in `beforeEach`, then drive CRUD through page
objects. Seed prerequisite data via the API (`createProductViaAPI`), not the UI.

```typescript
// tests/admin/product-management.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/login.page';
import { ProductListPage } from '../../pages/admin/product-list.page';
import { createTestProduct } from '../../fixtures/factories';

test.describe('Product Management', () => {
  let productListPage: ProductListPage;

  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('admin@example.com', 'admin123');

    productListPage = new ProductListPage(page);
    await productListPage.goto();
  });

  test('should create new product', async ({ page }) => {
    // Arrange
    const product = createTestProduct({ name: 'New Eco-Friendly Product', price: 49.99 });

    // Act
    await productListPage.openCreateDialog();
    await productListPage.fillProductForm(product);
    await productListPage.submitForm();

    // Assert
    await expect(page.getByText('Product created successfully')).toBeVisible();
    await expect(productListPage.getProductRow(product.name)).toBeVisible();
  });

  test('should delete product', async ({ page }) => {
    // Arrange — seed via API, not the UI
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
