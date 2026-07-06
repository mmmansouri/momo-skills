# Typography Guide

> **Ownership:** the BLOCKING typography rules (≤ 2 font families, body ≥ 16 px, line-height 1.4–1.6, line length 65–75 chars) are owned by **SKILL.md** (`## When Choosing Typography`).
> Generic font-pairing theory, responsive-typography scaling, and typography accessibility are native to the model — they are **not** restated here.
> This file keeps the house type-scale tokens, the AVOID-generic-fonts stance, and one concrete implementation example.

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

## 🔴 AVOID These Generic Fonts

House stance: distinctive design demands one or two intentional font choices no template ships by default.

| Font | Why Avoid |
|------|-----------|
| Inter | Overused by AI-generated designs |
| Roboto | Too generic, no personality |
| Arial | System default = lazy design choice |
| System fonts without intention | Lacks brand identity |

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
