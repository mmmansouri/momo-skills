# Mockito Reference

> Mockito 5+ patterns. Stack baseline: JUnit 5.13+, Spring Framework 7 / Spring Boot 4, Java 25.

---

## Table of Contents

1. [Setup](#setup)
2. [What to Mock — Decision Guide](#what-to-mock-decision-guide)
3. [Stubbing](#stubbing)
4. [Verification](#verification)
5. [Argument Matchers](#argument-matchers)
6. [Anti-Patterns](#anti-patterns)
7. [Spy (Partial Mock)](#spy-partial-mock)
8. [BDD Style (Given-When-Then)](#bdd-style-given-when-then)
9. [Mockito with Spring Boot 4](#mockito-with-spring-boot-4)

---

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

## What to Mock — Decision Guide

### 🔴 NEVER Mock

**Why:** mocking internals locks tests to today's implementation — every refactor breaks tests even when behaviour is unchanged. The test stops protecting behaviour and starts protecting implementation.

| Type | Why | Alternative |
|------|-----|-------------|
| Internal services | Hides integration bugs | Use real objects |
| Repositories | Test real queries | `@DataJpaTest` + Testcontainers `@ServiceConnection` |
| Value objects / records | No behaviour to mock | Create with `new` |
| Third-party libs | They may change | Wrap them, then mock the wrapper |
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

**Why:** calling `reset()` mid-test signals the test is doing two unrelated things — split it.

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

## Mockito with Spring Boot 4

### 🔴 BLOCKING — Use `@MockitoBean`, Not `@MockBean`

**Why:** `@MockBean` and `@SpyBean` were Spring Boot extensions; Spring Framework 6.2 promoted them to first-class framework annotations (`@MockitoBean` / `@MockitoSpyBean`) and Spring Boot 4 **removed** the deprecated names. New tests must use the framework annotations.

### Annotation Selection

| Annotation | Context | Use Case |
|------------|---------|----------|
| `@Mock` | No Spring | Plain unit tests |
| `@MockitoBean` | Spring Boot 4 / SF 7 | Replace bean in test ApplicationContext |
| `@MockitoSpyBean` | Spring Boot 4 / SF 7 | Spy on real bean in test ApplicationContext |
| `@TestBean` | Spring Boot 4 / SF 7 | Provide a real (non-mock) test instance |

```java
import org.springframework.test.context.bean.override.mockito.MockitoBean;

@SpringBootTest
class OrderControllerE2ETest {

    @MockitoBean
    private StripeClient stripeClient;  // Replaces real StripeClient in context

    @Autowired
    private MockMvcTester mvc;

    @Test
    void shouldProcessPayment() {
        when(stripeClient.charge(any())).thenReturn(success());

        assertThat(mvc.post().uri("/orders").contentType(APPLICATION_JSON).content(json))
            .hasStatus(CREATED);
    }
}
```

### 🟡 Migration Caveat

`@MockitoBean` is **not** supported on `@Configuration` or `@Component` classes (unlike the old `@MockBean`). Place it only on test classes.

📚 More details on bean overrides: see `spring-boot-testing.md` § Bean Overrides.

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
