# Code Review Checklist

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Code review is a learning opportunity, not blame assignment. Focus on design, logic, and maintainability.

---

## General Principles

### 🔴 BLOCKING - Must Be Fixed

- [ ] Code builds without errors
- [ ] All tests pass (unit + integration)
- [ ] No security vulnerabilities
- [ ] No hardcoded secrets/credentials
- [ ] Follows project coding standards
- [ ] Breaking changes documented

### 🟡 WARNING - Should Be Addressed

- [ ] Code smells (long methods, God classes)
- [ ] Missing tests for new features
- [ ] Poor naming (unclear, abbreviated)
- [ ] Commented-out code
- [ ] Console.log / System.out.println left in code

### 🟢 BEST PRACTICE - Nice to Have

- [ ] Javadoc/JSDoc for public APIs
- [ ] Performance optimizations
- [ ] Accessibility improvements
- [ ] Refactoring opportunities

---

## Backend Checklist (Java/Spring)

### Architecture & Design

```markdown
## Architecture Review
- [ ] Follows Clean Architecture layers (Domain → Application → Infrastructure)
- [ ] Package by feature, not by layer
- [ ] DTOs follow naming: *CreationRequest, *UpdateRequest, *RetrievalResponse
- [ ] Services orchestrate, repositories persist, entities hold business logic
- [ ] No cyclic dependencies between packages

## Domain Layer
- [ ] Entities use UUID primary keys
- [ ] JPA relationships properly mapped (@ManyToOne, @OneToMany)
- [ ] Bidirectional relationships have helper methods
- [ ] equals() and hashCode() implemented correctly
- [ ] No business logic in getters/setters

## Application Layer
- [ ] Services are transactional where needed (@Transactional)
- [ ] Service methods have single responsibility
- [ ] DTOs validate input (@Valid, @NotNull, @NotEmpty)
- [ ] Error handling uses domain exceptions
- [ ] No repository logic in controllers

## Infrastructure Layer
- [ ] Repository follows 3-layer pattern (if complex queries)
- [ ] Custom queries use @Query or Criteria API
- [ ] N+1 queries avoided (JOIN FETCH, EntityGraph)
- [ ] Pagination used for large result sets
```

### Code Quality

```markdown
## SOLID Principles
- [ ] Single Responsibility: Each class has one reason to change
- [ ] Open/Closed: Extension via interfaces, not modification
- [ ] Liskov Substitution: Subtypes don't break contracts
- [ ] Interface Segregation: Specific interfaces, not fat ones
- [ ] Dependency Inversion: Depend on abstractions, inject dependencies

## Clean Code
- [ ] Method names are verbs (calculateTotal, sendEmail)
- [ ] Class names are nouns (Order, Customer, OrderService)
- [ ] Variables have meaningful names (no abbreviations)
- [ ] Functions are small (< 20 lines ideally)
- [ ] Max 3 parameters (use DTOs for more)
- [ ] No magic numbers/strings (use constants/enums)
- [ ] Comments explain WHY, not WHAT

## Error Handling
- [ ] Exceptions for errors, not error codes
- [ ] Custom exceptions extend meaningful base classes
- [ ] RFC 7807 Problem Details for REST errors
- [ ] No generic catch(Exception e) without re-throw
- [ ] Resources properly closed (try-with-resources)
```

### Java 25 Features

```markdown
## Modern Java Usage
- [ ] Records for DTOs and value objects
- [ ] Pattern matching for instanceof
- [ ] Switch expressions (not statements)
- [ ] Sealed classes for closed hierarchies
- [ ] Text blocks for multi-line strings
- [ ] Optional instead of null returns
- [ ] Stream API for collections
- [ ] var for local variables (when type is obvious)
```

### Testing

```markdown
## Test Coverage
- [ ] Unit tests for business logic
- [ ] Integration tests for repositories
- [ ] E2E tests for critical flows
- [ ] Test naming: whenX_shouldY or given_when_then
- [ ] AAA pattern (Arrange-Act-Assert)

## No-Mock Philosophy
- [ ] Only mock external services (APIs, message queues)
- [ ] Don't mock repositories (use real database)
- [ ] Don't mock domain entities
- [ ] Use test data builders/factories

## Test Quality
- [ ] Tests are independent (no shared state)
- [ ] Tests are deterministic (no random data)
- [ ] One assertion per test (ideally)
- [ ] Test both happy path and edge cases
```

### Buy Nature Backend Specific

```markdown
## DTO Conventions
- [ ] CreationRequest for POST endpoints
- [ ] UpdateRequest for PUT/PATCH endpoints
- [ ] RetrievalResponse for GET endpoints
- [ ] from() static factory method in responses

Example:
```java
public record ItemCreationRequest(
    @NotBlank String name,
    @NotNull @Positive BigDecimal price
) { }

