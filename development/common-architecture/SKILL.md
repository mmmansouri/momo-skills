---
name: common-architecture
description: >-
  Application architecture decisions and system design. Use this skill whenever
  the user mentions architecture, system design, designing a new
  feature/module/service, choosing or evaluating an architectural style
  (Hexagonal, Clean, CQRS, Microservices, Event-Driven, Layered), trade-off
  analysis, ADRs (Architecture Decision Records), C4 diagrams,
  bounded contexts, package-by-feature, the dependency rule, or structuring
  code — even when the user does not explicitly say "architecture".
---

# Application Architecture Skill

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## When Reasoning About Architecture

Apply these foundational stances to every architectural decision:

1. **Domain-Centric** — Business logic at the center; technology serves the domain.
2. **Defer Decisions** — Delay technical choices until the constraints that drive them are concrete.
3. **Trade-offs Over Best Practices** — Every decision is a compromise. Document the trade-off, not the verdict.
4. **Testability First** — Good architecture makes testing easy. Hard-to-test code signals a structural defect.
5. **Evolutionary** — Architecture must evolve. Design boundaries that allow change without rewrite.

---

## When Starting Architecture Work

📚 **References:** [design-principles.md](references/design-principles.md)

Ask these questions before proposing any architecture:

| Category | Questions |
|----------|-----------|
| **Domain** | What is the core business problem? |
| **Scale** | Expected users, requests/sec, data volume? |
| **Team** | Size, skills, experience with patterns? |
| **Constraints** | Budget, timeline, compliance (GDPR, HIPAA, etc.)? |
| **Integration** | External systems, APIs, legacy? |
| **NFRs** | Priority: Performance, Security, Availability, Maintainability? |

---

## When Choosing Architectural Style

📚 **References:** [architectural-styles.md](references/architectural-styles.md) | [decision-framework.md](references/decision-framework.md)

| Context | Recommended Style |
|---------|-------------------|
| Small team, simple domain, MVP | **Modular Monolith** or **Layered** |
| Complex domain, business rules focus | **Hexagonal** or **Clean Architecture** |
| High read/write ratio imbalance | **CQRS** |
| Multiple teams, independent scaling | **Microservices** |
| Real-time, async requirements | **Event-Driven** |

### 🔴 BLOCKING

#### Never choose Microservices for an MVP — start with a modular monolith and extract services later
**Why:** distribution costs (network hops, eventual consistency, ops complexity) are amortized only at scale. Premature splitting produces a distributed monolith — harder to refactor than a modular monolith and slower to evolve under domain uncertainty.

#### Never skip domain analysis before selecting a style
**Why:** the chosen style must absorb the domain's irreducible complexity. Skipping analysis encodes hidden assumptions into the structure; they surface as expensive rework once the real domain shape becomes visible.

### 🟡 WARNING

#### Avoid the Golden Hammer — don't apply the same pattern to every context
**Why:** forcing one pattern into every context produces contortions where it doesn't fit. Pick the simplest pattern that solves each context's actual problem.

##### WRONG
```
All bounded contexts use Hexagonal — including a thin CRUD admin module
that has no domain logic and ends up with empty ports/adapters layers.
```
##### CORRECT
```
Order context (complex rules)  → Hexagonal.
Reporting (read-heavy)         → CQRS.
Admin (CRUD)                   → Layered.
Each context picks the style that fits its complexity.
```

---

## When Structuring Code

📚 **References:** [code-structures.md](references/code-structures.md)

### 🔴 BLOCKING

#### Package by Feature, not by Layer
**Why:** a feature change touches all layers. By-feature packaging keeps the change footprint local; by-layer packaging spreads the change across the codebase, creates merge conflicts, and obscures each bounded context's identity.

##### WRONG
```
src/
├── controllers/
│   ├── OrderController.java
│   └── ProductController.java
├── services/
│   ├── OrderService.java
│   └── ProductService.java
└── repositories/
    ├── OrderRepository.java
    └── ProductRepository.java
```
##### CORRECT
```
src/
├── order/
│   ├── OrderController.java
│   ├── OrderService.java
│   └── OrderRepository.java
└── product/
    ├── ProductController.java
    ├── ProductService.java
    └── ProductRepository.java
```

#### Apply the Dependency Rule — all dependencies point inward, toward the domain
**Why:** when the domain depends on infrastructure, replacing or testing infra forces touching the domain. Inward-only dependencies make the domain stable, independently testable, and survivable across infrastructure migrations.

#### Keep the domain framework-agnostic — no Spring/JPA/HTTP annotations in domain classes
**Why:** framework annotations couple domain logic to the framework's lifecycle, upgrade cycle, and runtime container. Pure domain classes survive framework migrations and run in plain unit tests without bootstrapping a container.

