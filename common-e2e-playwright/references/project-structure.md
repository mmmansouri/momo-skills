# E2E Project Structure

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

A well-organized E2E project makes tests easy to find, maintain, and extend. This guide shows the recommended structure for Playwright E2E projects.

---

## Recommended Structure

### 🔴 BLOCKING - Standard Layout

```
e2e-project/
├── tests/                      # Test files
│   ├── auth/
│   │   ├── login.spec.ts
│   │   └── logout.spec.ts
│   ├── catalog/
│   │   ├── browse-products.spec.ts
│   │   └── search.spec.ts
│   ├── checkout/
│   │   └── checkout-flow.spec.ts
│   └── smoke/
│       └── critical-paths.smoke.spec.ts
├── pages/                      # Page Object Models
│   ├── login.page.ts
│   ├── catalog.page.ts
│   └── checkout.page.ts
├── fixtures/                   # Custom fixtures & test data
│   ├── index.ts               # Custom test fixture
│   ├── auth.fixture.ts        # Authentication fixtures
│   └── test-data.ts           # Test data factories
├── utils/                      # Helper functions
│   ├── api-helper.ts          # API utility for test data
│   ├── auth-helper.ts         # Authentication helpers
│   └── db-helper.ts           # Database utilities
├── config/                     # Environment-specific configs
│   ├── local.config.ts
│   ├── staging.config.ts
│   └── ci.config.ts
├── playwright.config.ts        # Main Playwright config
├── global-setup.ts            # Global setup (once before all tests)
├── global-teardown.ts         # Global teardown (once after all tests)
├── package.json
└── README.md
```

---

## Tests Directory

### 🔴 BLOCKING - Organize by Feature

```
tests/
├── auth/                      # Authentication tests
│   ├── login.spec.ts
│   ├── logout.spec.ts
│   ├── register.spec.ts
│   └── password-reset.spec.ts
├── catalog/                   # Product catalog tests
│   ├── browse-products.spec.ts
│   ├── search.spec.ts
│   ├── filter.spec.ts
│   └── product-details.spec.ts
├── cart/                      # Shopping cart tests
│   ├── add-to-cart.spec.ts
│   ├── update-cart.spec.ts
│   └── remove-from-cart.spec.ts
├── checkout/                  # Checkout flow tests
│   ├── checkout-flow.spec.ts
│   ├── payment.spec.ts
│   └── order-confirmation.spec.ts
├── admin/                     # Admin-specific tests
│   ├── product-management.spec.ts
│   └── user-management.spec.ts
└── smoke/                     # Smoke tests
    └── critical-paths.smoke.spec.ts
```

### Naming Conventions

| File Type | Pattern | Example |
|-----------|---------|---------|
| Test file | `<feature>.spec.ts` | `login.spec.ts` |
| Smoke test | `<feature>.smoke.spec.ts` | `checkout.smoke.spec.ts` |
| Setup file | `<feature>.setup.ts` | `auth.setup.ts` |

---

## Pages Directory

### 🔴 BLOCKING - Page Object Models

```
pages/
├── base.page.ts               # Base page with common methods
├── login.page.ts
├── catalog.page.ts
├── product-detail.page.ts
├── cart.page.ts
├── checkout.page.ts
├── admin/
│   ├── admin-base.page.ts
│   ├── product-list.page.ts
│   └── user-list.page.ts
└── components/                # Reusable components
    ├── header.component.ts
    ├── footer.component.ts
    └── modal.component.ts
```

**Example Base Page:**
```typescript
// pages/base.page.ts
import { Page } from '@playwright/test';

export class BasePage {
  constructor(protected readonly page: Page) {}

  async goto(path: string): Promise<void> {
    await this.page.goto(path);
  }

  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  async getTitle(): Promise<string> {
    return await this.page.title();
  }
}
```

**Example Page Object:**
```typescript
// pages/login.page.ts
import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

export class LoginPage extends BasePage {
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;

  constructor(page: Page) {
    super(page);
    this.emailInput = page.getByTestId('email-input');
    this.passwordInput = page.getByTestId('password-input');
    this.submitButton = page.getByRole('button', { name: 'Sign In' });
  }

  async goto(): Promise<void> {
    await super.goto('/login');
  }

  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}
```

---

## Fixtures Directory

### 🔴 BLOCKING - Custom Fixtures

