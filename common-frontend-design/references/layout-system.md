# Layout & Spacing System

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Spacing Scale (8px Base)

A consistent spacing system creates visual harmony and speeds up development:

```css
:root {
  /* Base unit: 8px */
  --space-1: 0.25rem;  /* 4px - Tiny gaps */
  --space-2: 0.5rem;   /* 8px - Small gaps */
  --space-3: 0.75rem;  /* 12px - Compact spacing */
  --space-4: 1rem;     /* 16px - Default spacing */
  --space-5: 1.25rem;  /* 20px - Comfortable spacing */
  --space-6: 1.5rem;   /* 24px - Medium spacing */
  --space-8: 2rem;     /* 32px - Large spacing */
  --space-10: 2.5rem;  /* 40px - XL spacing */
  --space-12: 3rem;    /* 48px - Section spacing */
  --space-16: 4rem;    /* 64px - Hero spacing */
  --space-20: 5rem;    /* 80px - Major sections */
}
```

**Why 8px base?**
- Most screen sizes are divisible by 8
- Aligns with common UI component sizes
- Easy to scale (4px increments)
- Industry standard (iOS, Material Design)

---

## 🔴 BLOCKING Rules

| Rule | Why |
|------|-----|
| **Consistent spacing** | Use scale values, never arbitrary numbers |
| **Generous whitespace** | Improves readability and focus |
| **Mobile-first breakpoints** | Most users are mobile |
| **Touch targets ≥ 44px** | Apple/Google accessibility requirement |

---

## Spacing Usage Guide

| Size | Usage Example |
|------|---------------|
| 4px (space-1) | Icon-text gap, tight lists |
| 8px (space-2) | Between related elements (label + input) |
| 12px (space-3) | Compact card padding |
| 16px (space-4) | Default element spacing, button padding |
| 24px (space-6) | Card padding, section margins |
| 32px (space-8) | Between sections |
| 48px (space-12) | Major page sections |
| 64px (space-16) | Hero sections, page headers |

---

## Grid System

### Container Widths

```css
/* Fluid container with max width */
.container {
  --max-width: 1280px;
  width: min(100% - 2rem, var(--max-width));
  margin-inline: auto;
}

/* Narrow container for content */
.container--narrow {
  --max-width: 768px;
  width: min(100% - 2rem, var(--max-width));
  margin-inline: auto;
}

/* Wide container for dashboards */
.container--wide {
  --max-width: 1536px;
  width: min(100% - 2rem, var(--max-width));
  margin-inline: auto;
}
```

### 12-Column Grid

```css
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--space-6); /* 24px */
}

/* Span utilities */
.col-span-1 { grid-column: span 1; }
.col-span-2 { grid-column: span 2; }
.col-span-3 { grid-column: span 3; }
.col-span-4 { grid-column: span 4; }
.col-span-6 { grid-column: span 6; }
.col-span-8 { grid-column: span 8; }
.col-span-12 { grid-column: span 12; }
```

**Example Usage:**
```html
<div class="grid">
  <!-- Sidebar + Main content -->
  <aside class="col-span-3">Sidebar</aside>
  <main class="col-span-9">Content</main>
</div>

<div class="grid">
  <!-- 3-column product grid -->
  <div class="col-span-4">Product 1</div>
  <div class="col-span-4">Product 2</div>
  <div class="col-span-4">Product 3</div>
</div>
```

---

## Flexbox Layouts

```css
/* Common flex patterns */
.flex-row {
  display: flex;
  gap: var(--space-4);
}

.flex-col {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
```

---

## Whitespace Strategy

**The Golden Rule:** Whitespace is not wasted space - it's a design tool.

### Vertical Rhythm

```css
/* Consistent vertical spacing */
.content > * + * {
  margin-top: var(--space-6); /* 24px between elements */
}

.content h2 {
  margin-top: var(--space-12); /* 48px before new section */
}

.content p {
  margin-top: var(--space-4); /* 16px between paragraphs */
}
```

### Horizontal Spacing

```css
/* Card with generous padding */
.card {
  padding: var(--space-6); /* 24px on mobile */
}

@media (min-width: 768px) {
  .card {
    padding: var(--space-8); /* 32px on desktop */
  }
}
```

---

## Responsive Layout Patterns

### Stack to Row

```css
/* Mobile: stacked, Desktop: side-by-side */
.responsive-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

@media (min-width: 768px) {
  .responsive-grid {
    flex-direction: row;
    gap: var(--space-6);
  }
}
```

### Responsive Grid Columns

```css
/* Auto-fit columns */
.auto-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--space-6);
}

/* Result:
   Mobile: 1 column
   Tablet: 2 columns
   Desktop: 3-4 columns
*/
```

---

## Touch Target Sizes

**🔴 BLOCKING:** All interactive elements MUST be at least 44x44px on mobile.

```css
/* Minimum touch target */
.btn {
  min-width: 44px;
  min-height: 44px;
  padding: var(--space-3) var(--space-5);
}

/* Icon button with proper spacing */
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: var(--space-2);
}
```

---

## Z-Index Scale

Avoid z-index chaos with a predefined scale:

```css
:root {
  --z-base: 1;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-overlay: 300;
  --z-modal: 400;
  --z-toast: 500;
  --z-tooltip: 600;
}
```

**Usage:**
- **Base (1):** Default stacking
- **Dropdown (100):** Menus, select dropdowns
- **Sticky (200):** Sticky headers/footers
- **Overlay (300):** Modal backdrops
- **Modal (400):** Dialog boxes
- **Toast (500):** Notifications
- **Tooltip (600):** Always on top

---

## Common Layout Patterns

### Card Layout

```css
.card {
  background: white;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: var(--space-6);

  /* Prevent content overflow */
  overflow: hidden;
}

.card__header {
  margin-bottom: var(--space-4);
}

.card__footer {
  margin-top: var(--space-6);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-neutral-200);
}
```

### Header Layout

```css
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  background: white;
  box-shadow: var(--shadow-sm);
}

.header__logo {
  height: 40px;
}

.header__nav {
  display: flex;
  gap: var(--space-6);
}
```

### Section Spacing

```css
.section {
  padding-block: var(--space-12); /* 48px top/bottom */
}

@media (min-width: 1024px) {
  .section {
    padding-block: var(--space-20); /* 80px on desktop */
  }
}
```

---

## Layout Checklist

Before finalizing layout:

- [ ] Spacing uses defined scale (no arbitrary values)
- [ ] Touch targets are 44x44px minimum on mobile
- [ ] Content max-width prevents overly wide text
- [ ] Generous whitespace around elements
- [ ] Mobile-first responsive design
- [ ] Grid/flex gaps are consistent
- [ ] Z-index uses predefined scale
- [ ] Tested on 320px width (small phones)
- [ ] No horizontal scrolling at any breakpoint
