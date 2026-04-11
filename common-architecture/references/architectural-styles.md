# Architectural Styles Reference

## Layered Architecture

```
┌─────────────────────────┐
│     Presentation        │  ← Controllers, Views
├─────────────────────────┤
│     Application         │  ← Use Cases, Services
├─────────────────────────┤
│       Domain            │  ← Entities, Business Rules
├─────────────────────────┤
│    Infrastructure       │  ← DB, External APIs
└─────────────────────────┘
```

**Use When:** Simple CRUD apps, small teams, quick MVPs
**Avoid When:** Complex domain logic, need for testability

---

## Hexagonal Architecture (Ports & Adapters)

```
                    ┌──────────────────┐
    ┌───────────────┤   Web Adapter    │
    │               └──────────────────┘
    │ Input
    │ Ports         ┌──────────────────┐
    ▼               │                  │
┌───────┐           │      DOMAIN      │
│  API  │◄─────────►│                  │
└───────┘           │   (Use Cases)    │
                    │                  │
    ▲               └──────────────────┘
    │ Output
    │ Ports         ┌──────────────────┐
    └───────────────┤   DB Adapter     │
                    └──────────────────┘
```

**Key Concepts:**
- **Ports**: Interfaces defining how domain interacts with outside
- **Adapters**: Implementations of ports (Web, DB, Messaging)
- **Dependency Rule**: All dependencies point inward to domain

**Use When:** Complex business logic, need framework independence, high testability
**Avoid When:** Simple CRUD, tight deadlines

---

## Clean Architecture

Same principles as Hexagonal with explicit layers:

```
┌─────────────────────────────────────────┐
│           Frameworks & Drivers          │  ← Web, DB, UI
├─────────────────────────────────────────┤
│         Interface Adapters              │  ← Controllers, Presenters, Gateways
├─────────────────────────────────────────┤
│         Application Business Rules      │  ← Use Cases
├─────────────────────────────────────────┤
│         Enterprise Business Rules       │  ← Entities
└─────────────────────────────────────────┘
         Dependencies point INWARD →
```

---

## CQRS (Command Query Responsibility Segregation)

```
              ┌─────────────┐
              │   Command   │───► Write Model ───► Write DB
              └─────────────┘
    Request ──┤
              ┌─────────────┐
              │    Query    │───► Read Model  ───► Read DB
              └─────────────┘
```

**Use When:** Read/write ratio heavily imbalanced, different scaling needs, complex reporting
**Avoid When:** Simple domains, small teams unfamiliar with pattern

---

## Microservices

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Service │     │ Service │     │ Service │
│    A    │◄───►│    B    │◄───►│    C    │
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
     ▼               ▼               ▼
  ┌─────┐        ┌─────┐        ┌─────┐
  │ DB  │        │ DB  │        │ DB  │
  └─────┘        └─────┘        └─────┘
```

**Use When:** Multiple teams, independent deployments, different scaling needs per service
**Avoid When:** Small team (<5), unclear domain boundaries, MVP phase

---

## Event-Driven Architecture

```
┌─────────┐         ┌─────────────┐         ┌─────────┐
│ Service │──event─►│ Event Bus   │──event─►│ Service │
│    A    │         │ (Kafka/RMQ) │         │    B    │
└─────────┘         └─────────────┘         └─────────┘
```

**Use When:** Async processing, decoupled services, audit trails needed
**Avoid When:** Strict consistency required, simple request/response
