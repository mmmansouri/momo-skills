# Typography Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Type Scale

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

---

## 🔴 BLOCKING Rules

| Rule | Why |
|------|-----|
| **Max 2 font families** | More creates visual chaos |
| **Minimum body size: 16px** | Smaller is inaccessible on mobile |
| **Line height: 1.4-1.6 for body** | Improves readability |
| **Max line width: 65-75 characters** | Prevents eye fatigue |

---

## Font Pairing Strategy

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

**Display Font Characteristics:**
- Distinctive personality
- Used sparingly (headlines, hero sections)
- Can be decorative
- Examples: Playfair Display (serif), Space Grotesk (geometric), Fraunces (variable)

**Body Font Characteristics:**
- High readability at small sizes
- Clear at all weights
- Good x-height (tall lowercase letters)
- Examples: Source Sans Pro, Lato, Open Sans

---

## 🔴 AVOID These Generic Fonts

| Font | Why Avoid |
|------|-----------|
| Inter | Overused by AI-generated designs |
| Roboto | Too generic, no personality |
| Arial | System default = lazy design choice |
| System fonts without intention | Lacks brand identity |

---

## Font Selection Checklist

Before choosing fonts, ask:

- [ ] Does the display font reflect brand personality?
- [ ] Is the body font readable at 16px on mobile?
- [ ] Do they pair well (contrast in style but harmonious)?
- [ ] Are both available as web fonts (Google Fonts, Adobe Fonts)?
- [ ] Do they support all required characters (accents, symbols)?
- [ ] Is the license appropriate for commercial use?

---

## Implementation Example

```css
/* Import fonts */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+Pro:wght@400;600&display=swap');

:root {
  /* Font families */
  --font-display: 'Playfair Display', serif;
  --font-body: 'Source Sans Pro', sans-serif;

  /* Font sizes */
  --text-display: 3rem;      /* 48px */
  --text-h1: 2.25rem;        /* 36px */
  --text-h2: 1.875rem;       /* 30px */
  --text-h3: 1.5rem;         /* 24px */
  --text-h4: 1.25rem;        /* 20px */
  --text-body: 1rem;         /* 16px */
  --text-small: 0.875rem;    /* 14px */
  --text-xsmall: 0.75rem;    /* 12px */

  /* Line heights */
  --leading-tight: 1.2;
  --leading-normal: 1.5;
  --leading-relaxed: 1.6;
}

/* Typography scale application */
h1, .display {
  font-family: var(--font-display);
  font-size: var(--text-display);
  line-height: var(--leading-tight);
}

h2 {
  font-family: var(--font-display);
  font-size: var(--text-h1);
  line-height: var(--leading-tight);
}

body, p {
  font-family: var(--font-body);
  font-size: var(--text-body);
  line-height: var(--leading-normal);
  max-width: 65ch; /* 65 characters max line width */
}
```

---

## Common Typography Mistakes

| Mistake | Fix |
|---------|-----|
| Too many font sizes | Stick to the scale, no arbitrary sizes |
| Inconsistent line heights | Use defined values (tight, normal, relaxed) |
| Poor hierarchy | Size differences should be noticeable (1.2x minimum) |
| All caps overuse | Use sparingly, reduces readability |
| Center-aligned body text | Left-align for readability |
| Tight leading on long text | Use 1.5-1.6 line height for paragraphs |

---

## Responsive Typography

```css
/* Mobile-first approach */
:root {
  --text-h1: 2rem;    /* 32px on mobile */
  --text-body: 1rem;  /* 16px (never smaller) */
}

/* Scale up for larger screens */
@media (min-width: 768px) {
  :root {
    --text-h1: 2.5rem;  /* 40px on tablet */
  }
}

@media (min-width: 1024px) {
  :root {
    --text-h1: 3rem;    /* 48px on desktop */
  }
}
```

---

## Accessibility Considerations

- **Minimum 16px for body text** - Anything smaller is hard to read on mobile
- **High contrast** - At least 4.5:1 for normal text, 3:1 for large text
- **No color-only meaning** - Don't rely on color alone to convey information
- **Zoom support** - Text must be readable at 200% zoom
- **Line length** - 65-75 characters max for optimal readability
