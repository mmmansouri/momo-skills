---
name: common-frontend-angular
description: >-
  Frontend development with Angular 17-21. Use when: building Angular components,
  managing state (Signals/NgRx), handling forms (reactive), routing, HTTP services,
  testing (Jest/Jasmine), or applying frontend architecture patterns.
  Contains Angular 21 features, migration guidance from older versions, and deprecated APIs.
---

# Frontend Angular Developer Guide (Angular 17-21)

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## When Choosing Angular APIs (Modern vs Legacy)

> Angular 21 is the current target. These older APIs are still **supported** but modern alternatives offer better performance and type safety.

| Legacy API | Modern Alternative | Since | Severity |
|------------|-------------------|-------|----------|
| `*ngIf`, `*ngFor`, `*ngSwitch` | `@if`, `@for`, `@switch` | 17.0 | 🔴 BLOCKING |
| `@Input()` decorator | `input()` / `input.required()` | 17.1 | 🟡 WARNING |
| `@Output()` decorator | `output()` | 17.3 | 🟡 WARNING |
| `@ViewChild()` / `@ViewChildren()` | `viewChild()` / `viewChildren()` | 17.2 | 🟡 WARNING |
| `[ngClass]` / `[ngStyle]` | `[class]` / `[style]` binding | 21.0 | 🟡 WARNING |
| `NgModule` for components | `standalone: true` | 14+ | 🟡 WARNING |
| Class-based guards/resolvers | Functional guards/resolvers | 15+ | 🟡 WARNING |
| `BehaviorSubject` for state | Signals (`signal()`, `computed()`) | 16+ | 🟡 WARNING |
| `ngOnChanges` | `effect()` with signal inputs | 17+ | 🟡 WARNING |
| Zone.js change detection | Zoneless (default 21+) | 18+ | 🟡 WARNING |

### 🟢 Migration Strategy

- **New code:** Use modern alternatives exclusively
- **Existing code:** Migrate opportunistically
- **Migration schematics:** See [migration-checklist.md](references/migration-checklist.md)

---

## 🔴 When Validating Builds (MANDATORY)

```bash
# 1. Build (catches TypeScript + template errors)
npm run build

# 2. Tests (if Chrome/Chromium available)
CHROME_BIN=$(which chromium-browser) npm test -- --no-watch
```

Angular has **lazy compilation** — some errors only appear during full build, NOT during `npm install` or `ng lint`.

---

## When Structuring Projects

### 🔴 BLOCKING
- **Feature-based structure** → NOT layer-based
- **Smart vs Dumb components** → Container vs Presentational
- **Single Responsibility** → One component = one purpose

```
src/app/
├── features/           # Feature modules (lazy loaded)
│   ├── auth/
│   │   ├── components/
│   │   ├── services/
│   │   ├── models/
│   │   └── routes.ts
│   └── catalog/
├── shared/             # Reusable across features
├── core/               # Singleton services, guards, interceptors
├── app.config.ts       # provideRouter, provideHttpClient
└── app.routes.ts
```

| Aspect | Smart (Container) | Presentational (Dumb) |
|--------|-------------------|----------------------|
| Data | Injects services | Receives via `input()` |
| State | Manages with signals | Stateless or local UI state |
| Reusability | Feature-specific | Highly reusable |

---

## When Writing Components

📚 **References:** [angular-patterns.md](references/angular-patterns.md) — NgRx Store, Forms, HTTP, Routing full examples

### 🔴 BLOCKING - Modern Component Pattern

```typescript
@Component({
  selector: 'app-product-card',
  standalone: true,
  imports: [CurrencyPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (showPrice()) {
      <p class="price">{{ product().price | currency }}</p>
    }
    <button (click)="onAddToCart()" [disabled]="!product().inStock">
      {{ product().inStock ? 'Add to Cart' : 'Out of Stock' }}
    </button>
  `
})
export class ProductCardComponent {
  readonly product = input.required<Product>();
  readonly showPrice = input(true);
  readonly addToCart = output<Product>();
  readonly isAvailable = computed(() => this.product().inStock);

  onAddToCart() { this.addToCart.emit(this.product()); }
}
```

### 🔴 WRONG - Legacy Patterns

```typescript
@Component({...})
export class ProductCardComponent implements OnChanges {
  @Input() product!: Product;                          // ❌ Use input()
  @Output() addToCart = new EventEmitter<Product>();    // ❌ Use output()
  ngOnChanges(changes: SimpleChanges) { ... }          // ❌ Use effect()
}
```

---

## When Using Control Flow

### 🔴 BLOCKING - New Syntax (Angular 17+)

```html
@if (user()) {
  <p>Welcome, {{ user().name }}</p>
} @else { <p>Please log in</p> }

@for (product of products(); track product.id) {
  <app-product-card [product]="product" />
} @empty { <p>No products found</p> }

@switch (status()) {
  @case ('pending') { <span class="badge warning">Pending</span> }
  @case ('approved') { <span class="badge success">Approved</span> }
}
```

### 🟢 Deferrable Views — Lazy Load Heavy Components

```html
@defer (on viewport) {
  <app-heavy-chart [data]="chartData()" />
} @placeholder { <div class="chart-skeleton"></div> }
```

---

## When Using Signals

### 🔴 BLOCKING - Signal Update Rules

```typescript
// 🔴 WRONG - Direct mutation (won't trigger updates!)
this.items().push(newItem);
this.user().name = 'New Name';

