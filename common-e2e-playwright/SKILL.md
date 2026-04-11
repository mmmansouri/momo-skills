---
name: common-e2e-playwright
description: >-
  End-to-end testing with Playwright. Use when: writing E2E tests, designing
  page objects, handling async operations, managing test data, CI/CD integration,
  or debugging flaky tests. Contains both pure E2E discipline and Playwright-specific guidance.
---

# E2E Testing with Playwright Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

# Part 1: E2E Testing Discipline (Tool-Agnostic)

## Core Principles

1. **Test User Journeys**: Focus on critical paths, not implementation details
2. **Isolation**: Each test independent, no shared state between tests
3. **Stability Over Speed**: Reliable tests > fast but flaky tests
4. **Readable Tests**: Tests as documentation of expected behavior
5. **Minimal E2E**: Only test what can't be tested at lower levels

---

## When Designing E2E Test Strategy

📚 **References:** [test-strategy.md](references/test-strategy.md)

### Test Pyramid Positioning

```
        /\
       /  \  E2E (5-10%)
      /----\  - Critical user journeys
     /      \  - Integration points
    /--------\  Integration (20-30%)
   /          \  - API contracts
  /------------\  - Component integration
 /              \  Unit (60-70%)
/________________\  - Business logic
```

### 🔴 BLOCKING
- **Only test critical user journeys** → Login, checkout, core features
- **Don't duplicate unit test coverage** → E2E for integration only
- **No implementation details** → Test what user sees/does

### What to E2E Test

| ✅ Test | ❌ Don't Test |
|---------|---------------|
| Login/logout flow | Form validation rules |
| Purchase checkout | Individual component rendering |
| Search and filter | API response formats |
| Multi-step wizards | CSS styling |
| Cross-browser issues | Business logic (unit test) |

---

## When Structuring E2E Tests

📚 **References:** [project-structure.md](references/project-structure.md)

### 🔴 BLOCKING

```
e2e/
├── tests/
│   ├── auth/
│   │   ├── login.spec.ts
│   │   └── logout.spec.ts
│   ├── checkout/
│   │   ├── cart.spec.ts
│   │   └── payment.spec.ts
│   └── catalog/
│       └── product-search.spec.ts
├── pages/              # Page Object Models
│   ├── login.page.ts
│   ├── catalog.page.ts
│   └── checkout.page.ts
├── fixtures/           # Test data & setup
│   ├── users.ts
│   └── products.ts
├── utils/              # Helpers
│   └── api-helpers.ts
└── playwright.config.ts
```

---

## When Writing Page Objects

📚 **References:** [page-objects.md](references/page-objects.md)

### 🔴 BLOCKING
- **Encapsulate locators** → Never expose raw selectors to tests
- **Return page objects from navigation** → Enable fluent chaining
- **No assertions in page objects** → Page objects = actions, tests = assertions

### Page Object Pattern

```
┌─────────────────────────────────────┐
│           Test Spec                 │
│  • Describes user journey           │
│  • Contains assertions              │
│  • Uses page objects                │
└──────────────┬──────────────────────┘
               │ uses
               ▼
┌─────────────────────────────────────┐
│         Page Object                 │
│  • Encapsulates page structure      │
│  • Provides actions (click, fill)   │
│  • Hides locator details            │
└──────────────┬──────────────────────┘
               │ interacts with
               ▼
┌─────────────────────────────────────┐
│         Application                 │
└─────────────────────────────────────┘
```

---

## When Selecting Elements

### Selector Priority (Best → Worst)

| Priority | Selector Type | Example | Why |
|----------|---------------|---------|-----|
| 1 | Test ID | `data-testid="submit-btn"` | Explicit, stable |
| 2 | Role + Name | `role=button[name="Submit"]` | Accessible, semantic |
| 3 | Label text | `label:has-text("Email")` | User-visible |
| 4 | Placeholder | `placeholder="Enter email"` | User-visible |
| 5 | CSS class | `.submit-button` | Fragile, avoid |
| 6 | XPath | `//div[@class="x"]/button` | Very fragile, never |

