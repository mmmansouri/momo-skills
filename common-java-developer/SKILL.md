---
name: common-java-developer
description: >-
  Modern Java development guide (Java 17-25 focus, compatible with 8-16). Use for any Java
  backend development. Contains modern features (records, pattern matching, sealed classes,
  virtual threads), Stream API, Optional patterns, design patterns (Builder, Factory, Strategy),
  performance optimization, and critical pitfalls. For Java 8-16 projects, note that many
  features require Java 17+. Required for all Java development agents.
---

# Java Developer Guide (Java 8-25)

> **Severity Levels:** 🔴 BLOCKING (fails code review) | 🟡 WARNING (should fix) | 🟢 BEST PRACTICE (recommended)

---

## When Writing New Code

📚 **References:** [pattern-matching.md](references/pattern-matching.md) | [modern-features.md](references/modern-features.md)

### 🟢 Data Structures
| Need | Use | Not |
|------|-----|-----|
| Data carrier class | ✅ **Record** | ❌ Mutable POJO |
| Closed type hierarchy | ✅ **Sealed interface** | ❌ Open interface |
| Immutable collection | ✅ `List.of()`, `Set.of()` | ❌ `new ArrayList<>()` |
| Null-safe return | ✅ `Optional<T>` | ❌ `return null` |

### 🟢 Code Style
| Need | Use | Not |
|------|-----|-----|
| Multi-line string | ✅ **Text block** `"""..."""` | ❌ Concatenation |
| Type check + extract | ✅ **Pattern matching** `instanceof` | ❌ `instanceof` + cast |
| Multi-branch logic | ✅ **Switch expression** | ❌ if-else chains |
| Local variable | ✅ `var` (when type obvious) | ❌ Verbose declarations |

### 🟡 WARNING
- **Deprecated APIs** → Don't use `finalize()`, `Thread.stop()`, Security Manager

---

## When Refactoring Legacy Code

📚 **References:** [modern-features.md](references/modern-features.md)

| Legacy Pattern | Modern Replacement |
|---------------|-------------------|
| `instanceof` + manual cast | Pattern matching `if (obj instanceof String s)` |
| if-else type chains | Pattern matching `switch` |
| Mutable DTO class | Record |
| Anonymous inner class (single method) | Lambda expression |
| String concatenation in loops | `StringBuilder` or `Collectors.joining()` |
| `ThreadLocal` | Scoped Values (FINAL in Java 25, JEP 506) |
| Thread pools for blocking I/O | Virtual threads |
| `new ArrayList<>()` (never modified) | `List.of()` |
| Validation thrown from a private static helper called by the constructor | Statements before `super(...)` (Flexible Constructor Bodies — JEP 513) |
| Hand-rolled HKDF over `Mac` + `MessageDigest` | `javax.crypto.KDF` (JEP 510) |
| Long `import` blocks in scripts/snippets | `import module java.base;` (JEP 511) |

### ⚠️ When NOT to Modernize
Leave stable code alone when:
- Well-tested production code with good coverage
- Performance-critical tight loops (streams add overhead)
- Simple loops are clearer than functional equivalent
- Team unfamiliar with new features

**Tools:** `jdeps --jdk-internals`, `jdeprscan`, OpenRewrite

---

## When Handling Exceptions

