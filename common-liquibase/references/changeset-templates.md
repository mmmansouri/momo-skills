# Changeset Templates Reference

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
                  constraints:
                    primaryKey: true
                    nullable: false
              - column:
                  name: name
                  type: varchar(255)
                  constraints:
                    nullable: false
              - column:
                  name: description
                  type: text
                  constraints:
                    nullable: true
              - column:
                  name: price
                  type: decimal(19,4)
                  constraints:
                    nullable: false
              - column:
                  name: category_id
                  type: uuid
                  constraints:
                    nullable: false
              - column:
                  name: created_at
                  type: timestamp with time zone
                  constraints:
                    nullable: false
              - column:
                  name: updated_at
                  type: timestamp with time zone
                  constraints:
                    nullable: false
      rollback:
        - dropTable:
            tableName: items
```

---

## Add Foreign Key

```yaml
databaseChangeLog:
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

### ON DELETE Options

| Option | Behavior |
|--------|----------|
| `RESTRICT` | Prevent delete if referenced (default) |
| `CASCADE` | Delete referencing rows |
| `SET NULL` | Set FK column to NULL |
| `SET DEFAULT` | Set FK column to default |
| `NO ACTION` | Same as RESTRICT in most DBs |

---

## Add Column

```yaml
databaseChangeLog:
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
                  constraints:
                    nullable: true
      rollback:
        - dropColumn:
            tableName: items
            columnName: description
```

---

## Add Column with Default Value

```yaml
databaseChangeLog:
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
                  constraints:
                    nullable: false
      rollback:
        - dropColumn:
            tableName: items
            columnName: status
```

---

## Create Index

```yaml
databaseChangeLog:
  - changeSet:
      id: myapp-items-005-add-index-name
      author: teamname
      changes:
        - createIndex:
            tableName: items
            indexName: idx_items_name
            columns:
              - column:
                  name: name
      rollback:
        - dropIndex:
            tableName: items
            indexName: idx_items_name
```

### Composite Index

```yaml
- createIndex:
    tableName: items
    indexName: idx_items_category_name
    columns:
      - column:
          name: category_id
      - column:
          name: name
```

### Unique Index

```yaml
- createIndex:
    tableName: users
    indexName: idx_users_email_unique
    unique: true
    columns:
      - column:
          name: email
```

---

## Add Unique Constraint

```yaml
databaseChangeLog:
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

## Create ENUM Type (PostgreSQL)

```yaml
databaseChangeLog:
  - changeSet:
      id: myapp-orders-001-create-status-enum
      author: teamname
      changes:
        - sql:
            sql: >
              CREATE TYPE order_status AS ENUM (
                'CREATED', 'PAID', 'SHIPPED', 'DELIVERED',
                'CANCELLED', 'FINISHED', 'REFUNDED'
              );
      rollback:
        - sql:
            sql: DROP TYPE IF EXISTS order_status;
```

### Use ENUM in Table

```yaml
- column:
    name: status
    type: order_status
    constraints:
      nullable: false
```

---

## Modify Column

```yaml
databaseChangeLog:
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
```

---

## Rename Column

```yaml
databaseChangeLog:
  - changeSet:
      id: myapp-items-007-rename-column
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

---

## Insert Data (Seed)

```yaml
databaseChangeLog:
  - changeSet:
      id: myapp-categories-seed-001
      author: teamname
      context: "!test"  # Skip in test
      changes:
        - insert:
            tableName: categories
            columns:
              - column:
                  name: id
                  value: "550e8400-e29b-41d4-a716-446655440001"
              - column:
                  name: name
                  value: "Electronics"
              - column:
                  name: created_at
                  valueComputed: CURRENT_TIMESTAMP
              - column:
                  name: updated_at
                  valueComputed: CURRENT_TIMESTAMP
        - insert:
            tableName: categories
            columns:
              - column:
                  name: id
                  value: "550e8400-e29b-41d4-a716-446655440002"
              - column:
                  name: name
                  value: "Clothing"
              - column:
                  name: created_at
                  valueComputed: CURRENT_TIMESTAMP
              - column:
                  name: updated_at
                  valueComputed: CURRENT_TIMESTAMP
      rollback:
        - delete:
            tableName: categories
            where: id IN ('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002')
```

---

## Load Data from CSV

```yaml
databaseChangeLog:
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
              - column:
                  name: id
                  type: uuid
              - column:
                  name: name
                  type: string
      rollback:
        - delete:
            tableName: categories
```

---

## Drop Table (With Manual Rollback)

```yaml
databaseChangeLog:
  - changeSet:
      id: myapp-legacy-001-drop-old-table
      author: teamname
      changes:
        - dropTable:
            tableName: old_items
      rollback:
        # Must recreate table structure!
        - createTable:
            tableName: old_items
            columns:
              - column:
                  name: id
                  type: uuid
                  constraints:
                    primaryKey: true
              - column:
                  name: name
                  type: varchar(255)
```

**Warning:** Data is lost on drop! Only use when data migration is complete.

---

## Preconditions Example

```yaml
databaseChangeLog:
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

---

## Raw SQL (Use Sparingly)

```yaml
databaseChangeLog:
  - changeSet:
      id: myapp-custom-001
      author: teamname
      changes:
        - sql:
            sql: >
              UPDATE items
              SET status = 'ACTIVE'
              WHERE status IS NULL;
      rollback:
        - sql:
            sql: >
              UPDATE items
              SET status = NULL
              WHERE status = 'ACTIVE';
```

**Note:** Avoid raw SQL when Liquibase changes exist. Raw SQL is harder to rollback and may be DB-specific.
