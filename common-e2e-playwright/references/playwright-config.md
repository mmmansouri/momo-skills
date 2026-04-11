# Playwright Configuration Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Overview

`playwright.config.ts` is the central configuration file for Playwright tests. It controls test execution, browser settings, retries, parallelization, and reporting.

---

## Basic Configuration

### 🔴 BLOCKING - Essential Settings

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Test directory
  testDir: './tests',

  // Run tests in parallel
  fullyParallel: true,

  // Fail build on CI if you accidentally left test.only
  forbidOnly: !!process.env.CI,

  // Retry failed tests in CI
  retries: process.env.CI ? 2 : 0,

  // Limit parallel workers in CI for stability
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: 'html',

  // Shared settings for all projects
  use: {
    // Base URL for page.goto('/')
    baseURL: 'http://localhost:4200',

    // Collect trace on first retry
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',
  },

  // Browser projects
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
```

---

## Projects Configuration

### Multiple Browsers

```typescript
export default defineConfig({
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
});
```

### Mobile Browsers

```typescript
export default defineConfig({
  projects: [
    // Desktop
    {
      name: 'Desktop Chrome',
      use: { ...devices['Desktop Chrome'] },
    },

    // Mobile
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 13'] },
    },
  ],
});
```

### Authentication Setup Project

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  projects: [
    // Setup project - runs first
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },

    // Tests depend on setup
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
  ],
});
```

---

## Timeout Settings

### 🔴 BLOCKING

```typescript
export default defineConfig({
  // Global timeout for each test (30 seconds)
  timeout: 30 * 1000,

  // Expect timeout (5 seconds)
  expect: {
    timeout: 5 * 1000,
  },

  use: {
    // Navigation timeout (10 seconds)
    navigationTimeout: 10 * 1000,

    // Action timeout (5 seconds)
    actionTimeout: 5 * 1000,
  },
});
```

**Timeout Hierarchy:**
```
Test timeout (30s)
  └─> Navigation timeout (10s)
  └─> Action timeout (5s)
  └─> Expect timeout (5s)
```

### 🟡 WARNING
- **Don't set timeouts too high** → Masks real issues
- **Don't set timeouts too low** → Causes flaky tests
- **Adjust per environment** → CI may need higher timeouts

---

## Retries & Workers

### 🔴 BLOCKING

```typescript
export default defineConfig({
  // Retries: 0 locally, 2 in CI
  retries: process.env.CI ? 2 : 0,

  // Workers: unlimited locally, 1 in CI (for stability)
  workers: process.env.CI ? 1 : undefined,

  // Or limit workers by CPU cores
  workers: process.env.CI ? 2 : Math.max(1, Math.floor(os.cpus().length / 2)),
});
```

**Worker Strategies:**

| Environment | Workers | Rationale |
|-------------|---------|-----------|
| Local dev | `undefined` (50% of cores) | Fast feedback |
| CI (GitHub Actions) | `1-2` | Stability, resource limits |
| Powerful CI server | `4-8` | Balance speed/stability |

---

## Reporters

### Single Reporter

```typescript
export default defineConfig({
  reporter: 'html', // HTML report
});
```

### Multiple Reporters

```typescript
export default defineConfig({
  reporter: [
    ['html'],                              // HTML report
    ['json', { outputFile: 'results.json' }],  // JSON for processing
    ['junit', { outputFile: 'results.xml' }],  // JUnit for CI
    ['list'],                              // Console output
  ],
});
```

### Custom Reporter for CI

```typescript
export default defineConfig({
  reporter: process.env.CI
    ? [
        ['junit', { outputFile: 'test-results/results.xml' }],
        ['github'],  // GitHub Actions annotations
      ]
    : [
        ['html'],
        ['list'],
      ],
});
```

---

## Base URL & Environment

### 🔴 BLOCKING - Environment-Specific URLs

```typescript
export default defineConfig({
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:4200',
  },
});
```

**Usage in tests:**
```typescript
test('should navigate to home', async ({ page }) => {
  // Uses baseURL + relative path
  await page.goto('/');
  await page.goto('/products');
});
```

**Multiple environments:**
```bash
# Local
BASE_URL=http://localhost:4200 npx playwright test

# Staging
BASE_URL=https://staging.buynature.com npx playwright test

# Production smoke tests
BASE_URL=https://buynature.com npx playwright test smoke
```

---

## Web Server Integration

### 🔴 BLOCKING - Auto-Start Dev Server

```typescript
export default defineConfig({
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:4200',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,  // 2 minutes to start
  },
});
```

**How it works:**
1. Playwright starts `npm run start`
2. Waits for `http://localhost:4200` to be available
3. Runs tests
4. Stops server when tests complete

### Multiple Services (Backend + Frontend)

```typescript
export default defineConfig({
  webServer: [
    {
      command: 'npm run start:backend',
      url: 'http://localhost:8080/health',
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'npm run start:frontend',
      url: 'http://localhost:4200',
      reuseExistingServer: !process.env.CI,
    },
  ],
});
```

---

## Trace, Screenshot, Video

