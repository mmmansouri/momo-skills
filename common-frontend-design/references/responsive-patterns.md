# Responsive Design Patterns

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Breakpoints

Use mobile-first breakpoints for progressive enhancement:

```css
/* Mobile-first approach */
:root {
  --breakpoint-sm: 640px;   /* Large phones (landscape) */
  --breakpoint-md: 768px;   /* Tablets */
  --breakpoint-lg: 1024px;  /* Laptops */
  --breakpoint-xl: 1280px;  /* Desktops */
  --breakpoint-2xl: 1536px; /* Large screens */
}
```

**Why these sizes?**
- **640px** - iPhone 12 Pro Max landscape (428px) + buffer
- **768px** - iPad portrait (768px)
- **1024px** - iPad landscape (1024px)
- **1280px** - Common laptop (1366px)
- **1536px** - Large desktop monitors

---

## 🔴 BLOCKING Rules

| Rule | Why |
|------|-----|
| **Mobile-first CSS** | Start small, enhance for larger screens |
| **Test on real devices** | Emulators miss real touch/scroll issues |
| **Touch targets 44px+** | Fingers are not precise pointers |
| **No horizontal scroll** | Breaks mobile UX completely |

---

## Mobile-First Approach

**CORRECT - Start small, add complexity:**
```css
/* Base styles (mobile) */
.card {
  padding: var(--space-4);
  font-size: 1rem;
}

/* Enhance for tablet */
@media (min-width: 768px) {
  .card {
    padding: var(--space-6);
    font-size: 1.125rem;
  }
}

/* Enhance for desktop */
@media (min-width: 1024px) {
  .card {
    padding: var(--space-8);
    font-size: 1.25rem;
  }
}
```

**WRONG - Desktop-first (requires overrides):**
```css
/* DON'T DO THIS */
.card {
  padding: 64px; /* Desktop size */
  font-size: 1.5rem;
}

@media (max-width: 768px) {
  .card {
    padding: 16px; /* Have to override */
    font-size: 1rem;
  }
}
```

---

## Responsive Layout Patterns

### Stack to Sidebar

```css
/* Mobile: stack vertically */
.layout {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

/* Desktop: sidebar + main */
@media (min-width: 1024px) {
  .layout {
    flex-direction: row;
  }

  .sidebar {
    width: 250px;
    flex-shrink: 0;
  }

  .main {
    flex: 1;
  }
}
```

### Responsive Grid

```css
/* Auto-responsive grid */
.grid {
  display: grid;
  gap: var(--space-6);

  /* Mobile: 1 column */
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .grid {
    /* Tablet: 2 columns */
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .grid {
    /* Desktop: 3 columns */
    grid-template-columns: repeat(3, 1fr);
  }
}

/* OR use auto-fit (dynamic columns) */
.auto-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--space-6);
}
```

### Collapsible Navigation

```html
<!-- Mobile: hamburger menu -->
<nav class="nav">
  <button class="nav__toggle" aria-label="Toggle menu">
    ☰
  </button>

  <ul class="nav__menu">
    <li><a href="...">Home</a></li>
    <li><a href="...">Products</a></li>
    <li><a href="...">About</a></li>
  </ul>
</nav>
```

```css
/* Mobile: hidden menu */
.nav__menu {
  display: none;
  position: fixed;
  inset: 0;
  background: white;
  padding: var(--space-6);
}

.nav__menu.is-open {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* Desktop: horizontal menu */
@media (min-width: 768px) {
  .nav__toggle {
    display: none;
  }

  .nav__menu {
    display: flex;
    flex-direction: row;
    gap: var(--space-6);
    position: static;
    padding: 0;
  }
}
```

---

## Touch Targets

### 🔴 BLOCKING - Minimum Touch Target Size

**44x44px minimum** (Apple & Google guidelines)

```css
/* Correct: generous touch targets */
.btn {
  min-width: 44px;
  min-height: 44px;
  padding: var(--space-3) var(--space-5);
}

/* Icon-only button */
.icon-btn {
  width: 44px;
  height: 44px;
  padding: var(--space-2);
}

/* Small text link with extended tap area */
.link--small {
  position: relative;
  padding: var(--space-3);
}

.link--small::after {
  content: "";
  position: absolute;
  inset: -8px; /* Extends tap area */
}
```

### Touch-Friendly Spacing

```css
/* Mobile: more spacing between interactive elements */
.button-group {
  display: flex;
  gap: var(--space-4); /* 16px */
}

@media (min-width: 1024px) {
  .button-group {
    gap: var(--space-3); /* 12px on desktop (mouse is precise) */
  }
}
```

---

## Responsive Typography

### Fluid Typography

```css
/* Scales smoothly between viewports */
:root {
  --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  --text-lg: clamp(1.25rem, 1.15rem + 0.5vw, 1.5rem);
  --text-xl: clamp(1.5rem, 1.35rem + 0.75vw, 2rem);
}

body {
  font-size: var(--text-base);
}

h1 {
  font-size: var(--text-xl);
}
```

### Responsive Headings

