# Pattern Matching, Records & Sealed Classes

## Records

### When to Use Records
- DTOs (Data Transfer Objects)
- Value objects
- API request/response payloads
- Immutable data carriers
- Compound map keys

### Basic Record

```java
public record Point(int x, int y) { }

// Automatically generates:
// - Constructor: Point(int x, int y)
// - Accessors: x(), y()
// - equals(), hashCode(), toString()
```

### Compact Constructor (Validation)

```java
public record User(String email, String name) {
    public User {  // No parameters - compact constructor
        Objects.requireNonNull(email, "Email required");
        Objects.requireNonNull(name, "Name required");
        email = email.toLowerCase().strip();  // Normalize
        name = name.strip();
    }
}
```

### Records with Additional Methods

```java
public record Rectangle(int width, int height) {
    // Static factory method
    public static Rectangle square(int side) {
        return new Rectangle(side, side);
    }

    // Instance method
    public int area() {
        return width * height;
    }

    // Can override accessors
    public int width() {
        return Math.abs(width);  // Always positive
    }
}
```

### Record Limitations
- Cannot extend other classes (implicitly extends Record)
- All fields are final (immutable)
- Cannot declare instance fields outside components
- Can implement interfaces

---

## Sealed Classes & Interfaces

### When to Use Sealed Types
- Closed type hierarchies (known subtypes)
- Algebraic data types
- State machines
- Domain modeling with exhaustive handling

### Sealed Interface

```java
public sealed interface Shape
    permits Circle, Rectangle, Triangle {

    double area();
}

public record Circle(double radius) implements Shape {
    public double area() { return Math.PI * radius * radius; }
}

public record Rectangle(double width, double height) implements Shape {
    public double area() { return width * height; }
}

public final class Triangle implements Shape {
    // final - cannot be extended
}

public non-sealed class CustomShape implements Shape {
    // non-sealed - can be extended by anyone
}
```

### Benefits with Pattern Matching

```java
// Compiler ensures exhaustive handling
double getArea(Shape shape) {
    return switch (shape) {
        case Circle c -> Math.PI * c.radius() * c.radius();
        case Rectangle r -> r.width() * r.height();
        case Triangle t -> calculateTriangleArea(t);
        // No default needed - compiler knows all cases
    };
}
```

---

## Pattern Matching for instanceof

### Basic Usage

```java
// Before (verbose)
if (obj instanceof String) {
    String s = (String) obj;
    return s.length();
}

// After (concise)
if (obj instanceof String s) {
    return s.length();
}

// With negation
if (!(obj instanceof String s)) {
    throw new IllegalArgumentException();
}
// s is in scope here
return s.length();
```

### With Conditions

```java
if (obj instanceof String s && s.length() > 5) {
    return s.toUpperCase();
}

// Note: && works, || doesn't (s might not be bound)
// if (obj instanceof String s || s.length() > 5)  // Compile error
```

---

## Pattern Matching for switch

### Type Patterns

```java
String format(Object obj) {
    return switch (obj) {
        case Integer i -> "int: " + i;
        case Long l -> "long: " + l;
        case Double d -> "double: " + d;
        case String s -> "string: " + s;
        case null -> "null";
        default -> "unknown: " + obj;
    };
}
```

### Guarded Patterns (when clause)

```java
String classify(Number n) {
    return switch (n) {
        case Integer i when i < 0 -> "negative int";
        case Integer i when i == 0 -> "zero";
        case Integer i -> "positive int";
        case Double d when d.isNaN() -> "NaN";
        case Double d -> "double: " + d;
        default -> "other number";
    };
}
```

### Record Patterns (Deconstruction)

```java
record Point(int x, int y) { }
record Circle(Point center, double radius) { }

String describe(Object obj) {
    return switch (obj) {
        // Simple record pattern
        case Point(int x, int y) -> "Point at (" + x + ", " + y + ")";

        // Nested record pattern
        case Circle(Point(int x, int y), double r) ->
            "Circle centered at (" + x + ", " + y + ") with radius " + r;

        default -> "Unknown";
    };
}
```

### Null Handling

```java
// Explicit null case
switch (obj) {
    case null -> handleNull();
    case String s -> handleString(s);
    default -> handleOther(obj);
}

// Combined with default
switch (obj) {
    case String s -> handleString(s);
    case null, default -> handleOther(obj);  // null + default combined
}
```

---

## Unnamed Variables and Patterns

### In catch blocks

```java
try {
    return Integer.parseInt(input);
} catch (NumberFormatException _) {  // Don't need exception details
    return defaultValue;
}
```

### In lambdas

```java
map.forEach((_, value) -> process(value));  // Ignore key

list.removeIf(_ -> random.nextBoolean());   // Ignore element
```

### In patterns

```java
// Ignore some components
case Point(int x, _) -> "x is " + x;  // Ignore y

// Multiple ignored
case Rectangle(_, _) -> "some rectangle";
```

### In enhanced for loops

```java
int count = 0;
for (var _ : collection) {  // Just counting
    count++;
}
```

---

## Switch Expressions vs Statements

### Expression (returns value)

```java
String result = switch (day) {
    case MONDAY, FRIDAY -> "Work";
    case SATURDAY, SUNDAY -> "Weekend";
    default -> "Midweek";
};
```

### With yield (for blocks)

```java
String result = switch (status) {
    case SUCCESS -> "OK";
    case ERROR -> {
        log.error("Error occurred");
        yield "FAILED";  // yield returns value from block
    }
    default -> "UNKNOWN";
};
```

### Exhaustiveness

```java
// Sealed types - no default needed
sealed interface Result permits Success, Failure {}
record Success(String data) implements Result {}
record Failure(String error) implements Result {}

String handle(Result result) {
    return switch (result) {
        case Success(String data) -> "Data: " + data;
        case Failure(String error) -> "Error: " + error;
        // No default - compiler knows all cases
    };
}
```