public record ItemRetrievalResponse(
    UUID id,
    String name,
    BigDecimal price
) {
    public static ItemRetrievalResponse from(Item item) {
        return new ItemRetrievalResponse(
            item.getId(),
            item.getName(),
            item.getPrice()
        );
    }
}
```

## Repository Pattern
- [ ] Simple queries: JpaRepository methods
- [ ] Medium queries: @Query annotation
- [ ] Complex queries: Custom implementation (3-layer pattern)

Example:
```java
public interface OrderRepository extends JpaRepository<Order, UUID>, OrderRepositoryCustom {
    List<Order> findByCustomerId(UUID customerId);  // Simple

    @Query("SELECT o FROM Order o JOIN FETCH o.items WHERE o.status = :status")
    List<Order> findByStatusWithItems(@Param("status") OrderStatus status);  // Medium
}

public interface OrderRepositoryCustom {
    List<Order> findByComplexCriteria(OrderSearchCriteria criteria);  // Complex
}
```

## REST Controllers
- [ ] @RestController annotation
- [ ] Mapping uses resource names (plural): /api/orders, /api/items
- [ ] HTTP methods: POST (create), GET (read), PUT (full update), PATCH (partial), DELETE
- [ ] ResponseEntity with proper status codes
- [ ] @Valid for request validation
- [ ] Pagination for list endpoints

Example:
```java
@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;

    @PostMapping
    public ResponseEntity<OrderRetrievalResponse> createOrder(
        @Valid @RequestBody OrderCreationRequest request
    ) {
        Order order = orderService.createOrder(request);
        return ResponseEntity
            .status(HttpStatus.CREATED)
            .body(OrderRetrievalResponse.from(order));
    }

    @GetMapping("/{id}")
    public ResponseEntity<OrderRetrievalResponse> getOrder(@PathVariable UUID id) {
        return orderService.findById(id)
            .map(OrderRetrievalResponse::from)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
}
```
```

---

## Frontend Checklist (Angular/TypeScript)

### Architecture & Design

```markdown
## Component Design
- [ ] Standalone components (standalone: true)
- [ ] Smart/Container vs Dumb/Presentational separation
- [ ] OnPush change detection where applicable
- [ ] No business logic in components (move to services)
- [ ] Template-driven or Reactive forms (not mixed)

## State Management
- [ ] Signals for component state
- [ ] Signal stores for shared state
- [ ] Computed signals for derived state
- [ ] No manual subscriptions (use async pipe or toSignal)

## Services
- [ ] Injectable with providedIn: 'root'
- [ ] HTTP calls return Observables
- [ ] Error handling with catchError
- [ ] inject() function over constructor injection
```

### Code Quality

```markdown
## TypeScript
- [ ] Strict mode enabled
- [ ] No any types (use unknown or proper types)
- [ ] Interfaces for data structures
- [ ] Type guards for narrowing
- [ ] Optional chaining (?.) and nullish coalescing (??)

## Angular Patterns
- [ ] Control flow: @if, @for, @switch (not *ngIf, *ngFor)
- [ ] Signals for reactivity
- [ ] OnPush change detection
- [ ] trackBy for @for loops
- [ ] Lazy loading for routes

## Clean Code
- [ ] Functions are small (< 20 lines)
- [ ] Single responsibility per component/service
- [ ] Meaningful names (no abbreviations)
- [ ] No console.log in production code
```

### Testing

```markdown
## Component Tests
- [ ] Test user interactions, not implementation
- [ ] Use Angular Testing Library (preferred) or TestBed
- [ ] Mock services, not HTTP calls
- [ ] Test accessibility (aria labels, keyboard navigation)

## Service Tests
- [ ] Mock HttpClient with HttpClientTestingModule
- [ ] Test error handling
- [ ] Test data transformations

Example:
```typescript
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

  it('should fetch products', () => {
    const mockProducts = [{ id: '1', name: 'Test' }];

    service.getProducts().subscribe(products => {
      expect(products).toEqual(mockProducts);
    });

    const req = httpMock.expectOne('/api/products');
    expect(req.request.method).toBe('GET');
    req.flush(mockProducts);
  });
});
```
```

### Buy Nature Frontend Specific

```markdown
## Folder Structure
- [ ] Feature modules: src/app/features/<feature-name>
- [ ] Shared components: src/app/shared/components
- [ ] Core services: src/app/core/services
- [ ] Models: src/app/core/models

## Naming Conventions
- [ ] Components: product-list.component.ts
- [ ] Services: product.service.ts
- [ ] Pipes: currency.pipe.ts
- [ ] Guards: auth.guard.ts
- [ ] Interceptors: auth.interceptor.ts

## Signal Usage
```typescript
// ✅ CORRECT
@Component({...})
export class ProductListComponent {
  private productService = inject(ProductService);

