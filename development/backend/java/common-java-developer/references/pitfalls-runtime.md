# Java Runtime, Concurrency & Framework Pitfalls

> Runtime-level pitfalls — virtual threads, memory leaks, concurrency bugs, Spring AOP proxies.
> Language-level pitfalls (Optional / Stream / Record / generic anti-patterns) live in [pitfalls-language.md](pitfalls-language.md).

---

## Table of Contents

1. [Virtual Thread Pitfalls](#virtual-thread-pitfalls)
2. [Memory Leak Patterns](#memory-leak-patterns)
3. [Concurrency Bugs](#concurrency-bugs)
4. [Spring AOP Proxy Pitfalls](#spring-aop-proxy-pitfalls)

---

## Virtual Thread Pitfalls

### 🔴 Pooling Virtual Threads

```java
// ❌ WRONG - defeats the purpose of virtual threads
ExecutorService pool = Executors.newFixedThreadPool(100);
// or
Semaphore semaphore = new Semaphore(100);
virtualThread.run(() -> {
    semaphore.acquire();
    try { work(); }
    finally { semaphore.release(); }
});

// ✅ CORRECT - one virtual thread per task
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    tasks.forEach(task -> executor.submit(task));
}
```

### 🟡 Synchronized with Blocking (Java 21–23 only)

> **Java 24+ (JEP 491) removes carrier-thread pinning** caused by `synchronized`.
> The pitfall below applies only to code targeting Java 21 / 22 / 23 ;
> `ReentrantLock` remains the safe version-agnostic choice.

```java
// ❌ WRONG on Java 21–23 - pins carrier thread (no longer pins on Java 24+)
synchronized (lock) {
    socket.read();  // Blocking I/O inside synchronized
}

// ✅ CORRECT (version-agnostic) - use ReentrantLock
private final ReentrantLock lock = new ReentrantLock();

lock.lock();
try {
    socket.read();
} finally {
    lock.unlock();
}
```

### 🟡 ThreadLocal in Virtual Threads

```java
// ⚠️ WARNING - ThreadLocal works but may accumulate with many virtual threads
private static final ThreadLocal<Connection> CONNECTION = new ThreadLocal<>();

// ✅ BETTER - use Scoped Values (FINAL in Java 25, JEP 506)
private static final ScopedValue<Connection> CONNECTION = ScopedValue.newInstance();

ScopedValue.where(CONNECTION, conn).run(() -> {
    processRequest();
});
```

---

## Memory Leak Patterns

### 🟡 Static Collections Without Eviction

```java
// ❌ WRONG - unbounded growth
private static final Map<String, Object> cache = new HashMap<>();

public void addToCache(String key, Object value) {
    cache.put(key, value);  // Never removed = memory leak!
}

// ✅ CORRECT - bounded with eviction (LRU)
private static final Map<String, Object> cache =
    Collections.synchronizedMap(new LinkedHashMap<>(100, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry eldest) {
            return size() > 100;
        }
    });

// ✅ Or use a proper cache library (Caffeine, Guava Cache)
```

### 🔴 ThreadLocal Not Removed in Thread Pools

```java
// ❌ WRONG - ThreadLocal never cleared
private static final ThreadLocal<Connection> connectionHolder = new ThreadLocal<>();

public void handleRequest() {
    connectionHolder.set(getConnection());
    // work...
    // Never removed! Thread reused with stale connection
}

// ✅ CORRECT - always remove in finally
public void handleRequest() {
    try {
        connectionHolder.set(getConnection());
        // work...
    } finally {
        connectionHolder.remove();  // Critical!
    }
}
```

### 🟡 Inner Classes Holding Outer References

```java
// ❌ WRONG - anonymous class holds reference to Outer
public class Outer {
    private byte[] largeData = new byte[10_000_000];

    public Runnable getTask() {
        return new Runnable() {
            public void run() { }  // Holds reference to Outer!
        };
    }
}

// ✅ CORRECT - lambda captures nothing (if not using outer fields)
public Runnable getTask() {
    return () -> { };  // No implicit reference
}

// ✅ Or use static nested class
private static class MyTask implements Runnable {
    public void run() { }
}
```

### 🟡 Listeners Not Unregistered

```java
// ❌ WRONG - listener never removed
public void init() {
    eventSource.addListener(this);  // 'this' can't be GC'd
}

// ✅ CORRECT - remove when done
public void destroy() {
    eventSource.removeListener(this);
}

// ✅ Or use WeakReference-based listeners
```

---

## Concurrency Bugs

### 🔴 Check-Then-Act Race Conditions

```java
// ❌ WRONG - another thread can insert between check and put
if (!map.containsKey(key)) {
    map.put(key, computeValue());
}

// ✅ CORRECT - atomic operation
map.computeIfAbsent(key, k -> computeValue());

// ❌ WRONG - same issue with increment
if (counter < MAX) {
    counter++;
}

// ✅ CORRECT - use AtomicInteger
atomicCounter.updateAndGet(c -> c < MAX ? c + 1 : c);
```

### 🔴 Double-Checked Locking Without Volatile

```java
// ❌ WRONG - instruction reordering can expose partially constructed object
private static Singleton instance;

public static Singleton getInstance() {
    if (instance == null) {
        synchronized (Singleton.class) {
            if (instance == null) {
                instance = new Singleton();  // May be seen before fully constructed!
            }
        }
    }
    return instance;
}

// ✅ CORRECT - volatile prevents reordering
private static volatile Singleton instance;

// ✅ Or use static holder (preferred)
private static class Holder {
    private static final Singleton INSTANCE = new Singleton();
}
public static Singleton getInstance() {
    return Holder.INSTANCE;
}
```

### 🔴 Shared Mutable State Without Synchronization

```java
// ❌ WRONG - concurrent modification
private int count = 0;

public void increment() {
    count++;  // Not atomic! Read-modify-write
}

// ✅ CORRECT - use AtomicInteger
private final AtomicInteger count = new AtomicInteger(0);

public void increment() {
    count.incrementAndGet();
}

// ✅ Or synchronize
private int count = 0;
public synchronized void increment() {
    count++;
}
```

### 🟡 Publishing Objects Before Fully Constructed

```java
// ❌ WRONG - 'this' escapes before construction complete
public class BadExample {
    private final int value;

    public BadExample() {
        EventBus.register(this);  // 'this' escapes!
        value = 42;  // Not yet assigned when register() runs
    }
}

// ✅ CORRECT - use factory method
public class GoodExample {
    private final int value;

    private GoodExample() {
        value = 42;
    }

    public static GoodExample create() {
        GoodExample obj = new GoodExample();
        EventBus.register(obj);  // Fully constructed
        return obj;
    }
}
```

---

## Spring AOP Proxy Pitfalls

> Full coverage: See `common-rest-api/references/spring-boot-config-pitfalls.md`

### 🔴 Self-Invocation Bypasses Proxy

```java
// WRONG - @Async/@Transactional ignored (direct method call bypasses proxy)
@Service
public class OrderService {
    public void processOrder(UUID id) {
        sendNotification(id);  // Direct call — proxy NOT involved!
    }

    @Async
    public void sendNotification(UUID id) { ... }  // @Async silently ignored
}

// CORRECT - Use separate bean
@Service
public class OrderService {
    private final NotificationService notificationService;

    public void processOrder(UUID id) {
        notificationService.sendAsync(id);  // Through proxy — @Async works
    }
}
```

### 🟡 Don't Stack Multiple AOP Annotations

```java
// WRONG - unpredictable proxy layer ordering
@Async
@Retry(name = "emailRetry")
@Transactional
public void sendEmail(String to) { ... }

// CORRECT - one AOP annotation per method, delegate between beans
```