### 🔴 BLOCKING

```typescript
export default defineConfig({
  use: {
    // Trace: Record test execution details
    trace: 'on-first-retry',  // Only on retries
    // trace: 'on',           // Always record (slow)
    // trace: 'off',          // Never record

    // Screenshots
    screenshot: 'only-on-failure',  // On failure only
    // screenshot: 'on',            // Every action (large)
    // screenshot: 'off',           // Never

    // Videos
    video: 'retain-on-failure',  // Keep only failed test videos
    // video: 'on',              // Record all (very large)
    // video: 'off',             // Never record
  },
});
```

**Trace Options:**

| Value | When | Use Case |
|-------|------|----------|
| `'on-first-retry'` | First retry only | 🟢 **Recommended** - balance size/debug info |
| `'on'` | Every test | Local debugging only (huge files) |
| `'retain-on-failure'` | Failed tests | Alternative to on-first-retry |
| `'off'` | Never | CI with other debug tools |

---

## Global Setup & Teardown

### Global Setup

```typescript
// global-setup.ts
import { FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('Starting global setup...');

  // Example: Seed database
  await seedDatabase();

  // Example: Start mock server
  await startMockServer();

  console.log('Global setup complete');
}

export default globalSetup;
```

### Global Teardown

```typescript
// global-teardown.ts
import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('Starting global teardown...');

  // Example: Clean up database
  await cleanDatabase();

  // Example: Stop mock server
  await stopMockServer();

  console.log('Global teardown complete');
}

export default globalTeardown;
```

### Configuration

```typescript
export default defineConfig({
  globalSetup: require.resolve('./global-setup'),
  globalTeardown: require.resolve('./global-teardown'),
});
```

---

## Buy Nature E2E Configuration

### Frontend E2E

```typescript
// buy-nature-e2e-front/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/results.xml' }],
  ],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:4201',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    // Buy Nature specific settings
    extraHTTPHeaders: {
      'Accept-Language': 'fr-FR',
    },
  },

  projects: [
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
      dependencies: ['setup'],
    },
  ],

  // Local E2E mode: services already running
  // Docker mode: services in containers
  webServer: process.env.E2E_MODE === 'local' ? undefined : {
    command: 'docker-compose up',
    url: 'http://localhost:4201',
    reuseExistingServer: false,
    timeout: 120 * 1000,
  },
});
```

### Backoffice E2E

```typescript
// buy-nature-e2e-backoffice/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,  // Sequential for admin operations
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,  // Always 1 worker for admin tests

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:4200',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',

    // Admin-specific settings
    viewport: { width: 1920, height: 1080 },  // Larger viewport for admin tables
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
```

---

## Test Match Patterns

### 🔴 BLOCKING

```typescript
export default defineConfig({
  // Match all *.spec.ts files
  testMatch: '**/*.spec.ts',

  // Match specific patterns
  testMatch: [
    '**/tests/**/*.spec.ts',
    '**/e2e/**/*.test.ts',
  ],

  // Ignore patterns
  testIgnore: [
    '**/node_modules/**',
    '**/dist/**',
    '**/*.skip.spec.ts',
  ],
});
```

### Test Tags

```typescript
// Run only tests with @smoke tag
// npx playwright test --grep @smoke

// Run all except @slow tests
// npx playwright test --grep-invert @slow

test('@smoke should login', async ({ page }) => {
  // ...
});

test('@slow should process large dataset', async ({ page }) => {
  // ...
});
```

---

## Quick Reference

### Configuration Checklist

#### 🔴 BLOCKING
- [ ] `testDir` points to tests folder
- [ ] `forbidOnly: !!process.env.CI` prevents .only in CI
- [ ] `retries` set to 2 in CI, 0 locally
- [ ] `baseURL` uses environment variable
- [ ] `trace: 'on-first-retry'` for debugging

#### 🟡 WARNING
- [ ] `workers` limited in CI (1-2)
- [ ] `timeout` values are reasonable (30s default)
- [ ] Reporters configured for CI and local

#### 🟢 BEST PRACTICE
- [ ] Multiple projects for different browsers
- [ ] `webServer` auto-starts dev server
- [ ] `screenshot` and `video` on failure only
- [ ] Global setup for database seeding

---

## Common Patterns

### Pattern: Environment-Based Config

```typescript
const isCI = !!process.env.CI;
const isLocal = process.env.E2E_MODE === 'local';

export default defineConfig({
  retries: isCI ? 2 : 0,
  workers: isCI ? 1 : undefined,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:4200',
    trace: isCI ? 'on-first-retry' : 'off',
  },
  webServer: isLocal ? undefined : {
    command: 'npm run start',
    url: 'http://localhost:4200',
  },
});
```

### Pattern: Separate Smoke Tests

```typescript
export default defineConfig({
  projects: [
    {
      name: 'smoke',
      testMatch: '**/*.smoke.spec.ts',
      retries: 0,
    },
    {
      name: 'full',
      testMatch: '**/*.spec.ts',
      testIgnore: '**/*.smoke.spec.ts',
      retries: 2,
    },
  ],
});
```
