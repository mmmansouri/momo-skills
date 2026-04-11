# Testing in Modern Java

> JUnit 5, Mockito, test patterns, and TDD workflow for Java 8-25.

---

## Table of Contents
1. [JUnit 5 Essentials](#junit-5-essentials)
2. [Mockito Best Practices](#mockito-best-practices)
3. [Test Patterns](#test-patterns)
4. [TDD Workflow](#tdd-workflow)
5. [Decision Tree: What Type of Test?](#decision-tree-what-type-of-test)
6. [Parameterized Tests](#parameterized-tests)
7. [Test Data Builders](#test-data-builders)
8. [Code Review Checklist](#code-review-checklist)

---

## JUnit 5 Essentials

### Core Annotations

| Annotation | Purpose |
|------------|---------|
| `@Test` | Mark method as test |
| `@BeforeEach` | Run before each test (setup) |
| `@AfterEach` | Run after each test (cleanup) |
| `@BeforeAll` | Run once before all tests (static) |
| `@AfterAll` | Run once after all tests (static) |
| `@Nested` | Group related tests in inner class |
| `@DisplayName` | Custom test name in reports |
| `@Disabled` | Skip test temporarily |
| `@Tag` | Categorize tests for filtering |

### Basic Test Structure

```java
import org.junit.jupiter.api.*;
import static org.assertj.core.api.Assertions.*;

class UserServiceTest {

    private UserService userService;

    @BeforeEach
    void setUp() {
        userService = new UserService(new InMemoryUserRepository());
    }

    @Test
    @DisplayName("Should return user when found by ID")
    void findById_whenUserExists_returnsUser() {
        // Arrange
        var user = new User(1L, "john@example.com");
        userService.save(user);

        // Act
        var result = userService.findById(1L);

        // Assert
        assertThat(result).isPresent();
        assertThat(result.get().email()).isEqualTo("john@example.com");
    }

    @Test
    void findById_whenUserNotFound_returnsEmpty() {
        var result = userService.findById(999L);
        assertThat(result).isEmpty();
    }
}
```

### Nested Tests (Grouping Related Tests)

```java
@DisplayName("UserService")
class UserServiceTest {

    @Nested
    @DisplayName("when creating a user")
    class CreateUser {

        @Test
        void shouldSaveValidUser() { /* ... */ }

        @Test
        void shouldRejectDuplicateEmail() { /* ... */ }

        @Test
        void shouldRejectInvalidEmail() { /* ... */ }
    }

    @Nested
    @DisplayName("when deleting a user")
    class DeleteUser {

        @Test
        void shouldDeleteExistingUser() { /* ... */ }

        @Test
        void shouldThrowWhenUserNotFound() { /* ... */ }
    }
}
```

### Assertions (AssertJ Preferred)

```java
// AssertJ - fluent, readable
assertThat(user.name()).isEqualTo("John");
assertThat(users).hasSize(3).extracting(User::email).contains("a@test.com");
assertThat(price).isCloseTo(99.99, within(0.01));
assertThat(result).isEmpty();  // For Optional

// Exception assertions
assertThatThrownBy(() -> service.delete(null))
    .isInstanceOf(IllegalArgumentException.class)
    .hasMessageContaining("ID cannot be null");

// assertAll - run all, report all failures
assertAll(
    () -> assertThat(user.name()).isEqualTo("John"),
    () -> assertThat(user.email()).contains("@"),
    () -> assertThat(user.createdAt()).isBeforeOrEqualTo(Instant.now())
);
```

### Lifecycle

```
@BeforeAll (once)
    └── @BeforeEach
        └── @Test (test1)
    └── @AfterEach

    └── @BeforeEach
        └── @Test (test2)
    └── @AfterEach
@AfterAll (once)
```

---

## Mockito Best Practices

### When to Mock

| Scenario | Mock? | Why |
|----------|-------|-----|
| External service (HTTP, DB) | ✅ Yes | Isolate, control responses |
| Internal class (same module) | ❌ No | Test real behavior |
| Time-dependent code | ✅ Yes | Use `Clock` mock |
| Random/UUID generation | ✅ Yes | Reproducible tests |
| File system | ✅ Yes | Use in-memory or temp files |

### 🔴 BLOCKING: Don't Mock Internal Classes

```java
// 🔴 WRONG - mocking internal class hides bugs
@Mock private PriceCalculator calculator;  // Internal class!

@Test
void shouldApplyDiscount() {
    when(calculator.calculate(any())).thenReturn(90.0);  // Faking internal logic
    // If calculator has a bug, this test won't catch it!
}

// ✅ CORRECT - test real implementation
@Test
void shouldApplyDiscount() {
    var calculator = new PriceCalculator();  // Real implementation
    var service = new OrderService(calculator);
    var order = new Order(item, discount);

    assertThat(service.calculateTotal(order)).isEqualTo(90.0);
}
```

### Core Mockito Patterns

```java
@ExtendWith(MockitoExtension.class)
class PaymentServiceTest {

    @Mock
    private PaymentGateway gateway;  // External service - OK to mock

    @Mock
    private EmailService emailService;  // External service - OK to mock

    @InjectMocks
    private PaymentService paymentService;

    @Test
    void shouldProcessPaymentAndSendEmail() {
        // Arrange - stub external service
        when(gateway.charge(any(PaymentRequest.class)))
            .thenReturn(new PaymentResult(true, "txn-123"));

        // Act
        var result = paymentService.processPayment(100.0, "card-token");

        // Assert
        assertThat(result.isSuccess()).isTrue();

        // Verify interactions
        verify(gateway).charge(any());
        verify(emailService).sendReceipt(eq("txn-123"), anyDouble());
        verifyNoMoreInteractions(gateway);
    }

    @Test
    void shouldNotSendEmailOnFailedPayment() {
        when(gateway.charge(any())).thenReturn(new PaymentResult(false, null));

        paymentService.processPayment(100.0, "invalid-card");

        verify(emailService, never()).sendReceipt(any(), anyDouble());
    }
}
```

### ArgumentCaptor (Capture & Inspect Arguments)

```java
@Test
void shouldCreateOrderWithCorrectDetails() {
    ArgumentCaptor<Order> orderCaptor = ArgumentCaptor.forClass(Order.class);

    service.placeOrder(cart);

    verify(orderRepository).save(orderCaptor.capture());

    Order savedOrder = orderCaptor.getValue();
    assertThat(savedOrder.items()).hasSize(3);
    assertThat(savedOrder.total()).isEqualTo(299.99);
}
```

### Spy (Partial Mock)

```java
// Use sparingly - usually indicates design issue
@Spy
private NotificationService notificationService = new NotificationService();

@Test
void shouldLogButNotActuallySendInTest() {
    doNothing().when(notificationService).sendSms(any());  // Disable real SMS

    service.processOrder(order);

    verify(notificationService).sendSms(contains("Order confirmed"));
}
```

---

## Test Patterns

### AAA Pattern (Arrange-Act-Assert)

```java
@Test
void shouldApplyDiscountForLoyalCustomer() {
    // Arrange - set up test data and dependencies
    var customer = new Customer("loyal-123", CustomerTier.GOLD);
    var cart = new Cart(List.of(new Item("SKU-1", 100.0)));
    var service = new PricingService();

    // Act - execute the behavior under test
    var total = service.calculateTotal(cart, customer);

    // Assert - verify the outcome
    assertThat(total).isEqualTo(85.0);  // 15% gold discount
}
```

### Given-When-Then Naming

```java
// Format: methodName_givenCondition_expectedBehavior
void calculateTotal_givenGoldCustomer_appliesFifteenPercentDiscount()
void findUser_givenNonExistentId_returnsEmpty()
void createOrder_givenEmptyCart_throwsException()

// Or: when_condition_should_behavior
void whenCartEmpty_shouldThrowException()
void whenUserNotFound_shouldReturn404()
```

### Test Isolation

```java
// 🔴 WRONG - shared mutable state between tests
class OrderServiceTest {
    private static List<Order> orders = new ArrayList<>();  // Shared!

    @Test void test1() { orders.add(order1); /* ... */ }
    @Test void test2() { /* orders still contains order1! */ }
}

// ✅ CORRECT - fresh state per test
class OrderServiceTest {
    private List<Order> orders;

    @BeforeEach
    void setUp() {
        orders = new ArrayList<>();  // Fresh for each test
    }
}
```

### Testing Exceptions

```java
// AssertJ (preferred)
@Test
void shouldThrowWhenIdNull() {
    assertThatThrownBy(() -> service.findById(null))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessage("ID cannot be null");
}

// JUnit 5
@Test
void shouldThrowWhenIdNull() {
    var exception = assertThrows(IllegalArgumentException.class,
        () -> service.findById(null));

    assertEquals("ID cannot be null", exception.getMessage());
}

// Asserting no exception
@Test
void shouldNotThrowForValidInput() {
    assertThatCode(() -> service.process(validInput))
        .doesNotThrowAnyException();
}
```

---

## TDD Workflow

### Red → Green → Refactor

```
1. RED    - Write a failing test (defines expected behavior)
2. GREEN  - Write minimal code to pass the test
3. REFACTOR - Improve code while keeping tests green
```

### TDD Example

```java
// Step 1: RED - Write failing test first
@Test
void shouldCalculateTaxForOrder() {
    var calculator = new TaxCalculator();
    var order = new Order(100.0);

    var tax = calculator.calculate(order);

    assertThat(tax).isEqualTo(10.0);  // 10% tax
}
// Test fails: TaxCalculator doesn't exist

// Step 2: GREEN - Minimal implementation
public class TaxCalculator {
    public double calculate(Order order) {
        return order.total() * 0.10;  // Simplest thing that works
    }
}
// Test passes

// Step 3: REFACTOR - Improve (e.g., extract constant, handle edge cases)
public class TaxCalculator {
    private static final double TAX_RATE = 0.10;

    public double calculate(Order order) {
        Objects.requireNonNull(order, "Order cannot be null");
        return order.total() * TAX_RATE;
    }
}
// Tests still pass - refactor successful
```

### TDD Benefits

- **Design emerges** from requirements (test-first = spec-first)
- **Fast feedback** - know immediately if change breaks something
- **Documentation** - tests show how code should be used
- **Confidence** - refactor without fear

---

## Decision Tree: What Type of Test?

```
What are you testing?
│
├── Pure logic (no I/O, no framework)?
│   └── ✅ Unit test (plain JUnit + AssertJ)
│       - Fast, no Spring context
│       - Example: calculators, validators, converters
│
├── Database/JPA operations?
│   └── ✅ @DataJpaTest (slice test)
│       - Loads only JPA components
│       - Uses H2/TestContainers
│       - Example: repository tests
│
├── REST controller (HTTP layer)?
│   └── ✅ @WebMvcTest (slice test)
│       - Loads only web layer
│       - MockMvc for HTTP simulation
│       - Example: endpoint tests
│
├── Full request cycle (API → DB → response)?
│   └── ✅ @SpringBootTest (integration/E2E)
│       - Full application context
│       - Real HTTP with TestRestTemplate
│       - Example: feature tests
│
├── External service (HTTP client)?
│   └── ✅ WireMock + unit test
│       - Stub external API responses
│       - Test error handling, timeouts
│
└── Multiple services together?
    └── ✅ TestContainers + @SpringBootTest
        - Real DB, real dependencies
        - Docker-based isolation
```

### Test Pyramid

```
         /\
        /  \     E2E Tests (few, slow, expensive)
       /----\    - Full system, real browser/API
      /      \
     /--------\  Integration Tests (some)
    /          \ - @SpringBootTest, @DataJpaTest
   /------------\
  /              \ Unit Tests (many, fast, cheap)
 /----------------\ - Plain JUnit, no framework
```

---

## Parameterized Tests

### @ValueSource (Simple Values)

```java
@ParameterizedTest
@ValueSource(strings = {"", "  ", "\t", "\n"})
void shouldRejectBlankUsernames(String username) {
    assertThatThrownBy(() -> new User(username, "email@test.com"))
        .isInstanceOf(IllegalArgumentException.class);
}

@ParameterizedTest
@ValueSource(ints = {-1, 0, -100})
void shouldRejectNegativeQuantity(int quantity) {
    assertThat(validator.isValidQuantity(quantity)).isFalse();
}
```

### @CsvSource (Multiple Parameters)

```java
@ParameterizedTest
@CsvSource({
    "100, 10, 90",      // price, discount%, expected
    "200, 25, 150",
    "50, 0, 50",
    "100, 100, 0"
})
void shouldCalculateDiscountedPrice(double price, int discountPercent, double expected) {
    var result = calculator.applyDiscount(price, discountPercent);
    assertThat(result).isEqualTo(expected);
}
```

### @MethodSource (Complex Objects)

```java
@ParameterizedTest
@MethodSource("provideInvalidEmails")
void shouldRejectInvalidEmails(String email, String expectedError) {
    var result = validator.validate(email);
    assertThat(result.errors()).contains(expectedError);
}

static Stream<Arguments> provideInvalidEmails() {
    return Stream.of(
        Arguments.of("", "Email is required"),
        Arguments.of("invalid", "Invalid email format"),
        Arguments.of("no@domain", "Invalid domain"),
        Arguments.of("@nodomain.com", "Missing local part")
    );
}
```

### @EnumSource

```java
@ParameterizedTest
@EnumSource(value = OrderStatus.class, names = {"PENDING", "PROCESSING"})
void shouldAllowCancellationForPendingOrders(OrderStatus status) {
    var order = new Order(status);
    assertThat(order.canCancel()).isTrue();
}

@ParameterizedTest
@EnumSource(value = OrderStatus.class, mode = EXCLUDE, names = {"CANCELLED"})
void shouldGenerateInvoiceForNonCancelledOrders(OrderStatus status) {
    // ...
}
```

---

## Test Data Builders

### Builder Pattern for Test Data

```java
public class TestUserBuilder {
    private Long id = 1L;
    private String email = "default@test.com";
    private String name = "Test User";
    private UserRole role = UserRole.CUSTOMER;
    private boolean active = true;

    public static TestUserBuilder aUser() {
        return new TestUserBuilder();
    }

    public TestUserBuilder withId(Long id) {
        this.id = id;
        return this;
    }

    public TestUserBuilder withEmail(String email) {
        this.email = email;
        return this;
    }

    public TestUserBuilder withRole(UserRole role) {
        this.role = role;
        return this;
    }

    public TestUserBuilder inactive() {
        this.active = false;
        return this;
    }

    public TestUserBuilder admin() {
        this.role = UserRole.ADMIN;
        return this;
    }

    public User build() {
        return new User(id, email, name, role, active);
    }
}

// Usage in tests
@Test
void shouldAllowAdminAccess() {
    var admin = aUser().admin().withEmail("admin@company.com").build();
    assertThat(accessService.canAccessAdmin(admin)).isTrue();
}

@Test
void shouldDenyInactiveUserLogin() {
    var user = aUser().inactive().build();
    assertThat(authService.canLogin(user)).isFalse();
}
```

### Factory Methods (Simpler Alternative)

```java
public class TestData {

    public static User validUser() {
        return new User(1L, "user@test.com", "Test User", UserRole.CUSTOMER, true);
    }

    public static User adminUser() {
        return new User(2L, "admin@test.com", "Admin", UserRole.ADMIN, true);
    }

    public static Order pendingOrder(User user) {
        return new Order(1L, user, OrderStatus.PENDING, List.of(defaultItem()));
    }

    public static Item defaultItem() {
        return new Item("SKU-001", "Test Product", 99.99);
    }
}

// Usage
@Test
void shouldProcessOrder() {
    var user = TestData.validUser();
    var order = TestData.pendingOrder(user);
    // ...
}
```

---

## Code Review Checklist

### 🔴 BLOCKING

- [ ] **No shared mutable state between tests** → Use `@BeforeEach`
- [ ] **Don't mock internal classes** → Only mock external services
- [ ] **No `Thread.sleep()` in tests** → Use `Awaitility` for async
- [ ] **Tests pass in isolation** → Run single test, should pass

### 🟡 WARNING

- [ ] **Test names describe behavior** → `whenX_shouldY`, not `test1`
- [ ] **No test interdependencies** → Tests run in any order
- [ ] **Assertions present** → Every test asserts something
- [ ] **No ignored tests without reason** → `@Disabled("reason")`

### 🟢 BEST PRACTICE

- [ ] **Tests follow AAA pattern** → Clear Arrange-Act-Assert blocks
- [ ] **One logical assertion per test** → Test one behavior
- [ ] **Test edge cases** → Null, empty, boundary values
- [ ] **Use AssertJ** → Fluent, readable assertions
- [ ] **Parameterized for multiple inputs** → `@ParameterizedTest`
- [ ] **Test data builders for complex objects** → Readable test setup

---

## Quick Reference

### Test Type Selection

| What to Test | Annotation | Dependencies |
|--------------|------------|--------------|
| Pure logic | None (plain JUnit) | - |
| JPA repository | `@DataJpaTest` | H2/TestContainers |
| REST controller | `@WebMvcTest` | MockMvc |
| Full API flow | `@SpringBootTest` | All |
| External HTTP | WireMock | - |

### Assertion Styles

| Need | AssertJ |
|------|---------|
| Equality | `assertThat(x).isEqualTo(y)` |
| Null check | `assertThat(x).isNull()` / `.isNotNull()` |
| Collection | `assertThat(list).hasSize(3).contains(a, b)` |
| Optional | `assertThat(opt).isPresent().contains(value)` |
| Exception | `assertThatThrownBy(() -> ...).isInstanceOf(...)` |
| Boolean | `assertThat(flag).isTrue()` |
