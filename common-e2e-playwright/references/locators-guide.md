# Locators Guide for Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

Locators are the foundation of E2E tests. Choosing the right locator strategy makes tests stable, readable, and maintainable.

**Key principle**: Locate elements the way users would identify them - by role, label, or visible text.

---

## Locator Priority Table

### 🔴 BLOCKING - Use This Order

| Priority | Method | Example | Use When | Stability |
|----------|--------|---------|----------|-----------|
| 1 | `getByTestId` | `page.getByTestId('submit-btn')` | Explicit test contract needed | ⭐⭐⭐⭐⭐ |
| 2 | `getByRole` | `page.getByRole('button', { name: 'Submit' })` | Element has semantic role | ⭐⭐⭐⭐⭐ |
| 3 | `getByLabel` | `page.getByLabel('Email address')` | Form inputs with labels | ⭐⭐⭐⭐ |
| 4 | `getByPlaceholder` | `page.getByPlaceholder('Enter email')` | Inputs with placeholders | ⭐⭐⭐ |
| 5 | `getByText` | `page.getByText('Welcome back')` | Static text content | ⭐⭐⭐ |
| 6 | `getByAltText` | `page.getByAltText('Company logo')` | Images with alt text | ⭐⭐⭐ |
| 7 | `getByTitle` | `page.getByTitle('Close dialog')` | Elements with title attribute | ⭐⭐ |
| 8 | `locator` (CSS) | `page.locator('.submit-button')` | Last resort only | ⭐ |
| 9 | XPath | DON'T USE | Never | ❌ |

---

## getByTestId

### 🔴 BLOCKING - Explicit Test Contract

Most stable locator - requires adding `data-testid` attribute to HTML.

```typescript
// ✅ CORRECT - Test ID
await page.getByTestId('submit-button').click();
await page.getByTestId('email-input').fill('test@example.com');
await expect(page.getByTestId('error-message')).toBeVisible();
```

**HTML:**
```html
<button data-testid="submit-button">Submit</button>
<input data-testid="email-input" type="email" />
<div data-testid="error-message">Invalid email</div>
```

**When to use:**
- Complex components where role-based locators are ambiguous
- Dynamic content that changes frequently
- Elements without semantic roles
- Critical test paths requiring maximum stability

### 🟡 WARNING
- **Don't overuse** → Prefer semantic locators when possible
- **Consistent naming** → Use kebab-case (e.g., `product-card-title`)
- **Avoid implementation details** → `user-menu` not `div-123`

---

## getByRole

### 🔴 BLOCKING - Accessible Elements

Locates elements by ARIA role and accessible name. Best for semantic HTML.

```typescript
// Buttons
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByRole('button', { name: /^Save/ }).click(); // Regex

// Links
await page.getByRole('link', { name: 'Home' }).click();

// Text inputs
await page.getByRole('textbox', { name: 'Email' }).fill('test@example.com');

// Checkboxes
await page.getByRole('checkbox', { name: 'Accept terms' }).check();

// Radio buttons
await page.getByRole('radio', { name: 'Credit card' }).click();

// Select dropdowns
await page.getByRole('combobox', { name: 'Country' }).selectOption('France');

// Headings
await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();
await expect(page.getByRole('heading', { level: 1 })).toHaveText('Welcome');

// Table cells
await expect(page.getByRole('cell', { name: 'Total' })).toBeVisible();

// Dialogs
await expect(page.getByRole('dialog')).toBeVisible();
```

### Common Roles

| HTML Element | Role | Example |
|--------------|------|---------|
| `<button>` | `button` | `getByRole('button', { name: 'Click me' })` |
| `<a>` | `link` | `getByRole('link', { name: 'Home' })` |
| `<input type="text">` | `textbox` | `getByRole('textbox', { name: 'Email' })` |
| `<input type="checkbox">` | `checkbox` | `getByRole('checkbox', { name: 'Agree' })` |
| `<input type="radio">` | `radio` | `getByRole('radio', { name: 'Yes' })` |
| `<select>` | `combobox` | `getByRole('combobox', { name: 'Country' })` |
| `<h1>` to `<h6>` | `heading` | `getByRole('heading', { level: 1 })` |
| `<img>` | `img` | `getByRole('img', { name: 'Logo' })` |
| `<dialog>` | `dialog` | `getByRole('dialog')` |
| `<table>` | `table` | `getByRole('table')` |

**When to use:**
- Buttons, links, form elements
- Headings, navigation
- Accessible UI components

---

## getByLabel

### 🔴 BLOCKING - Form Inputs

Locates form inputs by their associated `<label>`.

```typescript
// ✅ CORRECT - By label text
await page.getByLabel('Email address').fill('test@example.com');
await page.getByLabel('Password').fill('secret123');
await page.getByLabel('Remember me').check();
```

**HTML:**
```html
<label for="email">Email address</label>
<input id="email" type="email" />

<!-- Or implicit association -->
<label>
  Password
  <input type="password" />
</label>
```

**When to use:**
- Form inputs with visible labels
- Better than placeholder (labels are always visible)

---

## getByPlaceholder

### 🟡 WARNING - Use Sparingly

Locates inputs by placeholder attribute.

```typescript
await page.getByPlaceholder('Enter your email').fill('test@example.com');
await page.getByPlaceholder('Search products...').fill('laptop');
```

**When to use:**
- Inputs without labels (search boxes)
- Placeholder is stable and unlikely to change

**When NOT to use:**
- Prefer `getByLabel` if label exists
- Placeholders often change for UX reasons

