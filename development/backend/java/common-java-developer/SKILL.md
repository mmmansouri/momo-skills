---
name: common-java-developer
description: >-
  Modern Java development guide (Java 17-25 focus, compatible with 8-16). Use for any Java
  backend development, or when reviewing a PR touching Java files. Contains modern features
  (records, pattern matching, sealed classes, virtual threads), Stream API, Optional patterns,
  design patterns (Builder, Factory, Strategy), performance optimization, and critical pitfalls.
  For Java 8-16 projects, note that many features require Java 17+. Required for all Java
  development and review agents.
---

# Java Developer Guide (Java 8-25)

> **Severity Levels:** 🔴 BLOCKING (fails code review) | 🟡 WARNING (should fix) | 🟢 BEST PRACTICE (recommended)

---

## When Writing New Code

📚 **When choosing data carriers, sealed hierarchies, or `instanceof`/`switch` type-extraction idioms → read [pattern-matching.md](references/pattern-matching.md).**

📚 **When deciding which language feature (records, text blocks, `var`, switch expressions, virtual threads) to use for a new construct, or checking the Java version that introduced it → read [modern-features.md](references/modern-features.md).**

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

📚 **When migrating Java 8/11 idioms to modern equivalents (lambdas, records, pattern matching, virtual threads, JEPs 506/510/511/513) and you need the version-by-version feature map → read [modern-features.md](references/modern-features.md).**

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