```
fixtures/
├── index.ts                   # Export custom test and expect
├── auth.fixture.ts            # Authentication fixtures
├── test-data.fixture.ts       # Test data factories
└── database.fixture.ts        # Database fixtures
```

**Example Custom Fixture:**
```typescript
// fixtures/auth.fixture.ts
import { test as base } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { ApiHelper } from '../utils/api-helper';

type AuthFixtures = {
  loginPage: LoginPage;
  authenticatedPage: Page;
};

export const test = base.extend<AuthFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  authenticatedPage: async ({ page }, use) => {
    const apiHelper = new ApiHelper();
    const token = await apiHelper.login('test@test.com', 'password');
    await page.goto('/');
    await page.evaluate(t => localStorage.setItem('token', t), token);
    await use(page);
  },
});

export { expect } from '@playwright/test';
```

---

## Utils Directory

### 🔴 BLOCKING - Helper Functions

```
utils/
├── api-helper.ts              # API calls for test data
├── auth-helper.ts             # Authentication utilities
├── db-helper.ts               # Database utilities
├── test-data-factory.ts       # Generate test data
└── wait-helpers.ts            # Custom wait functions
```

**Example API Helper:**
```typescript
// utils/api-helper.ts
import { APIRequestContext } from '@playwright/test';

export class ApiHelper {
  constructor(private request: APIRequestContext) {}

  async createProduct(product: Partial<Product>): Promise<Product> {
    const response = await this.request.post('/api/products', {
      data: product,
    });
    return await response.json();
  }

  async deleteProduct(id: string): Promise<void> {
    await this.request.delete(`/api/products/${id}`);
  }

  async login(email: string, password: string): Promise<string> {
    const response = await this.request.post('/oauth/token', {
      data: {
        grant_type: 'password',
        username: email,
        password: password,
      },
    });
    const json = await response.json();
    return json.access_token;
  }
}
```

---

## Config Directory

### 🟡 WARNING - Environment-Specific Configs

```
config/
├── local.config.ts            # Local development
├── staging.config.ts          # Staging environment
├── production.config.ts       # Production (smoke tests only)
└── ci.config.ts               # CI-specific settings
```

**Example Environment Config:**
```typescript
// config/local.config.ts
import { PlaywrightTestConfig } from '@playwright/test';

const config: Partial<PlaywrightTestConfig> = {
  use: {
    baseURL: 'http://localhost:4200',
    trace: 'off',
    screenshot: 'off',
  },
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:4200',
    reuseExistingServer: true,
  },
};

export default config;
```

**Main config imports environment:**
```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';
import localConfig from './config/local.config';
import ciConfig from './config/ci.config';

const envConfig = process.env.CI ? ciConfig : localConfig;

export default defineConfig({
  ...envConfig,
  testDir: './tests',
  fullyParallel: true,
  // ... other settings
});
```

---

## Buy Nature E2E Structure

### Frontend E2E (buy-nature-e2e-front)

```
buy-nature-e2e-front/
├── tests/
│   ├── auth/
│   │   ├── login.spec.ts
│   │   └── logout.spec.ts
│   ├── catalog/
│   │   ├── browse-products.spec.ts
│   │   ├── search-products.spec.ts
│   │   └── filter-products.spec.ts
│   ├── cart/
│   │   ├── add-to-cart.spec.ts
│   │   └── update-cart.spec.ts
│   ├── checkout/
│   │   ├── checkout-flow.spec.ts
│   │   └── payment.spec.ts
│   └── smoke/
│       └── critical-paths.smoke.spec.ts
├── pages/
│   ├── login.page.ts
│   ├── catalog.page.ts
│   ├── product-detail.page.ts
│   ├── cart.page.ts
│   └── checkout.page.ts
├── fixtures/
│   ├── index.ts
│   ├── auth.fixture.ts
│   └── test-data.fixture.ts
├── utils/
│   ├── api-helper.ts
│   ├── auth-helper.ts
│   └── test-data-factory.ts
├── playwright.config.ts
├── docker-compose.yml         # Docker mode
├── package.json
└── README.md
```

### Backoffice E2E (buy-nature-e2e-backoffice)

