# Page Objects with Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

Page Object Model (POM) is a design pattern that encapsulates page structure and behavior, keeping tests focused on business logic rather than implementation details.

**Benefits:**
- Tests read like user stories
- Locators defined once, used everywhere
- Easy to maintain when UI changes
- Reusable across multiple tests

---

## When to Use Page Objects

### 🔴 BLOCKING
- **Use page objects for ANY page with more than 2 interactions** → Don't inline locators
- **Encapsulate ALL locators** → Never expose raw selectors to tests
- **No assertions in page objects** → Page objects = actions, tests = assertions

### 🟡 WARNING
- **Avoid page object overkill** → Simple one-off pages may not need a class
- **Don't create mega-objects** → Split large pages into components

---

## Class-Based Page Objects

### Basic Structure

```typescript
// pages/login.page.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  // Locators as readonly properties
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(private readonly page: Page) {
    this.emailInput = page.getByTestId('email-input');
    this.passwordInput = page.getByTestId('password-input');
    this.submitButton = page.getByRole('button', { name: 'Sign In' });
    this.errorMessage = page.getByTestId('error-message');
  }

  async goto(): Promise<void> {
    await this.page.goto('/login');
  }

  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async getErrorText(): Promise<string> {
    return await this.errorMessage.textContent() ?? '';
  }
}
```

### 🔴 BLOCKING - Navigation Methods

```typescript
// ✅ CORRECT - Return new page object after navigation
async loginAndGoToDashboard(email: string, password: string): Promise<DashboardPage> {
  await this.login(email, password);
  await this.page.waitForURL('/dashboard');
  return new DashboardPage(this.page);
}

// 🔴 WRONG - Don't return void for navigation
async loginAndGoToDashboard(email: string, password: string): Promise<void> {
  await this.login(email, password);
  // Test needs to manually create DashboardPage instance
}
```

### 🔴 BLOCKING - No Assertions

```typescript
// 🔴 WRONG - Assertions in page object
async login(email: string, password: string): Promise<void> {
  await this.emailInput.fill(email);
  await this.passwordInput.fill(password);
  await this.submitButton.click();
  await expect(this.page).toHaveURL('/dashboard'); // ❌ Don't assert here
}

// ✅ CORRECT - Only actions
async login(email: string, password: string): Promise<void> {
  await this.emailInput.fill(email);
  await this.passwordInput.fill(password);
  await this.submitButton.click();
  // Test will handle assertions
}
```

---

## Component-Based Page Objects

For complex pages, split into logical components.

```typescript
// pages/product-detail.page.ts
import { Page, Locator } from '@playwright/test';

class ProductImageGallery {
  readonly mainImage: Locator;
  readonly thumbnails: Locator;

  constructor(private readonly page: Page) {
    this.mainImage = page.getByTestId('main-product-image');
    this.thumbnails = page.getByTestId('thumbnail').locator('img');
  }

  async selectThumbnail(index: number): Promise<void> {
    await this.thumbnails.nth(index).click();
  }
}

class ProductInfo {
  readonly title: Locator;
  readonly price: Locator;
  readonly description: Locator;
  readonly addToCartButton: Locator;

  constructor(private readonly page: Page) {
    this.title = page.getByTestId('product-title');
    this.price = page.getByTestId('product-price');
    this.description = page.getByTestId('product-description');
    this.addToCartButton = page.getByRole('button', { name: 'Add to Cart' });
  }

  async addToCart(): Promise<void> {
    await this.addToCartButton.click();
  }
}

export class ProductDetailPage {
  readonly gallery: ProductImageGallery;
  readonly info: ProductInfo;

  constructor(private readonly page: Page) {
    this.gallery = new ProductImageGallery(page);
    this.info = new ProductInfo(page);
  }

  async goto(productId: string): Promise<void> {
    await this.page.goto(`/products/${productId}`);
  }
}
```

**Usage:**
```typescript
test('should add product to cart', async ({ page }) => {
  const productPage = new ProductDetailPage(page);
  await productPage.goto('product-123');

  await productPage.info.addToCart();
  await expect(page.getByText('Item added to cart')).toBeVisible();
});
```

---

## Function-Based Page Objects

Alternative to classes for simpler pages.

```typescript
// pages/search.page.ts
import { Page } from '@playwright/test';

export function createSearchPage(page: Page) {
  const searchInput = page.getByPlaceholder('Search products...');
  const searchButton = page.getByRole('button', { name: 'Search' });
  const resultItems = page.getByTestId('search-result-item');

  return {
    async goto() {
      await page.goto('/search');
    },

    async search(query: string) {
      await searchInput.fill(query);
      await searchButton.click();
    },

    async getResultCount() {
      return await resultItems.count();
    },

    resultItems,
  };
}
```