### 🔴 BLOCKING
- **Never use XPath** → Too fragile, hard to read
- **Never use CSS classes for styling** → They change
- **Use data-testid for complex cases** → Explicit test contract

---

## When Managing Test Data

📚 **References:** [test-data.md](references/test-data.md)

### 🔴 BLOCKING
- **Each test creates its own data** → No shared test data between tests
- **Clean up after tests** → Or use isolated environments
- **Never use production data** → Security + stability risks

### Test Data Strategies

| Strategy | When to Use | Pros | Cons |
|----------|-------------|------|------|
| API seeding | Fast setup needed | Fast, reliable | Requires API access |
| UI seeding | Testing create flows | Tests real flow | Slow |
| Database seeding | Complex data setup | Very fast | Tight DB coupling |
| Fixtures | Static reference data | Simple | Can get stale |

---

## When Handling Async Operations

### 🔴 BLOCKING
- **Never use fixed waits** → `sleep(5000)` is always wrong
- **Wait for specific conditions** → Element visible, network idle, text appears
- **Set reasonable timeouts** → Don't wait forever

### Wait Strategies

| Need | Strategy |
|------|----------|
| Element appears | Wait for selector |
| Text changes | Wait for text content |
| Navigation | Wait for URL/load state |
| API response | Wait for network request |
| Animation | Wait for stable position |

---

## When Dealing with Flaky Tests

📚 **References:** [flaky-tests.md](references/flaky-tests.md)

### Common Causes & Solutions

| Cause | Solution |
|-------|----------|
| Race conditions | Explicit waits for conditions |
| Shared state | Test isolation, fresh data |
| Animation timing | Wait for animation end |
| Network variability | Mock or wait for network |
| Time-dependent logic | Mock time/dates |
| Random data | Seed random generators |

### 🔴 BLOCKING
- **Never add retry loops to hide flakiness** → Fix root cause
- **Never increase timeouts blindly** → Find the real issue

---

# Part 2: Playwright-Specific Guidance

## When Setting Up Playwright

📚 **References:** [playwright-config.md](references/playwright-config.md)

### 🔴 BLOCKING - Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,  // Fail CI if .only left in
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['junit', { outputFile: 'results.xml' }]
  ],
  
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:4200',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],

  webServer: {
    command: 'npm run start',
    url: 'http://localhost:4200',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## When Writing Page Objects

📚 **References:** [page-objects-playwright.md](references/page-objects-playwright.md)

### 🔴 BLOCKING

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
    // ✅ Use data-testid or role-based locators
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

  // ✅ Return new page object for navigation
  async loginAndGoToDashboard(email: string, password: string): Promise<DashboardPage> {
    await this.login(email, password);
    await this.page.waitForURL('/dashboard');
    return new DashboardPage(this.page);
  }

  async getErrorText(): Promise<string> {
    return await this.errorMessage.textContent() ?? '';
  }
}
```

### 🟡 WARNING
- **Don't mix page object styles** → Consistent pattern across project
- **Keep page objects focused** → One page = one class

---

## When Writing Tests

📚 **References:** [test-patterns.md](references/test-patterns.md)

### 🔴 BLOCKING

```typescript
// tests/auth/login.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/login.page';
import { DashboardPage } from '../../pages/dashboard.page';
import { testUsers } from '../../fixtures/users';

test.describe('Login', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('should login with valid credentials', async ({ page }) => {
    // Arrange
    const user = testUsers.validCustomer;

    // Act
    const dashboardPage = await loginPage.loginAndGoToDashboard(
      user.email, 
      user.password
    );

    // Assert
    await expect(page).toHaveURL('/dashboard');
    await expect(dashboardPage.welcomeMessage).toContainText(user.name);
  });

  test('should show error for invalid credentials', async () => {
    // Act
    await loginPage.login('invalid@email.com', 'wrongpassword');

    // Assert
    await expect(loginPage.errorMessage).toBeVisible();
    await expect(loginPage.errorMessage).toContainText('Invalid credentials');
  });
});
```

---

## When Using Locators

📚 **References:** [locators-guide.md](references/locators-guide.md)

### 🔴 BLOCKING - Preferred Locators

```typescript
// ✅ BEST - Test ID (explicit contract)
page.getByTestId('submit-button')

