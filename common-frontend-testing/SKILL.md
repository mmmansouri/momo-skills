---
name: common-frontend-testing
description: >-
  Frontend testing best practices with Jasmine (Angular default) and Angular Testing Library.
  Use when: writing unit tests for Angular components/services, mocking dependencies,
  testing async operations, setting up test fixtures, or choosing between Jasmine and Jest.
  Contains component testing patterns, service testing, and common pitfalls to avoid.
  Jasmine-first approach (Buy Nature standard), with Jest migration guidance.
---

# Frontend Testing Best Practices

> **Severity Levels:** 🔴 BLOCKING (must fix) | 🟡 WARNING (should fix) | 🟢 BEST PRACTICE (recommended)

---

## Testing Framework: Jasmine vs Jest

> **Buy Nature Projects:** Use **Jasmine** (Angular default). All code examples in this skill use Jasmine syntax.

### Why Jasmine for Buy Nature?

| Reason | Explanation |
|--------|-------------|
| **Angular Default** | Comes pre-configured with Angular CLI |
| **Zero Configuration** | Works out-of-the-box with Angular |
| **Mature Integration** | Deep integration with Angular testing utilities |
| **Team Standard** | Consistent across all Buy Nature projects |

### Syntax Comparison

| Operation | Jasmine (Buy Nature) | Jest (Alternative) |
|-----------|----------------------|-------------------|
| **Create spy** | `jasmine.createSpy('name')` | `jest.fn()` |
| **Spy on object** | `jasmine.createSpyObj('Service', ['method'])` | `jest.spyOn(obj, 'method')` |
| **Return value** | `spy.and.returnValue(value)` | `spy.mockReturnValue(value)` |
| **Return promise** | `spy.and.returnValue(Promise.resolve(value))` | `spy.mockResolvedValue(value)` |
| **Throw error** | `spy.and.throwError('error')` | `spy.mockImplementation(() => { throw new Error('error') })` |
| **Call through** | `spy.and.callThrough()` | `spy.mockImplementation()` |
| **Verify calls** | `expect(spy).toHaveBeenCalled()` | `expect(spy).toHaveBeenCalled()` (same) |

### 🟡 WARNING - Don't Mix Syntax

```typescript
// 🔴 WRONG - Mixing Jasmine and Jest syntax
const spy = jest.fn(); // Jest
spy.and.returnValue(data); // Jasmine - won't work!

// ✅ CORRECT - Consistent Jasmine
const spy = jasmine.createSpy('getData');
spy.and.returnValue(data);
```

### When to Consider Jest

Consider migrating to Jest if:
- You're starting a new non-Angular project
- You need better TypeScript support
- You want snapshot testing
- You need parallel test execution

**For Buy Nature:** Stick with Jasmine for consistency.

---

## Test Philosophy

### 🔴 BLOCKING — Test Behavior, Not Implementation

```typescript
// ❌ WRONG: Testing implementation details
it('should call private method _calculateTotal', () => {
  const spy = spyOn(component as any, '_calculateTotal');
  component.updateCart();
  expect(spy).toHaveBeenCalled();
});

// ✅ CORRECT: Test observable behavior
it('should display updated total when cart changes', () => {
  component.addItem({ id: '1', price: 10 });
  fixture.detectChanges();
  
  const total = fixture.nativeElement.querySelector('[data-testid="cart-total"]');
  expect(total.textContent).toContain('10');
});
```

### 🟢 BEST PRACTICE — Test Pyramid

```
         /\
        /  \        E2E Tests (few)
       /----\       - Critical user journeys
      /      \      - Use Playwright
     /--------\     Integration Tests (some)
    /          \    - Component + dependencies
   /------------\   Unit Tests (many)
  /              \  - Isolated logic
 /________________\ - Fast feedback
```

---

## Component Testing

### 🔴 BLOCKING — Always Use TestBed for Angular Components

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ProductCardComponent } from './product-card.component';

