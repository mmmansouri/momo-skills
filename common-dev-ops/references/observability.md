# Observability Guide

## Overview

Comprehensive guide for implementing the three pillars of observability: Logs, Metrics, and Traces.

---

## The Three Pillars

```
┌─────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY                             │
│                                                              │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│   │    LOGS     │   │   METRICS   │   │   TRACES    │       │
│   │             │   │             │   │             │       │
│   │ What        │   │ How much    │   │ Where       │       │
│   │ happened    │   │ how many    │   │ request     │       │
│   │             │   │             │   │ went        │       │
│   └─────────────┘   └─────────────┘   └─────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

| Pillar | Question | Example |
|--------|----------|---------|
| Logs | What happened? | "User 123 logged in" |
| Metrics | How much/many? | "500 requests/min, 2% errors" |
| Traces | Where did the request go? | "API → Auth → DB → Cache" |

---

## Logging

### Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| ERROR | Application errors requiring attention | Database connection failed |
| WARN | Unexpected but handled situations | Retry succeeded after failure |
| INFO | Normal operational events | User logged in, Order created |
| DEBUG | Detailed diagnostic information | Request payload, SQL queries |
| TRACE | Very detailed debugging | Function entry/exit |

### 🔴 BLOCKING Rules

1. **Structured Logging (JSON)**

```typescript
// 🔴 WRONG: Unstructured
console.log('User 123 created order 456');

// ✅ CORRECT: Structured JSON
logger.info({
  event: 'order_created',
  userId: 123,
  orderId: 456,
  amount: 99.99,
  currency: 'EUR'
});
```

2. **No Sensitive Data**

```typescript
// 🔴 WRONG
logger.info({ email, password, creditCard });

// ✅ CORRECT
logger.info({ 
  email: maskEmail(email),  // j***@example.com
  hasPassword: !!password,
  cardLast4: creditCard.slice(-4)
});
```

3. **Correlation IDs**

```typescript
// Add request ID to all logs
const requestId = req.headers['x-request-id'] || uuid();
logger.info({ requestId, event: 'request_start', path: req.path });
// ... later
logger.info({ requestId, event: 'request_end', duration: 150 });
```

### Log Output

```typescript
// ✅ Always log to stdout/stderr
const logger = winston.createLogger({
  transports: [
    new winston.transports.Console({
      format: winston.format.json()
    })
  ]
});

// Let the platform handle log aggregation
// Docker captures stdout/stderr
// Kubernetes forwards to logging backend
```

---

## Metrics

### Metric Types

| Type | Use Case | Example |
|------|----------|---------|
| Counter | Cumulative totals | Total requests, errors |
| Gauge | Current value | Active connections, queue size |
| Histogram | Distribution | Request latency percentiles |
| Summary | Similar to histogram | Request duration |

### Key Metrics Frameworks

#### RED Method (Request-focused)

| Metric | Description | Example |
|--------|-------------|---------|
| **R**ate | Requests per second | 1000 req/s |
| **E**rrors | Failed requests per second | 10 errors/s (1%) |
| **D**uration | Time per request | p50: 50ms, p99: 200ms |

#### USE Method (Resource-focused)

| Metric | Description | Example |
|--------|-------------|---------|
| **U**tilization | % resource busy | CPU: 70% |
| **S**aturation | Queue length | Pending requests: 50 |
| **E**rrors | Error count | Disk errors: 0 |

### 🔴 BLOCKING Metrics

```typescript
// These metrics are REQUIRED for every service

// 1. Request Rate
const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'path', 'status']
});

// 2. Error Rate
const httpErrorsTotal = new Counter({
  name: 'http_errors_total',
  help: 'Total HTTP errors',
  labelNames: ['method', 'path', 'error_type']
});

// 3. Request Duration
const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration',
  labelNames: ['method', 'path'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 5]
});

// 4. Business Metrics
const ordersCreated = new Counter({
  name: 'orders_created_total',
  help: 'Total orders created',
  labelNames: ['payment_method', 'currency']
});
```

### Prometheus Exposition

```typescript
// /metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});
```

---

## Tracing

### Trace Structure

```
Trace (end-to-end request)
├── Span: API Gateway (100ms)
│   ├── Span: Authentication (20ms)
│   └── Span: API Handler (80ms)
│       ├── Span: Database Query (30ms)
│       ├── Span: Cache Lookup (5ms)
│       └── Span: External API Call (40ms)
└── Total: 100ms
```

### OpenTelemetry Setup

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';

const sdk = new NodeSDK({
  serviceName: 'my-api',
  traceExporter: new OTLPTraceExporter({
    url: 'http://jaeger:4318/v1/traces'
  }),
  instrumentations: [getNodeAutoInstrumentations()]
});

sdk.start();
```

