# Design Tokens in Angular — Material Integration

> Token definitions, naming, category scales, and the never-hardcode rule are **owned by the `common-frontend-design` skill** — load it. This file covers only the Angular-specific consumption: Material palette wiring, component SCSS usage, and light/dark theme switching.

## Table of Contents

- [Integration with Angular Material](#integration-with-angular-material)
- [Component with Design Tokens](#component-with-design-tokens)
- [Theming Support (Light/Dark)](#theming-support-lightdark)

---

## Integration with Angular Material

```scss
// styles/theme.scss
@use '@angular/material' as mat;

$my-primary: mat.define-palette((
  50: var(--color-primary-50),
  100: var(--color-primary-100),
  500: var(--color-primary-500),
  contrast: (
    500: var(--color-white)
  )
));

$my-theme: mat.define-light-theme((
  color: (
    primary: $my-primary,
    accent: $my-accent,
  )
));

@include mat.all-component-themes($my-theme);
```

## Component with Design Tokens

```scss
// item-card.component.scss
.item-card {
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  background-color: var(--color-surface);
  box-shadow: var(--shadow-md);

  &:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(calc(var(--space-1) * -1));
  }
}

.item-card__title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}
```

## Theming Support (Light/Dark)

Theme token *values* (palettes per theme) are defined in `common-frontend-design`; the Angular mechanics:

```scss
:root {
  --color-background: #ffffff;
  --color-text-primary: #1f2937;
  --color-surface: #f9fafb;
}

[data-theme="dark"] {
  --color-background: #1f2937;
  --color-text-primary: #f9fafb;
  --color-surface: #374151;
}
```

```typescript
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly theme = signal<'light' | 'dark'>('light');
  readonly currentTheme = this.theme.asReadonly();

  toggleTheme(): void {
    const newTheme = this.theme() === 'light' ? 'dark' : 'light';
    this.theme.set(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  }
}
```
