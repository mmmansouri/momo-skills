# Java Performance Tuning

> JVM tuning (Java 25), memory analysis, code-level performance checklist and quick wins for Java 8-25.

---

## Table of Contents
1. [JVM Tuning (Java 25)](#jvm-tuning-java-25)
2. [Memory Analysis](#memory-analysis)
3. [Performance Checklist (Code Level)](#performance-checklist-code-level)
4. [Quick Wins](#quick-wins)

---

## JVM Tuning (Java 25)

### Compact Object Headers (FINAL in Java 25, JEP 519)

> Production-ready in Java 25, **off by default**. Reduces every Java object
> header from 12-16 bytes down to 8 bytes — typical heap savings are **10-20 %**
> on object-heavy workloads (DTOs, records, small collections).

```bash
# Enable
java -XX:+UnlockExperimentalVMOptions -XX:+UseCompactObjectHeaders -jar app.jar
```

**When it pays off:**
- Many short-lived small objects (event-loop / per-request DTOs)
- Memory-pressured services (heap close to `-Xmx`)
- Workloads where allocation rate, not CPU, is the bottleneck

**When it doesn't:**
- Heaps dominated by a few large arrays / buffers (savings negligible)
- Code that depends on the exact object layout (rare — fix the code)

Validate with JFR (`jdk.GarbageCollection`, `jdk.ObjectAllocationInNewTLAB`)
before and after.

### Generational Shenandoah (FINAL in Java 25, JEP 521)

> Shenandoah now ships with a **generational mode** — short-lived objects
> die in the young generation, dramatically reducing concurrent-mark work.

```bash
# Java 25 — enable generational mode (Shenandoah is still selected by -XX:+UseShenandoahGC)
java -XX:+UseShenandoahGC -XX:ShenandoahGCMode=generational -jar app.jar
```

**Pick a GC (Java 25 baseline):**

| Workload | Recommended GC |
|---|---|
| Default / mixed | **G1** (still the default) |
| Latency-critical, multi-GB heap | **ZGC** (generational, default since Java 24) |
| Throughput on huge heaps with low pause goal | **Shenandoah generational** (JEP 521) |
| Batch / throughput-only | **Parallel GC** |

---

## Memory Analysis

### Heap Dump Capture

```bash
# Trigger GC first (remove garbage)
jcmd <pid> GC.run

# Capture heap dump
jmap -dump:live,format=b,file=heap.hprof <pid>

# Or with jcmd
jcmd <pid> GC.heap_dump heap.hprof

# Auto-dump on OutOfMemoryError
java -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/dumps/ MyApp
```

### Analysis with Eclipse MAT

1. Open `heap.hprof` in Eclipse MAT
2. Run **Leak Suspects Report** (automatic analysis)
3. Check **Dominator Tree** (what retains most memory)
4. Check **Histogram** (object counts by class)

### Common Memory Leak Patterns

| Pattern | Cause | Solution |
|---------|-------|----------|
| Growing static collection | `static Map cache` without eviction | Use `CacheBuilder` with max size |
| ThreadLocal in thread pool | ThreadLocal not removed | Use `remove()` or Scoped Values |
| Inner class holding outer | Non-static inner class | Make inner class static |
| Event listeners not removed | `addListener()` without `removeListener()` | Use weak references or explicit cleanup |
| Large object graphs | One reference holds entire graph | Break references, use weak refs |

### Memory Leak Detection Checklist

```java
// 🔴 Unbounded cache
private static final Map<Key, Value> cache = new HashMap<>();  // Grows forever!

// ✅ Bounded cache
private static final Cache<Key, Value> cache = Caffeine.newBuilder()
    .maximumSize(10_000)
    .expireAfterWrite(Duration.ofMinutes(10))
    .build();

// 🔴 ThreadLocal not cleaned
private static final ThreadLocal<Context> context = new ThreadLocal<>();
// In thread pool, context accumulates!

// ✅ Clean up in finally
try {
    context.set(new Context());
    // ...
} finally {
    context.remove();  // Critical in pooled threads!
}

// 🔴 Non-static inner class
class Outer {
    byte[] largeData = new byte[10_000_000];

    class Inner {  // Holds implicit reference to Outer!
        void doSomething() { }
    }
}

// ✅ Static inner class
class Outer {
    byte[] largeData = new byte[10_000_000];

    static class Inner {  // No reference to Outer
        void doSomething() { }
    }
}
```

---

## Performance Checklist (Code Level)

### 🔴 BLOCKING

- [ ] **No string concatenation in loops** → Use `StringBuilder`
- [ ] **No boxed types in tight loops** → Use primitives
- [ ] **No unbounded caches** → Use `Caffeine` or `CacheBuilder`
- [ ] **ThreadLocal cleaned in pooled threads** → Call `remove()`

### 🟡 WARNING

- [ ] **Stream vs loop: measure, don't guess** → JMH benchmark
- [ ] **Parallel streams only when N × Q > 10,000**
- [ ] **Check N+1 query issues** → Enable SQL logging

### 🟢 BEST PRACTICE

- [ ] **Pre-size collections** when size known
- [ ] **Lazy initialization** for expensive objects
- [ ] **Connection/thread pooling** configured
- [ ] **Caching** for repeated expensive operations
- [ ] **Appropriate data structures** (HashMap O(1) vs TreeMap O(log n))

---

## Quick Wins

### StringBuilder in Loops

```java
// 🔴 WRONG - O(n²) - creates new String each iteration
String result = "";
for (String s : items) {
    result += s;
}

// ✅ CORRECT - O(n)
StringBuilder sb = new StringBuilder(items.size() * 16);  // Pre-size
for (String s : items) {
    sb.append(s);
}
String result = sb.toString();

// ✅ ALSO CORRECT - Collectors.joining()
String result = items.stream().collect(Collectors.joining());
```

### Primitives vs Boxed Types

```java
// 🔴 WRONG - boxing overhead (100x slower)
Long sum = 0L;
for (long i = 0; i < 1_000_000; i++) {
    sum += i;  // Unbox, add, box
}

// ✅ CORRECT - primitive
long sum = 0L;
for (long i = 0; i < 1_000_000; i++) {
    sum += i;
}

// ✅ ALSO CORRECT - LongStream
long sum = LongStream.range(0, 1_000_000).sum();
```

### Pre-size Collections

```java
// 🔴 WRONG - multiple resizes
List<User> users = new ArrayList<>();  // Default capacity 10
for (int i = 0; i < 10_000; i++) {
    users.add(loadUser(i));  // Resizes ~13 times
}

// ✅ CORRECT - pre-sized
List<User> users = new ArrayList<>(10_000);  // No resizing
for (int i = 0; i < 10_000; i++) {
    users.add(loadUser(i));
}

// HashMap: account for load factor (default 0.75)
int expectedSize = 1000;
Map<K, V> map = new HashMap<>(expectedSize * 4 / 3 + 1);
```

### Lazy Initialization

```java
// 🔴 WRONG - always creates expensive object
public class Service {
    private final ExpensiveResource resource = new ExpensiveResource();
}

// ✅ CORRECT - lazy (if not always needed)
public class Service {
    private volatile ExpensiveResource resource;

    private ExpensiveResource getResource() {
        ExpensiveResource local = resource;
        if (local == null) {
            synchronized (this) {
                local = resource;
                if (local == null) {
                    resource = local = new ExpensiveResource();
                }
            }
        }
        return local;
    }
}

// ✅ SIMPLER - use Supplier (Java 8+)
private final Supplier<ExpensiveResource> resource =
    Suppliers.memoize(ExpensiveResource::new);  // Guava
```

### Efficient String Operations

```java
// Check prefix/suffix
str.startsWith("prefix")  // ✅ Better than regex
str.endsWith(".txt")

// Empty check
str.isEmpty()        // ✅ Best (Java 6+)
str.isBlank()        // ✅ Best for whitespace (Java 11+)
str.length() == 0    // OK
"".equals(str)       // Avoid

// Comparison
str.equalsIgnoreCase(other)  // ✅ Better than toLowerCase().equals()
```

### Stream Performance Tips

```java
// Sequential by default (unless proven parallel is faster)
list.stream()        // ✅ Default
list.parallelStream()  // ⚠️ Only if N × Q > 10,000

// Prefer method references
.map(String::toLowerCase)  // ✅ Slightly faster
.map(s -> s.toLowerCase()) // OK

// Short-circuit operations
.anyMatch(...)  // ✅ Stops on first match
.filter(...).findFirst()  // ✅ Lazy evaluation

// Avoid boxed streams for primitives
IntStream.range(0, 1000).sum()  // ✅ Primitive
Stream.iterate(0, i -> i + 1).limit(1000).mapToInt(i -> i).sum()  // ❌ Boxing
```
