---
name: common-frontend-design
description: >-
  Frontend design and UX best practices. Use this skill whenever the user asks
  to design a UI, pick a color palette, choose typography, build a responsive
  layout, audit accessibility (WCAG AA), define design tokens, design a button or
  card hierarchy, animate a transition, improve the visual quality of a page,
  or review UI/design changes in a PR (component templates, SCSS, theme tokens,
  accessibility) — even when they don't explicitly say "design". Always loaded alongside
  `common-developer` (foundational craftsmanship) and, for Angular projects,
  `common-frontend-angular` (which consumes the design tokens defined here).
---

# Frontend Design & UX Skill

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
> **Foundational rules** (SOLID, Clean Code, Self-Review) live in `common-developer`. **Angular implementation** (Material integration, component CSS scoping) lives in `common-frontend-angular`. This skill is the **source of truth for design tokens, visual hierarchy, and a11y rules**.

---

## When Reasoning About Design

Apply these foundational stances to every UI:

1. **Commit to a direction** — pick one aesthetic and apply it consistently.
2. **Intentionality over defaults** — every color, font, and spacing choice is a deliberate decision.
3. **Accessibility is a baseline**, not a polish step.
4. **Tokens, not values** — every reusable visual decision lives in a CSS variable.
5. **Mobile-first**, then enhance.

### 🔴 BLOCKING

#### Commit to one bold aesthetic direction; never mix styles
**Why:** mixing minimalist with maximalist, brutalist with organic, etc., produces visual confusion that erodes trust before users even read the content. Pick one direction (Minimalist / Maximalist / Brutalist / Organic / Retro / Editorial) and apply it across every screen.

| Direction | Characteristics | Fits |
|-----------|-----------------|------|
| Minimalist | White space, simple typography | Professional services, luxury |
| Maximalist | Rich textures, bold colors | Creative, entertainment |
| Brutalist | Raw, exposed structure | Tech-forward, edgy brands |
| Organic | Soft shapes, natural colors | Eco, wellness |
| Retro | Nostalgic, vintage palette | Gaming, pop culture |
| Editorial | Magazine-like layouts, strong typography | Content-heavy sites |

#### Avoid AI-slop defaults — generic fonts, purple-on-white gradients, rainbow CTAs
**Why:** these are the visual signature of "we ran an LLM at the design stage and shipped what came out". Users register them subconsciously as low-effort and the brand loses credibility. Distinctive design demands one or two intentional choices that no template ships by default.

##### WRONG
```
Font: Inter / Roboto (default in every framework)
Hero gradient: linear-gradient(white → purple)
CTA: rainbow gradient pill button
Color palette: Tailwind defaults straight off the shelf
```
##### CORRECT
```
Font: Playfair Display (display) + Source Sans Pro (body)
Hero: solid background-color tied to brand token, sharp typography
CTA: single brand color, semantic hover state, focus-visible ring
Palette: 50/100/500/600/900 scale generated from the brand hue
```

---

## When Choosing Typography

📚 **When pairing display + body fonts, defining a type scale, setting line-height/line-length, or auditing typography accessibility → read [typography-guide.md](references/typography-guide.md).**

### Type Scale
```
Display:  48px / 3rem      → Headlines, hero sections
H1:       36px / 2.25rem   → Page titles
H2:       30px / 1.875rem  → Section headers
H3:       24px / 1.5rem    → Subsection headers
H4:       20px / 1.25rem   → Card titles
Body:     16px / 1rem      → Paragraph text
Small:    14px / 0.875rem  → Captions, metadata
XSmall:   12px / 0.75rem   → Labels, footnotes
```

### 🔴 BLOCKING

#### Use at most 2 font families per project (1 display + 1 body)
**Why:** every additional font multiplies the page weight (each face downloads), increases FOUT/FOIT during loading, and forces the reader's eye to retrain at each switch. Two well-chosen families produce hierarchy and personality without cost.

#### Body text ≥ 16px, line-height 1.4–1.6, max line length 65–75 characters
**Why:** smaller body text fails mobile readability for older users and is rejected by accessibility audits. Lines longer than ~75 characters force the reader's eye to track too far on the return scan, which causes line-skipping and re-reading. These three numbers are the cheapest readability win available.

