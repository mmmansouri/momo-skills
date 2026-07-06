# E2E Project Structure

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Generic advice (group by feature, not by type; keep helpers out of specs) is
craftsmanship covered elsewhere. This reference keeps the house **layout**,
**file-naming** convention, an **example tree**, and the **run recipe**.

## Table of Contents

- [Recommended Layout](#recommended-layout)
- [File Naming](#file-naming)
- [Example Tree (Frontend / Backoffice)](#example-tree-frontend--backoffice)
- [Run Recipe](#run-recipe)

---

## Recommended Layout

### 🔴 BLOCKING — standard layout

```
e2e-project/
├── tests/                  # Specs grouped by feature
│   ├── auth/
│   ├── catalog/
│   ├── checkout/
│   └── smoke/              # *.smoke.spec.ts (see e2e-strategy.md)
├── pages/                  # Page Object Models (+ pages/components/)
├── fixtures/               # Custom fixtures + test-data factories
│   ├── index.ts
│   ├── auth.fixture.ts
│   └── test-data.fixture.ts
├── utils/                  # api-helper.ts, auth-helper.ts, db-helper.ts
├── playwright.config.ts
├── global-setup.ts / global-teardown.ts
└── README.md
```

Tests grouped by feature; page objects in `pages/`; fixtures in `fixtures/`;
cross-cutting helpers (API client, auth) in `utils/`.

---

## File Naming

| File type | Pattern | Example |
|-----------|---------|---------|
| Test | `<feature>.spec.ts` | `login.spec.ts` |
| Smoke test | `<feature>.smoke.spec.ts` | `checkout.smoke.spec.ts` |
| Setup (auth project) | `<feature>.setup.ts` | `auth.setup.ts` |
| Page object | `<name>.page.ts` | `login.page.ts` |
| Component POM | `<name>.component.ts` | `header.component.ts` |
| Fixture | `<name>.fixture.ts` | `auth.fixture.ts` |

---

## Example Tree (Frontend / Backoffice)

```
<your-app>-e2e-front/                  <your-app>-e2e-backoffice/
├── tests/                             ├── tests/
│   ├── auth/                          │   ├── auth/admin-login.spec.ts
│   ├── catalog/                       │   ├── products/create-product.spec.ts
│   ├── cart/                          │   ├── users/view-users.spec.ts
│   ├── checkout/                      │   └── orders/view-orders.spec.ts
│   └── smoke/*.smoke.spec.ts          ├── pages/
├── pages/*.page.ts                    │   ├── product-list.page.ts
├── fixtures/                          │   └── product-form.page.ts
│   ├── auth.fixture.ts                ├── fixtures/admin-auth.fixture.ts
│   └── test-data.fixture.ts           ├── utils/admin-api-helper.ts
├── utils/api-helper.ts                └── playwright.config.ts
├── docker-compose.yml
└── playwright.config.ts
```

The backoffice tree is lighter (serial admin runs — see
`playwright-config.md`).

---

## Run Recipe

**Local mode** — three processes plus the DB, then the tests:

```bash
npm run db:up                                             # 1. database (Postgres, port 5434)
cd ../<your-app>-back && \
  mvn spring-boot:run -Dspring-boot.run.profiles=local-e2e   # 2. backend, local-e2e profile
cd ../<your-app>-front && npm run start:local-e2e        # 3. frontend on port 4201
npm run test:local                                       # 4. run E2E (E2E_MODE=local)
```

**Docker mode** — the stack is managed for you:

```bash
npm run e2e        # start services, run, stop
npm run e2e:ci     # same, with CI-correct exit codes
npm run test:smoke # @smoke subset only
```
