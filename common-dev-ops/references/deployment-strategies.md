# Deployment Strategies Guide

## Overview

Strategies for deploying applications with minimal risk and downtime.

---

## Strategy Comparison

| Strategy | Downtime | Risk | Rollback Speed | Resource Cost | Complexity |
|----------|----------|------|----------------|---------------|------------|
| Recreate | Yes | High | Slow | Low | Low |
| Rolling | No | Medium | Medium | Low | Medium |
| Blue-Green | No | Low | Instant | High (2x) | Medium |
| Canary | No | Very Low | Instant | Medium | High |
| Feature Flags | No | Very Low | Instant | Low | Medium |
| A/B Testing | No | Low | Instant | Medium | High |

---

## 1. Recreate Deployment

### Description

Stop old version completely, then start new version.

### Diagram

```
Time →
─────────────────────────────────────────────────────
v1  ████████████▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
                  │ Downtime │
v2  ░░░░░░░░░░░░░░░░░░░░░░░████████████████████████
```

### When to Use

- Stateful applications that can't run multiple versions
- Development/testing environments
- When downtime is acceptable

### 🔴 BLOCKING

- Schedule during low-traffic windows
- Have rollback plan ready
- Verify data migration before shutdown

### Example (Kubernetes)

```yaml
spec:
  strategy:
    type: Recreate
```

---

## 2. Rolling Deployment

### Description

Gradually replace old instances with new ones.

### Diagram

```
Time →
─────────────────────────────────────────────────────
v1  ████████████████▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░
v2  ░░░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓████████████████████████

     └── Both versions running during transition ──┘
```

### When to Use

- Standard deployments
- Stateless applications
- When zero-downtime is required

### 🔴 BLOCKING Rules

- Application must handle concurrent versions
- Database changes must be backward compatible
- Health checks must be reliable

### Example (Kubernetes)

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Extra pods during update
      maxUnavailable: 25%  # Max pods down during update
```

---

## 3. Blue-Green Deployment

### Description

Maintain two identical environments, switch traffic instantly.

### Diagram

```
                    Load Balancer
                         │
         ┌───────────────┼───────────────┐
         │                               │
         ▼                               ▼
    ┌─────────┐                     ┌─────────┐
    │  Blue   │   Switch 100%       │  Green  │
    │  (v1)   │  ────────────────►  │  (v2)   │
    │ Active  │                     │ Standby │
    └─────────┘                     └─────────┘
```

### When to Use

- Mission-critical applications
- When instant rollback is required
- Compliance requirements for easy auditing

### 🔴 BLOCKING Rules

- Both environments must be identical
- Database must support both versions
- DNS/LB switch must be instant

### Implementation

```bash
# 1. Deploy v2 to Green (inactive)
deploy_to_green v2

# 2. Test Green environment
run_smoke_tests green.internal.example.com

# 3. Switch traffic
switch_traffic blue green

# 4. Keep Blue for rollback
# If issues: switch_traffic green blue

# 5. After validation, Blue becomes next Green
```

---

## 4. Canary Deployment

### Description

Route small percentage of traffic to new version, gradually increase.

### Diagram

```
                    Load Balancer
                         │
              ┌──────────┴──────────┐
              │                     │
         95% traffic           5% traffic
              │                     │
              ▼                     ▼
         ┌─────────┐           ┌─────────┐
         │ Stable  │           │ Canary  │
         │  (v1)   │           │  (v2)   │
         └─────────┘           └─────────┘
```

### Traffic Progression

```
Phase 1:  v1: 99%  │  v2: 1%   (smoke test)
Phase 2:  v1: 95%  │  v2: 5%   (monitor 10 min)
Phase 3:  v1: 75%  │  v2: 25%  (monitor 30 min)
Phase 4:  v1: 50%  │  v2: 50%  (monitor 1 hour)
Phase 5:  v1: 0%   │  v2: 100% (complete)
```

### When to Use

- High-traffic applications
- When you need real-user validation
- Risk-averse deployments

### 🔴 BLOCKING Rules

- Automated metrics collection required
- Clear success/failure criteria defined
- Automatic rollback on threshold breach

### Example (Kubernetes + Istio)

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
spec:
  http:
  - route:
    - destination:
        host: myapp
        subset: stable
      weight: 95
    - destination:
        host: myapp
        subset: canary
      weight: 5
```

