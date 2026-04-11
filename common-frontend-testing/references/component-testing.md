# Angular Component Testing Patterns

## Testing Library Setup

### Installation

```bash
npm install -D @testing-library/angular @testing-library/jest-dom
```

### Configuration (jest-setup.ts)

```typescript
import '@testing-library/jest-dom';
```

---

## Query Priority

Use queries in this order (most to least preferred):

| Priority | Query | When to Use |
|----------|-------|-------------|
| 1 | `getByRole` | Interactive elements (buttons, inputs) |
| 2 | `getByLabelText` | Form fields with labels |
| 3 | `getByPlaceholderText` | Inputs with placeholder |
| 4 | `getByText` | Non-interactive text content |
| 5 | `getByDisplayValue` | Current value of form element |
| 6 | `getByAltText` | Images |
| 7 | `getByTitle` | Elements with title attribute |
| 8 | `getByTestId` | Last resort (data-testid) |

### Query Variants

| Variant | Returns | Throws | Async |
|---------|---------|--------|-------|
| `getBy*` | Element | Yes | No |
| `queryBy*` | Element or null | No | No |
| `findBy*` | Promise<Element> | Yes | Yes |
| `getAllBy*` | Element[] | Yes | No |
| `queryAllBy*` | Element[] | No | No |
| `findAllBy*` | Promise<Element[]> | Yes | Yes |

---

## Standalone Component Testing

### Basic Standalone Component

```typescript
// counter.component.ts
@Component({
  selector: 'app-counter',
  standalone: true,
  template: `
    <button (click)="decrement()">-</button>
    <span data-testid="count">{{ count() }}</span>
    <button (click)="increment()">+</button>
  `,
})
export class CounterComponent {
  count = signal(0);

  increment() { this.count.update(c => c + 1); }
  decrement() { this.count.update(c => c - 1); }
}

// counter.component.spec.ts
describe('CounterComponent', () => {
  it('should start at zero', async () => {
    await render(CounterComponent);
    expect(screen.getByTestId('count')).toHaveTextContent('0');
  });

  it('should increment when + clicked', async () => {
    await render(CounterComponent);
    
    fireEvent.click(screen.getByRole('button', { name: '+' }));
    
    expect(screen.getByTestId('count')).toHaveTextContent('1');
  });

  it('should decrement when - clicked', async () => {
    const { fixture } = await render(CounterComponent);
    fixture.componentInstance.count.set(5);
    fixture.detectChanges();
    
    fireEvent.click(screen.getByRole('button', { name: '-' }));
    
    expect(screen.getByTestId('count')).toHaveTextContent('4');
  });
});
```

### Component with Input Signals

```typescript
// greeting.component.ts
@Component({
  selector: 'app-greeting',
  standalone: true,
  template: `<h1>Hello, {{ name() }}!</h1>`,
})
export class GreetingComponent {
  name = input.required<string>();
}

// greeting.component.spec.ts
describe('GreetingComponent', () => {
  it('should display the name', async () => {
    await render(GreetingComponent, {
      componentInputs: { name: 'World' },
    });
    
    expect(screen.getByRole('heading')).toHaveTextContent('Hello, World!');
  });

  it('should update when input changes', async () => {
    const { fixture } = await render(GreetingComponent, {
      componentInputs: { name: 'World' },
    });
    
    fixture.componentRef.setInput('name', 'Angular');
    fixture.detectChanges();
    
    expect(screen.getByRole('heading')).toHaveTextContent('Hello, Angular!');
  });
});
```

### Component with Output

```typescript
// button.component.ts
@Component({
  selector: 'app-action-button',
  standalone: true,
  template: `<button (click)="clicked.emit()">{{ label() }}</button>`,
})
export class ActionButtonComponent {
  label = input('Click me');
  clicked = output<void>();
}

// button.component.spec.ts
describe('ActionButtonComponent', () => {
  it('should emit clicked when button pressed', async () => {
    const handleClick = jest.fn();
    
    await render(ActionButtonComponent, {
      componentOutputs: { clicked: handleClick },
    });
    
    fireEvent.click(screen.getByRole('button'));
    
    expect(handleClick).toHaveBeenCalled();
  });
});
```

---

## Component with Dependencies

### Service Injection

