# Flaky Tests Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

Flaky tests are tests that sometimes pass and sometimes fail without code changes. They erode confidence in the test suite and waste developer time.

**Goal**: Zero tolerance for flaky tests. Fix them, don't hide them with retries.

---

## Common Causes

### 🔴 BLOCKING - Identify Root Cause

| Cause | Symptom | Solution |
|-------|---------|----------|
| **Race conditions** | Fails randomly when checking state | Explicit waits for specific conditions |
| **Shared state** | Fails when run with other tests | Test isolation, unique test data |
| **Animation timing** | Fails during element interaction | Wait for animation end or disable animations |
| **Network variability** | Fails when API is slow | Wait for network response, not fixed timeout |
| **Time-dependent logic** | Fails at specific times | Mock time/dates |
| **Random data** | Fails with certain random values | Seed random generators |
| **Insufficient waits** | Fails on slow machines | Wait for specific conditions, not arbitrary delays |

---

## Race Conditions

### 🔴 BLOCKING - Explicit Waits

```typescript
// 🔴 WRONG - Race condition
test('should show success message', async ({ page }) => {
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.getByText('Success')).toBeVisible(); // ❌ May fail if message appears slowly
});

// ✅ CORRECT - Wait for specific condition
test('should show success message', async ({ page }) => {
  await page.getByRole('button', { name: 'Submit' }).click();

  // Wait for API response first
  await page.waitForResponse(resp => resp.url().includes('/api/submit'));

  // Then check message
  await expect(page.getByText('Success')).toBeVisible();
});

// ✅ EVEN BETTER - Playwright auto-waits
test('should show success message', async ({ page }) => {
  await page.getByRole('button', { name: 'Submit' }).click();

  // Playwright waits for element to be visible automatically
  await expect(page.getByText('Success')).toBeVisible({ timeout: 10000 });
});
```

---

## Shared State

### 🔴 BLOCKING - Test Isolation

```typescript
// 🔴 WRONG - Tests share user account
let globalUser = { email: 'test@test.com', password: 'password' };

test('should update profile', async ({ page }) => {
  await loginAs(page, globalUser);
  await updateProfile(page, { name: 'New Name' });
  // ❌ Modifies shared state
});

test('should login', async ({ page }) => {
  await loginAs(page, globalUser);
  // ❌ Fails if previous test changed user
});

// ✅ CORRECT - Each test creates its own data
test('should update profile', async ({ page }) => {
  const user = await createTestUser(); // Unique user
  await loginAs(page, user);
  await updateProfile(page, { name: 'New Name' });
  await deleteTestUser(user.id);
});

test('should login', async ({ page }) => {
  const user = await createTestUser(); // Different unique user
  await loginAs(page, user);
  await deleteTestUser(user.id);
});
```

### Unique Test Data

```typescript
// ✅ CORRECT - Generate unique data per test
let userCounter = 0;

function createTestUser(): User {
  userCounter++;
  return {
    email: `user-${Date.now()}-${userCounter}@test.com`,
    password: 'Test123!',
    name: `Test User ${userCounter}`,
  };
}

test('should create order', async ({ page }) => {
  const user = createTestUser(); // Guaranteed unique
  await loginAs(page, user);
  await createOrder(page);
});
```

---

## Animation Timing

### 🔴 BLOCKING - Wait for Stable Element

```typescript
// 🔴 WRONG - Click during animation
test('should open menu', async ({ page }) => {
  await page.getByRole('button', { name: 'Menu' }).click();
  await page.getByRole('menuitem', { name: 'Settings' }).click(); // ❌ May fail if menu still animating
});

// ✅ CORRECT - Playwright waits for element to be stable
test('should open menu', async ({ page }) => {
  await page.getByRole('button', { name: 'Menu' }).click();

  // Playwright auto-waits for element to:
  // 1. Be visible
  // 2. Stop animating
  // 3. Receive events
  await page.getByRole('menuitem', { name: 'Settings' }).click();
});

// 🟢 BEST PRACTICE - Disable animations in test mode
// In global CSS for test environment:
// * { animation-duration: 0s !important; transition-duration: 0s !important; }
```

---

## Network Variability

### 🔴 BLOCKING - Wait for Network

