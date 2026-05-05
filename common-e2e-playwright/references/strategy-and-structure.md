# E2E Strategy and Project Structure

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

## Table of Contents

- [E2E Test Strategy](#e2e-test-strategy)
  - [Strategy Overview](#strategy-overview)
  - [Testing Pyramid](#testing-pyramid)
  - [What to E2E Test](#what-to-e2e-test)
  - [Example Test Strategy](#example-test-strategy)
  - [Test Coverage Goals](#test-coverage-goals)
  - [Test Data Strategy](#test-data-strategy)
  - [When to Add E2E Tests](#when-to-add-e2e-tests)
  - [Maintenance Cost](#maintenance-cost)
  - [Smoke Tests vs Full Suite](#smoke-tests-vs-full-suite)
  - [Cross-Browser Testing](#cross-browser-testing)
  - [Strategy Quick Reference](#strategy-quick-reference)
  - [Strategy Common Patterns](#strategy-common-patterns)
  - [Strategy Anti-Patterns](#strategy-anti-patterns)
- [Project Structure](#project-structure)
  - [Structure Overview](#structure-overview)
  - [Recommended Structure](#recommended-structure)
  - [Tests Directory](#tests-directory)
  - [Pages Directory](#pages-directory)
  - [Fixtures Directory](#fixtures-directory)
  - [Utils Directory](#utils-directory)
  - [Config Directory](#config-directory)
  - [Example E2E Structure](#example-e2e-structure)
  - [File Organization Patterns](#file-organization-patterns)
  - [Structure Quick Reference](#structure-quick-reference)
  - [Structure Common Patterns](#structure-common-patterns)
  - [README Template](#readme-template)

---

## E2E Test Strategy

### Strategy Overview

A well-designed E2E test strategy balances test coverage with maintenance cost. E2E tests are expensive (slow, brittle), so focus on high-value critical paths.

---

### Testing Pyramid

#### 🔴 BLOCKING - Follow the Pyramid

```
        /\
       /  \  E2E (5-10%)
      /----\  - Critical user journeys
     /      \  - Happy paths only
    /--------\  Integration (20-30%)
   /          \  - API contracts
  /------------\  - Service integration
 /              \  Unit (60-70%)
/________________\  - Business logic
                    - Edge cases
```

**Distribution:**
- **Unit tests (60-70%)**: Fast, isolated, test business logic and edge cases
- **Integration tests (20-30%)**: Test API contracts, database access, service interactions
- **E2E tests (5-10%)**: Test critical user journeys through the UI

#### Why This Balance?

| Test Type | Speed | Stability | Maintenance | When to Use |
|-----------|-------|-----------|-------------|-------------|
| Unit | ⚡⚡⚡ | ✅✅✅ | ✅✅✅ | Business logic, edge cases |
| Integration | ⚡⚡ | ✅✅ | ✅✅ | API contracts, data access |
| E2E | ⚡ | ✅ | ❌ | Critical user flows only |

---

### What to E2E Test

#### 🔴 BLOCKING - Test Critical User Journeys

```
✅ DO E2E Test:
- Login/logout flow
- Purchase checkout
- User registration
- Password reset
- Search and filter products
- Add to cart and checkout
- Admin: Create/edit/delete resources
- Payment processing
- Order confirmation

❌ DON'T E2E Test:
- Form validation rules (unit test)
- Individual component rendering (unit test)
- API response formats (integration test)
- CSS styling (visual regression test)
- Business logic calculations (unit test)
- Error messages for every field (unit test)
```

#### Decision Matrix

| Scenario | E2E? | Alternative |
|----------|------|-------------|
| User can login | ✅ Yes | - |
| Invalid email shows error | ❌ No | Unit test form validator |
| User can add product to cart | ✅ Yes | - |
| Cart total calculates correctly | ❌ No | Unit test cart service |
| User can checkout with credit card | ✅ Yes | - |
| Stripe API validates card | ❌ No | Mock in E2E, integration test with Stripe test mode |
| Admin can create product | ✅ Yes | - |
| Product name validation | ❌ No | Unit test validator |

---

### Example Test Strategy

#### Frontend (Customer App)

##### 🔴 BLOCKING - Critical Paths

```typescript
// tests/critical-paths/
// 1. Authentication
tests/auth/login.spec.ts           // Login with valid credentials
tests/auth/logout.spec.ts          // Logout and session cleared

// 2. Product Discovery
tests/catalog/browse-products.spec.ts     // Browse product catalog
tests/catalog/search-products.spec.ts     // Search for products
tests/catalog/filter-products.spec.ts     // Filter by category/price

// 3. Shopping Flow
tests/cart/add-to-cart.spec.ts            // Add product to cart
tests/cart/update-cart.spec.ts            // Update quantities
tests/cart/remove-from-cart.spec.ts       // Remove items

// 4. Checkout (CRITICAL)
tests/checkout/checkout-flow.spec.ts      // Complete checkout with payment
tests/checkout/address-validation.spec.ts // Validate shipping address

// 5. Order Management
tests/orders/view-order-history.spec.ts   // View past orders
tests/orders/order-details.spec.ts        // View order details
```

**Total: ~12 critical E2E tests**

##### 🟡 WARNING - Secondary Paths

```typescript
// tests/secondary-paths/
tests/account/update-profile.spec.ts      // Update user profile
tests/account/change-password.spec.ts     // Change password
tests/wishlist/add-to-wishlist.spec.ts    // Add products to wishlist
```

**Total: ~5 secondary E2E tests**

#### Backoffice (Admin App)

##### 🔴 BLOCKING - Admin Critical Paths

```typescript
// tests/admin/
tests/admin/login.spec.ts                 // Admin login
tests/admin/product-management.spec.ts    // Create/edit/delete products
tests/admin/user-management.spec.ts       // View/disable users
tests/admin/order-management.spec.ts      // View/process orders
```

**Total: ~6 critical admin E2E tests**

---

### Test Coverage Goals

#### 🔴 BLOCKING - Coverage Targets

| Path Type | Coverage | Rationale |
|-----------|----------|-----------|
| Critical user journeys | 100% | Must work perfectly |
| Happy paths | 100% | Core functionality |
| Error scenarios | 20% | Sample only, unit test the rest |
| Edge cases | 0% | Unit/integration test |
| UI variations | 0% | Visual regression test |

**Example: Checkout Flow**

```
✅ E2E Test:
- Complete checkout with credit card (happy path)
- Complete checkout with PayPal (happy path)

❌ Unit Test Instead:
- Invalid credit card number
- Expired card
- Insufficient funds
- Invalid shipping address
- Missing required fields
```

---

### Test Data Strategy

#### 🔴 BLOCKING - Isolated Test Data

```typescript
// ✅ CORRECT - Each test creates its own data
test('should create order', async ({ page }) => {
  const user = await createTestUser();
  const product = await createTestProduct();

  await loginAs(page, user);
  await addToCart(page, product);
  await checkout(page);

  // Cleanup
  await deleteTestUser(user.id);
  await deleteTestProduct(product.id);
});

// 🔴 WRONG - Shared test data
const SHARED_USER = { email: 'test@test.com', password: 'password' };

test('should create order', async ({ page }) => {
  await loginAs(page, SHARED_USER); // ❌ Fails if another test modified user
});
```

#### Data Cleanup Strategies

| Strategy | Pros | Cons | Use When |
|----------|------|------|----------|
| API deletion | Fast, reliable | Requires API | Always prefer this |
| Database cleanup | Very fast | Tight coupling | Worker-scoped fixtures |
| UI deletion | Tests delete flow | Slow, fragile | Never for cleanup |
| Isolated DB per test | No conflicts | Slow setup | Complex integration tests |

---

### When to Add E2E Tests

#### 🔴 BLOCKING - New Feature Checklist

When adding a new feature:

1. **Ask: Is this a critical user journey?**
   - Yes → Add E2E test for happy path
   - No → Skip E2E, use unit/integration tests

2. **Ask: Does this span multiple systems?**
   - Yes (Frontend + Backend + Payment) → Add E2E test
   - No (Frontend only) → Component/unit test sufficient

3. **Ask: Is this high-risk?**
   - Yes (Payment, authentication, data loss) → Add E2E test
   - No → Skip E2E

**Example Decision Tree:**

```
Feature: Add product reviews
├─ Critical user journey? → No (nice-to-have feature)
├─ Spans multiple systems? → Yes (Frontend + Backend + Email)
├─ High-risk? → No (reviews are not critical)
└─ Decision: Skip E2E, add integration tests for API
```

```
Feature: Two-factor authentication
├─ Critical user journey? → Yes (authentication)
├─ Spans multiple systems? → Yes (Frontend + Backend + SMS)
├─ High-risk? → Yes (security)
└─ Decision: Add E2E test for 2FA flow
```

---

### Maintenance Cost

#### 🟡 WARNING - E2E Tests Are Expensive

**Cost factors:**
- **Slow execution**: 10-60 seconds per test
- **Flaky tests**: Network, timing, animation issues
- **Maintenance**: UI changes break tests frequently
- **Infrastructure**: Requires full stack running

**Mitigation strategies:**
1. **Minimize E2E tests**: Only critical paths
2. **Stable locators**: Use `data-testid` or semantic selectors
3. **Page objects**: Encapsulate UI changes
4. **Fast test data**: Use API, not UI
5. **Parallel execution**: Shard tests across workers

---

### Smoke Tests vs Full Suite

#### 🔴 BLOCKING - Separate Smoke Tests

**Smoke tests** (5-10 tests, 2-5 min):
- Run on every commit
- Test absolutely critical paths
- Fast feedback

**Full suite** (20-50 tests, 10-30 min):
- Run before merge to main
- Run nightly
- Comprehensive coverage

```typescript
// tests/smoke/checkout.smoke.spec.ts
test('@smoke should complete checkout', async ({ page }) => {
  // Absolute minimum: Login + Add to cart + Checkout
});

// tests/checkout/checkout-edge-cases.spec.ts
test('should handle payment failure gracefully', async ({ page }) => {
  // Full suite: Edge cases, error handling
});
```

**Run smoke tests:**
```bash
npx playwright test --grep @smoke
```

---

### Cross-Browser Testing

#### 🟡 WARNING - Selective Cross-Browser

```
✅ Test on all browsers:
- Critical paths (login, checkout)
- CSS-heavy features

❌ Don't test on all browsers:
- Admin CRUD operations (Chromium only)
- Secondary features
```

**Configuration:**
```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    // Run all tests on Chromium
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    // Run only smoke tests on Firefox/WebKit
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
      testMatch: '**/*.smoke.spec.ts',
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
      testMatch: '**/*.smoke.spec.ts',
    },
  ],
});
```

---

### Strategy Quick Reference

#### E2E Test Strategy Checklist

##### 🔴 BLOCKING
- [ ] E2E tests cover critical user journeys only
- [ ] Follow test pyramid (5-10% E2E)
- [ ] Each test creates isolated data
- [ ] Cleanup test data after tests
- [ ] Separate smoke tests from full suite

##### 🟡 WARNING
- [ ] E2E tests focus on happy paths
- [ ] Error cases tested in unit/integration tests
- [ ] Cross-browser only for critical paths
- [ ] Test data strategy defined (API/DB/UI)

##### 🟢 BEST PRACTICE
- [ ] Decision tree for when to add E2E
- [ ] Maintenance cost considered
- [ ] Page objects reduce brittleness
- [ ] Parallel execution configured
- [ ] Nightly full suite, PR smoke tests

---

### Strategy Common Patterns

#### Pattern: Risk-Based Prioritization

**High Priority (Must E2E Test):**
- Authentication/authorization
- Payment processing
- Data loss scenarios (delete, checkout)
- Multi-system integrations

**Medium Priority (Consider E2E):**
- Search and filtering
- User profile management
- Admin CRUD operations

**Low Priority (Skip E2E):**
- Static content pages
- UI-only features
- Form validation
- CSS/styling

#### Pattern: Smoke Test Selection

**Criteria for smoke tests:**
1. **Revenue impact**: Does it affect purchases?
2. **User frequency**: Used by majority of users?
3. **Failure impact**: Does failure block users completely?

**Example Smoke Tests (7 tests, ~3 min):**
```
1. Login as customer
2. Browse products
3. Add product to cart
4. Complete checkout with credit card
5. View order confirmation
6. Login as admin
7. View product list in backoffice
```

---

### Strategy Anti-Patterns

#### 🔴 WRONG - Testing Everything E2E

```typescript
// ❌ Don't test every validation rule with E2E
test('should show error when email is invalid', async ({ page }) => {
  await page.getByLabel('Email').fill('invalid');
  await expect(page.getByText('Invalid email')).toBeVisible();
});

test('should show error when password is too short', async ({ page }) => {
  await page.getByLabel('Password').fill('123');
  await expect(page.getByText('Password too short')).toBeVisible();
});
// ... 20 more validation tests ❌
```

#### ✅ CORRECT - One E2E, Many Unit Tests

```typescript
// ✅ Single E2E for happy path
test('should register new user', async ({ page }) => {
  await page.getByLabel('Email').fill('user@test.com');
  await page.getByLabel('Password').fill('ValidPass123!');
  await page.getByRole('button', { name: 'Sign Up' }).click();
  await expect(page).toHaveURL('/dashboard');
});

// ✅ Unit tests for validation
// validators/email.validator.spec.ts
test('should reject invalid email', () => {
  expect(validateEmail('invalid')).toBe(false);
  expect(validateEmail('test@test.com')).toBe(true);
});
```

#### 🔴 WRONG - Testing Implementation Details

```typescript
// ❌ Don't test internal state
test('should update cart state', async ({ page }) => {
  await page.evaluate(() => {
    return window.cartService.getItems().length; // ❌ Testing internals
  });
});
```

#### ✅ CORRECT - Test User-Visible Behavior

```typescript
// ✅ Test what user sees
test('should show 2 items in cart', async ({ page }) => {
  await addToCart(page, 'Product 1');
  await addToCart(page, 'Product 2');
  await expect(page.getByTestId('cart-count')).toHaveText('2');
});
```

---

## Project Structure

### Structure Overview

A well-organized E2E project makes tests easy to find, maintain, and extend. This guide shows the recommended structure for Playwright E2E projects.

---

### Recommended Structure

#### 🔴 BLOCKING - Standard Layout

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

### Tests Directory

#### 🔴 BLOCKING - Organize by Feature

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

#### Naming Conventions

| File Type | Pattern | Example |
|-----------|---------|---------|
| Test file | `<feature>.spec.ts` | `login.spec.ts` |
| Smoke test | `<feature>.smoke.spec.ts` | `checkout.smoke.spec.ts` |
| Setup file | `<feature>.setup.ts` | `auth.setup.ts` |

---

### Pages Directory

#### 🔴 BLOCKING - Page Object Models

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

### Fixtures Directory

#### 🔴 BLOCKING - Custom Fixtures

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

### Utils Directory

#### 🔴 BLOCKING - Helper Functions

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

### Config Directory

#### 🟡 WARNING - Environment-Specific Configs

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

### Example E2E Structure

#### Frontend E2E (`<your-app>-e2e-front`)

```
<your-app>-e2e-front/
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

#### Backoffice E2E (`<your-app>-e2e-backoffice`)

```
<your-app>-e2e-backoffice/
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

### File Organization Patterns

#### Pattern: Group by Feature

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

#### Pattern: Separate Smoke Tests

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

### Structure Quick Reference

#### Project Structure Checklist

##### 🔴 BLOCKING
- [ ] Tests organized by feature (not type)
- [ ] Page objects in `pages/` directory
- [ ] Custom fixtures in `fixtures/`
- [ ] Helper functions in `utils/`
- [ ] Consistent naming conventions

##### 🟡 WARNING
- [ ] Separate smoke tests directory or tags
- [ ] Environment-specific configs
- [ ] Base page for common functionality
- [ ] Components for reusable UI elements

##### 🟢 BEST PRACTICE
- [ ] README with setup instructions
- [ ] Global setup/teardown for shared state
- [ ] Test data factories for consistent data
- [ ] Docker Compose for integration mode
- [ ] Clear separation of concerns

---

### Structure Common Patterns

#### Pattern: Shared Components

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

#### Pattern: Test Data Factories

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

### README Template

```markdown
# E2E Tests

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
cd ../<your-app>-back
mvn spring-boot:run -Dspring-boot.run.profiles=local-e2e

# Terminal 3: Start frontend
cd ../<your-app>-front
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
