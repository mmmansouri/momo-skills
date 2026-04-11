# Testing Guidelines

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Test Pyramid

```
        /\
       /E2E\        ← Few (5-10%), slow, expensive
      /------\        End-to-end user flows
     /Integration\  ← Some (20-30%), medium speed
    /------------\    Component interactions, database
   / Unit Tests   \ ← Many (60-75%), fast, cheap
  /________________\  Business logic, pure functions
```

**Guideline:** More unit tests, fewer integration tests, even fewer E2E tests.

---

## Unit Tests

### Purpose
- Test single units in isolation
- Fast execution (milliseconds)
- High coverage of business logic
- No external dependencies

### AAA Pattern (Arrange-Act-Assert)

```java
@Test
void whenCalculateTotal_withMultipleItems_shouldReturnCorrectSum() {
    // Arrange (Given)
    Item item1 = new Item("Product 1", Money.of(10.00));
    Item item2 = new Item("Product 2", Money.of(15.50));
    Order order = Order.builder()
        .addItem(item1)
        .addItem(item2)
        .build();

    // Act (When)
    Money total = order.calculateTotal();

    // Assert (Then)
    assertThat(total).isEqualTo(Money.of(25.50));
}
```

### Test Naming

```java
// ✅ CORRECT: when_condition_should_expectedResult
@Test
void whenOrderIsConfirmed_shouldSendEmailNotification() { }

@Test
void whenQuantityIsNegative_shouldThrowInvalidQuantityException() { }

@Test
void whenCustomerIsPremium_shouldApplyDiscount() { }

// Alternative: given_when_then
@Test
void givenPendingOrder_whenConfirm_thenStatusIsConfirmed() { }

// ❌ WRONG: Unclear names
@Test
void testOrder() { }

@Test
void test1() { }

@Test
void checkDiscount() { }
```

