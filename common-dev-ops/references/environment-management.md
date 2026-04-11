# Environment Management Guide

## Overview

Managing consistent, reproducible environments across the development lifecycle.

---

## Environment Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                      PRODUCTION                              │
│  Real users, real data, monitored, HA                       │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│                       STAGING                                │
│  Production-like, E2E tests, final validation               │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│                         QA                                   │
│  Integration tests, shared testing                          │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│                     DEVELOPMENT                              │
│  Per-developer, local/ephemeral                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Characteristics

| Environment | Data | Access | Stability | Monitoring |
|-------------|------|--------|-----------|------------|
| Development | Synthetic | Open | Unstable | Minimal |
| QA | Seeded/Anonymized | Team | Semi-stable | Basic |
| Staging | Copy of prod (anonymized) | Restricted | Stable | Full |
| Production | Real | Highly restricted | Stable | Full |

---

## 🔴 BLOCKING Rules

### 1. Same Artifact Everywhere

```
Build Once → Deploy Everywhere

  ┌─────────┐
  │  Build  │
  └────┬────┘
       │
   Image:v1.2.3
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
   ┌──────┐      ┌──────┐      ┌──────┐
   │  Dev │      │ Stage│      │ Prod │
   └──────┘      └──────┘      └──────┘
   
   Same image, different config!
```

### 2. Configuration per Environment

```yaml
# ✅ CORRECT: Environment-specific config
# config/development.yaml
database:
  host: localhost
  pool_size: 5

# config/production.yaml
database:
  host: ${DATABASE_HOST}  # From env var
  pool_size: 20

# 🔴 WRONG: Hardcoded in code
# app.js
const dbHost = 'prod-db.company.com';
```

### 3. Never Use Production Data in Lower Environments

```bash
# 🔴 WRONG
pg_dump prod_db | psql staging_db

# ✅ CORRECT: Use anonymization tool
pg_dump prod_db | anonymize | psql staging_db

# Or use synthetic data generation
npm run seed:qa
```

---

## Configuration Management

### 12-Factor Config

```
┌─────────────────────────────────────────────┐
│  Application                                 │
│                                              │
│  process.env.DATABASE_URL  ──────────┐      │
│  process.env.API_KEY       ──────────┤      │
│  process.env.LOG_LEVEL     ──────────┤      │
└──────────────────────────────────────┼──────┘
                                       │
                               ┌───────▼───────┐
                               │  Environment  │
                               │   Variables   │
                               └───────────────┘
```

### Config Priority (Low → High)

1. **Defaults** in code
2. **Config files** (checked into repo)
3. **Environment-specific files** (.env.production)
4. **Environment variables** (highest priority)

### Example Structure

```
config/
├── default.yaml        # Base config
├── development.yaml    # Dev overrides
├── test.yaml          # Test overrides
├── staging.yaml       # Staging overrides
└── production.yaml    # Prod overrides (minimal)
```

---

## Secret Management

### Secret Types

| Type | Examples | Rotation |
|------|----------|----------|
| API Keys | Stripe, AWS | Quarterly |
| Database Credentials | Connection strings | On incident |
| Encryption Keys | JWT secrets | Annually |
| Service Tokens | Inter-service auth | Monthly |

### Storage Options

| Solution | Use Case | Cost |
|----------|----------|------|
| Environment variables | Simple deployments | Free |
| GitHub Secrets | GitHub Actions | Free |
| AWS Secrets Manager | AWS workloads | $0.40/secret/month |
| HashiCorp Vault | Enterprise, on-prem | Free/Enterprise |
| Doppler | Multi-environment | Free tier available |

### 🔴 BLOCKING

```bash
# Never commit secrets
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "*.pem" >> .gitignore
echo "*.key" >> .gitignore

# Use secret scanning
git secrets --install
git secrets --register-aws
```

---

## Environment Parity

### Infrastructure Parity

```yaml
# terraform/modules/app/main.tf
# Same module, different vars per environment

module "app" {
  source = "./modules/app"
  
  instance_count = var.environment == "production" ? 3 : 1
  instance_type  = var.environment == "production" ? "t3.large" : "t3.micro"
  
  # Same architecture, different scale
}
```

### Database Parity

```yaml
# All environments use same DB version
services:
  db:
    image: postgres:16.1-alpine  # Same everywhere
```

### What SHOULD Differ

| Component | Development | Production |
|-----------|-------------|------------|
| Scale | Single instance | Multiple/HA |
| Resources | Minimal | Right-sized |
| Data | Synthetic | Real |
| Monitoring | Minimal | Full |
| Backups | None | Automated |

### What Should NOT Differ

| Component | Requirement |
|-----------|-------------|
| OS/Runtime | Same version |
| Dependencies | Same versions |
| Architecture | Same topology |
| Code | Same artifact |

---

## Environment Promotion

### Promotion Flow

```
┌──────────────────────────────────────────────────────────┐
│                    Git Branch Flow                        │
│                                                           │
│  feature/* ──► develop ──► release/* ──► main            │
│      │            │            │           │              │
│      ▼            ▼            ▼           ▼              │
│   [Dev]        [QA]       [Staging]    [Prod]            │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Promotion Gates

| Gate | From → To | Criteria |
|------|-----------|----------|
| 1 | Dev → QA | Unit tests pass |
| 2 | QA → Staging | Integration tests pass, QA sign-off |
| 3 | Staging → Prod | E2E tests pass, load test, approval |

### Automated Promotion

```yaml
# GitHub Actions example
on:
  push:
    branches: [main]

jobs:
  promote:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Staging
        run: ./deploy.sh staging
      
      - name: Run E2E Tests
        run: npm run test:e2e
      
      - name: Deploy to Production
        if: success()
        run: ./deploy.sh production
```

---

## Ephemeral Environments

### Per-PR Environments

```yaml
# Deploy preview environment for each PR
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  deploy-preview:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy Preview
        run: |
          PREVIEW_URL="pr-${{ github.event.number }}.preview.example.com"
          ./deploy.sh preview --url $PREVIEW_URL
      
      - name: Comment URL
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              body: '🚀 Preview: https://pr-${{ github.event.number }}.preview.example.com'
            })
```

### Cleanup

```yaml
on:
  pull_request:
    types: [closed]

jobs:
  cleanup-preview:
    runs-on: ubuntu-latest
    steps:
      - name: Delete Preview Environment
        run: ./destroy-preview.sh pr-${{ github.event.number }}
```

---

## Local Development

### Docker Compose for Local

```yaml
# docker-compose.yml
services:
  app:
    build: .
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgres://postgres:postgres@db:5432/dev
    ports:
      - "3000:3000"
    depends_on:
      - db
      - redis

  db:
    image: postgres:16.1-alpine
    environment:
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres-data:
```

### .env.example

```bash
# .env.example (commit this)
DATABASE_URL=postgres://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379
API_KEY=your-api-key-here
LOG_LEVEL=debug

# .env (do NOT commit)
DATABASE_URL=postgres://dev:secret@localhost:5432/myapp
REDIS_URL=redis://localhost:6379
API_KEY=sk_test_actual_key
LOG_LEVEL=debug
```
