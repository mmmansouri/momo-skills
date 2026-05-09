# Test Structure Reference

> Patterns for structuring, naming, isolating, and organising tests.

---

## Table of Contents

1. [Given-When-Then Pattern (AAA)](#given-when-then-pattern-aaa)
2. [Test Naming Conventions](#test-naming-conventions)
3. [Test Isolation](#test-isolation)
4. [Test Data Patterns](#test-data-patterns)
5. [TDD Workflow (Red → Green → Refactor)](#tdd-workflow-red--green--refactor)
6. [Test Organization](#test-organization)
7. [Coverage Checklist](#coverage-checklist)
8. [Test Pyramid — Avoiding Overlap](#test-pyramid--avoiding-overlap)

---

## Given-When-Then Pattern (AAA)

### Structure

```java
@Test
void whenValidOrder_shouldCalculateTotal() {
    // Given — Arrange: setup test data
    var item1 = new OrderItem("product-1", 10.00, 2);
    var item2 = new OrderItem("product-2", 15.00, 1);
    var order = Order.create(List.of(item1, item2));

    // When — Act: execute the action under test
    var total = order.calculateTotal();

    // Then — Assert: verify the results
    assertThat(total).isEqualTo(35.00);
}
```

### 🔴 BLOCKING — One When Per Test

**Why:** if a test has two `// When` calls, a failure can't tell you which call broke. Reviewers also can't read the test as a single behaviour.
**How to apply:** if you find yourself adding a second action, write a second test instead.

### Key Rules

1. **Blank lines separate sections** → Visual clarity
2. **Given sets up preconditions** → All test data created here
3. **When executes ONE action** → Single method call
4. **Then verifies outcome** → Assertions only

---

## Test Naming Conventions

### 🔴 BLOCKING — Tests Must Describe Behaviour

**Why:** failing test names appear in CI logs without their body. `test1` failing tells nobody anything; `whenInvalidId_shouldReturn404` failing tells the reviewer where to look.

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

## Test Isolation

### 🔴 BLOCKING — No Shared Mutable State

**Why:** order-dependent tests fail randomly when JUnit reorders, parallelises, or filters them — and the failure points at the wrong test.
**How to apply:** if a test passes alone but fails in the suite (or vice-versa), that's a shared-state bug — fix it before merging.

```java
// 🔴 WRONG — Shared mutable state
private static List<Order> orders = new ArrayList<>();

@Test
void test1() {
    orders.add(new Order());  // Pollutes state for test2
}

// ✅ CORRECT — Fresh state per test
@BeforeEach
void setUp() {
    orders = new ArrayList<>();
}
```

### Unique Identifiers

```java
// Pattern: Descriptive name + context
String uniqueEmail = "test.user+" + testInfo.getDisplayName() + "@example.com";

// Pattern: Deterministic UUID for reproducible failures
UUID id = UUID.fromString("00000000-0000-0000-0000-000000000001");
```

### 🔴 BLOCKING — No Order Dependency

**Why:** JUnit 5 reorders tests by default for stability. `@Order` annotations bind your suite to today's execution model and silently rot the moment someone deletes a test.

```java
// 🔴 WRONG — test2 depends on test1's side effect
@Test @Order(1)
void test1_createOrder() {
    createdOrderId = service.create(order).getId();
}

@Test @Order(2)
void test2_verifyOrder() {
    var order = service.findById(createdOrderId);  // Fails if test1 skipped!
}

// ✅ CORRECT — Each test is independent
@Test
void shouldCreateOrder() {
    var created = service.create(order);
    assertThat(created.getId()).isNotNull();
}

@Test
void shouldFindOrder() {
    var created = service.create(order);  // Setup within test
    var found = service.findById(created.getId());
    assertThat(found).isPresent();
}
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

### Fixed vs Random Data

```java
// 🔴 WRONG — Random makes failures hard to reproduce
String email = "user" + Math.random() + "@test.com";

// ✅ CORRECT — Fixed, reproducible
String validEmail = "john.doe@example.com";
String invalidEmail = "not-an-email";
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

---

## Test Pyramid — Avoiding Overlap

```
         /\
        /  \     E2E (few, slow, expensive)
       /----\    Real browser / full HTTP cycle
      /      \
     /--------\  Integration (some)
    /          \ @SpringBootTest, @DataJpaTest, @WebMvcTest
   /------------\
  /              \ Unit (many, fast, cheap)
 /----------------\ Plain JUnit, no framework
```

### 🟡 WARNING — One scenario, one test level

**Why:** the same assertion at three levels triples CI cost without adding signal — and when the behaviour changes, three places need updating.
**How to apply:** before writing a test, check if the scenario is already covered higher up the pyramid.

### Anti-Pattern — Duplicate Scenarios

```java
// 🔴 WRONG — Same scenario tested at TWO levels

// Unit test
@Test
void whenPremiumCustomer_shouldApply10PercentDiscount() {
    var order = Order.create(premiumCustomer, items);
    assertThat(order.getDiscount()).isEqualTo(new BigDecimal("10.00"));
}

// Integration test — same logic, redundant
@Test
void whenPremiumCustomer_shouldApply10PercentDiscount() {
    var order = orderService.createOrder(premiumCustomerRequest);
    assertThat(order.getDiscount()).isEqualTo(new BigDecimal("10.00"));
}
```

```java
// ✅ CORRECT — Each level tests what only IT can test

// Unit test — pure business logic
@Test
void whenPremiumCustomer_shouldApply10PercentDiscount() {
    var order = Order.create(premiumCustomer, items);
    assertThat(order.getDiscount()).isEqualTo(new BigDecimal("10.00"));
}

// Integration test — persistence behaviour only (not the discount math)
@Test
void shouldPersistWithCorrectStatus() {
    var saved = orderRepository.save(OrderEntity.fromDomain(order));
    assertThat(orderRepository.findById(saved.getId()))
        .get().extracting(OrderEntity::getStatus).isEqualTo(OrderStatus.PENDING);
}
```

### Ownership Rules

1. **Unit tests own business logic** — pure computation, no Spring, no DB
2. **Integration tests own infrastructure** — DB queries, serialisation, external client wiring
3. **E2E tests own user flows** — multi-step scenarios crossing service boundaries
4. If a unit test validates a calculation, the integration test must **not** re-validate it
