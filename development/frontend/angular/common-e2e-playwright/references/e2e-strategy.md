# E2E Test Strategy

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

The test pyramid and "E2E is expensive, cover critical paths only" are stated in
`SKILL.md` and are general testing knowledge — not repeated here. This reference
keeps the operational decisions: the **what-to-E2E decision table**, **smoke vs
full** split, and **cross-browser** scope.

## Table of Contents

- [What to E2E Test](#what-to-e2e-test)
- [Smoke Tests vs Full Suite](#smoke-tests-vs-full-suite)
- [Cross-Browser Testing](#cross-browser-testing)

---

## What to E2E Test

E2E covers critical user journeys through the UI (happy paths). Everything a
lower layer can verify stays at that layer.

| Scenario | E2E? | If not E2E, cover with |
|----------|------|------------------------|
| User can log in / log out | ✅ Yes | — |
| User can add product to cart, checkout | ✅ Yes | — |
| Search and filter products | ✅ Yes | — |
| Admin can create/edit/delete a resource | ✅ Yes | — |
| Payment processing (happy path) | ✅ Yes | mock the third party (Stripe) |
| Invalid email / short password shows error | ❌ No | unit test the validator |
| Cart total calculation | ❌ No | unit test the cart service |
| API response format | ❌ No | integration test |
| CSS styling / component rendering | ❌ No | visual / unit test |
| Stripe validates the card | ❌ No | Stripe test mode / integration test |

### 🔴 BLOCKING

- **One happy-path E2E per journey, plus a ~20% sample of error paths.** Test the
  remaining error and edge cases at the unit/integration layer, not through the
  browser.

---

## Smoke Tests vs Full Suite

Tag a small critical subset `@smoke` and keep it in `*.smoke.spec.ts` files.

- **Smoke** (~5–10 tests, 2–5 min): run on every commit — login, browse, add to
  cart, checkout, order confirmation, admin login. Fast feedback.
- **Full** (20–50 tests): run before merge and nightly — full coverage including
  the sampled error paths.

```typescript
test('@smoke should complete checkout', async ({ page }) => {
  // Minimum revenue path: login + add to cart + checkout.
});
```

```bash
npx playwright test --grep @smoke   # smoke only
```

**Smoke-selection criteria:** revenue impact, used by most users, failure blocks
users completely.

---

## Cross-Browser Testing

### 🟡 WARNING

Run **critical paths** (login, checkout) and CSS-heavy features on all browsers.
Run everything else — admin CRUD, secondary features — on Chromium only. Wire it
by matching `*.smoke.spec.ts` on the non-Chromium projects:

```typescript
// playwright.config.ts
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },  // all tests
  { name: 'firefox', use: { ...devices['Desktop Firefox'] }, testMatch: '**/*.smoke.spec.ts' },
  { name: 'webkit',  use: { ...devices['Desktop Safari'] },  testMatch: '**/*.smoke.spec.ts' },
]
```
