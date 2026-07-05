---
name: common-liquibase
description: >-
  Liquibase database migration best practices (Liquibase 5.0+ Community/FSL,
  Liquibase Secure 5.1+, Spring Boot 4, PostgreSQL 17, Java 17+/tested with Java 25).
  Use when: creating/organizing changelogs, designing changesets, implementing
  rollback strategies, planning zero-downtime migrations, configuring Liquibase
  with Spring Boot, wiring policy checks/flow files in CI/CD, or reviewing a PR
  touching changelog/changeset YAML files under `db/changelog/`.
---

# Liquibase Developer Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
>
> **Stack baseline:** Liquibase 5.0+ (Community, FSL license) · Liquibase Secure 5.1+ (commercial, optional) · Spring Boot 4.x · PostgreSQL 17 · Java 17 minimum (verified with Java 25 — requires Liquibase 5.0.2+ for delayed class loading of SnakeYaml/OpenCSV).

---

## Decision Tree — Pick the Right Approach

| Scenario | Approach |
|---|---|
| Create new table | YAML `createTable` with rollback (auto-generated) |
| Add nullable column | YAML `addColumn` (single changeset) |
| Add NOT NULL column on populated table | **Expand-Contract**: add nullable → backfill → set NOT NULL (3 changesets) — [zero-downtime.md](references/zero-downtime.md) |
| Add foreign key | YAML `addForeignKeyConstraint` (separate changeset from table create) |
| Add index on small table | YAML `createIndex` |
| Add index on large/live table (PostgreSQL) | Raw SQL `CREATE INDEX CONCURRENTLY` + `runInTransaction: false` — [zero-downtime.md](references/zero-downtime.md) |
| Rename / drop column on live system | **Expand-Contract** across multiple deploys — [zero-downtime.md](references/zero-downtime.md) |
| Seed reference data (idempotent) | `loadUpdateData` (upsert) instead of `insert` |
| Multi-statement DDL (CREATE FUNCTION, DO $$ blocks, PL/pgSQL) | `runWith: psql` (Liquibase Secure) or single `sql` change with explicit `endDelimiter` |
| Mark a release point | `tag` changeset for targeted rollback |
| Fix a wrongly-applied checksum without re-running | `validCheckSum: any` (4.27+) on the impacted changeset |

---

## OSS vs Secure — Feature Matrix

| Feature | Community (OSS, FSL) | Secure (commercial) |
|---|---|---|
| Core changesets, contexts, labels | ✅ | ✅ |
| Rollback (changeset-defined) | ✅ | ✅ |
| Flow files (CI/CD orchestration) | ✅ (4.15+) | ✅ |
| LPM (`liquibase lpm`, package manager) | ✅ (5.0+) | ✅ |
| Spring Boot integration | ✅ | ✅ |
| `runWith: psql` / `sqlplus` / `sqlcmd` (native executors) | ❌ | ✅ |
| Policy Checks (ex-"Quality Checks") | ❌ | ✅ |
| Custom Python policy checks | ❌ | ✅ |
| Drift detection | ❌ | ✅ |
| Structured rollback / Operations Reports | ❌ | ✅ |
| VS Code extension (Liquibase Secure Developer) | ❌ | ✅ |

🟡 **Liquibase Hub** has been **sunset**. Do not reference it. Use Operations Reports (Secure) or self-hosted log aggregation instead.

---

## When Designing Changesets

📚 **When you need a YAML/SQL template for a specific change type (createTable, addColumn, addForeignKey, raw SQL with `endDelimiter`/`runWith`, `modifyChangeSets`, `validCheckSum: any`) → read [changeset-templates.md](references/changeset-templates.md).**

### 🔴 One Change Per Changeset

**Why:** Many DDL statements auto-commit on most databases (PostgreSQL, MySQL, Oracle). If a multi-change changeset fails midway, the database is left in a half-applied state with no rollback recorded — manual recovery is painful and risks divergence across environments.

```yaml
# 🔴 WRONG - Multiple changes in one changeset
- changeSet:
    id: items-001
    author: teamname
    changes:
      - createTable: ...
      - addForeignKeyConstraint: ...   # If this fails, table still exists, no rollback recorded!

# ✅ CORRECT - One change per changeset
- changeSet:
    id: items-001-create-table
    author: teamname
    changes:
      - createTable: ...

- changeSet:
    id: items-002-add-fk-category
    author: teamname
    changes:
      - addForeignKeyConstraint: ...
```

### 🔴 Always Include Rollback

**Why:** A changeset without a rollback blocks `liquibase rollback` and `rollback-count`. This forces emergency manual SQL on incident calls — exactly when you can least afford it. Auto-generated rollbacks (e.g. `createTable` → `dropTable`) cover ~70% of cases for free; provide manual rollback for the rest.

```yaml
- changeSet:
    id: items-001-create-table
    author: teamname
    changes:
      - createTable:
          tableName: items
          # ...
    rollback:
      - dropTable:
          tableName: items
```

### 🔴 Unique Changeset IDs

**Why:** Liquibase computes uniqueness via the triple `(id, author, filePath)`. Branches that pick the same `id`/`author` for unrelated work will collide on merge with confusing checksum errors. A naming convention prevents this without coordination overhead.

