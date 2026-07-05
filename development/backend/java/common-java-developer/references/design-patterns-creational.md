# Creational Design Patterns

> Object creation patterns: Builder, Factory Method, Abstract Factory, Singleton.
> Classic GoF forms paired with modern-Java idioms (records, sealed types, enums, `Consumer`-based builders).

---

## Table of Contents

1. [Builder Pattern](#builder-pattern)
2. [Factory Method Pattern](#factory-method-pattern)
3. [Abstract Factory Pattern](#abstract-factory-pattern)
4. [Singleton Pattern](#singleton-pattern)

---

## Builder Pattern

### 🟢 When to use
- Many constructor parameters (> 3-4)
- Optional parameters
- Step-by-step object construction
- Immutable objects

### Classic form (static inner Builder)

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

### Modern alternative: Consumer-based Builder with Records

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

---

## Factory Method Pattern

### 🟢 When to use
- Subclasses should decide which class to instantiate
- Decouple client from concrete classes
- Extensible object creation

### Classic form

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

### Modern Java with Sealed Types

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

**Why sealed types matter:** the compiler enforces exhaustiveness on the switch — adding a new `permits` member without updating `create` becomes a compile error.

---

## Abstract Factory Pattern

### 🟢 When to use
- Create families of related objects
- Ensure products from same family are used together
- Hide concrete classes from client

### Modern Java with Method References + Switch

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

---

## Singleton Pattern

### 🟢 When to use
- Exactly one instance needed (config, cache, connection pool)
- Global access point required

### 🟢 Preferred: Enum singleton (thread-safe, serialization-safe)

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

### Alternative: Static holder (lazy initialization)

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

### 🔴 Avoid: Double-Checked Locking without `volatile`

**Why:** Without `volatile`, JIT instruction reordering can publish a partially-constructed instance to another thread. Use enum or static holder instead. See `pitfalls-runtime.md` § Double-Checked Locking without `volatile` for the full anti-pattern.
