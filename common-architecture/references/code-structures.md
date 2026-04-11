# Code Structure Reference

## Spring Boot - Hexagonal/Clean Structure

```
src/main/java/com/example/
├── order/                          # Feature module
│   ├── domain/                     # Core business logic
│   │   ├── model/
│   │   │   ├── Order.java          # Entity
│   │   │   ├── OrderId.java        # Value Object
│   │   │   └── OrderStatus.java    # Enum
│   │   ├── port/
│   │   │   ├── in/
│   │   │   │   └── CreateOrderUseCase.java    # Input port
│   │   │   └── out/
│   │   │       └── OrderRepository.java       # Output port
│   │   └── service/
│   │       └── OrderDomainService.java        # Domain service
│   ├── application/                # Use cases implementation
│   │   └── CreateOrderService.java
│   └── infrastructure/             # Adapters
│       ├── persistence/
│       │   ├── OrderJpaEntity.java
│       │   ├── OrderJpaRepository.java
│       │   └── OrderRepositoryAdapter.java
│       └── web/
│           ├── OrderController.java
│           └── OrderDto.java
├── product/                        # Another feature module
│   └── ...
└── shared/                         # Cross-cutting concerns
    ├── domain/
    │   └── DomainEvent.java
    └── infrastructure/
        └── EventPublisher.java
```

### Layer Responsibilities

| Layer | Contains | Depends On |
|-------|----------|------------|
| **domain/** | Entities, Value Objects, Domain Services, Ports | Nothing external |
| **application/** | Use Case implementations | domain/ |
| **infrastructure/** | Controllers, DB Adapters, External APIs | domain/, application/ |

---

## Angular - Feature-Based Structure

```
src/app/
├── features/                       # Feature modules
│   ├── order/
│   │   ├── domain/                 # Business logic
│   │   │   ├── models/
│   │   │   │   └── order.model.ts
│   │   │   └── services/
│   │   │       └── order.facade.ts # State + API orchestration
│   │   ├── infrastructure/         # External adapters
│   │   │   └── order-api.service.ts
│   │   └── ui/                     # Presentation
│   │       ├── containers/         # Smart components
│   │       │   └── order-list.container.ts
│   │       └── components/         # Dumb components
│   │           └── order-card.component.ts
│   └── product/
│       └── ...
├── shared/                         # Shared utilities
│   ├── ui/                         # Reusable UI components
│   └── utils/                      # Helper functions
└── core/                           # App-wide singletons
    ├── auth/
    └── http/
```

### Component Types

| Type | Location | Characteristics |
|------|----------|-----------------|
| **Container** | `ui/containers/` | Has state, calls facade, passes data down |
| **Component** | `ui/components/` | Stateless, @Input/@Output only |
| **Facade** | `domain/services/` | Orchestrates state and API calls |
| **API Service** | `infrastructure/` | HTTP calls only |

---

## Dependency Rules

```
    ┌─────────────────────────────────────┐
    │         infrastructure/             │
    │   (Controllers, DB, External APIs)  │
    └───────────────┬─────────────────────┘
                    │ depends on
                    ▼
    ┌─────────────────────────────────────┐
    │          application/               │
    │         (Use Cases)                 │
    └───────────────┬─────────────────────┘
                    │ depends on
                    ▼
    ┌─────────────────────────────────────┐
    │            domain/                  │
    │   (Entities, Ports, Domain Logic)   │
    └─────────────────────────────────────┘

    ⚠️ domain/ NEVER depends on outer layers
```
