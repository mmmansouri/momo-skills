---
name: common-dev-ops
description: >-
  DevOps practices and CI/CD pipelines. Use when: designing CI/CD workflows,
  containerizing applications (Docker), orchestrating deployments (Kubernetes/Docker Compose),
  managing infrastructure (Terraform/Ansible), implementing GitOps, or setting up
  monitoring/observability. Contains both pure DevOps discipline and tool-specific guidance.
---

# DevOps & CI/CD Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

# Part 1: DevOps Discipline (Tool-Agnostic)

## Core Principles

1. **Automate Everything**: Manual processes are error-prone and don't scale
2. **Infrastructure as Code**: Version-controlled, reproducible environments
3. **Continuous Everything**: Integrate, test, deploy, and monitor continuously
4. **Fail Fast, Recover Faster**: Detect issues early, rollback quickly
5. **Security Shift-Left**: Security integrated from the start, not bolted on

---

## When Designing CI/CD Pipelines

📚 **References:** [pipeline-design.md](references/pipeline-design.md)

### Pipeline Stages

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│  Build  │ → │  Test   │ → │  Scan   │ → │ Package │ → │ Deploy  │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
     │             │             │             │             │
     ▼             ▼             ▼             ▼             ▼
  Compile      Unit tests    SAST/DAST    Container    Staging
  Lint         Integration   Deps scan    Registry     Production
  Type check   E2E (smoke)   Secrets      Artifacts    Rollback
```

### 🔴 BLOCKING
- **Every commit triggers pipeline** → No manual builds
- **Pipeline fails fast** → Cheapest checks first (lint, compile)
- **No manual deployments to production** → Always through pipeline
- **Artifacts are immutable** → Same artifact through all environments

### 🟡 WARNING
- **Don't skip tests for "urgent" fixes** → That's how bugs reach production
- **Don't store secrets in pipeline config** → Use secret managers

---

## When Structuring Pipelines

📚 **References:** [pipeline-patterns.md](references/pipeline-patterns.md)

### Stage Order (Fast → Slow)

| Order | Stage | Time | Purpose |
|-------|-------|------|---------|
| 1 | Lint/Format | <1 min | Code style |
| 2 | Build/Compile | 1-5 min | Syntax errors |
| 3 | Unit Tests | 1-5 min | Logic errors |
| 4 | Security Scan | 2-5 min | Vulnerabilities |
| 5 | Integration Tests | 5-15 min | Component interaction |
| 6 | E2E Tests | 10-30 min | User journeys |
| 7 | Package | 1-5 min | Create artifacts |
| 8 | Deploy Staging | 5-10 min | Test in real env |
| 9 | Deploy Production | 5-10 min | Release |

### 🔴 BLOCKING
- **Parallel where possible** → Run independent stages concurrently
- **Cache dependencies** → Don't download every build
- **Fail the whole pipeline on any failure** → No partial deployments

---

## When Containerizing Applications

📚 **References:** [containerization.md](references/containerization.md)

### 🔴 BLOCKING
- **One process per container** → Microservices, not monoliths
- **Stateless containers** → State in volumes or external services
- **Minimal base images** → Alpine, distroless, or scratch
- **No secrets in images** → Inject at runtime

### Image Layers (Ordered by Change Frequency)

```
┌─────────────────────────────────────┐  ← Changes rarely
│ Base image (OS, runtime)            │
├─────────────────────────────────────┤
│ System dependencies                 │
├─────────────────────────────────────┤
│ Application dependencies            │
├─────────────────────────────────────┤
│ Application code                    │  ← Changes often
└─────────────────────────────────────┘
```

---

## When Managing Environments

📚 **References:** [environment-management.md](references/environment-management.md)

### Environment Promotion

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│   Dev   │ → │   QA    │ → │ Staging │ → │  Prod   │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
  Per-dev      Shared        Prod-like     Production
  Local DB     Test data     Real data     Real users
  Fast iter    Integration   E2E tests     Monitored
```