### Custom Spans

```typescript
import { trace } from '@opentelemetry/api';

const tracer = trace.getTracer('my-service');

async function processOrder(order: Order) {
  return tracer.startActiveSpan('processOrder', async (span) => {
    try {
      span.setAttribute('order.id', order.id);
      span.setAttribute('order.amount', order.amount);
      
      await validateOrder(order);
      await chargePayment(order);
      await sendConfirmation(order);
      
      span.setStatus({ code: SpanStatusCode.OK });
    } catch (error) {
      span.setStatus({ code: SpanStatusCode.ERROR });
      span.recordException(error);
      throw error;
    } finally {
      span.end();
    }
  });
}
```

---

## Alerting

### 🔴 BLOCKING: Alert Design Principles

1. **Alert on Symptoms, Not Causes**

```yaml
# 🔴 WRONG: Alerting on cause
- alert: HighCPU
  expr: cpu_usage > 80%
  # CPU can be high without user impact

# ✅ CORRECT: Alerting on symptom
- alert: HighLatency
  expr: http_request_duration_p99 > 500ms
  # This directly impacts users
```

2. **Every Alert is Actionable**

```yaml
# ✅ GOOD: Clear action required
- alert: DatabaseConnectionPoolExhausted
  annotations:
    summary: "DB connection pool at capacity"
    runbook: "https://wiki/runbooks/db-pool-exhausted"
    action: "Scale DB connections or investigate slow queries"

# 🔴 BAD: No clear action
- alert: SomethingSeemsBroken
  annotations:
    summary: "Something might be wrong"
```

3. **Severity Levels**

| Severity | Response Time | Example |
|----------|---------------|---------|
| Critical | Immediate (page) | Service down, data loss |
| Warning | Same day | Degraded performance |
| Info | When convenient | Disk space warning |

### Alert Examples

```yaml
# Prometheus alerting rules
groups:
  - name: slo-alerts
    rules:
      # Error rate SLO breach
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          / sum(rate(http_requests_total[5m])) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate above 1% SLO"
          
      # Latency SLO breach
      - alert: HighLatency
        expr: |
          histogram_quantile(0.99, 
            sum(rate(http_request_duration_seconds_bucket[5m])) 
            by (le)) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p99 latency above 500ms"
```

---

## Dashboards

### Dashboard Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  Level 1: Executive Dashboard (1 per org)                   │
│  - Overall system health                                     │
│  - Business KPIs                                            │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│  Level 2: Service Dashboard (1 per service)                 │
│  - RED metrics                                               │
│  - Dependencies status                                       │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│  Level 3: Debug Dashboard (1 per service)                   │
│  - Detailed metrics                                          │
│  - Resource usage                                           │
└─────────────────────────────────────────────────────────────┘
```

### Service Dashboard Template

```
┌─────────────────────────────────────────────────────────────┐
│  Service: Order API                                          │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Request    │  │ Error      │  │ p99        │            │
│  │ Rate       │  │ Rate       │  │ Latency    │            │
│  │ 1.2k/s     │  │ 0.5%       │  │ 120ms      │            │
│  └────────────┘  └────────────┘  └────────────┘            │
├─────────────────────────────────────────────────────────────┤
│  Request Rate Over Time                                      │
│  ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█▇▆▅▄▃▂▁                             │
├─────────────────────────────────────────────────────────────┤
│  Error Rate Over Time                                        │
│  ▁▁▁▁▂▁▁▁▁▁▁▅▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁                             │
├─────────────────────────────────────────────────────────────┤
│  Latency Distribution (p50, p90, p99)                       │
│  ▁▂▃▄▅▆▇█                                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Tool Stack

### Logging

| Tool | Type | Best For |
|------|------|----------|
| ELK Stack | Self-hosted | Full control, large scale |
| Loki | Self-hosted | Lightweight, Grafana integration |
| CloudWatch | AWS | AWS native workloads |
| Datadog | SaaS | All-in-one solution |

### Metrics

| Tool | Type | Best For |
|------|------|----------|
| Prometheus | Self-hosted | Kubernetes, microservices |
| InfluxDB | Self-hosted | Time-series focus |
| CloudWatch | AWS | AWS native workloads |
| Datadog | SaaS | All-in-one solution |

### Tracing

| Tool | Type | Best For |
|------|------|----------|
| Jaeger | Self-hosted | Kubernetes native |
| Zipkin | Self-hosted | Simple setup |
| AWS X-Ray | AWS | AWS native workloads |
| Datadog APM | SaaS | All-in-one solution |
