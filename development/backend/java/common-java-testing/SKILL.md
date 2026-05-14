---
name: common-java-testing
description: >-
  Java testing guide for Spring Boot 4 / Spring Framework 7 / JUnit 5.13+ /
  Mockito 5+ / AssertJ / Testcontainers. Use when writing unit, slice, or
  integration tests; deciding what to mock (external boundaries only); structuring
  tests (Given-When-Then); using fluent assertions; or wiring Testcontainers via
  @ServiceConnection.
---

# Java Testing Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

> **Stack baseline:** Spring Boot 4.x · Spring Framework 7.x · JUnit 5.13+ / 6.x · Mockito 5+ · AssertJ 3.27+ · Testcontainers 2.x · Java 25.

---

## Decision Tree — What Type of Test?

```
What are you testing?
│
├── Pure logic, no I/O, no Spring?
│   └── Unit test (plain JUnit + AssertJ)
│
├── JPA repository or @Entity mapping?
│   └── @DataJpaTest + Testcontainers @ServiceConnection
│
├── REST controller (no service layer concerns)?
│   └── @WebMvcTest + MockMvcTester
│
├── HTTP client (RestClient / WebClient / @HttpExchange)?
│   └── @RestClientTest or MockWebServer
│
├── Full request → DB → response cycle?
│   └── @SpringBootTest + Testcontainers @ServiceConnection
│
├── External HTTP service (Stripe, Mailgun, …)?
│   └── WireMock or MockWebServer (the boundary)
│
└── Async / eventual consistency?
    └── Awaitility (never Thread.sleep)
```

📚 **When choosing a Spring Boot test slice (`@DataJpaTest`, `@WebMvcTest`, `@RestClientTest`, `@SpringBootTest`) or wiring `@MockitoBean`/`@ServiceConnection` → read [spring-boot-testing.md](references/spring-boot-testing.md).**

📚 **When wiring Testcontainers for JPA/HTTP/messaging integration tests via `@ServiceConnection` (Postgres, Kafka, Redis, etc.) → read [testcontainers.md](references/testcontainers.md).**

---

## Testing Philosophy

### 🔴 No-Mock Philosophy

```
PREFER: Real objects wired together (slice tests, integration tests)
MOCK:   Process boundaries only (HTTP, SMTP, payment, filesystem, clock)
NEVER:  Internal services, repositories, value objects, records
```

**Why:** mocks of internal collaborators hide integration bugs and freeze the design — the test passes against a fake that no longer matches the real collaborator.
**How to apply:** if a class lives in your codebase and you own its source, instantiate it. Mock only at the wire (external API, OS resource, time).

### 🔴 Test Isolation

- Each test creates its own data — no shared mutable state
- Use `@BeforeEach` for test-scoped setup; never `static` mutable fields
- Never depend on test execution order
- Never re-use entity IDs across tests in the same class

**Why:** order-dependent tests fail randomly when JUnit reorders, parallelises, or filters them — and the failure points at the wrong test.
**How to apply:** if a test passes alone but fails in the suite (or vice-versa), that's a shared-state bug — fix it before merging.

### 🟢 Fixed Test Data

```java
// 🔴 WRONG — Random data makes failures un-reproducible
String name = "User_" + UUID.randomUUID();

// ✅ CORRECT — Fixed values, reproducible
String name = "TestUser_ValidCase";
```

For UUIDs, use deterministic seeds: `UUID.fromString("00000000-0000-0000-0000-000000000001")`.

---

## When Structuring Tests

📚 **When structuring a test — Given-When-Then layout, `whenX_shouldY` naming, one-behaviour-per-test, KISS-over-DRY in test code → read [test-structure.md](references/test-structure.md).**

### 🔴 Given-When-Then Pattern

```java
@Test
void whenValidInput_shouldReturnExpectedResult() {
    // Given
    var request = new OrderRequest("item-1", 2);

    // When
    var result = orderService.create(request);

    // Then
    assertThat(result.getStatus()).isEqualTo(OrderStatus.CREATED);
}
```

**Why:** the three-block layout makes scope obvious — reviewers can spot a test that does too much (multiple When/Then) at a glance.
**How to apply:** if a test has more than one `// When`, split it.

### 🔴 Naming Convention — `whenX_shouldY`

| Pattern | Example |
|---------|---------|
| `when<Condition>_should<Result>` | `whenInvalidId_shouldReturn404` |
| `<method>_given<Condition>_<expectation>` | `findById_givenMissing_throws` |
| `@DisplayName` for human-readable runner output | `"Should return 404 when ID not found"` |

**Why:** failing test names appear in CI logs and PR comments without their body — `test1` failing tells nobody anything; `whenInvalidId_shouldReturn404` failing tells a reviewer where to look.

