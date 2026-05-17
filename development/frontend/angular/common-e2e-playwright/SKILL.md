---
name: common-e2e-playwright
description: >-
  End-to-end testing with Playwright. Use this skill whenever the user asks to
  write an E2E test, automate a UI scenario in the browser, design a Page Object,
  add a fixture, mock a network request, debug a flaky test, configure Playwright,
  wire E2E tests into CI, verify a regression in the browser, or review E2E
  test changes in a PR (`*.spec.ts`, Page Objects, fixtures,
  `playwright.config.ts`) — even when they don't explicitly say "E2E" or
  "Playwright". Contains both the E2E discipline
  (what to test, isolation, locator hygiene, async strategy) and the Playwright
  API surface (`getByRole`, `route`, fixtures, `expect`).
---

# E2E Testing with Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## When Reasoning About E2E Testing

Apply these foundational stances to every E2E test:

1. **Test user journeys**, not implementation details.
2. **Isolation** — each test must run on its own, with fresh data.
3. **Stability over speed** — a reliable slow test beats a fast flaky one.
4. **Readable as documentation** — a test should describe expected behavior to a non-author.
5. **Minimal E2E** — only test what cannot be covered at lower levels (unit, integration).

### 🔴 BLOCKING

#### Test critical user journeys only — not what unit or integration tests already cover
**Why:** E2E tests are 10–100× slower and more expensive to debug than unit tests. Duplicating coverage at the E2E level inflates the suite, slows the feedback loop, and creates redundant failure points. Every E2E test must justify its position by exercising integration that no other layer can reach.

| ✅ Test in E2E | ❌ Don't test in E2E |
|----------------|----------------------|
| Login / logout flow | Form validation rules |
| Purchase checkout | Individual component rendering |
| Search and filter | API response formats |
| Multi-step wizards | CSS styling |
| Cross-browser specifics | Business logic (unit) |

#### Each test runs in full isolation — no shared state across tests
**Why:** order-dependent tests fail unpredictably, can't be parallelized, and hide the real defect when one breaks. Shared mutable state (a shared user, a leftover cart) couples tests and turns the failure of test N into N false positives downstream.

#### Never add fixed waits or retry-loops to mask flakiness — fix the root cause
**Why:** `waitForTimeout(5000)` and `retries: 5` make the symptom go away locally but the underlying race condition still produces failures in CI under load. The fix is *always* an explicit wait condition (element visible, network response, URL change). Hiding flakiness consumes the team's debugging budget on the same defects forever.

##### WRONG
```typescript
await page.click('#submit')
await page.waitForTimeout(3000)        // hope the dialog is open by now
await page.click('text=Confirm')
```
##### CORRECT
```typescript
await page.click('#submit')
await expect(page.getByRole('dialog', { name: 'Confirm action' })).toBeVisible()
await page.getByRole('button', { name: 'Confirm' }).click()
```

---

## When Designing the E2E Test Strategy

📚 **When deciding what to cover at the E2E layer, positioning tests on the pyramid, choosing smoke vs full suite, or planning cross-browser scope → read [e2e-strategy.md](references/e2e-strategy.md).**

### Test Pyramid Positioning

```
        /\
       /  \    E2E (5–10%)        — critical user journeys
      /----\
     /      \  Integration (20–30%) — API contracts, component integration
    /--------\
   /          \ Unit (60–70%)       — business logic
  /____________\
```

### 🔴 BLOCKING

#### Don't duplicate coverage across layers — pick the lowest layer that can verify the behavior
**Why:** every behavior tested at multiple layers multiplies maintenance cost and debugging confusion when two layers diverge. The pyramid is a budget, not an addition.

---

## When Structuring the E2E Project

📚 **When laying out the `e2e/` folder, organizing specs by feature, or placing pages/fixtures/utils directories → read [project-structure.md](references/project-structure.md).**

```
e2e/
├── tests/                  # Spec files grouped by feature
│   ├── auth/
│   ├── checkout/
│   └── catalog/
├── pages/                  # Page Object Models
├── fixtures/               # Test data + Playwright fixtures
├── utils/                  # Cross-cutting helpers (API client, etc.)
└── playwright.config.ts
```

---

## When Selecting Locators

📚 **When choosing between `getByTestId`/`getByRole`/`getByLabel`, chaining locators, scoping within components, or replacing CSS/XPath selectors → read [locators-guide.md](references/locators-guide.md).**

### Selector Priority (best → worst)

| Priority | Selector | Example |
|---------:|----------|---------|
| 1 | Test ID | `page.getByTestId('submit-btn')` |
| 2 | Role + name | `page.getByRole('button', { name: 'Submit' })` |
| 3 | Label | `page.getByLabel('Email')` |
| 4 | Placeholder | `page.getByPlaceholder('Enter email')` |
| 5 | Text | `page.getByText('Welcome')` |
| 6 | CSS class | `page.locator('.btn-primary')` *(avoid)* |
| 7 | XPath | `page.locator('//button[...]')` *(never)* |

