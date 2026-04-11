# Color System Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Color System Structure

A well-structured color system has clear categories and consistent naming:

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

---

## 🔴 BLOCKING Rules

| Rule | Why |
|------|-----|
| **Contrast ratio ≥ 4.5:1 for text** | WCAG AA accessibility requirement |
| **Contrast ratio ≥ 3:1 for UI elements** | Buttons, icons must be visible |
| **Don't rely on color alone** | Use icons + color for status |
| **Test in grayscale** | Hierarchy must work without color |

---

## Color Scale System

Each color should have a scale from 50 (lightest) to 900 (darkest):

| Shade | Usage |
|-------|-------|
| 50-100 | Subtle backgrounds, hover states |
| 200-300 | Borders, dividers |
| 400-500 | Accents, secondary elements |
| 500-600 | Main color, primary actions |
| 700-800 | Text on light backgrounds |
| 900 | Text, strong emphasis |

**Example in Practice:**
```css
.btn-primary {
  background-color: var(--color-primary-500); /* Main */
  color: white;
}

.btn-primary:hover {
  background-color: var(--color-primary-600); /* Darker on hover */
}

.bg-subtle {
  background-color: var(--color-primary-50); /* Very light background */
}
```

---

## Color Psychology for E-Commerce

| Color | Association | Use For | Buy Nature Context |
|-------|-------------|---------|-------------------|
| Green | Nature, eco, growth | Primary brand color | Perfect for eco-friendly products |
| Dark Green | Luxury eco, premium | Premium products | High-end sustainable items |
| Blue | Trust, stability | Payment, security | Checkout, account pages |
| Orange | Urgency, action | CTAs, sales | Limited-time offers |
| White/Cream | Clean, premium | Backgrounds | Product showcases |
| Brown/Earth | Natural, organic | Accents | Supporting brand elements |

---

## 🔴 AVOID - Common Color Mistakes

| Mistake | Why | Alternative |
|---------|-----|-------------|
| Purple gradients on white | AI slop cliché | Solid brand colors |
| Rainbow gradients | Unprofessional | 2-3 color maximum |
| Neon colors without purpose | Hurts eyes | Muted, natural tones |
| Low contrast text | Inaccessible | Test with contrast checker |
| Red/green for status only | Color blindness | Add icons/text |

---

## Semantic Color Usage

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

**Usage Example:**
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

## Contrast Requirements (WCAG AA)

| Content Type | Minimum Contrast | Example |
|--------------|------------------|---------|
| Normal text (< 18px) | 4.5:1 | Black text on white: 21:1 ✓ |
| Large text (≥ 18px) | 3:1 | Gray text on white |
| UI components (buttons, icons) | 3:1 | Button border on background |
| Decorative elements | No requirement | Background patterns |

**Testing Contrast:**
- Use browser DevTools contrast checker
- Online tool: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- Figma/Sketch plugins

---

## Dark Mode Support

```css
/* Light mode (default) */
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f5;
  --text-primary: #171717;
  --text-secondary: #737373;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #171717;
    --bg-secondary: #262626;
    --text-primary: #fafafa;
    --text-secondary: #a3a3a3;
  }
}
```

**Dark Mode Tips:**
- Don't just invert colors - adjust for comfort
- Pure black (#000) is too harsh - use #171717
- Reduce saturation of accent colors in dark mode
- Test readability in both modes

---

## Buy Nature Color Palette

Based on the brand's eco-friendly identity:

```css
:root {
  /* Primary - Nature Green */
  --bn-green-500: #22c55e;
  --bn-green-600: #16a34a;
  --bn-green-900: #14532d;

  /* Secondary - Earth Tones */
  --bn-cream: #faf8f5;
  --bn-brown: #8b7355;
  --bn-brown-dark: #5c4a3a;

  /* Accent - Natural */
  --bn-sky: #7dd3fc;
  --bn-terracotta: #ea580c;

  /* Neutral */
  --bn-white: #ffffff;
  --bn-gray-100: #f5f5f5;
  --bn-gray-900: #171717;
}
```

**Usage Guidelines:**
- **Primary Green** - CTAs, brand elements, navigation
- **Earth Tones** - Backgrounds, subtle accents
- **Sky Blue** - Information, trust elements
- **Terracotta** - Urgency, promotions (use sparingly)

---

## Color Application Checklist

Before finalizing colors:

- [ ] All text meets 4.5:1 contrast ratio
- [ ] UI elements meet 3:1 contrast ratio
- [ ] Tested in grayscale (hierarchy still clear)
- [ ] Status indicators have icons + color
- [ ] Dark mode considered (if applicable)
- [ ] Brand colors used consistently
- [ ] Semantic colors used correctly (success/error/warning/info)
- [ ] No reliance on color alone for meaning