```typescript
// user-profile.component.ts
@Component({
  selector: 'app-user-profile',
  standalone: true,
  template: `
    @if (loading()) {
      <p>Loading...</p>
    } @else if (error()) {
      <p role="alert">{{ error() }}</p>
    } @else {
      <h1>{{ user()?.name }}</h1>
      <p>{{ user()?.email }}</p>
    }
  `,
})
export class UserProfileComponent implements OnInit {
  private userService = inject(UserService);
  
  user = signal<User | null>(null);
  loading = signal(true);
  error = signal<string | null>(null);

  ngOnInit() {
    this.userService.getCurrentUser().subscribe({
      next: (user) => {
        this.user.set(user);
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(e.message);
        this.loading.set(false);
      },
    });
  }
}

// user-profile.component.spec.ts
describe('UserProfileComponent', () => {
  const mockUser: User = { id: '1', name: 'John', email: 'john@example.com' };

  it('should show loading initially', async () => {
    const userService = { getCurrentUser: () => NEVER };
    
    await render(UserProfileComponent, {
      providers: [{ provide: UserService, useValue: userService }],
    });
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should display user after loading', async () => {
    const userService = { getCurrentUser: () => of(mockUser) };
    
    await render(UserProfileComponent, {
      providers: [{ provide: UserService, useValue: userService }],
    });
    
    expect(await screen.findByRole('heading')).toHaveTextContent('John');
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('should show error message on failure', async () => {
    const userService = {
      getCurrentUser: () => throwError(() => new Error('Network error')),
    };
    
    await render(UserProfileComponent, {
      providers: [{ provide: UserService, useValue: userService }],
    });
    
    expect(await screen.findByRole('alert')).toHaveTextContent('Network error');
  });
});
```

### Router Testing

```typescript
// navigation.component.spec.ts
describe('NavigationComponent', () => {
  it('should navigate to /about when link clicked', async () => {
    const router = { navigate: jest.fn() };
    
    await render(NavigationComponent, {
      providers: [{ provide: Router, useValue: router }],
    });
    
    fireEvent.click(screen.getByRole('link', { name: /about/i }));
    
    expect(router.navigate).toHaveBeenCalledWith(['/about']);
  });
});

// With RouterTestingModule for full routing
describe('AppComponent routing', () => {
  it('should render home component at /', async () => {
    await render(AppComponent, {
      imports: [
        RouterTestingModule.withRoutes([
          { path: '', component: HomeComponent },
          { path: 'about', component: AboutComponent },
        ]),
      ],
    });
    
    expect(screen.getByText('Welcome Home')).toBeInTheDocument();
  });
});
```

---

## Testing Directives

### Attribute Directive

```typescript
// highlight.directive.ts
@Directive({
  selector: '[appHighlight]',
  standalone: true,
})
export class HighlightDirective {
  color = input('yellow', { alias: 'appHighlight' });
  
  @HostBinding('style.backgroundColor')
  get bgColor() { return this.color(); }
}

// highlight.directive.spec.ts
describe('HighlightDirective', () => {
  @Component({
    standalone: true,
    imports: [HighlightDirective],
    template: `<p appHighlight="cyan">Test</p>`,
  })
  class TestComponent {}

  it('should apply background color', async () => {
    await render(TestComponent);
    
    expect(screen.getByText('Test')).toHaveStyle({ backgroundColor: 'cyan' });
  });
});
```

---

## Testing Pipes

```typescript
// currency.pipe.ts
@Pipe({ name: 'appCurrency', standalone: true })
export class CurrencyPipe implements PipeTransform {
  transform(value: number, currency = 'USD'): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(value);
  }
}

// currency.pipe.spec.ts
describe('CurrencyPipe', () => {
  const pipe = new CurrencyPipe();

  it('should format as USD by default', () => {
    expect(pipe.transform(19.99)).toBe('$19.99');
  });

  it('should format with specified currency', () => {
    expect(pipe.transform(19.99, 'EUR')).toBe('€19.99');
  });

  it('should handle zero', () => {
    expect(pipe.transform(0)).toBe('$0.00');
  });
});
```

---

## Snapshot Testing

```typescript
describe('CardComponent', () => {
  it('should match snapshot', async () => {
    const { container } = await render(CardComponent, {
      componentInputs: {
        title: 'Test Card',
        description: 'This is a test',
      },
    });
    
    expect(container).toMatchSnapshot();
  });
});
```

⚠️ **Warning**: Use snapshots sparingly. They're brittle and often auto-approved without review.

---

## Common Patterns

### Waiting for Async Content

```typescript
// Use findBy* for elements that appear asynchronously
const element = await screen.findByText('Loaded content');

// Use waitFor for conditions
await waitFor(() => {
  expect(screen.queryByText('Loading')).not.toBeInTheDocument();
});

// Use waitForElementToBeRemoved
await waitForElementToBeRemoved(() => screen.queryByText('Loading'));
```

### Testing Conditional Rendering

```typescript
it('should show login button when not authenticated', async () => {
  const authService = { isAuthenticated: () => false };
  
  await render(HeaderComponent, {
    providers: [{ provide: AuthService, useValue: authService }],
  });
  
  expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /logout/i })).not.toBeInTheDocument();
});
```

### Testing Lists

```typescript
it('should render all items', async () => {
  await render(ItemListComponent, {
    componentInputs: { items: ['A', 'B', 'C'] },
  });
  
  const listItems = screen.getAllByRole('listitem');
  expect(listItems).toHaveLength(3);
  expect(listItems[0]).toHaveTextContent('A');
});
```