### 🔴 BLOCKING

#### Never use XPath or CSS class selectors for production E2E
**Why:** XPath is unreadable and brittle. CSS classes belong to styling and change when the design team refactors — your tests then fail for reasons unrelated to product behavior. Test IDs and ARIA roles are explicit contracts that survive UI restyling.

##### WRONG
```typescript
page.locator('.btn-primary')
page.locator('div.container > form > button:nth-child(2)')
page.locator('//button[@type="submit"]')
```
##### CORRECT
```typescript
page.getByTestId('submit-btn')
page.getByRole('button', { name: 'Submit' })

// Scope within a component:
const card = page.getByTestId('product-card').filter({ hasText: 'iPhone' })
await card.getByRole('button', { name: 'Add to Cart' }).click()
```

---

## When Writing Page Objects

📚 **When designing a Page Object class, encapsulating locators, writing action methods that return the next page, or choosing class vs component vs function POMs → read [page-objects-playwright.md](references/page-objects-playwright.md).**

### 🔴 BLOCKING

#### Encapsulate locators inside the page object — never leak raw selectors to test specs
**Why:** raw selectors in tests scatter the same brittle string across N specs. When the UI changes, you patch N tests instead of 1 page object. The page object is the single source of truth for "how to find things on this page".

#### No assertions inside page objects — assertions live in specs
**Why:** an assertion in a page object hides the test's intent at the call site (`page.login()` either passes or fails for unknown reasons) and prevents the same action from being reused in negative-path tests. Page objects = actions; specs = expectations.

#### Return the next page object from navigation actions
**Why:** `loginAndGoToDashboard()` returning `DashboardPage` makes the test read like prose and prevents the caller from forgetting to wait for the URL change. Without the return, every test repeats the same `waitForURL` boilerplate.

```typescript
// pages/login.page.ts (compact form — full example in references/page-objects-playwright.md)
export class LoginPage {
  constructor(private readonly page: Page) {}

  readonly emailInput    = this.page.getByTestId('email')
  readonly passwordInput = this.page.getByTestId('password')
  readonly submit        = this.page.getByRole('button', { name: 'Sign in' })

  async goto()                                  { await this.page.goto('/login') }
  async login(email: string, password: string) {
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    await this.submit.click()
  }
  async loginAndGoToDashboard(email: string, password: string) {
    await this.login(email, password)
    await this.page.waitForURL('/dashboard')
    return new DashboardPage(this.page)
  }
}
```

---

## When Writing Tests

📚 **When structuring a spec with Arrange–Act–Assert, naming tests, parameterizing scenarios, using beforeEach/afterEach, or isolating per-test state → read [test-patterns.md](references/test-patterns.md).**

```typescript
test('logs in with valid credentials', async ({ page }) => {
  // Arrange
  const login = new LoginPage(page)
  await login.goto()

  // Act
  const dashboard = await login.loginAndGoToDashboard(user.email, user.password)

  // Assert
  await expect(page).toHaveURL('/dashboard')
  await expect(dashboard.welcomeMessage).toContainText(user.name)
})
```

### 🟡 WARNING

#### Follow Arrange–Act–Assert; one user-journey assertion per test
**Why:** multiple user-journey assertions per test obscure which step failed and force the entire setup to re-run for each behavior. AAA + small tests pay for themselves the first time something breaks.

---

## When Handling Async Operations

📚 **When picking a wait strategy (`toBeVisible`, `waitForURL`, `waitForResponse`, `toPass`), tuning timeouts, or handling animations and load states → read [async-waits.md](references/async-waits.md).**

### 🔴 BLOCKING

#### Wait for explicit conditions; never for fixed durations
**Why:** machines vary. A 3-second wait that works on your laptop fails on a slow CI runner; a 10-second wait wastes 7 seconds × N tests. Explicit conditions are both faster on average and immune to timing skew.

| Need | Strategy |
|------|----------|
| Element appears | `await expect(locator).toBeVisible()` |
| Text changes | `await expect(locator).toHaveText(...)` |
| Navigation | `await page.waitForURL('/dashboard')` |
| API response | `await page.waitForResponse(...)` |
| Network idle | `await page.waitForLoadState('networkidle')` |
| Custom polling | `await expect(async () => {...}).toPass({ timeout })` |

---

## When Mocking Network Requests

📚 **When intercepting requests with `page.route`, fulfilling responses, stubbing third-party APIs, or asserting on outgoing payloads → read [network-mocking.md](references/network-mocking.md).**

```typescript
await page.route('**/api/products', route =>
  route.fulfill({ status: 200, contentType: 'application/json',
                  body: JSON.stringify([{ id: '1', name: 'Test', price: 99.99 }]) })
)
await page.goto('/products')
await expect(page.getByText('Test')).toBeVisible()
```

---

## When Managing Test Data

📚 **When choosing between API/UI/DB seeding, using factories, cleaning up data, or avoiding production data leakage → read [test-data.md](references/test-data.md).**

