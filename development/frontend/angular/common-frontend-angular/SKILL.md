---
name: common-frontend-angular
description: >-
  Frontend development with Angular 17–21 (current target: 21). Use this skill
  whenever the user asks to write or fix an Angular component, manage state with
  signals or NgRx, build a typed reactive form, configure routing or guards, set
  up an HTTP service or interceptor, migrate from older Angular APIs (`*ngIf`,
  `@Input`, `BehaviorSubject`), go zoneless, apply design tokens, test an
  Angular component, or review an Angular PR (components, services, stores,
  guards, interceptors, routes) — even when they don't explicitly say "Angular". Always
  loaded alongside `common-developer` for foundational craftsmanship rules
  (SOLID, Clean Code, Self-Review).
---

# Frontend Angular Skill (Angular 17–21)

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
> **Foundational rules** (SOLID, Clean Code, naming, self-review) live in `common-developer` — this skill covers Angular-specific guidance only.
> **Build note:** Angular has lazy compilation — some errors only surface during `npm run build`, not during `npm install` or `ng lint`. Always run a full build before claiming a fix complete.

---

## When Choosing Angular APIs (Modern vs Legacy)

Angular 21 is the current target. Older APIs are still **supported** but modern alternatives offer better performance, type safety, and zoneless compatibility.

| Legacy API | Modern Alternative | Since | Severity |
|------------|--------------------|-------|----------|
| `*ngIf`, `*ngFor`, `*ngSwitch` | `@if`, `@for`, `@switch` | 17.0 | 🔴 BLOCKING |
| `@Input()` decorator | `input()` / `input.required()` | 17.1 | 🟡 WARNING |
| `@Output()` decorator | `output()` | 17.3 | 🟡 WARNING |
| `@ViewChild()` / `@ViewChildren()` | `viewChild()` / `viewChildren()` | 17.2 | 🟡 WARNING |
| `[ngClass]` / `[ngStyle]` | `[class]` / `[style]` binding | 21.0 | 🟡 WARNING |
| `NgModule` for components | `standalone: true` | 14+ | 🟡 WARNING |
| Class-based guards/resolvers | Functional guards/resolvers | 15+ | 🟡 WARNING |
| `BehaviorSubject` for state | `signal()` / `computed()` | 16+ | 🟡 WARNING |
| `ngOnChanges` | `effect()` with signal inputs | 17+ | 🟡 WARNING |
| Zone.js change detection | Zoneless (default 21+) | 18+ | 🟡 WARNING |

📚 **When migrating from legacy Angular APIs (control flow, decorators, NgModules, zones) and you need the `ng generate @angular/core:control-flow` / signal-input / standalone / zoneless migration commands → read [migration-checklist.md](references/migration-checklist.md).**

### 🔴 BLOCKING

#### Use the new control flow (`@if`, `@for`, `@switch`) for any new template
**Why:** the new control flow is parsed at compile time, produces smaller bundles, gives correct type narrowing inside branches, and is required for zoneless compatibility. `*ngIf` / `*ngFor` go through structural directive instantiation — slower, less type-safe, and slated for deprecation.

##### WRONG
```html
<div *ngIf="user$ | async as user; else loading">{{ user.name }}</div>
<ng-template #loading>Loading…</ng-template>
<ul>
  <li *ngFor="let p of products; trackBy: trackById">{{ p.name }}</li>
</ul>
```
##### CORRECT
```html
@if (user(); as user) {
  <div>{{ user.name }}</div>
} @else {
  <p>Loading…</p>
}
@for (p of products(); track p.id) {
  <li>{{ p.name }}</li>
} @empty {
  <p>No products found</p>
}
```

---

## When Structuring Projects

```
src/app/
├── features/              # Feature modules (lazy loaded)
│   ├── auth/
│   │   ├── components/
│   │   ├── services/
│   │   ├── models/
│   │   └── routes.ts
│   └── catalog/
├── shared/                # Reusable across features
├── core/                  # Singleton services, guards, interceptors
├── app.config.ts          # provideRouter, provideHttpClient
└── app.routes.ts
```

