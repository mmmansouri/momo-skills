# Java Pitfalls & Anti-Patterns

---

## Quick Fix Reference

| Anti-Pattern | How to Fix |
|--------------|------------|
| `orElse(method())` | Use `orElseGet(() -> method())` for lazy eval |
| `isPresent() + get()` | Use `map().orElse()` chain |
| Mutable state in streams | Use `collect()` to new collection |
| Reusing consumed stream | Create new stream each time |
| Parallel stream for I/O | Use virtual threads instead |
| `synchronized` + blocking I/O | Use `ReentrantLock` |
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

### orElse vs orElseGet

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

### isPresent + get Anti-Pattern

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

### Optional as Field or Parameter

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

### Wrapping Non-Null Values

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

### Reusing Streams

```java
// ❌ WRONG - streams can only be consumed once
Stream<String> stream = list.stream();
long count = stream.count();
List<String> result = stream.collect(toList());  // IllegalStateException!

// ✅ CORRECT - create new stream for each operation
long count = list.stream().count();
List<String> result = list.stream().collect(toList());
```

### Mutable State in Streams

```java
// ❌ WRONG - race condition in parallel
List<String> results = new ArrayList<>();
stream.parallel().forEach(item -> results.add(item));

// ✅ CORRECT - use collect
List<String> results = stream.parallel().collect(toList());

// ✅ Or use thread-safe collection (slower)
List<String> results = Collections.synchronizedList(new ArrayList<>());
stream.parallel().forEach(item -> results.add(item));
```

### Parallel Stream on Wrong Data Source

```java
// ❌ WRONG - LinkedList has O(n) split cost
LinkedList<Item> items = getItems();
items.parallelStream().map(this::process).collect(toList());

// ✅ CORRECT - ArrayList has O(1) split
ArrayList<Item> items = new ArrayList<>(getItems());
items.parallelStream().map(this::process).collect(toList());

// Best sources for parallel:
// - ArrayList, arrays
// - IntStream.range(), LongStream.range()
// - HashSet (moderate)
```

### Parallel Stream for I/O

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

### peek() for Side Effects

```java
// ❌ WRONG - peek is for debugging, not side effects
stream.peek(item -> item.setProcessed(true))  // Mutation!
      .collect(toList());

// ✅ CORRECT - use map for transformation
stream.map(item -> item.withProcessed(true))
      .collect(toList());

// peek is OK for debugging
stream.peek(item -> log.debug("Processing: {}", item))
      .filter(...)
      .collect(toList());
```

---

## Record Limitations

### Records Are Final

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

### Records Are Immutable

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

### Mutable Components in Records

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

## Virtual Thread Pitfalls

### Pooling Virtual Threads

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

### Synchronized with Blocking

```java
// ❌ WRONG - pins carrier thread
synchronized (lock) {
    socket.read();  // Blocking I/O inside synchronized
}

// ✅ CORRECT - use ReentrantLock
private final ReentrantLock lock = new ReentrantLock();

lock.lock();
try {
    socket.read();
} finally {
    lock.unlock();
}
```

### ThreadLocal in Virtual Threads

```java
// ⚠️ WARNING - ThreadLocal works but may accumulate with many virtual threads
private static final ThreadLocal<Connection> CONNECTION = new ThreadLocal<>();

// ✅ BETTER - use Scoped Values (Java 25)
private static final ScopedValue<Connection> CONNECTION = ScopedValue.newInstance();

ScopedValue.where(CONNECTION, conn).run(() -> {
    processRequest();
});
```

---

## General Java Anti-Patterns

### Catching Generic Exceptions

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

### Swallowing Exceptions

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

### Ignoring InterruptedException

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

### Using Raw Types

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

### Mutable Static Fields

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

---

## Memory Leak Patterns

### Static Collections Without Eviction

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

### ThreadLocal Not Removed in Thread Pools

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

### Inner Classes Holding Outer References

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

### Listeners Not Unregistered

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

### Check-Then-Act Race Conditions

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

### Double-Checked Locking Without Volatile

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

### Shared Mutable State Without Synchronization

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

### Publishing Objects Before Fully Constructed

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

### Self-Invocation Bypasses Proxy

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

### Don't Stack Multiple AOP Annotations

```java
// WRONG - unpredictable proxy layer ordering
@Async
@Retry(name = "emailRetry")
@Transactional
public void sendEmail(String to) { ... }

// CORRECT - one AOP annotation per method, delegate between beans
```
