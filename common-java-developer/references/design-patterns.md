# Design Patterns in Modern Java

---

## Pattern Selection Decision Tree

```
What problem are you solving?
│
├── CREATING OBJECTS
│   ├── Many optional constructor params?
│   │   └── Builder (static inner class or Consumer-based)
│   │
│   ├── Object type varies based on input/config?
│   │   └── Factory Method (sealed + switch for type safety)
│   │
│   ├── Need families of related objects?
│   │   └── Abstract Factory (enum with Suppliers)
│   │
│   └── Exactly one instance needed globally?
│       └── Singleton (enum preferred, or static holder)
│
├── STRUCTURING OBJECTS
│   ├── Need to adapt incompatible interfaces?
│   │   └── Adapter (or Function<Old, New>)
│   │
│   ├── Add behavior without modifying class?
│   │   └── Decorator (or Function.andThen() composition)
│   │
│   ├── Simplify complex subsystem?
│   │   └── Facade (single entry point class)
│   │
│   ├── Control access, lazy load, or log?
│   │   └── Proxy (static or dynamic Proxy.newProxyInstance)
│   │
│   ├── Tree/hierarchical structure?
│   │   └── Composite (sealed interface + records)
│   │
│   └── Many similar objects, memory critical?
│       └── Flyweight (factory + ConcurrentHashMap cache)
│
└── MANAGING BEHAVIOR
    ├── Algorithm varies at runtime?
    │   └── Strategy (Map<Type, Lambda> registry)
    │
    ├── Need to notify on state changes?
    │   └── Observer (Consumer<T> listeners)
    │
    ├── Need undo/redo or queue operations?
    │   └── Command (record as command + Deque history)
    │
    ├── Pass request through filters/middleware?
    │   └── Chain of Responsibility (Handler.orElse() chain)
    │
    ├── Fixed algorithm, variable steps?
    │   └── Template Method (abstract class or functional builder)
    │
    ├── Operations on closed type hierarchy?
    │   └── Visitor → Use sealed classes + pattern matching instead!
    │
    ├── Object behavior changes with state?
    │   └── State (sealed interface + record states, or enum)
    │
    └── Need to save/restore object state?
        └── Memento (record as immutable snapshot)
```

---

## When to Use Which Pattern

### Quick Reference Table

| Scenario | Pattern | Category |
|----------|---------|----------|
| Many optional constructor params | **Builder** | Creational |
| Object creation varies by subclass | **Factory Method** | Creational |
| Single instance needed | **Singleton** | Creational |
| Convert incompatible interfaces | **Adapter** | Structural |
| Add behavior dynamically | **Decorator** | Structural |
| Simplify complex subsystems | **Facade** | Structural |
| Lazy loading, access control, logging | **Proxy** | Structural |
| Tree structures, recursive composition | **Composite** | Structural |
| Many similar objects, optimize memory | **Flyweight** | Structural |
| Algorithm varies at runtime | **Strategy** | Behavioral |
| Notify multiple observers | **Observer** | Behavioral |
| Undo/redo, queue operations | **Command** | Behavioral |
| Pass request along handler chain | **Chain of Responsibility** | Behavioral |
| Fixed algorithm, variable steps | **Template Method** | Behavioral |
| Operations on closed type hierarchy | **Visitor** | Behavioral |
| Object behavior changes with state | **State** | Behavioral |
| Save/restore object state | **Memento** | Behavioral |

---

## Modern Java Pattern Philosophy

> **"Many Gang of Four patterns were designed to solve problems that no longer exist in modern Java."**

### Key Replacements Summary

| Traditional Pattern | Modern Java Replacement |
|--------------------|------------------------|
| Strategy classes | `@FunctionalInterface` + lambdas + `Map.of()` registry |
| Builder boilerplate | Records + Consumer-based builder |
| Factory if-else | Sealed interfaces + exhaustive switch |
| Singleton DCL | Enum singleton (thread-safe, serialization-safe) |
| Observer interfaces | `Consumer<T>` + method references |
| Template abstract classes | Default methods in sealed interfaces |
| Visitor double-dispatch | Sealed classes + pattern matching |

### When Traditional Patterns Are Still Needed

- Complex state management across multiple objects
- Framework integration requiring specific interfaces
- Legacy code compatibility
- Team familiarity and maintainability

