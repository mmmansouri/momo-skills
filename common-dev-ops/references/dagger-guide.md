# Dagger Guide

## Overview

Dagger is a programmable CI/CD engine that runs pipelines in containers. Write pipelines in Go, Python, or TypeScript instead of YAML.

---

## Why Dagger?

| Feature | Traditional CI | Dagger |
|---------|---------------|--------|
| Language | YAML | Go/Python/TypeScript |
| Local Testing | Difficult | `dagger call` works locally |
| Debugging | Limited | Full IDE support |
| Caching | CI-specific | Automatic, portable |
| Portability | Vendor-locked | Run anywhere |

---

## Installation

```bash
# Install Dagger CLI
curl -fsSL https://dl.dagger.io/dagger/install.sh | sh

# Or with Homebrew
brew install dagger/tap/dagger

# Verify
dagger version
```

---

## Project Setup (Go)

### Initialize Module

```bash
# Create new Dagger module
dagger init --sdk=go --name=myproject

# Structure created:
# myproject/
# ├── dagger.json
# ├── main.go
# └── dagger.gen.go
```

### Basic Pipeline

```go
// main.go
package main

import (
    "context"
    "dagger/myproject/internal/dagger"
)

type Myproject struct{}

// Build builds the application
func (m *Myproject) Build(ctx context.Context, source *dagger.Directory) *dagger.Container {
    return dag.Container().
        From("node:20-alpine").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithExec([]string{"npm", "ci"}).
        WithExec([]string{"npm", "run", "build"})
}

// Test runs the test suite
func (m *Myproject) Test(ctx context.Context, source *dagger.Directory) (string, error) {
    return dag.Container().
        From("node:20-alpine").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithExec([]string{"npm", "ci"}).
        WithExec([]string{"npm", "test"}).
        Stdout(ctx)
}
```

### Run Locally

```bash
# Run build
dagger call build --source=.

# Run tests
dagger call test --source=.
```

---

## Complete CI/CD Pipeline

```go
package main

import (
    "context"
    "fmt"
    "dagger/myproject/internal/dagger"
)

type Myproject struct{}

// Lint runs linting checks
func (m *Myproject) Lint(ctx context.Context, source *dagger.Directory) (string, error) {
    return m.nodeContainer(source).
        WithExec([]string{"npm", "run", "lint"}).
        Stdout(ctx)
}

// Test runs the test suite with coverage
func (m *Myproject) Test(ctx context.Context, source *dagger.Directory) (string, error) {
    return m.nodeContainer(source).
        WithExec([]string{"npm", "run", "test:coverage"}).
        Stdout(ctx)
}

// Build creates a production build
func (m *Myproject) Build(ctx context.Context, source *dagger.Directory) *dagger.Directory {
    return m.nodeContainer(source).
        WithExec([]string{"npm", "run", "build"}).
        Directory("/app/dist")
}

// Publish builds and pushes the Docker image
func (m *Myproject) Publish(
    ctx context.Context,
    source *dagger.Directory,
    registry string,
    username string,
    password *dagger.Secret,
    tag string,
) (string, error) {
    // Build the application
    dist := m.Build(ctx, source)
    
    // Create production image
    image := dag.Container().
        From("node:20-alpine").
        WithDirectory("/app/dist", dist).
        WithWorkdir("/app").
        WithExec([]string{"npm", "ci", "--only=production"}).
        WithUser("node").
        WithExposedPort(3000).
        WithEntrypoint([]string{"node", "dist/main.js"})
    
    // Push to registry
    addr := fmt.Sprintf("%s:%s", registry, tag)
    return image.
        WithRegistryAuth(registry, username, password).
        Publish(ctx, addr)
}

// CI runs the full CI pipeline
func (m *Myproject) CI(ctx context.Context, source *dagger.Directory) error {
    // Run lint and test in parallel
    errChan := make(chan error, 2)
    
    go func() {
        _, err := m.Lint(ctx, source)
        errChan <- err
    }()
    
    go func() {
        _, err := m.Test(ctx, source)
        errChan <- err
    }()
    
    // Wait for both
    for i := 0; i < 2; i++ {
        if err := <-errChan; err != nil {
            return err
        }
    }
    
    // Build
    m.Build(ctx, source)
    
    return nil
}

// Helper: Create base Node.js container
func (m *Myproject) nodeContainer(source *dagger.Directory) *dagger.Container {
    return dag.Container().
        From("node:20-alpine").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithMountedCache("/app/node_modules", dag.CacheVolume("node-modules")).
        WithExec([]string{"npm", "ci"})
}
```

---

## 🔴 BLOCKING Rules

