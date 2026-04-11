# Component Testing Patterns

> Complete patterns for testing Angular components effectively.

---

## Standalone Component Setup

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

describe('StandaloneComponent', () => {
  let component: StandaloneComponent;
  let fixture: ComponentFixture<StandaloneComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StandaloneComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        // Other providers
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(StandaloneComponent);
    component = fixture.componentInstance;
  });
});
```

---

## Testing Inputs

### Simple Inputs

```typescript
describe('ProductCardComponent', () => {
  it('should display product name', () => {
    // Using setInput (Angular 14.1+)
    fixture.componentRef.setInput('product', { 
      name: 'Test Product', 
      price: 99 
    });
    fixture.detectChanges();

    const name = fixture.nativeElement.querySelector('[data-testid="product-name"]');
    expect(name.textContent).toContain('Test Product');
  });

  // Alternative: direct property assignment
  it('should display product price', () => {
    component.product = { name: 'Test', price: 99 };
    fixture.detectChanges();

    const price = fixture.nativeElement.querySelector('[data-testid="product-price"]');
    expect(price.textContent).toContain('99');
  });
});
```

### Signal Inputs (Angular 17.1+)

```typescript
describe('Component with signal inputs', () => {
  it('should handle signal input', () => {
    // Signal inputs are set via setInput
    fixture.componentRef.setInput('title', 'Hello World');
    fixture.detectChanges();

    expect(component.title()).toBe('Hello World');
  });
});
```

### Required Inputs

```typescript
describe('Component with required input', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ComponentWithRequiredInput]
    }).compileComponents();

    fixture = TestBed.createComponent(ComponentWithRequiredInput);
    component = fixture.componentInstance;
    
    // Must set required input before detectChanges
    fixture.componentRef.setInput('requiredData', mockData);
  });
});
```

---

## Testing Outputs

### Event Emitter Outputs

```typescript
describe('ProductCardComponent outputs', () => {
  it('should emit addToCart event when button clicked', () => {
    const addToCartSpy = spyOn(component.addToCart, 'emit');
    component.product = { id: '1', name: 'Test', price: 99 };
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('[data-testid="add-to-cart"]');
    button.click();

    expect(addToCartSpy).toHaveBeenCalledWith({ id: '1', name: 'Test', price: 99 });
  });

  // Alternative: subscribe to output
  it('should emit event with product data', (done) => {
    component.product = { id: '1', name: 'Test', price: 99 };
    fixture.detectChanges();

    component.addToCart.subscribe((product) => {
      expect(product.id).toBe('1');
      done();
    });

    const button = fixture.nativeElement.querySelector('[data-testid="add-to-cart"]');
    button.click();
  });
});
```

### Output Signals (Angular 17.3+)

```typescript
describe('Component with output signals', () => {
  it('should emit via output signal', () => {
    const spy = jasmine.createSpy('outputSpy');
    
    // Subscribe to the output signal's observable
    component.valueChange.subscribe(spy);
    
    // Trigger the output
    component.updateValue('new value');
    
    expect(spy).toHaveBeenCalledWith('new value');
  });
});
```

---

## Testing DOM Interactions

### Click Events

```typescript
it('should toggle expanded state on click', () => {
  expect(component.isExpanded()).toBe(false);

  const header = fixture.nativeElement.querySelector('[data-testid="accordion-header"]');
  header.click();
  fixture.detectChanges();

  expect(component.isExpanded()).toBe(true);
  
  const content = fixture.nativeElement.querySelector('[data-testid="accordion-content"]');
  expect(content).toBeTruthy();
});
```

### Form Inputs

```typescript
it('should update model on input', () => {
  fixture.detectChanges();

  const input = fixture.nativeElement.querySelector('[data-testid="email-input"]');
  input.value = 'test@example.com';
  input.dispatchEvent(new Event('input'));
  fixture.detectChanges();

  expect(component.email()).toBe('test@example.com');
});

// For reactive forms
it('should update form control', () => {
  const input = fixture.nativeElement.querySelector('[data-testid="email-input"]');
  input.value = 'test@example.com';
  input.dispatchEvent(new Event('input'));

  expect(component.form.get('email')?.value).toBe('test@example.com');
});
```

### Select/Dropdown

```typescript
it('should update on selection change', () => {
  fixture.detectChanges();

  const select = fixture.nativeElement.querySelector('[data-testid="category-select"]');
  select.value = 'electronics';
  select.dispatchEvent(new Event('change'));
  fixture.detectChanges();

  expect(component.selectedCategory()).toBe('electronics');
});
```

### Keyboard Events

```typescript
it('should submit on Enter key', () => {
  const submitSpy = spyOn(component, 'submit');
  fixture.detectChanges();

  const input = fixture.nativeElement.querySelector('[data-testid="search-input"]');
  const event = new KeyboardEvent('keyup', { key: 'Enter' });
  input.dispatchEvent(event);

  expect(submitSpy).toHaveBeenCalled();
});
```

---

## Testing Conditional Rendering

### *ngIf / @if

```typescript
describe('conditional rendering', () => {
  it('should show loading spinner when loading', () => {
    component.isLoading.set(true);
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector('[data-testid="loading-spinner"]');
    const content = fixture.nativeElement.querySelector('[data-testid="content"]');

    expect(spinner).toBeTruthy();
    expect(content).toBeNull();
  });

  it('should show content when loaded', () => {
    component.isLoading.set(false);
    component.data.set({ title: 'Test' });
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector('[data-testid="loading-spinner"]');
    const content = fixture.nativeElement.querySelector('[data-testid="content"]');

    expect(spinner).toBeNull();
    expect(content).toBeTruthy();
  });
});
```

### *ngFor / @for

```typescript
it('should render list items', () => {
  component.items.set([
    { id: '1', name: 'Item 1' },
    { id: '2', name: 'Item 2' },
    { id: '3', name: 'Item 3' }
  ]);
  fixture.detectChanges();

  const items = fixture.nativeElement.querySelectorAll('[data-testid="list-item"]');
  expect(items.length).toBe(3);
  expect(items[0].textContent).toContain('Item 1');
});

