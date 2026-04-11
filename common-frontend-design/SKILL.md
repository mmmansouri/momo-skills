---
name: common-frontend-design
description: >-
  Frontend design and UX best practices. Use when: designing user interfaces,
  creating components with high visual quality, implementing responsive layouts,
  choosing typography and color schemes, or building accessible, user-friendly experiences.
  Contains both pure design discipline and practical implementation guidance.
---

# Frontend Design & UX Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

# Part 1: Design Discipline (Framework-Agnostic)

## Design Thinking Process

Before writing any code, understand the context and commit to a clear aesthetic direction:

### 1. Purpose Analysis

| Question | Why It Matters |
|----------|----------------|
| Who uses this interface? | Demographics affect design choices |
| What problem does it solve? | Guides feature prioritization |
| What's the emotional goal? | Trust? Excitement? Calm? |
| What's the context of use? | Mobile? Desktop? In a hurry? |

### 2. Aesthetic Direction

Choose a **bold, intentional** direction. Avoid generic "safe" designs.

| Direction | Characteristics | When to Use |
|-----------|-----------------|-------------|
| Minimalist | White space, simple typography | Professional services, luxury |
| Maximalist | Rich textures, bold colors | Creative, entertainment |
| Brutalist | Raw, exposed structure | Tech-forward, edgy brands |
| Organic | Soft shapes, natural colors | Eco-friendly, wellness |
| Retro | Nostalgic elements, vintage palette | Gaming, pop culture |
| Editorial | Magazine-like layouts, strong typography | Content-heavy sites |

### 🔴 BLOCKING

- **Commit to a direction** → Mixing styles creates visual confusion
- **Consistency is non-negotiable** → Same patterns throughout the app
- **Avoid "AI slop"** → No generic gradients, no overused Inter/Roboto fonts

---

## Typography

📚 **References:** [typography-guide.md](references/typography-guide.md)

### Type Scale

```
Display:   48px / 3rem    → Headlines, hero sections
H1:        36px / 2.25rem → Page titles
H2:        30px / 1.875rem → Section headers
H3:        24px / 1.5rem  → Subsection headers
H4:        20px / 1.25rem → Card titles
Body:      16px / 1rem    → Paragraph text
Small:     14px / 0.875rem → Captions, metadata
XSmall:    12px / 0.75rem → Labels, footnotes
```

### 🔴 BLOCKING Rules

| Rule | Why |
|------|-----|
| **Max 2 font families** | More creates visual chaos |
| **Minimum body size: 16px** | Smaller is inaccessible on mobile |
| **Line height: 1.4-1.6 for body** | Improves readability |
| **Max line width: 65-75 characters** | Prevents eye fatigue |

### Font Pairing Strategy

```
┌─────────────────────────────────────────────────────────┐
│  DISPLAY FONT (Distinctive)                              │
│  Headlines, heroes, marketing                            │
│  Examples: Playfair Display, Space Grotesk, Fraunces    │
├─────────────────────────────────────────────────────────┤
│  BODY FONT (Readable)                                    │
│  Paragraphs, UI elements                                 │
│  Examples: Source Sans Pro, Lato, Open Sans             │
└─────────────────────────────────────────────────────────┘
```

### 🔴 AVOID These Generic Fonts

- Inter (overused by AI-generated designs)
- Roboto (too generic)
- Arial (system default = lazy)
- System fonts without intention

---

## Color

📚 **References:** [color-system.md](references/color-system.md)

### Color System Structure

```css
:root {
  /* Primary - Brand color */
  --color-primary-50: #f0fdf4;
  --color-primary-100: #dcfce7;
  --color-primary-500: #22c55e;  /* Main */
  --color-primary-600: #16a34a;  /* Hover */
  --color-primary-900: #14532d;

  /* Neutral - Text and backgrounds */
  --color-neutral-50: #fafafa;
  --color-neutral-100: #f5f5f5;
  --color-neutral-500: #737373;
  --color-neutral-900: #171717;

  /* Semantic - Feedback */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;
}
```

### 🔴 BLOCKING Rules

| Rule | Why |
|------|-----|
| **Contrast ratio ≥ 4.5:1 for text** | WCAG accessibility requirement |
| **Contrast ratio ≥ 3:1 for UI elements** | Buttons, icons must be visible |
| **Don't rely on color alone** | Use icons + color for status |
| **Test in grayscale** | Hierarchy must work without color |

