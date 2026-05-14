# CI Integration: Docker, Reporting, Performance & Troubleshooting

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

## Table of Contents

- [Docker Integration](#docker-integration)
- [Test Reporting](#test-reporting)
- [Docker CI Workflow Example](#docker-ci-workflow-example)
- [Performance Optimization](#performance-optimization)
- [Quick Reference](#quick-reference)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Docker Integration

### 🔴 BLOCKING - Using Docker Compose

```yaml
# .github/workflows/e2e-docker.yml
name: E2E Tests (Docker)

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Start services with Docker Compose
        run: docker-compose -f docker-compose.e2e.yml up -d

      - name: Wait for services to be ready
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:4200/health; do sleep 2; done'
          timeout 60 bash -c 'until curl -f http://localhost:8080/actuator/health; do sleep 2; done'

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npx playwright test
        env:
          BASE_URL: http://localhost:4200

      - name: Stop services
        if: always()
        run: docker-compose -f docker-compose.e2e.yml down

      - name: Upload logs
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: docker-logs
          path: logs/
```

### docker-compose.e2e.yml

```yaml
version: '3.8'

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

## Test Reporting

### 🟢 BEST PRACTICE - GitHub Annotations

```typescript
// playwright.config.ts
export default defineConfig({
  reporter: [
    ['github'], // Shows errors as annotations in PR
    ['html'],
    ['junit', { outputFile: 'test-results/results.xml' }],
  ],
});
```

### JUnit XML for Test Results

```yaml
- name: Publish test results
  uses: dorny/test-reporter@v1
  if: always()
  with:
    name: Playwright Tests
    path: test-results/results.xml
    reporter: java-junit
```

---

## Docker CI Workflow Example

### Frontend E2E (Docker Mode)

```yaml
# <your-e2e-project>/.github/workflows/e2e-docker.yml
name: E2E Tests (Docker Mode)

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests in Docker
        run: npm run e2e:ci

      - name: Upload report
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report-docker
          path: playwright-report/

      - name: Upload container logs
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: docker-logs
          path: docker-logs/
```

---

## Performance Optimization

### 🟢 BEST PRACTICE - Caching

```yaml
- name: Cache Playwright browsers
  uses: actions/cache@v4
  with:
    path: ~/.cache/ms-playwright
    key: playwright-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      playwright-${{ runner.os }}-

- name: Install Playwright browsers
  run: npx playwright install --with-deps chromium
  # Only install if cache miss
```

### Parallel Jobs with Dependencies

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Build application
        run: npm run build
      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build
          path: dist/

  e2e-chrome:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download build
        uses: actions/download-artifact@v4
        with:
          name: build
          path: dist/
      - name: Run tests (Chrome)
        run: npx playwright test --project=chromium

  e2e-firefox:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download build
        uses: actions/download-artifact@v4
        with:
          name: build
          path: dist/
      - name: Run tests (Firefox)
        run: npx playwright test --project=firefox
```

---

## Quick Reference

### CI Integration Checklist

#### 🔴 BLOCKING
- [ ] `forbidOnly: !!process.env.CI` in config
- [ ] Retries enabled in CI (2-3)
- [ ] Workers limited in CI (1-2)
- [ ] GitHub reporter for annotations
- [ ] Upload artifacts on failure
- [ ] Health checks for services

#### 🟡 WARNING
- [ ] Test timeout appropriate (30-60s)
- [ ] Job timeout reasonable (30-60 min)
- [ ] Sharding for large test suites
- [ ] Cache dependencies (npm, browsers)

#### 🟢 BEST PRACTICE
- [ ] JUnit XML for test results
- [ ] Separate jobs for different browsers
- [ ] Re-run failed tests only
- [ ] Upload videos/traces on failure
- [ ] Docker Compose for services
- [ ] Environment variables for URLs/secrets

---

## Common Patterns

### Pattern: Conditional E2E (PR vs Main)

```yaml
jobs:
  e2e-smoke:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - name: Run smoke tests only
        run: npx playwright test --grep @smoke

  e2e-full:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Run all tests
        run: npx playwright test
```

### Pattern: Scheduled E2E (Nightly)

```yaml
on:
  schedule:
    - cron: '0 2 * * *' # 2 AM daily
  workflow_dispatch: # Manual trigger

jobs:
  e2e-full:
    runs-on: ubuntu-latest
    steps:
      - name: Run full E2E suite
        run: npx playwright test
      - name: Notify on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Troubleshooting

### CI Tests Pass Locally, Fail in CI

**Possible causes:**
- Different environment (Docker vs local)
- Timing issues (CI is slower)
- Missing dependencies
- Environment variables not set

**Solutions:**
```yaml
# Add verbose logging
- name: Run tests with debug logs
  run: DEBUG=pw:* npx playwright test

# Increase timeouts in CI
# playwright.config.ts
export default defineConfig({
  timeout: process.env.CI ? 60000 : 30000,
});
```

### Flaky Tests in CI

```yaml
# Enable trace on first retry
# playwright.config.ts
use: {
  trace: 'on-first-retry',
}

# Upload traces
- name: Upload traces
  uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: traces
    path: test-results/**/trace.zip
```
