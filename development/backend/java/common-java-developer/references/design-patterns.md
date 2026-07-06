# Design Patterns in Modern Java

> Decision surface for the GoF + modern-Java pattern catalog. Pattern implementations are standard knowledge and are intentionally not restated — pick with the tree and tables below, then apply the modern-Java idiom.

---

## Table of Contents

1. [Pattern Selection Decision Tree](#pattern-selection-decision-tree)
2. [Quick Reference Table](#quick-reference-table)
3. [Modern Java Pattern Philosophy](#modern-java-pattern-philosophy)

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

## Quick Reference Table

| Scenario | Pattern | Category |
|----------|---------|----------|
| Many optional constructor params | **Builder** | Creational |
| Object creation varies by subclass | **Factory Method** | Creational |
| Families of related products | **Abstract Factory** | Creational |
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

### 🟢 Key Replacements Summary

| Traditional Pattern | Modern Java Replacement |
|--------------------|------------------------|
| Strategy classes | `@FunctionalInterface` + lambdas + `Map.of()` registry |
| Builder boilerplate | Records + Consumer-based builder |
| Factory if-else | Sealed interfaces + exhaustive switch |
| Singleton DCL | Enum singleton (thread-safe, serialization-safe) |
| Observer interfaces | `Consumer<T>` + method references |
| Template abstract classes | Default methods in sealed interfaces |
| Visitor double-dispatch | Sealed classes + pattern matching |

### 🟡 When Traditional Patterns Are Still Needed

- Complex state management across multiple objects
- Framework integration requiring specific interfaces
- Legacy code compatibility
- Team familiarity and maintainability