// ✅ GOOD - Role-based (accessible)
page.getByRole('button', { name: 'Submit' })
page.getByRole('textbox', { name: 'Email' })
page.getByRole('link', { name: 'Home' })

// ✅ GOOD - Label-based
page.getByLabel('Email address')

// ✅ OK - Text-based (for static text)
page.getByText('Welcome back')

// 🔴 WRONG - CSS classes
page.locator('.btn-primary')

// 🔴 WRONG - Complex CSS
page.locator('div.container > form > button:nth-child(2)')

// 🔴 WRONG - XPath
page.locator('//button[@type="submit"]')
```

### Chaining Locators

```typescript
// ✅ CORRECT - Scope within component
const productCard = page.getByTestId('product-card').filter({ hasText: 'iPhone' });
await productCard.getByRole('button', { name: 'Add to Cart' }).click();

// ✅ CORRECT - Filter by child
const row = page.getByRole('row').filter({ 
  has: page.getByText('Order #123') 
});
await row.getByRole('button', { name: 'View' }).click();
```

---

## When Handling Waits

📚 **References:** [async-patterns.md](references/async-patterns.md)

### 🔴 BLOCKING

```typescript
// 🔴 WRONG - Fixed wait
await page.waitForTimeout(5000);

// ✅ CORRECT - Wait for element
await expect(page.getByTestId('result')).toBeVisible();

// ✅ CORRECT - Wait for navigation
await page.waitForURL('/dashboard');

// ✅ CORRECT - Wait for network
await page.waitForResponse(resp => 
  resp.url().includes('/api/products') && resp.status() === 200
);

// ✅ CORRECT - Wait for load state
await page.waitForLoadState('networkidle');

// ✅ CORRECT - Custom condition with polling
await expect(async () => {
  const count = await page.getByTestId('item').count();
  expect(count).toBeGreaterThan(0);
}).toPass({ timeout: 10000 });
```

---

## When Using Fixtures

📚 **References:** [fixtures-guide.md](references/fixtures-guide.md)

### 🔴 BLOCKING - Custom Fixtures

```typescript
// fixtures/index.ts
import { test as base } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { ApiHelper } from '../utils/api-helper';

type MyFixtures = {
  loginPage: LoginPage;
  apiHelper: ApiHelper;
  authenticatedPage: Page;
};

export const test = base.extend<MyFixtures>({
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await use(loginPage);
  },

  apiHelper: async ({ request }, use) => {
    const apiHelper = new ApiHelper(request);
    await use(apiHelper);
  },

  authenticatedPage: async ({ page, apiHelper }, use) => {
    // Setup: Login via API (faster than UI)
    const token = await apiHelper.login('test@example.com', 'password');
    await page.goto('/');
    await page.evaluate(t => localStorage.setItem('token', t), token);
    await page.reload();
    
    await use(page);
    
    // Cleanup
    await page.evaluate(() => localStorage.clear());
  },
});

export { expect } from '@playwright/test';
```

---

## When Mocking API

📚 **References:** [api-mocking.md](references/api-mocking.md)

### 🔴 BLOCKING

```typescript
test('should display products from API', async ({ page }) => {
  // Mock API response
  await page.route('**/api/products', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: '1', name: 'Test Product', price: 99.99 }
      ])
    });
  });

  await page.goto('/products');
  
  await expect(page.getByText('Test Product')).toBeVisible();
  await expect(page.getByText('$99.99')).toBeVisible();
});