### 🔴 BLOCKING
- **Same artifact across all environments** → Only config changes
- **Staging mirrors production** → Same infra, scaled down
- **Production access restricted** → Audit logs required

### 🟡 WARNING
- **Never copy production data to lower environments** → Use anonymized data

---

## When Implementing Deployment Strategies

📚 **References:** [deployment-strategies.md](references/deployment-strategies.md)

### Strategy Comparison

| Strategy | Risk | Downtime | Rollback | Resource Cost |
|----------|------|----------|----------|---------------|
| **Recreate** | High | Yes | Slow | Low |
| **Rolling** | Medium | No | Medium | Low |
| **Blue-Green** | Low | No | Instant | High (2x) |
| **Canary** | Low | No | Instant | Medium |
| **Feature Flags** | Very Low | No | Instant | Low |

### 🔴 BLOCKING
- **Always have rollback plan** → Automated, tested
- **Monitor deployments** → Automated rollback on errors
- **Database migrations are forward-only** → No breaking changes

---

## When Handling Secrets

📚 **References:** [secrets-management.md](references/secrets-management.md)

### 🔴 BLOCKING
- **Never commit secrets** → Use .gitignore, pre-commit hooks
- **Never log secrets** → Mask in CI/CD output
- **Rotate secrets regularly** → Automate rotation
- **Least privilege** → Only access what's needed

### Secret Storage Options

| Option | Use Case | Example |
|--------|----------|---------|
| Environment variables | Simple deployments | Docker env |
| Secret managers | Enterprise | HashiCorp Vault, AWS Secrets Manager |
| CI/CD secrets | Pipeline only | GitHub Secrets, GitLab CI vars |
| Config files (encrypted) | GitOps | SOPS, sealed-secrets |

---

## When Implementing Monitoring

📚 **References:** [observability.md](references/observability.md)

### Three Pillars of Observability

| Pillar | Purpose | Tools |
|--------|---------|-------|
| **Logs** | What happened | ELK, Loki, CloudWatch |
| **Metrics** | How much/many | Prometheus, Grafana |
| **Traces** | Request flow | Jaeger, Zipkin |

### 🔴 BLOCKING - Key Metrics

| Type | Examples |
|------|----------|
| **RED** (Request) | Rate, Errors, Duration |
| **USE** (Resources) | Utilization, Saturation, Errors |
| **Business** | Orders, Revenue, Users |

### 🔴 BLOCKING
- **Alert on symptoms, not causes** → "Slow response" not "High CPU"
- **Every alert is actionable** → No alert fatigue
- **Dashboards for investigation** → Not for monitoring

---

# Part 2: Tool-Specific Guidance

## Docker Best Practices

📚 **References:** [docker-guide.md](references/docker-guide.md)

### 🔴 BLOCKING - Dockerfile

```dockerfile
# ✅ CORRECT - Multi-stage, minimal, secure
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependency files first (better caching)
COPY package*.json ./
RUN npm ci --only=production

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS production

# Security: Non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nodejs -u 1001
USER nodejs

WORKDIR /app

# Copy only what's needed
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules

EXPOSE 3000
CMD ["node", "dist/main.js"]
```

### 🔴 WRONG Examples

```dockerfile
# 🔴 WRONG - Running as root
FROM node:20
COPY . .
CMD ["node", "app.js"]

# 🔴 WRONG - Secrets in build
ARG DATABASE_PASSWORD
ENV DB_PASS=$DATABASE_PASSWORD

# 🔴 WRONG - Installing unnecessary tools
RUN apt-get install vim curl wget telnet

# 🔴 WRONG - Not using multi-stage
COPY . .
RUN npm install
RUN npm run build
# Includes dev dependencies and source in final image!
```

---

## Docker Compose Best Practices

📚 **References:** [docker-compose-guide.md](references/docker-compose-guide.md)

### 🔴 BLOCKING

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://db:5432/app
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
    networks:
      - backend

  db:
    image: postgres:16-alpine
    volumes:
      - db-data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

volumes:
  db-data:

networks:
  backend:
    driver: bridge

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

---