### Color Psychology for E-Commerce

| Color | Association | Use For |
|-------|-------------|---------|
| Green | Nature, eco, growth | Buy Nature brand! |
| Blue | Trust, stability | Payment, security |
| Orange | Urgency, action | CTAs, sales |
| White | Clean, premium | Backgrounds |
| Dark green | Luxury eco | Premium products |

### 🔴 AVOID

- Purple gradients on white (AI slop cliché)
- Rainbow gradients (unprofessional)
- Neon colors without purpose
- Low contrast text

---

## Layout & Spacing

📚 **References:** [layout-system.md](references/layout-system.md)

### Spacing Scale (8px base)

```css
:root {
  --space-1: 0.25rem;  /* 4px */
  --space-2: 0.5rem;   /* 8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-5: 1.25rem;  /* 20px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-10: 2.5rem;  /* 40px */
  --space-12: 3rem;    /* 48px */
  --space-16: 4rem;    /* 64px */
}
```

### Grid System

```css
/* Container widths */
.container {
  --max-width: 1280px;
  width: min(100% - 2rem, var(--max-width));
  margin-inline: auto;
}

/* 12-column grid */
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--space-6);
}
```

### 🔴 BLOCKING Rules

| Rule | Why |
|------|-----|
| **Consistent spacing** | Use scale, never arbitrary values |
| **Generous whitespace** | Improves readability and focus |
| **Mobile-first breakpoints** | Most users are mobile |
| **Touch targets ≥ 44px** | Accessibility requirement |

---

## Components

📚 **References:** [component-patterns.md](references/component-patterns.md)

### Button Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│  PRIMARY                                                 │
│  Filled, brand color, high contrast                     │
│  Use: Main action (Add to Cart, Submit)                 │
├─────────────────────────────────────────────────────────┤
│  SECONDARY                                               │
│  Outlined or muted fill                                 │
│  Use: Alternative actions (Learn More, Details)         │
├─────────────────────────────────────────────────────────┤
│  TERTIARY / GHOST                                       │
│  Text only or minimal styling                           │
│  Use: Dismissive actions (Cancel, Skip)                 │
├─────────────────────────────────────────────────────────┤
│  DESTRUCTIVE                                            │
│  Red/danger color                                       │
│  Use: Dangerous actions (Delete, Remove)                │
└─────────────────────────────────────────────────────────┘
```

### 🔴 BLOCKING Rules

| Rule | Why |
|------|-----|
| **One primary CTA per view** | Clear action hierarchy |
| **Button labels are verbs** | "Add to Cart" not "Cart" |
| **Loading states for async** | User knows action is processing |
| **Disabled state is clear** | But don't disable without reason |

---

## Accessibility (a11y)

📚 **References:** [accessibility-checklist.md](references/accessibility-checklist.md)

### 🔴 BLOCKING - WCAG AA Requirements

| Requirement | Check |
|-------------|-------|
| Keyboard navigation | Tab through all interactive elements |
| Focus indicators | Visible focus ring on all focusable elements |
| Alt text | All meaningful images have descriptions |
| Form labels | Every input has associated label |
| Color contrast | 4.5:1 for text, 3:1 for UI |
| Error identification | Errors described in text, not just color |

### Quick Accessibility Test

```markdown
1. [ ] Can you Tab through the entire page?
2. [ ] Is focus always visible?
3. [ ] Can you use the form with keyboard only?
4. [ ] Does the page make sense with images off?
5. [ ] Does it work at 200% zoom?
6. [ ] Does screen reader announce content logically?
```

---

## Responsive Design

📚 **References:** [responsive-patterns.md](references/responsive-patterns.md)

### Breakpoints

```css
/* Mobile-first approach */
:root {
  --breakpoint-sm: 640px;   /* Large phones */
  --breakpoint-md: 768px;   /* Tablets */
  --breakpoint-lg: 1024px;  /* Laptops */
  --breakpoint-xl: 1280px;  /* Desktops */
  --breakpoint-2xl: 1536px; /* Large screens */
}
```

### 🔴 BLOCKING Rules

| Rule | Why |
|------|-----|
| **Mobile-first CSS** | Start small, enhance for larger |
| **Test on real devices** | Emulators miss real issues |
| **Touch targets 44px+** | Fingers are not precise |
| **No horizontal scroll** | Breaks mobile UX |

---

# Part 2: Implementation Patterns

## CSS Architecture

### 🟢 BEST PRACTICE: CSS Variables

```css
/* tokens.css - Design tokens */
:root {
  /* Colors */
  --color-brand: #22c55e;
  --color-brand-dark: #16a34a;
  
  /* Typography */
  --font-display: 'Playfair Display', serif;
  --font-body: 'Source Sans Pro', sans-serif;
  
  /* Spacing */
  --space-unit: 8px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px rgb(0 0 0 / 0.1);
  
  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;
  --radius-full: 9999px;
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 300ms ease;
}
```

### Component CSS Pattern

```css
/* button.css */
.btn {
  /* Base styles */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  
  padding: var(--space-3) var(--space-5);
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 1rem;
  line-height: 1.5;
  
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  
  transition: 
    background-color var(--transition-fast),
    transform var(--transition-fast);
}