---

## Creational Patterns

### Builder Pattern

**When to use:**
- Many constructor parameters (> 3-4)
- Optional parameters
- Step-by-step object construction
- Immutable objects

```java
public class User {
    private final String email;      // required
    private final String name;       // required
    private final String phone;      // optional
    private final String address;    // optional

    private User(Builder builder) {
        this.email = builder.email;
        this.name = builder.name;
        this.phone = builder.phone;
        this.address = builder.address;
    }

    public static class Builder {
        // Required
        private final String email;
        private final String name;

        // Optional with defaults
        private String phone = "";
        private String address = "";

        public Builder(String email, String name) {
            this.email = Objects.requireNonNull(email);
            this.name = Objects.requireNonNull(name);
        }

        public Builder phone(String phone) {
            this.phone = phone;
            return this;
        }

        public Builder address(String address) {
            this.address = address;
            return this;
        }

        public User build() {
            return new User(this);
        }
    }

    // Usage
    public static void main(String[] args) {
        User user = new User.Builder("john@example.com", "John")
            .phone("555-1234")
            .address("123 Main St")
            .build();
    }
}
```

**Modern Alternative: Consumer-based Builder with Records**

```java
// Record with Consumer-based builder - minimal boilerplate
public record User(String email, String name, String phone, String address) {

    public static User of(Consumer<Builder> builderConsumer) {
        Builder builder = new Builder();
        builderConsumer.accept(builder);
        return new User(
            Objects.requireNonNull(builder.email, "Email required"),
            Objects.requireNonNull(builder.name, "Name required"),
            builder.phone != null ? builder.phone : "",
            builder.address != null ? builder.address : ""
        );
    }

    public static class Builder {
        public String email;
        public String name;
        public String phone;
        public String address;
    }
}

// Clean, expressive usage
User user = User.of(b -> {
    b.email = "john@example.com";
    b.name = "John";
    b.phone = "555-1234";
});
```

### Factory Method Pattern

**When to use:**
- Subclasses should decide which class to instantiate
- Decouple client from concrete classes
- Extensible object creation

```java
// Product interface
public interface Notification {
    void send(String message);
}

// Concrete products
public class EmailNotification implements Notification {
    public void send(String message) {
        // Send email
    }
}

public class SmsNotification implements Notification {
    public void send(String message) {
        // Send SMS
    }
}

// Factory
public class NotificationFactory {
    public static Notification create(String type) {
        return switch (type.toLowerCase()) {
            case "email" -> new EmailNotification();
            case "sms" -> new SmsNotification();
            default -> throw new IllegalArgumentException("Unknown type: " + type);
        };
    }
}
```

**Modern Java with Sealed Types:**

```java
public sealed interface Notification permits EmailNotification, SmsNotification {
    void send(String message);

    static Notification create(NotificationType type) {
        return switch (type) {
            case EMAIL -> new EmailNotification();
            case SMS -> new SmsNotification();
        };
    }
}
```

### Abstract Factory Pattern

**When to use:**
- Create families of related objects
- Ensure products from same family are used together
- Hide concrete classes from client

**Modern Java with Method References + Switch:**

```java
// Product interfaces
sealed interface Button permits WindowsButton, MacButton {}
sealed interface Checkbox permits WindowsCheckbox, MacCheckbox {}

record WindowsButton() implements Button {}
record MacButton() implements Button {}
record WindowsCheckbox() implements Checkbox {}
record MacCheckbox() implements Checkbox {}

// Modern Abstract Factory using method references
public enum UIFactory {
    WINDOWS(WindowsButton::new, WindowsCheckbox::new),
    MAC(MacButton::new, MacCheckbox::new);

    private final Supplier<Button> buttonFactory;
    private final Supplier<Checkbox> checkboxFactory;

    UIFactory(Supplier<Button> buttonFactory, Supplier<Checkbox> checkboxFactory) {
        this.buttonFactory = buttonFactory;
        this.checkboxFactory = checkboxFactory;
    }

    public Button createButton() { return buttonFactory.get(); }
    public Checkbox createCheckbox() { return checkboxFactory.get(); }

    // Factory selection
    public static UIFactory forOS(String os) {
        return switch (os.toLowerCase()) {
            case "windows" -> WINDOWS;
            case "mac", "macos" -> MAC;
            default -> throw new IllegalArgumentException("Unknown OS: " + os);
        };
    }
}

// Usage - clean and type-safe
UIFactory factory = UIFactory.forOS(System.getProperty("os.name"));
Button button = factory.createButton();
Checkbox checkbox = factory.createCheckbox();
```