// ✅ CORRECT - Create new reference
this.items.update(current => [...current, newItem]);
this.user.update(u => ({ ...u, name: 'New Name' }));
```

### 🟢 linkedSignal (Angular 21+)

```typescript
const selectedProduct = linkedSignal(() => {
  const id = selectedId();
  return products().find(p => p.id === id) ?? null;
});
```

### 🟢 Signal Queries (Angular 17.2+)

```typescript
readonly inputRef = viewChild.required<ElementRef>('myInput');
readonly items = viewChildren(ItemComponent);
readonly header = contentChild(HeaderDirective);
```

---

## When Managing State

📚 **References:** [angular-patterns.md](references/angular-patterns.md#ngrx-signal-store-angular-17) — Full NgRx Signal Store example

| Scope | Solution |
|-------|----------|
| Local (component) | `signal()`, `computed()` |
| Shared (feature/app) | NgRx Signal Store (`signalStore`, `withState`, `withMethods`) |

### 🔴 Key Rules
- Use `patchState()` for store updates (immutable)
- Use `withComputed()` for derived state
- Use `inject()` for services inside `withMethods()`

---

## When Building Forms

📚 **References:** [angular-patterns.md](references/angular-patterns.md#typed-reactive-forms) — Full typed form example | [signal-forms.md](references/signal-forms.md) — Experimental Signal Forms

### 🔴 BLOCKING - Typed Reactive Forms

- Always use `nonNullable: true` on controls
- Define a typed interface for the form group
- Use `getRawValue()` for typed submission values

### 🟢 Signal Forms (Angular 21+ Experimental)

> Experimental — API may change. Use Reactive Forms for production.

---

## When Making HTTP Calls

📚 **References:** [angular-patterns.md](references/angular-patterns.md#http-with-signals) — Full HTTP service + interceptor example

### 🔴 Key Rules
- Use `toSignal()` from `@angular/core/rxjs-interop` to bridge Observable → Signal
- Use functional interceptors (`HttpInterceptorFn`), not class-based
- Angular 21+: `HttpClient` auto-provided, `provideHttpClient()` only needed for interceptors

---

## When Configuring Routing

📚 **References:** [angular-patterns.md](references/angular-patterns.md#routing-standalone) — Functional guards, route config, lazy loading

### 🔴 Key Rules
- Use functional guards (`CanActivateFn`), not class-based
- Use `loadComponent` / `loadChildren` for lazy loading
- Configure in `app.routes.ts` (standalone, no NgModule)

---

## When Going Zoneless

> **Angular 21:** Zoneless is now the DEFAULT for new projects.

### 🔴 BLOCKING for Zoneless

- All state must use Signals
- Replace `provideZoneChangeDetection()` with `provideZonelessChangeDetection()`
- Remove `zone.js` from `polyfills` in `angular.json`
- `async` pipe still works (triggers signal updates)

---

## When Applying Design Tokens

📚 **References:** [design-tokens-angular.md](references/design-tokens-angular.md) — Full examples, Material integration, theming

### 🔴 BLOCKING — Use CSS Variables, Not Hardcoded Values

| Category | CSS Variable Pattern | Example |
|----------|---------------------|---------|
| Colors | `--color-{name}-{shade}` | `--color-primary-600` |
| Spacing | `--space-{size}` | `--space-8` (32px) |
| Typography | `--text-{size}` | `--text-lg` |
| Border Radius | `--radius-{size}` | `--radius-lg` |
| Shadows | `--shadow-{size}` | `--shadow-md` |

> See `common-frontend-design` skill for complete token definitions.

---

## When Writing Tests

### 🔴 Test Signal Inputs (Angular 17+)

```typescript
it('should display product name', () => {
  const fixture = TestBed.createComponent(ProductCardComponent);
  fixture.componentRef.setInput('product', { id: '1', name: 'Test', price: 29.99 });
  fixture.detectChanges();
  expect(fixture.nativeElement.querySelector('h3').textContent).toContain('Test');
});
```

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] Standalone components (no NgModule)
- [ ] New control flow (`@if`, `@for`, `@switch`)
- [ ] Signal inputs: `input()` / `input.required()`
- [ ] Signal outputs: `output()`
- [ ] Signal queries: `viewChild()`, `viewChildren()`
- [ ] No direct signal mutation → use `update()`
- [ ] Typed reactive forms with `nonNullable: true`
- [ ] Functional guards and interceptors
- [ ] `track` expression in all `@for` loops

### 🟡 WARNING
- [ ] Prefer signals over BehaviorSubject
- [ ] Use `computed()` for derived values
- [ ] Use `effect()` instead of `ngOnChanges`
- [ ] Consider `@defer` for heavy components
- [ ] Prefer zoneless (default in Angular 21+)
- [ ] No `[ngClass]` / `[ngStyle]` → use `[class]` / `[style]`

### 🟢 BEST PRACTICE
- [ ] NgRx Signal Store for complex state
- [ ] Resource API for data fetching (Angular 21+)
- [ ] `linkedSignal` for derived writable state
- [ ] `data-testid` attributes for test selectors
- [ ] Design tokens via CSS variables (see [design-tokens-angular.md](references/design-tokens-angular.md))

---

## Related Skills

- `common-typescript` — TypeScript patterns for Angular
- `common-frontend-design` — Design tokens, accessibility
- `common-frontend-testing` — Component and service testing
- `common-e2e-playwright` — E2E testing strategy
