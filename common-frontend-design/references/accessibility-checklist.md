# Accessibility (a11y) Checklist

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## 🔴 BLOCKING - WCAG AA Requirements

WCAG (Web Content Accessibility Guidelines) Level AA is the legal standard in many countries.

| Requirement | How to Check | Example |
|-------------|--------------|---------|
| **Keyboard navigation** | Tab through all interactive elements | All buttons, links, forms accessible via Tab |
| **Focus indicators** | Visible focus ring on all focusable elements | 2px outline, 3:1 contrast ratio |
| **Alt text** | All meaningful images have descriptions | `<img src="..." alt="Product name">` |
| **Form labels** | Every input has associated label | `<label for="email">Email</label>` |
| **Color contrast** | 4.5:1 for text, 3:1 for UI | Use contrast checker tools |
| **Error identification** | Errors described in text, not just color | "Email is required" + red icon |

---

## Quick Accessibility Test

Run this checklist on every page/component:

```markdown
### Keyboard Navigation
- [ ] Can you Tab through the entire page?
- [ ] Can you Shift+Tab to go backwards?
- [ ] Can you activate buttons/links with Enter/Space?
- [ ] Can you close modals with Escape?
- [ ] Is the tab order logical (top to bottom, left to right)?

### Visual Feedback
- [ ] Is focus always visible?
- [ ] Are focus states clearly styled (not browser default)?
- [ ] Do hover and focus states look similar?

### Forms
- [ ] Can you use the form with keyboard only?
- [ ] Are error messages announced to screen readers?
- [ ] Do required fields have visual + programmatic indicators?
- [ ] Are error messages descriptive (not just "Invalid")?

### Content
- [ ] Does the page make sense with images off?
- [ ] Does it work at 200% zoom?
- [ ] Can you read all text without zooming?
- [ ] Is there enough contrast between text and background?

### Screen Reader
- [ ] Does screen reader announce content logically?
- [ ] Are headings properly nested (h1 → h2 → h3)?
- [ ] Are lists marked up as `<ul>` or `<ol>`?
- [ ] Do buttons/links have clear names?
```

---

## Semantic HTML

Use the right HTML element for the job:

| Use This | Not This | Why |
|----------|----------|-----|
| `<button>` | `<div onclick="...">` | Buttons get keyboard support free |
| `<a href="...">` | `<span onclick="...">` | Links are semantically meaningful |
| `<nav>` | `<div class="nav">` | Screen readers announce navigation |
| `<main>` | `<div class="main">` | Helps screen reader users skip to content |
| `<article>` | `<div class="article">` | Indicates independent content |
| `<label>` | `<span>` next to input | Programmatically links label to input |

---

## ARIA Attributes (Use Sparingly)

**Rule:** First rule of ARIA is don't use ARIA - use semantic HTML first.

### When ARIA is Needed

```html
<!-- Modal dialog -->
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
>
  <h2 id="modal-title">Confirm Action</h2>
  ...
</div>

<!-- Tab interface -->
<div role="tablist">
  <button role="tab" aria-selected="true" aria-controls="panel-1">
    Tab 1
  </button>
  <button role="tab" aria-selected="false" aria-controls="panel-2">
    Tab 2
  </button>
</div>
<div id="panel-1" role="tabpanel">...</div>
<div id="panel-2" role="tabpanel" hidden>...</div>

<!-- Loading state -->
<div aria-live="polite" aria-busy="true">
  Loading products...
</div>

<!-- Error message linked to input -->
<label for="email">Email</label>
<input
  id="email"
  type="email"
  aria-describedby="email-error"
  aria-invalid="true"
/>
<p id="email-error">Please enter a valid email</p>
```

### Common ARIA Attributes

| Attribute | Usage |
|-----------|-------|
| `aria-label` | Invisible label for screen readers |
| `aria-labelledby` | Points to visible label element |
| `aria-describedby` | Additional description (error messages, hints) |
| `aria-hidden="true"` | Hides decorative elements from screen readers |
| `aria-live="polite"` | Announces dynamic content changes |
| `aria-invalid="true"` | Marks invalid form fields |
| `aria-required="true"` | Marks required form fields |

---

## Keyboard Navigation Patterns

### Focus Management

```javascript
// Trap focus in modal
const modal = document.querySelector('.modal');
const focusableElements = modal.querySelectorAll(
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
);
const firstElement = focusableElements[0];
const lastElement = focusableElements[focusableElements.length - 1];

modal.addEventListener('keydown', (e) => {
  if (e.key === 'Tab') {
    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  }

  if (e.key === 'Escape') {
    closeModal();
  }
});
```

### Skip Links

```html
<!-- First element in <body> -->
<a href="#main-content" class="skip-link">
  Skip to main content
</a>

...

<main id="main-content">
  <!-- Page content -->
</main>
```

```css
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  padding: 8px;
  background: var(--color-primary-500);
  color: white;
  z-index: 1000;
}

.skip-link:focus {
  top: 0;
}
```

