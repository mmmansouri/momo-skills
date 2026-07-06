# Accessibility (a11y) — E-Commerce Specifics

> **Ownership:** the WCAG AA requirements table, the 6-point quick audit, and the BLOCKING a11y rules (keyboard-reachable focus, label + alt text, error-in-text-not-color) are owned by **SKILL.md** (`## When Ensuring Accessibility (WCAG AA)`).
> Generic WCAG / ARIA / semantic-HTML / focus-trap / screen-reader knowledge is native to the model — it is **not** restated here.
> This file keeps only what is specific to an e-commerce flow.

## E-Commerce Accessibility Priorities

1. **Product search** — screen-reader users must be able to search and filter.
2. **Cart management** — announce items added / removed (`aria-live`).
3. **Checkout flow** — clear error messages, fully keyboard accessible.
4. **Payment** — secure, accessible, explicit error handling.
5. **Order confirmation** — clear success message, order details reachable.

## Example: Accessible Product Card

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
