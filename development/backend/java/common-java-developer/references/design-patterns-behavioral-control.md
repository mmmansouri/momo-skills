# Behavioral Design Patterns — Control Flow

> Patterns that control how operations are selected, invoked, queued or chained:
> Strategy, Command, Chain of Responsibility, Template Method.
> Classic GoF forms paired with modern-Java idioms (functional interfaces, records, higher-order functions).

---

## Table of Contents

1. [Strategy Pattern](#strategy-pattern)
2. [Command Pattern](#command-pattern)
3. [Chain of Responsibility Pattern](#chain-of-responsibility-pattern)
4. [Template Method Pattern](#template-method-pattern)

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
