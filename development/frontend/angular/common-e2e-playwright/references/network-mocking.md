# API Mocking & Network Interception in Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

The `page.route` / `route.fulfill` / `route.continue` / `route.abort` API, HAR
replay, and request-inspection helpers are native Playwright knowledge — see the
official network docs. This reference keeps the house **no-mock policy** and the
mocks that encode house contracts: Stripe, RFC 7807 backend errors, and two-tier
auth.

## Table of Contents

- [When to Mock (No-Mock Policy)](#when-to-mock-no-mock-policy)
- [The One Pattern: route + fulfill](#the-one-pattern-route--fulfill)
- [Mock Stripe](#mock-stripe)
- [Mock Backend Errors (RFC 7807)](#mock-backend-errors-rfc-7807)
- [Mock Two-Tier Authentication](#mock-two-tier-authentication)

---

## When to Mock (No-Mock Policy)

### 🔴 BLOCKING

- **Happy paths with our own API → never mock.** Drive the real backend
  (local-e2e / docker stack). Mocking the happy path tests nothing but the mock.
- **Mock only:** error/edge simulation (500, 404, timeout, network failure) and
  **third-party** services we don't control (payment gateways, external APIs).

---

## The One Pattern: route + fulfill

Register the **most specific route first** — a broad `**/api/**` registered
earlier swallows requests before a specific route is reached.

```typescript
await page.route('**/api/products', async route => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: '1', name: 'Test Product', price: 99.99 }]),
  });
});

await page.goto('/products');
await expect(page.getByText('Test Product')).toBeVisible();
```

Everything else (conditional routing on method/query/body, `route.continue`
with header rewrite, `route.abort('failed')`, HAR replay) is standard API usage.

---

## Mock Stripe

Third party we don't control — mock its endpoints, let everything else hit the
real backend via `route.continue()`.

```typescript
test('should handle Stripe payment', async ({ page }) => {
  await page.route('**/api.stripe.com/**', async route => {
    if (route.request().url().includes('payment_intents')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'pi_mock_123', status: 'succeeded', amount: 9999, currency: 'eur' }),
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

---

## Mock Backend Errors (RFC 7807)

The backend returns **RFC 7807 Problem Details** (`application/problem+json` with
`type` / `title` / `status` / `detail`). Error mocks must match that shape so the
frontend's error handling is exercised faithfully.

```typescript
test('should handle product not found', async ({ page }) => {
  await page.route('**/api/products/999', route =>
    route.fulfill({
      status: 404,
      contentType: 'application/problem+json',
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
```

---

## Mock Two-Tier Authentication

To simulate auth without a live backend, branch `/oauth/token` on `grant_type`:
first the `client_credentials` grant, then the `password` grant.

```typescript
test('should mock two-tier auth', async ({ page }) => {
  await page.route('**/oauth/token', async route => {
    const postData = route.request().postDataJSON();
    if (postData.grant_type === 'client_credentials') {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ access_token: 'mock_client_token', token_type: 'Bearer', expires_in: 3600 }),
      });
    } else if (postData.grant_type === 'password') {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ access_token: 'mock_user_token', token_type: 'Bearer', expires_in: 7200 }),
      });
    }
  });

  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('john.doe@example.com', 'password');
  await page.waitForURL('/dashboard');
});
```

A `401 invalid_grant` on the `password` branch simulates bad credentials.
