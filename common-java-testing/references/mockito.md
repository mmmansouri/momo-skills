# Mockito Reference

## Setup

### JUnit 5 Integration

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private PaymentClient paymentClient;  // External service

    @Mock
    private EmailService emailService;    // External service

    @InjectMocks
    private OrderService orderService;    // Class under test

    // Mockito injects mocks into orderService constructor
}
```

### Manual Setup (When Needed)

```java
class OrderServiceTest {

    private PaymentClient paymentClient;
    private OrderService orderService;

    @BeforeEach
    void setUp() {
        paymentClient = Mockito.mock(PaymentClient.class);
        orderService = new OrderService(paymentClient);
    }
}
```

---

## What to Mock (Decision Guide)

### 🔴 NEVER Mock

| Type | Why | Alternative |
|------|-----|-------------|
| Internal services | Hides integration bugs | Use real objects |
| Repositories | Test real queries | `@DataJpaTest` or Testcontainers |
| Value objects/DTOs | No behavior to mock | Create with `new` |
| Third-party libs | They may change | Create wrapper interface |
| `List`, `Map`, `String` | Unnecessary | Use real instances |

### ✅ DO Mock

| Type | Tool | Example |
|------|------|---------|
| HTTP clients | WireMock | External APIs |
| Payment gateways | Mock interface | Stripe, PayPal |
| Email services | Mock interface | SMTP gateway |
| SMS services | Mock interface | Twilio |
| Time/Clock | Inject `Clock` | `Clock.fixed()` |
| Random | Inject source | Deterministic tests |

---

## Stubbing

### Basic Stubbing

```java
// Return value
when(paymentClient.charge(any())).thenReturn(new PaymentResult(SUCCESS));

// Return different values on consecutive calls
when(service.getStatus())
    .thenReturn(PENDING)
    .thenReturn(PROCESSING)
    .thenReturn(COMPLETED);

// Throw exception
when(paymentClient.charge(any()))
    .thenThrow(new PaymentFailedException("Card declined"));
```

### Argument-Specific Stubbing

```java
// 🔴 WRONG - any() is too broad
when(service.findById(any())).thenReturn(Optional.of(user));

// ✅ CORRECT - Specific argument
when(service.findById(eq(userId))).thenReturn(Optional.of(user));
when(service.findById(eq(unknownId))).thenReturn(Optional.empty());
```

### Answer (Dynamic Response)

```java
when(repository.save(any(Order.class)))
    .thenAnswer(invocation -> {
        Order order = invocation.getArgument(0);
        return order.withId(UUID.randomUUID());  // Simulate ID generation
    });
```

---

## Verification

### Basic Verification

```java
// Verify method was called
verify(emailService).sendOrderConfirmation(any());

// Verify never called
verify(emailService, never()).sendOrderConfirmation(any());

// Verify call count
verify(repository, times(2)).save(any());
verify(repository, atLeastOnce()).findById(any());
verify(repository, atMost(3)).findAll();
```

### Verify with Specific Arguments

```java
// 🔴 WRONG - any() doesn't verify actual value
verify(emailService).send(any());

// ✅ CORRECT - Verify specific email was sent
verify(emailService).send(eq("customer@example.com"));
```

### ArgumentCaptor

```java
@Captor
private ArgumentCaptor<Order> orderCaptor;

@Test
void shouldSaveOrderWithCorrectData() {
    service.createOrder(request);

    verify(repository).save(orderCaptor.capture());

    Order savedOrder = orderCaptor.getValue();
    assertThat(savedOrder.getCustomerId()).isEqualTo(customerId);
    assertThat(savedOrder.getItems()).hasSize(2);
    assertThat(savedOrder.getStatus()).isEqualTo(PENDING);
}
```

### Verify Order of Calls

```java
InOrder inOrder = inOrder(paymentClient, repository, emailService);

