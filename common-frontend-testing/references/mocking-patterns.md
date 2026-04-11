# Mocking Patterns for Angular Tests

> Comprehensive guide to creating effective mocks and spies for Angular testing.

---

## Jasmine Spy Basics

### Creating Spies

```typescript
// Spy on existing method
const spy = spyOn(service, 'getData');

// Spy with return value
spyOn(service, 'getData').and.returnValue(of(mockData));

// Spy with fake implementation
spyOn(service, 'processData').and.callFake((input) => {
  return input.toUpperCase();
});

// Spy that calls through to real implementation
spyOn(service, 'validate').and.callThrough();

// Spy that throws error
spyOn(service, 'riskyOperation').and.throwError('Failed');
```

### Spy Object (Full Mock)

```typescript
// Create mock with specified methods
const mockService = jasmine.createSpyObj('ServiceName', [
  'method1',
  'method2',
  'method3'
]);

// Create mock with methods AND properties
const mockService = jasmine.createSpyObj('ServiceName', 
  ['method1', 'method2'],  // Methods
  { propertyName: 'value' } // Properties
);

// Configure return values
mockService.method1.and.returnValue(of('result'));
mockService.method2.and.returnValue(Promise.resolve('async result'));
```

---

## Service Mocking Patterns

### Simple Service Mock

```typescript
// product.service.mock.ts
export function createMockProductService(): jasmine.SpyObj<ProductService> {
  return jasmine.createSpyObj('ProductService', [
    'getProducts',
    'getProduct',
    'createProduct',
    'updateProduct',
    'deleteProduct'
  ]);
}

// In test
describe('ProductListComponent', () => {
  let mockProductService: jasmine.SpyObj<ProductService>;

  beforeEach(async () => {
    mockProductService = createMockProductService();
    mockProductService.getProducts.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [ProductListComponent],
      providers: [
        { provide: ProductService, useValue: mockProductService }
      ]
    }).compileComponents();
  });
});
```

### Service Mock with Default Behaviors

```typescript
// auth.service.mock.ts
export function createMockAuthService(
  overrides: Partial<{
    isAuthenticated: boolean;
    currentUser: User | null;
  }> = {}
): jasmine.SpyObj<AuthService> {
  const defaults = {
    isAuthenticated: false,
    currentUser: null,
    ...overrides
  };

  const mock = jasmine.createSpyObj('AuthService', 
    ['login', 'logout', 'refreshToken'],
    {
      isAuthenticated$: of(defaults.isAuthenticated),
      currentUser$: of(defaults.currentUser)
    }
  );

  mock.login.and.returnValue(of({ token: 'mock-token' }));
  mock.logout.and.returnValue(of(void 0));
  mock.refreshToken.and.returnValue(of({ token: 'new-token' }));

  return mock;
}

// Usage
const mockAuth = createMockAuthService({ isAuthenticated: true });
```

### Service with Signal Properties

```typescript
// Angular 16+ with signals
export function createMockCartService(): jasmine.SpyObj<CartService> & {
  items: WritableSignal<CartItem[]>;
  total: Signal<number>;
} {
  const items = signal<CartItem[]>([]);
  const total = computed(() => items().reduce((sum, i) => sum + i.price, 0));

  const mock = jasmine.createSpyObj('CartService', [
    'addItem',
    'removeItem',
    'clear'
  ]) as any;

  mock.items = items;
  mock.total = total;

  mock.addItem.and.callFake((item: CartItem) => {
    items.update(current => [...current, item]);
  });

  mock.clear.and.callFake(() => {
    items.set([]);
  });

  return mock;
}
```

---

## HTTP Mocking

### HttpClientTestingModule Pattern

```typescript
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService]
    });

    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify(); // Verify no outstanding requests
  });

  it('should GET data', () => {
    const mockData = { id: 1, name: 'Test' };

    service.getData().subscribe(data => {
      expect(data).toEqual(mockData);
    });

    const req = httpMock.expectOne('/api/data');
    expect(req.request.method).toBe('GET');
    req.flush(mockData);
  });

  it('should POST data', () => {
    const payload = { name: 'New Item' };
    const response = { id: 1, ...payload };

    service.createItem(payload).subscribe(result => {
      expect(result).toEqual(response);
    });

    const req = httpMock.expectOne('/api/items');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(response);
  });

  it('should handle errors', () => {
    service.getData().subscribe({
      next: () => fail('should have errored'),
      error: (error) => {
        expect(error.status).toBe(404);
      }
    });

    const req = httpMock.expectOne('/api/data');
    req.flush('Not Found', { status: 404, statusText: 'Not Found' });
  });
});
```

### Multiple Request Matching

```typescript
it('should handle multiple requests', () => {
  service.getAll().subscribe();
  service.getById('1').subscribe();
  service.getById('2').subscribe();

  const requests = httpMock.match(req => req.url.startsWith('/api/'));
  expect(requests.length).toBe(3);

  requests.forEach(req => req.flush({}));
});

it('should match by URL pattern', () => {
  service.search('test').subscribe();

  const req = httpMock.expectOne(req => 
    req.url.includes('/search') && req.params.has('q')
  );
  expect(req.request.params.get('q')).toBe('test');
  req.flush([]);
});
```

---

## Router Mocking

### Mock ActivatedRoute

```typescript
// Simple route params
const mockActivatedRoute = {
  params: of({ id: '123' }),
  queryParams: of({ filter: 'active' }),
  snapshot: {
    params: { id: '123' },
    queryParams: { filter: 'active' },
    data: { title: 'Page Title' }
  }
};

// With paramMap
const mockActivatedRoute = {
  paramMap: of(convertToParamMap({ id: '123' })),
  queryParamMap: of(convertToParamMap({ filter: 'active' }))
};

// In TestBed
providers: [
  { provide: ActivatedRoute, useValue: mockActivatedRoute }
]
```

