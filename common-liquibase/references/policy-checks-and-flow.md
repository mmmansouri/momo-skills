# Policy Checks & Flow Files Reference

> Liquibase 5.0+ Community (Flow files, LPM, init project) and Liquibase Secure 5.1+ (Policy Checks, native executors). For wiring Liquibase into CI/CD pipelines.

---

## Table of Contents

1. [What's OSS vs Secure](#whats-oss-vs-secure)
2. [Bootstrap: `liquibase init project`](#bootstrap-liquibase-init-project)
3. [Package Manager: `liquibase lpm`](#package-manager-liquibase-lpm)
4. [Flow Files (OSS)](#flow-files-oss)
5. [Policy Checks (Secure)](#policy-checks-secure)
6. [Custom Python Policy Checks (Secure)](#custom-python-policy-checks-secure)
7. [GitHub Actions Pipeline Example](#github-actions-pipeline-example)
8. [Jenkins Pipeline Example](#jenkins-pipeline-example)
9. [Pre-Deploy / Post-Deploy Pattern](#pre-deploy--post-deploy-pattern)
10. [What to Run on Every PR](#what-to-run-on-every-pr)

---

## What's OSS vs Secure

| Capability | OSS (Community, FSL) | Secure (commercial) |
|---|---|---|
| `liquibase init project` | ✅ | ✅ |
| `liquibase lpm` (package manager) | ✅ | ✅ |
| `liquibase flow` files | ✅ | ✅ |
| `liquibase update`, `validate`, `status`, `tag`, `rollback` | ✅ | ✅ |
| `liquibase checks run` (Policy Checks) | ❌ | ✅ |
| Custom Python policy checks | ❌ | ✅ |
| `runWith: psql / sqlplus / sqlcmd` (native executors) | ❌ | ✅ |
| Drift detection (`liquibase drift`) | ❌ | ✅ |
| Operations Reports (HTML, structured) | ❌ | ✅ |
| Liquibase Secure Developer (VS Code extension) | ❌ | ✅ |

🟡 **Old terminology:** Liquibase Pro was renamed **Liquibase Secure** with the 5.x rebrand. "Quality Checks" was renamed **Policy Checks** (September 2024). Use the new names in new code/docs; the old CLI flags still resolve for back-compat.

---

## Bootstrap: `liquibase init project`

For a brand-new project (Liquibase 4.20+):

```bash
liquibase init project \
  --project-dir=./db \
  --changelog-file=db.changelog-master.yaml \
  --format=yaml \
  --project-defaults-file=liquibase.properties \
  --url="jdbc:postgresql://localhost:5432/myapp" \
  --username=dev \
  --password=dev
```

Generates:

- `db.changelog-master.yaml` — empty master with comment header
- `liquibase.properties` — connection + defaults
- `liquibase.flowfile.yaml` — example flow
- An example changeset

🟢 Use this for **new** projects. For Spring Boot apps, the changelog goes into `src/main/resources/db/changelog/` instead — but the generated `liquibase.properties` is still useful for local CLI runs (status, diff, generateChangeLog).

---

## Package Manager: `liquibase lpm`

LPM is bundled into Liquibase 5.0+ as the official way to install database drivers and extensions. Replaces dropping JARs into `lib/`.

```bash
liquibase lpm list                       # Installed packages
liquibase lpm search snowflake           # Find available
liquibase lpm install postgresql         # JDBC driver
liquibase lpm install liquibase-snowflake
liquibase lpm install liquibase-mongodb
liquibase lpm update                     # Refresh installed
liquibase lpm uninstall liquibase-mongodb
```

🟢 LPM pins versions in `liquibase.lpm.json` — **commit it** so CI runs reproduce the same toolchain.

---

## Flow Files (OSS)

Flow files (4.15+) bundle a multi-step Liquibase workflow into one CI-invocable command. Available in Community.

### Anatomy

```yaml
# liquibase.flowfile.yaml
globalVariables:
  RELEASE_TAG: "${RELEASE_TAG:-dev-snapshot}"

stages:
  Verify:
    actions:
      - type: liquibase
        command: validate
      - type: liquibase
        command: status
        cmdArgs:
          verbose: true

  Preview:
    actions:
      - type: liquibase
        command: update-sql
        cmdArgs:
          output-file: target/preview.sql
      - type: shell
        command: cat target/preview.sql

  Deploy:
    actions:
      - type: liquibase
        command: update
      - type: liquibase
        command: tag
        cmdArgs:
          tag: "${RELEASE_TAG}"

endStage:
  actions:
    - type: shell
      command: echo "Deploy completed for ${RELEASE_TAG}"
```

### Run

```bash
liquibase flow --flow-file=liquibase.flowfile.yaml
```

### Why use flow files

- **One command** in CI — not a chain of `validate && status && update-sql && update`
- **Portable** — same file runs on Jenkins, GitHub Actions, GitLab CI, developer laptops
- **Conditional stages** via `endStageOnFailure: true` and per-stage variables
- **Composition** — flows can call other flows (`type: flow`)

---

## Policy Checks (Secure)

Policy Checks (formerly "Quality Checks") enforce migration policy automatically — anti-patterns get rejected at the CI gate, not in code review.

### Built-In Checks (selection)

| Check | Catches |
|---|---|
| `ChangeDropTableWarn` | `dropTable` without explicit acknowledgement |
| `ChangeDropColumnWarn` | `dropColumn` (data loss risk) |
| `ChangesetCommentCheck` | Missing `comment` on changeset |
| `ChangesetLabelCheck` | Missing `labelFilter` |
| `ChangesetContextCheck` | Missing `contextFilter` |
| `RollbackRequired` | Missing rollback for non-auto-reversible change |
| `SqlGrantWarn` | `GRANT` statements (privilege escalation) |
| `SqlRevokeWarn` | `REVOKE` statements |
| `TableColumnLimit` | Tables exceeding column count threshold |
| `WarnOnTableCreate` | New table created (require explicit ack) |

### Run

```bash
# Run all enabled checks against the changelog
liquibase checks run

# Run against the live database (requires --checks-scope=database)
liquibase checks run --checks-scope=database

# Custom checks settings file
liquibase checks run --checks-settings-file=liquibase.checks-settings.conf

# Fail the build on severity ≥ MAJOR
liquibase checks run --check-status=MAJOR
```

### Customize

```bash
liquibase checks customize --check-name=ChangeDropTableWarn
# Interactive prompt to set severity, ENABLED/DISABLED, etc.
```

Stores changes in `liquibase.checks-settings.conf` (commit this file).

### Severity Levels

| Severity | Effect |
|---|---|
| `INFO` | Logged only |
| `MINOR` | Logged + flagged |
| `MAJOR` | Build-failing in CI when `--check-status=MAJOR` |
| `CRITICAL` | Always build-failing |

---

## Custom Python Policy Checks (Secure)

Define organization-specific rules in Python:

```python
# checks/no_truncate.py
import re

def check(changeset):
    """Reject any TRUNCATE statement in raw SQL."""
    for change in changeset.changes:
        if change.type == "sql" and re.search(r"\bTRUNCATE\b", change.sql, re.IGNORECASE):
            return {
                "passed": False,
                "message": f"TRUNCATE not allowed in changeset {changeset.id}"
            }
    return { "passed": True }
```

Enable:

```bash
liquibase checks run --checks-scripts-enabled=true --checks-scripts-path=./checks
```

🟡 Custom scripts are **disabled by default** for safety. Enable explicitly via `--checks-scripts-enabled=true`.

---

## GitHub Actions Pipeline Example

```yaml
# .github/workflows/db-migration.yml
name: Database Migration

on:
  pull_request:
    paths:
      - "src/main/resources/db/changelog/**"
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17-alpine
        env:
          POSTGRES_PASSWORD: ci
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 5s --health-timeout 5s --health-retries 10

    steps:
      - uses: actions/checkout@v5
      - uses: liquibase/setup-liquibase@v1
        with:
          version: "5.0.2"
          edition: "oss"   # or "secure" with LIQUIBASE_LICENSE_KEY

      - name: Install Postgres driver
        run: liquibase lpm install postgresql

      - name: Validate + Status (OSS)
        run: liquibase flow --flow-file=liquibase.flowfile.yaml
        env:
          LIQUIBASE_COMMAND_URL: jdbc:postgresql://localhost:5432/postgres
          LIQUIBASE_COMMAND_USERNAME: postgres
          LIQUIBASE_COMMAND_PASSWORD: ci

      # Secure-only: policy gate
      - name: Policy Checks
        if: env.LIQUIBASE_LICENSE_KEY != ''
        run: liquibase checks run --check-status=MAJOR
        env:
          LIQUIBASE_LICENSE_KEY: ${{ secrets.LIQUIBASE_LICENSE_KEY }}

      - name: Upload preview SQL
        uses: actions/upload-artifact@v4
        with:
          name: migration-preview
          path: target/preview.sql
```

---

## Jenkins Pipeline Example

```groovy
pipeline {
  agent any
  environment {
    LIQUIBASE_COMMAND_URL      = 'jdbc:postgresql://db:5432/app'
    LIQUIBASE_COMMAND_USERNAME = credentials('db-user')
    LIQUIBASE_COMMAND_PASSWORD = credentials('db-pass')
  }
  stages {
    stage('Setup') {
      steps {
        sh 'liquibase lpm install postgresql'
      }
    }
    stage('Verify') {
      steps {
        sh 'liquibase validate'
        sh 'liquibase status --verbose'
      }
    }
    stage('Policy Checks') {
      when { expression { env.LIQUIBASE_LICENSE_KEY != null } }
      steps {
        sh 'liquibase checks run --check-status=MAJOR'
      }
    }
    stage('Preview') {
      steps {
        sh 'liquibase update-sql --output-file=target/preview.sql'
        archiveArtifacts artifacts: 'target/preview.sql'
      }
    }
    stage('Deploy') {
      when { branch 'main' }
      steps {
        sh "liquibase flow --flow-file=liquibase.flowfile.yaml"
      }
    }
  }
}
```

---

## Pre-Deploy / Post-Deploy Pattern

For multi-instance deployments, split the pipeline into **two Liquibase runs**:

| Phase | When | Contains |
|---|---|---|
| **Pre-deploy** | Before app rollout | Backward-compatible additions: new tables, nullable columns, new indexes (CONCURRENTLY) |
| **Rollout** | – | Old pods drain, new pods come up |
| **Post-deploy** | After all pods are on the new version | Destructive changes: drop columns, drop tables, NOT NULL enforcement |

Implementation: tag changesets with `contextFilter`:

```yaml
- changeSet:
    id: items-add-status-nullable
    author: teamname
    contextFilter: "pre-deploy"
    changes: [...]

- changeSet:
    id: items-drop-old-flag
    author: teamname
    contextFilter: "post-deploy"
    changes: [...]
```

Run them separately:

```bash
liquibase --contextFilter=pre-deploy update    # Stage 1
# ... rollout app ...
liquibase --contextFilter=post-deploy update   # Stage 2
```

This forces the Expand-Contract pattern at the pipeline level — see [zero-downtime.md](zero-downtime.md).

---

## What to Run on Every PR

| Stage | Command | OSS / Secure | Blocking? |
|---|---|---|---|
| Validate syntax + checksums | `liquibase validate` | OSS | 🔴 Yes |
| Show pending changesets | `liquibase status --verbose` | OSS | 🟡 Inform |
| Generate SQL preview | `liquibase update-sql` | OSS | 🟡 Attach to PR |
| Run policy checks | `liquibase checks run --check-status=MAJOR` | Secure | 🔴 Yes (if licensed) |
| Apply against ephemeral DB | `liquibase update` (Testcontainers / CI Postgres) | OSS | 🔴 Yes |
| Run app integration tests | (your test suite) | – | 🔴 Yes |

🟢 **Block merges on policy check failures (Secure) and on `update` failures against the ephemeral DB (both editions).** Everything else is informational.