inOrder.verify(paymentClient).charge(any());
inOrder.verify(repository).save(any());
inOrder.verify(emailService).sendConfirmation(any());
```

---

## Argument Matchers

### Common Matchers

| Matcher | Use Case |
|---------|----------|
| `eq(value)` | Exact match |
| `any()` | Any value (avoid when possible) |
| `any(Class.class)` | Any instance of type |
| `anyString()` | Any string |
| `anyList()` | Any list |
| `isNull()` | Null value |
| `notNull()` | Non-null value |
| `argThat(predicate)` | Custom condition |

### Custom Matcher

```java
when(service.findByEmail(argThat(email ->
    email != null && email.endsWith("@example.com"))))
    .thenReturn(Optional.of(user));
```

### ⚠️ Matcher Rules

```java
// 🔴 WRONG - Mix of raw value and matcher
when(service.process("value", any())).thenReturn(result);

// ✅ CORRECT - All matchers
when(service.process(eq("value"), any())).thenReturn(result);
```

---

## Anti-Patterns

### Don't Use reset()

```java
// 🔴 WRONG - Indicates test does too much
@Test
void testMultipleScenarios() {
    service.methodA();
    verify(mock).called();

    reset(mock);  // Code smell!

    service.methodB();
    verify(mock).calledAgain();
}

// ✅ CORRECT - Separate tests
@Test
void scenarioA() {
    service.methodA();
    verify(mock).called();
}

@Test
void scenarioB() {
    service.methodB();
    verify(mock).calledAgain();
}
```

### Don't Mock Final/Static (Usually)

```java
// If you need to mock final/static, refactor first:

// 🔴 WRONG - Static dependency
public class OrderService {
    public void process() {
        Instant now = Instant.now();  // Hard to test!
    }
}

// ✅ CORRECT - Inject Clock
public class OrderService {
    private final Clock clock;

    public OrderService(Clock clock) {
        this.clock = clock;
    }

    public void process() {
        Instant now = Instant.now(clock);  // Testable!
    }
}

// Test with fixed clock
Clock fixedClock = Clock.fixed(Instant.parse("2024-01-15T10:00:00Z"), ZoneOffset.UTC);
var service = new OrderService(fixedClock);
```

### Don't Mock Value Objects

```java
// 🔴 WRONG - Unnecessary mock
@Mock private Order order;
when(order.getId()).thenReturn(orderId);
when(order.getStatus()).thenReturn(PENDING);

// ✅ CORRECT - Just create the object
Order order = Order.builder()
    .id(orderId)
    .status(PENDING)
    .build();
```

---

## Spy (Partial Mock)

Use sparingly - usually indicates need for refactoring.

```java
@Spy
private OrderService orderService = new OrderService(realDependency);

@Test
void shouldSkipExpensiveOperation() {
    // Mock only one method, keep others real
    doReturn(cachedResult).when(orderService).expensiveOperation();

    var result = orderService.process(input);

    // expensiveOperation returns cached, other methods run normally
}
```

---

## BDD Style (Given-When-Then)

```java
import static org.mockito.BDDMockito.*;

@Test
void shouldChargeCustomer() {
    // Given
    given(paymentClient.charge(any()))
        .willReturn(new PaymentResult(SUCCESS));

    // When
    var result = orderService.processPayment(order);

    // Then
    then(paymentClient).should().charge(chargeCaptor.capture());
    assertThat(result.isSuccessful()).isTrue();
}
```

---

## Mockito with Spring Boot

### @MockBean vs @Mock

| Annotation | Context | Use Case |
|------------|---------|----------|
| `@Mock` | No Spring | Unit tests |
| `@MockBean` | Spring Boot | Replace bean in context |

```java
@SpringBootTest
class OrderControllerE2ETest {

    @MockBean  // Replaces real StripeClient in Spring context
    private StripeClient stripeClient;

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void shouldProcessPayment() {
        when(stripeClient.charge(any())).thenReturn(success());

        var response = restTemplate.postForEntity("/orders", request, Order.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
    }
}
```

### Prefer Constructor Injection

```java
// ✅ Testable without Spring
@Service
@RequiredArgsConstructor
public class OrderService {
    private final OrderRepository repository;  // Constructor injection
    private final PaymentClient paymentClient;
}

// Unit test - no Spring needed
class OrderServiceTest {
    @Mock private PaymentClient paymentClient;
    @InjectMocks private OrderService orderService;
}
```