| Strategy | Use when | Pros | Cons |
|----------|----------|------|------|
| API seeding | Fast setup needed | Fast, reliable | Requires API access |
| UI seeding | Testing the create-flow itself | Tests the real flow | Slow |
| DB seeding | Complex pre-state | Fastest | Tightest coupling |
| Static fixtures | Reference data | Simple | Drifts vs schema |

### 🔴 BLOCKING

#### Each test creates and owns its data; never use production data
**Why:** shared data couples tests; production data leaks PII and breaks when prod state changes. Per-test data also makes the suite trivially parallelizable.

---

## When Using Custom Fixtures

📚 **When extending `base.extend<T>` with custom fixtures, wiring authenticated pages, scoping fixture lifecycle (test/worker), or composing fixtures across spec files → read [custom-fixtures.md](references/custom-fixtures.md).**

```typescript
export const test = base.extend<{ loginPage: LoginPage; authenticatedPage: Page }>({
  loginPage: async ({ page }, use) => { await use(new LoginPage(page)) },

  authenticatedPage: async ({ page, request }, use) => {
    const token = await loginViaApi(request)
    await page.goto('/')
    await page.evaluate(t => localStorage.setItem('token', t), token)
    await page.reload()
    await use(page)
    await page.evaluate(() => localStorage.clear())
  },
})
```

---

## When Configuring Playwright

📚 **When editing `playwright.config.ts` — projects, timeouts, reporters, baseURL, webServer, trace/screenshot/video, global setup/teardown → read [playwright-config.md](references/playwright-config.md).**

Minimum config every project must set:

```typescript
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,        // fails CI if .only is left in
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: process.env.BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
})
```

### 🔴 BLOCKING

#### Always set `forbidOnly: !!process.env.CI`
**Why:** an accidentally-committed `.only` causes CI to silently run a single test and report green. The forbidOnly flag turns that into a hard failure where it belongs.

---

## When Dealing with Flaky Tests

📚 **When diagnosing intermittent failures — race conditions, animation timing, shared state, time/random non-determinism — or deciding on a retry policy → read [flaky-tests.md](references/flaky-tests.md).**

| Cause | Solution |
|-------|----------|
| Race conditions | Explicit waits |
| Shared state | Test isolation, fresh data per test |
| Animation timing | Wait for stable position / animation end |
| Network variability | Mock or wait for the specific response |
| Time-dependent logic | Mock time/dates |
| Random data | Seed random generators |

### 🔴 BLOCKING

#### Investigate flakes — never silence them with retries or larger timeouts
**Why:** retries paper over real defects (race conditions, missing waits). The defect remains, only its visibility moves from "test fails" to "test takes 3× longer and occasionally fails". Investigate first, retry only as a stop-gap with a tracked ticket.

---

## When Running in CI

📚 **When wiring Playwright into GitHub Actions, sharding tests across workers, uploading reports/traces as artifacts, or installing browsers with `--with-deps` → read [ci-github-actions.md](references/ci-github-actions.md).**

📚 **When configuring Docker runners (docker-compose for the full stack), choosing reporters (HTML/JUnit/GitHub), tuning CI performance (caching, parallel jobs), or troubleshooting CI-only failures → read [ci-docker-reporting.md](references/ci-docker-reporting.md).**

### 🔴 BLOCKING

#### Upload the Playwright report and traces as artifacts on failure
**Why:** without artifacts, "the test failed in CI" is unactionable. The HTML report + traces let any developer reproduce the failure locally without re-running the suite.

#### Run with `retries: 2` in CI but `0` locally
**Why:** local retries hide flakes from authors; CI retries absorb genuinely transient infrastructure issues without inflating the on-call burden. The asymmetry is intentional.

#### Install browsers with `--with-deps` in the CI step
**Why:** missing system libraries cause cryptic crashes in headless mode. `--with-deps` installs all required OS packages — the few-second cost beats hours debugging missing libnss3.

---

## Output Contract

When producing E2E artifacts, deliver each in this exact form:

| Artifact | Required Form |
|----------|---------------|
| **Test spec** (`tests/**/*.spec.ts`) | One feature per `describe`, AAA per `test`, asserts only in tests, uses page objects + fixtures, no raw selectors. |
| **Page object** (`pages/*.page.ts`) | Class with `Locator` properties + action methods returning `Promise<void>` or the next page object. No assertions, no test data. |
| **Custom fixture** (`fixtures/index.ts`) | `base.extend<T>({...})` with setup before `await use(...)` and cleanup after. Re-export `expect`. |
| **Config** (`playwright.config.ts`) | `defineConfig` with `forbidOnly`, `retries`, `trace`, `screenshot`, `video`, project list, `webServer` for local dev. |
| **CI workflow** | Steps: checkout → setup-node → `npm ci` → `npx playwright install --with-deps` → `npx playwright test` → upload report on failure. See `ci-github-actions.md`. |
