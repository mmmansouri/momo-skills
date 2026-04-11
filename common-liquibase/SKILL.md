---
name: common-liquibase
description: >-
  Liquibase database migration best practices. Use when: creating/organizing
  changelogs, designing changesets, implementing rollback strategies, using
  contexts/labels, or configuring Liquibase with Spring Boot.
---

# Liquibase Developer Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## When Designing Changesets

📚 **References:** [changeset-templates.md](references/changeset-templates.md)

### 🔴 One Change Per Changeset

```yaml
# 🔴 WRONG - Multiple changes in one changeset
- changeSet:
    id: items-001
    changes:
      - createTable: ...
      - addForeignKeyConstraint: ...  # If this fails, table still exists!

# ✅ CORRECT - One change per changeset
- changeSet:
    id: items-001-create-table
    changes:
      - createTable: ...

- changeSet:
    id: items-002-add-fk
    changes:
      - addForeignKeyConstraint: ...
```

**Why?** Some databases auto-commit statements. If a changeset fails mid-way, the database is left in an unexpected state.

### 🔴 Always Include Rollback

```yaml
- changeSet:
    id: items-001-create-table
    changes:
      - createTable:
          tableName: items
          # ...
    rollback:
      - dropTable:
          tableName: items
```

### 🔴 Unique Changeset IDs

```yaml
# Pattern: <project>-<entity>-<sequence>-<action>
id: myapp-items-001-create-table
author: teamname
```

**Why?** Author + ID together determine uniqueness. Prevents conflicts across branches.

### 🟡 Never Edit Applied Changesets

Once a changeset is applied, create a NEW changeset for modifications. Editing changes the checksum and causes failures.

---

## When Organizing Changelogs

📚 **References:** [changelog-structure.md](references/changelog-structure.md)

### 🔴 Master Changelog Pattern

```yaml
# db.changelog-master.yaml - ONLY includes, no changesets!
databaseChangeLog:
  - include:
      file: tables/items-create-012025.yaml
      relativeToChangelogFile: true
  - include:
      file: tables/orders-create-012025.yaml
      relativeToChangelogFile: true
  - include:
      file: data/seed-categories-012025.yaml
      relativeToChangelogFile: true
```

### 🟡 Avoid Grouping by Type

```
# 🔴 WRONG - Leads to circular dependencies
db/changelog/
├── tables/           # All table creates
├── foreign-keys/     # All FKs
└── indexes/          # All indexes

# ✅ CORRECT - Group by feature/entity
db/changelog/
├── items/
│   ├── items-create-012025.yaml
│   └── items-add-description-022025.yaml
├── orders/
└── data/
```

### 🟢 File Naming Convention

```
<project>-<entity>-<action>-<MMYYYY>.yaml
```

Examples:
- `myapp-items-create-012025.yaml`
- `myapp-orders-add-status-022025.yaml`
- `myapp-categories-seed-data-012025.yaml`

### 🟢 LogicalFilePath When Moving Files

```yaml
# If you rename/move a file, add this to prevent re-execution
databaseChangeLog:
  - property:
      name: logicalFilePath
      value: original/path/filename.yaml
```

---

## When Using Preconditions

### 🟢 Prevent Re-Execution

```yaml
- changeSet:
    id: items-001-create-table
    preConditions:
      - onFail: MARK_RAN
      - not:
          - tableExists:
              tableName: items
    changes:
      - createTable:
          tableName: items
```

### Precondition Actions

| onFail Value | Behavior |
|--------------|----------|
| `HALT` | Stop execution (default) |
| `MARK_RAN` | Skip but mark as executed |
| `WARN` | Log warning, continue |
| `CONTINUE` | Skip silently |

### Common Preconditions

```yaml
# Table exists
- tableExists:
    tableName: items

# Column exists
- columnExists:
    tableName: items
    columnName: description

# SQL check
- sqlCheck:
    expectedResult: 0
    sql: SELECT COUNT(*) FROM items WHERE status IS NULL
```

