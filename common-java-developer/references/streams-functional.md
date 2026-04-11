# Stream API & Functional Programming

## Stream Pipeline Structure

```
Source → Intermediate Operations → Terminal Operation
```

- **Source**: Collection, array, generator, I/O channel
- **Intermediate**: Transform stream, return new stream (lazy)
- **Terminal**: Produce result or side-effect (triggers execution)

---

## Common Operations

### Intermediate Operations (Lazy)

```java
// filter - keep elements matching predicate
stream.filter(x -> x > 0)

// map - transform each element
stream.map(String::toUpperCase)

// flatMap - flatten nested streams
stream.flatMap(list -> list.stream())

// distinct - remove duplicates
stream.distinct()

// sorted - natural order or with comparator
stream.sorted()
stream.sorted(Comparator.comparing(User::getName))

// peek - debug/logging (don't modify!)
stream.peek(x -> log.debug("Processing: {}", x))

// limit - take first N elements
stream.limit(10)

// skip - skip first N elements
stream.skip(5)

// takeWhile (Java 9) - take while predicate true
stream.takeWhile(x -> x < 100)

// dropWhile (Java 9) - drop while predicate true
stream.dropWhile(x -> x < 100)
```

### Terminal Operations (Eager)

```java
// forEach - perform action on each element
stream.forEach(System.out::println)

// collect - gather into collection
stream.collect(Collectors.toList())

// reduce - combine elements
stream.reduce(0, Integer::sum)

// count - count elements
stream.count()

// findFirst / findAny
stream.findFirst()  // Optional<T>
stream.findAny()    // For parallel, may be faster

// anyMatch / allMatch / noneMatch
stream.anyMatch(x -> x > 0)
stream.allMatch(x -> x > 0)
stream.noneMatch(x -> x < 0)

// min / max
stream.min(Comparator.naturalOrder())
stream.max(Comparator.comparing(User::getAge))

// toArray
stream.toArray(String[]::new)
```

---

## Collectors

### Basic Collectors

```java
// toList, toSet
.collect(Collectors.toList())
.collect(Collectors.toSet())

// toMap
.collect(Collectors.toMap(
    User::getId,          // key mapper
    User::getName         // value mapper
))

// toMap with merge function (handle duplicates)
.collect(Collectors.toMap(
    User::getDepartment,
    User::getSalary,
    Integer::sum          // merge function
))

// joining
.collect(Collectors.joining(", "))  // "a, b, c"
.collect(Collectors.joining(", ", "[", "]"))  // "[a, b, c]"
```

### Grouping & Partitioning

```java
// groupingBy - group by key
Map<Department, List<Employee>> byDept =
    employees.stream()
        .collect(Collectors.groupingBy(Employee::getDepartment));

// groupingBy with downstream collector
Map<Department, Long> countByDept =
    employees.stream()
        .collect(Collectors.groupingBy(
            Employee::getDepartment,
            Collectors.counting()
        ));

// partitioningBy - split into true/false
Map<Boolean, List<Integer>> partition =
    numbers.stream()
        .collect(Collectors.partitioningBy(n -> n > 0));
```

### Aggregating Collectors

```java
// counting
.collect(Collectors.counting())

// summingInt / summingLong / summingDouble
.collect(Collectors.summingInt(Item::getQuantity))

// averagingInt / averagingDouble
.collect(Collectors.averagingDouble(Item::getPrice))

// summarizingInt - all stats at once
IntSummaryStatistics stats =
    items.stream().collect(Collectors.summarizingInt(Item::getQuantity));
// stats.getSum(), stats.getAverage(), stats.getMax(), stats.getMin(), stats.getCount()
```

---

## Parallel Streams

### The N × Q Rule

**Only use parallel streams when: N × Q > 10,000**

- **N** = number of elements
- **Q** = cost per element operation

```java
// ✅ Good candidate - large dataset, CPU-intensive
largeList.parallelStream()
    .filter(item -> complexCalculation(item))
    .collect(toList());

// ❌ Bad candidate - small dataset
smallList.parallelStream()  // Overhead > benefit
    .filter(item -> item.isActive())
    .collect(toList());
```

### Good Data Sources for Parallel

| Source | Splittable | Parallel-Friendly |
|--------|------------|-------------------|
| ArrayList | O(1) | ✅ Excellent |
| IntStream.range() | O(1) | ✅ Excellent |
| HashSet | O(n) | ⚠️ Moderate |
| LinkedList | O(n) | ❌ Poor |
| Stream.iterate() | O(n) | ❌ Poor |

### Critical Rules

1. **No shared mutable state**
```java
// ❌ WRONG - race condition
List<String> results = new ArrayList<>();
stream.parallel().forEach(item -> results.add(item));

// ✅ CORRECT - collect
List<String> results = stream.parallel().collect(toList());
```

2. **Avoid I/O operations**
```java
// ❌ WRONG - blocks ForkJoinPool
stream.parallel().forEach(item -> {
    database.save(item);  // Blocking I/O
});

// ✅ CORRECT - use virtual threads for I/O
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    items.forEach(item -> executor.submit(() -> database.save(item)));
}
```

3. **Order matters**
```java
// If order matters, use forEachOrdered
stream.parallel()
    .map(this::transform)
    .forEachOrdered(this::processInOrder);
```

---

## Optional Best Practices

### Correct Usage

```java
// Creating
Optional.of(value)           // Throws if null
Optional.ofNullable(value)   // Safe for nullable
Optional.empty()             // Empty optional

// Consuming
optional.map(User::getName)
        .filter(name -> !name.isEmpty())
        .orElse("Anonymous");

optional.ifPresent(user -> process(user));

optional.ifPresentOrElse(
    user -> process(user),
    () -> handleEmpty()
);
```

### orElse vs orElseGet

```java
// orElse - ALWAYS evaluates default
optional.orElse(createDefault());  // createDefault() always called!

// orElseGet - LAZY evaluation
optional.orElseGet(() -> createDefault());  // Only called if empty

// Rule: Use orElseGet for method calls
optional.orElse("constant");               // ✅ OK - simple value
optional.orElseGet(() -> loadFromDb());    // ✅ OK - expensive operation
optional.orElse(loadFromDb());             // ❌ WRONG - always loads!
```

### Anti-Patterns to Avoid

```java
// ❌ isPresent + get
if (optional.isPresent()) {
    return optional.get();
}

// ✅ Better
return optional.orElse(default);

// ❌ Optional as parameter
void process(Optional<String> name) { }

// ✅ Better - use overloading
void process(String name) { }
void process() { }  // No name version

// ❌ Optional as field
class User {
    private Optional<String> nickname;  // Don't do this
}

// ✅ Better - nullable field
class User {
    private String nickname;  // null means absent
    public Optional<String> getNickname() { return Optional.ofNullable(nickname); }
}
```
