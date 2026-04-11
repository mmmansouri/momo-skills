# Containerization Guide

## Overview

Best practices for containerizing applications using Docker and OCI-compliant tools.

---

## Container Principles

### The 12-Factor App for Containers

| Factor | Container Implementation |
|--------|-------------------------|
| Codebase | One repo → one image |
| Dependencies | All deps in image |
| Config | Environment variables |
| Backing Services | External, via network |
| Build/Release/Run | Separate stages |
| Processes | Stateless, share-nothing |
| Port Binding | EXPOSE + runtime mapping |
| Concurrency | Scale via container count |
| Disposability | Fast startup/shutdown |
| Dev/Prod Parity | Same image everywhere |
| Logs | Stdout/stderr |
| Admin Processes | One-off containers |

---

## Image Design

### Layer Strategy

```
┌─────────────────────────────────────┐
│ Application Code          (changes often) │
├─────────────────────────────────────┤
│ Application Dependencies  (changes sometimes) │
├─────────────────────────────────────┤
│ System Dependencies       (changes rarely) │
├─────────────────────────────────────┤
│ Base Image (OS/Runtime)   (changes rarely) │
└─────────────────────────────────────┘
```

### 🔴 BLOCKING Rules

1. **Order by change frequency**: Least changing → most changing
2. **One concern per layer**: Don't mix install + copy
3. **Clean up in same layer**: `RUN apt install && rm -rf /var/lib/apt/lists/*`

---

## Base Image Selection

### Decision Matrix

| Base Image | Size | Security | Use Case |
|------------|------|----------|----------|
| `scratch` | 0 MB | Excellent | Go static binaries |
| `distroless` | 2-20 MB | Excellent | Java, Node, Python |
| `alpine` | 5 MB | Good | General purpose |
| `slim` | 50-100 MB | Good | Needs more tools |
| `full` | 200+ MB | Moderate | Development only |

### 🔴 BLOCKING

- Never use `latest` tag in production
- Always specify exact version: `node:20.11.0-alpine3.19`
- Scan base images for vulnerabilities

---

## Multi-Stage Builds

### Why Multi-Stage?

```dockerfile
# Without multi-stage: 1.2 GB image
FROM node:20
COPY . .
RUN npm install
RUN npm run build
# Final image contains: node_modules, source, build tools, build output

# With multi-stage: 150 MB image
FROM node:20 AS builder
COPY . .
RUN npm ci && npm run build

FROM node:20-alpine AS production
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
# Final image contains: only production dependencies + build output
```

### Stage Naming Convention

```dockerfile
FROM base AS dependencies    # Install deps
FROM dependencies AS builder # Build application
FROM base AS tester         # Run tests
FROM base AS production     # Production image
```

---

## Security Hardening

### Non-Root User

```dockerfile
# 🔴 BLOCKING: Always run as non-root

# Create user
RUN addgroup -g 1001 -S appgroup \
    && adduser -S appuser -u 1001 -G appgroup

# Set ownership
COPY --chown=appuser:appgroup . .

# Switch user
USER appuser
```

### Read-Only Filesystem

```dockerfile
# At runtime
docker run --read-only --tmpfs /tmp myapp
```

### No Secrets in Images

```dockerfile
# 🔴 WRONG
ARG DATABASE_PASSWORD
ENV DB_PASS=$DATABASE_PASSWORD

# ✅ CORRECT: Inject at runtime
# docker run -e DATABASE_PASSWORD=secret myapp
```

### Minimal Capabilities

```dockerfile
# Drop all capabilities, add only needed
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE myapp
```

---

## Dependency Management

### Lockfiles

```dockerfile
# Node.js
COPY package.json package-lock.json ./
RUN npm ci  # Uses lockfile, not package.json

# Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Go
COPY go.mod go.sum ./
RUN go mod download
```

### 🔴 BLOCKING

- Always use lockfiles
- Never `npm install` without lockfile
- Pin versions in requirements.txt

---

## Build Optimization

### Caching Best Practices

```dockerfile
# ✅ CORRECT: Copy deps first, then code
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 🔴 WRONG: Copy everything, cache invalidated on any change
COPY . .
RUN npm ci
RUN npm run build
```

### .dockerignore

```dockerignore
# Essential .dockerignore
node_modules
.git
.env
*.md
tests/
docs/
.vscode/
coverage/
```

### BuildKit Features

```dockerfile
# syntax=docker/dockerfile:1.4

# Cache mounts (keeps cache between builds)
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Secret mounts (not stored in image)
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci
```

---

## Health Checks

### Dockerfile HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1
```

### Health Check Patterns

| Pattern | Command | Use Case |
|---------|---------|----------|
| HTTP | `curl -f http://localhost/health` | Web apps |
| TCP | `nc -z localhost 5432` | Databases |
| Command | `pg_isready` | PostgreSQL |
| File | `test -f /tmp/healthy` | Custom logic |

---

## Logging

### 🔴 BLOCKING Rules

1. **Log to stdout/stderr**: Not to files inside container
2. **Structured logging**: JSON format preferred
3. **No sensitive data**: Mask passwords, tokens

### Example

```dockerfile
# Application should log to stdout
CMD ["node", "app.js"]

# Docker captures stdout/stderr automatically
# View with: docker logs <container>
```

---

## Container Sizing

### Resource Limits

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Memory Guidelines

| App Type | Min Memory | Typical |
|----------|-----------|---------|
| Go/Rust | 16 MB | 64 MB |
| Node.js | 64 MB | 256 MB |
| Java | 256 MB | 512 MB |
| Python | 64 MB | 256 MB |

---

## Image Scanning

### Tools

| Tool | Type | Integration |
|------|------|-------------|
| Trivy | OSS | CLI, CI/CD |
| Snyk | SaaS | GitHub, CI/CD |
| Grype | OSS | CLI, CI/CD |
| Docker Scout | SaaS | Docker Hub |

### 🔴 BLOCKING

- Scan every image before push
- Block critical vulnerabilities
- Set threshold: `trivy image --severity CRITICAL,HIGH`

---

## Registry Best Practices

### Tagging Strategy

```bash
# ✅ Good tags
myapp:1.2.3           # Semantic version
myapp:1.2.3-abc123f   # Version + commit
myapp:1.2             # Minor version (mutable)
myapp:sha-abc123f     # Commit SHA

# 🔴 Bad tags
myapp:latest          # Ambiguous
myapp:dev             # Not versioned
myapp:test            # Not meaningful
```

### Image Signing

```bash
# Sign with cosign
cosign sign myregistry/myapp:1.2.3

# Verify before deploy
cosign verify myregistry/myapp:1.2.3
```

---

## Debugging Containers

### Common Commands

```bash
# Shell into running container
docker exec -it <container> sh

# View logs
docker logs -f <container>

# Inspect container
docker inspect <container>

# Resource usage
docker stats <container>

# Debug non-starting container
docker run -it --entrypoint sh myimage
```