```
buy-nature-e2e-backoffice/
├── tests/
│   ├── auth/
│   │   └── admin-login.spec.ts
│   ├── products/
│   │   ├── create-product.spec.ts
│   │   ├── edit-product.spec.ts
│   │   └── delete-product.spec.ts
│   ├── users/
│   │   ├── view-users.spec.ts
│   │   └── disable-user.spec.ts
│   └── orders/
│       └── view-orders.spec.ts
├── pages/
│   ├── admin-login.page.ts
│   ├── product-list.page.ts
│   ├── product-form.page.ts
│   └── user-list.page.ts
├── fixtures/
│   └── admin-auth.fixture.ts
├── utils/
│   └── admin-api-helper.ts
├── playwright.config.ts
└── README.md
```

---

## File Organization Patterns

### Pattern: Group by Feature

```
✅ GOOD - Feature-based
tests/
├── cart/
│   ├── add.spec.ts
│   ├── update.spec.ts
│   └── remove.spec.ts

❌ BAD - Type-based
tests/
├── unit/
├── integration/
└── e2e/
    └── all-cart-tests.spec.ts
```

### Pattern: Separate Smoke Tests

```
tests/
├── smoke/
│   └── critical-paths.smoke.spec.ts  # Tag with @smoke
├── catalog/
│   └── browse.spec.ts
└── checkout/
    └── checkout.spec.ts
```

**Run smoke tests:**
```bash
npx playwright test tests/smoke
# or
npx playwright test --grep @smoke
```

---

## Quick Reference

### Project Structure Checklist

#### 🔴 BLOCKING
- [ ] Tests organized by feature (not type)
- [ ] Page objects in `pages/` directory
- [ ] Custom fixtures in `fixtures/`
- [ ] Helper functions in `utils/`
- [ ] Consistent naming conventions

#### 🟡 WARNING
- [ ] Separate smoke tests directory or tags
- [ ] Environment-specific configs
- [ ] Base page for common functionality
- [ ] Components for reusable UI elements

#### 🟢 BEST PRACTICE
- [ ] README with setup instructions
- [ ] Global setup/teardown for shared state
- [ ] Test data factories for consistent data
- [ ] Docker Compose for integration mode
- [ ] Clear separation of concerns

---

## Common Patterns

### Pattern: Shared Components

```
pages/
├── components/
│   ├── header.component.ts
│   ├── footer.component.ts
│   └── product-card.component.ts
└── catalog.page.ts
```

**Example Component:**
```typescript
// pages/components/header.component.ts
import { Page, Locator } from '@playwright/test';

export class HeaderComponent {
  readonly cartIcon: Locator;
  readonly searchInput: Locator;

  constructor(private page: Page) {
    this.cartIcon = page.getByTestId('cart-icon');
    this.searchInput = page.getByPlaceholder('Search products...');
  }

  async openCart(): Promise<void> {
    await this.cartIcon.click();
  }

  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
  }
}
```

**Usage in Page Object:**
```typescript
import { HeaderComponent } from './components/header.component';

export class CatalogPage extends BasePage {
  readonly header: HeaderComponent;

  constructor(page: Page) {
    super(page);
    this.header = new HeaderComponent(page);
  }
}
```

### Pattern: Test Data Factories

```typescript
// utils/test-data-factory.ts
export class TestDataFactory {
  static createProduct(overrides?: Partial<Product>): Product {
    return {
      id: `product-${Date.now()}`,
      name: 'Test Product',
      price: 99.99,
      stock: 10,
      ...overrides,
    };
  }

  static createUser(overrides?: Partial<User>): User {
    return {
      email: `user-${Date.now()}@test.com`,
      password: 'Test123!',
      name: 'Test User',
      ...overrides,
    };
  }
}
```

---

## README Template

```markdown
# Buy Nature E2E Tests

## Setup

### Prerequisites
- Node.js 20+
- Docker (for Docker mode)

### Install
```bash
npm install
npx playwright install --with-deps
```

## Running Tests

### Local Mode
```bash
# Terminal 1: Start database
npm run db:up

# Terminal 2: Start backend
cd ../buy-nature-back
mvn spring-boot:run -Dspring-boot.run.profiles=local-e2e

# Terminal 3: Start frontend
cd ../buy-nature-front
npm run start:local-e2e

# Terminal 4: Run tests
npm run test:local
```

### Docker Mode
```bash
npm run e2e        # Start services, run tests, stop
npm run e2e:ci     # CI mode with proper exit codes
```

### Smoke Tests
```bash
npm run test:smoke
```

## Project Structure
- `tests/` - Test specifications
- `pages/` - Page Object Models
- `fixtures/` - Custom fixtures
- `utils/` - Helper functions

## Writing Tests
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
```
