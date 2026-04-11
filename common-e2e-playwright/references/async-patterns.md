# Async Patterns in Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

Playwright has built-in auto-waiting for most actions, but understanding async patterns is critical for writing stable, non-flaky tests.

**Key principle**: Wait for specific conditions, never use arbitrary timeouts.

---

## Auto-Waiting (Playwright's Default)

### 🟢 BEST PRACTICE - Playwright Waits Automatically

Playwright auto-waits before performing most actions:

```typescript
// ✅ No explicit wait needed - Playwright waits automatically for:
// 1. Element to be attached to DOM
// 2. Element to be visible
// 3. Element to be stable (not animating)
// 4. Element to receive events (not obscured)
// 5. Element to be enabled
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByLabel('Email').fill('test@example.com');
await page.getByRole('checkbox').check();
```

**Auto-waiting applies to:**
- `click()`, `dblclick()`, `hover()`
- `fill()`, `type()`, `selectOption()`
- `check()`, `uncheck()`
- `setInputFiles()`

### What Playwright Checks Before Action

```
┌─────────────────────────────────────┐
│    Auto-Wait Checks (in order)      │
├─────────────────────────────────────┤
│ 1. Element exists in DOM            │
│ 2. Element is visible               │
│ 3. Element is stable (no animation) │
│ 4. Element receives events          │
│ 5. Element is enabled (if needed)   │
└─────────────────────────────────────┘
```

---

## Fixed Waits (Never Use)

### 🔴 BLOCKING - Don't Use waitForTimeout

```typescript
// 🔴 WRONG - Fixed wait (brittle, slow)
await page.waitForTimeout(5000); // ❌ NEVER DO THIS
await page.getByRole('button', { name: 'Submit' }).click();

// ✅ CORRECT - Wait for specific condition
await expect(page.getByRole('button', { name: 'Submit' })).toBeVisible();
await page.getByRole('button', { name: 'Submit' }).click();

// ✅ EVEN BETTER - Playwright auto-waits
await page.getByRole('button', { name: 'Submit' }).click();
```

**Why fixed waits are bad:**
- Slow: Always wait full duration even if element appears immediately
- Brittle: Breaks if operation takes slightly longer
- Masks problems: Hides real issues with app performance

---

## Waiting for Navigation

### 🔴 BLOCKING - waitForURL

```typescript
// ✅ CORRECT - Wait for URL to change
await page.getByRole('button', { name: 'Sign In' }).click();
await page.waitForURL('/dashboard');

// ✅ CORRECT - Wait for URL pattern
await page.waitForURL(/\/products\/\d+/);

// ✅ CORRECT - Wait for URL with function
await page.waitForURL(url => url.pathname === '/checkout');

// ✅ CORRECT - With timeout
await page.waitForURL('/dashboard', { timeout: 10000 });
```

### 🟡 WARNING - waitForLoadState

```typescript
// Wait for page to finish loading
await page.goto('/products');
await page.waitForLoadState('load'); // DOMContentLoaded + load events

// Wait for network to be idle
await page.waitForLoadState('networkidle'); // No network requests for 500ms

// Wait for DOM ready
await page.waitForLoadState('domcontentloaded');
```

**Load States:**

| State | When Complete | Use Case |
|-------|---------------|----------|
| `load` | Page load event fired | Default, usually sufficient |
| `domcontentloaded` | DOM parsed | Very fast, use for static pages |
| `networkidle` | No network for 500ms | SPA with async data loading |

### 🟡 WARNING
- **Avoid `networkidle` if possible** → Can be slow and flaky
- **Prefer waiting for specific elements** → More precise than load state

---

## Waiting for Elements

### 🔴 BLOCKING - Use expect() Assertions

```typescript
// ✅ CORRECT - Wait for element to be visible
await expect(page.getByTestId('result')).toBeVisible();

// ✅ CORRECT - Wait for element to have text
await expect(page.getByTestId('message')).toHaveText('Success');

// ✅ CORRECT - Wait for element to contain text
await expect(page.getByTestId('message')).toContainText('Success');

// ✅ CORRECT - Wait for element count
await expect(page.getByTestId('product-card')).toHaveCount(10);

// ✅ CORRECT - Wait for element to be hidden
await expect(page.getByTestId('loading-spinner')).toBeHidden();

// ✅ CORRECT - Wait for element to be enabled
await expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled();
```

### Assertion Matchers for Waiting

| Matcher | Waits For |
|---------|-----------|
| `toBeVisible()` | Element visible |
| `toBeHidden()` | Element hidden |
| `toHaveText()` | Exact text match |
| `toContainText()` | Partial text match |
| `toHaveValue()` | Input value |
| `toBeEnabled()` | Element enabled |
| `toBeDisabled()` | Element disabled |
| `toBeChecked()` | Checkbox/radio checked |
| `toHaveCount()` | Specific number of elements |
| `toHaveAttribute()` | Attribute with value |

---

## Waiting for Network Requests

### 🔴 BLOCKING - waitForResponse