```css
/* Mobile: smaller headings */
h1 {
  font-size: 2rem; /* 32px */
  line-height: 1.2;
}

@media (min-width: 768px) {
  h1 {
    font-size: 2.5rem; /* 40px */
  }
}

@media (min-width: 1024px) {
  h1 {
    font-size: 3rem; /* 48px */
  }
}
```

---

## Responsive Images

### Responsive Image Techniques

```html
<!-- Srcset for different screen densities -->
<img
  src="product.jpg"
  srcset="product.jpg 1x, product@2x.jpg 2x"
  alt="Product name"
/>

<!-- Picture element for art direction -->
<picture>
  <source
    media="(min-width: 1024px)"
    srcset="product-wide.jpg"
  />
  <source
    media="(min-width: 768px)"
    srcset="product-medium.jpg"
  />
  <img src="product-small.jpg" alt="Product name" />
</picture>

<!-- Lazy loading -->
<img
  src="product.jpg"
  loading="lazy"
  alt="Product name"
/>
```

### Responsive Background Images

```css
.hero {
  background-image: url('hero-small.jpg');
  background-size: cover;
  background-position: center;
}

@media (min-width: 768px) {
  .hero {
    background-image: url('hero-medium.jpg');
  }
}

@media (min-width: 1024px) {
  .hero {
    background-image: url('hero-large.jpg');
  }
}
```

---

## Container Queries (Modern Approach)

```css
/* Component adapts to its container, not viewport */
.card-container {
  container-type: inline-size;
  container-name: card;
}

.card {
  padding: var(--space-4);
}

/* When container is > 400px */
@container card (min-width: 400px) {
  .card {
    display: flex;
    gap: var(--space-6);
    padding: var(--space-6);
  }

  .card__image {
    width: 200px;
  }
}
```

---

## Testing Responsive Design

### Device Testing Checklist

- [ ] **iPhone SE (375px)** - Smallest modern phone
- [ ] **iPhone 12 Pro (390px)** - Common size
- [ ] **iPhone 12 Pro Max (428px)** - Large phone
- [ ] **iPad Mini (768px)** - Small tablet
- [ ] **iPad Pro (1024px)** - Large tablet
- [ ] **Laptop (1366px)** - Common laptop
- [ ] **Desktop (1920px)** - Full HD monitor

### Real Device Testing

**🟡 WARNING:** Emulators miss these issues:
- Touch scroll performance
- Actual touch target usability
- Font rendering differences
- Browser-specific bugs
- Real network conditions

**Tools for remote testing:**
- **BrowserStack** - Test on real devices remotely
- **LambdaTest** - Cross-browser testing
- **Your actual phone** - Connect via USB debugging

---

## Common Responsive Patterns

### Hide/Show Content

```css
/* Show only on mobile */
.mobile-only {
  display: block;
}

@media (min-width: 768px) {
  .mobile-only {
    display: none;
  }
}

/* Show only on desktop */
.desktop-only {
  display: none;
}

@media (min-width: 768px) {
  .desktop-only {
    display: block;
  }
}
```

### Responsive Tables

```html
<!-- Mobile: card layout -->
<div class="table-responsive">
  <table>
    <thead>
      <tr>
        <th>Product</th>
        <th>Price</th>
        <th>Quantity</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td data-label="Product">T-Shirt</td>
        <td data-label="Price">$29.99</td>
        <td data-label="Quantity">2</td>
      </tr>
    </tbody>
  </table>
</div>
```

```css
/* Mobile: stack table rows as cards */
@media (max-width: 767px) {
  table, thead, tbody, th, td, tr {
    display: block;
  }

  thead {
    display: none; /* Hide header on mobile */
  }

  tr {
    margin-bottom: var(--space-4);
    border: 1px solid var(--color-neutral-200);
    border-radius: var(--radius-md);
  }

  td {
    display: flex;
    justify-content: space-between;
    padding: var(--space-3);
    border-bottom: 1px solid var(--color-neutral-100);
  }

  td::before {
    content: attr(data-label);
    font-weight: 600;
  }
}
```

---

## Performance Considerations

### Lazy Load Images

```html
<img
  src="placeholder.jpg"
  data-src="product.jpg"
  loading="lazy"
  alt="Product name"
/>
```

### Responsive Embeds

```css
/* 16:9 aspect ratio container */
.embed-container {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%; /* 16:9 ratio */
}

.embed-container iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
```

---

## Responsive Design Checklist

Before shipping:

- [ ] Tested on 320px width (smallest phones)
- [ ] No horizontal scrolling at any breakpoint
- [ ] Touch targets are 44x44px minimum
- [ ] Images are responsive (srcset, picture, lazy loading)
- [ ] Typography scales appropriately
- [ ] Navigation is accessible on mobile
- [ ] Forms are easy to use on mobile
- [ ] Performance is good on 3G (mobile network)
- [ ] Tested on real devices (not just emulator)
- [ ] Works in both portrait and landscape

---

## Buy Nature Specific Patterns

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
/* Mobile: full-width cart button */
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
