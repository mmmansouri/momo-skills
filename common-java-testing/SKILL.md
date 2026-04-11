---
name: common-java-testing
description: >-
  Java testing best practices with JUnit 5, Mockito, and AssertJ. Use when:
  writing unit/integration tests, deciding what to mock (external services only),
  structuring tests (Given-When-Then), using fluent assertions, or applying
  test isolation patterns.
---

# Java Testing Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Testing Philosophy

### 🔴 No-Mock Philosophy

```
PREFER: Integration tests with real objects wired together
MOCK:   External services only (HTTP, email, payment, filesystem)
NEVER:  Internal classes, repositories, value objects
```

**Why?** Mocks can hide integration bugs. If everything is mocked, are we really testing production code?

### 🔴 Test Isolation

- Each test creates its own data → No shared mutable state
- Use `@BeforeEach` for test-specific setup
- Never depend on execution order
- Use UUID suffix for unique identifiers

### 🟢 Fixed Test Data

```java
// 🔴 WRONG - Random data makes failures hard to reproduce
String name = "User_" + UUID.randomUUID();

// ✅ CORRECT - Fixed values, reproducible
String name = "TestUser_ValidCase";
```

---

## When Structuring Tests

📚 **References:** [test-structure.md](references/test-structure.md)

### 🔴 Given-When-Then Pattern

```java
@Test
void whenValidInput_shouldReturnExpectedResult() {
    // Given - setup test data
    var request = new OrderRequest("item-1", 2);

    // When - execute action
    var result = orderService.create(request);

    // Then - assert results
    assertThat(result.getStatus()).isEqualTo(OrderStatus.CREATED);
}
```

### 🔴 Naming Convention

| Pattern | Example |
|---------|---------|
| `when<Condition>_should<Result>` | `whenInvalidId_shouldReturn404` |
| `@DisplayName` | `"Should return 404 when ID not found"` |

### 🟡 WARNING

- **One test = one behavior** → Don't extend passing tests with "just one more thing"
- **KISS > DRY** → Duplicating test data is acceptable for clarity

---

## When Using JUnit 5

📚 **References:** [junit5.md](references/junit5.md)

### 🟢 Key Annotations

| Annotation | Use Case |
|------------|----------|
| `@Nested` | Group related tests by method/scenario |
| `@DisplayName` | Readable test names for reports |
| `@ParameterizedTest` | Test multiple inputs |
| `@BeforeEach` | Fresh state per test |

### 🟢 Exception Testing

```java
// ✅ CORRECT - assertThrows
@Test
void whenNullInput_shouldThrowException() {
    assertThrows(IllegalArgumentException.class,
        () -> service.process(null));
}

// With message verification
var ex = assertThrows(OrderNotFoundException.class,
    () -> service.findById(invalidId));
assertThat(ex.getMessage()).contains(invalidId.toString());
```

### 🟢 Grouped Assertions

```java
// All assertions run, report all failures
assertAll("order validation",
    () -> assertThat(order.getId()).isNotNull(),
    () -> assertThat(order.getStatus()).isEqualTo(CREATED),
    () -> assertThat(order.getItems()).hasSize(2)
);
```

---

## When Using Mockito

📚 **References:** [mockito.md](references/mockito.md)

### 🔴 What NOT to Mock

| Type | Why Not |
|------|---------|
| **Internal classes** | Test real integration |
| **Repositories** | Use `@DataJpaTest` or Testcontainers |
| **Value objects/DTOs** | Just create them with `new` |
| **Types you don't own** | Third-party libs may change |

### 🟢 What TO Mock

| Type | Tool |
|------|------|
| HTTP clients | WireMock, MockWebServer |
| Email services | Mock the gateway interface |
| Payment APIs | Mock the client interface |
| Clock/Time | Inject `Clock` dependency |

### 🟡 Mockito Guidelines

```java
// 🔴 WRONG - Mocking internal service
@Mock private OrderRepository orderRepository;

// ✅ CORRECT - Mock external HTTP client
@Mock private StripeClient stripeClient;

// 🔴 WRONG - any() loses specificity
when(service.process(any())).thenReturn(result);

// ✅ CORRECT - Specific values
when(service.process(eq(expectedInput))).thenReturn(result);
```

---

## When Using AssertJ

📚 **References:** [assertj.md](references/assertj.md)

### 🔴 Always Use AssertJ

```java
// 🔴 WRONG - JUnit assertions (poor error messages)
assertEquals(expected, actual);
assertTrue(list.contains(item));

// ✅ CORRECT - AssertJ (fluent, descriptive errors)
assertThat(actual).isEqualTo(expected);
assertThat(list).contains(item);
```

### 🟢 Key Patterns

| Need | AssertJ Method |
|------|----------------|
| Null check | `isNull()`, `isNotNull()` |
| Collections | `contains()`, `containsExactly()`, `hasSize()` |
| Strings | `startsWith()`, `contains()`, `matches()` |
| Optional | `isPresent()`, `isEmpty()`, `hasValue()` |
| Numbers | `isGreaterThan()`, `isBetween()`, `isCloseTo()` |

### 🟢 Advanced Patterns

```java
// Extract specific fields
assertThat(users)
    .extracting(User::getName, User::getEmail)
    .contains(tuple("John", "john@example.com"));

// Recursive comparison (ignore fields)
assertThat(actual)
    .usingRecursiveComparison()
    .ignoringFields("id", "createdAt")
    .isEqualTo(expected);

// Exception assertions
assertThatThrownBy(() -> service.process(null))
    .isInstanceOf(IllegalArgumentException.class)
    .hasMessageContaining("must not be null");
```

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] No mocking of internal classes (services, repos)
- [ ] No shared mutable state between tests
- [ ] Each test creates its own data
- [ ] Using `assertThat()` not `assertEquals()`
- [ ] No `Thread.sleep()` → Use Awaitility

### 🟡 WARNING
- [ ] Test names describe behavior, not implementation
- [ ] No production logic duplicated in tests
- [ ] No duplicate test scenarios across test levels (unit/integration/E2E)
- [ ] Prefer specific values over `any()` in mocks

### 🟢 BEST PRACTICE
- [ ] Given-When-Then structure with blank lines
- [ ] `@Nested` for grouping related tests
- [ ] `@ParameterizedTest` for multiple scenarios
- [ ] `extracting()` for specific field assertions
- [ ] `SoftAssertions` for multiple independent checks

---

## Project-Specific Testing Patterns

> **CRITICAL:** This skill provides GENERIC Java testing guidance. For **Buy Nature project-specific** conventions (base test classes, naming rules, mock boundaries), always consult `buy-nature-backend-coding-guide` → "When Writing Tests" section.

Key project-specific rules NOT covered here:
- `AbstractBuyNatureTest` base class (all integration tests must extend it)
- `XxxControllerE2ETest` naming convention (controller tests are integration tests)
- Only `StripeService` and SMTP are mocked via `@MockitoBean` (everything else is real)

---

## Related Skills

- `common-java-developer` — Modern Java test patterns
- `common-java-jpa` — Testing JPA repositories and entities
- `common-rest-api` — Testing REST controllers with @WebMvcTest
- `common-security` — Testing authentication and authorization
- `buy-nature-backend-coding-guide` — **Buy Nature testing conventions (AbstractBuyNatureTest, E2ETest naming, mock boundaries)**
