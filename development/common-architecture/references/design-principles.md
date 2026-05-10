# Design Principles Reference

## 🔴 CRITICAL - Always Apply

| # | Principle | Description |
|---|-----------|-------------|
| 1 | **Separation of Concerns** | Each component has one clear responsibility |
| 2 | **Dependency Inversion** | Depend on abstractions, not implementations |
| 3 | **High Cohesion** | Related things stay together |
| 4 | **Low Coupling** | Minimal dependencies between modules |
| 5 | **Explicit Boundaries** | Clear contracts at every boundary |

---

## 🟡 SOLID Principles

| Principle | Meaning | Violation Sign |
|-----------|---------|----------------|
| **S**ingle Responsibility | One reason to change | Class doing too many things |
| **O**pen/Closed | Open for extension, closed for modification | Modifying existing code for new features |
| **L**iskov Substitution | Subtypes must be substitutable | Override breaks parent behavior |
| **I**nterface Segregation | Many specific interfaces > one general | Implementing unused methods |
| **D**ependency Inversion | Depend on abstractions | Concrete classes in constructor |

---

## 🟢 Additional Principles

| # | Principle | Application |
|---|-----------|-------------|
| 6 | **Package by Feature** | Organize by business capability, not layer |
| 7 | **YAGNI** | Don't build it until you need it |
| 8 | **DRY** | Extract only when you see 3+ repetitions |
| 9 | **KISS** | Simplest solution that works |
| 10 | **Composition over Inheritance** | Prefer has-a over is-a |
| 11 | **Tell, Don't Ask** | Objects do work, don't expose data |
| 12 | **Law of Demeter** | Only talk to immediate friends |
| 13 | **Fail Fast** | Validate early, crash clearly |
| 14 | **Principle of Least Astonishment** | Behavior matches expectations |
| 15 | **Convention over Configuration** | Sensible defaults, minimal config |

---

## Domain-Driven Design Principles

| Principle | Application |
|-----------|-------------|
| **Ubiquitous Language** | Same terms in code and business discussions |
| **Bounded Context** | Clear boundaries between subdomains |
| **Aggregate** | Cluster of entities with consistency boundary |
| **Domain Events** | Capture "something happened" in the domain |
| **Anti-Corruption Layer** | Translate between bounded contexts |