### 🟡 WARNING

- **One test = one behaviour** — don't extend a green test with "just one more thing"
- **KISS > DRY in tests** — duplicating a 3-line setup is fine when it makes the scenario obvious

---

## When Using JUnit 5

📚 **When using JUnit 5 features — `@Nested`, `@DisplayName`, `@ParameterizedTest`/`@ParameterizedClass`, lifecycle, exception assertions, grouped assertions → read [junit5.md](references/junit5.md).**

### 🟢 Key Annotations

| Annotation | Use Case |
|------------|----------|
| `@Nested` | Group tests by scenario (`when creating`, `when deleting`) |
| `@DisplayName` | Human-readable name for reports |
| `@ParameterizedTest` | Same logic, multiple inputs |
| `@ParameterizedClass` *(JUnit 5.13+)* | Parameterise the entire test class |
| `@BeforeEach` | Fresh state per test |

### 🟢 Exception Testing — Prefer AssertJ

```java
// ✅ CORRECT — AssertJ fluent (preferred)
assertThatThrownBy(() -> service.findById(invalidId))
    .isInstanceOf(OrderNotFoundException.class)
    .hasMessageContaining(invalidId.toString());

// 🟡 OK but verbose — assertThrows
var ex = assertThrows(OrderNotFoundException.class,
    () -> service.findById(invalidId));
assertThat(ex.getMessage()).contains(invalidId.toString());
```

### 🟢 Grouped Assertions

```java
assertAll("order validation",
    () -> assertThat(order.getId()).isNotNull(),
    () -> assertThat(order.getStatus()).isEqualTo(CREATED),
    () -> assertThat(order.getItems()).hasSize(2)
);
```

---

## When Using Mockito

📚 **When deciding what to mock vs instantiate, writing stubs, using argument matchers, or replacing Spring beans with `@MockitoBean`/`@MockitoSpyBean` → read [mockito.md](references/mockito.md).**

### 🔴 What NOT to Mock

| Type | Why Not |
|------|---------|
| **Internal services** | Test the real integration |
| **Repositories** | Use `@DataJpaTest` + Testcontainers instead |
| **Value objects / records** | Just `new` them |
| **Types you don't own** | Wrap them, then mock the wrapper |

**Why:** mocking internals locks the test to today's implementation — every refactor breaks the test even when behaviour is unchanged. The test stops protecting behaviour and starts protecting implementation.

### 🟢 What TO Mock

| Type | Tool |
|------|------|
| HTTP clients | WireMock, MockWebServer (mock the wire, not the client class) |
| Email / SMS gateways | Mock the gateway interface you own |
| Payment APIs | Mock the client interface you own |
| Clock / Time | Inject `Clock` and provide a fixed one in tests |

### 🟡 Mockito Guidelines

```java
// 🔴 WRONG — mocking an internal repository
@Mock private OrderRepository orderRepository;

// ✅ CORRECT — real repository via @DataJpaTest, mock only the external client
@MockitoBean private StripeClient stripeClient;

// 🔴 WRONG — any() loses specificity, hides regressions
when(service.process(any())).thenReturn(result);

// ✅ CORRECT — assert the actual contract
when(service.process(eq(expectedInput))).thenReturn(result);
```

---

## When Using AssertJ

📚 **When writing assertions — collections, strings, Optionals, exceptions, `extracting()`, recursive comparison, soft assertions → read [assertj.md](references/assertj.md).**

### 🔴 Always Use AssertJ — Not JUnit Assertions

```java
// 🔴 WRONG — JUnit assertions produce poor failure messages
assertEquals(expected, actual);
assertTrue(list.contains(item));

// ✅ CORRECT — AssertJ: fluent, chainable, descriptive errors
assertThat(actual).isEqualTo(expected);
assertThat(list).contains(item);
```

**Why:** AssertJ failure messages show the actual vs expected diff (including for collections/objects); JUnit's `assertTrue(list.contains(item))` just says "expected true, was false" — no clue what was in the list.

### 🟢 Key Patterns

| Need | AssertJ Method |
|------|----------------|
| Null check | `isNull()`, `isNotNull()` |
| Collections | `contains()`, `containsExactly()`, `hasSize()` |
| Strings | `startsWith()`, `contains()`, `matches()` |
| Optional | `isPresent()`, `isEmpty()`, `hasValue(v)` |
| Numbers | `isGreaterThan()`, `isBetween()`, `isCloseTo()` |
| Exceptions | `assertThatThrownBy(...)` |

### 🟢 Advanced Patterns

