# Changelog Structure Reference

> Liquibase 5.0+ patterns. Master changelog organization, file naming, includes, and `modifyChangeSets` for bulk attribute application.

---

## Table of Contents

1. [Recommended Directory Structure](#recommended-directory-structure)
2. [Master Changelog](#master-changelog)
3. [File Naming Conventions](#file-naming-conventions)
4. [Include Patterns](#include-patterns)
5. [`modifyChangeSets` for Bulk Attributes](#modifychangesets-for-bulk-attributes)
6. [Handling File Moves / Renames (`logicalFilePath`)](#handling-file-moves--renames)
7. [Version-Based Organization (Alternative)](#version-based-organization)
8. [Dependency Order](#dependency-order)
9. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
10. [Bootstrap with `liquibase init project`](#bootstrap-with-liquibase-init-project)
11. [Extensions via `liquibase lpm`](#extensions-via-liquibase-lpm)

---

## Recommended Directory Structure

```
src/main/resources/db/changelog/
├── db.changelog-master.yaml       # Master file — includes only
├── items/                         # Feature: items
│   ├── items-create-012025.yaml
│   ├── items-add-fk-category-012025.yaml
│   └── items-add-description-022025.yaml
├── orders/                        # Feature: orders
│   ├── orders-create-012025.yaml
│   ├── orders-status-check-012025.yaml
│   └── orders-add-tracking-022025.yaml
├── customers/
│   └── customers-create-012025.yaml
└── data/                          # Seed data (loadUpdateData)
    ├── categories-seed-012025.yaml
    ├── categories.csv
    └── users-admin-seed-012025.yaml
```

---

## Master Changelog

The master changelog must contain **only `include` / `includeAll`** — no changesets:

```yaml
# db.changelog-master.yaml
databaseChangeLog:
  # 1. Independent tables first
  - include:
      file: customers/customers-create-012025.yaml
      relativeToChangelogFile: true
  - include:
      file: categories/categories-create-012025.yaml
      relativeToChangelogFile: true

  # 2. Tables with FKs
  - include:
      file: items/items-create-012025.yaml
      relativeToChangelogFile: true
  - include:
      file: items/items-add-fk-category-012025.yaml
      relativeToChangelogFile: true
  - include:
      file: orders/orders-create-012025.yaml
      relativeToChangelogFile: true

  # 3. Seed data
  - include:
      file: data/categories-seed-012025.yaml
      relativeToChangelogFile: true
```

---

## File Naming Conventions

### Pattern

```
<project>-<entity>-<action>-<MMYYYY>.yaml
```

### Actions

| Action | Use Case |
|---|---|
| `create` | Initial table creation |
| `add-<column>` | Add new column |
| `add-fk-<target>` | Add foreign key |
| `add-idx-<column>` | Add index |
| `add-idx-<column>-concurrently` | PostgreSQL non-blocking index |
| `drop-<column>` | Remove column |
| `modify-<column>` | Alter column type/constraint |
| `rename-<column>` | Rename column |
| `seed-data` / `seed-<entity>` | Insert / upsert reference data |
| `status-check` | Add CHECK constraint for enum values |
| `tag-<release>` | Mark release boundary |

### Examples

```
myapp-items-create-012025.yaml
myapp-items-add-description-022025.yaml
myapp-items-add-fk-category-012025.yaml
myapp-items-add-idx-name-022025.yaml
myapp-items-add-idx-name-concurrently-032025.yaml
myapp-orders-status-check-012025.yaml
myapp-categories-seed-data-012025.yaml
```

---

## Include Patterns

### Single File

```yaml
- include:
    file: items/items-create-012025.yaml
    relativeToChangelogFile: true
```

### All Files in a Directory

```yaml
- includeAll:
    path: items/
    relativeToChangelogFile: true
    errorIfMissingOrEmpty: true
```

🟡 `includeAll` processes files **alphabetically**. Without timestamps in filenames you lose deterministic order — keep the `MMYYYY` suffix.

### Conditional Include (`contextFilter`)

```yaml
- include:
    file: data/test-data-only.yaml
    relativeToChangelogFile: true
    contextFilter: test       # 4.16+ — replaces legacy `context:`
```

---

## `modifyChangeSets` for Bulk Attributes

When importing many changesets that share an attribute (e.g. all run via `psql`, all need an ID prefix), wrap them once:

```yaml
databaseChangeLog:
  - modifyChangeSets:
      runWith: psql               # All nested changesets execute via psql (Secure)
      idPrefix: imported-
      idSuffix: -v1
      changeSets:
        - changeSet:
            id: 001-create-functions
            author: dba
            changes:
              - sqlFile: { path: imported/001-functions.sql }
        - changeSet:
            id: 002-create-views
            author: dba
            changes:
              - sqlFile: { path: imported/002-views.sql }
```

Effective IDs become `imported-001-create-functions-v1`, `imported-002-create-views-v1`.

---

## Handling File Moves / Renames

When moving or renaming a changelog file, Liquibase sees it as new (different `filePath` → different identity) and tries to re-apply every changeset.

### Solution: `logicalFilePath`

```yaml
# In the moved/renamed file
databaseChangeLog:
  - property:
      name: logicalFilePath
      value: original/path/old-filename.yaml

  - changeSet:
      id: items-001-create
      # ...
```

Or per-changeset:

```yaml
- changeSet:
    id: items-001-create
    author: teamname
    logicalFilePath: original/path/old-filename.yaml
    changes: [...]
```

🟡 **Bug fixed in Liquibase 5.0:** prior versions had inconsistent `logicalFilePath` handling. Upgrade if affected.

---

## Version-Based Organization (Alternative)

For projects with explicit release cycles, group by version instead of feature:

```
db/changelog/
├── db.changelog-master.yaml
├── v1.0/
│   ├── items-create.yaml
│   └── orders-create.yaml
├── v1.1/
│   ├── items-add-description.yaml
│   └── orders-add-tracking.yaml
└── v2.0/
    └── customers-create.yaml
```

```yaml
# db.changelog-master.yaml
databaseChangeLog:
  - includeAll: { path: v1.0/, relativeToChangelogFile: true }
  - includeAll: { path: v1.1/, relativeToChangelogFile: true }
  - includeAll: { path: v2.0/, relativeToChangelogFile: true }
```

---

## Dependency Order

Tables must exist before their FKs reference them:

```yaml
databaseChangeLog:
  # 1. Independent tables
  - include: { file: categories-create.yaml }
  - include: { file: customers-create.yaml }

  # 2. Dependent tables
  - include: { file: items-create.yaml }     # references categories
  - include: { file: orders-create.yaml }    # references customers

  # 3. Foreign keys (separate files for clarity)
  - include: { file: items-add-fk-category.yaml }
  - include: { file: orders-add-fk-customer.yaml }

  # 4. Indexes
  - include: { file: items-add-idx-name.yaml }

  # 5. Seed / reference data
  - include: { file: categories-seed.yaml }
```

---

## Anti-Patterns to Avoid

### ❌ Grouping by Change Type

```
db/changelog/
├── tables/
├── foreign-keys/      # Cross-cuts every feature — impossible to extract one
└── indexes/
```

**Problem:** removing or extracting a feature requires touching multiple folders. Foreign keys, indexes, and tables for the same feature drift apart.

### ❌ Changesets in the Master Changelog

```yaml
databaseChangeLog:
  - include: { file: items.yaml }
  - changeSet:                    # 🔴 Don't mix
      id: quick-fix
      changes: ...
```

### ❌ Editing Applied Changesets

Once applied, the checksum is stored. Any edit changes the checksum and `validate` fails:

```
Validation Failed:
  1 changesets check sum was:
    items-001-create was: 8:abc123 but is now: 8:def456
```

**Solutions:**
1. Create a NEW changeset for the change (preferred)
2. Use `validCheckSum: any` (4.27+) for non-functional edits — see [changeset-templates.md](changeset-templates.md#validchecksum-any)

---

## Bootstrap with `liquibase init project`

For a brand new project, use the official scaffolder (4.20+):

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

Generates: `db.changelog-master.yaml`, `liquibase.properties`, an example changeset, and a flow file template.

---

## Extensions via `liquibase lpm`

Liquibase Package Manager is bundled in 5.0+. Use it to install database drivers and extensions instead of dropping JARs in `lib/` manually:

```bash
liquibase lpm list                       # List installed
liquibase lpm search snowflake           # Find available
liquibase lpm install liquibase-snowflake
liquibase lpm install postgresql         # JDBC driver
liquibase lpm update                     # Refresh installed packages
```

🟢 LPM resolves transitive dependencies and pins versions in `liquibase.lpm.json` — keep that file in version control.