## GitHub Actions Best Practices

📚 **References:** [github-actions-guide.md](references/github-actions-guide.md)

### 🔴 BLOCKING

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Stage 1: Fast checks
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run lint

  # Stage 2: Build and test
  test:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run test:ci
      - uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  # Stage 3: Security scan
  security:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          exit-code: '1'
          severity: 'CRITICAL,HIGH'

  # Stage 4: Build and push image
  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
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
            type=sha,prefix=
            type=ref,event=branch
            type=semver,pattern={{version}}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # Stage 5: Deploy to staging
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - name: Deploy to staging
        run: |
          echo "Deploying ${{ needs.build.outputs.image-tag }} to staging"
          # Add deployment commands here

  # Stage 6: Deploy to production
  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Deploy to production
        run: |
          echo "Deploying ${{ needs.build.outputs.image-tag }} to production"
          # Add deployment commands here
```

---

## Dagger CI Best Practices (Go SDK)

📚 **References:** [dagger-guide.md](references/dagger-guide.md)

### 🔴 BLOCKING

```go
// ci/main.go
package main

import (
    "context"
    "dagger/ci/internal/dagger"
)

type Ci struct{}

// Build compiles the application
func (m *Ci) Build(ctx context.Context, source *dagger.Directory) *dagger.Directory {
    return dag.Container().
        From("node:20-alpine").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithExec([]string{"npm", "ci"}).
        WithExec([]string{"npm", "run", "build"}).
        Directory("/app/dist")
}

// Test runs unit tests
func (m *Ci) Test(ctx context.Context, source *dagger.Directory) (string, error) {
    return dag.Container().
        From("node:20-alpine").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithExec([]string{"npm", "ci"}).
        WithExec([]string{"npm", "run", "test:ci"}).
        Stdout(ctx)
}

// Lint checks code quality
func (m *Ci) Lint(ctx context.Context, source *dagger.Directory) (string, error) {
    return dag.Container().
        From("node:20-alpine").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithExec([]string{"npm", "ci"}).
        WithExec([]string{"npm", "run", "lint"}).
        Stdout(ctx)
}

// Publish builds and pushes container image
func (m *Ci) Publish(
    ctx context.Context,
    source *dagger.Directory,
    registry string,
    username string,
    password *dagger.Secret,
) (string, error) {
    // Build production image
    container := dag.Container().
        From("node:20-alpine").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithExec([]string{"npm", "ci", "--only=production"}).
        WithExec([]string{"npm", "run", "build"}).
        WithEntrypoint([]string{"node", "dist/main.js"})

    // Push to registry
    return container.
        WithRegistryAuth(registry, username, password).
        Publish(ctx, registry+"/myapp:latest")
}

// All runs the complete pipeline
func (m *Ci) All(ctx context.Context, source *dagger.Directory) error {
    // Run lint and test in parallel
    _, err := m.Lint(ctx, source)
    if err != nil {
        return err
    }

    _, err = m.Test(ctx, source)
    if err != nil {
        return err
    }

    // Build if all checks pass
    _ = m.Build(ctx, source)
    return nil
}
```

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] No secrets in code or config files
- [ ] Dockerfile uses non-root user
- [ ] Dockerfile uses multi-stage builds
- [ ] Pipeline fails fast (lint before tests)
- [ ] Same artifact through all environments
- [ ] Rollback plan exists and tested
- [ ] Production deployments are automated
- [ ] Health checks configured

### 🟡 WARNING
- [ ] Dependencies are cached in CI
- [ ] Base images are pinned (version tags)
- [ ] Resource limits set on containers
- [ ] Secrets use secret managers, not env vars
- [ ] Deployments use blue-green or canary

### 🟢 BEST PRACTICE
- [ ] Infrastructure as Code (Terraform, Ansible)
- [ ] GitOps for deployments
- [ ] Monitoring dashboards for each service
- [ ] Alerts are actionable, not noisy
- [ ] Chaos engineering practices
- [ ] Security scanning in pipeline (SAST/DAST)