```java
// Extract specific fields
assertThat(users)
    .extracting(User::getName, User::getEmail)
    .contains(tuple("John", "john@example.com"));

// Recursive comparison (ignore framework-set fields)
assertThat(actual)
    .usingRecursiveComparison()
    .ignoringFields("id", "createdAt")
    .isEqualTo(expected);

// Soft assertions — collect all failures, report once
SoftAssertions.assertSoftly(softly -> {
    softly.assertThat(order.getStatus()).isEqualTo(CREATED);
    softly.assertThat(order.getItems()).hasSize(2);
    softly.assertThat(order.getTotal()).isEqualTo(BigDecimal.valueOf(99.99));
});
```

---

## When Testing Spring Applications

📚 **When testing Spring Boot 4 apps — slice selection (`@DataJpaTest`/`@WebMvcTest`/`@RestClientTest`/`@SpringBootTest`), `MockMvcTester`, `@MockitoBean`, `@ServiceConnection` wiring → read [spring-boot-testing.md](references/spring-boot-testing.md).**

### 🔴 BLOCKING

- **Use `@MockitoBean`, not `@MockBean`** — `@MockBean` was removed in Spring Boot 4.0
- **Use `@MockitoSpyBean`, not `@SpyBean`** — same removal
- **Use `@ServiceConnection`, not `@DynamicPropertySource`** for Testcontainers wiring

**Why:** `@MockBean` / `@SpyBean` were Spring Boot extensions; Spring Framework 6.2 promoted them to first-class framework annotations (`@MockitoBean` / `@MockitoSpyBean`) and Boot 4 removed the deprecated names.

### 🟢 Slice Test Selection

| Test target | Annotation | Loads |
|-------------|------------|-------|
| Pure logic | None — plain JUnit | Nothing |
| `@Repository` | `@DataJpaTest` | JPA + DataSource only |
| `@RestController` | `@WebMvcTest(MyController.class)` | Web layer only |
| RestClient / WebClient bean | `@RestClientTest` | HTTP client + Jackson |
| Full app | `@SpringBootTest` | Entire context |

### 🟢 MockMvcTester (Spring Framework 7) — Default for Controller Tests

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired private MockMvcTester mvc;
    @MockitoBean private OrderService orderService;

    @Test
    void whenOrderExists_returns200() {
        when(orderService.findById(any())).thenReturn(Optional.of(order));

        assertThat(mvc.get().uri("/orders/{id}", id))
            .hasStatusOk()
            .bodyJson()
            .extractingPath("$.status").isEqualTo("CREATED");
    }
}
```

---

## When Testing Async Code

### 🔴 Never Use Thread.sleep()

```java
// 🔴 WRONG — flaky, slow, non-deterministic
service.processAsync(order);
Thread.sleep(2000);
assertThat(repository.findById(id)).isPresent();

// ✅ CORRECT — Awaitility polls until condition is met (or timeout)
service.processAsync(order);
await().atMost(5, SECONDS)
    .untilAsserted(() ->
        assertThat(repository.findById(id)).isPresent());
```

**Why:** `Thread.sleep(2000)` runs for the full 2s every time and still flakes when the machine is slow. `await().untilAsserted(...)` returns as soon as the assertion passes — typically in <100ms — and fails fast with the actual assertion error if it times out.

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] No mocking of internal classes (services, repos, value objects)
- [ ] No shared mutable state between tests
- [ ] Each test creates its own data (no static fixtures mutated by tests)
- [ ] `assertThat()` not `assertEquals()`
- [ ] No `Thread.sleep()` — Awaitility for async assertions
- [ ] `@MockitoBean` / `@MockitoSpyBean` (not the removed `@MockBean` / `@SpyBean`)

### 🟡 WARNING
- [ ] Test names describe behaviour, not implementation
- [ ] No production logic duplicated in test code (use the real method)
- [ ] No duplicate scenarios across unit / integration / E2E layers
- [ ] Specific values in mocks, not blanket `any()`
- [ ] `@ServiceConnection` (not `@DynamicPropertySource`) for Testcontainers

### 🟢 BEST PRACTICE
- [ ] Given-When-Then blocks with blank lines
- [ ] `@Nested` to group related scenarios
- [ ] `@ParameterizedTest` / `@ParameterizedClass` for multi-input cases
- [ ] `extracting()` for field-level collection assertions
- [ ] `SoftAssertions` for multiple independent checks
- [ ] `MockMvcTester` (AssertJ) over plain `MockMvc` (Hamcrest)

---

## Related Skills

- `common-java-developer` — Modern Java patterns (records, sealed, pattern matching)
- `common-java-jpa` — Entity tests, Hibernate 7, `@DataJpaTest` patterns
- `common-rest-api` — Controller tests, OpenAPI, contract testing
- `common-security` — Authentication, authorisation, security tests