### Buy Nature Unit Test Example

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private OrderRepository orderRepository;

    @Mock
    private NotificationService notificationService;

    @Mock
    private InventoryService inventoryService;

    @InjectMocks
    private OrderService orderService;

    @Test
    void whenConfirmOrder_shouldUpdateStatusAndNotifyCustomer() {
        // Arrange
        UUID orderId = UUID.randomUUID();
        Order order = TestData.pendingOrder(orderId);

        when(orderRepository.findById(orderId)).thenReturn(Optional.of(order));
        when(orderRepository.save(any(Order.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        Order result = orderService.confirmOrder(orderId);

        // Assert
        assertThat(result.getStatus()).isEqualTo(OrderStatus.CONFIRMED);
        verify(notificationService).sendOrderConfirmation(order);
        verify(orderRepository).save(order);
    }

    @Test
    void whenConfirmOrder_withInvalidStatus_shouldThrowException() {
        // Arrange
        UUID orderId = UUID.randomUUID();
        Order order = TestData.confirmedOrder(orderId);  // Already confirmed

        when(orderRepository.findById(orderId)).thenReturn(Optional.of(order));

        // Act & Assert
        assertThatThrownBy(() -> orderService.confirmOrder(orderId))
            .isInstanceOf(InvalidOrderStateException.class)
            .hasMessageContaining("Only pending orders can be confirmed");
    }
}
```

### Test Data Factories

```java
// ✅ BEST PRACTICE: Test data builders
public class TestData {

    public static Customer customer() {
        return Customer.builder()
            .id(UUID.randomUUID())
            .email("test@example.com")
            .firstName("John")
            .lastName("Doe")
            .build();
    }

    public static Order pendingOrder(UUID orderId) {
        return Order.builder()
            .id(orderId)
            .customer(customer())
            .status(OrderStatus.PENDING)
            .addItem(orderItem())
            .build();
    }

    public static OrderItem orderItem() {
        return OrderItem.builder()
            .product(product())
            .quantity(2)
            .price(Money.of(10.00))
            .build();
    }

    public static Product product() {
        return Product.builder()
            .id(UUID.randomUUID())
            .name("Test Product")
            .price(Money.of(10.00))
            .stock(100)
            .build();
    }
}

// Usage
Order order = TestData.pendingOrder(UUID.randomUUID());
```

---

## Integration Tests

### Purpose
- Test component interactions
- Real dependencies (database, message queue)
- Focus on boundaries and contracts
- Slower than unit tests, faster than E2E

### Buy Nature Integration Test Example

```java
@SpringBootTest
@Transactional
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class OrderRepositoryIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private CustomerRepository customerRepository;

    @Test
    void whenFindByCustomerId_shouldReturnCustomerOrders() {
        // Arrange
        Customer customer = customerRepository.save(TestData.customer());

        Order order1 = TestData.pendingOrder(customer);
        Order order2 = TestData.confirmedOrder(customer);

        orderRepository.save(order1);
        orderRepository.save(order2);

        // Act
        List<Order> orders = orderRepository.findByCustomerId(customer.getId());

        // Assert
        assertThat(orders)
            .hasSize(2)
            .extracting(Order::getStatus)
            .containsExactlyInAnyOrder(OrderStatus.PENDING, OrderStatus.CONFIRMED);
    }

    @Test
    void whenSaveOrder_shouldPersistWithItems() {
        // Arrange
        Customer customer = customerRepository.save(TestData.customer());
        Order order = TestData.orderWithItems(customer);

        // Act
        Order saved = orderRepository.save(order);
        entityManager.flush();
        entityManager.clear();  // Clear persistence context

        // Assert
        Order retrieved = orderRepository.findById(saved.getId()).orElseThrow();
        assertThat(retrieved.getItems()).hasSize(2);
        assertThat(retrieved.getCustomer().getId()).isEqualTo(customer.getId());
    }
}
```

### No-Mock Philosophy

```java
// ❌ WRONG: Mocking repositories in integration tests
@SpringBootTest
class OrderServiceIntegrationTest {
    @MockBean
    private OrderRepository orderRepository;  // DON'T mock in integration test

    @Autowired
    private OrderService orderService;

    @Test
    void test() {
        // This is not an integration test, it's a unit test
        when(orderRepository.findById(any())).thenReturn(Optional.of(order));
    }
}

// ✅ CORRECT: Use real database
@SpringBootTest
@Testcontainers
class OrderServiceIntegrationTest {
    @Autowired
    private OrderRepository orderRepository;  // Real repository

    @Autowired
    private OrderService orderService;

    @Test
    void test() {
        // Test actual database interaction
        Order saved = orderRepository.save(order);
        Order retrieved = orderService.findById(saved.getId());
    }
}
```

**Only mock external services:**
- External APIs (payment gateways, email services)
- Message queues
- Third-party libraries

**Don't mock:**
- Your own repositories
- Your own services (in integration tests)
- Domain entities
- JPA entities

---

## E2E Tests (Playwright)

### Purpose
- Test complete user flows
- Real browser, real server
- Catch integration issues
- Most realistic, but slowest

### Buy Nature E2E Example

```typescript
// tests/checkout.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Checkout Flow', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to product page
    await page.goto('/products');
  });

  test('should complete checkout successfully', async ({ page }) => {
    // Arrange: Add product to cart
    await page.getByTestId('product-card-1').click();
    await page.getByRole('button', { name: 'Add to Cart' }).click();

    // Go to cart
    await page.getByTestId('cart-icon').click();
    await expect(page.getByTestId('cart-item')).toBeVisible();

    // Proceed to checkout
    await page.getByRole('button', { name: 'Proceed to Checkout' }).click();

    // Fill shipping information
    await page.getByLabel('Full Name').fill('John Doe');
    await page.getByLabel('Email').fill('john@example.com');
    await page.getByLabel('Address').fill('123 Main St');
    await page.getByLabel('City').fill('Springfield');
    await page.getByLabel('Zip Code').fill('12345');

    // Fill payment information (test card)
    await page.getByLabel('Card Number').fill('4242424242424242');
    await page.getByLabel('Expiry').fill('12/25');
    await page.getByLabel('CVV').fill('123');

    // Submit order
    await page.getByRole('button', { name: 'Place Order' }).click();

    // Assert: Order confirmation
    await expect(page.getByTestId('order-confirmation')).toBeVisible();
    await expect(page.getByText(/Order #/)).toBeVisible();
    await expect(page.getByText(/Thank you for your order/)).toBeVisible();
  });

  test('should show error for invalid card', async ({ page }) => {
    // Arrange: Add product and go to checkout
    await page.getByTestId('product-card-1').click();
    await page.getByRole('button', { name: 'Add to Cart' }).click();
    await page.getByTestId('cart-icon').click();
    await page.getByRole('button', { name: 'Proceed to Checkout' }).click();

    // Fill shipping
    await page.getByLabel('Full Name').fill('John Doe');
    await page.getByLabel('Email').fill('john@example.com');

    // Fill invalid card
    await page.getByLabel('Card Number').fill('0000000000000000');
    await page.getByLabel('Expiry').fill('12/25');
    await page.getByLabel('CVV').fill('123');

    // Submit
    await page.getByRole('button', { name: 'Place Order' }).click();

    // Assert: Error message
    await expect(page.getByTestId('error-message')).toContainText('Invalid card number');
  });

});
```

### Page Object Pattern

```typescript
// page-objects/checkout.page.ts
export class CheckoutPage {
  constructor(private page: Page) {}

