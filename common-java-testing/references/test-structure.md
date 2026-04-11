# Test Structure Reference

## Given-When-Then Pattern (AAA)

### Structure

```java
@Test
void whenValidOrder_shouldCalculateTotal() {
    // Given - Arrange: setup test data
    var item1 = new OrderItem("product-1", 10.00, 2);
    var item2 = new OrderItem("product-2", 15.00, 1);
    var order = Order.create(List.of(item1, item2));

    // When - Act: execute the action under test
    var total = order.calculateTotal();

    // Then - Assert: verify the results
    assertThat(total).isEqualTo(35.00);
}
```

### Key Rules

1. **Blank lines separate sections** → Visual clarity
2. **Given sets up preconditions** → All test data created here
3. **When executes ONE action** → Single method call
4. **Then verifies outcome** → Assertions only

---

## Test Naming Conventions

### Pattern 1: when_should

```java
void whenCreateWithValidData_shouldReturnCreated()
void whenCreateWithBlankName_shouldReturn400()
void whenGetWithInvalidId_shouldReturn404()
void whenUnauthorizedUser_shouldReturn403()
```

### Pattern 2: @DisplayName

```java
@Test
@DisplayName("Should return 404 when order ID doesn't exist")
void orderNotFound() {
    // ...
}

@Test
@DisplayName("Should calculate 10% discount for premium customers")
void premiumDiscount() {
    // ...
}
```

### Pattern 3: methodName_stateUnderTest_expectedBehavior

```java
void calculateTotal_withEmptyCart_shouldReturnZero()
void calculateTotal_withDiscountCode_shouldApplyDiscount()
void findById_whenUserExists_shouldReturnUser()
```

---

## Test Isolation

### 🔴 BLOCKING Rules

```java
// 🔴 WRONG - Shared mutable state
private static List<Order> orders = new ArrayList<>();

@Test
void test1() {
    orders.add(new Order());  // Pollutes state for test2
}

// ✅ CORRECT - Fresh state per test
@BeforeEach
void setUp() {
    orders = new ArrayList<>();
}
```

### Unique Identifiers

```java
// Pattern: Descriptive name + context
String uniqueEmail = "test.user+" + testInfo.getDisplayName() + "@example.com";

// Pattern: UUID for database uniqueness
String categoryName = "TestCategory_" + UUID.randomUUID();
```

### No Order Dependency

```java
// 🔴 WRONG - test2 depends on test1's side effect
@Test @Order(1)
void test1_createOrder() {
    createdOrderId = service.create(order).getId();
}

@Test @Order(2)
void test2_verifyOrder() {
    var order = service.findById(createdOrderId);  // Fails if test1 skipped!
}

// ✅ CORRECT - Each test is independent
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
// ✅ CORRECT - All data visible in test
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
// For complex objects, use builders
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

### Fixed vs Random Data

```java
// 🔴 WRONG - Random makes failures hard to reproduce
@Test
void shouldValidateEmail() {
    String email = "user" + Math.random() + "@test.com";
    // If this fails, you can't reproduce with same input!
}

// ✅ CORRECT - Fixed, reproducible
@Test
void shouldValidateEmail() {
    String validEmail = "john.doe@example.com";
    String invalidEmail = "not-an-email";

    assertThat(validator.isValid(validEmail)).isTrue();
    assertThat(validator.isValid(invalidEmail)).isFalse();
}
```

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

### Using @Nested

```java
class OrderServiceTest {

    @Nested
    @DisplayName("create()")
    class Create {

        @Test
        @DisplayName("should create order with valid data")
        void validData() { }

        @Test
        @DisplayName("should throw when customer not found")
        void customerNotFound() { }
    }

    @Nested
    @DisplayName("cancel()")
    class Cancel {

        @Test
        @DisplayName("should cancel pending order")
        void pendingOrder() { }

        @Test
        @DisplayName("should throw when already shipped")
        void alreadyShipped() { }
    }
}
```

---

## Coverage Checklist

Every public method should test:

| Scenario | HTTP Status |
|----------|-------------|
| Happy path | 200, 201 |
| Validation errors | 400 |
| Not found | 404 |
| Unauthorized | 401 |
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

## Test Pyramid: Avoiding Overlap

### Severity: 🟡 WARNING

Each scenario should be tested at **exactly one level** of the test pyramid.
Duplicating the same assertion across unit, integration, and E2E tests wastes time and slows CI
without increasing confidence.

### Decision Tree: Where to Test What

| What You're Testing | Test Level | Why |
|---------------------|-----------|-----|
| Pure business logic (calculations, validation, transformations) | **Unit test** | No I/O needed, fast |
| Database queries, JPA mappings, transactions | **Integration test** (`@DataJpaTest`, Testcontainers) | Needs real DB |
| HTTP contract (status codes, serialization, validation) | **Integration test** (`@WebMvcTest`, E2E) | Needs Spring context |
| Full user flow across multiple services | **E2E test** | Needs running application |

### Anti-Pattern: Duplicate Scenarios

```java
// 🔴 WRONG - Same scenario tested at TWO levels

// Unit test (OrderServiceTest.java)
@Test
void whenPremiumCustomer_shouldApply10PercentDiscount() {
    var order = Order.create(premiumCustomer, items);
    assertThat(order.getDiscount()).isEqualTo(new BigDecimal("10.00"));
}

// Integration test (OrderServiceIntegrationTest.java)
@Test
void whenPremiumCustomer_shouldApply10PercentDiscount() {
    // Same logic, but with Spring context and real DB — redundant!
    var order = orderService.createOrder(premiumCustomerRequest);
    assertThat(order.getDiscount()).isEqualTo(new BigDecimal("10.00"));
}
```

```java
// ✅ CORRECT - Each level tests what only IT can test

// Unit test — business logic (no DB, no Spring)
@Test
void whenPremiumCustomer_shouldApply10PercentDiscount() {
    var order = Order.create(premiumCustomer, items);
    assertThat(order.getDiscount()).isEqualTo(new BigDecimal("10.00"));
}

// Integration test — DB persistence only (not the discount calculation)
@Test
void whenCreateOrder_shouldPersistWithCorrectStatus() {
    var saved = orderRepository.save(OrderEntity.fromDomain(order));
    var found = orderRepository.findById(saved.getId());
    assertThat(found).isPresent();
    assertThat(found.get().getStatus()).isEqualTo(OrderStatus.PENDING);
}
```

### Rules
1. **Before writing a test**, check if the scenario is already covered at another level
2. Unit tests own **business logic** — if it's pure computation, test it here only
3. Integration tests own **infrastructure** — DB queries, external service calls, serialization
4. E2E tests own **user flows** — multi-step scenarios that cross service boundaries
5. If a unit test already validates a calculation, the integration test should NOT re-validate it
