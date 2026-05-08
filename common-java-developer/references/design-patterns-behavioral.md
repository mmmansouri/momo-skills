# Behavioral Design Patterns

> Object-interaction patterns: Strategy, Observer, Command, Chain of Responsibility, Template Method, Visitor (with pattern matching), State (sealed + enum), Memento.
> Classic GoF forms paired with modern-Java idioms (functional interfaces, sealed types, records, pattern matching).

---

## Table of Contents

1. [Strategy Pattern](#strategy-pattern)
2. [Observer Pattern](#observer-pattern)
3. [Command Pattern](#command-pattern)
4. [Chain of Responsibility Pattern](#chain-of-responsibility-pattern)
5. [Template Method Pattern](#template-method-pattern)
6. [Visitor Pattern (with Pattern Matching)](#visitor-pattern-with-pattern-matching)
7. [State Pattern](#state-pattern)
8. [Memento Pattern](#memento-pattern)

---

## Strategy Pattern

### 🟢 When to use
- Multiple algorithms for same task
- Algorithm selection at runtime
- Avoid conditional statements for algorithm selection

### Classic form

```java
// Strategy interface
public interface PaymentStrategy {
    void pay(double amount);
}

// Concrete strategies
public class CreditCardPayment implements PaymentStrategy {
    private final String cardNumber;

    public CreditCardPayment(String cardNumber) {
        this.cardNumber = cardNumber;
    }

    public void pay(double amount) {
        // Process credit card
    }
}

public class PayPalPayment implements PaymentStrategy {
    private final String email;

    public PayPalPayment(String email) {
        this.email = email;
    }

    public void pay(double amount) {
        // Process PayPal
    }
}

// Context
public class ShoppingCart {
    private PaymentStrategy paymentStrategy;

    public void setPaymentStrategy(PaymentStrategy strategy) {
        this.paymentStrategy = strategy;
    }

    public void checkout(double total) {
        paymentStrategy.pay(total);
    }
}
```

### Modern Java with Lambdas

```java
// Strategy as functional interface
@FunctionalInterface
public interface PaymentStrategy {
    void pay(double amount);
}

// Usage with lambdas
PaymentStrategy creditCard = amount -> processCreditCard(amount);
PaymentStrategy paypal = amount -> processPayPal(amount);

cart.setPaymentStrategy(creditCard);
cart.checkout(100.0);
```

### 🟢 Modern Best Practice: Map-based Strategy Registry

```java
// Type-safe enum for strategy keys
public enum PaymentType { CREDIT_CARD, PAYPAL, APPLE_PAY, CRYPTO }

// Immutable strategy registry - no if-else, no switch
public class PaymentProcessor {
    private static final Map<PaymentType, PaymentStrategy> STRATEGIES = Map.of(
        PaymentType.CREDIT_CARD, amount -> processCreditCard(amount),
        PaymentType.PAYPAL, amount -> processPayPal(amount),
        PaymentType.APPLE_PAY, amount -> processApplePay(amount),
        PaymentType.CRYPTO, amount -> processCrypto(amount)
    );

    public void process(PaymentType type, double amount) {
        STRATEGIES.getOrDefault(type, a -> {
            throw new UnsupportedOperationException("Unknown payment: " + type);
        }).pay(amount);
    }

    // Or with Optional for cleaner error handling
    public Optional<PaymentStrategy> getStrategy(PaymentType type) {
        return Optional.ofNullable(STRATEGIES.get(type));
    }
}

// Usage - clean and type-safe
processor.process(PaymentType.CREDIT_CARD, 99.99);

// With method references for existing methods
Map<PaymentType, PaymentStrategy> strategies = Map.of(
    PaymentType.CREDIT_CARD, paymentService::chargeCreditCard,
    PaymentType.PAYPAL, paymentService::chargePayPal
);
```

---

## Observer Pattern

### 🟢 When to use
- One-to-many dependency between objects
- Event-driven systems
- Notification mechanisms

### Modern Java using Flow API (Java 9+)

```java
import java.util.concurrent.Flow.*;

public class EventPublisher implements Publisher<Event> {
    private final List<Subscriber<? super Event>> subscribers = new ArrayList<>();

    public void subscribe(Subscriber<? super Event> subscriber) {
        subscribers.add(subscriber);
        subscriber.onSubscribe(new Subscription() {
            public void request(long n) { }
            public void cancel() { subscribers.remove(subscriber); }
        });
    }

    public void publish(Event event) {
        subscribers.forEach(s -> s.onNext(event));
    }
}

// Subscriber
public class EventLogger implements Subscriber<Event> {
    public void onSubscribe(Subscription subscription) { }
    public void onNext(Event event) { log(event); }
    public void onError(Throwable throwable) { }
    public void onComplete() { }
}
```

### Simple callback approach

```java
public interface EventListener {
    void onEvent(Event event);
}

public class EventEmitter {
    private final List<EventListener> listeners = new CopyOnWriteArrayList<>();

    public void addListener(EventListener listener) {
        listeners.add(listener);
    }

    public void emit(Event event) {
        listeners.forEach(l -> l.onEvent(event));
    }
}

// Usage with lambdas
emitter.addListener(event -> log.info("Received: {}", event));
```

---

## Command Pattern

### 🟢 When to use
- Parameterize objects with operations
- Queue operations
- Support undo/redo

```java
// Command interface
@FunctionalInterface
public interface Command {
    void execute();
}

// With undo support
public interface UndoableCommand extends Command {
    void undo();
}

// Concrete command
public class AddItemCommand implements UndoableCommand {
    private final ShoppingCart cart;
    private final Item item;

    public AddItemCommand(ShoppingCart cart, Item item) {
        this.cart = cart;
        this.item = item;
    }

    public void execute() {
        cart.add(item);
    }

    public void undo() {
        cart.remove(item);
    }
}

// Command history for undo
public class CommandHistory {
    private final Deque<UndoableCommand> history = new ArrayDeque<>();

    public void execute(UndoableCommand command) {
        command.execute();
        history.push(command);
    }

    public void undo() {
        if (!history.isEmpty()) {
            history.pop().undo();
        }
    }
}
```

---

## Chain of Responsibility Pattern

### 🟢 When to use
- Multiple handlers can process a request
- Handler isn't known in advance
- Request should be passed along a chain
- Middleware, filters, validation pipelines

```java
// Modern functional approach
@FunctionalInterface
interface Handler<T, R> {
    Optional<R> handle(T request);

    default Handler<T, R> orElse(Handler<T, R> next) {
        return request -> this.handle(request)
            .or(() -> next.handle(request));
    }
}

// Request and Response types
record HttpRequest(String path, String method, Map<String, String> headers, String body) {}
record HttpResponse(int status, String body) {}

// Handlers as lambdas
class RequestHandlers {
    // Authentication check
    static Handler<HttpRequest, HttpResponse> auth = request -> {
        if (!request.headers().containsKey("Authorization")) {
            return Optional.of(new HttpResponse(401, "Unauthorized"));
        }
        return Optional.empty();  // Pass to next handler
    };

    // Rate limiting
    static Handler<HttpRequest, HttpResponse> rateLimit = request -> {
        if (isRateLimited(request)) {
            return Optional.of(new HttpResponse(429, "Too Many Requests"));
        }
        return Optional.empty();
    };

    // Validation
    static Handler<HttpRequest, HttpResponse> validation = request -> {
        if (request.body() == null || request.body().isBlank()) {
            return Optional.of(new HttpResponse(400, "Body required"));
        }
        return Optional.empty();
    };

    // Actual processing (terminal handler)
    static Handler<HttpRequest, HttpResponse> processor = request ->
        Optional.of(new HttpResponse(200, "Processed: " + request.body()));

    private static boolean isRateLimited(HttpRequest request) {
        return false;  // Simplified
    }
}

// Build pipeline
Handler<HttpRequest, HttpResponse> pipeline = RequestHandlers.auth
    .orElse(RequestHandlers.rateLimit)
    .orElse(RequestHandlers.validation)
    .orElse(RequestHandlers.processor);

// Process request
HttpResponse response = pipeline.handle(request).orElseThrow();

// Alternative: List-based chain (more flexible)
class FilterChain<T, R> {
    private final List<Handler<T, R>> handlers = new ArrayList<>();
    private final Handler<T, R> defaultHandler;

    public FilterChain(Handler<T, R> defaultHandler) {
        this.defaultHandler = defaultHandler;
    }

    public FilterChain<T, R> addFilter(Handler<T, R> handler) {
        handlers.add(handler);
        return this;
    }

    public R process(T request) {
        return handlers.stream()
            .map(h -> h.handle(request))
            .filter(Optional::isPresent)
            .map(Optional::get)
            .findFirst()
            .orElseGet(() -> defaultHandler.handle(request).orElseThrow());
    }
}
```

---

## Template Method Pattern

### 🟢 When to use
- Algorithm structure is fixed, but steps vary
- Common behavior in base class, specifics in subclasses
- "Don't call us, we'll call you" (Hollywood Principle)

### Classic form (abstract class)

```java
abstract class DataExporter {
    // Template method - final to prevent override
    public final void export(List<Record> records) {
        validateRecords(records);
        String header = createHeader();
        List<String> rows = records.stream()
            .map(this::formatRecord)
            .toList();
        String footer = createFooter(records.size());
        writeOutput(header, rows, footer);
        cleanup();
    }

    // Common implementation
    private void validateRecords(List<Record> records) {
        if (records == null || records.isEmpty()) {
            throw new IllegalArgumentException("Records cannot be empty");
        }
    }

    // Abstract methods - must be implemented
    protected abstract String createHeader();
    protected abstract String formatRecord(Record record);
    protected abstract void writeOutput(String header, List<String> rows, String footer);

    // Hook methods - optional override
    protected String createFooter(int count) {
        return "Total records: " + count;
    }

    protected void cleanup() {
        // Default: do nothing
    }
}

// CSV implementation
class CsvExporter extends DataExporter {
    private final Path outputPath;

    CsvExporter(Path outputPath) {
        this.outputPath = outputPath;
    }

    @Override
    protected String createHeader() {
        return "id,name,email,created_at";
    }

    @Override
    protected String formatRecord(Record record) {
        return String.join(",",
            record.id(),
            escapeCSV(record.name()),
            record.email(),
            record.createdAt().toString()
        );
    }

    @Override
    protected void writeOutput(String header, List<String> rows, String footer) {
        List<String> lines = new ArrayList<>();
        lines.add(header);
        lines.addAll(rows);
        lines.add("# " + footer);
        Files.write(outputPath, lines);
    }

    private String escapeCSV(String value) {
        return value.contains(",") ? "\"" + value + "\"" : value;
    }
}
```

### Modern functional approach — template as higher-order function

```java
class DataPipeline<T, R> {
    private final Function<T, R> reader;
    private final Function<R, R> transformer;
    private final Consumer<R> writer;
    private Runnable beforeHook = () -> {};
    private Runnable afterHook = () -> {};

    private DataPipeline(Function<T, R> reader, Function<R, R> transformer, Consumer<R> writer) {
        this.reader = reader;
        this.transformer = transformer;
        this.writer = writer;
    }

    public static <T, R> Builder<T, R> builder() {
        return new Builder<>();
    }

    public void execute(T input) {
        beforeHook.run();
        try {
            R data = reader.apply(input);
            R transformed = transformer.apply(data);
            writer.accept(transformed);
        } finally {
            afterHook.run();
        }
    }

    public static class Builder<T, R> {
        private Function<T, R> reader;
        private Function<R, R> transformer = Function.identity();
        private Consumer<R> writer;
        private Runnable beforeHook = () -> {};
        private Runnable afterHook = () -> {};

        public Builder<T, R> reader(Function<T, R> reader) {
            this.reader = reader;
            return this;
        }

        public Builder<T, R> transformer(Function<R, R> transformer) {
            this.transformer = transformer;
            return this;
        }

        public Builder<T, R> writer(Consumer<R> writer) {
            this.writer = writer;
            return this;
        }

        public Builder<T, R> before(Runnable hook) {
            this.beforeHook = hook;
            return this;
        }

        public Builder<T, R> after(Runnable hook) {
            this.afterHook = hook;
            return this;
        }

        public DataPipeline<T, R> build() {
            Objects.requireNonNull(reader, "Reader is required");
            Objects.requireNonNull(writer, "Writer is required");
            DataPipeline<T, R> pipeline = new DataPipeline<>(reader, transformer, writer);
            pipeline.beforeHook = beforeHook;
            pipeline.afterHook = afterHook;
            return pipeline;
        }
    }
}

// Usage
DataPipeline.<Path, List<String>>builder()
    .reader(path -> Files.readAllLines(path))
    .transformer(lines -> lines.stream()
        .map(String::toUpperCase)
        .toList())
    .writer(lines -> Files.write(Path.of("output.txt"), lines))
    .before(() -> log.info("Starting export"))
    .after(() -> log.info("Export complete"))
    .build()
    .execute(Path.of("input.txt"));
```

---

## Visitor Pattern (with Pattern Matching)

### 🟢 When to use
- Operations on closed type hierarchy
- Multiple unrelated operations on the same data structure
- Without modifying the data classes

### 🔴 Avoid: classic double-dispatch boilerplate

**Why:** Modern Java replaces the visitor interface + accept method ceremony with sealed types + an exhaustive switch — same compile-time guarantees, no double dispatch.

```java
// ❌ OLD WAY - Visitor with double dispatch (verbose)
interface ExprVisitor<T> {
    T visit(Num num);
    T visit(Add add);
    T visit(Mul mul);
}
interface Expr {
    <T> T accept(ExprVisitor<T> visitor);
}

// ✅ MODERN WAY - Sealed classes + pattern matching (no double dispatch!)
public sealed interface Expr permits Num, Add, Mul {}

public record Num(int value) implements Expr {}
public record Add(Expr left, Expr right) implements Expr {}
public record Mul(Expr left, Expr right) implements Expr {}

// Operations as simple methods with exhaustive switch
public class ExprEvaluator {
    public static int evaluate(Expr expr) {
        return switch (expr) {
            case Num(int v) -> v;
            case Add(Expr l, Expr r) -> evaluate(l) + evaluate(r);
            case Mul(Expr l, Expr r) -> evaluate(l) * evaluate(r);
        };
    }

    public static String print(Expr expr) {
        return switch (expr) {
            case Num(int v) -> String.valueOf(v);
            case Add(Expr l, Expr r) -> "(%s + %s)".formatted(print(l), print(r));
            case Mul(Expr l, Expr r) -> "(%s * %s)".formatted(print(l), print(r));
        };
    }
}

// Usage
Expr expr = new Add(new Num(1), new Mul(new Num(2), new Num(3)));
int result = ExprEvaluator.evaluate(expr);  // 7
String printed = ExprEvaluator.print(expr); // (1 + (2 * 3))
```

**Benefits:**
- No visitor interface boilerplate
- Compiler enforces exhaustiveness
- Pattern matching extracts data directly
- Adding new operations is trivial (just add a new method)

---

## State Pattern

### 🟢 When to use
- Object behavior changes with state
- State-specific logic belongs to that state
- State transitions must be explicit and validated

### 🟢 Sealed classes — full state machine with compile-time safety

```java
// State as sealed interface
public sealed interface OrderState
    permits Created, Paid, Shipped, Delivered, Cancelled {

    OrderState pay();
    OrderState ship();
    OrderState deliver();
    OrderState cancel();
}

// Each state as a record (immutable)
public record Created() implements OrderState {
    public OrderState pay() { return new Paid(); }
    public OrderState ship() { throw new IllegalStateException("Cannot ship unpaid order"); }
    public OrderState deliver() { throw new IllegalStateException("Cannot deliver unshipped order"); }
    public OrderState cancel() { return new Cancelled(); }
}

public record Paid() implements OrderState {
    public OrderState pay() { throw new IllegalStateException("Already paid"); }
    public OrderState ship() { return new Shipped(); }
    public OrderState deliver() { throw new IllegalStateException("Cannot deliver unshipped order"); }
    public OrderState cancel() { return new Cancelled(); }
}

public record Shipped() implements OrderState {
    public OrderState pay() { throw new IllegalStateException("Already paid"); }
    public OrderState ship() { throw new IllegalStateException("Already shipped"); }
    public OrderState deliver() { return new Delivered(); }
    public OrderState cancel() { throw new IllegalStateException("Cannot cancel shipped order"); }
}

public record Delivered() implements OrderState {
    public OrderState pay() { throw new IllegalStateException("Order complete"); }
    public OrderState ship() { throw new IllegalStateException("Order complete"); }
    public OrderState deliver() { throw new IllegalStateException("Already delivered"); }
    public OrderState cancel() { throw new IllegalStateException("Cannot cancel delivered order"); }
}

public record Cancelled() implements OrderState {
    public OrderState pay() { throw new IllegalStateException("Order cancelled"); }
    public OrderState ship() { throw new IllegalStateException("Order cancelled"); }
    public OrderState deliver() { throw new IllegalStateException("Order cancelled"); }
    public OrderState cancel() { throw new IllegalStateException("Already cancelled"); }
}

// Context with pattern matching for state-specific behavior
public class Order {
    private OrderState state = new Created();

    public void transition(String action) {
        state = switch (action) {
            case "pay" -> state.pay();
            case "ship" -> state.ship();
            case "deliver" -> state.deliver();
            case "cancel" -> state.cancel();
            default -> throw new IllegalArgumentException("Unknown action: " + action);
        };
    }

    public String getStatus() {
        return switch (state) {
            case Created _ -> "Awaiting payment";
            case Paid _ -> "Payment received, preparing";
            case Shipped _ -> "In transit";
            case Delivered _ -> "Delivered";
            case Cancelled _ -> "Cancelled";
        };
    }
}
```

### 🟢 Enum — simpler alternative for fixed cycles

For simple state machines with a fixed transition cycle and no per-state data, prefer enum with abstract methods.

```java
public enum TrafficLight {
    RED {
        @Override public TrafficLight next() { return GREEN; }
        @Override public int duration() { return 30; }
    },
    GREEN {
        @Override public TrafficLight next() { return YELLOW; }
        @Override public int duration() { return 25; }
    },
    YELLOW {
        @Override public TrafficLight next() { return RED; }
        @Override public int duration() { return 5; }
    };

    public abstract TrafficLight next();
    public abstract int duration();
}

// Usage
TrafficLight light = TrafficLight.RED;
light = light.next();  // GREEN
```

### Choosing between sealed records and enums

| Need | Use |
|------|-----|
| State carries data (e.g., `Paid(timestamp, amount)`) | Sealed records |
| Per-state behavior is significant | Sealed records |
| Fixed cyclic transitions, no per-state data | Enum |
| Compact implementation | Enum |

---

## Memento Pattern

### 🟢 When to use
- Capture and restore object state
- Implement undo/redo functionality
- Create snapshots without exposing internals

```java
// Memento - immutable snapshot (use record!)
record EditorMemento(String content, int cursorPosition, Instant timestamp) {}

// Originator - creates and restores from mementos
class TextEditor {
    private String content = "";
    private int cursorPosition = 0;

    public void type(String text) {
        content = content.substring(0, cursorPosition)
                + text
                + content.substring(cursorPosition);
        cursorPosition += text.length();
    }

    public void delete(int count) {
        int start = Math.max(0, cursorPosition - count);
        content = content.substring(0, start) + content.substring(cursorPosition);
        cursorPosition = start;
    }

    public void moveCursor(int position) {
        cursorPosition = Math.max(0, Math.min(position, content.length()));
    }

    // Create memento
    public EditorMemento save() {
        return new EditorMemento(content, cursorPosition, Instant.now());
    }

    // Restore from memento
    public void restore(EditorMemento memento) {
        this.content = memento.content();
        this.cursorPosition = memento.cursorPosition();
    }

    public String getContent() { return content; }
}

// Caretaker - manages memento history
class EditorHistory {
    private final Deque<EditorMemento> undoStack = new ArrayDeque<>();
    private final Deque<EditorMemento> redoStack = new ArrayDeque<>();
    private final TextEditor editor;

    public EditorHistory(TextEditor editor) {
        this.editor = editor;
    }

    public void save() {
        undoStack.push(editor.save());
        redoStack.clear();  // Clear redo after new action
    }

    public void undo() {
        if (!undoStack.isEmpty()) {
            redoStack.push(editor.save());  // Save current for redo
            editor.restore(undoStack.pop());
        }
    }

    public void redo() {
        if (!redoStack.isEmpty()) {
            undoStack.push(editor.save());
            editor.restore(redoStack.pop());
        }
    }

    public boolean canUndo() { return !undoStack.isEmpty(); }
    public boolean canRedo() { return !redoStack.isEmpty(); }
}

// Usage
TextEditor editor = new TextEditor();
EditorHistory history = new EditorHistory(editor);

history.save();
editor.type("Hello");
history.save();
editor.type(" World");
System.out.println(editor.getContent());  // "Hello World"

history.undo();
System.out.println(editor.getContent());  // "Hello"

history.redo();
System.out.println(editor.getContent());  // "Hello World"
```
