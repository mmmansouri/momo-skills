---
name: common-frontend-testing
description: >-
  Frontend unit and component testing for Angular projects using Jasmine + the
  Angular TestBed (with Angular Testing Library as an alternative). Use this
  skill whenever the user asks to write a unit test for a component, service,
  pipe or directive, spy on a service, mock an HTTP call, test an async
  observable, test a signal or effect, set up TestBed, or pick between Jasmine
  and Jest — even when they don't explicitly say "test". Always loaded alongside
  `common-developer` (foundational craftsmanship) and, for Angular projects,
  `common-frontend-angular` (component / service shapes under test).
---

# Frontend Testing Skill

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
> **Foundational rules** (SOLID, Clean Code, Self-Review, "every change ships with tests") live in `common-developer`. **Component / service shapes** under test live in `common-frontend-angular`. **E2E discipline** (browser-level user journeys) lives in `common-e2e-playwright`. This skill covers **unit & component tests only**.

---

## When Reasoning About Frontend Tests

Apply these foundational stances:

1. **Test behavior**, not implementation details.
2. **Isolation** — each test sets up its own state, no shared mutable globals.
3. **Fast** — milliseconds per test; no real HTTP, no real timers.
4. **Readable** — `should X when Y` test names; AAA structure.
5. **Boundaries first** — mock external collaborators, exercise the real internals.

### 🔴 BLOCKING

#### Test observable behavior, never private internals
**Why:** tests on private methods couple the suite to the current implementation. The first refactor that renames `_calculateTotal()` breaks every test that spied on it, even when the externally-visible behavior is unchanged. Tests on rendered output (DOM, return value, emitted event) survive any refactor that preserves the contract.

##### WRONG
```typescript
it('should call private method _calculateTotal', () => {
  const spy = spyOn(component as any, '_calculateTotal');
  component.updateCart();
  expect(spy).toHaveBeenCalled();
});
```
##### CORRECT
```typescript
it('should display updated total when cart changes', () => {
  component.addItem({ id: '1', price: 10 });
  fixture.detectChanges();

  const total = fixture.nativeElement.querySelector('[data-testid="cart-total"]');
  expect(total.textContent).toContain('10');
});
```

#### Each test is independent — fresh state in `beforeEach`, cleanup in `afterEach`
**Why:** order-dependent tests fail unpredictably under parallelism, hide the real defect when one breaks (N false positives downstream), and make the suite hostile to flake investigation. Independence is the property that makes the suite trustworthy.

##### WRONG
```typescript
let counter = 0;

it('should increment counter', () => {
  counter++;
  expect(counter).toBe(1);
});
it('should have counter at 1', () => {
  expect(counter).toBe(1);   // fails if previous test didn't run
});
```
##### CORRECT
```typescript
beforeEach(() => { component.counter = 0; });

it('should increment counter', () => {
  component.increment();
  expect(component.counter).toBe(1);
});
```

---

## When Choosing the Test Framework

**Default for Angular projects: Jasmine** (ships with Angular CLI, integrates with `TestBed`, no configuration overhead). All examples in this skill use Jasmine syntax.

Consider **Jest** for non-Angular projects, when you need built-in snapshot testing, or when parallel execution becomes a bottleneck.

### Jasmine ↔ Jest syntax (single source of truth)

| Operation | Jasmine | Jest |
|-----------|---------|------|
| Create spy function | `jasmine.createSpy('name')` | `jest.fn()` |
| Spy on a method | `spyOn(obj, 'method')` | `jest.spyOn(obj, 'method')` |
| Service-wide spy | `jasmine.createSpyObj('Svc', ['a','b'])` | manual `{ a: jest.fn(), b: jest.fn() }` |
| Return value | `spy.and.returnValue(v)` | `spy.mockReturnValue(v)` |
| Resolve promise | `spy.and.resolveTo(v)` | `spy.mockResolvedValue(v)` |
| Throw error | `spy.and.throwError('e')` | `spy.mockImplementation(() => { throw new Error('e') })` |
| Call through | `spy.and.callThrough()` | (no direct equivalent — use partial mocks) |
| Verify call | `expect(spy).toHaveBeenCalled()` | `expect(spy).toHaveBeenCalled()` |

### 🟡 WARNING

#### Never mix Jasmine and Jest syntax in the same test
**Why:** the runtime APIs are not interchangeable: `jest.fn()` does not have `.and.returnValue`, and `jasmine.createSpy()` does not have `.mockReturnValue`. Mixed code fails at the point of mismatch with a confusing TypeError, often paired with a passing-but-stale assertion above it.

---

## When Setting Up Component Tests

📚 **When configuring TestBed for a component, testing inputs/outputs, DOM interactions, conditional rendering, router, providers, child components or lifecycle hooks → read [testing-with-testbed.md](references/testing-with-testbed.md).**

📚 **When writing query-driven tests with `getByRole` / `getByTestId`, testing directives or pipes with Angular Testing Library, or considering snapshot testing as an alternative to TestBed → read [testing-with-testing-library.md](references/testing-with-testing-library.md).**

### 🔴 BLOCKING

