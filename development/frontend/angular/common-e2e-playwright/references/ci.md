# CI Integration for E2E (Local Mode, Docker Stack, Reporting)

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Generic GitHub-Actions plumbing (matrix, sharding, artifact upload, retries,
browser caching) is native knowledge from the official Playwright CI docs and is
not repeated here. This reference keeps only what is specific to the house E2E
setup: the **local-mode** workflow (`local-e2e` Spring profile, frontend on port
4201, backend on 8080), the **docker-compose** stack, and the `e2e:ci` script.

## Table of Contents

- [Local Mode Workflow](#local-mode-workflow)
- [Docker Stack (docker-compose.e2e.yml)](#docker-stack-docker-composee2eyml)
- [Docker Mode Workflow (e2e:ci)](#docker-mode-workflow-e2eci)
- [Reporting](#reporting)

---

## Local Mode Workflow

Local mode runs the three processes side by side: a Postgres service, the
backend under the **`local-e2e`** Spring profile, and the frontend served with
**`npm run start:local-e2e`** on **port 4201**. Playwright then targets
`http://localhost:4201` (see [playwright-config.md](playwright-config.md), the
`E2E_MODE=local` branch).

```yaml
# <your-e2e-project>/.github/workflows/e2e-local.yml
jobs:
  e2e:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: e2euser
          POSTGRES_PASSWORD: e2epass
          POSTGRES_DB: e2edb
        ports:
          - 5434:5432          # house Postgres port for E2E
        options: >-
          --health-cmd pg_isready --health-interval 10s
          --health-timeout 5s --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - uses: actions/setup-java@v4
        with: { java-version: 21, distribution: 'temurin', cache: 'maven' }

      # Backend under the local-e2e profile, wait for health.
      - name: Start backend
        run: |
          cd ../<your-backend>
          mvn spring-boot:run -Dspring-boot.run.profiles=local-e2e &
          timeout 120 bash -c 'until curl -f http://localhost:8080/actuator/health; do sleep 2; done'

      # Frontend on port 4201, wait for it to answer.
      - name: Start frontend
        run: |
          cd ../<your-frontend>
          npm ci
          npm run start:local-e2e &
          timeout 120 bash -c 'until curl -f http://localhost:4201; do sleep 2; done'

      - name: Run E2E tests
        run: |
          npm ci
          npx playwright install --with-deps
          npm run test:local:headless
        env:
          DATABASE_URL: postgresql://e2euser:e2epass@localhost:5434/e2edb
```

---

## Docker Stack (docker-compose.e2e.yml)

Docker mode brings the whole stack up in containers. Backend runs the **`e2e`**
profile (`SPRING_PROFILES_ACTIVE: e2e`); Postgres is published on **5434**; each
service gates the next through a `healthcheck` + `depends_on: condition:
service_healthy`.

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpass
      POSTGRES_DB: testdb
    ports:
      - '5434:5432'
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U testuser']
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ../<your-backend>
      dockerfile: Dockerfile
    environment:
      SPRING_PROFILES_ACTIVE: e2e
      DATABASE_URL: jdbc:postgresql://postgres:5432/testdb
      DATABASE_USERNAME: testuser
      DATABASE_PASSWORD: testpass
    ports:
      - '8080:8080'
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ['CMD-SHELL', 'curl -f http://localhost:8080/actuator/health || exit 1']
      interval: 10s
      timeout: 5s
      retries: 10

  frontend:
    build:
      context: ../<your-frontend>
      dockerfile: Dockerfile
    environment:
      API_URL: http://backend:8080
    ports:
      - '4200:80'
    depends_on:
      backend:
        condition: service_healthy
```

---

## Docker Mode Workflow (e2e:ci)

In Docker mode the whole run is wrapped by the house **`e2e:ci`** npm script,
which starts the compose stack, runs the tests, and tears down with proper exit
codes. The workflow just calls it:

```yaml
      - name: Run E2E tests in Docker
        run: npm run e2e:ci

      - name: Upload report
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report-docker
          path: playwright-report/
```

`e2e` (local dev) starts services, runs, and stops; `e2e:ci` is the same but
returns the test exit code so CI fails correctly.

---

## Reporting

Keep the CI reporters that feed GitHub and JUnit consumers:

```typescript
// playwright.config.ts — CI reporters
reporter: [
  ['github'],                                        // PR annotations
  ['html'],
  ['junit', { outputFile: 'test-results/results.xml' }],
]
```