describe('ProductCardComponent', () => {
  let component: ProductCardComponent;
  let fixture: ComponentFixture<ProductCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductCardComponent], // Standalone component
      // declarations: [ProductCardComponent], // Module-based component
    }).compileComponents();

    fixture = TestBed.createComponent(ProductCardComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
```

### 🔴 BLOCKING — Call detectChanges() After State Changes

```typescript
// ❌ WRONG: Checking DOM before change detection
it('should display product name', () => {
  component.product = { name: 'Test Product', price: 99 };
  // Missing detectChanges()!
  const name = fixture.nativeElement.querySelector('.product-name');
  expect(name.textContent).toBe('Test Product'); // FAILS
});

// ✅ CORRECT: Trigger change detection
it('should display product name', () => {
  component.product = { name: 'Test Product', price: 99 };
  fixture.detectChanges(); // Required!
  
  const name = fixture.nativeElement.querySelector('.product-name');
  expect(name.textContent).toContain('Test Product');
});
```

### 🟡 WARNING — Use data-testid for Test Selectors

```typescript
// ❌ FRAGILE: CSS class or structure-based selectors
const button = fixture.nativeElement.querySelector('.btn.btn-primary.submit');
const title = fixture.nativeElement.querySelector('div > h1');

// ✅ ROBUST: data-testid attributes
const button = fixture.nativeElement.querySelector('[data-testid="submit-button"]');
const title = fixture.nativeElement.querySelector('[data-testid="page-title"]');
```

```html
<!-- In template -->
<button data-testid="submit-button" class="btn btn-primary">Submit</button>
<h1 data-testid="page-title">{{ title }}</h1>
```

### 🟢 BEST PRACTICE — Component Testing Patterns

📚 **Reference:** `references/component-patterns.md`

```typescript
describe('ProductListComponent', () => {
  let component: ProductListComponent;
  let fixture: ComponentFixture<ProductListComponent>;
  let productService: jasmine.SpyObj<ProductService>;

  beforeEach(async () => {
    // Create spy object for service
    const productServiceSpy = jasmine.createSpyObj('ProductService', ['getProducts']);

    await TestBed.configureTestingModule({
      imports: [ProductListComponent],
      providers: [
        { provide: ProductService, useValue: productServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ProductListComponent);
    component = fixture.componentInstance;
    productService = TestBed.inject(ProductService) as jasmine.SpyObj<ProductService>;
  });

  describe('initialization', () => {
    it('should load products on init', () => {
      const mockProducts = [{ id: '1', name: 'Product 1' }];
      productService.getProducts.and.returnValue(of(mockProducts));

      fixture.detectChanges(); // Triggers ngOnInit

      expect(productService.getProducts).toHaveBeenCalled();
      expect(component.products()).toEqual(mockProducts);
    });
  });

  describe('user interactions', () => {
    it('should filter products when search term changes', () => {
      // Arrange
      component.products.set([
        { id: '1', name: 'Apple' },
        { id: '2', name: 'Banana' }
      ]);
      fixture.detectChanges();

      // Act
      const searchInput = fixture.nativeElement.querySelector('[data-testid="search-input"]');
      searchInput.value = 'Apple';
      searchInput.dispatchEvent(new Event('input'));
      fixture.detectChanges();

      // Assert
      const productCards = fixture.nativeElement.querySelectorAll('[data-testid="product-card"]');
      expect(productCards.length).toBe(1);
    });
  });
});
```

---

## Service Testing

### 🔴 BLOCKING — Test Services in Isolation

```typescript
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ProductService } from './product.service';

describe('ProductService', () => {
  let service: ProductService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ProductService]
    });

    service = TestBed.inject(ProductService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    // Verify no outstanding HTTP requests
    httpMock.verify();
  });

  it('should fetch products', () => {
    const mockProducts = [{ id: '1', name: 'Product 1' }];

    service.getProducts().subscribe(products => {
      expect(products).toEqual(mockProducts);
    });

    const req = httpMock.expectOne('/api/products');
    expect(req.request.method).toBe('GET');
    req.flush(mockProducts);
  });

  it('should handle error response', () => {
    service.getProducts().subscribe({
      next: () => fail('should have failed'),
      error: (error) => {
        expect(error.status).toBe(500);
      }
    });

    const req = httpMock.expectOne('/api/products');
    req.flush('Error', { status: 500, statusText: 'Server Error' });
  });
});
```

### 🟢 BEST PRACTICE — Service with Dependencies

```typescript
describe('CartService', () => {
  let service: CartService;
  let storageService: jasmine.SpyObj<StorageService>;
  let analyticsService: jasmine.SpyObj<AnalyticsService>;

  beforeEach(() => {
    const storageSpy = jasmine.createSpyObj('StorageService', ['get', 'set']);
    const analyticsSpy = jasmine.createSpyObj('AnalyticsService', ['track']);

    TestBed.configureTestingModule({
      providers: [
        CartService,
        { provide: StorageService, useValue: storageSpy },
        { provide: AnalyticsService, useValue: analyticsSpy }
      ]
    });

    service = TestBed.inject(CartService);
    storageService = TestBed.inject(StorageService) as jasmine.SpyObj<StorageService>;
    analyticsService = TestBed.inject(AnalyticsService) as jasmine.SpyObj<AnalyticsService>;
  });

  it('should persist cart to storage when item added', () => {
    storageService.get.and.returnValue([]);

    service.addItem({ id: '1', name: 'Test', price: 10 });

    expect(storageService.set).toHaveBeenCalledWith('cart', jasmine.any(Array));
  });

  it('should track analytics when item added', () => {
    storageService.get.and.returnValue([]);

    service.addItem({ id: '1', name: 'Test', price: 10 });

    expect(analyticsService.track).toHaveBeenCalledWith('cart_item_added', {
      productId: '1',
      price: 10
    });
  });
});
```

---

## Mocking

### 🔴 BLOCKING — Only Mock External Dependencies

```typescript
// ❌ WRONG: Mocking internal logic
const spy = spyOn(component, 'calculateDiscount').and.returnValue(10);