```typescript
// 🔴 WRONG - Fixed timeout
test('should load products', async ({ page }) => {
  await page.goto('/products');
  await page.waitForTimeout(3000); // ❌ Arbitrary wait
  await expect(page.getByTestId('product-card')).toHaveCount(10);
});

// ✅ CORRECT - Wait for specific network response
test('should load products', async ({ page }) => {
  const responsePromise = page.waitForResponse('/api/products');
  await page.goto('/products');
  const response = await responsePromise;

  expect(response.status()).toBe(200);
  await expect(page.getByTestId('product-card')).toHaveCount(10);
});

// ✅ ALSO CORRECT - Wait for element to appear
test('should load products', async ({ page }) => {
  await page.goto('/products');

  // Wait for first product card to appear (indicates data loaded)
  await expect(page.getByTestId('product-card').first()).toBeVisible();
  await expect(page.getByTestId('product-card')).toHaveCount(10);
});
```

---

## Time-Dependent Logic

### 🔴 BLOCKING - Mock Time

```typescript
// 🔴 WRONG - Test depends on current time
test('should show greeting', async ({ page }) => {
  await page.goto('/dashboard');
  const hour = new Date().getHours();

  if (hour < 12) {
    await expect(page.getByText('Good morning')).toBeVisible();
  } else {
    await expect(page.getByText('Good afternoon')).toBeVisible();
  }
  // ❌ Fails when run at midnight
});

// ✅ CORRECT - Mock the clock
test('should show morning greeting', async ({ page }) => {
  // Set time to 9 AM
  await page.clock.setFixedTime(new Date('2024-01-01T09:00:00'));

  await page.goto('/dashboard');
  await expect(page.getByText('Good morning')).toBeVisible();
});

test('should show afternoon greeting', async ({ page }) => {
  // Set time to 2 PM
  await page.clock.setFixedTime(new Date('2024-01-01T14:00:00'));

  await page.goto('/dashboard');
  await expect(page.getByText('Good afternoon')).toBeVisible();
});
```

---

## Random Data

### 🔴 BLOCKING - Deterministic Data

```typescript
// 🔴 WRONG - Random data causes random failures
test('should sort products by price', async ({ page }) => {
  const products = Array.from({ length: 10 }, () => ({
    name: `Product ${Math.random()}`,
    price: Math.random() * 100, // ❌ Random price
  }));

  await seedProducts(products);
  await page.goto('/products?sort=price');

  // ❌ Assertion may fail if random prices are equal
  const firstPrice = await page.getByTestId('product-price').first().textContent();
  const lastPrice = await page.getByTestId('product-price').last().textContent();
  expect(parseFloat(firstPrice!)).toBeLessThan(parseFloat(lastPrice!));
});

// ✅ CORRECT - Deterministic data
test('should sort products by price', async ({ page }) => {
  const products = [
    { name: 'Product A', price: 10 },
    { name: 'Product B', price: 50 },
    { name: 'Product C', price: 100 },
  ];

  await seedProducts(products);
  await page.goto('/products?sort=price');

  await expect(page.getByTestId('product-price').first()).toHaveText('€10.00');
  await expect(page.getByTestId('product-price').last()).toHaveText('€100.00');
});
```

---

## Debugging Flaky Tests

### 🔴 BLOCKING - Diagnosis Tools

#### 1. Trace Viewer

```bash
# Run test with trace
npx playwright test --trace on

# Open trace viewer
npx playwright show-trace trace.zip
```

**Trace shows:**
- Network requests
- DOM snapshots
- Screenshots at each step
- Console logs
- Action timeline

#### 2. Screenshot on Failure

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
});
```

#### 3. Verbose Logging

```bash
# Run with debug logs
DEBUG=pw:* npx playwright test

# Or in test
test('debug test', async ({ page }) => {
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('requestfailed', req => console.log('FAILED:', req.url()));
});
```

#### 4. Slow Motion

```typescript
test('debug slow motion', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' });

  // Slow down actions by 100ms each
  await page.context().browser()?.newContext({ slowMo: 100 });
});
```

---

## Buy Nature Flaky Test Examples

### Example: Two-Tier Auth Timing

```typescript
// 🔴 FLAKY - Doesn't wait for both auth calls
test('should login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('john.doe@example.com', 'password');

  // ❌ May redirect before user token is stored
  await expect(page).toHaveURL('/dashboard');
});

// ✅ FIXED - Wait for both auth responses
test('should login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();

  const [clientTokenResp, userTokenResp] = await Promise.all([
    page.waitForResponse(resp => resp.url().includes('/oauth/token') &&
                                   resp.request().postDataJSON()?.grant_type === 'client_credentials'),
    page.waitForResponse(resp => resp.url().includes('/oauth/token') &&
                                   resp.request().postDataJSON()?.grant_type === 'password'),
    loginPage.login('john.doe@example.com', 'password'),
  ]);

  expect(clientTokenResp.status()).toBe(200);
  expect(userTokenResp.status()).toBe(200);
  await expect(page).toHaveURL('/dashboard');
});
```

### Example: Product Search Timing

```typescript
// 🔴 FLAKY - Search results may not be loaded
test('should search products', async ({ page }) => {
  await page.goto('/products');
  await page.getByPlaceholder('Search').fill('laptop');
  await page.getByPlaceholder('Search').press('Enter');

  // ❌ Assertion runs before search completes
  await expect(page.getByTestId('product-card')).toHaveCount(5);
});

