# API Mocking with Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

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

## Basic Request Interception

### 🔴 BLOCKING - page.route()

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

### Route Patterns

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

## Response Mocking

### 🔴 BLOCKING - fulfill() Options

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

### Mock with File

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

## Conditional Mocking

### 🔴 BLOCKING - Route Based on Request

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

## Error Simulation

### 🔴 BLOCKING - Testing Error Handling

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

### Abort Reasons

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

## Partial Mocking

### 🟡 WARNING - Mock Only Specific Requests

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

### Modify Request Before Continuing

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

## Mock Priority

### 🔴 BLOCKING - Most Specific Routes First

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

## HAR Replay (Record & Replay)

### 🟢 BEST PRACTICE - Record Real Traffic

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

## Buy Nature Examples

### Mock Stripe Payment API

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

### Mock Buy Nature Backend Errors

```typescript
test('should handle product not found', async ({ page }) => {
  // Mock 404 error from Buy Nature backend
  await page.route('**/api/products/999', route =>
    route.fulfill({
      status: 404,
      contentType: 'application/problem+json', // RFC 7807
      body: JSON.stringify({
        type: 'https://buynature.com/errors/product-not-found',
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

### Mock Two-Tier Authentication

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

### Mock Product Catalog with Pagination

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

## Debugging Mocked Requests

### 🟢 BEST PRACTICE - Log Intercepted Requests

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

### Verify Request Was Made

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

## Quick Reference

### API Mocking Checklist

#### 🔴 BLOCKING
- [ ] Use mocking for error cases and third-party APIs
- [ ] Don't mock happy paths with your own API
- [ ] Most specific routes defined first
- [ ] Mock returns realistic data structures
- [ ] Test both success and failure scenarios

#### 🟡 WARNING
- [ ] Don't over-mock (reduces confidence in tests)
- [ ] Mock responses match real API contracts
- [ ] Update mocks when API changes
- [ ] Use HAR replay for complex scenarios

#### 🟢 BEST PRACTICE
- [ ] Conditional mocking based on request details
- [ ] Combine mocking with real API calls (partial mocking)
- [ ] Log intercepted requests during debugging
- [ ] Extract mock data to fixtures
- [ ] Verify mocked endpoints were called

---

## Common Patterns

### Pattern: Mock Factory

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
        type: 'https://buynature.com/errors/generic',
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

### Pattern: Reusable Mock Helpers

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

## Anti-Patterns

### 🔴 WRONG - Mocking Everything

```typescript
// ❌ Don't mock your own API for happy paths
test('should display products', async ({ page }) => {
  await page.route('**/api/**', route => route.fulfill(...)); // ❌ Over-mocking
  await page.goto('/products');
  // Not testing real integration
});
```

### ✅ CORRECT - Mock Only When Needed

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