### Singleton Pattern

**When to use:**
- Exactly one instance needed (config, cache, connection pool)
- Global access point required

```java
// Thread-safe singleton using enum (recommended)
public enum ConfigManager {
    INSTANCE;

    private final Properties properties = new Properties();

    ConfigManager() {
        loadProperties();
    }

    public String get(String key) {
        return properties.getProperty(key);
    }
}

// Usage
String value = ConfigManager.INSTANCE.get("app.name");
```

**Alternative: Static holder (lazy initialization)**

```java
public class ConfigManager {
    private ConfigManager() { }

    private static class Holder {
        private static final ConfigManager INSTANCE = new ConfigManager();
    }

    public static ConfigManager getInstance() {
        return Holder.INSTANCE;
    }
}
```

---

## Behavioral Patterns

### Strategy Pattern

**When to use:**
- Multiple algorithms for same task
- Algorithm selection at runtime
- Avoid conditional statements for algorithm selection

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

**Modern Java with Lambdas:**

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

**Modern Best Practice: Map-based Strategy Registry**

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

### Observer Pattern

**When to use:**
- One-to-many dependency between objects
- Event-driven systems
- Notification mechanisms

```java
// Modern Java using Flow API (Java 9+)
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

**Simple callback approach:**

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

### Command Pattern

**When to use:**
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

## Structural Patterns

### Decorator Pattern

**When to use:**
- Add responsibilities dynamically
- Alternative to subclassing
- Combine behaviors flexibly

```java
// Component interface
public interface DataSource {
    void writeData(String data);
    String readData();
}

// Concrete component
public class FileDataSource implements DataSource {
    private final String filename;

    public FileDataSource(String filename) {
        this.filename = filename;
    }

    public void writeData(String data) {
        // Write to file
    }

    public String readData() {
        // Read from file
        return "";
    }
}

// Base decorator
public abstract class DataSourceDecorator implements DataSource {
    protected final DataSource wrappee;

    public DataSourceDecorator(DataSource source) {
        this.wrappee = source;
    }

    public void writeData(String data) {
        wrappee.writeData(data);
    }

    public String readData() {
        return wrappee.readData();
    }
}

// Concrete decorators
public class EncryptionDecorator extends DataSourceDecorator {
    public EncryptionDecorator(DataSource source) {
        super(source);
    }

    public void writeData(String data) {
        super.writeData(encrypt(data));
    }

    public String readData() {
        return decrypt(super.readData());
    }
}

public class CompressionDecorator extends DataSourceDecorator {
    public CompressionDecorator(DataSource source) {
        super(source);
    }

    public void writeData(String data) {
        super.writeData(compress(data));
    }

    public String readData() {
        return decompress(super.readData());
    }
}

// Usage - combine decorators
DataSource source = new CompressionDecorator(
    new EncryptionDecorator(
        new FileDataSource("data.txt")
    )
);
source.writeData("sensitive data");  // Encrypted, then compressed
```

### Adapter Pattern

**When to use:**
- Make incompatible interfaces work together
- Reuse existing classes with incompatible interfaces
- Create a reusable class that works with unrelated classes

```java
// Target interface
public interface MediaPlayer {
    void play(String audioType, String fileName);
}

// Adaptee (existing class with different interface)
public class AdvancedMediaPlayer {
    public void playVlc(String fileName) { }
    public void playMp4(String fileName) { }
}

// Adapter
public class MediaAdapter implements MediaPlayer {
    private final AdvancedMediaPlayer advancedPlayer = new AdvancedMediaPlayer();

    public void play(String audioType, String fileName) {
        switch (audioType.toLowerCase()) {
            case "vlc" -> advancedPlayer.playVlc(fileName);
            case "mp4" -> advancedPlayer.playMp4(fileName);
        }
    }
}
```

---

## Modern Java Patterns (Java 17+)

### Visitor Pattern with Pattern Matching

**Traditional Visitor requires double dispatch. Modern Java eliminates this with sealed classes + pattern matching.**

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

### State Pattern with Sealed Classes

**Use sealed classes to define all possible states with compile-time safety.**

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

### State Pattern with Enum (Simpler Alternative)

**For simpler state machines, use enum with abstract methods.**

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

### Decorator Pattern with Function Composition

**Use `Function` and `andThen()` for lightweight decoration.**

```java
// Traditional decorator requires class hierarchy
// Modern Java uses function composition

