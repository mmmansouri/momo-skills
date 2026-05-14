# Java Language Pitfalls & Anti-Patterns

> Language-level pitfalls — `Optional`, Streams, Records, and general Java anti-patterns.
> Runtime / concurrency / framework pitfalls live in [pitfalls-runtime.md](pitfalls-runtime.md).

---

## Table of Contents

1. [Quick Fix Reference](#quick-fix-reference)
2. [Optional Misuse](#optional-misuse)
3. [Stream Pitfalls](#stream-pitfalls)
4. [Record Limitations](#record-limitations)
5. [General Java Anti-Patterns](#general-java-anti-patterns)

---

## Quick Fix Reference

| Anti-Pattern | How to Fix |
|--------------|------------|
| `orElse(method())` | Use `orElseGet(() -> method())` for lazy eval |
| `isPresent() + get()` | Use `map().orElse()` chain |
| Mutable state in streams | Use `collect()` to new collection |
| Reusing consumed stream | Create new stream each time |
| Parallel stream for I/O | Use virtual threads instead |
| `synchronized` + blocking I/O (Java 21–23 only) | Use `ReentrantLock`. Java 24+ removes pinning (JEP 491). |
| ThreadLocal in pools | Call `remove()` in finally |
| Empty catch block | Log and rethrow wrapped exception |
| Swallowing `InterruptedException` | Restore interrupt + rethrow |
| Unbounded static cache | Use Caffeine with max size |
| Non-static inner class | Make static or use lambda |

### Related References

- **Security anti-patterns**: See [security.md](security.md) for password hashing, encryption, and SQL injection
- **Testing anti-patterns**: See [testing.md](testing.md) for shared test state and mocking rules
- **Concurrency guidance**: See [concurrency.md](concurrency.md) for virtual thread patterns

---

## Optional Misuse

### 🔴 orElse vs orElseGet

```java
// ❌ WRONG - fetchDefault() ALWAYS called even if value present
Optional<User> user = Optional.of(currentUser);
user.orElse(fetchDefault());  // fetchDefault() executed unnecessarily!

// ✅ CORRECT - lazy evaluation
user.orElseGet(() -> fetchDefault());  // Only called if empty

// ✅ OK for simple values
user.orElse(null);           // No method call
user.orElse(DEFAULT_USER);   // Constant
```

### 🔴 isPresent + get Anti-Pattern

```java
// ❌ WRONG - verbose and error-prone
if (optional.isPresent()) {
    User user = optional.get();
    return user.getName();
} else {
    return "Unknown";
}

// ✅ CORRECT - functional style
return optional
    .map(User::getName)
    .orElse("Unknown");
```

### 🟡 Optional as Field or Parameter

```java
// ❌ WRONG - Optional as field
public class User {
    private Optional<String> nickname;  // Don't do this
}

// ✅ CORRECT - nullable field with Optional accessor
public class User {
    private String nickname;  // Can be null

    public Optional<String> getNickname() {
        return Optional.ofNullable(nickname);
    }
}

// ❌ WRONG - Optional as parameter
void processUser(Optional<User> user) { }

// ✅ CORRECT - overloaded methods or nullable
void processUser(User user) { }
void processUser() { processUser(defaultUser); }
```

### 🟡 Wrapping Non-Null Values

```java
// ❌ WRONG - pointless wrapping
return Optional.of(computeValue());  // If computeValue() never returns null

// ✅ CORRECT - return directly
return computeValue();

// Use Optional.of() only when value might be null
return Optional.ofNullable(possiblyNullValue);
```

---

## Stream Pitfalls

### 🔴 Reusing Streams

```java
// ❌ WRONG - streams can only be consumed once
Stream<String> stream = list.stream();
long count = stream.count();
List<String> result = stream.toList();  // IllegalStateException!

// ✅ CORRECT - create new stream for each operation
long count = list.stream().count();
List<String> result = list.stream().toList();
```

### 🔴 Mutable State in Streams

```java
// ❌ WRONG - race condition in parallel
List<String> results = new ArrayList<>();
stream.parallel().forEach(item -> results.add(item));

// ✅ CORRECT - collect to a new list
List<String> results = stream.parallel().toList();

// ✅ Or use thread-safe collection (slower)
List<String> results = Collections.synchronizedList(new ArrayList<>());
stream.parallel().forEach(item -> results.add(item));
```

### 🟡 Parallel Stream on Wrong Data Source

```java
// ❌ WRONG - LinkedList has O(n) split cost
LinkedList<Item> items = getItems();
items.parallelStream().map(this::process).toList();

// ✅ CORRECT - ArrayList has O(1) split
ArrayList<Item> items = new ArrayList<>(getItems());
items.parallelStream().map(this::process).toList();

// Best sources for parallel:
// - ArrayList, arrays
// - IntStream.range(), LongStream.range()
// - HashSet (moderate)
```

### 🔴 Parallel Stream for I/O

```java
// ❌ WRONG - blocks shared ForkJoinPool
items.parallelStream().forEach(item -> {
    database.save(item);  // Blocking I/O
});

// ✅ CORRECT - use virtual threads for I/O
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    items.forEach(item -> executor.submit(() -> database.save(item)));
}
```

### 🟡 peek() for Side Effects

```java
// ❌ WRONG - peek is for debugging, not side effects
stream.peek(item -> item.setProcessed(true))  // Mutation!
      .toList();

// ✅ CORRECT - use map for transformation
stream.map(item -> item.withProcessed(true))
      .toList();

// peek is OK for debugging
stream.peek(item -> log.debug("Processing: {}", item))
      .filter(...)
      .toList();
```

---

## Record Limitations

### 🟢 Records Are Final

```java
// ❌ WRONG - cannot extend records
public record BasePoint(int x, int y) {}
public record Point3D(int x, int y, int z) extends BasePoint {} // Compile error!

// ✅ CORRECT - use composition or interfaces
public interface Point {
    int x();
    int y();
}
public record Point2D(int x, int y) implements Point {}
public record Point3D(int x, int y, int z) implements Point {}
```

### 🟢 Records Are Immutable

```java
// ❌ WRONG - no setters
public record User(String name) {
    public void setName(String name) { }  // Cannot modify
}

// ✅ CORRECT - create new instance (wither pattern)
public record User(String name) {
    public User withName(String newName) {
        return new User(newName);
    }
}
```

### 🔴 Mutable Components in Records

```java
// ⚠️ DANGER - list can be modified externally
public record Container(List<String> items) {}

Container c = new Container(Arrays.asList("a", "b"));
c.items().add("c");  // Modifies the list!

// ✅ CORRECT - defensive copy
public record Container(List<String> items) {
    public Container {
        items = List.copyOf(items);  // Immutable copy
    }
}
```

---

## General Java Anti-Patterns

### 🔴 Catching Generic Exceptions

```java
// ❌ WRONG - catches everything including RuntimeException
try {
    doSomething();
} catch (Exception e) {
    log.error("Error", e);
}

// ✅ CORRECT - catch specific exceptions
try {
    doSomething();
} catch (IOException e) {
    handleIoError(e);
} catch (SQLException e) {
    handleDbError(e);
}
```

### 🔴 Swallowing Exceptions

```java
// ❌ WRONG - silent failure
try {
    doSomething();
} catch (Exception e) {
    // Empty catch block
}

// ❌ WRONG - logging but ignoring
try {
    doSomething();
} catch (Exception e) {
    log.error("Error", e);
    // Method continues as if nothing happened
}

// ✅ CORRECT - handle or rethrow
try {
    doSomething();
} catch (IOException e) {
    throw new ServiceException("Operation failed", e);
}
```

### 🟡 Ignoring InterruptedException

```java
// ❌ WRONG - swallowing interrupt status
try {
    Thread.sleep(1000);
} catch (InterruptedException e) {
    // Ignore
}

// ✅ CORRECT - restore interrupt status
try {
    Thread.sleep(1000);
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw new RuntimeException("Interrupted", e);
}
```

### 🔴 Using Raw Types

```java
// ❌ WRONG - raw type
List items = new ArrayList();
items.add("string");
items.add(123);  // No compile error!

// ✅ CORRECT - parameterized type
List<String> items = new ArrayList<>();
items.add("string");
items.add(123);  // Compile error!
```

### 🟡 Mutable Static Fields

```java
// ❌ WRONG - shared mutable state
public class Config {
    public static Map<String, String> settings = new HashMap<>();
}

// ✅ CORRECT - immutable or properly encapsulated
public class Config {
    private static final Map<String, String> settings =
        Map.of("key1", "value1", "key2", "value2");

    public static String get(String key) {
        return settings.get(key);
    }
}
```