```typescript
// ✅ CORRECT - Wait for specific API response
const responsePromise = page.waitForResponse('/api/products');
await page.getByRole('button', { name: 'Load Products' }).click();
const response = await responsePromise;
expect(response.status()).toBe(200);

// ✅ CORRECT - Wait for response matching condition
const responsePromise = page.waitForResponse(
  response => response.url().includes('/api/products') && response.status() === 200
);
await page.getByRole('button', { name: 'Load Products' }).click();
await responsePromise;

// ✅ CORRECT - Multiple criteria
const responsePromise = page.waitForResponse(
  response =>
    response.url().endsWith('/checkout') &&
    response.request().method() === 'POST' &&
    response.status() === 201
);
await page.getByRole('button', { name: 'Complete Order' }).click();
await responsePromise;
```

### waitForRequest

```typescript
// Wait for specific request
const requestPromise = page.waitForRequest('/api/products');
await page.goto('/products');
const request = await requestPromise;
expect(request.method()).toBe('GET');

// Wait for request with condition
const requestPromise = page.waitForRequest(
  request => request.url().includes('/search') && request.method() === 'GET'
);
await page.getByPlaceholder('Search').fill('laptop');
await requestPromise;
```

---

## Custom Wait Conditions

### 🔴 BLOCKING - expect.poll() for Complex Conditions

```typescript
// ✅ CORRECT - Poll for custom condition
await expect
  .poll(async () => {
    const items = await page.getByTestId('cart-item').count();
    return items;
  })
  .toBe(3);

// ✅ CORRECT - Poll with custom timeout
await expect
  .poll(
    async () => {
      const text = await page.getByTestId('status').textContent();
      return text;
    },
    { timeout: 10000 }
  )
  .toBe('Completed');

// ✅ CORRECT - Poll for complex validation
await expect
  .poll(async () => {
    const prices = await page.getByTestId('product-price').allTextContents();
    const total = prices
      .map(p => parseFloat(p.replace('€', '')))
      .reduce((sum, p) => sum + p, 0);
    return total;
  })
  .toBeGreaterThan(100);
```

### expect.toPass() for Flaky Conditions

```typescript
// ✅ CORRECT - Retry until assertion passes
await expect(async () => {
  const count = await page.getByTestId('item').count();
  expect(count).toBeGreaterThan(0);
}).toPass({ timeout: 5000 });

// ✅ CORRECT - Useful for eventually consistent data
await expect(async () => {
  const balance = await page.getByTestId('account-balance').textContent();
  expect(balance).toBe('€1,000.00');
}).toPass({ timeout: 10000, intervals: [1000, 2000, 3000] });
```

---

## Timeouts

### 🔴 BLOCKING - Timeout Hierarchy

```typescript
// Test-level timeout (default: 30s)
test('should complete checkout', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds for this test
  await checkout(page);
});

// Assertion-level timeout
await expect(page.getByText('Success')).toBeVisible({ timeout: 10000 });

// Action-level timeout
await page.getByRole('button', { name: 'Submit' }).click({ timeout: 5000 });

// Navigation timeout
await page.goto('/products', { timeout: 15000 });
```

**Timeout Levels:**

```
Test Timeout (30s default)
  └─> Navigation Timeout (from config)
  └─> Action Timeout (from config)
  └─> Assertion Timeout (from config)
```

### 🟡 WARNING
- **Don't increase timeouts to hide problems** → Fix the root cause
- **Use longer timeouts in CI if needed** → CI may be slower
- **Keep timeouts reasonable** → Long timeouts slow down failure detection

---

## Handling Animations

### 🔴 BLOCKING - Wait for Animation End

```typescript
// ✅ CORRECT - Playwright waits for element to be stable
await page.getByRole('button', { name: 'Menu' }).click();
await page.getByRole('menuitem', { name: 'Settings' }).click(); // Waits for animation

// ✅ CORRECT - Explicitly wait for animation
await page.getByTestId('modal').waitFor({ state: 'visible' });
// Playwright ensures modal is stable before continuing

// 🟡 OK - Disable animations in test mode (faster, more stable)
// Add to global CSS in test environment:
// * { animation-duration: 0s !important; }
```

---

## Waiting for Multiple Conditions

### 🔴 BLOCKING - Promise.all for Parallel Waits

```typescript
// ✅ CORRECT - Wait for multiple conditions in parallel
await Promise.all([
  expect(page.getByText('Success')).toBeVisible(),
  expect(page.getByTestId('cart-count')).toHaveText('1'),
  page.waitForURL('/cart'),
]);

// ✅ CORRECT - Wait for multiple API calls
const [productsResponse, categoriesResponse] = await Promise.all([
  page.waitForResponse('/api/products'),
  page.waitForResponse('/api/categories'),
  page.goto('/catalog'),
]);

expect(productsResponse.status()).toBe(200);
expect(categoriesResponse.status()).toBe(200);
```

---

## Buy Nature Async Patterns

### Two-Tier Authentication Flow