---

## Screen Reader Considerations

### Announce Dynamic Content

```html
<!-- Polite: waits for user to finish -->
<div aria-live="polite" role="status">
  3 items added to cart
</div>

<!-- Assertive: interrupts immediately (use sparingly) -->
<div aria-live="assertive" role="alert">
  Payment failed. Please try again.
</div>
```

### Hide Decorative Content

```html
<!-- Decorative icon (hidden from screen readers) -->
<button>
  <svg aria-hidden="true">...</svg>
  Add to Cart
</button>

<!-- Meaningful icon (needs label) -->
<button aria-label="Close">
  <svg aria-hidden="true">×</svg>
</button>
```

### Provide Alternative Text

```html
<!-- Product image -->
<img
  src="product.jpg"
  alt="Organic cotton t-shirt in forest green, front view"
/>

<!-- Decorative image -->
<img
  src="pattern.jpg"
  alt=""
  role="presentation"
/>

<!-- Complex image (chart, infographic) -->
<figure>
  <img src="sales-chart.jpg" alt="Sales chart" />
  <figcaption>
    Sales increased by 30% in Q4 2025, reaching $2.5M total revenue.
  </figcaption>
</figure>
```

---

## Color & Contrast

### Contrast Ratios (WCAG AA)

| Content Type | Minimum Ratio | Example |
|--------------|---------------|---------|
| Normal text (< 18px) | 4.5:1 | #595959 on white = 4.5:1 |
| Large text (≥ 18px or bold ≥ 14px) | 3:1 | #767676 on white = 3:1 |
| UI components (buttons, icons) | 3:1 | Border/icon on background |
| Decorative elements | No requirement | Background patterns |

### Testing Tools

- **Browser DevTools:** Chrome/Firefox have built-in contrast checkers
- **Online:** [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- **Figma/Sketch:** Plugins available
- **Automated:** axe DevTools, Lighthouse

### Don't Rely on Color Alone

```html
<!-- WRONG: Color-only status -->
<span style="color: red;">Error</span>
<span style="color: green;">Success</span>

<!-- CORRECT: Color + icon + text -->
<div class="alert alert--error">
  <svg class="icon" aria-hidden="true">⚠️</svg>
  <p>Payment failed. Please try again.</p>
</div>

<div class="alert alert--success">
  <svg class="icon" aria-hidden="true">✓</svg>
  <p>Order placed successfully!</p>
</div>
```

---

## Motion & Animation

### Respect User Preferences

```css
/* Reduce motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Safe Animation Practices

- **Duration:** 150-300ms for UI (longer feels sluggish)
- **Purpose:** Animate to guide attention, not for decoration
- **Avoid:** Flashing content (seizure risk if > 3 flashes/second)

---

## Complete Accessibility Checklist

### Perceivable
- [ ] Text has 4.5:1 contrast ratio
- [ ] UI components have 3:1 contrast ratio
- [ ] Images have alt text
- [ ] Color is not the only way to convey information
- [ ] Videos have captions

### Operable
- [ ] All functionality available via keyboard
- [ ] No keyboard traps
- [ ] Focus indicators are visible
- [ ] Skip links provided
- [ ] Enough time to read/interact
- [ ] No flashing content

### Understandable
- [ ] Language declared in HTML (`<html lang="en">`)
- [ ] Navigation is consistent across pages
- [ ] Form errors are clearly described
- [ ] Instructions are provided for complex interactions
- [ ] Headings are properly nested (h1 → h2 → h3)

### Robust
- [ ] Valid HTML
- [ ] ARIA used correctly
- [ ] Works with assistive technologies
- [ ] Works without JavaScript (progressive enhancement)
- [ ] Works at 200% zoom

---

## Testing Tools

| Tool | Purpose |
|------|---------|
| **axe DevTools** | Automated accessibility testing (browser extension) |
| **Lighthouse** | Built into Chrome DevTools |
| **WAVE** | Visual feedback on accessibility issues |
| **NVDA/JAWS** | Windows screen readers |
| **VoiceOver** | macOS/iOS screen reader (Cmd+F5) |
| **Keyboard only** | Unplug mouse, try using the site |

---

## Buy Nature Specific Considerations

### E-Commerce Accessibility Priorities

1. **Product search** - Screen reader users must be able to search and filter
2. **Cart management** - Announce items added/removed
3. **Checkout flow** - Clear error messages, keyboard accessible
4. **Payment** - Secure, accessible, error handling
5. **Order confirmation** - Clear success message, details accessible

### Example: Accessible Product Card

```html
<article class="product-card">
  <img
    src="product.jpg"
    alt="Organic cotton t-shirt in forest green"
  />

  <h3 class="product-card__name">Organic Cotton T-Shirt</h3>

  <p class="product-card__price">
    <span aria-label="Price">$29.99</span>
  </p>

  <button
    class="btn btn--primary"
    aria-label="Add Organic Cotton T-Shirt to cart"
  >
    Add to Cart
  </button>
</article>
```