// ✅ CORRECT: Mock external services
const discountService = jasmine.createSpyObj('DiscountService', ['getDiscount']);
discountService.getDiscount.and.returnValue(of(10));
```

### 🔴 BLOCKING — Mock HTTP, Never Real Calls

```typescript
// ❌ WRONG: Real HTTP calls in tests
beforeEach(() => {
  TestBed.configureTestingModule({
    imports: [HttpClientModule], // Real HTTP!
    providers: [ProductService]
  });
});

// ✅ CORRECT: Mock HTTP
beforeEach(() => {
  TestBed.configureTestingModule({
    imports: [HttpClientTestingModule], // Mocked HTTP
    providers: [ProductService]
  });
});
```

### 🟢 BEST PRACTICE — Creating Test Mocks

📚 **Reference:** `references/mocking-patterns.md`

```typescript
// Mock factory function
function createMockProductService(): jasmine.SpyObj<ProductService> {
  return jasmine.createSpyObj('ProductService', [
    'getProducts',
    'getProduct',
    'createProduct',
    'updateProduct',
    'deleteProduct'
  ]);
}

// Mock with default behaviors
function createMockProductServiceWithDefaults(): jasmine.SpyObj<ProductService> {
  const mock = createMockProductService();
  mock.getProducts.and.returnValue(of([]));
  mock.getProduct.and.returnValue(of(null));
  return mock;
}

// Partial mock (spy on real service)
it('should call real method with spy', () => {
  const service = TestBed.inject(ProductService);
  spyOn(service, 'getProducts').and.callThrough();
  
  // Test with real implementation but ability to verify calls
});
```

### 🟡 WARNING — Jasmine vs Jest Mocking Syntax

```typescript
// Jasmine
const spy = jasmine.createSpyObj('Service', ['method']);
spy.method.and.returnValue(of(data));
spyOn(object, 'method').and.returnValue(value);

