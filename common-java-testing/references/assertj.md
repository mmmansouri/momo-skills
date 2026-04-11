# AssertJ Reference

## Why AssertJ?

```java
// 🔴 JUnit - Cryptic error message
assertEquals(expected, actual);
// Error: expected:<[foo]> but was:<[bar]>

// ✅ AssertJ - Descriptive error message
assertThat(actual).isEqualTo(expected);
// Error: Expecting: <"bar"> to be equal to: <"foo"> but was not.
```

---

## Basic Assertions

### Objects

```java
assertThat(result).isNotNull();
assertThat(result).isNull();
assertThat(result).isEqualTo(expected);
assertThat(result).isNotEqualTo(other);
assertThat(result).isSameAs(sameInstance);  // Same reference
assertThat(result).isInstanceOf(Order.class);
```

### Booleans

```java
assertThat(result).isTrue();
assertThat(result).isFalse();
```

### Numbers

```java
assertThat(count).isEqualTo(5);
assertThat(count).isGreaterThan(0);
assertThat(count).isLessThanOrEqualTo(100);
assertThat(count).isBetween(1, 10);
assertThat(count).isPositive();
assertThat(count).isNegative();
assertThat(count).isZero();

// BigDecimal comparison
assertThat(price).isEqualByComparingTo(new BigDecimal("99.99"));
assertThat(price).isCloseTo(new BigDecimal("100"), within(new BigDecimal("0.01")));
```

---

## Strings

```java
assertThat(name).isEqualTo("John");
assertThat(name).isEqualToIgnoringCase("JOHN");
assertThat(name).startsWith("Jo");
assertThat(name).endsWith("hn");
assertThat(name).contains("oh");
assertThat(name).doesNotContain("xyz");
assertThat(name).matches("[A-Z][a-z]+");
assertThat(name).isNotBlank();
assertThat(name).isNotEmpty();
assertThat(name).hasSize(4);

// Multiple conditions
assertThat(email)
    .isNotBlank()
    .contains("@")
    .endsWith(".com");
```

---

## Collections

### Basic

```java
assertThat(list).isEmpty();
assertThat(list).isNotEmpty();
assertThat(list).hasSize(3);
assertThat(list).hasSizeGreaterThan(2);
assertThat(list).contains("item1", "item2");
assertThat(list).containsExactly("item1", "item2", "item3");  // Order matters
assertThat(list).containsExactlyInAnyOrder("item3", "item1", "item2");
assertThat(list).containsOnly("item1", "item2");  // Only these, any order
assertThat(list).doesNotContain("invalid");
assertThat(list).containsNull();
assertThat(list).doesNotContainNull();
```

### First/Last Elements

```java
assertThat(list).first().isEqualTo("first");
assertThat(list).last().isEqualTo("last");
assertThat(list).element(2).isEqualTo("third");
```

### Filtering

```java
assertThat(users)
    .filteredOn(user -> user.getAge() > 18)
    .hasSize(5);

assertThat(users)
    .filteredOn("status", UserStatus.ACTIVE)
    .hasSize(10);
```

---

## Extracting Fields

### Single Field

```java
assertThat(users)
    .extracting(User::getName)
    .contains("John", "Jane", "Bob");

assertThat(users)
    .extracting("name")  // By field name
    .contains("John", "Jane");
```

### Multiple Fields

```java
assertThat(users)
    .extracting(User::getName, User::getEmail)
    .contains(
        tuple("John", "john@example.com"),
        tuple("Jane", "jane@example.com")
    );
```

### Nested Fields

```java
assertThat(orders)
    .extracting("customer.name")
    .contains("John", "Jane");

assertThat(orders)
    .flatExtracting(Order::getItems)
    .hasSize(10);
```

---

## Optional

```java
Optional<User> result = service.findById(id);

assertThat(result).isPresent();
assertThat(result).isEmpty();
assertThat(result).hasValue(expectedUser);
assertThat(result).hasValueSatisfying(user -> {
    assertThat(user.getName()).isEqualTo("John");
    assertThat(user.getEmail()).contains("@");
});

// Get and continue asserting
assertThat(result)
    .isPresent()
    .get()
    .extracting(User::getName)
    .isEqualTo("John");
```

---

## Exceptions

### assertThatThrownBy

```java
assertThatThrownBy(() -> service.findById(null))
    .isInstanceOf(IllegalArgumentException.class)
    .hasMessage("ID must not be null")
    .hasMessageContaining("must not be null");

assertThatThrownBy(() -> service.process(invalidData))
    .isInstanceOf(ValidationException.class)
    .hasMessageStartingWith("Invalid")
    .hasCauseInstanceOf(IllegalStateException.class);
```

