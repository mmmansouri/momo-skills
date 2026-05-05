# Network and Async Patterns in Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

## Table of Contents

- [Async & Wait Strategies](#async--wait-strategies)
  - [Overview](#overview)
  - [Auto-Waiting (Playwright's Default)](#auto-waiting-playwrights-default)
  - [Fixed Waits (Never Use)](#fixed-waits-never-use)
  - [Waiting for Navigation](#waiting-for-navigation)
  - [Waiting for Elements](#waiting-for-elements)
  - [Waiting for Network Requests](#waiting-for-network-requests)
  - [Custom Wait Conditions](#custom-wait-conditions)
  - [Timeouts](#timeouts)
  - [Handling Animations](#handling-animations)
  - [Waiting for Multiple Conditions](#waiting-for-multiple-conditions)
  - [Example Async Patterns](#example-async-patterns)
  - [Async Quick Reference](#async-quick-reference)
  - [Async Common Patterns](#async-common-patterns)
  - [Async Anti-Patterns](#async-anti-patterns)
- [API Mocking & Network Interception](#api-mocking--network-interception)
  - [Mocking Overview](#mocking-overview)
  - [Basic Request Interception](#basic-request-interception)
  - [Response Mocking](#response-mocking)
  - [Conditional Mocking](#conditional-mocking)
  - [Error Simulation](#error-simulation)
  - [Partial Mocking](#partial-mocking)
  - [Mock Priority](#mock-priority)
  - [HAR Replay (Record & Replay)](#har-replay-record--replay)
  - [Example Mocking Scenarios](#example-mocking-scenarios)
  - [Debugging Mocked Requests](#debugging-mocked-requests)
  - [Mocking Quick Reference](#mocking-quick-reference)
  - [Mocking Common Patterns](#mocking-common-patterns)
  - [Mocking Anti-Patterns](#mocking-anti-patterns)

---

## Async & Wait Strategies

### Overview

Playwright has built-in auto-waiting for most actions, but understanding async patterns is critical for writing stable, non-flaky tests.

**Key principle**: Wait for specific conditions, never use arbitrary timeouts.

---

### Auto-Waiting (Playwright's Default)

#### 🟢 BEST PRACTICE - Playwright Waits Automatically

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

#### What Playwright Checks Before Action

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

### Fixed Waits (Never Use)

#### 🔴 BLOCKING - Don't Use waitForTimeout

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

### Waiting for Navigation

#### 🔴 BLOCKING - waitForURL

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

#### 🟡 WARNING - waitForLoadState

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

#### 🟡 WARNING
- **Avoid `networkidle` if possible** → Can be slow and flaky
- **Prefer waiting for specific elements** → More precise than load state

---

### Waiting for Elements

#### 🔴 BLOCKING - Use expect() Assertions

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

#### Assertion Matchers for Waiting

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

### Waiting for Network Requests

#### 🔴 BLOCKING - waitForResponse

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

#### waitForRequest

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

### Custom Wait Conditions

#### 🔴 BLOCKING - expect.poll() for Complex Conditions

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

#### expect.toPass() for Flaky Conditions

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

### Timeouts

#### 🔴 BLOCKING - Timeout Hierarchy

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

#### 🟡 WARNING
- **Don't increase timeouts to hide problems** → Fix the root cause
- **Use longer timeouts in CI if needed** → CI may be slower
- **Keep timeouts reasonable** → Long timeouts slow down failure detection

---

### Handling Animations

#### 🔴 BLOCKING - Wait for Animation End

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

### Waiting for Multiple Conditions

#### 🔴 BLOCKING - Promise.all for Parallel Waits

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

### Example Async Patterns

#### Two-Tier Authentication Flow

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
    loginPage.login('john.doe@example.com', 'password123'),
  ]);

  // Assert both auth calls succeeded
  expect(clientTokenResponse.status()).toBe(200);
  expect(userTokenResponse.status()).toBe(200);

  // Wait for redirect to dashboard
  await page.waitForURL('/dashboard');
  await expect(page.getByText('Welcome, John')).toBeVisible();
});
```

#### Product Catalog with Lazy Loading

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

#### Checkout Flow with Payment Processing

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

### Async Quick Reference

#### Async Patterns Checklist

##### 🔴 BLOCKING
- [ ] No `waitForTimeout()` or fixed waits
- [ ] Use `expect()` assertions for waiting
- [ ] Wait for specific URL after navigation
- [ ] Wait for API responses when testing data loading
- [ ] Use `toPass()` for eventually consistent conditions

##### 🟡 WARNING
- [ ] Avoid `networkidle` unless necessary
- [ ] Timeouts are reasonable (not too high/low)
- [ ] Poll intervals are appropriate for use case
- [ ] Animation waits handled explicitly

##### 🟢 BEST PRACTICE
- [ ] Rely on auto-waiting when possible
- [ ] Use `Promise.all` for parallel waits
- [ ] Custom matchers for complex conditions
- [ ] Disable animations in test mode

---

### Async Common Patterns

#### Pattern: Wait and Extract Data

```typescript
// Wait for element and get its text
const price = await page.getByTestId('product-price').textContent();
expect(price).toBe('€99.99');

// Wait for multiple elements and extract data
const prices = await page.getByTestId('product-price').allTextContents();
expect(prices).toHaveLength(10);
```

#### Pattern: Conditional Wait

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

#### Pattern: Wait with Retry

```typescript
// Retry action until it succeeds
await expect(async () => {
  await page.getByRole('button', { name: 'Retry' }).click();
  await expect(page.getByText('Connected')).toBeVisible();
}).toPass({ timeout: 30000 });
```

---

### Async Anti-Patterns

#### 🔴 WRONG - Sleep Instead of Wait

```typescript
// ❌ Don't do this
await page.waitForTimeout(3000);
await page.getByRole('button').click();

// ✅ Do this instead
await page.getByRole('button').click(); // Auto-waits
```

#### 🔴 WRONG - Polling with While Loop

```typescript
// ❌ Don't do this
while (!(await page.getByText('Loaded').isVisible())) {
  await page.waitForTimeout(100);
}

// ✅ Do this instead
await expect(page.getByText('Loaded')).toBeVisible();
```

#### 🔴 WRONG - Chaining Timeouts

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

---

## API Mocking & Network Interception

### Mocking Overview

API mocking allows you to intercept network requests and return controlled responses. Use mocking to test edge cases, simulate errors, and make tests faster and more reliable.

**When to mock:**
- Testing error handling (500 errors, network failures)
- Testing edge cases (empty responses, unusual data)
- Third-party APIs (payment gateways, external services)
- Slow APIs in development

**When NOT to mock:**
- Testing happy paths with your own API
- Integration testing (test real API)
- E2E smoke tests (use real services)

---

### Basic Request Interception

#### 🔴 BLOCKING - page.route()

```typescript
// Mock a GET request
await page.route('**/api/products', async route => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([
      { id: '1', name: 'Test Product', price: 99.99 },
      { id: '2', name: 'Another Product', price: 49.99 },
    ]),
  });
});

await page.goto('/products');
await expect(page.getByText('Test Product')).toBeVisible();
```

#### Route Patterns

```typescript
// Exact URL
await page.route('https://api.example.com/products', route => route.fulfill(...));

// Wildcard pattern
await page.route('**/api/products', route => route.fulfill(...));

// Regex pattern
await page.route(/\/api\/products\/\d+/, route => route.fulfill(...));

// Multiple endpoints
await page.route('**/api/**', route => route.fulfill(...));
```

---

### Response Mocking

#### 🔴 BLOCKING - fulfill() Options

```typescript
test('should mock API response', async ({ page }) => {
  await page.route('**/api/products', async route => {
    await route.fulfill({
      status: 200,                        // HTTP status code
      contentType: 'application/json',    // Content-Type header
      headers: {                          // Custom headers
        'X-Custom-Header': 'value',
      },
      body: JSON.stringify({              // Response body
        products: [
          { id: '1', name: 'Product 1' },
        ],
      }),
    });
  });

  await page.goto('/products');
  await expect(page.getByText('Product 1')).toBeVisible();
});
```

#### Mock with File

```typescript
await page.route('**/api/products', async route => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    path: './fixtures/products.json', // Load from file
  });
});
```

---

### Conditional Mocking

#### 🔴 BLOCKING - Route Based on Request

```typescript
await page.route('**/api/products', async route => {
  const request = route.request();

  // Check HTTP method
  if (request.method() === 'GET') {
    await route.fulfill({
      status: 200,
      body: JSON.stringify([{ id: '1', name: 'Product' }]),
    });
  } else if (request.method() === 'POST') {
    await route.fulfill({
      status: 201,
      body: JSON.stringify({ id: '2', name: 'New Product' }),
    });
  }
});

// Check query parameters
await page.route('**/api/products', async route => {
  const url = new URL(route.request().url());
  const category = url.searchParams.get('category');

  if (category === 'electronics') {
    await route.fulfill({
      status: 200,
      body: JSON.stringify([{ id: '1', name: 'Laptop' }]),
    });
  } else {
    await route.fulfill({
      status: 200,
      body: JSON.stringify([]),
    });
  }
});

// Check request body
await page.route('**/api/orders', async route => {
  const postData = route.request().postDataJSON();

  if (postData.total > 1000) {
    await route.fulfill({
      status: 400,
      body: JSON.stringify({ error: 'Order exceeds maximum amount' }),
    });
  } else {
    await route.fulfill({
      status: 201,
      body: JSON.stringify({ id: 'order-123', status: 'created' }),
    });
  }
});
```

---

### Error Simulation

#### 🔴 BLOCKING - Testing Error Handling

```typescript
// 500 Internal Server Error
test('should handle server error', async ({ page }) => {
  await page.route('**/api/products', route =>
    route.fulfill({ status: 500 })
  );

  await page.goto('/products');
  await expect(page.getByText('Failed to load products')).toBeVisible();
});

// 404 Not Found
test('should handle not found', async ({ page }) => {
  await page.route('**/api/products/999', route =>
    route.fulfill({
      status: 404,
      body: JSON.stringify({ error: 'Product not found' }),
    })
  );

  await page.goto('/products/999');
  await expect(page.getByText('Product not found')).toBeVisible();
});

// Network timeout
test('should handle network timeout', async ({ page }) => {
  await page.route('**/api/products', async route => {
    await new Promise(resolve => setTimeout(resolve, 60000)); // Never resolve
  });

  await page.goto('/products');
  await expect(page.getByText('Request timed out')).toBeVisible();
});

// Network failure
test('should handle network failure', async ({ page }) => {
  await page.route('**/api/products', route => route.abort('failed'));

  await page.goto('/products');
  await expect(page.getByText('Network error')).toBeVisible();
});
```

#### Abort Reasons

| Reason | Simulates |
|--------|-----------|
| `'failed'` | Generic network failure |
| `'aborted'` | Request aborted |
| `'timedout'` | Request timeout |
| `'accessdenied'` | Access denied (CORS, etc.) |
| `'connectionclosed'` | Connection closed |
| `'connectionreset'` | Connection reset |
| `'internetdisconnected'` | No internet connection |

---

### Partial Mocking

#### 🟡 WARNING - Mock Only Specific Requests

```typescript
// Mock only third-party APIs, allow own API
await page.route('**/*', async route => {
  const url = route.request().url();

  if (url.includes('stripe.com')) {
    // Mock Stripe API
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ paymentIntentId: 'pi_mock_123' }),
    });
  } else {
    // Let other requests continue to real API
    await route.continue();
  }
});
```

#### Modify Request Before Continuing

```typescript
// Add authentication header
await page.route('**/api/**', async route => {
  await route.continue({
    headers: {
      ...route.request().headers(),
      'Authorization': 'Bearer mock-token-123',
    },
  });
});

// Modify request body
await page.route('**/api/orders', async route => {
  const postData = route.request().postDataJSON();
  await route.continue({
    postData: JSON.stringify({
      ...postData,
      testMode: true, // Add test flag
    }),
  });
});
```

---

### Mock Priority

#### 🔴 BLOCKING - Most Specific Routes First

```typescript
// ✅ CORRECT - Specific before generic
await page.route('**/api/products/123', async route => {
  // Specific product
  await route.fulfill({ status: 200, body: JSON.stringify({ id: '123', name: 'Special Product' }) });
});

await page.route('**/api/products', async route => {
  // All products
  await route.fulfill({ status: 200, body: JSON.stringify([{ id: '1', name: 'Product 1' }]) });
});

// 🔴 WRONG - Generic before specific (specific route never reached)
await page.route('**/api/**', route => route.fulfill(...)); // ❌ Catches everything
await page.route('**/api/products/123', route => route.fulfill(...)); // ❌ Never called
```

---

### HAR Replay (Record & Replay)

#### 🟢 BEST PRACTICE - Record Real Traffic

```typescript
// Record HAR during manual test
// npx playwright test --save-har=products.har

// Replay HAR in automated test
test('should replay HAR', async ({ browser }) => {
  const context = await browser.newContext({
    recordHar: { path: './hars/products.har', mode: 'minimal' },
  });
  const page = await context.newPage();

  await page.goto('/products');
  await expect(page.getByText('Product 1')).toBeVisible();

  await context.close();
});
```

---

### Example Mocking Scenarios

#### Mock Stripe Payment API

```typescript
test('should handle Stripe payment', async ({ page }) => {
  // Mock Stripe API
  await page.route('**/api.stripe.com/**', async route => {
    const url = route.request().url();

    if (url.includes('payment_intents')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'pi_mock_123',
          status: 'succeeded',
          amount: 9999,
          currency: 'eur',
        }),
      });
    } else {
      await route.continue();
    }
  });

  const checkoutPage = new CheckoutPage(page);
  await checkoutPage.goto();
  await checkoutPage.fillCreditCard('4242 4242 4242 4242', '12/25', '123');
  await checkoutPage.submitPayment();

  await expect(page.getByText('Payment successful')).toBeVisible();
});
```

#### Mock Backend Errors

```typescript
test('should handle product not found', async ({ page }) => {
  // Mock 404 error from backend
  await page.route('**/api/products/999', route =>
    route.fulfill({
      status: 404,
      contentType: 'application/problem+json', // RFC 7807
      body: JSON.stringify({
        type: 'https://example.com/errors/product-not-found',
        title: 'Product Not Found',
        status: 404,
        detail: 'Product with ID 999 does not exist',
      }),
    })
  );

  await page.goto('/products/999');
  await expect(page.getByText('Product Not Found')).toBeVisible();
});

test('should handle authentication error', async ({ page }) => {
  // Mock 401 during login
  await page.route('**/oauth/token', route =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({
        error: 'invalid_grant',
        error_description: 'Invalid credentials',
      }),
    })
  );

  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('invalid@test.com', 'wrongpassword');

  await expect(page.getByText('Invalid credentials')).toBeVisible();
});
```

#### Mock Two-Tier Authentication

```typescript
test('should mock two-tier auth', async ({ page }) => {
  let clientTokenCalled = false;
  let userTokenCalled = false;

  await page.route('**/oauth/token', async route => {
    const postData = route.request().postDataJSON();

    if (postData.grant_type === 'client_credentials') {
      // First tier: Client authentication
      clientTokenCalled = true;
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          access_token: 'mock_client_token_123',
          token_type: 'Bearer',
          expires_in: 3600,
        }),
      });
    } else if (postData.grant_type === 'password') {
      // Second tier: User authentication
      userTokenCalled = true;
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          access_token: 'mock_user_token_456',
          token_type: 'Bearer',
          expires_in: 7200,
        }),
      });
    }
  });

  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('john.doe@example.com', 'password');

  await page.waitForURL('/dashboard');

  expect(clientTokenCalled).toBe(true);
  expect(userTokenCalled).toBe(true);
});
```

#### Mock Product Catalog with Pagination

```typescript
test('should mock paginated products', async ({ page }) => {
  await page.route('**/api/products', async route => {
    const url = new URL(route.request().url());
    const page = parseInt(url.searchParams.get('page') || '0', 10);
    const size = parseInt(url.searchParams.get('size') || '20', 10);

    // Generate mock products for this page
    const products = Array.from({ length: size }, (_, i) => ({
      id: `product-${page * size + i}`,
      name: `Product ${page * size + i + 1}`,
      price: 10 + i,
      stock: 100,
    }));

    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        content: products,
        totalElements: 100,
        totalPages: 5,
        number: page,
      }),
    });
  });

  await page.goto('/products');
  await expect(page.getByTestId('product-card')).toHaveCount(20);

  // Scroll to load next page
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await expect(page.getByTestId('product-card')).toHaveCount(40);
});
```

---

### Debugging Mocked Requests

#### 🟢 BEST PRACTICE - Log Intercepted Requests

```typescript
test('should log intercepted requests', async ({ page }) => {
  await page.route('**/api/**', async route => {
    console.log(`Intercepted: ${route.request().method()} ${route.request().url()}`);
    console.log('Headers:', route.request().headers());
    console.log('Body:', route.request().postData());

    await route.continue();
  });

  await page.goto('/products');
});
```

#### Verify Request Was Made

```typescript
test('should verify API was called', async ({ page }) => {
  let apiCalled = false;

  await page.route('**/api/products', async route => {
    apiCalled = true;
    await route.fulfill({
      status: 200,
      body: JSON.stringify([{ id: '1', name: 'Product' }]),
    });
  });

  await page.goto('/products');

  expect(apiCalled).toBe(true);
});
```

---

### Mocking Quick Reference

#### API Mocking Checklist

##### 🔴 BLOCKING
- [ ] Use mocking for error cases and third-party APIs
- [ ] Don't mock happy paths with your own API
- [ ] Most specific routes defined first
- [ ] Mock returns realistic data structures
- [ ] Test both success and failure scenarios

##### 🟡 WARNING
- [ ] Don't over-mock (reduces confidence in tests)
- [ ] Mock responses match real API contracts
- [ ] Update mocks when API changes
- [ ] Use HAR replay for complex scenarios

##### 🟢 BEST PRACTICE
- [ ] Conditional mocking based on request details
- [ ] Combine mocking with real API calls (partial mocking)
- [ ] Log intercepted requests during debugging
- [ ] Extract mock data to fixtures
- [ ] Verify mocked endpoints were called

---

### Mocking Common Patterns

#### Pattern: Mock Factory

```typescript
// utils/mock-factory.ts
export class MockFactory {
  static productList(count: number) {
    return Array.from({ length: count }, (_, i) => ({
      id: `product-${i}`,
      name: `Product ${i + 1}`,
      price: 10 + i,
    }));
  }