```yaml
# Pattern: <project>-<entity>-<sequence>-<action>
id: myapp-items-001-create-table
author: <team-or-author>
```

### 🔴 Never Edit Applied Changesets

**Why:** Liquibase stores a checksum of every applied changeset. Editing it changes the checksum and `validate` fails on every environment that already ran the original — including production. The fix (clearing checksums) loses tracking integrity.

If you absolutely must amend an already-applied changeset (e.g. typo in a comment), use **`validCheckSum: any`** (4.27+) on that changeset to tolerate both old and new checksums across environments. Otherwise: create a NEW changeset.

```yaml
# ✅ Tolerate prior checksums after a non-functional edit
- changeSet:
    id: myapp-items-001-create-table
    author: teamname
    validCheckSum: any
    changes: [...]
```

---

## When Organizing Changelogs

📚 **When organizing master changelogs, choosing file names, or moving/renaming changeset files (`logicalFilePath`) → read [changelog-structure.md](references/changelog-structure.md).**

### 🔴 Master Changelog: Includes Only

**Why:** Mixing changesets and includes in the master file makes ordering, conditional execution, and module extraction much harder — and it tempts contributors to dump "quick fixes" at the bottom, bypassing the per-feature folder convention.

```yaml
# db.changelog-master.yaml — ONLY includes
databaseChangeLog:
  - include:
      file: items/items-create-012025.yaml
      relativeToChangelogFile: true
  - include:
      file: orders/orders-create-012025.yaml
      relativeToChangelogFile: true
  - include:
      file: data/seed-categories-012025.yaml
      relativeToChangelogFile: true
```

### 🟡 Group by Feature, Not by Change Type

**Why:** Grouping by type (`tables/`, `foreign-keys/`, `indexes/`) creates circular ordering: foreign keys need tables but spanning multiple features, and you can never insert a feature in one place. Per-feature folders keep related changes together and make removal/extraction trivial.

```
✅ CORRECT                    🔴 WRONG
db/changelog/                 db/changelog/
├── items/                    ├── tables/
├── orders/                   ├── foreign-keys/
└── data/                     └── indexes/
```

### 🟢 File Naming

`<project>-<entity>-<action>-<MMYYYY>.yaml` — examples: `myapp-items-create-012025.yaml`, `myapp-orders-add-status-022025.yaml`.

### 🟢 `logicalFilePath` When Moving Files

```yaml
# Moved file — declare original logical path so checksum stays anchored
databaseChangeLog:
  - property:
      name: logicalFilePath
      value: original/path/filename.yaml
```

---

## When Using Preconditions