import java.util.function.Function;
import java.util.function.UnaryOperator;

public class TextProcessing {
    // Individual transformations as functions
    static UnaryOperator<String> trim = String::trim;
    static UnaryOperator<String> lowercase = String::toLowerCase;
    static UnaryOperator<String> removeExtraSpaces = s -> s.replaceAll("\\s+", " ");
    static UnaryOperator<String> capitalize = s ->
        s.isEmpty() ? s : Character.toUpperCase(s.charAt(0)) + s.substring(1);

    // Compose decorators dynamically
    public static void main(String[] args) {
        UnaryOperator<String> normalizer = trim
            .andThen(lowercase)
            .andThen(removeExtraSpaces)
            .andThen(capitalize);

        String result = normalizer.apply("  HELLO    WORLD  ");  // "Hello world"
    }
}

// For more complex cases with state, use a pipeline builder
public class Pipeline<T> {
    private Function<T, T> pipeline = Function.identity();

    public Pipeline<T> add(Function<T, T> step) {
        pipeline = pipeline.andThen(step);
        return this;
    }

    public T execute(T input) {
        return pipeline.apply(input);
    }
}

// Usage
String result = new Pipeline<String>()
    .add(String::trim)
    .add(String::toLowerCase)
    .add(s -> s.replace(" ", "-"))
    .execute("  Hello World  ");  // "hello-world"
```

**When to use function composition vs class decorator:**
| Scenario | Use |
|----------|-----|
| Simple transformations | Function composition |
| Stateless operations | Function composition |
| Need to track applied decorators | Class decorator |
| Complex behavior with dependencies | Class decorator |
| Runtime decorator inspection | Class decorator |

---

## Additional Structural Patterns

### Facade Pattern

**When to use:**
- Simplify complex subsystem interfaces
- Reduce coupling between clients and subsystems
- Provide unified entry point to a set of interfaces

```java
// Complex subsystem classes
class OrderValidator {
    boolean validate(Order order) { /* complex validation */ return true; }
}

class InventoryService {
    void reserve(List<Item> items) { /* reserve stock */ }
    void release(List<Item> items) { /* release stock */ }
}

class PaymentProcessor {
    PaymentResult charge(PaymentInfo info, double amount) { /* process payment */ return null; }
}

class ShippingService {
    String createShippingLabel(Address address) { /* create label */ return "TRACK123"; }
}

class NotificationService {
    void sendOrderConfirmation(String email, String orderId) { /* send email */ }
}

// Facade - simplified interface for order processing
public class OrderFacade {
    private final OrderValidator validator;
    private final InventoryService inventory;
    private final PaymentProcessor payment;
    private final ShippingService shipping;
    private final NotificationService notification;

    public OrderFacade(OrderValidator validator, InventoryService inventory,
                       PaymentProcessor payment, ShippingService shipping,
                       NotificationService notification) {
        this.validator = validator;
        this.inventory = inventory;
        this.payment = payment;
        this.shipping = shipping;
        this.notification = notification;
    }

    // Single method hides all complexity
    public OrderResult processOrder(Order order) {
        // Step 1: Validate
        if (!validator.validate(order)) {
            return OrderResult.invalid("Validation failed");
        }

        // Step 2: Reserve inventory
        try {
            inventory.reserve(order.getItems());
        } catch (InsufficientStockException e) {
            return OrderResult.outOfStock(e.getMessage());
        }

        // Step 3: Process payment
        PaymentResult paymentResult = payment.charge(
            order.getPaymentInfo(),
            order.getTotal()
        );
        if (!paymentResult.isSuccessful()) {
            inventory.release(order.getItems());  // Rollback
            return OrderResult.paymentFailed(paymentResult.getError());
        }

        // Step 4: Create shipping
        String trackingNumber = shipping.createShippingLabel(order.getShippingAddress());

        // Step 5: Notify customer
        notification.sendOrderConfirmation(order.getCustomerEmail(), order.getId());

        return OrderResult.success(order.getId(), trackingNumber);
    }
}

