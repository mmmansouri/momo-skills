# Modern Java Features (Java 8-25)

## Java 8 (2014) - Foundation of Modern Java

### Lambda Expressions
```java
// Before
list.forEach(new Consumer<String>() {
    @Override
    public void accept(String s) { System.out.println(s); }
});

// After
list.forEach(s -> System.out.println(s));
list.forEach(System.out::println); // Method reference
```

### Stream API
```java
List<String> filtered = items.stream()
    .filter(item -> item.getPrice() > 100)
    .map(Item::getName)
    .sorted()
    .collect(Collectors.toList());
```

### Optional
```java
Optional<User> user = repository.findById(id);
String name = user.map(User::getName).orElse("Unknown");
```

### java.time Package
```java
LocalDate today = LocalDate.now();
LocalDateTime timestamp = LocalDateTime.now();
ZonedDateTime zoned = ZonedDateTime.now(ZoneId.of("Europe/Paris"));
Duration duration = Duration.between(start, end);
```

### Default Methods in Interfaces
```java
public interface Validator {
    boolean validate(String input);

    default boolean validateAndLog(String input) {
        boolean result = validate(input);
        log(result);
        return result;
    }
}
```

---

## Java 9 (2017)

### Factory Methods for Collections
```java
List<String> list = List.of("a", "b", "c");           // Immutable
Set<Integer> set = Set.of(1, 2, 3);                   // Immutable
Map<String, Integer> map = Map.of("a", 1, "b", 2);    // Immutable
```

### Stream Enhancements
```java
// takeWhile - stop when predicate fails
Stream.of(1, 2, 3, 4, 5).takeWhile(n -> n < 4);  // 1, 2, 3

// dropWhile - skip until predicate fails
Stream.of(1, 2, 3, 4, 5).dropWhile(n -> n < 4);  // 4, 5

// ofNullable - create stream from nullable
Stream.ofNullable(nullableValue);
```

### Optional Enhancements
```java
optional.ifPresentOrElse(
    value -> process(value),
    () -> handleEmpty()
);

optional.or(() -> Optional.of(defaultValue));
optional.stream();  // Convert to stream
```

---

## Java 10 (2018)

### Local Variable Type Inference (var)
```java
var list = new ArrayList<String>();  // Inferred as ArrayList<String>
var stream = list.stream();          // Inferred as Stream<String>
var map = Map.of("key", "value");    // Inferred as Map<String, String>

// When to use var:
// ✅ Type is obvious from right side
// ✅ Reduces verbosity with generics
// ❌ Type is not clear from context
// ❌ Primitive types (use explicit int, long, etc.)
```

---

## Java 11 (2018) - LTS

### var in Lambda Parameters
```java
list.forEach((var item) -> process(item));
// Useful for adding annotations
list.forEach((@NonNull var item) -> process(item));
```

### String Methods
```java
"  hello  ".strip();        // "hello" (Unicode-aware)
"  hello  ".stripLeading(); // "hello  "
"  hello  ".stripTrailing();// "  hello"
"".isBlank();               // true
"hello\nworld".lines();     // Stream of lines
"abc".repeat(3);            // "abcabcabc"
```

### Files.readString / writeString
```java
String content = Files.readString(Path.of("file.txt"));
Files.writeString(Path.of("output.txt"), content);
```

---

## Java 14-16 (2020-2021)

### Records (Java 16)
```java
public record Point(int x, int y) {
    // Compact constructor for validation
    public Point {
        if (x < 0 || y < 0) throw new IllegalArgumentException();
    }

    // Additional methods allowed
    public double distance() {
        return Math.sqrt(x * x + y * y);
    }
}
```

### Pattern Matching for instanceof (Java 16)
```java
// Before
if (obj instanceof String) {
    String s = (String) obj;
    return s.length();
}

// After
if (obj instanceof String s) {
    return s.length();
}
```

---

## Java 17 (2021) - LTS

### Sealed Classes
```java
public sealed interface Shape permits Circle, Rectangle, Triangle {}

public final class Circle implements Shape { }
public final class Rectangle implements Shape { }
public non-sealed class Triangle implements Shape { } // Can be extended
```

### Text Blocks
```java
String json = """
    {
        "name": "%s",
        "price": %.2f
    }
    """.formatted(name, price);

String sql = """
    SELECT *
    FROM users
    WHERE status = 'ACTIVE'
    ORDER BY created_at DESC
    """;
```

---

## Java 21 (2023) - LTS

### Virtual Threads
```java
// Create virtual thread
Thread.startVirtualThread(() -> handleRequest());

// Using executor
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    executor.submit(() -> blockingOperation());
}
```

### Record Patterns
```java
// Deconstruct records in patterns
if (obj instanceof Point(int x, int y)) {
    return x + y;
}

// Nested deconstruction
switch (shape) {
    case Circle(Point(var x, var y), var r) -> area(r);
    case Rectangle(Point p1, Point p2) -> area(p1, p2);
}
```

### Pattern Matching for switch
```java
return switch (obj) {
    case Integer i -> "Integer: " + i;
    case String s -> "String: " + s;
    case null -> "null";
    default -> "Unknown";
};
```

### Sequenced Collections
```java
SequencedCollection<String> list = new ArrayList<>();
list.addFirst("first");
list.addLast("last");
String first = list.getFirst();
String last = list.getLast();
List<String> reversed = list.reversed();
```

---

## Java 22-25 (2024-2025)

### Stream Gatherers (Java 24)
```java
// Window fixed - batch processing
List<List<Integer>> batches = numbers.stream()
    .gather(Gatherers.windowFixed(10))
    .toList();

// Window sliding
List<List<Integer>> windows = numbers.stream()
    .gather(Gatherers.windowSliding(3))
    .toList();
```

### Scoped Values (Java 25)
```java
// Replacement for ThreadLocal - better for virtual threads
private static final ScopedValue<User> CURRENT_USER = ScopedValue.newInstance();

ScopedValue.where(CURRENT_USER, user).run(() -> {
    // User available in this scope and child scopes
    User u = CURRENT_USER.get();
});
```

### Primitive Types in Patterns (Java 25)
```java
switch (value) {
    case int i when i > 0 -> "positive";
    case int i when i < 0 -> "negative";
    case int _ -> "zero";
}
```

### Unnamed Variables (Java 22)
```java
try { return parse(input); }
catch (Exception _) { return defaultValue; }  // Ignore exception

map.forEach((_, value) -> process(value));  // Ignore key

case Point(int x, _) -> x;  // Ignore y coordinate
```
