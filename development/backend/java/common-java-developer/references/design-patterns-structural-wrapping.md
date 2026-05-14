# Structural Design Patterns — Wrapping

> Patterns that wrap one object behind another: Adapter, Decorator, Facade, Proxy.
> Classic GoF forms paired with modern-Java idioms (function composition, dynamic proxies).

---

## Table of Contents

1. [Adapter Pattern](#adapter-pattern)
2. [Decorator Pattern](#decorator-pattern)
3. [Facade Pattern](#facade-pattern)
4. [Proxy Pattern](#proxy-pattern)

---

## Adapter Pattern

### 🟢 When to use
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

## Decorator Pattern

### 🟢 When to use
- Add responsibilities dynamically
- Alternative to subclassing
- Combine behaviors flexibly

### Classic form: class hierarchy

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

### Modern alternative: Function composition

Use `Function` and `andThen()` for lightweight decoration of stateless transformations.

```java
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

### 🟢 Choosing between class decorator and function composition

| Scenario | Use |
|----------|-----|
| Simple transformations | Function composition |
| Stateless operations | Function composition |
| Need to track applied decorators | Class decorator |
| Complex behavior with dependencies | Class decorator |
| Runtime decorator inspection | Class decorator |

---

## Facade Pattern

### 🟢 When to use
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

---

## Proxy Pattern

### 🟢 When to use
- Lazy initialization (virtual proxy)
- Access control (protection proxy)
- Logging/monitoring (logging proxy)
- Caching (caching proxy)
- Remote object access (remote proxy)

### Virtual Proxy — lazy loading

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
```

### Protection Proxy — access control

```java
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
```

### Modern: Dynamic Proxy for logging/metrics

```java
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
