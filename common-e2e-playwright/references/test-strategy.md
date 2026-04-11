# E2E Test Strategy

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

A well-designed E2E test strategy balances test coverage with maintenance cost. E2E tests are expensive (slow, brittle), so focus on high-value critical paths.

---

## Testing Pyramid

### 🔴 BLOCKING - Follow the Pyramid

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

### Why This Balance?

| Test Type | Speed | Stability | Maintenance | When to Use |
|-----------|-------|-----------|-------------|-------------|
| Unit | ⚡⚡⚡ | ✅✅✅ | ✅✅✅ | Business logic, edge cases |
| Integration | ⚡⚡ | ✅✅ | ✅✅ | API contracts, data access |
| E2E | ⚡ | ✅ | ❌ | Critical user flows only |

---

## What to E2E Test

### 🔴 BLOCKING - Test Critical User Journeys

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

### Decision Matrix

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

## Buy Nature Test Strategy

### Frontend (Customer App)

#### 🔴 BLOCKING - Critical Paths

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

#### 🟡 WARNING - Secondary Paths

```typescript
// tests/secondary-paths/
tests/account/update-profile.spec.ts      // Update user profile
tests/account/change-password.spec.ts     // Change password
tests/wishlist/add-to-wishlist.spec.ts    // Add products to wishlist
```

**Total: ~5 secondary E2E tests**

### Backoffice (Admin App)

#### 🔴 BLOCKING - Admin Critical Paths

```typescript
// tests/admin/
tests/admin/login.spec.ts                 // Admin login
tests/admin/product-management.spec.ts    // Create/edit/delete products
tests/admin/user-management.spec.ts       // View/disable users
tests/admin/order-management.spec.ts      // View/process orders
```

**Total: ~6 critical admin E2E tests**

---

## Test Coverage Goals

### 🔴 BLOCKING - Coverage Targets

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

## Test Data Strategy

### 🔴 BLOCKING - Isolated Test Data

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

### Data Cleanup Strategies

| Strategy | Pros | Cons | Use When |
|----------|------|------|----------|
| API deletion | Fast, reliable | Requires API | Always prefer this |
| Database cleanup | Very fast | Tight coupling | Worker-scoped fixtures |
| UI deletion | Tests delete flow | Slow, fragile | Never for cleanup |
| Isolated DB per test | No conflicts | Slow setup | Complex integration tests |

---

## When to Add E2E Tests

### 🔴 BLOCKING - New Feature Checklist

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

## Maintenance Cost

### 🟡 WARNING - E2E Tests Are Expensive

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

## Smoke Tests vs Full Suite

### 🔴 BLOCKING - Separate Smoke Tests

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

## Cross-Browser Testing

### 🟡 WARNING - Selective Cross-Browser

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

## Quick Reference

### E2E Test Strategy Checklist

#### 🔴 BLOCKING
- [ ] E2E tests cover critical user journeys only
- [ ] Follow test pyramid (5-10% E2E)
- [ ] Each test creates isolated data
- [ ] Cleanup test data after tests
- [ ] Separate smoke tests from full suite

#### 🟡 WARNING
- [ ] E2E tests focus on happy paths
- [ ] Error cases tested in unit/integration tests
- [ ] Cross-browser only for critical paths
- [ ] Test data strategy defined (API/DB/UI)

#### 🟢 BEST PRACTICE
- [ ] Decision tree for when to add E2E
- [ ] Maintenance cost considered
- [ ] Page objects reduce brittleness
- [ ] Parallel execution configured
- [ ] Nightly full suite, PR smoke tests

---

## Common Patterns

### Pattern: Risk-Based Prioritization

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

### Pattern: Smoke Test Selection

**Criteria for smoke tests:**
1. **Revenue impact**: Does it affect purchases?
2. **User frequency**: Used by majority of users?
3. **Failure impact**: Does failure block users completely?

**Buy Nature Smoke Tests (7 tests, ~3 min):**
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

## Anti-Patterns

### 🔴 WRONG - Testing Everything E2E

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

### ✅ CORRECT - One E2E, Many Unit Tests

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

### 🔴 WRONG - Testing Implementation Details

```typescript
// ❌ Don't test internal state
test('should update cart state', async ({ page }) => {
  await page.evaluate(() => {
    return window.cartService.getItems().length; // ❌ Testing internals
  });
});
```

### ✅ CORRECT - Test User-Visible Behavior

```typescript
// ✅ Test what user sees
test('should show 2 items in cart', async ({ page }) => {
  await addToCart(page, 'Product 1');
  await addToCart(page, 'Product 2');
  await expect(page.getByTestId('cart-count')).toHaveText('2');
});
```
