# Concurrency in Modern Java

---

## Decision Flowchart: Choosing the Right Approach

```
What type of task are you running?
│
├── 1. I/O-bound or CPU-bound?
│   ├── I/O-bound (network, database, file) → Go to step 2
│   └── CPU-bound (computation) → Use parallel streams or ForkJoinPool
│
├── 2. How many concurrent tasks?
│   ├── Few (<100) → Platform threads are fine
│   └── Many (>1000) → Virtual threads (Java 21+)
│
├── 3. Are tasks related (must complete together)?
│   ├── Yes → Structured Concurrency (Java 25)
│   └── No → Virtual thread executor
│
└── 4. Need complex async pipelines?
    ├── Yes → CompletableFuture
    └── No → Virtual threads (simpler)
```

### Quick Reference Table

| Scenario | Recommended Approach |
|----------|---------------------|
| HTTP server handling requests | Virtual threads |
| Parallel data processing | Parallel streams |
| Fetch user + orders concurrently | Structured Concurrency |
| Chain of async transformations | CompletableFuture |
| CPU-intensive batch job | ForkJoinPool |
| Simple I/O operations | Virtual threads |
| Timeout on multiple sources | `ShutdownOnSuccess` |

---

## Virtual Threads (Java 21+)

### What Are Virtual Threads?

Virtual threads are lightweight threads managed by the JVM, not the OS.

| Aspect | Platform Thread | Virtual Thread |
|--------|----------------|----------------|
| Managed by | OS | JVM |
| Memory | ~1MB stack | ~1KB initially |
| Creation cost | High | Very low |
| Max count | ~thousands | ~millions |
| Best for | CPU-bound | I/O-bound |

### Creating Virtual Threads

```java
// Direct creation
Thread.startVirtualThread(() -> {
    handleRequest();
});

// Using builder
Thread thread = Thread.ofVirtual()
    .name("my-virtual-thread")
    .start(() -> handleRequest());

// Using executor (recommended)
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    executor.submit(() -> handleRequest1());
    executor.submit(() -> handleRequest2());
}  // Waits for all tasks
```

### When to Use Virtual Threads

**Use Virtual Threads For:**
- HTTP server handlers
- Database queries
- File I/O
- Network calls
- Any blocking I/O operation

**Don't Use Virtual Threads For:**
- CPU-intensive computation (use platform threads)
- Tasks requiring thread affinity
- Tasks using `synchronized` with blocking inside

### Virtual Threads Pitfalls

#### 1. Don't Pool Virtual Threads

```java
// ❌ WRONG - defeats the purpose
ExecutorService pool = Executors.newFixedThreadPool(10);

// ✅ CORRECT - create per task
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    // New virtual thread per task
}
```

#### 2. Avoid synchronized with Blocking I/O

```java
// ❌ WRONG - pins carrier thread
synchronized (lock) {
    database.query();  // Blocking inside synchronized
}

// ✅ CORRECT - use ReentrantLock
private final ReentrantLock lock = new ReentrantLock();

lock.lock();
try {
    database.query();
} finally {
    lock.unlock();
}
```

#### 3. ThreadLocal Considerations

```java
// ⚠️ ThreadLocal works but may accumulate
// Use Scoped Values instead (Java 25)

// Traditional ThreadLocal
private static final ThreadLocal<User> CURRENT_USER = new ThreadLocal<>();

// Scoped Values (preferred for virtual threads)
private static final ScopedValue<User> CURRENT_USER = ScopedValue.newInstance();
```

---

## Scoped Values (Java 25)

### Replacement for ThreadLocal

```java
private static final ScopedValue<User> CURRENT_USER = ScopedValue.newInstance();

// Bind value for a scope
ScopedValue.where(CURRENT_USER, authenticatedUser).run(() -> {
    processRequest();  // CURRENT_USER available here
});

// Read value
void processRequest() {
    User user = CURRENT_USER.get();  // Gets bound value
    // or
    CURRENT_USER.orElse(defaultUser);
}
```

### Benefits over ThreadLocal
- Automatic cleanup (no need to remove())
- Inheritance to child scopes
- Better for virtual threads
- Immutable within scope

---

## Structured Concurrency (Java 25 Preview)

### Basic Usage

```java
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Subtask<User> userTask = scope.fork(() -> fetchUser(userId));
    Subtask<Orders> ordersTask = scope.fork(() -> fetchOrders(userId));

    scope.join();           // Wait for all tasks
    scope.throwIfFailed();  // Propagate exceptions

    return new UserProfile(
        userTask.get(),
        ordersTask.get()
    );
}
```

### ShutdownOnSuccess (first wins)

```java
try (var scope = new StructuredTaskScope.ShutdownOnSuccess<String>()) {
    scope.fork(() -> fetchFromMirror1());
    scope.fork(() -> fetchFromMirror2());
    scope.fork(() -> fetchFromMirror3());

    scope.join();
    return scope.result();  // First successful result
}
```

### Benefits
- Automatic cancellation of remaining tasks on failure
- Clear parent-child relationship
- Better error handling than CompletableFuture
- Observability-friendly

---

## CompletableFuture (Still Relevant)

### Basic Operations

```java
CompletableFuture<User> future = CompletableFuture
    .supplyAsync(() -> fetchUser(id))
    .thenApply(user -> enrichUser(user))
    .exceptionally(ex -> defaultUser);

// Combining futures
CompletableFuture<Void> all = CompletableFuture.allOf(future1, future2, future3);

// First completed
CompletableFuture<Object> any = CompletableFuture.anyOf(future1, future2, future3);
```

### Chaining

```java
CompletableFuture.supplyAsync(() -> fetchUser(id))
    .thenApply(user -> user.getProfile())       // Transform result
    .thenAccept(profile -> save(profile))       // Consume result
    .thenRun(() -> log("Done"))                 // Run after
    .exceptionally(ex -> { log(ex); return null; });
```

### When to Use What

| Scenario | Use This |
|----------|----------|
| Simple blocking I/O | Virtual Threads |
| Complex async pipelines | CompletableFuture |
| Multiple related tasks | Structured Concurrency |
| CPU-bound parallelism | Parallel Streams |

---

## Best Practices Summary

### Do's

```java
// ✅ Use virtual threads for I/O
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    tasks.forEach(task -> executor.submit(task));
}

// ✅ Use ReentrantLock instead of synchronized for virtual threads
private final ReentrantLock lock = new ReentrantLock();

// ✅ Use Scoped Values instead of ThreadLocal
private static final ScopedValue<Context> CTX = ScopedValue.newInstance();

// ✅ Use try-with-resources for executors
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    // tasks
}
```

### Don'ts

```java
// ❌ Don't pool virtual threads
ExecutorService pool = Executors.newFixedThreadPool(100);

// ❌ Don't use synchronized with blocking I/O in virtual threads
synchronized (lock) {
    blockingCall();
}

// ❌ Don't use parallel streams for I/O
items.parallelStream()
    .forEach(item -> database.save(item));  // Wrong!

// ❌ Don't ignore InterruptedException
catch (InterruptedException e) {
    // Wrong: swallowing interrupt
}
// ✅ Correct
catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw new RuntimeException(e);
}
```
