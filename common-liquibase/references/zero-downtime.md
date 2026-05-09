# Zero-Downtime Migration Patterns

> Liquibase 5.0+ · PostgreSQL 17 · Rolling-deploy environments (Kubernetes, blue/green). Patterns for changing schema without taking the application offline.

---

## Table of Contents

1. [Why Zero-Downtime Matters](#why-zero-downtime-matters)
2. [Operations That Lock Live Tables](#operations-that-lock-live-tables)
3. [Expand-Contract Pattern](#expand-contract-pattern)
4. [Adding NOT NULL on a Populated Table](#adding-not-null-on-a-populated-table)
5. [Renaming a Column Safely](#renaming-a-column-safely)
6. [Dropping a Column Safely](#dropping-a-column-safely)
7. [Adding a Foreign Key on a Populated Table](#adding-a-foreign-key-on-a-populated-table)
8. [`CREATE INDEX CONCURRENTLY` (PostgreSQL)](#create-index-concurrently)
9. [Backfilling Large Tables in Batches](#backfilling-large-tables-in-batches)
10. [Splitting / Combining Columns](#splitting--combining-columns)
11. [`liquibase-zd` Plugin (PostgreSQL)](#liquibase-zd-plugin)
12. [Anti-Patterns](#anti-patterns)

---

## Why Zero-Downtime Matters

In a rolling deploy, **two app versions run simultaneously** for a few seconds to minutes:

```
        ┌──────────────────────────┐
        │  Pod A (old version)     │  ← still reads/writes old schema
        ├──────────────────────────┤
        │  Pod B (new version)     │  ← reads/writes new schema
        └──────────────────────────┘
                     │
                     ▼
              ┌──────────────┐
              │  Database    │
              └──────────────┘
```

A migration that changes the schema in a way only Pod B understands **breaks Pod A immediately**. The app appears "down" until rollout completes.

🔴 **Every destructive change on a live table must be split into multiple deploys** so old and new app versions can coexist with the schema in any intermediate state.

---

## Operations That Lock Live Tables

PostgreSQL acquires `ACCESS EXCLUSIVE` (full table lock) for these operations — readers and writers stall until completion:

| Operation | Lock | Mitigation |
|---|---|---|
| `ALTER TABLE ... ADD COLUMN` (with default, PG <11) | Full lock + table rewrite | Add nullable column, backfill, then set default |
| `ALTER TABLE ... ALTER COLUMN ... SET NOT NULL` | Full lock + table scan | `ADD CONSTRAINT NOT VALID` then `VALIDATE CONSTRAINT` (PG 12+) |
| `ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY` | Full lock | `NOT VALID` then `VALIDATE CONSTRAINT` |
| `CREATE INDEX` (without `CONCURRENTLY`) | Write lock | Use `CREATE INDEX CONCURRENTLY` |
| `ALTER TABLE ... DROP COLUMN` | Full lock (brief) | Rename → drop in next release |
| `ALTER TABLE ... ALTER COLUMN TYPE` | Full lock + rewrite | New column → backfill → switch reads → drop old |

🟢 PostgreSQL 17 has improved `ALTER TABLE` for some cases (e.g. adding a column with a constant default is metadata-only since PG 11), but treat any `ALTER` on a live multi-million-row table as suspect until proven otherwise on a representative dataset.

---

## Expand-Contract Pattern

The canonical zero-downtime workflow. **Three phases, three deploys minimum:**

| Phase | Deploy | Schema | App reads | App writes |
|---|---|---|---|---|
| 1 — Expand | N | Add new structure | Old | Old + New (dual-write) |
| 2 — Switch | N+1 | (no DDL) | New | New only |
| 3 — Contract | N+2 | Drop old structure | New | New |

**Key invariant:** at every intermediate state, **both the old and the new app versions can run against the current schema without errors.**

---

## Adding NOT NULL on a Populated Table

### 🔴 Wrong (single deploy, blocks)

```yaml
- changeSet:
    id: items-add-status-notnull-WRONG
    author: teamname
    changes:
      - addColumn:
          tableName: items
          columns:
            - column:
                name: status
                type: varchar(20)
                constraints: { nullable: false }   # 🔴 Fails on existing rows
```

### ✅ Correct (Expand-Contract, 3 deploys)

**Deploy N — add nullable column:**

```yaml
- changeSet:
    id: items-001-add-status-nullable
    author: teamname
    changes:
      - addColumn:
          tableName: items
          columns:
            - column: { name: status, type: varchar(20) }
    rollback:
      - dropColumn:
          tableName: items
          columnName: status
```

**Deploy N (same release, separate changeset) — backfill:**

```yaml
- changeSet:
    id: items-002-backfill-status
    author: teamname
    changes:
      - sql:
          sql: UPDATE items SET status = 'ACTIVE' WHERE status IS NULL;
    rollback: empty
```

**Deploy N+1 — app writes `status` on every insert/update.** No schema change.

**Deploy N+2 — enforce NOT NULL (PostgreSQL 12+ pattern, non-blocking validation):**

```yaml
- changeSet:
    id: items-003-status-notnull-add-constraint
    author: teamname
    changes:
      - sql:
          sql: ALTER TABLE items ADD CONSTRAINT items_status_not_null CHECK (status IS NOT NULL) NOT VALID;
    rollback:
      - sql:
          sql: ALTER TABLE items DROP CONSTRAINT items_status_not_null;

- changeSet:
    id: items-004-status-notnull-validate
    author: teamname
    changes:
      - sql:
          sql: ALTER TABLE items VALIDATE CONSTRAINT items_status_not_null;
    rollback: empty
```

**Why split `NOT VALID` then `VALIDATE`:** `NOT VALID` adds the constraint with a brief lock and applies it to **new** rows immediately. `VALIDATE CONSTRAINT` scans existing rows but only takes a `SHARE UPDATE EXCLUSIVE` lock — concurrent reads/writes continue.

---

## Renaming a Column Safely

### Phases

| Deploy | Action |
|---|---|
| N | Add new column `display_name` (nullable). App writes both old `name` and new `display_name`. |
| N | Backfill: `UPDATE items SET display_name = name WHERE display_name IS NULL`. |
| N+1 | App reads from `display_name`, still dual-writes. |
| N+2 | App reads + writes only `display_name`. |
| N+3 | Drop `name` column. |

### Changesets

```yaml
# Deploy N
- changeSet:
    id: items-001-add-display-name
    author: teamname
    changes:
      - addColumn:
          tableName: items
          columns:
            - column: { name: display_name, type: varchar(255) }
    rollback:
      - dropColumn:
          tableName: items
          columnName: display_name

- changeSet:
    id: items-002-backfill-display-name
    author: teamname
    changes:
      - sql:
          sql: UPDATE items SET display_name = name WHERE display_name IS NULL;
    rollback: empty

# Deploy N+3
- changeSet:
    id: items-003-drop-name
    author: teamname
    changes:
      - dropColumn:
          tableName: items
          columnName: name
    rollback:
      # Best-effort recreate — data is lost
      - addColumn:
          tableName: items
          columns:
            - column: { name: name, type: varchar(255) }
```

🟡 **Liquibase's `renameColumn` is unsafe for live tables** — it performs a single `ALTER TABLE` and old app pods immediately fail to read the renamed column. Only use `renameColumn` on tables guaranteed to have no live readers (e.g. brand-new tables, single-pod deployments, or maintenance windows).

---

## Dropping a Column Safely

| Deploy | Action |
|---|---|
| N | App stops reading the column. |
| N+1 | App stops writing the column (still allowed in schema). |
| N+2 | Drop the column. |

```yaml
# Deploy N+2
- changeSet:
    id: items-007-drop-deprecated-flag
    author: teamname
    changes:
      - dropColumn:
          tableName: items
          columnName: deprecated_flag
    rollback:
      - addColumn:
          tableName: items
          columns:
            - column: { name: deprecated_flag, type: boolean, defaultValue: false }
```

🔴 If the column is part of an index, drop the index first (separately) — `dropColumn` on an indexed column locks the table.

---

## Adding a Foreign Key on a Populated Table

### 🔴 Wrong (full table lock)

```yaml
- addForeignKeyConstraint:
    baseTableName: items
    baseColumnNames: category_id
    referencedTableName: categories
    referencedColumnNames: id
    constraintName: fk_items_category   # 🔴 Locks `items` for the full validation
```

### ✅ Correct (PostgreSQL `NOT VALID` + `VALIDATE`)

```yaml
- changeSet:
    id: items-add-fk-category-add
    author: teamname
    changes:
      - sql:
          sql: |
            ALTER TABLE items
              ADD CONSTRAINT fk_items_category
              FOREIGN KEY (category_id) REFERENCES categories (id) NOT VALID;
    rollback:
      - sql:
          sql: ALTER TABLE items DROP CONSTRAINT fk_items_category;

- changeSet:
    id: items-add-fk-category-validate
    author: teamname
    changes:
      - sql:
          sql: ALTER TABLE items VALIDATE CONSTRAINT fk_items_category;
    rollback: empty
```

`NOT VALID` adds the constraint with a brief lock — new rows are checked immediately. `VALIDATE CONSTRAINT` scans existing rows under a lighter lock that allows concurrent reads/writes.

---

## `CREATE INDEX CONCURRENTLY` (PostgreSQL) {#create-index-concurrently}

```yaml
- changeSet:
    id: items-add-idx-name-concurrently
    author: teamname
    runInTransaction: false   # 🔴 Required — CONCURRENTLY forbidden in transactions
    changes:
      - sql:
          sql: CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_items_name ON items (name);
    rollback:
      - sql:
          sql: DROP INDEX CONCURRENTLY IF EXISTS idx_items_name;
```

### Recovering from a Failed `CONCURRENTLY` Build

PostgreSQL leaves an `INVALID` index behind if `CREATE INDEX CONCURRENTLY` is interrupted. Drop and retry:

```sql
SELECT indexname FROM pg_indexes WHERE indexname = 'idx_items_name';
SELECT indisvalid FROM pg_index JOIN pg_class ON pg_class.oid = pg_index.indexrelid
  WHERE relname = 'idx_items_name';

-- If indisvalid is false:
DROP INDEX CONCURRENTLY idx_items_name;
-- Then re-run the changeset (idempotent thanks to IF NOT EXISTS)
```

---

## Backfilling Large Tables in Batches

For tables with millions of rows, a single `UPDATE` locks rows for too long and bloats WAL. Batch with a key range:

```yaml
- changeSet:
    id: items-backfill-status-batch
    author: teamname
    runInTransaction: false
    changes:
      - sql:
          splitStatements: false
          sql: |
            DO $$
            DECLARE
              batch_size INT := 10000;
              rows_updated INT;
            BEGIN
              LOOP
                UPDATE items
                SET status = 'ACTIVE'
                WHERE id IN (
                  SELECT id FROM items WHERE status IS NULL LIMIT batch_size FOR UPDATE SKIP LOCKED
                );
                GET DIAGNOSTICS rows_updated = ROW_COUNT;
                EXIT WHEN rows_updated = 0;
                COMMIT;        -- Requires runInTransaction: false
                PERFORM pg_sleep(0.1);
              END LOOP;
            END $$;
    rollback: empty
```

🟡 For very large backfills (10M+ rows, multi-hour), prefer a **dedicated worker job** outside Liquibase — gated by a feature flag — so deploys aren't blocked.

---

## Splitting / Combining Columns

Same Expand-Contract sequence as renaming, with a transformation step:

| Deploy | Action |
|---|---|
| N | Add `first_name`, `last_name`. Backfill: `SPLIT_PART(full_name, ' ', 1)` / `SPLIT_PART(full_name, ' ', 2)`. App dual-writes. |
| N+1 | App reads from `first_name` / `last_name`. |
| N+2 | App stops writing `full_name`. |
| N+3 | Drop `full_name`. |

```yaml
- changeSet:
    id: users-001-add-name-parts
    author: teamname
    changes:
      - addColumn:
          tableName: users
          columns:
            - column: { name: first_name, type: varchar(100) }
            - column: { name: last_name, type: varchar(100) }
    rollback:
      - dropColumn: { tableName: users, columnName: first_name }
      - dropColumn: { tableName: users, columnName: last_name }

- changeSet:
    id: users-002-backfill-name-parts
    author: teamname
    changes:
      - sql:
          sql: |
            UPDATE users
            SET first_name = SPLIT_PART(full_name, ' ', 1),
                last_name  = SPLIT_PART(full_name, ' ', 2)
            WHERE first_name IS NULL OR last_name IS NULL;
    rollback: empty
```

---

## `liquibase-zd` Plugin

[`liquibase-zd`](https://github.com/coenvk/liquibase-zd) is a community plugin that automates expand-contract for PostgreSQL. It generates the multi-step changesets from a higher-level intent.

🟡 Third-party plugin — evaluate maintenance status and license fit (currently MIT) before adopting in production. Manual Expand-Contract changesets remain the most portable approach.

---

## Anti-Patterns

| Anti-pattern | Why it breaks | Do this instead |
|---|---|---|
| Single-step `addColumn` with NOT NULL on populated table | Old rows have NULL; constraint fails | Nullable → backfill → `NOT VALID` + `VALIDATE` |
| `renameColumn` on live table | Old pods crash on next read | Add new col, dual-write, switch reads, drop old |
| `CREATE INDEX` on million-row table | Locks writes for minutes | `CREATE INDEX CONCURRENTLY` + `runInTransaction: false` |
| `ALTER COLUMN TYPE` on live table | Full lock + table rewrite | New column → backfill → switch → drop |
| `dropColumn` while app still writes it | Writes fail | Stop writes (deploy N) → wait → drop (deploy N+1) |
| Single 50M-row `UPDATE` | Long lock + WAL bloat | Batch with `LIMIT … SKIP LOCKED` + `COMMIT` |
| Liquibase backfill of 100M+ rows | Blocks deploy for hours | Dedicated worker job, flag-gated |
