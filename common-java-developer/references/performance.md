# Java Performance Analysis

> Profiling tools, benchmarking, and memory analysis for Java 8-25.

---

## Table of Contents
1. [Decision Tree: Which Tool?](#decision-tree-which-tool)
2. [JFR (Java Flight Recorder)](#jfr-java-flight-recorder)
3. [async-profiler](#async-profiler)
4. [JMH (Microbenchmarks)](#jmh-microbenchmarks)
5. [Memory Analysis](#memory-analysis)
6. [Performance Checklist (Code Level)](#performance-checklist-code-level)
7. [Quick Wins](#quick-wins)

---

## Decision Tree: Which Tool?

```
What performance issue are you investigating?
│
├── Where is CPU time spent?
│   ├── Production-safe needed? → JFR
│   └── Development/staging? → async-profiler (flamegraph)
│
├── Comparing two implementations?
│   └── JMH (microbenchmark)
│
├── Memory leak suspected?
│   └── Heap dump + Eclipse MAT
│
├── Thread contention/deadlock?
│   ├── Production? → JFR (lock events)
│   └── Development? → async-profiler (lock mode)
│
├── GC pauses too long?
│   └── JFR (GC events) + GC log analysis
│
└── Slow database queries?
    └── Enable SQL logging + explain plans (not Java tooling)
```

### Tool Comparison

| Tool | Best For | Overhead | Production Safe |
|------|----------|----------|-----------------|
| **JFR** | Continuous monitoring, all-purpose | Very low (<1%) | ✅ Yes |
| **async-profiler** | CPU/allocation flamegraphs | Low (~1-3%) | ✅ Yes (careful) |
| **JMH** | Micro-benchmarks, A/B comparisons | N/A | ❌ Development only |
| **VisualVM** | Quick exploration, heap browsing | Medium | ⚠️ Development |
| **Eclipse MAT** | Heap dump analysis, leak detection | N/A | N/A (offline) |

---

## JFR (Java Flight Recorder)

JFR is built into the JDK (free since Java 11). Production-safe with <1% overhead.

### Starting a Recording

**Command Line (at JVM start)**
```bash
java -XX:StartFlightRecording=filename=recording.jfr,duration=60s,settings=profile MyApp
```

**Command Line (attach to running JVM)**
```bash
# List Java processes
jcmd

# Start recording
jcmd <pid> JFR.start name=MyRecording duration=60s filename=recording.jfr

# Stop recording
jcmd <pid> JFR.stop name=MyRecording
```

**Programmatic (Java 14+)**
```java
import jdk.jfr.*;

try (Recording recording = new Recording(Configuration.getConfiguration("profile"))) {
    recording.setDestination(Path.of("recording.jfr"));
    recording.start();

    // ... application runs ...

    Thread.sleep(Duration.ofMinutes(1).toMillis());
    recording.stop();
}
```

### JFR Settings

| Setting | Use Case |
|---------|----------|
| `default` | Low overhead, basic events |
| `profile` | More detail, slightly higher overhead |
| Custom `.jfc` | Fine-tuned for specific needs |

### Key Events to Monitor

| Event | What It Shows |
|-------|---------------|
| `jdk.CPULoad` | System and JVM CPU usage |
| `jdk.GarbageCollection` | GC events and pause times |
| `jdk.ObjectAllocationInNewTLAB` | Allocation hotspots |
| `jdk.ThreadPark` | Virtual thread issues (Java 21+) |
| `jdk.JavaMonitorEnter` | Lock contention |
| `jdk.FileRead/Write` | File I/O operations |
| `jdk.SocketRead/Write` | Network I/O operations |
| `jdk.ExecutionSample` | CPU sampling (method hotspots) |

### JFR Analysis Workflow

```
1. Start recording (production-safe)
       ↓
2. Let application run under realistic load
       ↓
3. Stop and download .jfr file
       ↓
4. Analyze with:
   - JDK Mission Control (JMC) - Official GUI
   - IntelliJ IDEA Profiler - Integrated
   - jfr CLI tool - Command line
```

**CLI Quick Analysis**
```bash
# Summary
jfr summary recording.jfr

# Print specific events
jfr print --events jdk.GarbageCollection recording.jfr

# Convert to JSON
jfr print --json recording.jfr > recording.json
```

---

## async-profiler

Native profiler with very low overhead. Produces flamegraphs.

### Installation

```bash
# Download from https://github.com/jvm-profiling-tools/async-profiler
wget https://github.com/async-profiler/async-profiler/releases/download/v3.0/async-profiler-3.0-linux-x64.tar.gz
tar xzf async-profiler-*.tar.gz
```

### CPU Profiling

```bash
# Profile for 30 seconds, output HTML flamegraph
./asprof -d 30 -f profile.html <pid>

# With specific event (cpu, wall, alloc, lock)
./asprof -e cpu -d 30 -f cpu.html <pid>

# Wall-clock time (includes I/O waits)
./asprof -e wall -d 30 -f wall.html <pid>
```

### Allocation Profiling

```bash
# Find where memory is allocated
./asprof -e alloc -d 30 -f alloc.html <pid>
```

### Lock Contention Profiling

```bash
# Find lock hotspots
./asprof -e lock -d 30 -f locks.html <pid>
```

### Reading Flamegraphs

```
┌─────────────────────────────────────────────────────────────┐
│                    main                                      │ ← Entry point (bottom)
├──────────────────────┬──────────────────────────────────────┤
│    processOrder      │         handlePayment                │ ← Called methods
├─────────┬────────────┼────────────┬─────────────────────────┤
│ validate│ calculate  │ chargeCard │     sendEmail           │ ← Deeper calls
├─────────┴────────────┴────────────┴─────────────────────────┤

Width = time spent (wider = more time)
Height = call stack depth
Color = usually random (no meaning) or package-based
```

**What to Look For:**
- **Wide bars at top** = Method taking most time
- **Tall narrow towers** = Deep call stacks (potential simplification)
- **Plateaus** = Time spent in single method (optimize this)

---

## JMH (Microbenchmarks)

JMH is the standard for accurate Java microbenchmarks. Handles JVM warmup, dead code elimination, and other pitfalls.

### Setup (Maven)

```xml
<dependency>
    <groupId>org.openjdk.jmh</groupId>
    <artifactId>jmh-core</artifactId>
    <version>1.37</version>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.openjdk.jmh</groupId>
    <artifactId>jmh-generator-annprocess</artifactId>
    <version>1.37</version>
    <scope>test</scope>
</dependency>
```

### Basic Benchmark

```java
import org.openjdk.jmh.annotations.*;
import java.util.concurrent.TimeUnit;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@State(Scope.Benchmark)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(2)
public class StringConcatBenchmark {

    private List<String> items;

    @Setup
    public void setup() {
        items = IntStream.range(0, 100)
            .mapToObj(i -> "item" + i)
            .toList();
    }

    @Benchmark
    public String concatWithPlus() {
        String result = "";
        for (String s : items) {
            result += s;  // O(n²)
        }
        return result;
    }

    @Benchmark
    public String concatWithBuilder() {
        StringBuilder sb = new StringBuilder();
        for (String s : items) {
            sb.append(s);  // O(n)
        }
        return sb.toString();
    }

    @Benchmark
    public String concatWithJoining() {
        return items.stream().collect(Collectors.joining());
    }
}
```

### Running Benchmarks

```bash
# Maven
mvn clean install
java -jar target/benchmarks.jar

# Or use JMH Runner programmatically
public static void main(String[] args) throws Exception {
    Options opt = new OptionsBuilder()
        .include(StringConcatBenchmark.class.getSimpleName())
        .forks(2)
        .build();
    new Runner(opt).run();
}
```

### JMH Annotations Reference

| Annotation | Purpose |
|------------|---------|
| `@Benchmark` | Mark method as benchmark |
| `@BenchmarkMode` | Throughput, AverageTime, SampleTime, SingleShotTime |
| `@OutputTimeUnit` | ns, us, ms, s |
| `@State` | Scope of state (Benchmark, Thread, Group) |
| `@Setup` / `@TearDown` | Before/after benchmark (Level: Trial, Iteration, Invocation) |
| `@Warmup` | Warmup configuration |
| `@Measurement` | Measurement configuration |
| `@Fork` | Number of JVM forks |
| `@Param` | Parameterized benchmarks |

### Common JMH Pitfalls

```java
// 🔴 WRONG - Dead code elimination (result unused)
@Benchmark
public void measure() {
    Math.sin(x);  // JVM may eliminate this!
}

// ✅ CORRECT - Return result or use Blackhole
@Benchmark
public double measureReturn() {
    return Math.sin(x);
}

@Benchmark
public void measureBlackhole(Blackhole bh) {
    bh.consume(Math.sin(x));
}

// 🔴 WRONG - Constant folding
@Benchmark
public double measureConstant() {
    return Math.sin(0.5);  // JVM pre-computes at compile time!
}

// ✅ CORRECT - Use @State field
@State(Scope.Benchmark)
public class MyBenchmark {
    double x = 0.5;

    @Benchmark
    public double measure() {
        return Math.sin(x);  // x read from field, not constant
    }
}
```

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

---

## Quick Reference Commands

```bash
# JFR
jcmd <pid> JFR.start name=rec duration=60s filename=rec.jfr
jcmd <pid> JFR.stop name=rec
jfr print --events jdk.GarbageCollection rec.jfr

# async-profiler
./asprof -d 30 -f cpu.html <pid>          # CPU
./asprof -e alloc -d 30 -f alloc.html <pid>  # Allocation
./asprof -e lock -d 30 -f lock.html <pid>    # Lock contention

# Heap dump
jcmd <pid> GC.run                          # Trigger GC first
jcmd <pid> GC.heap_dump heap.hprof         # Capture dump

# GC logs (JVM args)
-Xlog:gc*:file=gc.log:time,uptime,level,tags
```
