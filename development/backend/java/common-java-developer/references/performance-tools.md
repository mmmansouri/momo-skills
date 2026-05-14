# Java Performance Tools

> Profiling and benchmarking tools for Java 8-25: JFR, async-profiler, JMH, plus a tool-selection decision tree and quick-reference commands.

---

## Table of Contents
1. [Decision Tree: Which Tool?](#decision-tree-which-tool)
2. [JFR (Java Flight Recorder)](#jfr-java-flight-recorder)
3. [async-profiler](#async-profiler)
4. [JMH (Microbenchmarks)](#jmh-microbenchmarks)
5. [Quick Reference Commands](#quick-reference-commands)

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