```typescript
test('should authenticate and load dashboard', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();

  // Act - Login triggers two API calls:
  // 1. Client auth (OAuth2 client credentials)
  // 2. User auth (OAuth2 password grant)
  const [clientTokenResponse, userTokenResponse] = await Promise.all([
    page.waitForResponse(resp => resp.url().includes('/oauth/token') && resp.request().postDataJSON()?.grant_type === 'client_credentials'),
    page.waitForResponse(resp => resp.url().includes('/oauth/token') && resp.request().postDataJSON()?.grant_type === 'password'),
    loginPage.login('john.doe@example.com', 'Str0ngP@ssword123!'),
  ]);

  // Assert both auth calls succeeded
  expect(clientTokenResponse.status()).toBe(200);
  expect(userTokenResponse.status()).toBe(200);

  // Wait for redirect to dashboard
  await page.waitForURL('/dashboard');
  await expect(page.getByText('Welcome, John')).toBeVisible();
});
```

### Product Catalog with Lazy Loading

```typescript
test('should load products on scroll', async ({ page }) => {
  await page.goto('/products');

  // Wait for initial products to load
  const firstLoadResponse = page.waitForResponse('/api/products?page=0');
  await expect(page.getByTestId('product-card')).toHaveCount(20);
  await firstLoadResponse;

  // Scroll to trigger lazy load
  const secondLoadResponse = page.waitForResponse('/api/products?page=1');
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await secondLoadResponse;

  // Wait for additional products to appear
  await expect(page.getByTestId('product-card')).toHaveCount(40);
});
```

### Checkout Flow with Payment Processing

```typescript
test('should process payment', async ({ page }) => {
  const checkoutPage = new CheckoutPage(page);
  await checkoutPage.goto();

  // Fill checkout form
  await checkoutPage.fillShippingAddress('123 Main St');
  await checkoutPage.selectPaymentMethod('credit-card');
  await checkoutPage.fillCreditCard('4242 4242 4242 4242', '12/25', '123');

  // Wait for multiple API calls during checkout:
  // 1. Validate address
  // 2. Process payment
  // 3. Create order
  const [addressResponse, paymentResponse, orderResponse] = await Promise.all([
    page.waitForResponse('/api/addresses/validate'),
    page.waitForResponse('/api/payments/process'),
    page.waitForResponse('/api/orders'),
    checkoutPage.submitOrder(),
  ]);

  expect(addressResponse.status()).toBe(200);
  expect(paymentResponse.status()).toBe(200);
  expect(orderResponse.status()).toBe(201);

  // Wait for success message and redirect
  await expect(page.getByText('Order placed successfully')).toBeVisible();
  await page.waitForURL(/\/orders\/\d+/);
});
```

---

## Quick Reference

### Async Patterns Checklist

#### 🔴 BLOCKING
- [ ] No `waitForTimeout()` or fixed waits
- [ ] Use `expect()` assertions for waiting
- [ ] Wait for specific URL after navigation
- [ ] Wait for API responses when testing data loading
- [ ] Use `toPass()` for eventually consistent conditions

#### 🟡 WARNING
- [ ] Avoid `networkidle` unless necessary
- [ ] Timeouts are reasonable (not too high/low)
- [ ] Poll intervals are appropriate for use case
- [ ] Animation waits handled explicitly

#### 🟢 BEST PRACTICE
- [ ] Rely on auto-waiting when possible
- [ ] Use `Promise.all` for parallel waits
- [ ] Custom matchers for complex conditions
- [ ] Disable animations in test mode

---

## Common Patterns

### Pattern: Wait and Extract Data

```typescript
// Wait for element and get its text
const price = await page.getByTestId('product-price').textContent();
expect(price).toBe('€99.99');

// Wait for multiple elements and extract data
const prices = await page.getByTestId('product-price').allTextContents();
expect(prices).toHaveLength(10);
```

### Pattern: Conditional Wait

```typescript
// Wait for one of multiple possible outcomes
const result = await Promise.race([
  page.getByText('Success').waitFor().then(() => 'success'),
  page.getByText('Error').waitFor().then(() => 'error'),
]);

if (result === 'success') {
  // Handle success
} else {
  // Handle error
}
```

### Pattern: Wait with Retry

```typescript
// Retry action until it succeeds
await expect(async () => {
  await page.getByRole('button', { name: 'Retry' }).click();
  await expect(page.getByText('Connected')).toBeVisible();
}).toPass({ timeout: 30000 });
```

---

## Anti-Patterns

### 🔴 WRONG - Sleep Instead of Wait

```typescript
// ❌ Don't do this
await page.waitForTimeout(3000);
await page.getByRole('button').click();

// ✅ Do this instead
await page.getByRole('button').click(); // Auto-waits
```

### 🔴 WRONG - Polling with While Loop

```typescript
// ❌ Don't do this
while (!(await page.getByText('Loaded').isVisible())) {
  await page.waitForTimeout(100);
}

// ✅ Do this instead
await expect(page.getByText('Loaded')).toBeVisible();
```

### 🔴 WRONG - Chaining Timeouts

```typescript
// ❌ Don't do this
await page.waitForTimeout(1000);
await page.getByRole('button').click();
await page.waitForTimeout(2000);
await expect(page.getByText('Success')).toBeVisible();

// ✅ Do this instead
await page.getByRole('button').click();
await expect(page.getByText('Success')).toBeVisible();
```