  products = signal<Product[]>([]);
  isLoading = signal<boolean>(false);
  error = signal<string | null>(null);

  totalPrice = computed(() =>
    this.products().reduce((sum, p) => sum + p.price, 0)
  );

  ngOnInit() {
    this.loadProducts();
  }

  loadProducts() {
    this.isLoading.set(true);

    this.productService.getProducts().subscribe({
      next: (products) => {
        this.products.set(products);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.error.set(err.message);
        this.isLoading.set(false);
      }
    });
  }
}
```

## Template Syntax
```html
<!-- ✅ CORRECT: Control flow syntax -->
@if (isLoading()) {
  <app-loader />
}

@if (error(); as errorMessage) {
  <app-error [message]="errorMessage" />
}

@if (products().length === 0) {
  <app-empty-state message="No products found" />
} @else {
  <div class="product-grid">
    @for (product of products(); track product.id) {
      <app-product-card [product]="product" />
    }
  </div>
}

<!-- Total: {{ totalPrice() | currency }} -->
```
```

---

## Security Checklist

```markdown
## Authentication & Authorization
- [ ] Passwords hashed (BCrypt, Argon2)
- [ ] JWT tokens validated
- [ ] CSRF protection enabled
- [ ] CORS configured correctly
- [ ] Sensitive endpoints protected (@PreAuthorize)

## Input Validation
- [ ] All user input validated
- [ ] SQL injection prevention (prepared statements)
- [ ] XSS prevention (sanitize HTML)
- [ ] Path traversal prevention
- [ ] File upload restrictions (type, size)

## Data Protection
- [ ] No secrets in code (use environment variables)
- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced
- [ ] Secure headers (CSP, X-Frame-Options)
- [ ] Rate limiting on APIs
```

---

## Performance Checklist

```markdown
## Backend Performance
- [ ] N+1 queries avoided (eager loading)
- [ ] Pagination for large datasets
- [ ] Caching where appropriate (@Cacheable)
- [ ] Database indexes on frequently queried columns
- [ ] Connection pooling configured

## Frontend Performance
- [ ] Lazy loading for routes
- [ ] OnPush change detection
- [ ] TrackBy for lists
- [ ] Image optimization (WebP, lazy loading)
- [ ] Bundle size reasonable (< 500KB initial)
```

---

## Documentation Checklist

```markdown
## Code Documentation
- [ ] Public APIs have Javadoc/JSDoc
- [ ] Complex algorithms explained
- [ ] WHY comments for non-obvious decisions
- [ ] No commented-out code (use git)

## API Documentation
- [ ] OpenAPI/Swagger spec updated
- [ ] Example requests/responses
- [ ] Error codes documented
- [ ] Authentication requirements clear

## README
- [ ] Setup instructions
- [ ] Running tests
- [ ] Environment variables
- [ ] Deployment process
```

---

## Review Etiquette

### As a Reviewer

**DO:**
- Focus on code quality, not personal preferences
- Ask questions ("Why did you choose...?")
- Suggest alternatives ("Consider using...")
- Praise good solutions
- Be specific ("Line 42: This could cause NPE")

**DON'T:**
- Use harsh language
- Nitpick style (automate with linters)
- Block on personal preferences
- Review your own code
- Approve without actually reading

### As an Author

**DO:**
- Provide context in PR description
- Self-review before requesting review
- Respond to all comments
- Ask for clarification if unclear
- Thank reviewers

**DON'T:**
- Take feedback personally
- Argue over minor points
- Ignore feedback
- Merge without approval
- Force push after review (unless requested)

---

## PR Description Template

```markdown
## Summary
Brief description of changes

## Changes Made
- Added checkout service
- Implemented payment integration
- Created E2E tests for checkout flow

## Related Issues
Closes #123
Related to #456

## Test Plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed

## Screenshots (if UI changes)
[Attach screenshots]

## Checklist
- [ ] Code builds without errors
- [ ] All tests pass
- [ ] No security vulnerabilities
- [ ] Documentation updated
- [ ] Ready for review

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

---

## Quick Decision Matrix

| Severity | Action | Example |
|----------|--------|---------|
| 🔴 BLOCKING | Request changes | Security flaw, tests failing, breaks build |
| 🟡 WARNING | Comment, but approve if minor | Missing tests, code smell, performance concern |
| 🟢 BEST PRACTICE | Suggestion for future | Refactoring opportunity, documentation improvement |

---

## Final Checklist

Before approving PR:

- [ ] Code solves the stated problem
- [ ] No security vulnerabilities
- [ ] Tests added and passing
- [ ] Follows project conventions
- [ ] No obvious bugs
- [ ] Readable and maintainable
- [ ] Documentation updated (if needed)
- [ ] Ready to merge