| Aspect | Smart (Container) | Presentational (Dumb) |
|--------|-------------------|-----------------------|
| Data | Injects services | Receives via `input()` |
| State | Manages with signals | Stateless or local UI state |
| Reusability | Feature-specific | Highly reusable |

### 🔴 BLOCKING

#### Package by feature, not by layer
**Why:** a feature change touches a component, its template, its store, its tests. By-feature packaging keeps the change footprint local; by-layer (`components/`, `services/`, `pipes/` at the root) spreads it across the codebase and creates cross-cutting merge conflicts. (Same rule as `common-architecture` — applied here to Angular's directory layout.)

#### Split smart and dumb components
**Why:** mixing data-fetching and presentation in the same component blocks reuse (a presentational card cannot be reused if it injects a feature-specific service) and makes change detection harder to optimize. The split lets dumb components run with `OnPush` and trivial inputs.

---

## When Writing Components

📚 **When writing or reviewing a standalone component and you need worked patterns (signal-input templates, signal-output emission, `OnPush` skeletons, deferrable views) → read [angular-patterns.md](references/angular-patterns.md).**

### 🔴 BLOCKING

#### Every new component is `standalone: true` with `ChangeDetectionStrategy.OnPush` and signal-based inputs/outputs
**Why:** standalone removes the NgModule indirection (faster startup, simpler DI), `OnPush` cuts change-detection passes by an order of magnitude on real apps, and signal inputs/outputs are the only ones that work zoneless and with `linkedSignal`/`computed` chains. Decorator-based `@Input`/`@Output` block the zoneless migration.

##### WRONG
```typescript
@Component({
  selector: 'app-product-card',
  templateUrl: './product-card.component.html',
})
export class ProductCardComponent implements OnChanges {
  @Input() product!: Product;
  @Output() addToCart = new EventEmitter<Product>();

  ngOnChanges(changes: SimpleChanges) {
    if (changes['product']) { /* react to input change */ }
  }
}
```
##### CORRECT
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
  `,
})
export class ProductCardComponent {
  readonly product   = input.required<Product>();
  readonly showPrice = input(true);
  readonly addToCart = output<Product>();
  readonly available = computed(() => this.product().inStock);

  onAddToCart() { this.addToCart.emit(this.product()); }
}
```

---

## When Using Signals

### 🔴 BLOCKING

#### Never mutate the value held by a signal — produce a new reference
**Why:** signals detect change by reference equality on the value. Mutating in place (`items().push(x)`, `user().name = 'X'`) bypasses the equality check, the dependency graph never re-fires, and the UI silently goes stale. The `update()` callback enforces "produce a new reference" by construction.

##### WRONG
```typescript
this.items().push(newItem);              // mutates the array in place
this.user().name = 'New Name';           // mutates the object in place
```
##### CORRECT
```typescript
this.items.update(current => [...current, newItem]);
this.user.update(u => ({ ...u, name: 'New Name' }));
```

### 🟢 Modern Signal APIs (Angular 17+ / 21+)

```typescript
// Signal queries (17.2+)
readonly inputRef = viewChild.required<ElementRef>('myInput');
readonly items    = viewChildren(ItemComponent);
readonly header   = contentChild(HeaderDirective);

// linkedSignal — derived but writable (21+)
const selectedProduct = linkedSignal(() => {
  const id = selectedId();
  return products().find(p => p.id === id) ?? null;
});
```

---

## When Using Control Flow

### 🟢 Deferrable Views — Lazy Load Heavy Components

```html
@defer (on viewport) {
  <app-heavy-chart [data]="chartData()" />
} @placeholder {
  <div class="chart-skeleton"></div>
} @loading (after 200ms; minimum 500ms) {
  <app-spinner />
}
```

---

## When Managing State

📚 **When building a shared (feature/app-scoped) NgRx Signal Store with `withState` / `withComputed` / `withMethods` and `patchState` → read [angular-patterns.md#ngrx-signal-store-angular-17](references/angular-patterns.md#ngrx-signal-store-angular-17).**

| Scope | Solution |
|-------|----------|
| Local (component) | `signal()`, `computed()`, `effect()` |
| Shared (feature/app) | NgRx Signal Store (`signalStore`, `withState`, `withMethods`) |

### 🔴 BLOCKING

#### Use `patchState()` for store updates and `withComputed()` for derived state
**Why:** direct assignment to a signal store's state is not supported and breaks the immutable update contract that drives subscriber re-evaluation. `patchState` is the only mutation API that the store's reactivity tracks.

---

## When Building Forms

📚 **When building a Typed Reactive Form with `FormControl<T>`, `nonNullable: true`, and typed `getRawValue()` for submission → read [angular-patterns.md#typed-reactive-forms](references/angular-patterns.md#typed-reactive-forms).**

📚 **When experimenting with Angular 21+ Signal Forms (experimental API, not production) → read [signal-forms.md](references/signal-forms.md).**

### 🔴 BLOCKING

#### Use Typed Reactive Forms with `nonNullable: true` on every control
**Why:** without `nonNullable`, every control's value is typed as `T | null`, forcing `!` or null-checks at every access. With it, `getRawValue()` returns a fully-typed object that compiles directly into your DTO without runtime checks for nulls that the form itself would never produce.

```typescript
interface LoginForm {
  email:    FormControl<string>;
  password: FormControl<string>;
}

form = this.fb.group<LoginForm>({
  email:    this.fb.control('', { nonNullable: true, validators: [Validators.required, Validators.email] }),
  password: this.fb.control('', { nonNullable: true, validators: [Validators.required, Validators.minLength(8)] }),
});

onSubmit() {
  if (this.form.valid) {
    const { email, password } = this.form.getRawValue();   // fully typed, never null
  }
}
```

### 🟢 Signal Forms (Angular 21+ Experimental)
> API may change. Use Reactive Forms for production.

---

## When Making HTTP Calls

📚 **When writing an `HttpClient` service, a functional `HttpInterceptorFn`, or bridging an Observable to a signal with `toSignal()` → read [angular-patterns.md#http-with-signals](references/angular-patterns.md#http-with-signals).**

### 🔴 BLOCKING

#### Use functional interceptors (`HttpInterceptorFn`), never class-based
**Why:** class-based interceptors require `multi: true` provider boilerplate and don't compose cleanly with `provideHttpClient(withInterceptors(...))`. The functional form is what Angular 21 standardizes on; class-based interceptors are slated for deprecation.

#### Bridge Observable → Signal with `toSignal()`, not by manually subscribing in components
**Why:** manual `.subscribe()` in components leaks subscriptions on destroy, requires `takeUntilDestroyed` ceremony, and bypasses the change-detection optimizations Angular wires into signals. `toSignal()` handles cleanup, initial value, and integrates with `OnPush`.

---

## When Configuring Routing

📚 **When configuring standalone routes with functional guards (`CanActivateFn`) and lazy loading via `loadComponent` / `loadChildren` → read [angular-patterns.md#routing-standalone](references/angular-patterns.md#routing-standalone).**

### 🔴 BLOCKING

#### Use functional guards (`CanActivateFn`) and `loadComponent` / `loadChildren` for lazy loading
**Why:** functional guards are tree-shakable, accept normal `inject()`, and don't require the class-based `providedIn: 'root'` boilerplate. Lazy loading via `loadComponent`/`loadChildren` keeps the initial bundle small and is the only path that benefits from Angular's deferred-loading optimizations.

---

## When Going Zoneless

> **Angular 21:** Zoneless is the **default for new projects**.

### 🔴 BLOCKING

#### Going zoneless requires every reactive value to be a signal
**Why:** zoneless removes Zone.js, which is what triggers change detection on async operations (timers, XHR, events). Without it, anything that mutates a non-signal field becomes invisible to the renderer. A single `BehaviorSubject` left untouched will silently fail to re-render its subscribers.

##### Migration steps
1. Replace `provideZoneChangeDetection()` with `provideZonelessChangeDetection()`
2. Remove `zone.js` from `polyfills` in `angular.json`
3. Convert any remaining `BehaviorSubject` / class-field state to `signal()` / `toSignal()`
4. `async` pipe still works (pipe internally subscribes and pushes signal updates)

---

## When Applying Design Tokens

Token definitions, naming, and the never-hardcode 🔴 rule are **owned by the `common-frontend-design` skill** — load it when styling.

📚 **When integrating Angular Material palettes with tokens or wiring light/dark theme switching → read [design-tokens-angular.md](references/design-tokens-angular.md).**

---

## When Using Angular Material CDK Overlays

> Applies to any Material overlay primitive (`mat-select`, `mat-menu`, `mat-dialog`, `mat-autocomplete`, `mat-tooltip`) — i.e. anything rendered through the CDK `Overlay` service.

### 🟡 WARNING

#### Apply theme classes to `body`, never to `html`
**Why:** the CDK overlay container is appended to `body`, not inside the component tree. Theme classes set on `<html>` don't cascade into the overlay pane — popups render unthemed (wrong colors, missing typography). Applying themes to `<body>` is the only placement that reaches both the app tree and the overlay container.

#### Avoid CSS `transform` (and `perspective`, `filter`, `will-change: transform`) on any ancestor of an overlay trigger
**Why:** these properties create a new containing block for `position: fixed/absolute` elements (CSS positioned-ancestor rule). The CDK overlay then positions the pane relative to that ancestor instead of the viewport, misaligning popups (often by tens of pixels, sometimes off-screen). If a card animation needs `transform: scale(...)`, move the overlay trigger outside that subtree or remove the transform on the trigger's parent chain.

---

## When Writing Tests

> Component-test patterns and Angular Testing Library guidance live in `common-frontend-testing`. This snippet covers signal-input testing only.

### 🔴 BLOCKING

#### Set signal inputs via `componentRef.setInput()`, not by assigning a property
**Why:** signal inputs are read-only from outside the component class. Assigning `component.product = ...` either fails to compile or sets a stale value the signal never tracks. `setInput()` goes through the framework's input-binding pipeline and triggers the same reactivity as a parent template binding.

```typescript
it('should display product name', () => {
  const fixture = TestBed.createComponent(ProductCardComponent);
  fixture.componentRef.setInput('product', { id: '1', name: 'Test', price: 29.99 });
  fixture.detectChanges();
  expect(fixture.nativeElement.querySelector('h3').textContent).toContain('Test');
});
```

---

## Output Contract

When producing Angular artifacts, deliver each in this exact form:

| Artifact | Required Form |
|----------|---------------|
| **Component** (`*.component.ts`) | `standalone: true`, `ChangeDetectionStrategy.OnPush`, signal inputs (`input()` / `input.required()`), signal outputs (`output()`), new control flow in template, no `NgModule`. |
| **Service** (`*.service.ts`) | `@Injectable({ providedIn: 'root' })`, dependencies via `inject()`, `HttpClient` use returns either an Observable or `toSignal()`-wrapped signal — never a manual subscription. |
| **NgRx Signal Store** (`*.store.ts`) | `signalStore({ providedIn }, withState, withComputed, withMethods)`, mutations via `patchState`, derived state via `withComputed`. |
| **Functional guard** (`*.guard.ts`) | `export const xxxGuard: CanActivateFn = (route, state) => {...}` using `inject()` — no class. |
| **Functional interceptor** (`*.interceptor.ts`) | `export const xxxInterceptor: HttpInterceptorFn = (req, next) => {...}` — no class. |
| **Typed reactive form** | Interface `XxxForm` typing each `FormControl<T>`, `fb.group<XxxForm>(...)` with `nonNullable: true` on every control, submission reads `getRawValue()`. |
| **Component test** | `TestBed.createComponent(...)` + `componentRef.setInput(...)` for signal inputs + `detectChanges()` + DOM assertions. |
