# Changeset Templates Reference

> Liquibase 5.0+ patterns. PostgreSQL 17 examples. YAML format.

---

## Table of Contents

1. [Rollback Coverage Matrix](#rollback-coverage-matrix)
2. [Create Table](#create-table)
3. [Add Foreign Key](#add-foreign-key)
4. [Add Column](#add-column)
5. [Add Column with Default](#add-column-with-default)
6. [Create Index](#create-index)
7. [Create Index Concurrently (PostgreSQL, Live Tables)](#create-index-concurrently)
8. [Add Unique Constraint](#add-unique-constraint)
9. [Enum Values: `addCheckConstraint` vs Native ENUM](#enum-values)
10. [Modify / Rename Column](#modify--rename-column)
11. [Insert vs `loadUpdateData` (Idempotent Seed)](#insert-vs-loadupdatedata)
12. [Load Data from CSV](#load-data-from-csv)
13. [Drop Table (with Manual Rollback)](#drop-table)
14. [Tag a Release](#tag-a-release)
15. [Preconditions Pattern](#preconditions-pattern)
16. [Raw SQL with `endDelimiter` / `runWith` / `runInTransaction`](#raw-sql)
17. [`modifyChangeSets` (bulk attribute application)](#modifychangesets)
18. [Format SQL Changesets (alternative to YAML)](#format-sql-changesets)
19. [`validCheckSum: any` (after a non-functional edit)](#validchecksum-any)

---

## Rollback Coverage Matrix

### Auto-Generated Rollbacks (no `rollback:` block needed)

| Change | Auto-Rollback |
|---|---|
| `createTable` | `dropTable` |
| `addColumn` | `dropColumn` |
| `createIndex` | `dropIndex` |
| `addForeignKeyConstraint` | `dropForeignKeyConstraint` |
| `addUniqueConstraint` | `dropUniqueConstraint` |
| `addCheckConstraint` | `dropCheckConstraint` |
| `renameColumn` / `renameTable` | reverse rename |
| `addPrimaryKey` | `dropPrimaryKey` |

### Manual Rollback Required

| Change | Must Provide |
|---|---|
| `dropTable` | full `createTable` (data is lost — accept it) |
| `dropColumn` | `addColumn` (data is lost) |
| `insert` | `delete` (with explicit `where`) |
| `update` | reverse `update` |
| `delete` | reverse `insert` (with archived rows) |
| `sql` (raw DDL/DML) | reverse SQL — or `rollback: empty` if truly irreversible |
| `loadUpdateData` | `delete` with row-id list — or `rollback: empty` for additive seeds |
| `tagDatabase` | `rollback: empty` (tags are non-destructive) |

🔴 **`rollback: empty` is a deliberate decision, not a default.** Use it when reversing makes no sense (VACUUM, ANALYZE, post-deploy seed) — never to skip writing the rollback you owe.

---

## Create Table

```yaml
databaseChangeLog:
  - changeSet:
      id: myapp-items-001-create-table
      author: teamname
      changes:
        - createTable:
            tableName: items
            columns:
              - column:
                  name: id
                  type: uuid
                  constraints: { primaryKey: true, nullable: false }
              - column:
                  name: name
                  type: varchar(255)
                  constraints: { nullable: false }
              - column:
                  name: description
                  type: text
              - column:
                  name: price
                  type: decimal(19,4)
                  constraints: { nullable: false }
              - column:
                  name: category_id
                  type: uuid
                  constraints: { nullable: false }
              - column:
                  name: created_at
                  type: timestamp with time zone
                  constraints: { nullable: false }
              - column:
                  name: updated_at
                  type: timestamp with time zone
                  constraints: { nullable: false }
      rollback:
        - dropTable:
            tableName: items
```

---

## Add Foreign Key

```yaml
- changeSet:
    id: myapp-items-002-add-fk-category
    author: teamname
    changes:
      - addForeignKeyConstraint:
          baseTableName: items
          baseColumnNames: category_id
          referencedTableName: categories
          referencedColumnNames: id
          constraintName: fk_items_category
          onDelete: RESTRICT
          onUpdate: CASCADE
    rollback:
      - dropForeignKeyConstraint:
          baseTableName: items
          constraintName: fk_items_category
```

### `ON DELETE` Options

| Option | Behavior |
|---|---|
| `RESTRICT` | Prevent delete if referenced (default) |
| `CASCADE` | Delete referencing rows |
| `SET NULL` | Set FK column to NULL |
| `SET DEFAULT` | Set FK column to default |
| `NO ACTION` | Same as `RESTRICT` on most DBs |

---

## Add Column

```yaml
- changeSet:
    id: myapp-items-003-add-description
    author: teamname
    changes:
      - addColumn:
          tableName: items
          columns:
            - column:
                name: description
                type: text
    rollback:
      - dropColumn:
          tableName: items
          columnName: description
```

---

## Add Column with Default

```yaml
- changeSet:
    id: myapp-items-004-add-status
    author: teamname
    changes:
      - addColumn:
          tableName: items
          columns:
            - column:
                name: status
                type: varchar(20)
                defaultValue: 'ACTIVE'
                constraints: { nullable: false }
    rollback:
      - dropColumn:
          tableName: items
          columnName: status
```

🟡 On a populated table, **adding a NOT NULL column with default rewrites every row** on older PostgreSQL versions (<11). Modern PG handles this in metadata only when the default is constant — but verify on your version. For variable defaults, use Expand-Contract (see [zero-downtime.md](zero-downtime.md)).

---

## Create Index

```yaml
- changeSet:
    id: myapp-items-005-add-index-name
    author: teamname
    changes:
      - createIndex:
          tableName: items
          indexName: idx_items_name
          columns:
            - column: { name: name }
    rollback:
      - dropIndex:
          tableName: items
          indexName: idx_items_name
```

### Composite / Unique

```yaml
- createIndex:
    tableName: items
    indexName: idx_items_category_name
    columns:
      - column: { name: category_id }
      - column: { name: name }

- createIndex:
    tableName: users
    indexName: idx_users_email_unique
    unique: true
    columns:
      - column: { name: email }
```

🔴 **Live tables on PostgreSQL** — use `CREATE INDEX CONCURRENTLY` instead. See next section.

---

## Create Index Concurrently {#create-index-concurrently}

```yaml
- changeSet:
    id: myapp-items-006-add-idx-name-concurrently
    author: teamname
    runInTransaction: false   # CONCURRENTLY cannot run inside a transaction
    changes:
      - sql:
          sql: CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_items_name ON items (name);
    rollback:
      - sql:
          sql: DROP INDEX CONCURRENTLY IF EXISTS idx_items_name;
```

**Why `runInTransaction: false`:** PostgreSQL forbids `CONCURRENTLY` inside a transaction block. Liquibase wraps each changeset in a transaction by default — you must opt out for this single changeset.

---

## Add Unique Constraint

```yaml
- changeSet:
    id: myapp-users-003-unique-email
    author: teamname
    changes:
      - addUniqueConstraint:
          tableName: users
          columnNames: email
          constraintName: uk_users_email
    rollback:
      - dropUniqueConstraint:
          tableName: users
          constraintName: uk_users_email
```

---

## Enum Values: `addCheckConstraint` vs Native ENUM {#enum-values}

### 🟢 Preferred: `varchar` + `addCheckConstraint`

**Why preferred:** native PostgreSQL `ENUM` types are painful — adding a value requires `ALTER TYPE ... ADD VALUE` (which can't be in a transaction in some cases), removing one is impossible without a full type rebuild, and rollback is destructive.

```yaml
- changeSet:
    id: myapp-orders-001-status-check
    author: teamname
    changes:
      - addCheckConstraint:
          tableName: orders
          constraintName: ck_orders_status
          constraintBody: "status IN ('CREATED','PAID','SHIPPED','DELIVERED','CANCELLED','REFUNDED')"
    rollback:
      - dropCheckConstraint:
          tableName: orders
          constraintName: ck_orders_status
```

### 🟡 Native ENUM (PostgreSQL) — only when integrating with existing schema

```yaml
- changeSet:
    id: myapp-orders-001-create-status-enum
    author: teamname
    changes:
      - sql:
          splitStatements: false
          sql: |
            CREATE TYPE order_status AS ENUM (
              'CREATED', 'PAID', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED'
            );
    rollback:
      - sql:
          sql: DROP TYPE IF EXISTS order_status;
```

---

## Modify / Rename Column

```yaml
# Modify type
- changeSet:
    id: myapp-items-006-modify-name-length
    author: teamname
    changes:
      - modifyDataType:
          tableName: items
          columnName: name
          newDataType: varchar(500)
    rollback:
      - modifyDataType:
          tableName: items
          columnName: name
          newDataType: varchar(255)

# Rename column
- changeSet:
    id: myapp-items-007-rename-description
    author: teamname
    changes:
      - renameColumn:
          tableName: items
          oldColumnName: description
          newColumnName: details
          columnDataType: text
    rollback:
      - renameColumn:
          tableName: items
          oldColumnName: details
          newColumnName: description
          columnDataType: text
```

🔴 **Renaming a column on a live system breaks any app pod still reading the old name.** Use Expand-Contract: add new column → dual-write → switch reads → drop old. See [zero-downtime.md](zero-downtime.md).

---

## Insert vs `loadUpdateData` (Idempotent Seed) {#insert-vs-loadupdatedata}

### 🔴 Avoid raw `insert` for seed data that may evolve

`insert` runs once. If you tweak the seed value later, you have to write a follow-up `update` changeset and you can't easily re-run from a clean DB without divergence.

### 🟢 Preferred: `loadUpdateData` (upsert by primary key)

```yaml
- changeSet:
    id: myapp-categories-seed-001
    author: teamname
    contextFilter: "!test"
    changes:
      - loadUpdateData:
          tableName: categories
          file: data/categories.csv
          relativeToChangelogFile: true
          primaryKey: id
    rollback:
      - sql:
          sql: DELETE FROM categories WHERE id IN ('550e8400-...','660e8400-...');
```

**`data/categories.csv`:**
```csv
id,name,created_at,updated_at
550e8400-e29b-41d4-a716-446655440001,Electronics,2026-01-01T00:00:00Z,2026-01-01T00:00:00Z
550e8400-e29b-41d4-a716-446655440002,Clothing,2026-01-01T00:00:00Z,2026-01-01T00:00:00Z
```

### Inline `insert` (when CSV is overkill)

```yaml
- changeSet:
    id: myapp-categories-seed-001
    author: teamname
    contextFilter: "!test"
    changes:
      - insert:
          tableName: categories
          columns:
            - column: { name: id, value: "550e8400-e29b-41d4-a716-446655440001" }
            - column: { name: name, value: "Electronics" }
            - column: { name: created_at, valueComputed: "CURRENT_TIMESTAMP" }
            - column: { name: updated_at, valueComputed: "CURRENT_TIMESTAMP" }
    rollback:
      - delete:
          tableName: categories
          where: "id = '550e8400-e29b-41d4-a716-446655440001'"
```

---

## Load Data from CSV

```yaml
- changeSet:
    id: myapp-categories-load-csv
    author: teamname
    changes:
      - loadData:
          tableName: categories
          file: data/categories.csv
          relativeToChangelogFile: true
          separator: ","
          columns:
            - column: { name: id, type: uuid }
            - column: { name: name, type: string }
    rollback:
      - delete:
          tableName: categories
```

🟡 `loadData` does not deduplicate. Use `loadUpdateData` if rows may already exist.

---

## Drop Table (with Manual Rollback) {#drop-table}

```yaml
- changeSet:
    id: myapp-legacy-001-drop-old-items
    author: teamname
    changes:
      - dropTable:
          tableName: old_items
    rollback:
      # Must recreate full structure — data is lost!
      - createTable:
          tableName: old_items
          columns:
            - column:
                name: id
                type: uuid
                constraints: { primaryKey: true }
            - column:
                name: name
                type: varchar(255)
```

🔴 **Data is lost on drop.** Only run after migration verification. For live tables, run a `RENAME` first (deprecation period), then drop in a later release.

---

## Tag a Release {#tag-a-release}

```yaml
- changeSet:
    id: release-v2.0-tag
    author: release-bot
    changes:
      - tagDatabase:
          tag: v2.0
```

```bash
liquibase rollback v2.0   # Rolls back every changeset applied after the tag
```

---

## Preconditions Pattern {#preconditions-pattern}

```yaml
- changeSet:
    id: myapp-items-create-if-not-exists
    author: teamname
    preConditions:
      - onFail: MARK_RAN
      - not:
          - tableExists:
              tableName: items
    changes:
      - createTable:
          tableName: items
          # ...
```

| `onFail` | Effect |
|---|---|
| `HALT` | Stop (default) |
| `MARK_RAN` | Skip + record as run |
| `WARN` | Log warning, continue |
| `CONTINUE` | Skip silently |

---

## Raw SQL with `endDelimiter` / `runWith` / `runInTransaction` {#raw-sql}

### Inline SQL with custom delimiter (PL/pgSQL block)

```yaml
- changeSet:
    id: myapp-functions-001-bump-counter
    author: teamname
    changes:
      - sql:
          splitStatements: false
          stripComments: true
          endDelimiter: "/"
          sql: |
            CREATE OR REPLACE FUNCTION bump_counter() RETURNS TRIGGER AS $$
            BEGIN
              NEW.counter := COALESCE(OLD.counter, 0) + 1;
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            /
    rollback:
      - sql:
          sql: DROP FUNCTION IF EXISTS bump_counter();
```

### `runWith: psql` (Liquibase Secure only)

When you need real `psql` semantics — `\copy`, multi-statement DDL with `$$` blocks, or scripts that already work in `psql` — delegate to the native executor:

```yaml
- changeSet:
    id: myapp-functions-002-complex-script
    author: teamname
    runWith: psql
    changes:
      - sqlFile:
          path: sql/complex-functions.sql
          relativeToChangelogFile: true
```

🟡 **Do not** set `splitStatements` or `endDelimiter` with `runWith: psql` — psql parses delimiters natively. Requires `liquibase.psql.conf` for executor path/timeout.

🔴 `runWith: psql` is a **Liquibase Secure** (commercial) feature. Not available in OSS Community.

### `runInTransaction: false`

Required for any statement PostgreSQL forbids in transactions: `CREATE INDEX CONCURRENTLY`, `REINDEX CONCURRENTLY`, `VACUUM`, `ALTER SYSTEM`, certain `CREATE DATABASE` operations.

```yaml
- changeSet:
    id: myapp-vacuum-orders
    author: ops
    runInTransaction: false
    changes:
      - sql:
          sql: VACUUM ANALYZE orders;
    rollback: empty
```

---

## `modifyChangeSets` (bulk attribute application) {#modifychangesets}

When importing third-party SQL or applying the same attribute to many changesets in a file, `modifyChangeSets` (4.10+) avoids repetition:

```yaml
databaseChangeLog:
  - modifyChangeSets:
      runWith: psql              # Apply to every nested changeset
      idPrefix: imported-
      idSuffix: -v1
      changeSets:
        - changeSet:
            id: 001-create-schema
            author: imported
            changes:
              - sqlFile:
                  path: imported/001.sql
        - changeSet:
            id: 002-create-functions
            author: imported
            changes:
              - sqlFile:
                  path: imported/002.sql
```

Resulting IDs: `imported-001-create-schema-v1`, `imported-002-create-functions-v1`.

---

## Format SQL Changesets (alternative to YAML) {#format-sql-changesets}

Plain `.sql` files become Liquibase changelogs by adding the `--liquibase formatted sql` header:

```sql
--liquibase formatted sql

--changeset teamname:myapp-items-001-create-table
CREATE TABLE items (
  id          uuid PRIMARY KEY,
  name        varchar(255) NOT NULL,
  created_at  timestamptz NOT NULL
);
--rollback DROP TABLE items;

--changeset teamname:myapp-items-002-add-idx-name runInTransaction:false
CREATE INDEX CONCURRENTLY idx_items_name ON items (name);
--rollback DROP INDEX CONCURRENTLY IF EXISTS idx_items_name;
```

🟢 **Use formatted SQL when:** the team prefers SQL syntax, you're working with DBA-authored scripts, or you need the file to be runnable directly via `psql` for debugging.

🟡 **Stick with YAML when:** you want database-agnostic changes (`createTable` works on PG/MySQL/Oracle), preconditions, or readable diffs across change types.

---

## `validCheckSum: any` (after a non-functional edit) {#validchecksum-any}

When you've made a cosmetic edit (typo in comment, formatting) to an already-applied changeset and don't want to break checksum validation across environments:

```yaml
- changeSet:
    id: myapp-items-001-create-table
    author: teamname
    validCheckSum: any           # Tolerate any prior checksum (4.27+)
    changes:
      - createTable: ...
```

🔴 **Never** use this to mask functional changes. Functional changes must be a NEW changeset. `validCheckSum: any` is for the equivalent of "I added a missing comma in a comment".