// Client code is now simple
OrderResult result = orderFacade.processOrder(order);
```

### Proxy Pattern

**When to use:**
- Lazy initialization (virtual proxy)
- Access control (protection proxy)
- Logging/monitoring (logging proxy)
- Caching (caching proxy)
- Remote object access (remote proxy)

```java
// Subject interface
interface Image {
    void display();
    int getWidth();
    int getHeight();
}

// Real subject - expensive to create
class HighResolutionImage implements Image {
    private final String filename;
    private final byte[] data;

    HighResolutionImage(String filename) {
        this.filename = filename;
        this.data = loadFromDisk(filename);  // Expensive!
        System.out.println("Loaded: " + filename);
    }

    private byte[] loadFromDisk(String filename) {
        // Simulate expensive I/O operation
        return new byte[10_000_000];
    }

    @Override public void display() { /* render image */ }
    @Override public int getWidth() { return 1920; }
    @Override public int getHeight() { return 1080; }
}

// Virtual Proxy - lazy loading
class ImageProxy implements Image {
    private final String filename;
    private HighResolutionImage realImage;  // Lazy loaded

    ImageProxy(String filename) {
        this.filename = filename;  // Cheap - just store reference
    }

    @Override
    public void display() {
        if (realImage == null) {
            realImage = new HighResolutionImage(filename);  // Load on first use
        }
        realImage.display();
    }

    @Override public int getWidth() { return getRealImage().getWidth(); }
    @Override public int getHeight() { return getRealImage().getHeight(); }

    private HighResolutionImage getRealImage() {
        if (realImage == null) {
            realImage = new HighResolutionImage(filename);
        }
        return realImage;
    }
}

// Protection Proxy - access control
class SecuredDocumentProxy implements Document {
    private final Document realDocument;
    private final User currentUser;

    SecuredDocumentProxy(Document document, User user) {
        this.realDocument = document;
        this.currentUser = user;
    }

    @Override
    public String read() {
        if (!currentUser.hasPermission("READ")) {
            throw new AccessDeniedException("Read permission required");
        }
        return realDocument.read();
    }

    @Override
    public void write(String content) {
        if (!currentUser.hasPermission("WRITE")) {
            throw new AccessDeniedException("Write permission required");
        }
        realDocument.write(content);
    }
}

// Modern: Dynamic Proxy for logging/metrics
public class LoggingProxyFactory {
    @SuppressWarnings("unchecked")
    public static <T> T create(T target, Class<T> interfaceType) {
        return (T) Proxy.newProxyInstance(
            interfaceType.getClassLoader(),
            new Class<?>[] { interfaceType },
            (proxy, method, args) -> {
                long start = System.nanoTime();
                try {
                    System.out.println("→ " + method.getName() + " called");
                    Object result = method.invoke(target, args);
                    System.out.println("← " + method.getName() + " returned: " + result);
                    return result;
                } finally {
                    long duration = System.nanoTime() - start;
                    System.out.println("⏱ " + method.getName() + " took " + duration / 1_000_000 + "ms");
                }
            }
        );
    }
}

// Usage
UserService proxied = LoggingProxyFactory.create(realUserService, UserService.class);
proxied.findById("123");  // Automatically logged with timing
```

### Composite Pattern

**When to use:**
- Tree structures (file systems, org charts, UI components)
- Treat individual objects and compositions uniformly
- Recursive structures

```java
// Component - common interface
sealed interface FileSystemNode permits File, Directory {
    String getName();
    long getSize();
    void print(String indent);
}

// Leaf
record File(String name, long size) implements FileSystemNode {
    @Override
    public String getName() { return name; }

    @Override
    public long getSize() { return size; }

    @Override
    public void print(String indent) {
        System.out.println(indent + "📄 " + name + " (" + formatSize(size) + ")");
    }

    private String formatSize(long bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return bytes / 1024 + " KB";
        return bytes / (1024 * 1024) + " MB";
    }
}

// Composite
record Directory(String name, List<FileSystemNode> children) implements FileSystemNode {
    // Defensive copy in compact constructor
    public Directory {
        children = List.copyOf(children);
    }

    @Override
    public String getName() { return name; }

