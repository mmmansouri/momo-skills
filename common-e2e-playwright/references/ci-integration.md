# CI Integration for Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

Running Playwright tests in CI/CD pipelines ensures code quality before deployment. This guide covers GitHub Actions, Docker, parallel execution, and artifact management.

---

## GitHub Actions Setup

### 🔴 BLOCKING - Basic Workflow

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload test report
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7
```

---

## Multi-Browser Testing

### 🔴 BLOCKING - Matrix Strategy

```yaml
jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false # Don't cancel other browsers if one fails
      matrix:
        browser: [chromium, firefox, webkit]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps ${{ matrix.browser }}

      - name: Run tests on ${{ matrix.browser }}
        run: npx playwright test --project=${{ matrix.browser }}

      - name: Upload report (${{ matrix.browser }})
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report-${{ matrix.browser }}
          path: playwright-report/
```

---

## Sharding Tests

### 🔴 BLOCKING - Parallel Execution with Shards

```yaml
jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4] # Split tests into 4 parallel jobs

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

      - name: Run tests (shard ${{ matrix.shard }}/4)
        run: npx playwright test --shard=${{ matrix.shard }}/4

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-${{ matrix.shard }}
          path: test-results/
```

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
      context: ../buy-nature-back
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
      context: ../buy-nature-front
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

## Artifact Management

### 🔴 BLOCKING - Upload Test Artifacts

```yaml
- name: Run E2E tests
  run: npx playwright test
  continue-on-error: true # Continue to upload artifacts even if tests fail

- name: Upload Playwright report
  uses: actions/upload-artifact@v4
  if: always() # Upload even if tests fail
  with:
    name: playwright-report
    path: playwright-report/
    retention-days: 30

- name: Upload test results (JUnit XML)
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: test-results
    path: test-results/
    retention-days: 30

- name: Upload videos
  uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: videos
    path: test-results/**/video.webm
    retention-days: 7

- name: Upload traces
  uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: traces
    path: test-results/**/trace.zip
    retention-days: 7
```

---

## Retries & Failure Handling

### 🔴 BLOCKING - Retry Failed Tests

```yaml
- name: Run E2E tests
  run: npx playwright test --retries=2
  continue-on-error: true

- name: Re-run failed tests only
  if: failure()
  run: npx playwright test --last-failed --retries=1

- name: Fail job if tests still fail
  if: failure()
  run: exit 1
```

### playwright.config.ts for CI

```typescript
export default defineConfig({
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  forbidOnly: !!process.env.CI,

  reporter: process.env.CI
    ? [
        ['junit', { outputFile: 'test-results/results.xml' }],
        ['html', { open: 'never' }],
        ['github'], // GitHub Actions annotations
      ]
    : [['html']],
});
```

---

## Environment Variables

### 🔴 BLOCKING - CI-Specific Configuration

```yaml
- name: Run E2E tests
  run: npx playwright test
  env:
    BASE_URL: ${{ secrets.STAGING_URL }}
    API_KEY: ${{ secrets.API_KEY }}
    CI: true
    NODE_ENV: test
```

**Accessing in tests:**
```typescript
test('should use staging environment', async ({ page }) => {
  const baseUrl = process.env.BASE_URL || 'http://localhost:4200';
  await page.goto(`${baseUrl}/products`);
});
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

## Buy Nature CI Examples

### Frontend E2E (Local Mode)

```yaml
# buy-nature-e2e-front/.github/workflows/e2e-local.yml
name: E2E Tests (Local Mode)

on: [push, pull_request]

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
          - 5434:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Setup Java
        uses: actions/setup-java@v4
        with:
          java-version: 21
          distribution: 'temurin'
          cache: 'maven'

      # Start backend
      - name: Build backend
        run: |
          cd ../buy-nature-back
          mvn clean package -DskipTests

      - name: Start backend
        run: |
          cd ../buy-nature-back
          mvn spring-boot:run -Dspring-boot.run.profiles=local-e2e &
          timeout 120 bash -c 'until curl -f http://localhost:8080/actuator/health; do sleep 2; done'

      # Start frontend
      - name: Install frontend dependencies
        run: |
          cd ../buy-nature-front
          npm ci

      - name: Start frontend
        run: |
          cd ../buy-nature-front
          npm run start:local-e2e &
          timeout 120 bash -c 'until curl -f http://localhost:4201; do sleep 2; done'

      # Run E2E tests
      - name: Install E2E dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:local:headless
        env:
          DATABASE_URL: postgresql://e2euser:e2epass@localhost:5434/e2edb

      - name: Upload report
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report-local
          path: playwright-report/
```

### Frontend E2E (Docker Mode)

```yaml
# buy-nature-e2e-front/.github/workflows/e2e-docker.yml
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
