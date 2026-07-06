# Flaky Tests Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

The universal flake cures — explicit waits over fixed timeouts, isolated data,
`page.clock` for time, seeded randomness — are covered generically in the
official docs and in [async-waits.md](async-waits.md). This reference keeps the
cause→fix lookup and the one house-specific flake: **two-tier auth timing**.

## Table of Contents

- [Cause → Fix Table](#cause--fix-table)
- [Two-Tier Auth Timing](#two-tier-auth-timing)
- [Mocking Time](#mocking-time)
- [Debugging: Trace Viewer](#debugging-trace-viewer)

---

## Cause → Fix Table

| Cause | Symptom | Fix |
|-------|---------|-----|
| Race condition | Fails randomly checking state | Explicit wait for the specific condition |
| Shared state | Fails when run with other tests | Isolation, unique data per test |
| Animation timing | Fails interacting with element | Rely on auto-wait for stability, or disable animations |
| Network variability | Fails when API is slow | Wait for the specific response, not a timeout |
| Time-dependent logic | Fails at specific times | Mock the clock |
| Random data | Fails on certain values | Seed generators / use deterministic data |

### 🔴 BLOCKING

- **Fix the root cause; never mask a flake** with `waitForTimeout`, an inflated
  timeout, `test.retries(n)`, or `test.skip`. Retries in CI are a stop-gap tied
  to a tracked ticket, not a fix.

---

## Two-Tier Auth Timing

The most common house flake: a login test asserts the redirect before the
**second** OAuth2 grant (the `password` grant) has resolved and stored its token.
Wait for **both** `/oauth/token` responses before asserting.

```typescript
// 🔴 FLAKY — may redirect before the user (password-grant) token is stored
test('should login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('john.doe@example.com', 'password');
  await expect(page).toHaveURL('/dashboard');
});

// ✅ FIXED — wait for both client_credentials and password grants
test('should login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();

  const [clientTokenResp, userTokenResp] = await Promise.all([
    page.waitForResponse(resp => resp.url().includes('/oauth/token')
      && resp.request().postDataJSON()?.grant_type === 'client_credentials'),
    page.waitForResponse(resp => resp.url().includes('/oauth/token')
      && resp.request().postDataJSON()?.grant_type === 'password'),
    loginPage.login('john.doe@example.com', 'password'),
  ]);

  expect(clientTokenResp.status()).toBe(200);
  expect(userTokenResp.status()).toBe(200);
  await expect(page).toHaveURL('/dashboard');
});
```

---

## Mocking Time

For greetings, expiry, or any date-dependent UI, freeze the clock instead of
branching on the wall clock:

```typescript
await page.clock.setFixedTime(new Date('2024-01-01T09:00:00'));
await page.goto('/dashboard');
await expect(page.getByText('Good morning')).toBeVisible();
```

---

## Debugging: Trace Viewer

Reproduce a flake from CI artifacts (trace uploaded on failure — see
[ci.md](ci.md)):

```bash
npx playwright show-trace trace.zip
```

The trace holds network, DOM snapshots, per-step screenshots, console logs, and
the action timeline — enough to diagnose without re-running the suite.
