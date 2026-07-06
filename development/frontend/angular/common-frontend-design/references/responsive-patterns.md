# Responsive Design Patterns

> **Ownership:** the BLOCKING responsive rules (mobile-first CSS, no horizontal scroll, touch targets ≥ 44 px, test on real devices) and the breakpoint doctrine are owned by **SKILL.md** (`## When Building Responsive Layouts`).
> Generic responsive techniques (mobile-first media queries, hamburger nav, `srcset` / `<picture>`, container queries, responsive tables, fluid typography) are native to the model — they are **not** restated here.
> This file keeps the house breakpoint tokens and the concrete e-commerce layout patterns.

## Breakpoints

```css
/* Mobile-first breakpoint tokens */
:root {
  --breakpoint-sm: 640px;   /* Large phones (landscape) */
  --breakpoint-md: 768px;   /* Tablets */
  --breakpoint-lg: 1024px;  /* Laptops */
  --breakpoint-xl: 1280px;  /* Desktops */
  --breakpoint-2xl: 1536px; /* Large screens */
}
```

House rationale: `640px` = large phone landscape + buffer · `768px` = iPad portrait · `1024px` = iPad landscape · `1280px` = common laptop · `1536px` = large desktop.

---

## E-Commerce Responsive Patterns

### Product Grid

```css
/* Mobile: 1 column */
.product-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-6);
}

/* Tablet: 2 columns */
@media (min-width: 640px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop: 3-4 columns */
@media (min-width: 1024px) {
  .product-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1280px) {
  .product-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

### Mobile-First Cart

```css
/* Mobile: full-width fixed cart button */
.cart-button {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: var(--space-4);
  background: white;
  box-shadow: var(--shadow-lg);
}

/* Desktop: inline cart button */
@media (min-width: 1024px) {
  .cart-button {
    position: static;
    box-shadow: none;
  }
}
```
