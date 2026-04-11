# Pipeline Patterns

## Overview

Common patterns for structuring CI/CD pipelines effectively.

---

## Pattern 1: Trunk-Based Development

### Description

All developers work on a single main branch with short-lived feature branches.

### Pipeline Structure

```
Feature Branch        Main Branch
     │                    │
     ▼                    ▼
┌─────────┐          ┌─────────┐
│  Build  │          │  Build  │
│  Test   │   PR     │  Test   │
│  Lint   │ ──────►  │  Scan   │
└─────────┘  Merge   │ Deploy  │
                     └─────────┘
```

### When to Use

- Small teams (< 10 developers)
- Mature testing culture
- Fast pipeline (< 15 min)

### 🔴 BLOCKING Rules

- Feature branches live < 24 hours
- All tests pass before merge
- Main is always deployable

---

## Pattern 2: GitFlow Pipeline

### Description

Structured branching with develop, release, and main branches.

### Pipeline Structure

```
Feature → Develop → Release → Main → Hotfix
    │         │         │        │       │
    ▼         ▼         ▼        ▼       ▼
  Tests    Tests    Tests    Deploy   Deploy
  Lint     Scan     E2E      Prod     Prod
           Stage
```

### When to Use

- Scheduled releases
- Multiple environments
- Regulated industries

### 🔴 BLOCKING Rules

- Never commit directly to main
- Release branches are frozen (bugfixes only)
- Hotfixes merge to both main and develop

---

## Pattern 3: Environment Pipeline

### Description

Each environment has its own pipeline stage.

### Pipeline Structure

```
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│  Dev   │ → │   QA   │ → │ Stage  │ → │  Prod  │
└────────┘   └────────┘   └────────┘   └────────┘
     │            │            │            │
   Auto        Auto         Auto        Manual
  Deploy      Deploy       Deploy       Approve
```

### Promotion Rules

| From → To | Trigger | Gate |
|-----------|---------|------|
| Dev → QA | Auto on merge | Tests pass |
| QA → Staging | Auto | Integration tests pass |
| Staging → Prod | Manual | E2E + approval |

---

## Pattern 4: Matrix Pipeline

### Description

Test across multiple configurations simultaneously.

### Example: Multi-Platform Testing

```yaml
strategy:
  matrix:
    os: [ubuntu, windows, macos]
    node: [18, 20, 22]
    
# Creates 9 parallel jobs:
# ubuntu-18, ubuntu-20, ubuntu-22
# windows-18, windows-20, windows-22
# macos-18, macos-20, macos-22
```

### When to Use

- Library/package development
- Cross-platform applications
- Multiple runtime versions support

---

## Pattern 5: Fan-Out / Fan-In

### Description

Parallel execution with aggregation.

### Pipeline Structure

```
        ┌──────────┐
        │   Build  │
        └────┬─────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌──────┐ ┌──────┐ ┌──────┐
│Test 1│ │Test 2│ │Test 3│  Fan-Out
└──┬───┘ └──┬───┘ └──┬───┘
   │        │        │
   └────────┼────────┘
            ▼
      ┌──────────┐
      │ Aggregate│              Fan-In
      │  Report  │
      └────┬─────┘
           ▼
      ┌──────────┐
      │  Deploy  │
      └──────────┘
```

### Use Cases

- Large test suites (sharding)
- Multiple scan types
- Multi-region deployment

---

## Pattern 6: Canary Pipeline

### Description

Gradual rollout with automatic rollback.

### Pipeline Structure

```
┌─────────────────────────────────────────────┐
│                 Production                   │
│  ┌─────────┐                 ┌───────────┐  │
│  │ Canary  │   Promote ───►  │   Stable  │  │
│  │   5%    │     or          │    95%    │  │
│  └─────────┘   Rollback      └───────────┘  │
└─────────────────────────────────────────────┘
```

### Promotion Criteria

```yaml
canary:
  steps:
    - weight: 5
      pause: { duration: 10m }
      analysis:
        - metric: error-rate
          threshold: 1%
    - weight: 25
      pause: { duration: 30m }
    - weight: 50
      pause: { duration: 1h }
    - weight: 100
```

### 🔴 BLOCKING Rules

- Automated metrics collection required
- Rollback must be automatic on threshold breach
- Traffic split must be configurable

---

## Pattern 7: Blue-Green Pipeline

### Description

Two identical environments, instant switchover.

### Pipeline Structure

```
Load Balancer
      │
      ├──────────────────┐
      ▼                  │
┌──────────┐       ┌──────────┐
│   Blue   │       │  Green   │
│ (Active) │       │(Standby) │
└──────────┘       └──────────┘

Deploy to Green → Test → Switch LB → Green Active
```

### Switchover Process

1. Deploy new version to inactive environment
2. Run smoke tests on inactive
3. Switch load balancer
4. Keep old environment for instant rollback

---

## Pattern 8: Feature Flag Pipeline

### Description

Deploy code with features disabled, enable separately.

### Pipeline Structure

```
Code Deploy ────────────────► Production
     │                             │
     │                             ▼
     │                      ┌────────────┐
     │                      │  Feature   │
     │                      │   Flags    │
     │                      └────────────┘
     │                             │
     ▼                             ▼
Feature Branch              Gradual Enable
(flag: off)                 (1% → 10% → 100%)
```

### Benefits

- Decouple deploy from release
- A/B testing built-in
- Instant disable without deploy

---

## Choosing the Right Pattern

| Context | Recommended Pattern |
|---------|-------------------|
| Startup, fast iteration | Trunk-based |
| Enterprise, compliance | GitFlow |
| Microservices | Environment + Canary |
| Platform/Library | Matrix |
| High availability | Blue-Green |
| Experimentation | Feature Flags |

---

## Anti-Patterns

### 🔴 Avoid These

1. **Merge Train**: Long queue of PRs waiting to merge
2. **Deploy Friday**: Production deploys before weekend
3. **YOLO Deploy**: Skipping staging/testing
4. **Manual Pipeline**: Running steps by hand
5. **Zombie Branches**: Long-lived feature branches

---

## Migration Path

### From Manual to Automated

```
Week 1-2: Add build + lint
Week 3-4: Add unit tests
Week 5-6: Add integration tests
Week 7-8: Add staging deploy
Week 9+:  Add production deploy
```

### From Monolith to Microservices

```
Phase 1: Single pipeline for monolith
Phase 2: Extract shared pipeline templates
Phase 3: Per-service pipelines
Phase 4: Service mesh + distributed tracing
```