#### Use `TestBed.configureTestingModule(...).compileComponents()` then `TestBed.createComponent(...)`
**Why:** TestBed is the only setup path that builds the component with Angular's real injector, change-detection, and lifecycle hooks. Bypassing TestBed (instantiating with `new MyComponent(...)`) skips DI, lifecycle hooks, and template compilation — the test then verifies a class that has nothing to do with what runs in production.

```typescript
beforeEach(async () => {
  await TestBed.configureTestingModule({
    imports: [ProductCardComponent],            // standalone
    providers: [
      { provide: ProductService, useValue: jasmine.createSpyObj('ProductService', ['getProducts']) },
    ],
  }).compileComponents();

  fixture = TestBed.createComponent(ProductCardComponent);
  component = fixture.componentInstance;
});
```

#### Call `fixture.detectChanges()` after every state change
**Why:** Angular does not auto-render in tests. A property change on the component class is invisible to the DOM until change detection runs. Asserting on the DOM without a `detectChanges()` test the previous state, not the change you just made.

##### WRONG
```typescript
component.product = { name: 'Test', price: 99 };
const name = fixture.nativeElement.querySelector('.product-name');
expect(name.textContent).toBe('Test');     // empty — fails
```
##### CORRECT
```typescript
component.product = { name: 'Test', price: 99 };
fixture.detectChanges();
const name = fixture.nativeElement.querySelector('.product-name');
expect(name.textContent).toContain('Test');
```

#### Use `data-testid` attributes for test selectors — never CSS classes or DOM structure
**Why:** classes belong to styling, structure belongs to the design system — both change for reasons unrelated to component behavior, breaking tests that depended on them. `data-testid` is an explicit test contract: it changes only when the test should change.

##### WRONG
```typescript
fixture.nativeElement.querySelector('.btn.btn-primary.submit');
fixture.nativeElement.querySelector('div > h1');
```
##### CORRECT
```typescript
fixture.nativeElement.querySelector('[data-testid="submit-button"]');
fixture.nativeElement.querySelector('[data-testid="page-title"]');
```

#### For signal inputs: set values via `componentRef.setInput('name', value)`, never by property assignment
**Why:** signal inputs are read-only on the component instance — direct assignment either fails to compile under strict mode or silently sets a stale field the signal never tracks. `setInput()` goes through Angular's input-binding pipeline, which is the same mechanism a parent template uses.

```typescript
fixture.componentRef.setInput('product', { id: '1', name: 'Test', price: 99 });
fixture.detectChanges();
```

---

## When Testing Services

📚 **When testing an Angular service — setting up `HttpClientTestingModule`, injecting test doubles via providers, or wiring up `HttpTestingController` for request assertions → read [testing-with-testbed.md](references/testing-with-testbed.md).**

### 🔴 BLOCKING

#### Use `HttpClientTestingModule` + `HttpTestingController` — never real HTTP
**Why:** real HTTP makes tests slow, flaky (network), and dependent on environment (which API is up?). The testing module intercepts `HttpClient` calls and lets the test assert on the request **and** craft the response synchronously.

##### WRONG
```typescript
TestBed.configureTestingModule({
  imports: [HttpClientModule],          // real HTTP — hits the network
  providers: [ProductService],
});
```
##### CORRECT
```typescript
TestBed.configureTestingModule({
  imports: [HttpClientTestingModule],
  providers: [ProductService],
});
afterEach(() => httpMock.verify());     // catch unexpected calls
```

#### Inject test doubles for every collaborator
**Why:** a service test that uses real collaborators is an integration test in disguise — it can break for reasons that have nothing to do with the unit under test, and the failure message points to the wrong file. Doubles isolate the cause.

```typescript
const storageSpy = jasmine.createSpyObj('StorageService', ['get', 'set']);
const analyticsSpy = jasmine.createSpyObj('AnalyticsService', ['track']);

TestBed.configureTestingModule({
  providers: [
    CartService,
    { provide: StorageService,   useValue: storageSpy },
    { provide: AnalyticsService, useValue: analyticsSpy },
  ],
});
```

---

## When Mocking

📚 **When building Jasmine spies, mocking services / HTTP / Router / forms / store state, or choosing between `createSpyObj` and `spyOn` for a specific collaborator → read [mocking-patterns.md](references/mocking-patterns.md).**

### 🔴 BLOCKING

#### Mock external dependencies only — never the unit under test's own internals
**Why:** mocking your own logic ("this method returns 10") inverts the test: you no longer verify the behavior, you verify that the test setup matches itself. The remaining assertions become tautologies.

##### WRONG
```typescript
const spy = spyOn(component, 'calculateDiscount').and.returnValue(10);
component.computeTotal();
expect(component.total).toBe(110);     // proves nothing about computeTotal
```
##### CORRECT
```typescript
const discountService = jasmine.createSpyObj('DiscountService', ['getDiscount']);
discountService.getDiscount.and.returnValue(of(10));
component.computeTotal();
expect(component.total).toBe(110);     // exercises real computeTotal logic
```