### assertThatCode (No Exception)

```java
assertThatCode(() -> service.process(validData))
    .doesNotThrowAnyException();
```

### Specific Exception Types

```java
assertThatIllegalArgumentException()
    .isThrownBy(() -> service.process(null))
    .withMessage("Input required");

assertThatNullPointerException()
    .isThrownBy(() -> service.process(null));

assertThatIOException()
    .isThrownBy(() -> fileService.read(invalidPath));
```

---

## Recursive Comparison

### Compare DTOs/Entities

```java
// Compare all fields recursively
assertThat(actual)
    .usingRecursiveComparison()
    .isEqualTo(expected);

// Ignore specific fields
assertThat(actual)
    .usingRecursiveComparison()
    .ignoringFields("id", "createdAt", "updatedAt")
    .isEqualTo(expected);

// Ignore fields by type
assertThat(actual)
    .usingRecursiveComparison()
    .ignoringFieldsOfTypes(Instant.class, UUID.class)
    .isEqualTo(expected);

// Custom comparator for specific fields
assertThat(actual)
    .usingRecursiveComparison()
    .withComparatorForFields(
        (a, b) -> a.toLowerCase().equals(b.toLowerCase()),
        "name", "email"
    )
    .isEqualTo(expected);
```

---

## Soft Assertions

### Collect All Failures

```java
// 🔴 WRONG - Stops at first failure
assertThat(user.getName()).isEqualTo("John");
assertThat(user.getEmail()).isEqualTo("john@example.com");
assertThat(user.getAge()).isEqualTo(30);
// If first fails, you don't know about others

// ✅ CORRECT - Reports ALL failures
SoftAssertions.assertSoftly(softly -> {
    softly.assertThat(user.getName()).isEqualTo("John");
    softly.assertThat(user.getEmail()).isEqualTo("john@example.com");
    softly.assertThat(user.getAge()).isEqualTo(30);
});
```

### With AutoCloseable

```java
try (AutoCloseableSoftAssertions softly = new AutoCloseableSoftAssertions()) {
    softly.assertThat(user.getName()).isEqualTo("John");
    softly.assertThat(user.getEmail()).contains("@");
}  // Assertions verified here
```

### JUnit 5 Extension

```java
@ExtendWith(SoftAssertionsExtension.class)
class UserTest {

    @InjectSoftAssertions
    private SoftAssertions softly;

    @Test
    void shouldHaveCorrectFields() {
        softly.assertThat(user.getName()).isEqualTo("John");
        softly.assertThat(user.getEmail()).contains("@");
        // Automatically verified after test
    }
}
```

---

## Custom Assertions

### For Domain Objects

```java
public class OrderAssert extends AbstractAssert<OrderAssert, Order> {

    public OrderAssert(Order actual) {
        super(actual, OrderAssert.class);
    }

    public static OrderAssert assertThat(Order actual) {
        return new OrderAssert(actual);
    }

    public OrderAssert hasTotalGreaterThan(BigDecimal amount) {
        isNotNull();
        if (actual.getTotal().compareTo(amount) <= 0) {
            failWithMessage("Expected order total to be greater than %s but was %s",
                amount, actual.getTotal());
        }
        return this;
    }

    public OrderAssert isPending() {
        isNotNull();
        if (actual.getStatus() != OrderStatus.PENDING) {
            failWithMessage("Expected order to be PENDING but was %s",
                actual.getStatus());
        }
        return this;
    }
}

// Usage
assertThat(order)
    .isPending()
    .hasTotalGreaterThan(BigDecimal.ZERO);
```

---

## Chaining Assertions

```java
assertThat(order)
    .isNotNull()
    .extracting(Order::getStatus, Order::getTotal)
    .containsExactly(OrderStatus.PENDING, new BigDecimal("99.99"));

assertThat(users)
    .isNotEmpty()
    .hasSize(3)
    .extracting(User::getName)
    .containsExactlyInAnyOrder("John", "Jane", "Bob");
```

---

## Date/Time Assertions

```java
assertThat(instant).isBefore(Instant.now());
assertThat(instant).isAfter(startTime);
assertThat(instant).isBetween(startTime, endTime);

assertThat(localDate).isToday();
assertThat(localDate).isInThePast();
assertThat(localDate).isInTheFuture();

// With tolerance
assertThat(actual)
    .isCloseTo(expected, within(1, ChronoUnit.SECONDS));
```

---

## File Assertions

```java
assertThat(file).exists();
assertThat(file).doesNotExist();
assertThat(file).isFile();
assertThat(file).isDirectory();
assertThat(file).hasName("config.json");
assertThat(file).hasExtension("json");
assertThat(file).hasContent("expected content");
```