📚 **When you need the full `onFail` action table (`HALT` / `MARK_RAN` / `WARN` / `CONTINUE`) and additional precondition patterns → read [changeset-templates.md § Preconditions Pattern](references/changeset-templates.md#preconditions-pattern).**

### 🟢 Make Changesets Idempotent

```yaml
- changeSet:
    id: items-001-create-table
    author: teamname
    preConditions:
      - onFail: MARK_RAN
      - not:
          - tableExists:
              tableName: items
    changes:
      - createTable:
          tableName: items
```

---

## When Using Contexts & Labels (`contextFilter` / `labelFilter`)

### 🟡 Use Modern Attribute Names

**Why:** As of Liquibase 4.16, `context` was renamed to `contextFilter` and `labels` to `labelFilter` to clarify *filter* vs *tag* semantics. The old names still work for back-compat but new code should use the new ones — they read better and align with the `--contextFilter` / `--labelFilter` CLI flags.

```yaml
# ✅ CORRECT (4.16+)
- changeSet:
    id: seed-test-data
    author: teamname
    contextFilter: "dev, staging"
    labelFilter: "feature-x, v2.0"
    changes:
      - insert: ...

# 🔴 LEGACY (still works, avoid in new code)
- changeSet:
    id: seed-test-data
    context: "dev, staging"
    labels: "feature-x, v2.0"
```

### Conventions

- **Contexts** → environment / scope decided by the **author** (`dev`, `staging`, `prod`, `!test`)
- **Labels** → tag chosen by the **deployer** at runtime (`feature-x`, `v2.0`, `hotfix`)

```bash
liquibase --contextFilter=dev update
liquibase --labelFilter="v2.0" update
```

---

## When Implementing Rollback

📚 **When deciding which changes need a manual `rollback:` block vs which auto-generate (full coverage matrix) → read [changeset-templates.md § Rollback Coverage Matrix](references/changeset-templates.md#rollback-coverage-matrix).**

### 🟢 Quick Rule

- **Additive ops** (`createTable`, `addColumn`, `createIndex`, `add*Constraint`, `rename*`) — auto-generated, no `rollback:` block needed
- **Destructive ops** (`dropTable`, `dropColumn`, `insert`, `update`, `delete`, `sql`) — explicit `rollback:` block required (or `rollback: empty` with justification)

### 🟢 Use `tag` for Release Boundaries

```yaml
- changeSet:
    id: release-v2.0-tag
    author: release-bot
    changes:
      - tagDatabase:
          tag: v2.0
```

```bash
liquibase rollback v2.0           # Roll back to v2.0 tag
liquibase rollback-count 1
liquibase rollback-to-date 2026-01-15
```

🔴 **Always test rollback in staging before production.** A rollback that's never been exercised is a rollback that won't work.

---

## When Doing Zero-Downtime Migrations

📚 **When changing schema on a live system (Expand-Contract, adding NOT NULL on populated tables, safe renames/drops, adding FK on populated tables, batched backfill, `CREATE INDEX CONCURRENTLY` recovery) → read [zero-downtime.md](references/zero-downtime.md).**

### 🔴 Use Expand-Contract for Destructive Changes

**Why:** A `dropColumn`, `renameColumn`, or NOT NULL constraint on a populated table breaks any running app instance reading the old schema during a rolling deploy. Expand-Contract splits the change across multiple deploys so old and new app versions coexist safely.

| Step | Deploy | Action |
|---|---|---|
| 1 (expand) | N | Add new column / table / index — backward-compatible |
| 2 (migrate) | N | Backfill data + dual-write from app code |
| 3 (switch) | N+1 | App reads from new column |
| 4 (contract) | N+2 | Drop old column / constraint |

### 🔴 Never Block Live Tables

**Why:** `CREATE INDEX` (without `CONCURRENTLY`), `ALTER TABLE ... ADD CONSTRAINT NOT NULL`, and `ALTER TABLE ... ADD FOREIGN KEY` take a full table lock on PostgreSQL. On a live table this stalls all reads and writes for the duration — a de-facto outage.

```yaml
# ✅ CORRECT for PostgreSQL — non-blocking index
- changeSet:
    id: items-add-idx-name-concurrently
    author: teamname
    runInTransaction: false   # CONCURRENTLY cannot run inside a transaction
    changes:
      - sql:
          sql: CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_items_name ON items (name);
    rollback:
      - sql:
          sql: DROP INDEX CONCURRENTLY IF EXISTS idx_items_name;
```

---

## When Running Liquibase in CI/CD

📚 **When wiring Liquibase into a pipeline (Flow files, Policy Checks for Secure, GitHub Actions / Jenkins examples, pre/post-deploy contexts, `liquibase init project`, `liquibase lpm`) → read [policy-checks-and-flow.md](references/policy-checks-and-flow.md).**

### 🟢 Pipeline Stage Order

`validate` → (Secure: `checks run --check-status=MAJOR`) → `status --verbose` → `update-sql` (artifact) → `update` → `tag <release>`. Pack with `liquibase flow --flow-file=liquibase.flowfile.yaml` to invoke as a single CI step.

### 🟢 Bootstrap

```bash
liquibase init project           # scaffolds changelog + properties + flow file
liquibase lpm install postgresql # 5.0+ — drivers + extensions (Snowflake, Mongo, etc.)
```

---

## When Using Spring Boot

📚 **When configuring Liquibase in a Spring Boot 4 app (full property reference, profile-specific config, multi-datasource, Testcontainers `@ServiceConnection`, troubleshooting checksum + lock issues) → read [spring-boot-config.md](references/spring-boot-config.md).**

### 🟢 Key Properties (Spring Boot 4)

```yaml
spring:
  liquibase:
    change-log: classpath:/db/changelog/db.changelog-master.yaml
    enabled: true
    contexts: ${LIQUIBASE_CONTEXTS:dev}
    labels: ${LIQUIBASE_LABELS:}
    show-summary: summary        # SB 3.4+ — off | summary | verbose
    ui-service: logger           # SB 3.4+ — console | logger (use logger in prod)
    parameters:
      schema_name: ${DB_SCHEMA:public}
```

🟡 **Spring Boot 4 package change:** `LiquibaseProperties` moved from `org.springframework.boot.autoconfigure.liquibase` to `org.springframework.boot.liquibase.autoconfigure`. Update any direct imports.

🟡 **`spring.liquibase.async` does not exist.** Liquibase always runs synchronously during `ApplicationContext` initialization in Spring Boot. If you need asynchronous migration (rare and risky), wire a custom `SpringLiquibase` bean and start it in a separate thread — but document it carefully.

### 🟢 Disable for Tests Selectively

```yaml
# application-test.yml — when using @Sql or pre-loaded snapshots
spring:
  liquibase:
    enabled: false
```

For Testcontainers tests: keep Liquibase enabled and let it run against the container — load the `common-java-testing` skill (Testcontainers reference).

---

## When Reviewing a Liquibase PR

📚 **When reviewing a PR that adds or modifies changesets (full BLOCKING / WARNING / BEST PRACTICE checklist + reviewer workflow with local commands) → read [code-review-checklist.md](references/code-review-checklist.md).**

---

## Related Skills

- `common-java-jpa` — Hibernate entity mapping that the schema feeds
- `common-java-developer` — modern Java patterns
- `common-java-testing` — Testcontainers + `@ServiceConnection` for integration tests
- `common-rest-api` — Spring Boot 4 base (config conventions, profiles)
- `common-security` — secrets handling for DB credentials and Liquibase parameters
