# Color System Guide

> **Ownership:** the BLOCKING color rules (contrast ≥ 4.5:1 text / ≥ 3:1 UI, never-color-alone, test-in-grayscale) and the WCAG contrast table are owned by **SKILL.md** (`## When Working with Color`).
> Generic color theory (color psychology, dark-mode tips, common mistakes) is native to the model — it is **not** restated here.
> This file keeps the house token conventions: the `--color-{name}-{shade}` scale, the semantic-color set, and the eco-brand palette.

## Table of Contents

- [Color System Structure](#color-system-structure)
- [Semantic Color Usage](#semantic-color-usage)
- [Eco Brand Color Palette Example](#eco-brand-color-palette-example)

---

## Color System Structure

House convention: every color is a token named `--color-{name}-{shade}`, with the shade running from `50` (lightest) to `900` (darkest).

```css
:root {
  /* PRIMARY - Brand color */
  --color-primary-50: #f0fdf4;
  --color-primary-100: #dcfce7;
  --color-primary-200: #bbf7d0;
  --color-primary-300: #86efac;
  --color-primary-400: #4ade80;
  --color-primary-500: #22c55e;  /* Main brand color */
  --color-primary-600: #16a34a;  /* Hover state */
  --color-primary-700: #15803d;
  --color-primary-800: #166534;
  --color-primary-900: #14532d;

  /* NEUTRAL - Text and backgrounds */
  --color-neutral-50: #fafafa;
  --color-neutral-100: #f5f5f5;
  --color-neutral-200: #e5e5e5;
  --color-neutral-300: #d4d4d4;
  --color-neutral-400: #a3a3a3;
  --color-neutral-500: #737373;
  --color-neutral-600: #525252;
  --color-neutral-700: #404040;
  --color-neutral-800: #262626;
  --color-neutral-900: #171717;

  /* SEMANTIC - Feedback colors */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;
}
```

Shade → usage (house convention): `50-100` subtle backgrounds/hover · `200-300` borders/dividers · `400-500` accents · `500-600` main color / primary actions · `700-800` text on light backgrounds · `900` strong emphasis text.

---

## Semantic Color Usage

Each semantic color ships a base plus a `-light` and `-dark` companion token:

```css
:root {
  /* Success - confirmations, completed actions */
  --color-success: #22c55e;
  --color-success-light: #dcfce7;
  --color-success-dark: #15803d;

  /* Warning - alerts, caution */
  --color-warning: #f59e0b;
  --color-warning-light: #fef3c7;
  --color-warning-dark: #d97706;

  /* Error - failures, destructive actions */
  --color-error: #ef4444;
  --color-error-light: #fee2e2;
  --color-error-dark: #dc2626;

  /* Info - neutral information */
  --color-info: #3b82f6;
  --color-info-light: #dbeafe;
  --color-info-dark: #2563eb;
}
```

```html
<!-- Success message -->
<div class="alert alert--success">
  <svg class="icon">✓</svg>
  <p>Order placed successfully!</p>
</div>

<!-- Error message -->
<div class="alert alert--error">
  <svg class="icon">✕</svg>
  <p>Payment failed. Please try again.</p>
</div>
```

---

## Eco Brand Color Palette Example

Reference palette for an eco-friendly brand identity:

```css
:root {
  /* Primary - Nature Green */
  --brand-green-500: #22c55e;
  --brand-green-600: #16a34a;
  --brand-green-900: #14532d;

  /* Secondary - Earth Tones */
  --brand-cream: #faf8f5;
  --brand-brown: #8b7355;
  --brand-brown-dark: #5c4a3a;

  /* Accent - Natural */
  --brand-sky: #7dd3fc;
  --brand-terracotta: #ea580c;

  /* Neutral */
  --brand-white: #ffffff;
  --brand-gray-100: #f5f5f5;
  --brand-gray-900: #171717;
}
```

**Usage Guidelines:**
- **Primary Green** — CTAs, brand elements, navigation.
- **Earth Tones** — backgrounds, subtle accents.
- **Sky Blue** — information, trust elements.
- **Terracotta** — urgency, promotions (use sparingly).