##### WRONG
```css
body { font-family: Inter, Roboto, system-ui; font-size: 14px; line-height: 1.2; }
.article { max-width: 100%; }
```
##### CORRECT
```css
body { font-family: var(--font-body), serif; font-size: 1rem; line-height: 1.5; }
.article { max-width: 65ch; }   /* characters, not pixels */
```

---

## When Working with Color

📚 **When building a 50→900 color scale, defining semantic colors, checking WCAG contrast ratios, or designing dark-mode palettes → read [color-system.md](references/color-system.md).**

### Color System Structure
```css
:root {
  /* Primary (brand) — full 50→900 scale */
  --color-primary-50:  #f0fdf4;
  --color-primary-500: #22c55e;
  --color-primary-600: #16a34a;
  --color-primary-900: #14532d;

  /* Neutral — text, backgrounds, borders */
  --color-neutral-50:  #fafafa;
  --color-neutral-500: #737373;
  --color-neutral-900: #171717;

  /* Semantic — feedback only */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error:   #ef4444;
  --color-info:    #3b82f6;
}
```

### 🔴 BLOCKING

#### Contrast ratio ≥ 4.5:1 for text, ≥ 3:1 for UI elements
**Why:** WCAG AA is the legal accessibility floor in many jurisdictions and the practical floor for users with low vision, age-related decline, or sub-optimal screens (cheap LCD, sun glare). Below those ratios you measurably exclude readers; above them, design quality goes up for everyone.

#### Never communicate state by color alone — pair with icon, text, or shape
**Why:** ~8% of men are red/green colorblind, and a far larger fraction of users navigate in suboptimal lighting. A green ✓ + red ✗ collapses to an indistinguishable pair for them; adding the icon disambiguates without cost.

##### WRONG
```html
<span class="text-success">Saved</span>
<span class="text-error">Failed</span>
```
##### CORRECT
```html
<span class="text-success"><CheckIcon/> Saved</span>
<span class="text-error"><AlertIcon/> Failed — retry</span>
```