  static errorResponse(status: number, message: string) {
    return {
      status,
      contentType: 'application/problem+json',
      body: JSON.stringify({
        type: 'https://example.com/errors/generic',
        title: 'Error',
        status,
        detail: message,
      }),
    };
  }
}

// Usage
await page.route('**/api/products', route =>
  route.fulfill({
    status: 200,
    body: JSON.stringify(MockFactory.productList(10)),
  })
);
```

#### Pattern: Reusable Mock Helpers

```typescript
// utils/mock-helpers.ts
export async function mockProductsAPI(page: Page, products: Product[]) {
  await page.route('**/api/products', route =>
    route.fulfill({
      status: 200,
      body: JSON.stringify(products),
    })
  );
}

export async function mockAuthError(page: Page) {
  await page.route('**/oauth/token', route =>
    route.fulfill({
      status: 401,
      body: JSON.stringify({ error: 'invalid_credentials' }),
    })
  );
}

// Usage
test('should display products', async ({ page }) => {
  await mockProductsAPI(page, [
    { id: '1', name: 'Product 1', price: 10 },
    { id: '2', name: 'Product 2', price: 20 },
  ]);

  await page.goto('/products');
  await expect(page.getByText('Product 1')).toBeVisible();
});
```

---

### Mocking Anti-Patterns

#### 🔴 WRONG - Mocking Everything

```typescript
// ❌ Don't mock your own API for happy paths
test('should display products', async ({ page }) => {
  await page.route('**/api/**', route => route.fulfill(...)); // ❌ Over-mocking
  await page.goto('/products');
  // Not testing real integration
});
```

#### ✅ CORRECT - Mock Only When Needed

```typescript
// ✅ Test against real API for happy paths
test('should display products', async ({ page }) => {
  // No mocking - uses real backend
  await page.goto('/products');
  await expect(page.getByTestId('product-card')).toHaveCount(10);
});

// ✅ Mock only for error cases
test('should handle API error', async ({ page }) => {
  await page.route('**/api/products', route => route.fulfill({ status: 500 }));
  await page.goto('/products');
  await expect(page.getByText('Failed to load')).toBeVisible();
});
```