#### Use `jasmine.createSpyObj` for whole-service mocks; `spyOn` for single methods on a real instance
**Why:** `createSpyObj` produces a fully-typed mock with every method stubbed — no accidental real calls. `spyOn` keeps the real implementation but lets you assert call counts; use it only when you genuinely need partial mocking.

---

## When Testing Async Code

### 🔴 BLOCKING

#### Use `fakeAsync` + `tick(ms)` for timer-based code; never real `setTimeout`
**Why:** real timers turn 100 ms debounces into 100 ms tests. With 200 such tests the suite takes a full minute longer than necessary, and any timing skew produces flake. `fakeAsync` virtualizes the clock — `tick(300)` advances it instantly and synchronously.

##### WRONG
```typescript
it('should debounce search', (done) => {
  component.searchTerm = 'test';
  setTimeout(() => {
    expect(component.results.length).toBeGreaterThan(0);
    done();
  }, 500);                                      // 500 ms × N tests
});
```
##### CORRECT
```typescript
it('should debounce search', fakeAsync(() => {
  component.searchTerm = 'test';
  tick(300);                                    // instant
  expect(component.results.length).toBeGreaterThan(0);
}));
```

#### Use `waitForAsync` (or `await fixture.whenStable()`) for promise-based code
**Why:** the assertion must run after the microtask queue drains, otherwise the test passes/fails on the previous state. `waitForAsync` wraps the test in a zone that resolves only when all pending promises settle.

```typescript
it('should load data', waitForAsync(() => {
  component.loadData();
  fixture.whenStable().then(() => {
    expect(component.data).toBeDefined();
  });
}));
```

---

## When Testing Signals (Angular 17+)

### 🔴 BLOCKING

#### Read signals as functions in assertions — `signal()`, never `signal.value`
**Why:** signals are accessor functions, not properties. `signal.value` returns `undefined` on a regular signal (or the function reference on a writable one) — the assertion compares the wrong thing. `signal()` invokes the accessor, which is what production code does too.

```typescript
component.items.set([{ price: 10 }, { price: 20 }]);
expect(component.total()).toBe(30);             // function call
```

#### Use `fakeAsync` + `tick()` to flush effects
**Why:** `effect()` runs asynchronously through Angular's scheduler. A synchronous assertion after `signal.set()` runs before the effect has fired. `tick()` advances the scheduler in `fakeAsync` mode and lets the effect flush.

```typescript
it('should trigger effect on signal change', fakeAsync(() => {
  const logSpy = spyOn(console, 'log');
  component.value.set('new value');
  tick();
  expect(logSpy).toHaveBeenCalledWith('new value');
}));
```

---

## When Organizing Tests

### Naming

```typescript
// ❌ vague
it('should work', () => {});
it('test discount', () => {});

// ✅ describes behavior + context
describe('ProductCardComponent', () => {
  describe('when product is out of stock', () => {
    it('should display "Out of Stock" badge', () => {});
    it('should disable add to cart button', () => {});
  });
});
```

### 🟡 WARNING

#### Each test follows AAA — Arrange, Act, Assert — clearly separated
**Why:** mixed setup and assertions hide the test's intent. AAA makes the input, the trigger, and the expectation legible at a glance — when the test fails, the diagnosis is immediate.

#### Don't test framework code (decorators, untouched lifecycle shells)
**Why:** Angular already tests `@Input` binding and `ngOnInit` plumbing. A test that asserts `component.title === 'Test'` after assignment proves nothing about your code — it slows the suite for zero coverage value.

---

## When Deciding What to Cover

| Priority | What | Target |
|----------|------|--------|
| **High** | Business logic | 80–90 % |
| **High** | User interactions (DOM events → state) | 70–80 % |
| **High** | Error handling paths | every branch |
| **Medium** | Edge cases (empty, null, boundaries) | each documented |
| **Medium** | Integration points (service ↔ component) | contract verified |
| **Skip** | Trivial getters/setters, framework code | — |

> Aim for **meaningful coverage**, not 100 %. A 65 % suite that exercises every branch of business logic beats a 95 % suite that re-asserts framework code.

---

## Output Contract

When producing test artifacts, deliver each in this exact form:

| Artifact | Required Form |
|----------|---------------|
| **Component test** (`*.component.spec.ts`) | `TestBed.configureTestingModule + compileComponents`, signal inputs via `componentRef.setInput`, `data-testid` selectors, AAA per `it`, nested `describe` for context, fixture cleanup if subscriptions used. |
| **Service test** (`*.service.spec.ts`) | `HttpClientTestingModule` for HTTP, `jasmine.createSpyObj` for collaborators, `httpMock.verify()` in `afterEach`, error path covered. |
| **Spy / Mock** | `jasmine.createSpyObj('Svc', [...])` for whole-service mocks; `spyOn(obj, 'method')` for single methods; never `as any` to bypass typing. |
| **Async test** | `fakeAsync` + `tick(ms)` for timers/effects/signal updates; `waitForAsync` + `fixture.whenStable()` for promises; `(done) => {...}` only as a last resort. |
| **Test name** | `should <expected behavior> when <condition>` — verb, object, precondition. |