// Jest
const spy = jest.fn().mockReturnValue(of(data));
jest.spyOn(object, 'method').mockReturnValue(value);
```

---

## Async Testing

### 🔴 BLOCKING — Use fakeAsync for Timer-Based Code

```typescript
import { fakeAsync, tick, flush } from '@angular/core/testing';

// ❌ WRONG: Real timers make tests slow and flaky
it('should debounce search', (done) => {
  component.searchTerm = 'test';
  setTimeout(() => {
    expect(component.results.length).toBeGreaterThan(0);
    done();
  }, 500); // Slow!
});

// ✅ CORRECT: Use fakeAsync and tick
it('should debounce search', fakeAsync(() => {
  component.searchTerm = 'test';
  tick(300); // Fast-forward 300ms
  
  expect(component.results.length).toBeGreaterThan(0);
}));

// ✅ CORRECT: flush() for all pending timers
it('should complete all animations', fakeAsync(() => {
  component.startAnimation();
  flush(); // Complete all pending timers
  
  expect(component.animationComplete).toBe(true);
}));
```

### 🔴 BLOCKING — Use waitForAsync for Promise-Based Code

```typescript
import { waitForAsync } from '@angular/core/testing';

it('should load data', waitForAsync(() => {
  component.loadData();
  
  fixture.whenStable().then(() => {
    expect(component.data).toBeDefined();
  });
}));
```

### 🟢 BEST PRACTICE — Testing Observables

```typescript
import { of, throwError, delay } from 'rxjs';

describe('Observable testing', () => {
  it('should handle observable with done callback', (done) => {
    service.getData().subscribe({
      next: (data) => {
        expect(data).toBeDefined();
        done();
      },
      error: done.fail
    });
  });

  it('should use fakeAsync for delayed observables', fakeAsync(() => {
    let result: string | undefined;
    
    of('test').pipe(delay(1000)).subscribe(v => result = v);
    
    expect(result).toBeUndefined();
    tick(1000);
    expect(result).toBe('test');
  }));

  it('should test observable errors', () => {
    productService.getProduct.and.returnValue(
      throwError(() => new Error('Not found'))
    );

    component.loadProduct('invalid-id');
    fixture.detectChanges();

    expect(component.error()).toBe('Not found');
  });
});
```

---

## Signal Testing (Angular 16+)

### 🔴 BLOCKING — Use Signal Accessors in Tests

```typescript
describe('Component with Signals', () => {
  it('should update computed signal', () => {
    // Arrange
    component.items.set([
      { price: 10 },
      { price: 20 }
    ]);

    // Assert - call signal as function
    expect(component.total()).toBe(30);
  });

  it('should react to signal changes', () => {
    component.count.set(5);
    fixture.detectChanges();

    const display = fixture.nativeElement.querySelector('[data-testid="count"]');
    expect(display.textContent).toContain('5');
  });
});
```

### 🟢 BEST PRACTICE — Testing Signal Effects

```typescript
import { TestBed, fakeAsync, tick } from '@angular/core/testing';

it('should trigger effect on signal change', fakeAsync(() => {
  const logSpy = spyOn(console, 'log');
  
  // Component has effect(() => console.log(this.value()))
  component.value.set('new value');
  tick(); // Effects run asynchronously
  
  expect(logSpy).toHaveBeenCalledWith('new value');
}));
```

---

## Test Organization

### 🟢 BEST PRACTICE — AAA Pattern (Arrange-Act-Assert)

```typescript
it('should calculate discount for premium user', () => {
  // Arrange
  const user: User = { id: '1', tier: 'premium' };
  const cart: CartItem[] = [
    { productId: 'p1', price: 100, quantity: 2 }
  ];
  component.user.set(user);
  component.cart.set(cart);

  // Act
  const discount = component.calculateDiscount();

  // Assert
  expect(discount).toBe(20); // 10% for premium
});
```

### 🟢 BEST PRACTICE — Descriptive Test Names

```typescript
// ❌ WRONG: Vague names
it('should work', () => {});
it('test discount', () => {});