---

## getByText

### 🔴 BLOCKING - Static Text

Locates elements containing specific text.

```typescript
// Exact match
await page.getByText('Welcome back').click();

// Partial match
await page.getByText('Welcome', { exact: false }).click();

// Regex match
await page.getByText(/welcome/i).click(); // Case-insensitive

// In specific element
await page.getByRole('main').getByText('Dashboard').click();
```

**When to use:**
- Static text content (headings, paragraphs, labels)
- Error messages, notifications
- Menu items, list items

**When NOT to use:**
- Dynamic text (user names, dates, prices)
- Text that changes based on locale

---

## getByAltText

### 🟢 BEST PRACTICE - Images

Locates images by `alt` attribute.

```typescript
await page.getByAltText('Company logo').click();
await expect(page.getByAltText('Product image')).toBeVisible();
```

**HTML:**
```html
<img src="logo.png" alt="Company logo" />
```

---

## Locator Chaining

### 🔴 BLOCKING - Scoping Locators

Combine locators to narrow down to specific elements.

```typescript
// Filter by text
const productCard = page.getByTestId('product-card').filter({ hasText: 'iPhone' });
await productCard.getByRole('button', { name: 'Add to Cart' }).click();

// Filter by child element
const row = page.getByRole('row').filter({
  has: page.getByText('Order #123')
});
await row.getByRole('button', { name: 'View' }).click();

// Filter by NOT having element
const uncheckedItems = page.getByTestId('todo-item').filter({
  hasNot: page.getByRole('checkbox', { checked: true })
});

// Nth element
await page.getByTestId('product-card').nth(0).click(); // First
await page.getByTestId('product-card').last().click(); // Last

// First/Last
await page.getByTestId('product-card').first().click();
```

---

## CSS Locators (Last Resort)

### 🔴 BLOCKING - Avoid When Possible

```typescript
// 🔴 WRONG - CSS class
await page.locator('.btn-primary').click();

// 🔴 WRONG - Complex CSS
await page.locator('div.container > form > button:nth-child(2)').click();

// 🟡 OK - When no better option exists
await page.locator('[data-custom-attr="value"]').click();
```

**When CSS is acceptable:**
- Third-party components without semantic markup
- Temporary workaround during refactoring
- Testing CSS-specific behavior

---

## XPath (Never Use)

### 🔴 BLOCKING - DON'T USE XPATH

```typescript
// ❌ NEVER DO THIS
await page.locator('//button[@type="submit"]').click();
await page.locator('//*[@id="email"]').fill('test@test.com');
```

**Why not:**
- Fragile and breaks easily
- Hard to read and maintain
- Slower than CSS/role-based locators
- Not cross-browser compatible

---

## Buy Nature Examples

### Customer Frontend

```typescript
// Login page
await page.getByLabel('Email').fill('john.doe@example.com');
await page.getByLabel('Password').fill('Str0ngP@ssword123!');
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

---

## Advanced Locator Techniques

### Locator with Multiple Filters

```typescript
const activeProducts = page
  .getByTestId('product-card')
  .filter({ hasText: 'In Stock' })
  .filter({ has: page.getByRole('button', { name: 'Add to Cart' }) });

await expect(activeProducts).toHaveCount(10);
```

### Locator with Regex

```typescript
// Match partial text
await page.getByText(/order #\d+/i).click();

// Match button starting with text
await page.getByRole('button', { name: /^Save/ }).click();
```

### Locator with Multiple Roles

```typescript
// Find heading with specific level
await page.getByRole('heading', { level: 2, name: 'Products' });

// Find checked checkbox
await page.getByRole('checkbox', { name: 'Accept terms', checked: true });
```

### Frame Locators

```typescript
// Locate element inside iframe
const frame = page.frameLocator('iframe[name="payment"]');
await frame.getByLabel('Card number').fill('4242 4242 4242 4242');
```

---

## Quick Reference

### Locator Selection Checklist

#### 🔴 BLOCKING
- [ ] Prefer `getByRole` for semantic elements
- [ ] Use `getByTestId` for complex/dynamic components
- [ ] Use `getByLabel` for form inputs
- [ ] Never use XPath
- [ ] Avoid CSS classes for styling

#### 🟡 WARNING
- [ ] `getByText` only for static content
- [ ] `getByPlaceholder` when no label exists
- [ ] CSS locators as last resort only

#### 🟢 BEST PRACTICE
- [ ] Chain locators to scope searches
- [ ] Use filters to narrow results
- [ ] Regex for flexible text matching
- [ ] Comment why CSS locator is needed (if used)

---

## Common Patterns

### Pattern: Find Within Container

```typescript
const header = page.getByRole('banner'); // <header> element
await header.getByRole('link', { name: 'Home' }).click();

const nav = page.getByRole('navigation');
await nav.getByRole('link', { name: 'Products' }).click();
```

### Pattern: Find by Multiple Criteria

```typescript
// Find submit button that is enabled
const submitButton = page
  .getByRole('button', { name: 'Submit' })
  .filter({ hasNot: page.locator('[disabled]') });
await submitButton.click();
```

### Pattern: Dynamic List Items

```typescript
// Get all product cards
const products = page.getByTestId('product-card');

// Count them
await expect(products).toHaveCount(10);

// Interact with specific one
await products.nth(2).click();

// Iterate over all
const count = await products.count();
for (let i = 0; i < count; i++) {
  const title = await products.nth(i).getByTestId('product-title').textContent();
  console.log(`Product ${i}: ${title}`);
}
```