it('should show empty state when no items', () => {
  component.items.set([]);
  fixture.detectChanges();

  const emptyState = fixture.nativeElement.querySelector('[data-testid="empty-state"]');
  expect(emptyState).toBeTruthy();
});
```

---

## Testing with Router

```typescript
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';

describe('NavigationComponent', () => {
  let harness: RouterTestingHarness;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      providers: [
        provideRouter([
          { path: 'products', component: ProductListComponent },
          { path: 'products/:id', component: ProductDetailComponent }
        ])
      ]
    }).compileComponents();

    harness = await RouterTestingHarness.create();
  });

  it('should navigate to product detail', async () => {
    const component = await harness.navigateByUrl('/products/123', ProductDetailComponent);
    
    expect(component.productId()).toBe('123');
  });
});

// Testing router link clicks
describe('NavComponent', () => {
  it('should navigate on link click', fakeAsync(() => {
    const router = TestBed.inject(Router);
    const navigateSpy = spyOn(router, 'navigate');

    const link = fixture.nativeElement.querySelector('[data-testid="products-link"]');
    link.click();
    tick();

    expect(navigateSpy).toHaveBeenCalledWith(['/products']);
  }));
});
```

---

## Testing with Providers

### Override Providers

```typescript
beforeEach(async () => {
  await TestBed.configureTestingModule({
    imports: [MyComponent]
  })
  .overrideComponent(MyComponent, {
    set: {
      providers: [
        { provide: MyService, useValue: mockService }
      ]
    }
  })
  .compileComponents();
});
```

### Injection Token Testing

```typescript
import { InjectionToken } from '@angular/core';

const API_URL = new InjectionToken<string>('API_URL');

beforeEach(async () => {
  await TestBed.configureTestingModule({
    imports: [MyComponent],
    providers: [
      { provide: API_URL, useValue: 'http://test-api.com' }
    ]
  }).compileComponents();
});
```

---

## Testing Child Components

### With NO_ERRORS_SCHEMA (Quick but Less Safe)

```typescript
import { NO_ERRORS_SCHEMA } from '@angular/core';

beforeEach(async () => {
  await TestBed.configureTestingModule({
    imports: [ParentComponent],
    schemas: [NO_ERRORS_SCHEMA] // Ignores unknown elements
  }).compileComponents();
});
```

### With Mock Components (Preferred)

```typescript
@Component({
  selector: 'app-child',
  standalone: true,
  template: '<ng-content></ng-content>'
})
class MockChildComponent {
  @Input() data: any;
  @Output() action = new EventEmitter<void>();
}

beforeEach(async () => {
  await TestBed.configureTestingModule({
    imports: [ParentComponent]
  })
  .overrideComponent(ParentComponent, {
    remove: { imports: [ChildComponent] },
    add: { imports: [MockChildComponent] }
  })
  .compileComponents();
});
```

---

## Testing Lifecycle Hooks

```typescript
describe('lifecycle hooks', () => {
  it('should call service on init', () => {
    const loadSpy = spyOn(mockService, 'load').and.returnValue(of([]));
    
    fixture.detectChanges(); // Triggers ngOnInit
    
    expect(loadSpy).toHaveBeenCalled();
  });

  it('should cleanup on destroy', () => {
    fixture.detectChanges();
    const unsubscribeSpy = spyOn(component['subscription'], 'unsubscribe');
    
    fixture.destroy();
    
    expect(unsubscribeSpy).toHaveBeenCalled();
  });

  it('should react to input changes', () => {
    component.productId = '1';
    fixture.detectChanges();
    
    component.productId = '2';
    fixture.detectChanges();
    
    // ngOnChanges should have been called
    expect(mockService.getProduct).toHaveBeenCalledWith('2');
  });
});
```

---

## Debug Utilities

```typescript
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';

describe('debugging', () => {
  it('should find element by directive', () => {
    const debugEl: DebugElement = fixture.debugElement;
    
    // By CSS selector
    const button = debugEl.query(By.css('[data-testid="submit"]'));
    
    // By directive
    const tooltips = debugEl.queryAll(By.directive(TooltipDirective));
    
    // Access native element
    const nativeButton = button.nativeElement as HTMLButtonElement;
    
    // Access component instance
    const tooltipComponent = tooltips[0].componentInstance;
  });

  it('should inspect component state', () => {
    console.log('Component:', component);
    console.log('DOM:', fixture.nativeElement.innerHTML);
  });
});
```
