# Behavioral Design Patterns — State & Notification

> Patterns that model observable change, finite state, snapshots, and operations over
> closed type hierarchies: Observer, Visitor (with pattern matching), State, Memento.
> Classic GoF forms paired with modern-Java idioms (sealed types, records, pattern matching, Flow API).

---

## Table of Contents

1. [Observer Pattern](#observer-pattern)
2. [Visitor Pattern (with Pattern Matching)](#visitor-pattern-with-pattern-matching)
3. [State Pattern](#state-pattern)
4. [Memento Pattern](#memento-pattern)

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
