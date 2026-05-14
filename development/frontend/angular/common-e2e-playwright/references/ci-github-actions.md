# CI Integration: GitHub Actions for Playwright

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

## Table of Contents

- [Overview](#overview)
- [GitHub Actions Setup](#github-actions-setup)
- [Multi-Browser Testing](#multi-browser-testing)
- [Sharding Tests](#sharding-tests)
- [Artifact Management](#artifact-management)
- [Retries & Failure Handling](#retries--failure-handling)
- [Environment Variables](#environment-variables)
- [Example CI Workflows](#example-ci-workflows)

---

## Overview

Running Playwright tests in CI/CD pipelines ensures code quality before deployment. This guide covers GitHub Actions, parallel execution, sharding, and artifact management.

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

## Example CI Workflows

### Frontend E2E (Local Mode)

```yaml
# <your-e2e-project>/.github/workflows/e2e-local.yml
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
          cd ../<your-backend>
          mvn clean package -DskipTests

      - name: Start backend
        run: |
          cd ../<your-backend>
          mvn spring-boot:run -Dspring-boot.run.profiles=local-e2e &
          timeout 120 bash -c 'until curl -f http://localhost:8080/actuator/health; do sleep 2; done'

      # Start frontend
      - name: Install frontend dependencies
        run: |
          cd ../<your-frontend>
          npm ci

      - name: Start frontend
        run: |
          cd ../<your-frontend>
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
