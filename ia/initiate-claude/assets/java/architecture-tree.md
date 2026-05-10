# Architecture Tree — Spring Boot / Java Backend

Stack-specific template for Section 1. Format rules (indented tree, groups only, omit empty layers) are in `SKILL.md` Section 1.

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
- Package-by-feature: show the internal module pattern once, then list modules as a bulleted list with domain + key specifics (NO table)
- Event-driven: add `event/`, `listener/`, `job/` nodes under feature modules
- Omit layers that don't exist instead of leaving empty placeholders
