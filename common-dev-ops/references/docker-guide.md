# Docker Guide

## Overview

Comprehensive guide for writing production-grade Dockerfiles and managing Docker images.

---

## Dockerfile Instructions Reference

### FROM

```dockerfile
# Base image selection
FROM node:20-alpine                    # Named tag
FROM node:20.11.0-alpine3.19          # Pinned version (recommended)
FROM node@sha256:abc123...            # Digest (most reproducible)

# Multi-stage naming
FROM node:20 AS builder
FROM nginx:alpine AS production
```

### WORKDIR

```dockerfile
# 🔴 BLOCKING: Always use WORKDIR, never cd
WORKDIR /app

# Creates directory if not exists
# All subsequent commands run from here
```

### COPY vs ADD

```dockerfile
# ✅ COPY: Use for local files
COPY package.json ./
COPY src/ ./src/

# ADD: Only for tar extraction or remote URLs
ADD archive.tar.gz /app/
ADD https://example.com/file.txt /app/

# 🔴 BLOCKING: Prefer COPY over ADD
```

### RUN

```dockerfile
# Combine commands to reduce layers
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Use shell form for complex commands
RUN set -ex; \
    if [ "$ENV" = "production" ]; then \
        npm ci --only=production; \
    else \
        npm ci; \
    fi
```

### ENV vs ARG

```dockerfile
# ARG: Build-time only
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}

# ENV: Runtime environment
ENV NODE_ENV=production
ENV PORT=3000

# 🔴 BLOCKING: Never put secrets in ENV or ARG
```

### EXPOSE

```dockerfile
# Documentation only - doesn't publish ports
EXPOSE 3000
EXPOSE 8080/tcp
EXPOSE 8081/udp

# Actual port mapping at runtime:
# docker run -p 3000:3000 myapp
```

### USER

```dockerfile
# Create and switch to non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nodejs -u 1001 -G nodejs

USER nodejs

# 🔴 BLOCKING: Never run as root in production
```

### ENTRYPOINT vs CMD

```dockerfile
# ENTRYPOINT: The executable
# CMD: Default arguments

# Pattern 1: Fixed command
ENTRYPOINT ["node"]
CMD ["app.js"]
# Runs: node app.js
# Override args: docker run myapp server.js → node server.js

# Pattern 2: Flexible command
CMD ["node", "app.js"]
# Override full command: docker run myapp npm test

# Pattern 3: Init wrapper
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["node", "app.js"]
```

### HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s \
            --timeout=3s \
            --start-period=5s \
            --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1
```

---

## Complete Dockerfile Examples

### Node.js Production

```dockerfile
# syntax=docker/dockerfile:1.4

###################
# Build Stage
###################
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (better caching)
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

# Prune dev dependencies
RUN npm prune --production

###################
# Production Stage
###################
FROM node:20-alpine AS production

# Security: Non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nodejs -u 1001 -G nodejs

WORKDIR /app

# Copy only production files
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./

# Switch to non-root
USER nodejs

# Expose port (documentation)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start application
CMD ["node", "dist/main.js"]
```

### Java Spring Boot

```dockerfile
# syntax=docker/dockerfile:1.4

###################
# Build Stage
###################
FROM eclipse-temurin:21-jdk-alpine AS builder

WORKDIR /app

# Copy Gradle files first
COPY gradlew ./
COPY gradle/ ./gradle/
COPY build.gradle.kts settings.gradle.kts ./

# Download dependencies (cached)
RUN ./gradlew dependencies --no-daemon

# Copy source and build
COPY src/ ./src/
RUN ./gradlew bootJar --no-daemon

###################
# Production Stage
###################
FROM eclipse-temurin:21-jre-alpine AS production

# Security: Non-root user
RUN addgroup -g 1001 -S spring \
    && adduser -S spring -u 1001 -G spring

WORKDIR /app

# Copy JAR
COPY --from=builder --chown=spring:spring /app/build/libs/*.jar app.jar

USER spring

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

# JVM options for containers
ENTRYPOINT ["java", \
    "-XX:+UseContainerSupport", \
    "-XX:MaxRAMPercentage=75.0", \
    "-jar", "app.jar"]
```

### Python FastAPI

```dockerfile
# syntax=docker/dockerfile:1.4

###################
# Build Stage
###################
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

###################
# Production Stage
###################
FROM python:3.12-slim AS production

# Security: Non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application
COPY --chown=appuser:appuser app/ ./app/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Go Application

```dockerfile
# syntax=docker/dockerfile:1.4

###################
# Build Stage
###################
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Download dependencies
COPY go.mod go.sum ./
RUN go mod download

# Copy source and build
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /app/server ./cmd/server

###################
# Production Stage
###################
FROM scratch AS production

# Copy CA certificates for HTTPS
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy binary
COPY --from=builder /app/server /server

EXPOSE 8080

ENTRYPOINT ["/server"]
```

---

## Common Anti-Patterns

### 🔴 WRONG: Running as Root

```dockerfile
# 🔴 WRONG
FROM node:20
COPY . .
CMD ["node", "app.js"]
# Runs as root!
```

### 🔴 WRONG: Secrets in Image

```dockerfile
# 🔴 WRONG
ARG API_KEY
ENV API_KEY=$API_KEY
# Secret is baked into image layers!
```

### 🔴 WRONG: No .dockerignore

```dockerfile
# Without .dockerignore:
COPY . .
# Copies: node_modules, .git, .env, tests, docs...
# Image is huge and contains secrets!
```

### 🔴 WRONG: Not Using Multi-Stage

```dockerfile
# 🔴 WRONG
FROM node:20
COPY . .
RUN npm install
RUN npm run build
# Image contains: source, dev deps, build tools
# Size: 1+ GB
```

### 🔴 WRONG: Using latest Tag

```dockerfile
# 🔴 WRONG
FROM node:latest
# Build may break when node:latest changes!
```

---

## Build Optimization Tips

### 1. Order Matters

```dockerfile
# ✅ CORRECT: Stable → Volatile
COPY package*.json ./     # Changes rarely
RUN npm ci                # Cached if package.json unchanged
COPY . .                  # Changes often
RUN npm run build
```

### 2. Combine RUN Commands

```dockerfile
# ✅ CORRECT: One layer
RUN apt-get update \
    && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

# 🔴 WRONG: Multiple layers, cache not cleaned
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*
```

### 3. Use BuildKit Cache Mounts

```dockerfile
# syntax=docker/dockerfile:1.4
RUN --mount=type=cache,target=/root/.npm \
    npm ci
```
