# Design Tokens in Angular

> See also: `common-frontend-design` skill for token definitions and design system principles.

## Use CSS Variables, Not Hardcoded Values

```scss
// ❌ WRONG - Hardcoded values
.button {
  background-color: #22c55e;
  padding: 16px;
  border-radius: 8px;
  font-size: 16px;
  color: #ffffff;
}

// ✅ CORRECT - Design tokens via CSS variables
.button {
  background-color: var(--color-primary-500);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  color: var(--color-white);
}
```

## Token Categories

| Category | CSS Variable Pattern | Example |
|----------|---------------------|---------|
| Colors | `--color-{name}-{shade}` | `--color-primary-600` |
| Spacing | `--space-{size}` | `--space-8` (32px) |
| Typography | `--text-{size}` | `--text-lg` |
| Border Radius | `--radius-{size}` | `--radius-lg` |
| Shadows | `--shadow-{size}` | `--shadow-md` |
| Breakpoints | `--breakpoint-{size}` | `--breakpoint-lg` |

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

.item-card__price {
  font-size: var(--text-lg);
  color: var(--color-primary-600);
  font-weight: var(--font-bold);
}
```

## Responsive Design with Tokens

```scss
@media (min-width: 768px) {  // --breakpoint-md
  .item-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-6);
  }
}

@media (min-width: 1024px) {  // --breakpoint-lg
  .item-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-8);
  }
}
```

## Theming Support (Light/Dark)

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
