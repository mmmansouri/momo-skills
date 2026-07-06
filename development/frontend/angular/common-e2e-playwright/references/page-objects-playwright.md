# Page Objects with Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

The Page Object rules — encapsulate locators, no assertions in POMs, return the
next page from navigation — are stated with rationale in `SKILL.md` (§ When
Writing Page Objects). This reference holds the **full canonical example**, the
component/function alternatives, and the **two-tier auth** integration.

## Table of Contents

- [Canonical Class-Based Page Object](#canonical-class-based-page-object)
- [Component & Function Alternatives](#component--function-alternatives)
- [Two-Tier Authentication Integration](#two-tier-authentication-integration)

---

## Canonical Class-Based Page Object

Locators as `readonly` properties, actions as methods, navigation methods return
the next page object, no assertions inside.

```typescript
// pages/login.page.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(private readonly page: Page) {
    this.emailInput = page.getByTestId('email-input');
    this.passwordInput = page.getByTestId('password-input');
    this.submitButton = page.getByRole('button', { name: 'Sign In' });
    this.errorMessage = page.getByTestId('error-message');
  }

  async goto(): Promise<void> {
    await this.page.goto('/login');
  }

  // Actions only — the spec asserts.
  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  // Navigation returns the next page object so callers can't forget the wait.
  async loginAndGoToDashboard(email: string, password: string): Promise<DashboardPage> {
    await this.login(email, password);
    await this.page.waitForURL('/dashboard');
    return new DashboardPage(this.page);
  }
}
```

Compose actions into an object parameter once a method needs more than ~3
arguments (`completeCheckout(data: CheckoutData)`), and scope child locators with
`.filter({ hasText })` rather than exposing raw selectors to the spec.

---

## Component & Function Alternatives

- **Component POMs** — for a complex page, split logical regions into their own
  small classes (`ProductImageGallery`, `ProductInfo`) and expose them as
  properties on the page object (`productPage.info.addToCart()`). Keeps a big
  page from becoming a mega-class.
- **Function POMs** — for a trivial page, a factory returning an object of
  actions (`createSearchPage(page)`) is lighter than a class. Same rules apply:
  encapsulate locators, no assertions.

---

## Two-Tier Authentication Integration

House auth is two-tier OAuth2. Two ways to reach an authenticated state:

**Via UI** — the Angular HTTP interceptor performs the `client_credentials`
grant automatically; the page object only drives the user login form.

```typescript
export class AuthenticatedPage {
  constructor(private readonly page: Page) {}

  async loginAsCustomer(email: string, password: string): Promise<void> {
    const loginPage = new LoginPage(this.page);
    await loginPage.goto();
    await loginPage.login(email, password);   // client grant runs via interceptor
    await this.page.waitForURL('/dashboard');
  }
}
```

**Via API (faster)** — `AuthHelper` performs both grants over the API and stores
the token in `localStorage`. This is what the authenticated-page fixture uses
(see [custom-fixtures.md](custom-fixtures.md#authenticated-page-fixture-two-tier-auth)).

```typescript
// utils/auth-helper.ts
export class AuthHelper {
  constructor(
    private readonly page: Page,
    private readonly request: APIRequestContext,
  ) {}

  async loginViaApi(email: string, password: string): Promise<string> {
    // Tier 1: client authentication
    const clientResp = await this.request.post('/oauth/token', {
      data: { grant_type: 'client_credentials', client_id: 'your-client-id', client_secret: 'client-secret' },
    });
    const clientToken = (await clientResp.json()).access_token;

    // Tier 2: user authentication (bearer the client token)
    const userResp = await this.request.post('/oauth/token', {
      headers: { Authorization: `Bearer ${clientToken}` },
      data: { grant_type: 'password', username: email, password },
    });
    const userToken = (await userResp.json()).access_token;

    await this.page.goto('/');
    await this.page.evaluate(t => localStorage.setItem('access_token', t), userToken);
    return userToken;
  }
}
```
