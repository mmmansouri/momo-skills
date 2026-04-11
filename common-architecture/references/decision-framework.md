# Architecture Decision Framework

## Decision Matrix Template

| Criterion | Weight | Option A | Option B | Option C |
|-----------|--------|----------|----------|----------|
| Maintainability | High (3) | ? | ? | ? |
| Team Familiarity | Medium (2) | ? | ? | ? |
| Time to Market | High (3) | ? | ? | ? |
| Scalability | Context (1-3) | ? | ? | ? |
| Operational Cost | Medium (2) | ? | ? | ? |
| Testability | High (3) | ? | ? | ? |

**Scoring:** 1 (Poor) → 5 (Excellent)
**Total:** Sum of (Weight × Score) for each option

---

## Quick Decision Guide

### Architectural Style Selection

```
START
  │
  ├─ Simple CRUD, MVP, < 3 devs?
  │   └─► Layered / Modular Monolith
  │
  ├─ Complex domain logic, high testability needed?
  │   └─► Hexagonal / Clean Architecture
  │
  ├─ Heavy read vs write imbalance?
  │   └─► CQRS
  │
  ├─ Multiple teams, independent deployments?
  │   └─► Microservices
  │
  └─ Async processing, event sourcing?
      └─► Event-Driven
```

### Technology Selection

| Question | If Yes | If No |
|----------|--------|-------|
| Team knows it? | Prefer it | Add learning time |
| Active community? | Safe choice | Risk of abandonment |
| Fits scale needs? | Good | Overengineering risk |
| Easy to hire for? | Sustainable | Team risk |

---

## Trade-off Analysis Template

```markdown
## Decision: [What are we deciding?]

### Option A: [Name]

**Pros:**
- Pro 1
- Pro 2

**Cons:**
- Con 1
- Con 2

**Risk:** [Low/Medium/High] - [Explanation]

### Option B: [Name]

**Pros:**
- Pro 1

**Cons:**
- Con 1
- Con 2

**Risk:** [Low/Medium/High] - [Explanation]

### Recommendation

[Option X] because [key reason aligning with priorities].
```

---

## NFR Priority Template

Rank these 1-6 for your project (1 = highest priority):

| NFR | Rank | Notes |
|-----|------|-------|
| Performance | _ | Response time, throughput |
| Security | _ | Auth, data protection |
| Availability | _ | Uptime requirements |
| Maintainability | _ | Code quality, documentation |
| Scalability | _ | Growth handling |
| Cost | _ | Infrastructure, development |

The top 2-3 should drive architectural decisions.