### Canary Analysis

```yaml
# Automated canary analysis
analysis:
  interval: 5m
  threshold: 5
  metrics:
    - name: error-rate
      threshold: 1%
      query: |
        sum(rate(http_requests_total{status=~"5.*"}[5m]))
        / sum(rate(http_requests_total[5m])) * 100
    - name: latency-p99
      threshold: 500ms
      query: |
        histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

---

## 5. Feature Flags

### Description

Deploy code with features disabled, enable separately from deployment.

### Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Application v2                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Feature A   │  │ Feature B   │  │ Feature C   │  │
│  │   (ON)      │  │   (OFF)     │  │   (10%)     │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Feature Flag   │
                  │    Service      │
                  └─────────────────┘
```

### When to Use

- Trunk-based development
- A/B testing
- Gradual feature rollout
- Kill switches for problematic features

### 🔴 BLOCKING Rules

- Feature flags have clear ownership
- Flags are cleaned up after full rollout
- Default state is well-defined

### Implementation

```typescript
// Feature flag check
if (await featureFlags.isEnabled('new-checkout', { userId })) {
  return newCheckoutFlow();
} else {
  return legacyCheckoutFlow();
}
```

### Feature Flag Lifecycle

```
1. Create flag (default: OFF)
2. Deploy code behind flag
3. Enable for internal users (1%)
4. Enable for beta users (10%)
5. Enable for all users (100%)
6. Remove flag from code
7. Delete flag from service
```

---

## 6. A/B Testing

### Description

Route users to different versions based on criteria, measure outcomes.

### Diagram

```
                    ┌─────────────────┐
                    │   User Request  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  A/B Assignment │
                    │    Service      │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     Bucket A (50%)                Bucket B (50%)
              │                             │
              ▼                             ▼
    ┌─────────────────┐          ┌─────────────────┐
    │   Version A     │          │   Version B     │
    │  (Control)      │          │  (Experiment)   │
    └─────────────────┘          └─────────────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
                    ┌────────▼────────┐
                    │    Analytics    │
                    │  (Compare KPIs) │
                    └─────────────────┘
```

### When to Use

- Validating UX changes
- Testing pricing strategies
- Measuring conversion optimization

### 🔴 BLOCKING Rules

- Statistical significance required
- Same user = same bucket (sticky sessions)
- Clear success metrics defined upfront

---

## Database Deployment Strategies

### 🔴 BLOCKING: Forward-Only Migrations

```sql
-- ✅ CORRECT: Additive change
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- 🔴 WRONG: Breaking change
ALTER TABLE users DROP COLUMN email;
```

### Expand-Contract Pattern

```
Phase 1: Expand
  - Add new column (nullable)
  - Deploy code that writes to both
  
Phase 2: Migrate
  - Backfill data to new column
  - Verify data integrity

Phase 3: Contract
  - Remove old column usage from code
  - Make new column required
  - (Optional) Remove old column
```

### Example

```sql
-- Phase 1: Expand
ALTER TABLE users ADD COLUMN full_name VARCHAR(200);

-- Phase 2: Migrate (application writes to both)
UPDATE users SET full_name = first_name || ' ' || last_name;

-- Phase 3: Contract (after code removes old column usage)
ALTER TABLE users DROP COLUMN first_name;
ALTER TABLE users DROP COLUMN last_name;
```

---

## Rollback Strategies

### Immediate Rollback

| Strategy | Rollback Method |
|----------|----------------|
| Recreate | Redeploy previous version |
| Rolling | Reverse rolling update |
| Blue-Green | Switch LB back |
| Canary | Route 100% to stable |
| Feature Flags | Disable flag |

### Rollback Checklist

```markdown
## Before Deployment
- [ ] Previous version image available
- [ ] Rollback runbook documented
- [ ] Database migration is reversible OR forward-only

## During Incident
- [ ] Identify issue severity
- [ ] If critical: rollback immediately
- [ ] If moderate: attempt hotfix OR rollback
- [ ] Notify stakeholders

## After Rollback
- [ ] Verify service restored
- [ ] Collect logs and metrics
- [ ] Schedule post-mortem
```
