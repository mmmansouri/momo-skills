# Test Structure Reference

> Java-specific patterns for naming, test data, TDD, organisation, and coverage.
> The language-agnostic foundations (Given-When-Then layout, one-behavior-per-test,
> isolation, test pyramid) are owned by `common-developer` § When Writing Tests — load it.

---

## Table of Contents

1. [Test Naming Conventions](#test-naming-conventions)
2. [Test Data Patterns](#test-data-patterns)
3. [TDD Workflow (Red → Green → Refactor)](#tdd-workflow-red--green--refactor)
4. [Test Organization](#test-organization)
5. [Coverage Checklist](#coverage-checklist)

---

## Test Naming Conventions

Foundation (names state behavior + condition) is owned by `common-developer`. The house Java patterns:

### Pattern 1 — `when_should`

```java
void whenCreateWithValidData_shouldReturnCreated()
void whenCreateWithBlankName_shouldReturn400()
void whenGetWithInvalidId_shouldReturn404()
void whenUnauthorizedUser_shouldReturn403()
```

### Pattern 2 — `@DisplayName`

```java
@Test
@DisplayName("Should return 404 when order ID doesn't exist")
void orderNotFound() { /* ... */ }

@Test
@DisplayName("Should calculate 10% discount for premium customers")
void premiumDiscount() { /* ... */ }
```

### Pattern 3 — `methodName_stateUnderTest_expectedBehavior`

```java
void calculateTotal_withEmptyCart_shouldReturnZero()
void calculateTotal_withDiscountCode_shouldApplyDiscount()
void findById_whenUserExists_shouldReturnUser()
```

---

## Test Data Patterns

### Self-Contained Tests

```java
// ✅ CORRECT — All data visible in test
@Test
void shouldApplyDiscount() {
    var customer = Customer.builder()
        .type(CustomerType.PREMIUM)
        .build();
    var order = Order.builder()
        .customer(customer)
        .total(new BigDecimal("100.00"))
        .build();

    var discounted = discountService.apply(order);

    assertThat(discounted.getTotal()).isEqualTo(new BigDecimal("90.00"));
}
```

### Test Data Builders

```java
public class OrderTestBuilder {

    private UUID customerId = UUID.randomUUID();
    private List<OrderItem> items = new ArrayList<>();
    private OrderStatus status = OrderStatus.PENDING;

    public static OrderTestBuilder anOrder() {
        return new OrderTestBuilder();
    }

    public OrderTestBuilder withCustomer(UUID customerId) {
        this.customerId = customerId;
        return this;
    }

    public OrderTestBuilder withItem(String productId, int quantity) {
        items.add(new OrderItem(productId, quantity));
        return this;
    }

    public Order build() {
        return new Order(customerId, items, status);
    }
}

// Usage
var order = anOrder()
    .withCustomer(customerId)
    .withItem("product-1", 2)
    .build();
```

### Factory Methods (Simpler Alternative)

```java
public class TestData {

    public static User validUser() {
        return new User(1L, "user@test.com", "Test User", UserRole.CUSTOMER, true);
    }

    public static Order pendingOrder(User user) {
        return new Order(1L, user, OrderStatus.PENDING, List.of(defaultItem()));
    }
}
```

### Unique Identifiers

```java
// Pattern: Descriptive name + context
String uniqueEmail = "test.user+" + testInfo.getDisplayName() + "@example.com";

// Pattern: Deterministic UUID for reproducible failures
UUID id = UUID.fromString("00000000-0000-0000-0000-000000000001");
```

---

## TDD Workflow (Red → Green → Refactor)

```
1. RED       — Write a failing test (defines expected behaviour)
2. GREEN     — Write minimal code to pass the test
3. REFACTOR  — Improve code while keeping tests green
```

### Example

```java
// Step 1 — RED — Failing test first
@Test
void shouldCalculateTaxForOrder() {
    var calculator = new TaxCalculator();
    var order = new Order(100.0);

    assertThat(calculator.calculate(order)).isEqualTo(10.0);  // 10% tax
}
// Test fails: TaxCalculator doesn't exist yet

// Step 2 — GREEN — Minimal implementation
public class TaxCalculator {
    public double calculate(Order order) {
        return order.total() * 0.10;
    }
}
// Test passes

// Step 3 — REFACTOR — Improve without changing behaviour
public class TaxCalculator {
    private static final double TAX_RATE = 0.10;

    public double calculate(Order order) {
        Objects.requireNonNull(order, "Order cannot be null");
        return order.total() * TAX_RATE;
    }
}
// Tests still pass — refactor successful
```

### Benefits

- **Design emerges** from requirements (test-first = spec-first)
- **Fast feedback** — break-detection within seconds
- **Documentation** — tests show how code should be used
- **Refactor confidence** — green suite is the safety net

---

## Test Organization

### By Feature (Recommended)

```
src/test/java/com/example/
├── order/
│   ├── OrderServiceTest.java
│   ├── OrderControllerE2ETest.java
│   └── OrderJpaAdapterTest.java
├── customer/
│   ├── CustomerServiceTest.java
│   └── CustomerControllerE2ETest.java
└── shared/
    └── AbstractIntegrationTest.java
```

### Using `@Nested`

```java
class OrderServiceTest {

    @Nested
    @DisplayName("create()")
    class Create {
        @Test @DisplayName("should create order with valid data")
        void validData() { }

        @Test @DisplayName("should throw when customer not found")
        void customerNotFound() { }
    }

    @Nested
    @DisplayName("cancel()")
    class Cancel {
        @Test @DisplayName("should cancel pending order")
        void pendingOrder() { }

        @Test @DisplayName("should throw when already shipped")
        void alreadyShipped() { }
    }
}
```

---

## Coverage Checklist

Every public endpoint should test:

| Scenario | HTTP Status |
|----------|-------------|
| Happy path | 200, 201 |
| Validation errors | 400 |
| Not found | 404 |
| Unauthorised | 401 |
| Forbidden | 403 |
| Edge cases | varies |

```java
@Nested
class CreateOrder {
    @Test void whenValidData_shouldReturn201() { }
    @Test void whenBlankName_shouldReturn400() { }
    @Test void whenCustomerNotFound_shouldReturn404() { }
    @Test void whenNotAuthenticated_shouldReturn401() { }
    @Test void whenNotAdmin_shouldReturn403() { }
    @Test void whenEmptyItems_shouldReturn400() { }
}
```

**Pyramid ownership** (foundation in `common-developer`): unit tests own business logic; integration tests own infrastructure (DB queries, serialisation, client wiring); E2E tests own user flows. If a unit test validates a calculation, the integration test must **not** re-validate it.