// ✅ CORRECT: Describe behavior and context
describe('ProductCardComponent', () => {
  describe('when product is out of stock', () => {
    it('should display "Out of Stock" badge', () => {});
    it('should disable add to cart button', () => {});
    it('should show "Notify me" option', () => {});
  });

  describe('when product has discount', () => {
    it('should display original price with strikethrough', () => {});
    it('should display discounted price in red', () => {});
    it('should show discount percentage badge', () => {});
  });
});
```

### 🟢 BEST PRACTICE — Test File Structure

```typescript
describe('FeatureComponent', () => {
  // Setup
  let component: FeatureComponent;
  let fixture: ComponentFixture<FeatureComponent>;
  let mockService: jasmine.SpyObj<FeatureService>;

  beforeEach(async () => {
    // TestBed configuration
  });

  // Group related tests
  describe('initialization', () => {
    it('should create', () => {});
    it('should load initial data', () => {});
  });

  describe('user interactions', () => {
    describe('when clicking submit button', () => {
      it('should validate form', () => {});
      it('should show loading state', () => {});
      it('should submit data to service', () => {});
    });
  });

  describe('error handling', () => {
    it('should display error message on API failure', () => {});
    it('should allow retry on error', () => {});
  });

  describe('edge cases', () => {
    it('should handle empty data', () => {});
    it('should handle null response', () => {});
  });
});
```

---

## Common Pitfalls

### 🔴 BLOCKING — Don't Forget Cleanup

```typescript
describe('Component with subscriptions', () => {
  let subscription: Subscription;

  afterEach(() => {
    // Clean up subscriptions
    subscription?.unsubscribe();
  });

  it('should subscribe to data', () => {
    subscription = service.data$.subscribe(/* ... */);
  });
});
```

### 🔴 BLOCKING — Avoid Test Interdependence

```typescript
// ❌ WRONG: Tests depend on each other
let counter = 0;

it('should increment counter', () => {
  counter++;
  expect(counter).toBe(1);
});

it('should have counter at 1', () => {
  expect(counter).toBe(1); // Fails if first test doesn't run
});

// ✅ CORRECT: Each test is independent
beforeEach(() => {
  component.counter = 0;
});

it('should increment counter', () => {
  component.increment();
  expect(component.counter).toBe(1);
});
```

### 🟡 WARNING — Don't Test Framework Code

```typescript
// ❌ WRONG: Testing Angular's @Input decorator
it('should accept input', () => {
  component.title = 'Test';
  expect(component.title).toBe('Test'); // Pointless
});

// ✅ CORRECT: Test how input affects behavior
it('should display title in header', () => {
  component.title = 'Test';
  fixture.detectChanges();
  
  const header = fixture.nativeElement.querySelector('h1');
  expect(header.textContent).toContain('Test');
});
```

---

## Test Coverage Guidelines

### 🟢 BEST PRACTICE — What to Test

| Priority | What | Why |
|----------|------|-----|
| **High** | Business logic | Core functionality |
| **High** | User interactions | UX correctness |
| **High** | Error handling | Resilience |
| **Medium** | Edge cases | Robustness |
| **Medium** | Integration points | Contract verification |
| **Low** | Simple getters/setters | Low value |
| **Skip** | Framework code | Already tested |

### 🟡 WARNING — Coverage Targets

```
Aim for meaningful coverage, not 100%:
- Services: 80-90% (focus on business logic)
- Components: 70-80% (focus on interactions)
- Utils/Helpers: 90%+ (pure functions are easy to test)
- Models/Types: No runtime tests needed
```

---

## Related Skills

- `common-frontend-angular` — Angular testing patterns
- `common-typescript` — TypeScript test utilities
- `common-e2e-playwright` — E2E testing with Playwright
- `buy-nature-frontend-coding-guide` — Frontend testing philosophy
- `buy-nature-backoffice-coding-guide` — Backoffice testing patterns