### Mock Router

```typescript
const mockRouter = jasmine.createSpyObj('Router', ['navigate', 'navigateByUrl']);
mockRouter.navigate.and.returnValue(Promise.resolve(true));

// With events
const mockRouter = {
  navigate: jasmine.createSpy('navigate').and.returnValue(Promise.resolve(true)),
  events: of(new NavigationEnd(1, '/', '/'))
};

providers: [
  { provide: Router, useValue: mockRouter }
]
```

---

## Form Mocking

### Mock FormBuilder Results

```typescript
// When testing a component that uses FormBuilder
describe('FormComponent', () => {
  it('should initialize with default values', () => {
    fixture.detectChanges();

    expect(component.form.get('email')?.value).toBe('');
    expect(component.form.get('password')?.value).toBe('');
  });

  it('should validate required fields', () => {
    fixture.detectChanges();

    expect(component.form.valid).toBe(false);

    component.form.patchValue({
      email: 'test@example.com',
      password: 'password123'
    });

    expect(component.form.valid).toBe(true);
  });
});
```

### Mock Validators Service

```typescript
const mockValidators = jasmine.createSpyObj('CustomValidators', [
  'emailExists',
  'passwordStrength'
]);

mockValidators.emailExists.and.returnValue(() => of(null)); // Valid
mockValidators.passwordStrength.and.returnValue(() => null); // Valid

providers: [
  { provide: CustomValidators, useValue: mockValidators }
]
```

---

## Store/State Mocking

### NgRx Store Mock

```typescript
import { provideMockStore, MockStore } from '@ngrx/store/testing';

describe('Component with NgRx', () => {
  let store: MockStore;

  const initialState = {
    products: {
      items: [],
      loading: false,
      error: null
    }
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MyComponent],
      providers: [
        provideMockStore({ initialState })
      ]
    }).compileComponents();

    store = TestBed.inject(MockStore);
  });

  it('should dispatch load action on init', () => {
    const dispatchSpy = spyOn(store, 'dispatch');
    fixture.detectChanges();

    expect(dispatchSpy).toHaveBeenCalledWith(loadProducts());
  });

  it('should show products from store', () => {
    store.setState({
      products: {
        items: [{ id: '1', name: 'Product 1' }],
        loading: false,
        error: null
      }
    });
    fixture.detectChanges();

    const items = fixture.nativeElement.querySelectorAll('[data-testid="product"]');
    expect(items.length).toBe(1);
  });

  it('should select data with selector', () => {
    store.overrideSelector(selectProducts, [{ id: '1', name: 'Test' }]);
    fixture.detectChanges();

    expect(component.products().length).toBe(1);
  });
});
```

### Signal Store Mock (NgRx 17+)

```typescript
// When using @ngrx/signals
const mockStore = {
  products: signal<Product[]>([]),
  loading: signal(false),
  error: signal<string | null>(null),
  loadProducts: jasmine.createSpy('loadProducts'),
  addProduct: jasmine.createSpy('addProduct')
};

providers: [
  { provide: ProductStore, useValue: mockStore }
]
```

---

## Utility Mocks

### Mock Window/Document

```typescript
// window.location
const mockWindow = {
  location: {
    href: 'http://localhost/',
    reload: jasmine.createSpy('reload')
  },
  localStorage: {
    getItem: jasmine.createSpy('getItem'),
    setItem: jasmine.createSpy('setItem'),
    removeItem: jasmine.createSpy('removeItem')
  }
};

providers: [
  { provide: 'Window', useValue: mockWindow }
]

// In component: @Inject('Window') private window: Window
```

### Mock Date/Time

```typescript
describe('time-sensitive tests', () => {
  beforeEach(() => {
    jasmine.clock().install();
    jasmine.clock().mockDate(new Date('2024-01-15T10:00:00Z'));
  });

  afterEach(() => {
    jasmine.clock().uninstall();
  });

  it('should format today correctly', () => {
    expect(component.formattedDate()).toBe('January 15, 2024');
  });

  it('should advance time', () => {
    component.startTimer();
    jasmine.clock().tick(5000); // Advance 5 seconds
    expect(component.elapsed()).toBe(5);
  });
});
```

### Mock Intersection Observer

```typescript
class MockIntersectionObserver {
  constructor(private callback: IntersectionObserverCallback) {}
  
  observe = jasmine.createSpy('observe');
  unobserve = jasmine.createSpy('unobserve');
  disconnect = jasmine.createSpy('disconnect');
  
  // Helper to trigger intersection
  triggerIntersection(entries: Partial<IntersectionObserverEntry>[]) {
    this.callback(entries as IntersectionObserverEntry[], this as any);
  }
}

beforeEach(() => {
  (window as any).IntersectionObserver = MockIntersectionObserver;
});
```

---

## Best Practices Summary

| Pattern | When to Use |
|---------|-------------|
| `jasmine.createSpyObj` | Full mock of a service |
| `spyOn().and.returnValue` | Mock single method on real object |
| `HttpTestingController` | Test HTTP calls |
| Mock factories | Reusable mocks with defaults |
| `provideMockStore` | NgRx state testing |
| Partial mocks | When you need some real behavior |

### Avoid

- ❌ Mocking too much (loses integration confidence)
- ❌ Mocking internal/private methods
- ❌ Complex mock setups that are hard to understand
- ❌ Mocks that don't match real behavior
