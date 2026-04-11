# GitHub Actions Guide

## Overview

Best practices for building CI/CD pipelines with GitHub Actions.

---

## Workflow Structure

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'
  REGISTRY: ghcr.io

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: npm run build
```

---

## 🔴 BLOCKING Rules

### 1. Pin Action Versions

```yaml
# ✅ CORRECT: Pinned to SHA (most secure)
- uses: actions/checkout@8ade135a41bc03ea155e62e844d188df1ea18608  # v4.1.1

# ✅ ACCEPTABLE: Pinned to major version
- uses: actions/checkout@v4

# 🔴 WRONG: Unpinned or latest
- uses: actions/checkout@main
- uses: actions/checkout@latest
```

### 2. Use Secrets for Sensitive Data

```yaml
# ✅ CORRECT
env:
  API_KEY: ${{ secrets.API_KEY }}
  
# 🔴 WRONG: Never hardcode
env:
  API_KEY: sk_live_abc123
```

### 3. Limit Token Permissions

```yaml
# ✅ CORRECT: Minimal permissions
permissions:
  contents: read
  packages: write

# 🔴 WRONG: Default write-all
permissions: write-all
```

---

## Complete CI/CD Example

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  release:
    types: [published]

env:
  NODE_VERSION: '20'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

permissions:
  contents: read
  packages: write
  pull-requests: write

jobs:
  # ============================================
  # Stage 1: Lint and Type Check (Fast)
  # ============================================
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint
        run: npm run lint
      
      - name: Type check
        run: npm run type-check

  # ============================================
  # Stage 2: Test (Parallel)
  # ============================================
  test-unit:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - run: npm ci
      
      - name: Run unit tests
        run: npm run test:unit -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  test-integration:
    needs: lint
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
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
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - run: npm ci
      
      - name: Run integration tests
        run: npm run test:integration
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test

  # ============================================
  # Stage 3: Security Scan
  # ============================================
  security:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
      
      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  # ============================================
  # Stage 4: Build
  # ============================================
  build:
    needs: [test-unit, test-integration, security]
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix=
            type=semver,pattern={{version}}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ============================================
  # Stage 5: Deploy to Staging
  # ============================================
  deploy-staging:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Staging
        run: ./scripts/deploy.sh staging
        env:
          IMAGE_TAG: ${{ needs.build.outputs.image-tag }}
          KUBECONFIG: ${{ secrets.STAGING_KUBECONFIG }}

  # ============================================
  # Stage 6: E2E Tests on Staging
  # ============================================
  e2e-tests:
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Run E2E tests
        run: npm run test:e2e
        env:
          BASE_URL: https://staging.example.com

  # ============================================
  # Stage 7: Deploy to Production
  # ============================================
  deploy-production:
    if: github.event_name == 'release'
    needs: [build, e2e-tests]
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Production
        run: ./scripts/deploy.sh production
        env:
          IMAGE_TAG: ${{ needs.build.outputs.image-tag }}
          KUBECONFIG: ${{ secrets.PROD_KUBECONFIG }}
```

---

## Caching

### Node.js

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'  # Automatic caching
```

### Docker

```yaml
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Custom Cache

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip
      ~/.local
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

---

## Matrix Builds

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node: [18, 20, 22]
        exclude:
          - os: windows-latest
            node: 18
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
```

---

## Reusable Workflows

### Define Reusable Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      image-tag:
        required: true
        type: string
    secrets:
      KUBECONFIG:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - name: Deploy
        run: kubectl set image deployment/app app=${{ inputs.image-tag }}
        env:
          KUBECONFIG: ${{ secrets.KUBECONFIG }}
```

### Use Reusable Workflow

```yaml
jobs:
  deploy-staging:
    uses: ./.github/workflows/deploy.yml
    with:
      environment: staging
      image-tag: ghcr.io/org/app:sha-abc123
    secrets:
      KUBECONFIG: ${{ secrets.STAGING_KUBECONFIG }}
```

---

## Composite Actions

```yaml
# .github/actions/setup-project/action.yml
name: Setup Project
description: Setup Node.js and install dependencies

inputs:
  node-version:
    description: Node.js version
    default: '20'

runs:
  using: composite
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'
    
    - run: npm ci
      shell: bash
```

### Usage

```yaml
steps:
  - uses: ./.github/actions/setup-project
    with:
      node-version: '20'
```

---

## Environments and Approvals

```yaml
jobs:
  deploy-prod:
    environment:
      name: production
      url: https://example.com
    # Requires manual approval configured in repo settings
```

---

## Debugging

### Enable Debug Logging

```yaml
# Set these secrets in repo settings
ACTIONS_STEP_DEBUG: true
ACTIONS_RUNNER_DEBUG: true
```

### SSH Debug Session

```yaml
- name: Setup tmate session
  if: failure()
  uses: mxschmitt/action-tmate@v3
  timeout-minutes: 15
```
