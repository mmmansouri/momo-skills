# Architecture Tree — Angular Frontend

Stack-specific template for Section 1. Format rules (indented tree, groups only, omit empty layers) are in `SKILL.md` Section 1.

## Template

```
Application
├── Pages / Routes
│   ├── Feature Pages — routed components (lazy-loaded modules)
│   └── Shared Layouts — header, footer, sidebar
├── Components
│   ├── Smart Components — state-aware, inject services/stores
│   └── Dumb Components — @Input/@Output only, pure presentation
├── State Management
│   ├── Stores (Signal/NgRx) — application state
│   └── Effects / Reducers — side effects, state transitions
├── Services
│   ├── API Services — HTTP calls (HttpClient)
│   └── Business Services — client-side logic, guards, resolvers
└── Infrastructure
    ├── Interceptors — auth tokens, error handling, logging
    ├── Pipes / Directives — reusable template utilities
    └── Environments — environment.ts, environment.prod.ts
```

## Adaptation Rules

- Show component classification: Smart (state-aware) vs Dumb (presentational)
- Include state management approach (Signals, NgRx, or Signal stores)
- For large apps, group by feature module or routing structure
- Omit layers that don't exist instead of leaving empty placeholders