#### Test the design in grayscale before shipping
**Why:** if hierarchy collapses without color (you can't tell the primary CTA from a secondary link), the page leans on color to do work that should be done by typography weight, size, and spacing. Greyscale is a 5-second filter that surfaces the defect.

### 🟡 WARNING — Avoid

- Purple gradients on white (AI-slop cliché).
- Rainbow gradients (unprofessional unless the brand mandates them).
- Neon colors without semantic purpose.
- Low-contrast "subtle" gray text (`#999` on `#fff`).

---

## When Composing Layouts

📚 **When applying the 8 px spacing scale, choosing grid vs flexbox, sizing touch targets, setting z-index tiers, or composing common page layouts → read [layout-system.md](references/layout-system.md).**

### Spacing Scale (8 px base)
```css
--space-1:  0.25rem; /* 4 px  */
--space-2:  0.5rem;  /* 8 px  */
--space-4:  1rem;    /* 16 px */
--space-6:  1.5rem;  /* 24 px */
--space-8:  2rem;    /* 32 px */
--space-12: 3rem;    /* 48 px */
--space-16: 4rem;    /* 64 px */
```

### 🔴 BLOCKING

#### Use the spacing scale exclusively — never arbitrary px values
**Why:** arbitrary values (`padding: 13px`) compound silently across the codebase: each new component drifts one or two pixels off the rhythm, and the page gradually stops feeling cohesive. The scale is what makes "consistent" measurable.

#### Touch targets ≥ 44 × 44 px
**Why:** smaller targets fail Fitts's-law thresholds for fingertip use — users tap the wrong thing or have to retry. The 44 px floor matches Apple's HIG and Android Material guidelines and is enforced by accessibility audits.

#### Use generous whitespace between sections
**Why:** density without rhythm reads as "cheap" or "spam-like". The visual silence between sections is what lets the reader's eye chunk the page and absorb the hierarchy. Every reduction in whitespace increases cognitive load measurably.

---

## When Designing Components

📚 **When specifying buttons, forms, cards, modals, or the 5 interactive states (default/hover/focus-visible/active/disabled) plus loading/error → read [component-patterns.md](references/component-patterns.md).**

### Button Hierarchy

| Tier | Visual | Use for |
|------|--------|---------|
| **Primary** | Filled, brand color, high contrast | Main action (Add to Cart, Submit) |
| **Secondary** | Outlined or muted fill | Alternative actions (Learn More) |
| **Tertiary / Ghost** | Text only | Dismissive (Cancel, Skip) |
| **Destructive** | Red / danger color | Dangerous (Delete, Remove) |

### 🔴 BLOCKING

#### One primary CTA per view
**Why:** two equally-prominent CTAs split the user's attention and reduce conversion on both. A clear hierarchy ("the one button I should click") is what makes the page actionable. Demote secondary actions visually.

#### Button labels are imperative verbs, not nouns
**Why:** "Cart" is a destination, "Add to Cart" is an action. Nouns force the user to infer what will happen on click; verbs describe the action explicitly. Verb labels measurably increase click-through.

##### WRONG
```html
<button>Cart</button>
<button>Settings</button>
<button>Profile</button>
```
##### CORRECT
```html
<button>Add to cart</button>
<button>Open settings</button>
<button>View profile</button>
```

#### Design all 5 states for every interactive component: default, hover, focus-visible, active, disabled — plus loading and error for async actions
**Why:** missing states are the dominant source of "the app feels broken" complaints. A button with no `:focus-visible` is invisible to keyboard users. A submit with no loading state lets users double-click and double-submit. Design every state up front.

---

## When Ensuring Accessibility (WCAG AA)

📚 **When auditing WCAG AA compliance, validating semantic HTML, applying ARIA attributes, designing keyboard navigation, or testing with screen readers → read [accessibility-checklist.md](references/accessibility-checklist.md).**

| Requirement | Pass criterion |
|-------------|----------------|
| Keyboard navigation | Tab reaches every interactive element |
| Focus indicator | Visible `:focus-visible` ring on every focusable element |
| Alt text | Every meaningful image has a description; decorative ones use `alt=""` |
| Form labels | Every input has an associated `<label>` (or `aria-label`) |
| Color contrast | 4.5:1 text, 3:1 UI |
| Error identification | Errors named in text, not just colored borders |

### Quick Audit (run before every release)

1. Tab through the entire page — does focus follow a logical order?
2. Is the focus ring visible on every focusable element?
3. Can the form be completed with the keyboard alone?
4. Does the page make sense with images turned off?
5. Does it work at 200 % browser zoom?
6. Does a screen reader announce the content in a meaningful order?

### 🔴 BLOCKING

#### Every interactive element is keyboard-reachable with a visible focus indicator
**Why:** keyboard users (motor impairments, screen-reader users, power users) literally cannot use the page without tab-reachable focus. `outline: none` without a replacement is the single most common a11y defect; the cost of a `:focus-visible` style is one rule.

#### Every form input has an associated label; every meaningful image has alt text
**Why:** screen readers announce inputs by their label. An unlabeled input reads as "edit text" with no context. Decorative-only images need `alt=""` to be skipped explicitly; meaningful images need a description. Both rules together are what makes the page navigable without sight.

#### Error messages are described in text, not by border color alone
**Why:** colorblind users and screen readers cannot perceive a red border. The text "Email is required" is what makes the error recoverable. Color is amplification, never the sole channel.

---

## When Building Responsive Layouts

📚 **When writing mobile-first media queries, designing responsive grids, sizing touch targets, using container queries, or auditing responsive performance → read [responsive-patterns.md](references/responsive-patterns.md).**

### Breakpoints
```css
--breakpoint-sm:  640px;  /* large phones */
--breakpoint-md:  768px;  /* tablets */
--breakpoint-lg:  1024px; /* laptops */
--breakpoint-xl:  1280px; /* desktops */
--breakpoint-2xl: 1536px; /* large screens */
```

### 🔴 BLOCKING

#### Mobile-first CSS — start small, enhance with `min-width` media queries
**Why:** most traffic is mobile. Writing desktop-first means every smaller screen overrides every rule, producing fragile and bloated CSS. Mobile-first lets the small-screen styles be the default and the larger-screen styles add features additively.

#### Never produce horizontal scroll on mobile (except inside intentional carousels)
**Why:** unintended horizontal scroll is universally read as "the site is broken on mobile". It usually indicates a fixed-width element or an `overflow` mistake — fix the cause, not the symptom (`overflow-x: hidden` hides the bug rather than fixing it).

#### Test on real devices, not only on the desktop emulator
**Why:** emulators miss touch latency, font rendering on low-DPI screens, soft-keyboard behavior, and iOS Safari's idiosyncrasies (notch handling, address-bar resize). A 30-second check on a real phone catches defects emulators silently pass.

---

## When Animating

```css
/* Always honor user preference */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 🔴 BLOCKING

#### Respect `prefers-reduced-motion: reduce`
**Why:** vestibular-disorder users get nauseous from large transforms. Honoring the OS-level setting is a one-rule change that prevents real harm. Skipping it is a hard accessibility fail.

#### UI animations stay between 150 ms and 300 ms
**Why:** below 100 ms the animation reads as instant (no perceived feedback). Above 300 ms it reads as sluggish and the user starts wondering if the action registered. The 150–300 ms band is the perceptual sweet spot.

#### Animate only `transform` and `opacity`; never animate `width`, `height`, `top`, `left`
**Why:** transform and opacity run on the GPU compositor at 60 fps with no layout cost. Animating `width`/`height` triggers layout on every frame, which janks below 60 fps the moment the page has any other content competing for the main thread.

---

## When Defining Design Tokens

```css
/* tokens.css — single source of truth for every reusable visual value */
:root {
  /* Color (see When Working with Color) */
  --color-primary-500: #...;
  --color-neutral-500: #...;
  --color-success:     #...;

  /* Typography */
  --font-display: 'Playfair Display', serif;
  --font-body:    'Source Sans Pro', sans-serif;
  --text-base:    1rem;
  --text-lg:      1.25rem;

  /* Spacing (8 px base) */
  --space-4: 1rem;
  --space-8: 2rem;

  /* Radius */
  --radius-sm:   4px;
  --radius-md:   8px;
  --radius-full: 9999px;

  /* Shadow */
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px rgb(0 0 0 / 0.10);

  /* Transition */
  --transition-fast:   150ms ease;
  --transition-normal: 300ms ease;
}
```

### 🔴 BLOCKING

#### Every color, spacing, font-size, radius, shadow, and transition lives in a CSS variable
**Why:** hardcoded values fork the design system the moment a theme switch (dark mode, brand re-skin, accessibility tweak) is needed. Tokens let theming happen by changing one `:root` block instead of grepping the codebase. Hardcoded values are tomorrow's tech debt.

---

## Output Contract

When producing design artifacts, deliver each in this exact form:

| Artifact | Required Form |
|----------|---------------|
| **Design tokens** (`tokens.css`) | `:root { --color-*, --space-*, --text-*, --radius-*, --shadow-*, --transition-* }`. No hardcoded hex / px elsewhere. |
| **Color palette** | Primary + neutral 50/100/500/600/900 shades, four semantic colors (success/warning/error/info). All combinations passing WCAG AA (4.5:1 text, 3:1 UI). |
| **Typography scale** | Display / H1 / H2 / H3 / H4 / Body / Small / XSmall, each with px **and** rem values. Two font families maximum (display + body). |
| **Spacing scale** | 8 px base, multiples 1 / 2 / 3 / 4 / 5 / 6 / 8 / 10 / 12 / 16. |
| **Component spec** | Base styles + variants (primary / secondary / tertiary / destructive) + 5 states (default / hover / focus-visible / active / disabled) + loading + error states for async. |
| **Accessibility audit** | The 6-point quick-audit list above, each item annotated PASS / FAIL with the file or line where the defect lives. |