---

## When Using Contexts & Labels

### 🟢 Contexts for Environments

```yaml
# Only run in dev/staging
- changeSet:
    id: seed-test-data
    context: dev, staging
    changes:
      - insert: ...

# Exclude from test environment
- changeSet:
    id: seed-prod-data
    context: "!test"
    changes:
      - insert: ...
```

### 🟢 Labels for Features/Versions

```yaml
- changeSet:
    id: feature-x-001
    labels: "feature-x, v2.0"
    changes:
      - createTable: ...
```

### Runtime Usage

```bash
# Run only dev context
liquibase --contexts=dev update

# Run specific labels
liquibase --labels="v2.0" update
```

---

## When Implementing Rollback

📚 **References:** [changeset-templates.md](references/changeset-templates.md)

### Auto-Generated Rollbacks

These changes have automatic rollback:

| Change | Auto-Rollback |
|--------|---------------|
| `createTable` | `dropTable` |
| `addColumn` | `dropColumn` |
| `createIndex` | `dropIndex` |
| `addForeignKeyConstraint` | `dropForeignKeyConstraint` |
| `addUniqueConstraint` | `dropUniqueConstraint` |

### Manual Rollback Required

These changes need explicit rollback:

| Change | Must Provide |
|--------|-------------|
| `dropTable` | `createTable` (with columns!) |
| `dropColumn` | `addColumn` (data lost!) |
| `insert` | `delete` |
| `update` | Reverse `update` |
| `sql` | Reverse SQL |

```yaml
# Manual rollback for insert
- changeSet:
    id: seed-categories
    changes:
      - insert:
          tableName: categories
          columns:
            - column: { name: id, value: "uuid-1" }
            - column: { name: name, value: "Electronics" }
    rollback:
      - delete:
          tableName: categories
          where: id = 'uuid-1'
```

### 🟢 Test Rollbacks

```bash
# Rollback last N changesets
liquibase rollback-count 1

# Rollback to tag
liquibase rollback v1.0

# Rollback to date
liquibase rollback-to-date 2025-01-15
```

---

## When Using Spring Boot

📚 **References:** [spring-boot-config.md](references/spring-boot-config.md)

### 🟢 Key Properties

```yaml
# application.yml
spring:
  liquibase:
    change-log: classpath:/db/changelog/db.changelog-master.yaml
    contexts: ${LIQUIBASE_CONTEXTS:dev}
    enabled: true

    # Custom tracking tables
    database-change-log-table: CHANGELOG
    database-change-log-lock-table: CHANGELOG_LOCK
```

### 🟢 Environment-Specific Parameters

```yaml
# application.yml
spring:
  liquibase:
    parameters:
      schema_name: ${DB_SCHEMA:public}

# Use in changelog
- changeSet:
    changes:
      - sql:
          sql: CREATE SCHEMA IF NOT EXISTS ${schema_name}
```

### 🟢 Profile-Specific Config

```yaml
# application-dev.yml
spring:
  liquibase:
    contexts: dev

# application-prod.yml
spring:
  liquibase:
    contexts: prod
```

### 🟢 Disable for Tests (If Needed)

```yaml
# application-test.yml
spring:
  liquibase:
    enabled: false  # Use @Sql or embedded DB init instead
```

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] One change per changeset
- [ ] Rollback provided (explicit for destructive changes)
- [ ] Unique ID (author + meaningful name)
- [ ] Master changelog only has includes

### 🟡 WARNING
- [ ] No editing of applied changesets
- [ ] Preconditions for idempotency
- [ ] Context/labels for environment-specific data

### 🟢 BEST PRACTICE
- [ ] Timestamps in filenames (MMYYYY)
- [ ] Group by feature, not by change type
- [ ] Test rollback before production
- [ ] logicalFilePath when moving files
