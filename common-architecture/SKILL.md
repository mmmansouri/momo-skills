---
name: common-architecture
description: >-
  Architecture decisions and system design. Use when: designing new features/modules,
  choosing architectural style (Hexagonal, Clean, CQRS, Microservices), evaluating
  trade-offs, creating ADRs or C4 diagrams, applying SOLID/DDD principles, or
  structuring code (package by feature).
---

# Application Architect Skill

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Core Philosophy

1. **Domain-Centric**: Business logic at the center, technology serves the domain
2. **Defer Decisions**: Delay technical choices until necessary
3. **Trade-offs Over Best Practices**: Every decision is a compromise—document why
4. **Testability First**: Good architecture makes testing easy
5. **Evolutionary**: Architecture must evolve—design for change

---

## When Starting Architecture Work

📚 **References:** [design-principles.md](references/design-principles.md)

Ask these questions before proposing any architecture:

| Category | Questions |
|----------|-----------|
| **Domain** | What is the core business problem? |
| **Scale** | Expected users, requests/sec, data volume? |
| **Team** | Size, skills, experience with patterns? |
| **Constraints** | Budget, timeline, compliance (GDPR)? |
| **Integration** | External systems, APIs, legacy? |
| **NFRs** | Priority: Performance, Security, Availability, Maintainability? |

---

## When Choosing Architectural Style

📚 **References:** [architectural-styles.md](references/architectural-styles.md)

| Context | Recommended Style |
|---------|-------------------|
| Small team, simple domain, MVP | **Modular Monolith** or **Layered** |
| Complex domain, business rules focus | **Hexagonal** or **Clean Architecture** |
| High read/write ratio imbalance | **CQRS** |
| Multiple teams, independent scaling | **Microservices** |
| Real-time, async requirements | **Event-Driven** |

### 🔴 BLOCKING
- **Never choose Microservices for MVP** → Start modular monolith, extract later
- **Never skip domain analysis** → Style must match domain complexity

### 🟡 WARNING
- **Avoid "Golden Hammer"** → Don't use same pattern everywhere

---

## When Structuring Code

📚 **References:** [code-structures.md](references/code-structures.md)

### 🔴 BLOCKING
- **Package by Feature, not Layer** → `order/`, `product/`, not `controllers/`, `services/`
- **Dependency Rule** → All dependencies point inward to domain
- **Domain is Framework-Agnostic** → No Spring/@Autowired in domain layer

### 🟡 WARNING
- **Avoid Anemic Domain Model** → Entities should have behavior, not just data

### 🟢 BEST PRACTICE
- **Explicit Boundaries** → Clear contracts (interfaces) at every boundary
- **High Cohesion, Low Coupling** → Related things together, minimal cross-module deps

---

## When Documenting Decisions

📚 **References:** [adr-template.md](references/adr-template.md) | [decision-framework.md](references/decision-framework.md)

### 🔴 BLOCKING
- **Every significant decision needs an ADR** → No undocumented architecture choices
- **Document the WHY, not just WHAT** → Trade-offs must be explicit

### Output Checklist
- [ ] C4 Context Diagram (system + external actors)
- [ ] C4 Container Diagram (high-level building blocks)
- [ ] ADR for each significant decision
- [ ] Module Map (bounded contexts)

---

## When Validating Architecture

### 🔴 BLOCKING Checklist
- [ ] Dependency Rule respected (deps point inward)
- [ ] Each module has single responsibility
- [ ] Core domain is framework-agnostic
- [ ] Easy to test in isolation

### Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Big Ball of Mud** | No structure | Define modules, enforce boundaries |
| **Premature Microservices** | Distributed monolith | Start modular, extract later |
| **Anemic Domain Model** | Logic in services | Rich domain with behavior |
| **Leaky Abstractions** | Infra in domain | Strict port/adapter separation |
| **Circular Dependencies** | Modules depend on each other | Dependency inversion, events |

---

## Agent Workflow: Planning Before Coding

When acting as an architect/planner, design implementation plans **BEFORE** code is written.

### Planning Workflow

> **Note:** This workflow is for the **Plan agent** (orchestrator role), which IS allowed to explore the codebase broadly. Dev agents receiving the resulting plan should follow `common-agent` rules (trust provided context, no broad exploration).

1. **Understand**: Read codebase-state.md, then read specific files relevant to the change
2. **Analyze**: Identify what needs to change, what existing patterns can be reused
3. **Design**: Propose solution following project patterns
4. **Document**: List files to create/modify with clear steps (these become the Implementation Context for dev agents)
5. **Verify**: Include verification steps (tests, build, manual checks)

### Plan Output Format

Your plans should include:

- **Summary**: 1-2 sentences describing the change
- **Files to modify**: List with brief description of changes
- **Files to create**: List with purpose
- **Implementation steps**: Ordered list
- **Testing strategy**: How to verify the implementation
- **Risks/Considerations**: Any concerns or alternatives considered

### Example Plan Structure

```markdown
## Summary
Add soft-delete support to the Order entity.

## Files to Modify
- `order/entity/OrderEntity.java` — Add deletedAt field
- `order/repository/OrderJpaRepository.java` — Add @Where clause

## Files to Create
- `order/service/OrderArchiveService.java` — Archive logic
- `changelog/2024-02-05-add-order-deleted-at.yaml` — Migration

## Implementation Steps
1. Create Liquibase migration
2. Add deletedAt field to entity
3. Update repository query filter
4. Create archive service
5. Write tests

## Testing Strategy
- Unit test: archive sets deletedAt
- Integration test: archived orders excluded from findAll

## Risks
- Existing queries may need @Where override for admin views
```

---

## Buy Nature Integration

### Module Map

The Buy Nature platform follows modular architecture with clear bounded contexts:

| Module | Responsibility | Key Entities |
|--------|---------------|--------------|
| `order/` | Order processing, checkout | Order, OrderItem, OrderStatus |
| `product/` | Catalog, items, categories | Item, Category, Stock |
| `customer/` | Customer management, addresses | Customer, Address, CustomerProfile |
| `auth/` | OAuth2 client + user authentication | User, Role, Token |
| `payment/` | Stripe integration | Payment, PaymentIntent, PaymentStatus |
| `email/` | Notifications | EmailTemplate, EmailLog |

### Inter-Module Communication Patterns

**Direct REST Calls (Synchronous):**
- Order → Customer: Billing and shipping address retrieval
- Order → Product: Stock validation and reservation
- Payment → Order: Payment status updates

**Domain Events (Asynchronous):**
- `OrderCreatedEvent` → Email notification service
- `PaymentCompletedEvent` → Order status update
- `StockUpdatedEvent` → Cache invalidation

### Application Architecture

```
buy-nature-back (Monolith)
├── order/           - Order domain
├── product/         - Product catalog
├── customer/        - Customer management
├── auth/            - Authentication
├── payment/         - Stripe integration
└── common/          - Shared utilities

buy-nature-front     - Customer SPA (Angular 20)
buy-nature-back-office - Admin SPA (Angular 18)
buy-nature-ci        - Dagger CI/CD
buy-nature-e2e-*     - Playwright E2E tests
```

### Key Architectural Decisions

1. **Monolith-first**: All domains in single Spring Boot app for simplicity
2. **Shared database**: PostgreSQL with schema-per-module
3. **No microservices**: YAGNI - split only if needed
4. **Event-driven within monolith**: Spring ApplicationEvents for decoupling
5. **API segregation**: `/api/*` (public) vs `/api/admin/*` (admin)
