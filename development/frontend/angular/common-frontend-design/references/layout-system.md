# Layout & Spacing System

> **Ownership:** the BLOCKING layout rules (spacing-scale-exclusively, touch targets ≥ 44 px, generous whitespace, mobile-first) are owned by **SKILL.md** (`## When Composing Layouts`). Responsive layout patterns live in [responsive-patterns.md](responsive-patterns.md); common component layouts (card, header) live in [component-patterns.md](component-patterns.md). Generic flexbox utilities are native to the model.
> This file keeps the house token scales: spacing, the grid, whitespace rhythm, and the z-index tiers.

## Table of Contents

- [Spacing Scale (8px Base)](#spacing-scale-8px-base)
- [Spacing Usage Guide](#spacing-usage-guide)
- [Grid System](#grid-system)
- [Whitespace Strategy](#whitespace-strategy)
- [Z-Index Scale](#z-index-scale)

---

## Spacing Scale (8px Base)

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

House convention: 8 px base (most screen sizes divide by 8, aligns with common component sizes, matches iOS / Material). Always pick a scale token, never an arbitrary px value.

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

## Whitespace Strategy

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
