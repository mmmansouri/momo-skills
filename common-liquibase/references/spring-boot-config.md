# Spring Boot Liquibase Configuration Reference

## Basic Configuration

### application.yml

```yaml
spring:
  liquibase:
    # Master changelog location
    change-log: classpath:/db/changelog/db.changelog-master.yaml

    # Enable/disable migrations
    enabled: true

    # Contexts to run (comma-separated)
    contexts: ${LIQUIBASE_CONTEXTS:dev}

    # Labels to run
    labels: ${LIQUIBASE_LABELS:}

    # Custom tracking tables
    database-change-log-table: DATABASECHANGELOG
    database-change-log-lock-table: DATABASECHANGELOGLOCK

    # Schema for tracking tables (if different from default)
    liquibase-schema: ${DB_SCHEMA:public}

    # Default schema for migrations
    default-schema: ${DB_SCHEMA:public}

    # Drop database first (DANGEROUS - dev only!)
    drop-first: false

    # Clear checksums (use for development only)
    clear-checksums: false
```

---

## Environment-Specific Parameters

### Using Parameters in Changelogs

```yaml
# application.yml
spring:
  liquibase:
    parameters:
      schema_name: ${DB_SCHEMA:public}
      table_prefix: ${TABLE_PREFIX:}
      admin_email: ${ADMIN_EMAIL:admin@example.com}
```

```yaml
# In changelog
- changeSet:
    id: create-schema
    changes:
      - sql:
          sql: CREATE SCHEMA IF NOT EXISTS ${schema_name}

- changeSet:
    id: create-users-table
    changes:
      - createTable:
          schemaName: ${schema_name}
          tableName: ${table_prefix}users
          columns:
            - column:
                name: email
                type: varchar(255)
                defaultValue: ${admin_email}
```

---

## Profile-Specific Configuration

### Development Profile

```yaml
# application-dev.yml
spring:
  liquibase:
    contexts: dev
    # Run seed data for development
    parameters:
      seed_data: true
```

### Test Profile

```yaml
# application-test.yml
spring:
  liquibase:
    # Option 1: Use test context
    contexts: test

    # Option 2: Disable completely (use @Sql or embedded DB)
    enabled: false
```

### Production Profile

```yaml
# application-prod.yml
spring:
  liquibase:
    contexts: prod
    # Never drop in production!
    drop-first: false
    clear-checksums: false
    parameters:
      seed_data: false
```

---

## Multi-Datasource Configuration

### Primary and Secondary Databases

```java
@Configuration
public class LiquibaseConfig {

    @Bean
    @Primary
    public SpringLiquibase primaryLiquibase(
            @Qualifier("primaryDataSource") DataSource dataSource) {
        SpringLiquibase liquibase = new SpringLiquibase();
        liquibase.setDataSource(dataSource);
        liquibase.setChangeLog("classpath:/db/changelog/primary/db.changelog-master.yaml");
        liquibase.setContexts("dev");
        return liquibase;
    }

    @Bean
    public SpringLiquibase secondaryLiquibase(
            @Qualifier("secondaryDataSource") DataSource dataSource) {
        SpringLiquibase liquibase = new SpringLiquibase();
        liquibase.setDataSource(dataSource);
        liquibase.setChangeLog("classpath:/db/changelog/secondary/db.changelog-master.yaml");
        liquibase.setContexts("dev");
        return liquibase;
    }
}
```

---

## Startup Behavior

### Run Before Application Ready

By default, Liquibase runs during `ApplicationContext` initialization. The application won't start until migrations complete.

### Async Migrations (Not Recommended)

```yaml
# application.yml
spring:
  liquibase:
    # Run migrations asynchronously (risky!)
    # Application may start before migrations complete
    async: true
```

**Warning:** Async migrations can cause race conditions. Only use if you understand the implications.

---

## Logging Configuration

### Show Migration Progress

```yaml
# application.yml
logging:
  level:
    liquibase: INFO
    liquibase.changelog: DEBUG
    liquibase.executor: DEBUG
```

### SQL Logging

```yaml
logging:
  level:
    liquibase.executor.jvm.JdbcExecutor: DEBUG
```

---

## Common Properties Reference

| Property | Default | Description |
|----------|---------|-------------|
| `spring.liquibase.enabled` | `true` | Enable Liquibase |
| `spring.liquibase.change-log` | `classpath:/db/changelog/db.changelog-master.yaml` | Master changelog |
| `spring.liquibase.contexts` | - | Contexts to run |
| `spring.liquibase.labels` | - | Labels to run |
| `spring.liquibase.default-schema` | - | Default schema |
| `spring.liquibase.liquibase-schema` | - | Schema for tracking tables |
| `spring.liquibase.database-change-log-table` | `DATABASECHANGELOG` | Changelog table name |
| `spring.liquibase.database-change-log-lock-table` | `DATABASECHANGELOGLOCK` | Lock table name |
| `spring.liquibase.drop-first` | `false` | Drop DB before migrations |
| `spring.liquibase.clear-checksums` | `false` | Clear all checksums |
| `spring.liquibase.parameters.*` | - | Custom parameters |
| `spring.liquibase.tag` | - | Tag to roll back to |
| `spring.liquibase.rollback-file` | - | File to write rollback SQL |

---

## Testing Strategies

### Option 1: Use Test Context

```yaml
# application-test.yml
spring:
  liquibase:
    contexts: test
```

```yaml
# In changelog - skip seed data in tests
- changeSet:
    id: seed-categories
    context: "!test"
    changes:
      - insert: ...
```

### Option 2: Disable and Use @Sql

```yaml
# application-test.yml
spring:
  liquibase:
    enabled: false
```

```java
@SpringBootTest
@Sql(scripts = "/test-data.sql")
class OrderServiceTest {
    // Tests with custom test data
}
```

### Option 3: Testcontainers with Full Migrations

```java
@Testcontainers
@SpringBootTest
class IntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        // Liquibase runs automatically against container
    }
}
```

---

## Troubleshooting

### Lock Table Issues

If migrations fail and leave lock:

```sql
-- Manual cleanup (use with caution)
DELETE FROM DATABASECHANGELOGLOCK WHERE LOCKED = true;
```

Or via configuration:

```yaml
spring:
  liquibase:
    # Force release lock on startup (dev only)
    # Not recommended for production
```

### Checksum Mismatch

```
Validation Failed: 1 changesets check sum was...
```

Solutions:
1. **Never edit applied changesets** - create new ones instead
2. **Development only:** `clear-checksums: true` (resets all)
3. **Production:** Use `validCheckSum` in changeset:

```yaml
- changeSet:
    id: items-001-create
    author: team
    validCheckSum: 8:abc123  # Old checksum
    validCheckSum: 8:def456  # New checksum (after fix)
    changes: ...
```

### Migration Order Issues

If changelogs run in wrong order:

1. Check `include` order in master changelog
2. Use timestamps in filenames with `includeAll`
3. Verify `logicalFilePath` for moved files