    @Override
    public long getSize() {
        return children.stream()
            .mapToLong(FileSystemNode::getSize)
            .sum();
    }

    @Override
    public void print(String indent) {
        System.out.println(indent + "📁 " + name + "/");
        children.forEach(child -> child.print(indent + "  "));
    }

    // Builder for mutable construction phase
    public static Builder builder(String name) {
        return new Builder(name);
    }

    public static class Builder {
        private final String name;
        private final List<FileSystemNode> children = new ArrayList<>();

        Builder(String name) { this.name = name; }

        public Builder addFile(String name, long size) {
            children.add(new File(name, size));
            return this;
        }

        public Builder addDirectory(Directory dir) {
            children.add(dir);
            return this;
        }

        public Directory build() {
            return new Directory(name, children);
        }
    }
}

// Usage
Directory root = Directory.builder("project")
    .addFile("README.md", 1024)
    .addFile("pom.xml", 2048)
    .addDirectory(
        Directory.builder("src")
            .addFile("Main.java", 4096)
            .addFile("Utils.java", 2048)
            .build()
    )
    .addDirectory(
        Directory.builder("test")
            .addFile("MainTest.java", 3072)
            .build()
    )
    .build();

root.print("");  // Prints tree structure
System.out.println("Total size: " + root.getSize());  // Recursive calculation

// Pattern matching with composite
long countJavaFiles(FileSystemNode node) {
    return switch (node) {
        case File(String name, _) when name.endsWith(".java") -> 1;
        case File _ -> 0;
        case Directory(_, List<FileSystemNode> children) ->
            children.stream().mapToLong(this::countJavaFiles).sum();
    };
}
```

### Flyweight Pattern

**When to use:**
- Large number of similar objects
- Objects share significant common state
- Memory optimization is critical

```java
// Flyweight - immutable shared state (intrinsic)
record TreeType(String name, String color, String texture, byte[] meshData) {
    void draw(Graphics g, int x, int y) {
        // Use shared meshData to render at specific position (extrinsic state)
        g.drawTree(meshData, x, y, color);
    }
}

// Flyweight Factory
class TreeTypeFactory {
    private static final Map<String, TreeType> cache = new ConcurrentHashMap<>();

    public static TreeType getTreeType(String name, String color, String texture) {
        String key = name + "_" + color + "_" + texture;
        return cache.computeIfAbsent(key, k -> {
            byte[] meshData = loadMeshData(name);  // Expensive, done once
            return new TreeType(name, color, texture, meshData);
        });
    }

    private static byte[] loadMeshData(String name) {
        // Load 3D mesh data from file - expensive operation
        return new byte[100_000];  // Simulated heavy data
    }
}

// Context - contains extrinsic state (position)
record Tree(int x, int y, TreeType type) {
    void draw(Graphics g) {
        type.draw(g, x, y);  // Delegate to flyweight with position
    }
}

// Client - forest with millions of trees
class Forest {
    private final List<Tree> trees = new ArrayList<>();

    public void plantTree(int x, int y, String name, String color, String texture) {
        // Get shared flyweight - memory efficient!
        TreeType type = TreeTypeFactory.getTreeType(name, color, texture);
        trees.add(new Tree(x, y, type));
    }

    public void draw(Graphics g) {
        trees.forEach(tree -> tree.draw(g));
    }

    // Memory savings example:
    // 1,000,000 trees with 3 tree types
    // Without flyweight: 1,000,000 × 100KB = 100GB
    // With flyweight: 3 × 100KB + 1,000,000 × 12B = 300KB + 12MB ≈ 12MB
}

// Java's built-in flyweights
String s1 = "hello".intern();  // String pool
String s2 = "hello".intern();
assert s1 == s2;  // Same object

Integer i1 = Integer.valueOf(100);  // Integer cache (-128 to 127)
Integer i2 = Integer.valueOf(100);
assert i1 == i2;  // Same object
```

---

## Additional Behavioral Patterns

### Chain of Responsibility Pattern

**When to use:**
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

### Template Method Pattern

**When to use:**
- Algorithm structure is fixed, but steps vary
- Common behavior in base class, specifics in subclasses
- "Don't call us, we'll call you" (Hollywood Principle)

```java
// Traditional approach with abstract class
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

// Modern functional approach - template as higher-order function
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

### Memento Pattern

**When to use:**
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