### 1. Use Cache Volumes

```go
// ✅ CORRECT: Use cache for dependencies
func (m *Myproject) Build(source *dagger.Directory) *dagger.Container {
    return dag.Container().
        From("node:20-alpine").
        WithMountedCache("/app/node_modules", dag.CacheVolume("node-modules")).
        WithDirectory("/app", source).
        WithExec([]string{"npm", "ci"})
}

// 🔴 WRONG: No caching
func (m *Myproject) Build(source *dagger.Directory) *dagger.Container {
    return dag.Container().
        From("node:20-alpine").
        WithDirectory("/app", source).
        WithExec([]string{"npm", "ci"})  // Downloads every time
}
```

### 2. Handle Secrets Properly

```go
// ✅ CORRECT: Use dagger.Secret
func (m *Myproject) Deploy(
    ctx context.Context,
    apiKey *dagger.Secret,
) (string, error) {
    return dag.Container().
        From("alpine").
        WithSecretVariable("API_KEY", apiKey).
        WithExec([]string{"./deploy.sh"}).
        Stdout(ctx)
}

// 🔴 WRONG: Hardcoded or string secrets
func (m *Myproject) Deploy(apiKey string) { /* Never do this */ }
```

### 3. Use Multi-Stage Builds

```go
// ✅ CORRECT: Separate build and runtime
func (m *Myproject) Container(source *dagger.Directory) *dagger.Container {
    // Build stage
    builder := dag.Container().
        From("golang:1.22-alpine").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"go", "build", "-o", "app"})
    
    // Runtime stage
    return dag.Container().
        From("alpine:3.19").
        WithFile("/app", builder.File("/src/app")).
        WithEntrypoint([]string{"/app"})
}
```

---

## Integration with CI

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run CI Pipeline
        uses: dagger/dagger-for-github@v5
        with:
          verb: call
          args: ci --source=.
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - ci

ci:
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - apk add curl
    - curl -fsSL https://dl.dagger.io/dagger/install.sh | sh
  script:
    - dagger call ci --source=.
```

---

## Services (Databases, etc.)

```go
// Test with PostgreSQL service
func (m *Myproject) TestWithDB(ctx context.Context, source *dagger.Directory) (string, error) {
    // Start PostgreSQL service
    postgres := dag.Container().
        From("postgres:16-alpine").
        WithEnvVariable("POSTGRES_PASSWORD", "test").
        WithExposedPort(5432).
        AsService()
    
    // Run tests with DB
    return dag.Container().
        From("node:20-alpine").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithServiceBinding("db", postgres).
        WithEnvVariable("DATABASE_URL", "postgres://postgres:test@db:5432/test").
        WithExec([]string{"npm", "ci"}).
        WithExec([]string{"npm", "run", "test:integration"}).
        Stdout(ctx)
}
```

---

## Common Patterns

### Environment-Specific Config

```go
func (m *Myproject) Deploy(
    ctx context.Context,
    source *dagger.Directory,
    env string,  // "staging" or "production"
) (string, error) {
    var config map[string]string
    
    switch env {
    case "staging":
        config = map[string]string{
            "API_URL": "https://api.staging.example.com",
            "LOG_LEVEL": "debug",
        }
    case "production":
        config = map[string]string{
            "API_URL": "https://api.example.com",
            "LOG_LEVEL": "info",
        }
    }
    
    container := dag.Container().From("node:20-alpine")
    for k, v := range config {
        container = container.WithEnvVariable(k, v)
    }
    
    return container.
        WithDirectory("/app", source).
        WithExec([]string{"./deploy.sh"}).
        Stdout(ctx)
}
```

### Artifact Export

```go
func (m *Myproject) Export(ctx context.Context, source *dagger.Directory) (bool, error) {
    dist := m.Build(ctx, source)
    
    // Export to local filesystem
    return dist.Export(ctx, "./dist")
}
```

### Parallel Execution

```go
import "golang.org/x/sync/errgroup"

func (m *Myproject) AllTests(ctx context.Context, source *dagger.Directory) error {
    g, ctx := errgroup.WithContext(ctx)
    
    g.Go(func() error {
        _, err := m.TestUnit(ctx, source)
        return err
    })
    
    g.Go(func() error {
        _, err := m.TestIntegration(ctx, source)
        return err
    })
    
    g.Go(func() error {
        _, err := m.TestE2E(ctx, source)
        return err
    })
    
    return g.Wait()
}
```

---

## Debugging

```bash
# Verbose output
dagger call --debug build --source=.

# Interactive shell in container
dagger call build --source=. terminal

# Export container for inspection
dagger call build --source=. export --path=./container.tar
```
