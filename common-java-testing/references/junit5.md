# JUnit 5 Reference

## Setup & Annotations

### Basic Test Class

```java
@ExtendWith(MockitoExtension.class)  // If using Mockito
class OrderServiceTest {

    @Mock
    private StripeClient stripeClient;  // External service mock

    @InjectMocks
    private OrderService orderService;

    @BeforeEach
    void setUp() {
        // Fresh state for each test
    }

    @Test
    void shouldCreateOrder() {
        // Test implementation
    }
}
```

### Lifecycle Annotations

| Annotation | Scope | Use Case |
|------------|-------|----------|
| `@BeforeEach` | Per test | Reset state, create test data |
| `@AfterEach` | Per test | Cleanup resources |
| `@BeforeAll` | Per class | Expensive setup (static) |
| `@AfterAll` | Per class | Expensive cleanup (static) |

```java
class DatabaseTest {

    @BeforeAll
    static void startDatabase() {
        // Start Testcontainers once
    }

    @BeforeEach
    void cleanTables() {
        // Clean data before each test
    }

    @AfterAll
    static void stopDatabase() {
        // Stop containers
    }
}
```

---

## @Nested Classes

### Group by Method Under Test

```java
class UserServiceTest {

    @Nested
    @DisplayName("register()")
    class Register {

        @Test
        @DisplayName("should create user with valid data")
        void validData() { }

        @Test
        @DisplayName("should throw when email already exists")
        void duplicateEmail() { }

        @Test
        @DisplayName("should hash password before saving")
        void passwordHashing() { }
    }

    @Nested
    @DisplayName("authenticate()")
    class Authenticate {

        @Test
        @DisplayName("should return token for valid credentials")
        void validCredentials() { }

        @Test
        @DisplayName("should throw for invalid password")
        void invalidPassword() { }
    }
}
```

### Group by Scenario

```java
class OrderServiceTest {

    @Nested
    @DisplayName("When order is pending")
    class WhenPending {

        private Order pendingOrder;

        @BeforeEach
        void setUp() {
            pendingOrder = createOrder(OrderStatus.PENDING);
        }

        @Test void canBeCancelled() { }
        @Test void canBeUpdated() { }
        @Test void canBeShipped() { }
    }

    @Nested
    @DisplayName("When order is shipped")
    class WhenShipped {

        private Order shippedOrder;

        @BeforeEach
        void setUp() {
            shippedOrder = createOrder(OrderStatus.SHIPPED);
        }

        @Test void cannotBeCancelled() { }
        @Test void cannotBeUpdated() { }
        @Test void canBeDelivered() { }
    }
}
```

---

## @ParameterizedTest

### @ValueSource (Single Values)

```java
@ParameterizedTest
@ValueSource(strings = {"", " ", "   ", "\t", "\n"})
void shouldRejectBlankNames(String name) {
    assertThrows(ValidationException.class,
        () -> service.create(name));
}

@ParameterizedTest
@ValueSource(ints = {-1, 0, -100})
void shouldRejectNegativeQuantity(int quantity) {
    assertThrows(ValidationException.class,
        () -> new OrderItem("product", quantity));
}
```

### @CsvSource (Multiple Values)

```java
@ParameterizedTest
@CsvSource({
    "100.00, 10, 90.00",    // 10% discount
    "50.00, 20, 40.00",     // 20% discount
    "200.00, 0, 200.00"     // No discount
})
void shouldApplyDiscount(BigDecimal price, int discountPercent, BigDecimal expected) {
    var result = discountService.apply(price, discountPercent);
    assertThat(result).isEqualByComparingTo(expected);
}
```

### @EnumSource

```java
@ParameterizedTest
@EnumSource(OrderStatus.class)
void shouldHandleAllStatuses(OrderStatus status) {
    var order = Order.builder().status(status).build();
    assertDoesNotThrow(() -> service.process(order));
}

@ParameterizedTest
@EnumSource(value = OrderStatus.class, names = {"PENDING", "CONFIRMED"})
void shouldAllowCancellation(OrderStatus status) {
    var order = Order.builder().status(status).build();
    assertDoesNotThrow(() -> service.cancel(order));
}
```

### @MethodSource (Complex Objects)

```java
@ParameterizedTest
@MethodSource("invalidEmailProvider")
void shouldRejectInvalidEmails(String email, String expectedError) {
    var result = validator.validate(email);
    assertThat(result.getError()).isEqualTo(expectedError);
}

static Stream<Arguments> invalidEmailProvider() {
    return Stream.of(
        Arguments.of("", "Email is required"),
        Arguments.of("no-at-sign", "Invalid email format"),
        Arguments.of("no-domain@", "Invalid email format"),
        Arguments.of("@no-local.com", "Invalid email format")
    );
}
```

---

## Exception Testing

### assertThrows

```java
@Test
void shouldThrowWhenNotFound() {
    UUID invalidId = UUID.randomUUID();

    var exception = assertThrows(OrderNotFoundException.class,
        () -> service.findById(invalidId));

    assertThat(exception.getMessage()).contains(invalidId.toString());
}
```

### assertDoesNotThrow

```java
@Test
void shouldNotThrowForValidInput() {
    assertDoesNotThrow(() -> service.process(validInput));
}
```

---

## assertAll (Grouped Assertions)

```java
@Test
void shouldCreateOrderWithAllFields() {
    var created = service.create(request);

    assertAll("order fields",
        () -> assertThat(created.getId()).isNotNull(),
        () -> assertThat(created.getStatus()).isEqualTo(PENDING),
        () -> assertThat(created.getCustomerId()).isEqualTo(customerId),
        () -> assertThat(created.getItems()).hasSize(2),
        () -> assertThat(created.getCreatedAt()).isNotNull()
    );
}
```

**Why?** All assertions run even if one fails → See all failures at once.

---

## @DisplayName

```java
@Test
@DisplayName("Should return 404 when order doesn't exist")
void orderNotFound() { }

@Test
@DisplayName("Should apply 10% discount for premium customers")
void premiumDiscount() { }

@Nested
@DisplayName("When user is not authenticated")
class WhenNotAuthenticated {
    @Test
    @DisplayName("Should return 401 Unauthorized")
    void shouldReturn401() { }
}
```

---

## Timeouts

```java
@Test
@Timeout(5)  // Fails if takes longer than 5 seconds
void shouldCompleteQuickly() {
    service.process(input);
}

@Test
@Timeout(value = 500, unit = TimeUnit.MILLISECONDS)
void shouldRespondFast() {
    client.ping();
}
```

---

## Conditional Execution

```java
@Test
@EnabledOnOs(OS.LINUX)
void onlyOnLinux() { }

@Test
@DisabledIfEnvironmentVariable(named = "CI", matches = "true")
void notOnCI() { }

@Test
@EnabledIf("customCondition")
void conditionalTest() { }

boolean customCondition() {
    return System.getProperty("runSlowTests") != null;
}
```

---

## Test Instance Lifecycle

```java
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class ExpensiveSetupTest {

    private ExpensiveResource resource;

    @BeforeAll
    void setUp() {  // No need for static!
        resource = new ExpensiveResource();
    }

    @Test void test1() { }
    @Test void test2() { }

    @AfterAll
    void tearDown() {
        resource.close();
    }
}
```

---

## Assumptions

```java
@Test
void onlyWhenDatabaseAvailable() {
    assumeTrue(isDatabaseRunning(), "Database not available");

    // Test only runs if assumption passes
    var result = repository.findAll();
    assertThat(result).isNotEmpty();
}
```
