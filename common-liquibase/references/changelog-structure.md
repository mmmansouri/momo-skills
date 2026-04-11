# Changelog Structure Reference

## Recommended Directory Structure

```
src/main/resources/db/changelog/
├── db.changelog-master.yaml       # Master file - includes only
├── items/                         # Feature: items
│   ├── items-create-012025.yaml
│   ├── items-add-fk-category-012025.yaml
│   └── items-add-description-022025.yaml
├── orders/                        # Feature: orders
│   ├── orders-create-012025.yaml
│   ├── orders-status-enum-012025.yaml
│   └── orders-add-tracking-022025.yaml
├── customers/                     # Feature: customers
│   └── customers-create-012025.yaml
└── data/                          # Seed data
    ├── categories-seed-012025.yaml
    └── users-admin-seed-012025.yaml
```

---

## Master Changelog

The master changelog should ONLY contain `include` tags:

```yaml
# db.changelog-master.yaml
databaseChangeLog:
  # Tables - in dependency order
  - include:
      file: customers/customers-create-012025.yaml
      relativeToChangelogFile: true
  - include:
      file: items/items-create-012025.yaml
      relativeToChangelogFile: true
  - include:
      file: items/items-add-fk-category-012025.yaml
      relativeToChangelogFile: true
  - include:
      file: orders/orders-status-enum-012025.yaml
      relativeToChangelogFile: true
  - include:
      file: orders/orders-create-012025.yaml
      relativeToChangelogFile: true

  # Seed data
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
|--------|----------|
| `create` | Initial table creation |
| `add-<column>` | Add new column |
| `add-fk-<target>` | Add foreign key |
| `add-index-<column>` | Add index |
| `drop-<column>` | Remove column |
| `modify-<column>` | Alter column type/constraint |
| `seed-data` | Insert reference data |

### Examples

```
myapp-items-create-012025.yaml
myapp-items-add-description-022025.yaml
myapp-items-add-fk-category-012025.yaml
myapp-items-add-index-name-022025.yaml
myapp-orders-status-enum-012025.yaml
myapp-categories-seed-data-012025.yaml
```

---

## Include Patterns

### Single File Include

```yaml
- include:
    file: path/to/changelog.yaml
    relativeToChangelogFile: true
```

### Include All Files in Directory

```yaml
- includeAll:
    path: items/
    relativeToChangelogFile: true
```

**Warning:** `includeAll` processes files alphabetically. Use timestamps in filenames to ensure correct order.

### Conditional Include

```yaml
- include:
    file: data/test-data.yaml
    relativeToChangelogFile: true
    context: test
```

---

## Handling File Moves/Renames

When moving or renaming changelog files, Liquibase will try to re-apply them (different path = different changeset).

### Solution: logicalFilePath

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

---

## Version-Based Organization (Alternative)

For projects with release cycles:

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
  - includeAll:
      path: v1.0/
      relativeToChangelogFile: true
  - includeAll:
      path: v1.1/
      relativeToChangelogFile: true
  - includeAll:
      path: v2.0/
      relativeToChangelogFile: true
```

---

## Dependency Order

Tables must be created before their foreign keys can reference them:

```yaml
# CORRECT ORDER
databaseChangeLog:
  # 1. Independent tables first
  - include: { file: categories-create.yaml }
  - include: { file: customers-create.yaml }

  # 2. Dependent tables
  - include: { file: items-create.yaml }  # References categories
  - include: { file: orders-create.yaml } # References customers

  # 3. Foreign keys (optional separate files)
  - include: { file: items-add-fk-category.yaml }
  - include: { file: orders-add-fk-customer.yaml }

  # 4. Indexes
  - include: { file: items-add-indexes.yaml }

  # 5. Seed data
  - include: { file: seed-categories.yaml }
```

---

## Anti-Patterns to Avoid

### ❌ Grouping by Change Type

```
# BAD - Leads to circular dependencies
db/changelog/
├── tables/
│   ├── all-tables.yaml
├── foreign-keys/
│   ├── all-fks.yaml      # Needs tables to exist first
└── indexes/
    ├── all-indexes.yaml  # Needs tables to exist first
```

**Problem:** Foreign keys need tables to exist, but the FK changelog runs after ALL tables. If table B references table A, and table A's FK references table C, you get circular dependencies.

### ❌ Changesets in Master Changelog

```yaml
# BAD - Don't mix includes and changesets
databaseChangeLog:
  - include: { file: items.yaml }
  - changeSet:       # NO! Put this in its own file
      id: quick-fix
      changes: ...
```

### ❌ Editing Applied Changesets

Once a changeset is applied, its checksum is stored. Any edit changes the checksum and causes:

```
Validation Failed:
  1 changesets check sum was:
    items-001-create was: 8:abc123 but is now: 8:def456
```

**Solution:** Create a NEW changeset for modifications.