// ✅ FIXED - Wait for search API response
test('should search products', async ({ page }) => {
  await page.goto('/products');

  const searchResponsePromise = page.waitForResponse(resp =>
    resp.url().includes('/api/products') &&
    resp.url().includes('search=laptop')
  );

  await page.getByPlaceholder('Search').fill('laptop');
  await page.getByPlaceholder('Search').press('Enter');

  await searchResponsePromise;
  await expect(page.getByTestId('product-card')).toHaveCount(5);
});
```

---

## Retry Strategy

### 🔴 BLOCKING - Fix, Don't Hide

```typescript
// 🔴 WRONG - Retry to hide flakiness
test('flaky test', async ({ page }) => {
  test.setTimeout(30000);
  let attempts = 0;

  while (attempts < 3) {
    try {
      await page.goto('/products');
      await expect(page.getByText('Products')).toBeVisible();
      break;
    } catch {
      attempts++;
      // ❌ Hiding flakiness with retries
    }
  }
});

// ✅ CORRECT - Fix root cause
test('fixed test', async ({ page }) => {
  await page.goto('/products');

  // Wait for page to be ready
  await page.waitForLoadState('networkidle');

  await expect(page.getByText('Products')).toBeVisible();
});
```

### When Retries Are Acceptable

```typescript
// 🟢 OK - Retry for known external flakiness
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 2 : 0, // Only retry in CI
});

// But always investigate and fix if possible!
```

---

## Quick Reference

### Flaky Test Checklist

#### 🔴 BLOCKING
- [ ] No fixed timeouts (`waitForTimeout`)
- [ ] Wait for specific conditions (URL, element, network)
- [ ] Each test creates isolated data
- [ ] No shared mutable state between tests
- [ ] Time/dates mocked if used in logic
- [ ] Random data is seeded or deterministic

#### 🟡 WARNING
- [ ] Animations don't interfere (wait or disable)
- [ ] Network responses awaited explicitly
- [ ] Elements stable before interaction
- [ ] Retry strategy documented if used

#### 🟢 BEST PRACTICE
- [ ] Trace viewer used for debugging
- [ ] Screenshots/videos on failure
- [ ] Verbose logging when needed
- [ ] Root cause identified and fixed
- [ ] CI retries kept to minimum (0-2)

---

## Common Patterns

### Pattern: Polling Until Stable

```typescript
// Wait for element count to stabilize
await expect
  .poll(async () => {
    return await page.getByTestId('product-card').count();
  })
  .toBe(10);

// Wait for value to stop changing
await expect
  .poll(async () => {
    return await page.getByTestId('total-price').textContent();
  }, { timeout: 5000 })
  .toBe('€99.99');
```

### Pattern: Eventually Consistent

```typescript
// For eventually consistent systems
await expect(async () => {
  await page.reload();
  const count = await page.getByTestId('notification').count();
  expect(count).toBe(1);
}).toPass({ timeout: 10000, intervals: [1000, 2000, 3000] });
```

---

## Anti-Patterns

### 🔴 WRONG - Masking Flakiness

```typescript
// ❌ Don't add arbitrary delays
await page.waitForTimeout(5000);

// ❌ Don't retry without understanding why
test.retries(10);

// ❌ Don't skip flaky tests
test.skip('flaky test', async ({ page }) => {});
```

### ✅ CORRECT - Fix Root Cause

```typescript
// ✅ Wait for specific condition
await expect(page.getByText('Loaded')).toBeVisible();

// ✅ Investigate and fix
// 1. Enable trace viewer
// 2. Reproduce locally
// 3. Identify root cause
// 4. Fix properly
```

---

## Flakiness Metrics

Track flakiness over time:

```bash
# Run test 10 times to detect flakiness
for i in {1..10}; do npx playwright test tests/checkout.spec.ts; done

# If any runs fail, investigate immediately
```

**CI Integration:**
```yaml
# GitHub Actions: Fail if test is flaky
- name: Run tests multiple times
  run: |
    for i in {1..3}; do
      npx playwright test || exit 1
    done
```
