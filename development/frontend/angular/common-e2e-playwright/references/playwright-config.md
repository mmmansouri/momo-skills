# Playwright Configuration Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

The standard `defineConfig` options (`testDir`, `fullyParallel`, `forbidOnly`,
`retries`, `workers`, `timeout`, `reporter`, `use.trace/screenshot/video`,
`projects`, `webServer`, global setup/teardown, `testMatch`) are native
Playwright knowledge — see the official config docs, and `SKILL.md` for the
minimum every project must set. This reference keeps the two **house configs**.

## Table of Contents

- [Frontend E2E Config](#frontend-e2e-config)
- [Backoffice E2E Config](#backoffice-e2e-config)

---

## Frontend E2E Config

Key house specifics: an **`E2E_MODE=local`** branch (services already running →
no `webServer`; otherwise bring up the docker-compose stack), **baseURL on port
4201**, an **`fr-FR`** `Accept-Language` header, and a **`setup` project** the
browser projects depend on.

```typescript
// <your-e2e-project>/playwright.config.ts
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

    // House: customer app runs in French.
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

  // Local E2E mode: services already running.
  // Docker mode: bring the stack up.
  webServer: process.env.E2E_MODE === 'local' ? undefined : {
    command: 'docker-compose up',
    url: 'http://localhost:4201',
    reuseExistingServer: false,
    timeout: 120 * 1000,
  },
});
```

---

## Backoffice E2E Config

The admin app runs **serially** (`fullyParallel: false`, `workers: 1`) because
admin operations mutate shared server state, and uses a **1920×1080** viewport
for the wide admin tables.

```typescript
// <your-e2e-backoffice-project>/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,  // Sequential for admin operations
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,            // Always 1 worker for admin tests

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:4200',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',

    // Larger viewport for admin tables.
    viewport: { width: 1920, height: 1080 },
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
```
