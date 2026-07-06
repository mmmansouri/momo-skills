# Async & Wait Strategies in Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Playwright auto-waits before every action and every web-first assertion
(`toBeVisible`, `toHaveText`, `waitForURL`, `waitForResponse`, `toPass`) is a
native wait. Those APIs are covered in the official docs — this reference keeps
only the house wait conventions that diverge from or extend the defaults.

## Table of Contents

- [Load States](#load-states)
- [expect.toPass for Eventually-Consistent Data](#expecttopass-for-eventually-consistent-data)
- [Two-Tier Authentication Flow](#two-tier-authentication-flow)

---

## Load States

Prefer waiting for a specific element or response over a load state. When a load
state is unavoidable:

| State | Complete when | Use |
|-------|---------------|-----|
| `load` | Page `load` event fired | Default, usually sufficient |
| `domcontentloaded` | DOM parsed | Static pages, very fast |
| `networkidle` | No network for 500 ms | SPA async data — **last resort, slow & flaky** |

### 🟡 WARNING

- **Avoid `networkidle`** — it is slow and flaky. Wait for the concrete element
  or the concrete API response instead.

---

## expect.toPass for Eventually-Consistent Data

For state that settles after a short delay (async projections, read models),
retry the whole assertion block rather than adding a fixed wait:

```typescript
await expect(async () => {
  const balance = await page.getByTestId('account-balance').textContent();
  expect(balance).toBe('€1,000.00');
}).toPass({ timeout: 10000, intervals: [1000, 2000, 3000] });
```

---

## Two-Tier Authentication Flow

House auth is two-tier OAuth2: a **client_credentials** grant followed by a
**password** grant, both hitting `/oauth/token`. When exercising login through
the UI, wait for **both** token responses so the assertion never races the
second grant (see also [flaky-tests.md](flaky-tests.md#two-tier-auth-timing)).

```typescript
test('should authenticate and load dashboard', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();

  // Login triggers two OAuth2 calls: client_credentials, then password grant.
  const [clientTokenResponse, userTokenResponse] = await Promise.all([
    page.waitForResponse(resp => resp.url().includes('/oauth/token')
      && resp.request().postDataJSON()?.grant_type === 'client_credentials'),
    page.waitForResponse(resp => resp.url().includes('/oauth/token')
      && resp.request().postDataJSON()?.grant_type === 'password'),
    loginPage.login('john.doe@example.com', 'password123'),
  ]);

  expect(clientTokenResponse.status()).toBe(200);
  expect(userTokenResponse.status()).toBe(200);

  await page.waitForURL('/dashboard');
  await expect(page.getByText('Welcome, John')).toBeVisible();
});
```