**Usage:**
```typescript
test('should search for products', async ({ page }) => {
  const searchPage = createSearchPage(page);
  await searchPage.goto();

  await searchPage.search('laptop');

  await expect(searchPage.resultItems).toHaveCount(10);
});
```

---

## Locator Strategies in Page Objects

### 🔴 BLOCKING - Preferred Order

| Priority | Method | Example | When to Use |
|----------|--------|---------|-------------|
| 1 | `getByTestId` | `page.getByTestId('submit-btn')` | Explicit test contract |
| 2 | `getByRole` | `page.getByRole('button', { name: 'Submit' })` | Accessible elements |
| 3 | `getByLabel` | `page.getByLabel('Email address')` | Form inputs |
| 4 | `getByPlaceholder` | `page.getByPlaceholder('Enter email')` | Inputs with placeholders |
| 5 | `getByText` | `page.getByText('Welcome')` | Static text content |

```typescript
export class SignupPage {
  // ✅ BEST - Test ID
  readonly emailInput = this.page.getByTestId('email-input');

  // ✅ GOOD - Role-based
  readonly submitButton = this.page.getByRole('button', { name: 'Create Account' });

  // ✅ GOOD - Label-based
  readonly passwordInput = this.page.getByLabel('Password');

  // 🟡 OK - Text-based (use for static content only)
  readonly welcomeText = this.page.getByText('Welcome to Buy Nature');

  // 🔴 WRONG - CSS classes
  readonly submitButton = this.page.locator('.btn-primary'); // ❌

  constructor(private readonly page: Page) {}
}
```

### Scoped Locators

```typescript
export class CartPage {
  private cartItems = this.page.getByTestId('cart-item');

  constructor(private readonly page: Page) {}

  // ✅ CORRECT - Scope within specific item
  async getItemPrice(productName: string): Promise<string> {
    const item = this.cartItems.filter({ hasText: productName });
    return await item.getByTestId('item-price').textContent() ?? '';
  }

  async removeItem(productName: string): Promise<void> {
    const item = this.cartItems.filter({ hasText: productName });
    await item.getByRole('button', { name: 'Remove' }).click();
  }
}
```

---

## Action Methods

### 🔴 BLOCKING - Method Design

```typescript
export class CheckoutPage {
  readonly shippingAddressInput = this.page.getByTestId('shipping-address');
  readonly paymentMethodSelect = this.page.getByTestId('payment-method');
  readonly placeOrderButton = this.page.getByRole('button', { name: 'Place Order' });

  constructor(private readonly page: Page) {}

  // ✅ CORRECT - Single responsibility
  async fillShippingAddress(address: string): Promise<void> {
    await this.shippingAddressInput.fill(address);
  }

  async selectPaymentMethod(method: 'credit-card' | 'paypal' | 'bank-transfer'): Promise<void> {
    await this.paymentMethodSelect.selectOption(method);
  }

  // ✅ CORRECT - Composite action for common workflows
  async completeCheckout(address: string, paymentMethod: string): Promise<void> {
    await this.fillShippingAddress(address);
    await this.selectPaymentMethod(paymentMethod as any);
    await this.placeOrderButton.click();
  }

  // 🔴 WRONG - Too many parameters
  async completeCheckout(
    address: string,
    city: string,
    zip: string,
    country: string,
    paymentMethod: string,
    cardNumber: string,
    cvv: string
  ): Promise<void> {
    // ❌ Use an object parameter instead
  }

  // ✅ CORRECT - Use object parameter
  async completeCheckout(data: CheckoutData): Promise<void> {
    await this.fillShippingAddress(data.address);
    await this.selectPaymentMethod(data.paymentMethod);
    // ...
  }
}

interface CheckoutData {
  address: string;
  paymentMethod: string;
}
```

---

## Buy Nature Integration: Two-Tier Authentication

### OAuth2 Client + User Login

```typescript
// pages/buy-nature/authenticated.page.ts
import { Page } from '@playwright/test';
import { LoginPage } from './login.page';

export class AuthenticatedPage {
  constructor(private readonly page: Page) {}

  /**
   * Two-tier authentication for Buy Nature:
   * 1. OAuth2 client authentication (automatic via interceptor)
   * 2. User login via UI
   */
  async loginAsCustomer(email: string, password: string): Promise<void> {
    const loginPage = new LoginPage(this.page);
    await loginPage.goto();

    // Client auth happens automatically via Angular HTTP interceptor
    // We just need to handle user login
    await loginPage.login(email, password);

    // Wait for successful authentication
    await this.page.waitForURL('/dashboard');
  }

  async loginAsAdmin(): Promise<void> {
    await this.loginAsCustomer('admin@buynature.com', 'admin123');
  }
}
```

