# Component Design Patterns

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Button Hierarchy

Visual hierarchy guides users to the most important actions:

```
┌─────────────────────────────────────────────────────────┐
│  PRIMARY BUTTON                                          │
│  Filled, brand color, high contrast                     │
│  Use: Main action per view (Add to Cart, Submit)        │
├─────────────────────────────────────────────────────────┤
│  SECONDARY BUTTON                                        │
│  Outlined or muted fill                                 │
│  Use: Alternative actions (Learn More, Details)         │
├─────────────────────────────────────────────────────────┤
│  TERTIARY / GHOST BUTTON                                │
│  Text only or minimal styling                           │
│  Use: Dismissive actions (Cancel, Skip)                 │
├─────────────────────────────────────────────────────────┤
│  DESTRUCTIVE BUTTON                                     │
│  Red/danger color                                       │
│  Use: Dangerous actions (Delete, Remove)                │
└─────────────────────────────────────────────────────────┘
```

---

## 🔴 BLOCKING - Button Rules

| Rule | Why |
|------|-----|
| **One primary CTA per view** | Clear action hierarchy - don't confuse users |
| **Button labels are verbs** | "Add to Cart" not "Cart" - action-oriented |
| **Loading states for async** | User knows action is processing |
| **Disabled state is clear** | But don't disable without explaining why |

---

## Button Implementation

```css
/* Base button */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);

  min-height: 44px;
  padding: var(--space-3) var(--space-5);

  font-family: var(--font-body);
  font-weight: 600;
  font-size: 1rem;

  border: 2px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;

  transition: all var(--transition-fast);
}

/* Primary - main action */
.btn--primary {
  background-color: var(--color-primary-500);
  color: white;
}

.btn--primary:hover {
  background-color: var(--color-primary-600);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* Secondary - alternative action */
.btn--secondary {
  background-color: transparent;
  color: var(--color-primary-600);
  border-color: var(--color-primary-500);
}

.btn--secondary:hover {
  background-color: var(--color-primary-50);
}

/* Tertiary/Ghost - low emphasis */
.btn--tertiary {
  background-color: transparent;
  color: var(--color-neutral-700);
}

.btn--tertiary:hover {
  background-color: var(--color-neutral-100);
}

/* Destructive - dangerous actions */
.btn--destructive {
  background-color: var(--color-error);
  color: white;
}

/* States */
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.btn--loading {
  position: relative;
  color: transparent;
}

.btn--loading::after {
  content: "";
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

---

## Form Components

### Input Fields

```css
.input {
  width: 100%;
  padding: var(--space-3);

  font-family: var(--font-body);
  font-size: 1rem;

  border: 2px solid var(--color-neutral-300);
  border-radius: var(--radius-md);

  transition: border-color var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px var(--color-primary-100);
}

.input--error {
  border-color: var(--color-error);
}

.input:disabled {
  background-color: var(--color-neutral-100);
  cursor: not-allowed;
}
```

### Form Field Structure

```html
<div class="form-field">
  <label for="email" class="form-field__label">
    Email Address
    <span class="form-field__required">*</span>
  </label>

  <input
    type="email"
    id="email"
    class="input"
    aria-describedby="email-error"
    required
  />

  <p id="email-error" class="form-field__error">
    Please enter a valid email address
  </p>

  <p class="form-field__hint">
    We'll never share your email
  </p>
</div>
```

---

## Card Components

### Product Card

```html
<article class="card card--product">
  <img src="..." alt="Product name" class="card__image" />

  <div class="card__content">
    <h3 class="card__title">Product Name</h3>
    <p class="card__price">$29.99</p>
    <p class="card__description">Brief description...</p>
  </div>

  <div class="card__actions">
    <button class="btn btn--primary">Add to Cart</button>
    <button class="btn btn--tertiary">Details</button>
  </div>
</article>
```

```css
.card {
  display: flex;
  flex-direction: column;

  background: white;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  overflow: hidden;

  transition: transform var(--transition-normal),
              box-shadow var(--transition-normal);
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.card__image {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
}

.card__content {
  flex: 1;
  padding: var(--space-6);
}

.card__actions {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-neutral-200);
}
```

---

## State Patterns

### Loading State

```html
<div class="loading-state">
  <div class="spinner"></div>
  <p>Loading products...</p>
</div>
```

### Empty State

```html
<div class="empty-state">
  <svg class="empty-state__icon">...</svg>
  <h3 class="empty-state__title">No products found</h3>
  <p class="empty-state__message">Try adjusting your filters</p>
  <button class="btn btn--primary">Clear Filters</button>
</div>
```

### Error State

```html
<div class="error-state">
  <svg class="error-state__icon">⚠️</svg>
  <h3 class="error-state__title">Something went wrong</h3>
  <p class="error-state__message">We couldn't load the products</p>
  <button class="btn btn--primary">Try Again</button>
</div>
```

---

## Modal/Dialog Pattern

```html
<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <div class="modal__backdrop"></div>

  <div class="modal__container">
    <div class="modal__header">
      <h2 id="modal-title">Confirm Action</h2>
      <button class="modal__close" aria-label="Close">×</button>
    </div>

    <div class="modal__content">
      <p>Are you sure you want to delete this item?</p>
    </div>

    <div class="modal__footer">
      <button class="btn btn--tertiary">Cancel</button>
      <button class="btn btn--destructive">Delete</button>
    </div>
  </div>
</div>
```

```css
.modal {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);

  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
}

.modal__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}

.modal__container {
  position: relative;
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-neutral-200);
}

.modal__content {
  padding: var(--space-6);
}

.modal__footer {
  display: flex;
  gap: var(--space-3);
  justify-content: flex-end;
  padding: var(--space-6);
  border-top: 1px solid var(--color-neutral-200);
}
```

---

## Accessibility Requirements

### 🔴 BLOCKING - Component Accessibility

| Component | Requirements |
|-----------|-------------|
| **Buttons** | `<button>` tag, clear focus state, keyboard accessible |
| **Forms** | Labels linked with `for`/`id`, error messages with `aria-describedby` |
| **Modals** | `role="dialog"`, `aria-modal="true"`, focus trap, Escape to close |
| **Images** | Meaningful `alt` text, decorative images use `alt=""` |
| **Links** | Descriptive text (not "click here"), underlined or clearly styled |

### Focus Management

```css
/* Visible focus indicator */
*:focus-visible {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}

/* Custom focus for buttons */
.btn:focus-visible {
  outline: 3px solid var(--color-primary-500);
  outline-offset: 2px;
}
```

---

## Component Checklist

Before shipping a component:

- [ ] Works without JavaScript (progressive enhancement)
- [ ] Keyboard accessible (Tab, Enter, Escape work)
- [ ] Focus states are visible
- [ ] Screen reader friendly (ARIA labels, semantic HTML)
- [ ] Loading states implemented
- [ ] Error states designed
- [ ] Empty states designed
- [ ] Responsive on all screen sizes
- [ ] Touch targets ≥ 44px on mobile
- [ ] Color contrast meets WCAG AA
