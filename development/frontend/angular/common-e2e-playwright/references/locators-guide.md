# Locators Guide for Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

The mechanics of each locator (`getByRole`, `getByLabel`, `getByPlaceholder`,
`getByText`, `getByAltText`, `.filter()`, `.nth()`, frame locators) are native
Playwright API knowledge — see the official locators docs. This reference keeps
the **house priority ladder** (which diverges from Playwright's `getByRole`-first
recommendation), the `getByTestId` naming convention, and application examples.

## Table of Contents

- [Locator Priority (House Order)](#locator-priority-house-order)
- [getByTestId & Naming](#getbytestid--naming)
- [Application Locator Examples](#application-locator-examples)

---

## Locator Priority (House Order)

### 🔴 BLOCKING — use this order

The house convention puts **`getByTestId` first** (Playwright's docs put
`getByRole` first). A `data-testid` is an explicit test contract that survives
copy, restyle, and i18n; role/name still comes right after for semantic elements.

| Priority | Method | Example | Stability |
|---------:|--------|---------|-----------|
| 1 | `getByTestId` | `page.getByTestId('submit-btn')` | ⭐⭐⭐⭐⭐ |
| 2 | `getByRole` | `page.getByRole('button', { name: 'Submit' })` | ⭐⭐⭐⭐⭐ |
| 3 | `getByLabel` | `page.getByLabel('Email address')` | ⭐⭐⭐⭐ |
| 4 | `getByPlaceholder` | `page.getByPlaceholder('Enter email')` | ⭐⭐⭐ |
| 5 | `getByText` | `page.getByText('Welcome back')` | ⭐⭐⭐ |
| 6 | `getByAltText` | `page.getByAltText('Company logo')` | ⭐⭐⭐ |
| 7 | `locator` (CSS) | `page.locator('.submit-button')` | ⭐ last resort |
| 8 | XPath | — | ❌ never |

Never use XPath, and never use CSS **class** selectors (they belong to styling
and break on restyle). CSS is acceptable only for third-party markup without
roles or test IDs.

---

## getByTestId & Naming

```typescript
await page.getByTestId('submit-button').click();
await page.getByTestId('email-input').fill('test@example.com');
await expect(page.getByTestId('error-message')).toBeVisible();
```

```html
<button data-testid="submit-button">Submit</button>
<input data-testid="email-input" type="email" />
```

### 🟡 WARNING

- **Consistent naming** — kebab-case describing purpose (`product-card-title`),
  never implementation details (`div-123`).
- **Don't overuse** — prefer `getByRole` when a semantic role is unambiguous.

---

## Application Locator Examples

### Customer Frontend

```typescript
// Login page
await page.getByLabel('Email').fill('john.doe@example.com');
await page.getByLabel('Password').fill('password123');
await page.getByRole('button', { name: 'Sign In' }).click();

// Product catalog
const productCard = page.getByTestId('product-card').filter({
  hasText: 'Eco-Friendly Water Bottle'
});
await expect(productCard.getByTestId('product-price')).toHaveText('€24.99');
await productCard.getByRole('button', { name: 'Add to Cart' }).click();

// Cart
const cartItem = page.getByTestId('cart-item').filter({
  hasText: 'Eco-Friendly Water Bottle'
});
await cartItem.getByRole('button', { name: 'Remove' }).click();

// Checkout
await page.getByLabel('Shipping address').fill('123 Main St');
await page.getByRole('combobox', { name: 'Payment method' }).selectOption('credit-card');
await page.getByRole('button', { name: 'Place Order' }).click();
```

### Backoffice Admin

```typescript
// Product management
await page.getByRole('link', { name: 'Products' }).click();
await page.getByRole('button', { name: 'Add Product' }).click();

const dialog = page.getByRole('dialog');
await dialog.getByLabel('Product name').fill('New Eco Product');
await dialog.getByLabel('Price').fill('49.99');
await dialog.getByLabel('Stock').fill('100');
await dialog.getByRole('button', { name: 'Save' }).click();

// Product list table
const productRow = page.getByRole('row').filter({
  has: page.getByText('New Eco Product')
});
await expect(productRow.getByRole('cell', { name: '€49.99' })).toBeVisible();
await productRow.getByRole('button', { name: 'Edit' }).click();

// User management
const userRow = page.getByRole('row').filter({
  has: page.getByText('john.doe@example.com')
});
await userRow.getByRole('button', { name: 'Disable' }).click();
```