/* Variants */
.btn--primary {
  background-color: var(--color-brand);
  color: white;
}

.btn--primary:hover {
  background-color: var(--color-brand-dark);
}

.btn--primary:active {
  transform: scale(0.98);
}

/* States */
.btn:focus-visible {
  outline: 2px solid var(--color-brand);
  outline-offset: 2px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

## Animation & Motion

### 🔴 BLOCKING Rules

| Rule | Why |
|------|-----|
| **Respect prefers-reduced-motion** | Accessibility for motion-sensitive users |
| **Duration 150-300ms for UI** | Longer feels sluggish |
| **Purpose over decoration** | Animation should guide, not distract |

### Implementation

```css
/* Respect user preference */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* Meaningful animation */
.card {
  transition: transform var(--transition-normal),
              box-shadow var(--transition-normal);
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

/* Page load stagger */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-in {
  animation: fadeInUp 0.6s ease-out forwards;
}

.animate-in:nth-child(1) { animation-delay: 0ms; }
.animate-in:nth-child(2) { animation-delay: 100ms; }
.animate-in:nth-child(3) { animation-delay: 200ms; }
```

---

## Code Review Checklist

### Design Quality

```markdown
## Visual Review
- [ ] Follows established design system tokens
- [ ] Typography hierarchy is clear
- [ ] Color contrast meets WCAG AA (4.5:1 text, 3:1 UI)
- [ ] Spacing is consistent (uses scale values)
- [ ] No orphan text (single words on new lines)

## Accessibility
- [ ] All interactive elements are keyboard accessible
- [ ] Focus states are visible
- [ ] Images have alt text
- [ ] Forms have proper labels
- [ ] Error messages are descriptive

## Responsiveness
- [ ] Works on 320px width (small phones)
- [ ] Touch targets are 44px minimum
- [ ] No horizontal scrolling
- [ ] Images are responsive

## Performance
- [ ] Images are optimized (WebP, lazy loading)
- [ ] Fonts are preloaded
- [ ] CSS is minimal (no unused styles)
- [ ] Animations use transform/opacity (GPU accelerated)

## UX
- [ ] Loading states for async operations
- [ ] Empty states are designed
- [ ] Error states are helpful
- [ ] Success feedback is clear
```

---

## Buy Nature Specific Guidelines

### Brand Application

| Element | Value |
|---------|-------|
| Primary Color | Green (#22c55e) - Nature, eco-friendly |
| Secondary Color | Earth tones, cream, natural browns |
| Typography | Clean, modern sans-serif for body |
| Imagery | Natural textures, plants, organic shapes |
| Tone | Trustworthy, warm, environmentally conscious |

### E-Commerce UX Priorities

1. **Clear product information** → Users need to trust what they buy
2. **Easy cart/checkout** → Reduce friction to purchase
3. **Mobile-optimized** → Most traffic is mobile
4. **Fast load times** → Slow = lost sales
5. **Trust signals** → Eco certifications, reviews, secure checkout

---

## Related Skills

- `common-frontend-angular` — Implementing design in Angular
- `common-typescript` — Type-safe design tokens
- `buy-nature-frontend-coding-guide` — Buy Nature design system
- `buy-nature-backoffice-coding-guide` — Bio-Forest theme colors
