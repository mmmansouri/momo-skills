# Pipeline Design Guide

## Overview

This document provides detailed guidance on designing effective CI/CD pipelines that are fast, reliable, and maintainable.

---

## Pipeline Philosophy

### Core Objectives

1. **Speed**: Fast feedback loops enable rapid iteration
2. **Reliability**: Consistent, reproducible builds every time
3. **Visibility**: Clear status and easy debugging
4. **Security**: Secure by default, secrets properly managed

### The Build Triangle

```
          Speed
           /\
          /  \
         /    \
        /______\
   Reliability  Cost
```

You can optimize for two at the expense of the third. Choose wisely based on your context.

---

## Pipeline Stages in Detail

### Stage 1: Build

**Purpose**: Compile code, verify syntax, prepare artifacts

**What to include**:
- Dependency installation (cached)
- Code compilation/transpilation
- Asset bundling
- Linting and formatting checks

**🔴 BLOCKING Rules**:
- Build must be deterministic (same input → same output)
- Build artifacts must be versioned
- Build logs must be preserved

**Example timing**: 1-5 minutes

### Stage 2: Test

**Purpose**: Verify correctness at multiple levels

**Test Pyramid**:
```
        /\
       /E2E\        (few, slow, expensive)
      /------\
     / Integr \     (moderate)
    /----------\
   /    Unit    \   (many, fast, cheap)
  /______________\
```

**🔴 BLOCKING Rules**:
- Unit tests run on every commit
- Integration tests run on every PR
- E2E tests run before production deploy

### Stage 3: Security Scan

**Purpose**: Identify vulnerabilities before deployment

**Types of scans**:
| Scan Type | When | What |
|-----------|------|------|
| SAST | Every commit | Source code vulnerabilities |
| DAST | Pre-deploy | Running application vulnerabilities |
| Dependency | Every build | Known CVEs in dependencies |
| Secret | Every commit | Leaked credentials |

### Stage 4: Package

**Purpose**: Create deployable artifacts

**🔴 BLOCKING Rules**:
- One artifact per build (immutable)
- Artifact includes version metadata
- Artifact is signed/verified

### Stage 5: Deploy

**Purpose**: Release to target environment

**Environment progression**:
```
Dev → QA → Staging → Production
```

**🔴 BLOCKING Rules**:
- Never skip environments
- Automated rollback on failure
- Deployment audit trail

---

## Pipeline Triggers

### When to Run What

| Trigger | Pipeline Scope |
|---------|---------------|
| Push to feature branch | Build + Unit tests |
| Pull Request | Full pipeline (no prod deploy) |
| Merge to main | Full pipeline + Staging deploy |
| Release tag | Full pipeline + Production deploy |
| Schedule (nightly) | Extended tests, security scans |

---

## Caching Strategy

### What to Cache

1. **Dependencies**: npm/maven/pip packages
2. **Build artifacts**: Compiled code, Docker layers
3. **Test fixtures**: Large test datasets

### Cache Keys

```yaml
# Good: Version-specific cache
cache-key: deps-${{ hashFiles('package-lock.json') }}

# Bad: Generic cache (stale dependencies)
cache-key: deps-main
```

---

## Parallelization

### Independent Stages

Run simultaneously when no dependencies:

```
┌─────────┐
│  Build  │
└────┬────┘
     │
     ├──────────┬──────────┐
     ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│  Lint  │ │  Test  │ │  Scan  │
└────────┘ └────────┘ └────────┘
```

### Test Sharding

Split large test suites across parallel runners:

```
Tests (1000) → 4 runners × 250 tests each
Total time: ~25% of sequential run
```

---

## Failure Handling

### Fail Fast

Order stages by:
1. Speed (fastest first)
2. Failure rate (most likely to fail first)

### Retry Strategy

| Failure Type | Retry? | Action |
|--------------|--------|--------|
| Test failure | No | Fix the code |
| Network timeout | Yes (2x) | Transient, retry |
| Resource exhaustion | Yes (1x) | Scale or wait |
| Build error | No | Fix the code |

---

## Metrics to Track

### Pipeline Health

- **Lead time**: Commit to production
- **Deployment frequency**: Deploys per day/week
- **Failure rate**: % of failed pipelines
- **Recovery time**: Time to fix a broken build

### Target Metrics

| Metric | Good | Elite |
|--------|------|-------|
| Lead time | < 1 day | < 1 hour |
| Deploy frequency | Weekly | On-demand |
| Failure rate | < 15% | < 5% |
| Recovery time | < 1 day | < 1 hour |

---

## Anti-Patterns to Avoid

### 🔴 Pipeline Anti-Patterns

1. **Snowflake pipelines**: Each project has unique config
2. **Manual gates**: Humans required for every deploy
3. **Flaky tests**: Tests that fail randomly
4. **Long-running jobs**: Single jobs > 30 minutes
5. **No caching**: Download everything every build
6. **Secret sprawl**: Secrets duplicated everywhere

---

## Best Practices Summary

1. ✅ Pipeline as code (version controlled)
2. ✅ Fast feedback (< 10 min for basic checks)
3. ✅ Idempotent builds (run twice, same result)
4. ✅ Comprehensive logging
5. ✅ Automated rollback
6. ✅ Environment parity
7. ✅ Security scanning integrated
8. ✅ Metrics and monitoring