📚 **References:** [pitfalls-antipatterns.md](references/pitfalls-antipatterns.md#general-java-anti-patterns)

### 🔴 BLOCKING
- **Never catch generic `Exception`/`Throwable`** → Catch specific types
- **Never leave catch blocks empty** → Log or rethrow

### 🟢 BEST PRACTICE
- **Use checked exceptions** for recoverable conditions (I/O, network, database)
- **Use unchecked exceptions** for programming errors (null, invalid args)
- **Always chain exceptions** to preserve root cause

```java
// 🔴 WRONG - generic catch
catch (Exception e) { }

// 🔴 WRONG - empty catch
catch (IOException e) { }

// ✅ CORRECT - specific + chained
catch (SQLException e) {
    throw new DataAccessException("Failed to fetch user", e);
}
```

### 🟡 WARNING
- **Catch-and-rethrow hides exceptions from retry frameworks** → If Resilience4j `@Retry` is configured for `MailException` but you catch and wrap it as `EmailSendingException`, retry never triggers. Let retriable exceptions propagate. See `common-rest-api/references/spring-boot-config-pitfalls.md`

---

## When Creating Immutable Objects

📚 **References:** [pitfalls-antipatterns.md](references/pitfalls-antipatterns.md#record-limitations)

### 🔴 BLOCKING
- **Mutable fields in records without defensive copy** → Use `List.copyOf()`

```java
// 🔴 WRONG - list can be modified externally
public record Team(String name, List<String> members) {}

// ✅ CORRECT - defensive copy
public record Team(String name, List<String> members) {
    public Team {
        Objects.requireNonNull(name);
        members = List.copyOf(members);  // True immutable copy!
    }
}
```

### 🟢 BEST PRACTICE
- **Validate early** with `Objects.requireNonNull()`
- **Use `List.copyOf()`** not `Collections.unmodifiableList()`

```java
// ⚠️ unmodifiableList is a VIEW, not a copy!
List<String> original = new ArrayList<>();
List<String> unmodifiable = Collections.unmodifiableList(original);
original.add("item");  // unmodifiable NOW CONTAINS "item"!

List<String> copy = List.copyOf(original);  // True copy - unaffected
```

---

## When Using Streams

📚 **References:** [streams-functional.md](references/streams-functional.md) | [pitfalls-antipatterns.md](references/pitfalls-antipatterns.md#stream-pitfalls)

### 🔴 BLOCKING
- **Mutate shared state in streams** → Use `collect()` to new structure
- **Reuse a consumed stream** → Create new stream each time

```java
// 🔴 WRONG - mutating external state
List<String> results = new ArrayList<>();
stream.forEach(s -> results.add(s.toUpperCase()));  // Race condition in parallel!

// ✅ CORRECT
List<String> results = stream.map(String::toUpperCase).toList();

// 🔴 WRONG - stream already consumed
Stream<String> stream = names.stream();
stream.forEach(System.out::println);
stream.count();  // IllegalStateException!
```

### 🟡 WARNING
- **Infinite streams without `limit()` or `takeWhile()`** → May hang indefinitely

### 🟢 BEST PRACTICE
- Use `collect()` to gather results
- Use sequential streams by default
- Use `ArrayList` or arrays as parallel stream source (not `LinkedList`)

**Parallel Stream Decision:** N × Q > 10,000
- **N** = number of elements
- **Q** = cost per element
- Below threshold → use sequential (overhead > benefit)

---

## When Using Optional

📚 **References:** [streams-functional.md](references/streams-functional.md) | [pitfalls-antipatterns.md](references/pitfalls-antipatterns.md#optional-misuse)

### 🔴 BLOCKING
- **`orElse(method())`** → Use `orElseGet(() -> method())` for lazy evaluation
- **`isPresent()` + `get()`** → Use `map().orElse()` chain
- **`Optional.get()` directly** → Use `orElseThrow()`

```java
// 🔴 WRONG - expensiveMethod() ALWAYS called even if value present
optional.orElse(expensiveMethod());

// ✅ CORRECT - lazy evaluation
optional.orElseGet(() -> expensiveMethod());

// 🔴 WRONG - verbose and error-prone
if (optional.isPresent()) { return optional.get(); }

// ✅ CORRECT - functional style
optional.map(User::getName).orElse("Unknown");
optional.orElseThrow(() -> new NotFoundException(id));
```

### 🟡 WARNING
- **Optional as method parameter** → Use method overloading instead
- **Optional as class field** → Use nullable field + Optional getter
- **Optional in collections** → Filter out nulls instead

---

## When Using Concurrency

📚 **References:** [concurrency.md](references/concurrency.md)

### 🔴 BLOCKING
- **Pool virtual threads** → Create new virtual thread per task

```java
// 🔴 WRONG - defeats the purpose of virtual threads
ExecutorService pool = Executors.newFixedThreadPool(100);

// ✅ CORRECT - one virtual thread per task
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    tasks.forEach(task -> executor.submit(task));
}
```

### 🟡 WARNING
- **`synchronized` with blocking I/O in virtual threads (Java 21–23 only)** → Pins carrier thread, use `ReentrantLock`. **Java 24+ (JEP 491) removes this pinning** — rule still applies to code targeting Java 21–23.
- **`ThreadLocal` with virtual threads** → May accumulate memory, use Scoped Values (FINAL in Java 25, JEP 506)

```java
// 🟡 WARNING on Java 21–23 - pins carrier thread (no longer pins on Java 24+)
synchronized (lock) {
    socket.read();  // Blocking I/O inside synchronized
}

// ✅ CORRECT (version-agnostic) - ReentrantLock never pins
private final ReentrantLock lock = new ReentrantLock();
lock.lock();
try { socket.read(); }
finally { lock.unlock(); }
```

### 🟢 When to Use What
| Scenario | Use |
|----------|-----|
| Blocking I/O at scale | Virtual threads |
| CPU-bound parallelism | Parallel streams or ForkJoinPool |
| Complex async pipelines | CompletableFuture |
| Related concurrent tasks | Structured Concurrency (Java 25 — 5th Preview, JEP 505) |

---

## Performance Quick Wins

📚 **Reference:** [performance.md](references/performance.md) — full guide (JFR, async-profiler, JMH, GC tuning, memory analysis)

The five most-broken patterns in code review (full examples & rationale in `performance.md`):

1. **String concat in loops** → `StringBuilder` (pre-sized) or `Collectors.joining()`
2. **Boxed types in tight loops** → primitives (or `LongStream`/`IntStream` for sums)
3. **Default-capacity collections** → pre-size when N is known (`new ArrayList<>(n)`, `new HashMap<>(n*4/3)`)
4. **Unbounded caches** → Caffeine with `maximumSize` + `expireAfterWrite`
5. **`ThreadLocal` in pooled threads** → call `remove()` in `finally` (or migrate to Scoped Values, JEP 506)

JVM-level Java 25 wins: Compact Object Headers (JEP 519), Generational Shenandoah (JEP 521) — see `performance.md` § JVM Tuning.

---

## Design Patterns Quick Guide

📚 **References:** [design-patterns.md](references/design-patterns.md) (decision tree + index) | [creational](references/design-patterns-creational.md) (Builder, Factory, Singleton) | [structural](references/design-patterns-structural.md) (Adapter, Decorator, Facade, Proxy, Composite, Flyweight) | [behavioral](references/design-patterns-behavioral.md) (Strategy, Observer, Command, CoR, Template, Visitor, State, Memento)

**Modern-Java replacements to favour over textbook GoF:**

| Traditional | Modern Java |
|---|---|
| Strategy classes | `@FunctionalInterface` + `Map<Type, Strategy>` |
| Builder boilerplate | Record + `Consumer<Builder>` factory |
| Factory if-else | Sealed interface + exhaustive switch |
| Singleton (DCL) | `enum` singleton (or static holder) |
| Observer | `Consumer<T>` + method references / Flow API |
| Visitor double-dispatch | Sealed + pattern matching switch |
| State machine | Sealed interface of state records |
| Memento | Record as immutable snapshot |

For the rest (Adapter, Decorator, Facade, Proxy, Composite, Flyweight, Chain of Responsibility, Template, Command, Abstract Factory): consult the reference — each section shows both the classical and the modern Java 17+ form.

---

## When Writing Tests

📚 **References:** [testing.md](references/testing.md)

### 🔴 BLOCKING
- **No shared mutable state between tests** → Use `@BeforeEach` for fresh state
- **Don't mock internal classes** → Only mock external services (HTTP, DB)

### 🟡 WARNING
- **Test names must describe behavior** → `whenX_shouldY`, not `test1`
- **No `Thread.sleep()` in tests** → Use `Awaitility` for async assertions

### 🟢 Test Type Decision
| Question | Test Type |
|----------|-----------|
| Pure logic, no I/O? | Unit test (plain JUnit) |
| Database access? | `@DataJpaTest` |
| REST controller? | `@WebMvcTest` |
| Full HTTP request cycle? | `@SpringBootTest` E2E |

### 🟢 Test Naming Convention
```java
void findById_whenUserExists_returnsUser()
void calculateTotal_givenEmptyCart_throwsException()
```

---

## When Handling Security

📚 **References:** [security.md](references/security.md)

### 🔴 BLOCKING
- **Never use MD5/SHA1 for passwords** → Use BCrypt (work factor 12+) or Argon2
- **Never hardcode secrets** → Use environment variables
- **Never build SQL with string concatenation** → Use parameterized queries
- **Never use `Random` for security tokens** → Use `SecureRandom`

### 🟢 Algorithm Quick Reference
| Need | Use |
|------|-----|
| Password storage | BCrypt or Argon2 |
| Data encryption | AES-256-GCM |
| Random tokens | `SecureRandom` + Base64 |
| Hashing (integrity) | SHA-256 |
| Signatures | ECDSA or RSA-PSS |

```java
// 🔴 WRONG
String hash = MessageDigest.getInstance("MD5").digest(password.getBytes());

// ✅ CORRECT (Spring Security)
BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(12);
String hash = encoder.encode(password);
```

---

## When Using Modules

📚 **References:** [module-system.md](references/module-system.md)

### 🟢 When to Modularize
- Building a reusable **library** for external consumers
- Need **strong encapsulation** of internal packages
- Large application with clear **architectural boundaries**

### 🟢 When NOT to Modularize
- Small applications or rapid prototyping
- All dependencies don't support modules
- Heavy reflection frameworks without clear `opens` strategy

### 🟡 WARNING
- **Don't export internal packages** → Only export public API
- **Use `opens` for frameworks** → Jackson, Hibernate, Spring need reflection access

```java
module com.example.myapp {
    exports com.example.myapp.api;          // Public API only
    opens com.example.myapp.dto to com.fasterxml.jackson.databind;
}
```

---

## When Analyzing Performance

📚 **References:** [performance.md](references/performance.md)

### 🟢 Tool Selection
| Question | Tool |
|----------|------|
| Where is CPU time spent? | async-profiler (flamegraph) |
| Production-safe monitoring? | JFR (Java Flight Recorder) |
| Compare two implementations? | JMH (microbenchmark) |
| Memory leak suspected? | Heap dump + Eclipse MAT |

### 🔴 BLOCKING (Performance Anti-Patterns)
- **String concatenation in loops** → Use `StringBuilder`
- **Boxed types in tight loops** → Use primitives
- **Unbounded caches** → Use `Caffeine` with max size
- **ThreadLocal not cleaned in pooled threads** → Call `remove()`

```bash
# JFR - start recording
jcmd <pid> JFR.start name=rec duration=60s filename=rec.jfr

# async-profiler - CPU flamegraph
./asprof -d 30 -f cpu.html <pid>
```

---

## Code Review Checklist

### 🔴 BLOCKING (Must fix before merge)
- [ ] No `orElse(method())` → use `orElseGet()`
- [ ] No `isPresent()` + `get()` or bare `.get()`
- [ ] No mutable state in stream operations
- [ ] No generic `Exception` catch or empty catch
- [ ] No mutable fields in records without `List.copyOf()`
- [ ] No virtual thread pooling
- [ ] No MD5/SHA1 for password hashing → BCrypt/Argon2
- [ ] No hardcoded secrets → environment variables
- [ ] No SQL string concatenation → parameterized queries
- [ ] No shared mutable state between tests

### 🟡 WARNING (Should fix)
- [ ] No deprecated API usage
- [ ] No `synchronized` with blocking I/O in virtual threads
- [ ] No infinite streams without `limit()`
- [ ] Test names describe behavior, not implementation
- [ ] Internal packages not exported from modules
- [ ] No catch-and-rethrow that hides exceptions from `@Retry` configuration
- [ ] No stacking multiple AOP annotations (`@Async` + `@Retry` + `@Transactional`) on same method

### 🟢 BEST PRACTICE (Recommended)
- [ ] Records used for data carrier classes
- [ ] Pattern matching instead of instanceof + cast
- [ ] Switch expressions instead of if-else chains
- [ ] Text blocks for multi-line strings
- [ ] StringBuilder in string loops
- [ ] Primitives (not boxed) in tight loops
- [ ] Collections pre-sized when size known
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)
- [ ] Only external services mocked in tests
- [ ] BCrypt work factor >= 12

---

## Related Skills

- `common-java-jpa` — JPA entities, relationships, Hibernate optimization
- `common-java-testing` — JUnit 5, Mockito, Testcontainers
- `common-rest-api` — Spring REST controllers, OpenAPI
- `common-security` — Authentication, authorization, OWASP
- `buy-nature-backend-coding-guide` — Buy Nature Java conventions
