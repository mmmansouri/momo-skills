# Architecture Tree — Spring Boot / Java Backend

Copy and adapt this tree. Each node = group/package name + role after a dash. Show only groups/packages, not individual classes.

## Template

```
Application
├── API Layer
│   ├── Controllers — REST exposure, input validation
│   └── Filters/Interceptors — auth, logging, error handling
├── Business Layer
│   ├── Services — business logic
│   └── Handlers — complex workflow orchestration
├── Data Layer
│   ├── Repositories — DB access (Spring Data JPA)
│   └── Entities — data model
└── Infrastructure
    ├── Config — Spring profiles, beans, security
    └── Helpers/Utils — cross-cutting utilities
```

## Adaptation Rules

- Standard layered: use the template as-is
- Hexagonal / Clean Architecture: show ports (interfaces) and adapters (implementations) as separate sub-nodes
- Package-by-feature: show the internal module pattern once, then list all modules in a table with domain + key specifics
- Event-driven: add `event/`, `listener/`, `job/` nodes under feature modules
- Omit layers that don't exist instead of leaving empty placeholders