test('should handle API errors gracefully', async ({ page }) => {
  await page.route('**/api/products', route => 
    route.fulfill({ status: 500 })
  );

  await page.goto('/products');
  
  await expect(page.getByText('Failed to load products')).toBeVisible();
});
```

---

## When Running in CI

📚 **References:** [ci-integration.md](references/ci-integration.md)

### 🔴 BLOCKING - GitHub Actions

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright browsers
        run: npx playwright install --with-deps
      
      - name: Run E2E tests
        run: npx playwright test
        env:
          BASE_URL: ${{ secrets.STAGING_URL }}
      
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7
```

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] No `waitForTimeout()` / fixed sleeps
- [ ] No XPath or fragile CSS selectors
- [ ] Page objects encapsulate all locators
- [ ] No assertions in page objects
- [ ] Each test is independent (no shared state)
- [ ] Test data created per test
- [ ] Meaningful test descriptions
- [ ] No `.only` left in code

### 🟡 WARNING
- [ ] Prefer `getByTestId` or `getByRole` over `locator()`
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)
- [ ] Page objects return new page objects on navigation
- [ ] Flaky tests are investigated, not retried

### 🟢 BEST PRACTICE
- [ ] Custom fixtures for common setup
- [ ] API mocking for edge cases
- [ ] Screenshots/videos on failure
- [ ] Parallel execution enabled
- [ ] Tests grouped by feature

---

---

## Buy Nature Integration

### Two-Tier Authentication in E2E Tests

Buy Nature requires **client token + user token** for authenticated requests:

```typescript
// fixtures/auth.fixture.ts
export async function authenticateCustomer(page: Page): Promise<AuthTokens> {
  // Step 1: Get client token
  const clientTokenResponse = await page.request.post('/api/auth/client/token', {
    data: {
      clientId: 'buynature-front',
      clientSecret: 'client-secret-123'
    }
  });
  const { access_token: clientToken } = await clientTokenResponse.json();

  // Step 2: Get user token (requires client token)
  const userTokenResponse = await page.request.post('/api/auth/user/login', {
    headers: { 'Authorization': `Bearer ${clientToken}` },
    data: {
      email: 'john.doe@example.com',
      password: 'Str0ngP@ssword123!'
    }
  });
  const { access_token: userToken } = await userTokenResponse.json();

  return { clientToken, userToken };
}
```

### Test Data Factories

```typescript
// utils/test-data-factories.ts
export function createTestItem(overrides: Partial<Item> = {}): Item {
  return {
    id: crypto.randomUUID(),
    name: `Test Item ${Date.now()}`,
    price: 10.99,
    categoryId: 'default-category',
    stock: 100,
    ...overrides
  };
}

export function createTestOrder(overrides: Partial<Order> = {}): Order {
  return {
    id: crypto.randomUUID(),
    customerId: crypto.randomUUID(),
    items: [createTestItem()],
    totalAmount: 10.99,
    status: 'PENDING',
    ...overrides
  };
}
```

### Page Objects

```typescript
// pages/LoginPage.ts
export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.page.getByLabel('Email').fill(email);
    await this.page.getByLabel('Password').fill(password);
    await this.page.getByRole('button', { name: 'Login' }).click();
    await this.page.waitForURL('/');
  }
}

// pages/CartPage.ts
export class CartPage {
  constructor(private page: Page) {}

  async addItemToCart(itemId: string) {
    await this.page.goto(`/items/${itemId}`);
    await this.page.getByRole('button', { name: 'Add to Cart' }).click();
    await expect(this.page.getByText('Item added')).toBeVisible();
  }

  async proceedToCheckout() {
    await this.page.goto('/cart');
    await this.page.getByRole('button', { name: 'Checkout' }).click();
    await this.page.waitForURL('/checkout');
  }
}
```

---

## Related Skills

- `common-frontend-angular` — Angular components to test
- `common-frontend-testing` — Unit vs E2E test strategy
- `common-architecture` — E2E test architecture
- `buy-nature-frontend-coding-guide` — Frontend E2E patterns
- `buy-nature-backoffice-coding-guide` — Backoffice E2E patterns