  async fillShippingInfo(info: ShippingInfo) {
    await this.page.getByLabel('Full Name').fill(info.name);
    await this.page.getByLabel('Email').fill(info.email);
    await this.page.getByLabel('Address').fill(info.address);
    await this.page.getByLabel('City').fill(info.city);
    await this.page.getByLabel('Zip Code').fill(info.zipCode);
  }

  async fillPaymentInfo(card: CardInfo) {
    await this.page.getByLabel('Card Number').fill(card.number);
    await this.page.getByLabel('Expiry').fill(card.expiry);
    await this.page.getByLabel('CVV').fill(card.cvv);
  }

  async submitOrder() {
    await this.page.getByRole('button', { name: 'Place Order' }).click();
  }

  async expectOrderConfirmation() {
    await expect(this.page.getByTestId('order-confirmation')).toBeVisible();
  }
}

// Usage
test('checkout flow', async ({ page }) => {
  const checkout = new CheckoutPage(page);

  await checkout.fillShippingInfo({
    name: 'John Doe',
    email: 'john@example.com',
    address: '123 Main St',
    city: 'Springfield',
    zipCode: '12345'
  });

  await checkout.fillPaymentInfo({
    number: '4242424242424242',
    expiry: '12/25',
    cvv: '123'
  });

  await checkout.submitOrder();
  await checkout.expectOrderConfirmation();
});
```

---

## TypeScript/Angular Testing

### Component Testing

```typescript
// product-list.component.spec.ts
describe('ProductListComponent', () => {
  let component: ProductListComponent;
  let fixture: ComponentFixture<ProductListComponent>;
  let productService: jasmine.SpyObj<ProductService>;

  beforeEach(() => {
    const productServiceSpy = jasmine.createSpyObj('ProductService', ['getProducts']);

    TestBed.configureTestingModule({
      imports: [ProductListComponent],
      providers: [
        { provide: ProductService, useValue: productServiceSpy }
      ]
    });

    fixture = TestBed.createComponent(ProductListComponent);
    component = fixture.componentInstance;
    productService = TestBed.inject(ProductService) as jasmine.SpyObj<ProductService>;
  });

  it('should display products', () => {
    // Arrange
    const mockProducts = [
      { id: '1', name: 'Product 1', price: 10 },
      { id: '2', name: 'Product 2', price: 20 }
    ];

    productService.getProducts.and.returnValue(of(mockProducts));

    // Act
    fixture.detectChanges();

    // Assert
    const productCards = fixture.nativeElement.querySelectorAll('.product-card');
    expect(productCards.length).toBe(2);
    expect(productCards[0].textContent).toContain('Product 1');
  });

  it('should show loading state', () => {
    // Arrange
    productService.getProducts.and.returnValue(NEVER);  // Never completes

    // Act
    component.ngOnInit();
    fixture.detectChanges();

    // Assert
    expect(component.isLoading()).toBe(true);
    const loader = fixture.nativeElement.querySelector('app-loader');
    expect(loader).toBeTruthy();
  });

  it('should handle error', () => {
    // Arrange
    productService.getProducts.and.returnValue(
      throwError(() => new Error('Network error'))
    );

    // Act
    component.ngOnInit();
    fixture.detectChanges();

    // Assert
    expect(component.error()).toBe('Network error');
    const errorMessage = fixture.nativeElement.querySelector('.error-message');
    expect(errorMessage.textContent).toContain('Network error');
  });
});
```

### Service Testing

```typescript
// product.service.spec.ts
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
    httpMock.verify();  // Ensure no outstanding requests
  });

  it('should fetch products', (done) => {
    // Arrange
    const mockProducts: Product[] = [
      { id: '1', name: 'Product 1', price: 10 },
      { id: '2', name: 'Product 2', price: 20 }
    ];

    // Act
    service.getProducts().subscribe({
      next: (products) => {
        // Assert
        expect(products).toEqual(mockProducts);
        expect(products.length).toBe(2);
        done();
      }
    });

    // Assert HTTP call
    const req = httpMock.expectOne('/api/products');
    expect(req.request.method).toBe('GET');
    req.flush(mockProducts);
  });

  it('should handle error', (done) => {
    // Act
    service.getProducts().subscribe({
      next: () => fail('should have failed'),
      error: (error) => {
        // Assert
        expect(error.status).toBe(500);
        done();
      }
    });

    // Simulate error
    const req = httpMock.expectOne('/api/products');
    req.flush('Server error', { status: 500, statusText: 'Internal Server Error' });
  });
});
```

---

## Test Isolation

### 🔴 BLOCKING - Tests Must Be Independent

```java
// ❌ WRONG: Shared state between tests
class OrderServiceTest {
    private static Order order;  // WRONG: shared state