### API-Based Authentication (Faster)

```typescript
// utils/auth-helper.ts
import { Page, APIRequestContext } from '@playwright/test';

export class AuthHelper {
  constructor(
    private readonly page: Page,
    private readonly request: APIRequestContext
  ) {}

  async loginViaAPI(email: string, password: string): Promise<string> {
    // Step 1: Client authentication
    const clientTokenResponse = await this.request.post('/oauth/token', {
      data: {
        grant_type: 'client_credentials',
        client_id: 'buynature-front',
        client_secret: 'client-secret-123',
      },
    });
    const clientToken = (await clientTokenResponse.json()).access_token;

    // Step 2: User authentication
    const userTokenResponse = await this.request.post('/oauth/token', {
      headers: {
        Authorization: `Bearer ${clientToken}`,
      },
      data: {
        grant_type: 'password',
        username: email,
        password: password,
      },
    });
    const userToken = (await userTokenResponse.json()).access_token;

    // Store token in browser
    await this.page.goto('/');
    await this.page.evaluate(token => {
      localStorage.setItem('access_token', token);
    }, userToken);

    return userToken;
  }
}
```

**Usage in Page Object:**
```typescript
export class DashboardPage {
  constructor(
    private readonly page: Page,
    private readonly authHelper?: AuthHelper
  ) {}

  async gotoAsAuthenticatedUser(email: string, password: string): Promise<void> {
    if (this.authHelper) {
      await this.authHelper.loginViaAPI(email, password);
    }
    await this.page.goto('/dashboard');
  }
}
```

---

## Quick Reference

### Page Object Checklist

#### 🔴 BLOCKING
- [ ] All locators defined as readonly properties
- [ ] Constructor accepts `Page` parameter
- [ ] No assertions in methods
- [ ] Navigation methods return new page objects
- [ ] Use `getByTestId` or `getByRole` for locators

#### 🟡 WARNING
- [ ] Methods have single responsibility
- [ ] Complex workflows use object parameters
- [ ] Components extracted for complex pages

#### 🟢 BEST PRACTICE
- [ ] Public methods return `Promise<void>` or `Promise<PageObject>`
- [ ] Private helper methods for repeated logic
- [ ] TypeScript interfaces for method parameters

---

## Common Patterns

### Pattern: Fluent Interface

```typescript
export class FilterPage {
  constructor(private readonly page: Page) {}

  async selectCategory(category: string): Promise<FilterPage> {
    await this.page.getByTestId(`category-${category}`).click();
    return this;
  }

  async setPriceRange(min: number, max: number): Promise<FilterPage> {
    await this.page.getByTestId('price-min').fill(min.toString());
    await this.page.getByTestId('price-max').fill(max.toString());
    return this;
  }

  async applyFilters(): Promise<void> {
    await this.page.getByRole('button', { name: 'Apply Filters' }).click();
  }
}

// Usage
await filterPage
  .selectCategory('electronics')
  .setPriceRange(100, 500)
  .applyFilters();
```

### Pattern: Dynamic Locators

```typescript
export class ProductListPage {
  constructor(private readonly page: Page) {}

  private getProductCard(productName: string): Locator {
    return this.page.getByTestId('product-card').filter({ hasText: productName });
  }

  async addToCart(productName: string): Promise<void> {
    const productCard = this.getProductCard(productName);
    await productCard.getByRole('button', { name: 'Add to Cart' }).click();
  }

  async getProductPrice(productName: string): Promise<string> {
    const productCard = this.getProductCard(productName);
    return await productCard.getByTestId('product-price').textContent() ?? '';
  }
}
```

---

## Anti-Patterns

### 🔴 WRONG - Mixing Concerns

```typescript
// ❌ Don't do this
export class LoginPage {
  async loginAndVerifyDashboard(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();

    // ❌ Assertion in page object
    await expect(this.page).toHaveURL('/dashboard');
    await expect(this.page.getByText('Welcome')).toBeVisible();
  }
}
```

### ✅ CORRECT - Separation of Concerns

```typescript
// ✅ Page object - actions only
export class LoginPage {
  async login(email: string, password: string): Promise<DashboardPage> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
    await this.page.waitForURL('/dashboard');
    return new DashboardPage(this.page);
  }
}

// ✅ Test - assertions
test('should login successfully', async ({ page }) => {
  const loginPage = new LoginPage(page);
  const dashboardPage = await loginPage.login('user@test.com', 'password');

  await expect(page).toHaveURL('/dashboard');
  await expect(dashboardPage.welcomeMessage).toBeVisible();
});
```