📚 **When reviewing `try`/`catch` blocks, choosing checked vs unchecked exceptions, or diagnosing swallowed/rewrapped exceptions → read [pitfalls-language.md](references/pitfalls-language.md#general-java-anti-patterns).**

### 🔴 BLOCKING
- **Never catch generic `Exception`/`Throwable`** → Catch specific types
  **Why:** a generic catch also swallows the `RuntimeException`s and programming errors you never meant to handle, hiding real bugs behind a handler written for something else.
- **Never leave catch blocks empty** → Log or rethrow
  **Why:** an empty catch discards the failure silently, so execution continues in a corrupted state and the root cause never surfaces in any log or trace.

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
- **Catch-and-rethrow hides exceptions from retry frameworks** → If Resilience4j `@Retry` is configured for `MailException` but you catch and wrap it as `EmailSendingException`, retry never triggers. Let retriable exceptions propagate. Load the `common-spring-boot-config` skill for the full pitfall.

---

## When Creating Immutable Objects

📚 **When designing records/value objects, defending against mutable collection arguments, or auditing immutability claims → read [pitfalls-language.md](references/pitfalls-language.md#record-limitations).**

### 🔴 BLOCKING
- **Mutable fields in records without defensive copy** → Use `List.copyOf()`
  **Why:** the canonical constructor stores the caller's collection reference, so the caller can keep mutating it after construction — silently breaking the record's immutability and thread-safety guarantees.

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

📚 **When building stream pipelines, choosing collectors, or deciding sequential vs parallel execution → read [streams-functional.md](references/streams-functional.md).**

📚 **When diagnosing stream bugs (shared-state mutation, consumed streams, infinite streams, bad parallel sources) → read [pitfalls-language.md](references/pitfalls-language.md#stream-pitfalls).**

### 🔴 BLOCKING
- **Mutate shared state in streams** → Use `collect()` to new structure
  **Why:** side-effecting into a shared collection is a data race under parallel execution and has undefined ordering even when sequential — `collect()` performs a well-defined, thread-safe reduction instead.
- **Reuse a consumed stream** → Create new stream each time
  **Why:** a stream is a single-use pipeline; its terminal operation consumes it, so touching it again throws `IllegalStateException`.

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

📚 **When writing functional `Optional` chains (`map`/`flatMap`/`orElseGet`) or applying Optional best practices → read [streams-functional.md](references/streams-functional.md).**

📚 **When auditing `Optional` misuse (eager `orElse`, `isPresent()`+`get()`, Optional as field/parameter/collection element) → read [pitfalls-language.md](references/pitfalls-language.md#optional-misuse).**

### 🔴 BLOCKING
- **`orElse(method())`** → Use `orElseGet(() -> method())` for lazy evaluation
  **Why:** `orElse` eagerly evaluates its argument even when the Optional is present — a hidden cost or side effect on the happy path.
- **`isPresent()` + `get()`** → Use `map().orElse()` chain
  **Why:** the isPresent/get pair reintroduces the very null-check-then-dereference dance Optional exists to remove, and dropping the guard throws `NoSuchElementException`.
- **`Optional.get()` directly** → Use `orElseThrow()`
  **Why:** a bare `get()` on an empty Optional throws a contextless `NoSuchElementException`, whereas `orElseThrow()` documents intent and lets you supply a meaningful exception.

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

📚 **When designing thread-safe code, sizing executors, adopting virtual threads / Scoped Values / Structured Concurrency, or composing `CompletableFuture` pipelines → read [concurrency.md](references/concurrency.md).**

📚 **When diagnosing runtime failures (virtual-thread pinning, `ThreadLocal` leaks in pools, race conditions, double-checked locking, AOP self-invocation, memory leaks) → read [pitfalls-runtime.md](references/pitfalls-runtime.md).**

### 🔴 BLOCKING
- **Pool virtual threads** → Create new virtual thread per task
  **Why:** virtual threads are cheap and designed to be created one-per-task; capping them in a fixed pool serializes work and reintroduces the exact thread-starvation limit they were built to remove.

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

📚 **When the code-level quick wins aren't enough and you need GC tuning, memory-leak analysis, or the full code-level performance checklist → read [performance-tuning.md](references/performance-tuning.md).**

📚 **When you need profiling or benchmarking tools (JFR, async-profiler, JMH, MAT) and a tool-selection decision tree → read [performance-tools.md](references/performance-tools.md).**

The five most-broken patterns in code review (full examples & rationale in `performance-tuning.md`):

1. **String concat in loops** → `StringBuilder` (pre-sized) or `Collectors.joining()`
2. **Boxed types in tight loops** → primitives (or `LongStream`/`IntStream` for sums)
3. **Default-capacity collections** → pre-size when N is known (`new ArrayList<>(n)`, `new HashMap<>(n*4/3)`)
4. **Unbounded caches** → Caffeine with `maximumSize` + `expireAfterWrite`
5. **`ThreadLocal` in pooled threads** → call `remove()` in `finally` (or migrate to Scoped Values, JEP 506)

JVM-level Java 25 wins: Compact Object Headers (JEP 519), Generational Shenandoah (JEP 521) — see `performance-tuning.md` § JVM Tuning.

---

## Design Patterns Quick Guide

📚 **When picking a pattern from scratch and you need the decision tree, quick reference table, and modern-Java philosophy → read [design-patterns.md](references/design-patterns.md).**

📚 **When implementing Builder, Factory Method, Abstract Factory, or Singleton (especially the modern record / sealed / enum forms) → read [design-patterns-creational.md](references/design-patterns-creational.md).**

📚 **When implementing Adapter, Decorator, Facade, or Proxy (wrapping patterns — class hierarchies, function composition, dynamic proxies) → read [design-patterns-structural-wrapping.md](references/design-patterns-structural-wrapping.md).**

📚 **When implementing Composite or Flyweight (composition / shared-state patterns with sealed interfaces and `ConcurrentHashMap` factories) → read [design-patterns-structural-composition.md](references/design-patterns-structural-composition.md).**

📚 **When implementing Strategy, Command, Chain of Responsibility, or Template Method (control-flow patterns — functional interfaces, command queues, handler chains, higher-order templates) → read [design-patterns-behavioral-control.md](references/design-patterns-behavioral-control.md).**

📚 **When implementing Observer, Visitor, State, or Memento (state & notification patterns — Flow API, sealed types + pattern matching, record snapshots) → read [design-patterns-behavioral-state.md](references/design-patterns-behavioral-state.md).**

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

📚 **When writing or reviewing Java tests → load the `common-java-testing` skill** — single source of truth for JUnit 5, Mockito, AssertJ, Spring Boot testing slices, Testcontainers, and Given-When-Then conventions.

---

## When Handling Security

📚 **When choosing crypto primitives (password hashing, encryption, signatures, RNGs), defending against injection, or implementing secret/key management in Java code → read [security.md](references/security.md).**

### 🔴 BLOCKING
- **Never use MD5/SHA1 for passwords** → Use BCrypt (work factor 12+) or Argon2
  **Why:** MD5/SHA1 are fast, general-purpose hashes — a GPU brute-forces billions per second, whereas BCrypt/Argon2 are deliberately slow and salted to resist offline cracking of a stolen hash table.
- **Never hardcode secrets** → Use environment variables
  **Why:** a secret committed to source is exposed forever in VCS history to anyone with repo access, and rotating it then requires a code change and redeploy.
- **Never build SQL with string concatenation** → Use parameterized queries
  **Why:** concatenating user input into a query lets an attacker inject SQL syntax; bind parameters keep data separate from the statement so input can never alter its structure.
- **Never use `Random` for security tokens** → Use `SecureRandom`
  **Why:** `java.util.Random` is a predictable linear-congruential PRNG whose future output can be reconstructed from a few samples, making its tokens guessable; `SecureRandom` draws from a cryptographic entropy source.

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

📚 **When writing a `module-info.java`, choosing `exports`/`opens` directives, or migrating a classpath project to JPMS → read [module-system.md](references/module-system.md).**

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

📚 **When investigating CPU hotspots or benchmarking — and you need the JFR / async-profiler / JMH commands and decision tree → read [performance-tools.md](references/performance-tools.md).**

📚 **When investigating memory leaks, GC pauses, or running the code-level performance checklist (heap dumps, MAT, JVM tuning) → read [performance-tuning.md](references/performance-tuning.md).**

### 🟢 Tool Selection
| Question | Tool |
|----------|------|
| Where is CPU time spent? | async-profiler (flamegraph) |
| Production-safe monitoring? | JFR (Java Flight Recorder) |
| Compare two implementations? | JMH (microbenchmark) |
| Memory leak suspected? | Heap dump + Eclipse MAT |

### 🔴 BLOCKING (Performance Anti-Patterns)
- **String concatenation in loops** → Use `StringBuilder`
  **Why:** `String` is immutable, so `+=` allocates and copies a whole new character array every iteration — O(n²) time and garbage that a single `StringBuilder` buffer avoids.
- **Boxed types in tight loops** → Use primitives
  **Why:** autoboxing allocates a wrapper object per iteration and adds unboxing overhead, creating GC pressure that a primitive `int`/`long` avoids entirely.
- **Unbounded caches** → Use `Caffeine` with max size
  **Why:** a cache that never evicts grows with every unique key until it exhausts the heap — a slow but certain memory leak; a bounded eviction policy caps the footprint.
- **ThreadLocal not cleaned in pooled threads** → Call `remove()`
  **Why:** pooled threads are reused, so a `ThreadLocal` left set leaks its value into the next unrelated task and can pin a classloader, eventually causing `OutOfMemoryError`.

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

### 🟡 WARNING (Should fix)
- [ ] No deprecated API usage
- [ ] No `synchronized` with blocking I/O in virtual threads
- [ ] No infinite streams without `limit()`
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
- [ ] BCrypt work factor >= 12

---

## Related Skills

- `common-java-jpa` — JPA entities, relationships, Hibernate optimization
- `common-java-testing` — JUnit 5, Mockito, Testcontainers
- `common-rest-api` — Spring REST controllers, OpenAPI
- `common-security` — Authentication, authorization, OWASP