    @BeforeAll
    static void setup() {
        order = TestData.pendingOrder();
    }

    @Test
    void test1() {
        order.confirm();  // Modifies shared state
    }

    @Test
    void test2() {
        // This test fails if test1 runs first
        assertThat(order.getStatus()).isEqualTo(OrderStatus.PENDING);
    }
}

// ✅ CORRECT: Each test creates its own data
class OrderServiceTest {

    @Test
    void test1() {
        Order order = TestData.pendingOrder();  // Fresh instance
        order.confirm();
        assertThat(order.getStatus()).isEqualTo(OrderStatus.CONFIRMED);
    }

    @Test
    void test2() {
        Order order = TestData.pendingOrder();  // Fresh instance
        assertThat(order.getStatus()).isEqualTo(OrderStatus.PENDING);
    }
}
```

---

## Coverage Goals

| Type | Coverage Target | Focus |
|------|----------------|-------|
| Unit | 80-90% | Business logic, algorithms, utilities |
| Integration | 60-70% | Repositories, service interactions, database |
| E2E | 20-30% | Critical user flows (checkout, login, search) |

**100% coverage is not the goal.** Focus on critical paths and complex logic.

---

## Testing Checklist

Before committing:

- [ ] All new code has tests
- [ ] All tests pass locally
- [ ] Test names are descriptive
- [ ] Tests use AAA pattern
- [ ] No test interdependencies
- [ ] Tests are fast (unit tests < 100ms)
- [ ] Edge cases tested (null, empty, boundary values)
- [ ] Error cases tested
- [ ] No console.log/System.out.println in tests

---

## Buy Nature Specific

### Test File Naming

```
Java:
src/test/java/com/buynature/order/OrderServiceTest.java
src/test/java/com/buynature/order/OrderRepositoryIntegrationTest.java

TypeScript:
src/app/features/product/product-list.component.spec.ts
src/app/core/services/product.service.spec.ts
```

### Test Data Location

```
Java:
src/test/java/com/buynature/testutil/TestData.java

TypeScript:
src/app/testing/test-data.ts
```

---

## Resources

- [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)
- [Mockito Documentation](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html)
- [AssertJ Documentation](https://assertj.github.io/doc/)
- [Playwright Documentation](https://playwright.dev/)
- [Angular Testing Guide](https://angular.io/guide/testing)