##### WRONG
```java
// In domain/model/Order.java — domain leaks JPA
@Entity
@Table(name = "orders")
public class Order {
    @Id @GeneratedValue
    private Long id;
    @Column private BigDecimal total;
}
```
##### CORRECT
```java
// In domain/model/Order.java — pure domain
public class Order {
    private final OrderId id;
    private Money total;
    public void addLine(OrderLine line) { /* invariants enforced here */ }
}

// In infrastructure/persistence/OrderJpaEntity.java — adapter owns the mapping
@Entity @Table(name = "orders")
class OrderJpaEntity { /* JPA mapping only, no business logic */ }
```

### 🟡 WARNING

#### Avoid an Anemic Domain Model — entities should carry behavior, not only data
**Why:** behavior on entities keeps invariants enforceable at the only place that owns the data. Extracting it to services scatters business rules and lets callers bypass them.

##### WRONG
```java
class Order { /* getters/setters only */ }
class OrderService {
    BigDecimal calculateTotal(Order order) { /* logic outside the entity */ }
}
```
##### CORRECT
```java
class Order {
    Money total() { /* logic owned by the entity that holds the lines */ }
    void addLine(OrderLine line) { /* enforces invariants */ }
}
```

### 🟢 BEST PRACTICE

- **Explicit Boundaries** — define clear contracts (interfaces) at every module boundary.
- **High Cohesion, Low Coupling** — keep related concepts together; minimize cross-module dependencies.

---

## When Documenting Decisions

📚 **References:** [adr-template.md](references/adr-template.md) | [decision-framework.md](references/decision-framework.md)

### 🔴 BLOCKING

#### Every significant architectural decision must produce an ADR
**Why:** undocumented decisions are forgotten within months — the team re-litigates them or, worse, silently reverses them. ADRs preserve the reasoning so future readers can challenge it on its merits, not on guesses.

#### Document the WHY, not just the WHAT — record trade-offs explicitly
**Why:** the WHAT is recoverable from the code; the WHY is not. Without the rationale, future maintainers cannot tell which constraints still apply and which have lapsed.

### Output Contract

When producing architecture artifacts, deliver each in this exact form:

| Artifact | Required Form |
|----------|---------------|
| **ADR** | Markdown using the structure in [adr-template.md](references/adr-template.md): Status, Date, Deciders, Context, Decision Drivers, Considered Options, Decision Outcome (with Consequences Good/Bad), Pros/Cons per option, Links. |
| **C4 Context Diagram** | One box for the system; external actors and external systems around it; every relationship labeled with its purpose and protocol. |
| **C4 Container Diagram** | Containers (apps, databases, services) inside the system box; each container annotated with its technology choice; every relationship labeled with protocol (REST, gRPC, async event, etc.). |
| **Module Map** | Table with columns: Module, Responsibility, Key Entities, Inbound Communication, Outbound Communication. One row per bounded context. |
| **Trade-off Analysis** | Use the template in [decision-framework.md](references/decision-framework.md): Pros/Cons/Risk per option, then a Recommendation with the key reason aligned to the project's NFR priorities. |

---

## When Validating Architecture

### 🔴 BLOCKING Checklist
- [ ] Dependency Rule respected — all dependencies point inward.
- [ ] Each module has a single, named responsibility.
- [ ] Core domain is framework-agnostic.
- [ ] Each module is testable in isolation, without spinning up the full stack.

### Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Big Ball of Mud** | No structure, everything coupled to everything | Define modules; enforce boundaries via dependency rules and ArchUnit-style tests |
| **Premature Microservices** | Distributed monolith with deployment coupling | Start as a modular monolith; extract a service only when scale, team boundaries, or independent deploy cadence demand it |
| **Anemic Domain Model** | Business logic scattered across services | Move behavior onto the entity that owns the data |
| **Leaky Abstractions** | Infrastructure types appear in domain signatures | Strict port/adapter separation — translate at the boundary |
| **Circular Dependencies** | Modules depend on each other | Apply Dependency Inversion or domain events to break the cycle |

---

## End-to-End Example

**Input** (user request):
> "We need to add a 'subscription billing' capability to the platform. It manages plans, recurring charges, dunning, and integrates with Stripe."

**Expected output** (this skill produces):

1. **Domain analysis** — bounded context `billing/`, separate from `order/` and `payment/`. Aggregates identified: `Subscription`, `BillingPlan`, `DunningPolicy`.
2. **Style decision** — Hexagonal: complex domain rules (proration, dunning, plan upgrades) plus the need to swap payment provider later. Recorded as **ADR-0042**.
3. **C4 Container diagram** — adds a `billing` module to the existing monolith; arrow to Stripe (`HTTPS, idempotent POST`); arrow to `email/` (async event `InvoiceIssuedEvent`).
4. **Module Map row** — `billing/` | Recurring charges, dunning, plans | `Subscription`, `BillingPlan`, `Invoice` | inbound: REST `/api/billing/*` | outbound: Stripe (REST), `email/` (event), `payment/` (REST).
5. **Code structure** — `billing/{domain,application,infrastructure}` with a JPA adapter for persistence and a Stripe adapter behind an output port `PaymentProviderPort`.
6. **Trade-off note** — chose Hexagonal over Layered: more boilerplate accepted to enable provider swap and isolated testing of dunning rules.
