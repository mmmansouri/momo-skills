# ADR Template

## Format

```markdown
# ADR-{NUMBER}: {TITLE}

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX
**Date:** YYYY-MM-DD
**Deciders:** [names]

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision Drivers

- Driver 1 (e.g., performance requirement)
- Driver 2 (e.g., team expertise)
- Driver 3 (e.g., time constraint)

## Considered Options

1. **Option A** - Brief description
2. **Option B** - Brief description
3. **Option C** - Brief description

## Decision Outcome

Chosen option: **"Option X"**, because [justification].

### Consequences

**Good:**
- Benefit 1
- Benefit 2

**Bad:**
- Drawback 1
- Drawback 2

## Pros and Cons of Options

### Option A

- ✅ Pro 1
- ✅ Pro 2
- ❌ Con 1

### Option B

- ✅ Pro 1
- ❌ Con 1
- ❌ Con 2

## Links

- [Related ADR](./ADR-XXX.md)
- [External reference](https://...)
```

---

## Example ADR

```markdown
# ADR-001: Use Hexagonal Architecture for Order Service

**Status:** Accepted
**Date:** 2024-01-15
**Deciders:** Tech Lead, Senior Devs

## Context

The Order service has complex business rules that need to be testable
independently of the database and web framework.

## Decision Drivers

- High testability requirement
- Need to swap persistence layer later
- Complex domain logic

## Considered Options

1. **Layered Architecture** - Traditional 3-tier
2. **Hexagonal Architecture** - Ports & Adapters
3. **Microkernel** - Plugin-based

## Decision Outcome

Chosen option: **"Hexagonal Architecture"**, because it provides
framework independence and high testability for complex domain logic.

### Consequences

**Good:**
- Domain logic fully testable without mocks
- Can swap database without touching business logic

**Bad:**
- More boilerplate (ports, adapters)
- Learning curve for junior developers
```
