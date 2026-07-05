# Spring Boot Liquibase Configuration Reference

> Spring Boot 4.x · Liquibase 5.0+ · PostgreSQL 17. The `LiquibaseProperties` class moved to `org.springframework.boot.liquibase.autoconfigure` in Spring Boot 4 (was `org.springframework.boot.autoconfigure.liquibase` in 3.x).

---

## Table of Contents

1. [Basic Configuration](#basic-configuration)
2. [Modern Properties (`show-summary`, `ui-service`, `analytics-enabled`)](#modern-properties)
3. [Environment-Specific Parameters](#environment-specific-parameters)
4. [Profile-Specific Configuration](#profile-specific-configuration)
5. [Multi-Datasource Configuration](#multi-datasource-configuration)
6. [Startup Behavior (no `async`)](#startup-behavior)
7. [Logging Configuration](#logging-configuration)
8. [Common Properties Reference](#common-properties-reference)
9. [Testing Strategies (`@ServiceConnection`)](#testing-strategies)
10. [Troubleshooting](#troubleshooting)

---

## Basic Configuration

### `application.yml`

```yaml
spring:
  liquibase:
    # Master changelog location
    change-log: classpath:/db/changelog/db.changelog-master.yaml

    # Enable/disable migrations
    enabled: true

    # Filters (4.16+ — old `contexts` / `labels` are still supported on the SB side)
    contexts: ${LIQUIBASE_CONTEXTS:dev}
    labels: ${LIQUIBASE_LABELS:}

    # Output behavior (Spring Boot 3.4+ / SB 4)
    show-summary: summary        # off | summary | verbose
    ui-service: logger           # console | logger — use `logger` in containers/CI

    # Telemetry — disable for air-gapped environments (Liquibase 4.27+)
    analytics-enabled: false

    # Custom tracking tables
    database-change-log-table: DATABASECHANGELOG
    database-change-log-lock-table: DATABASECHANGELOGLOCK

    # Schemas
    liquibase-schema: ${DB_SCHEMA:public}
    default-schema: ${DB_SCHEMA:public}

    # Tag to roll back to (used by `liquibase rollback` ops, not at boot)
    tag: ${ROLLBACK_TAG:}

    # 🔴 DANGEROUS — dev-only
    drop-first: false
    clear-checksums: false
```

🟡 **There is no `spring.liquibase.async` property.** Liquibase always runs synchronously during `ApplicationContext` initialization. If you need asynchronous migration, wire a custom `SpringLiquibase` bean and start it on a dedicated thread — but understand the race conditions you're accepting.

---

## Modern Properties

### `show-summary` (Spring Boot 3.4+)

Controls the post-migration summary printed to the configured `ui-service`:

| Value | Output |
|---|---|
| `off` | Nothing |
| `summary` | Per-changeset PASS/FAIL counts (default) |
| `verbose` | Full per-changeset table |

### `ui-service` (Liquibase 4.25+)

| Value | Where output goes |
|---|---|
| `console` | Direct `System.out` (default) — fine for local dev |
| `logger` | Through Liquibase's logger (SLF4J → Logback) — preferred in containers |

🟢 **Use `logger` in production.** It routes summary output through your standard log pipeline instead of bypassing it via `System.out`.

### `analytics-enabled` (Liquibase 4.27+)

Liquibase OSS sends anonymous usage analytics by default. Disable in regulated/air-gapped environments:

```yaml
spring:
  liquibase:
    analytics-enabled: false
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
# In a changelog
- changeSet:
    id: create-schema
    author: teamname
    changes:
      - sql:
          sql: CREATE SCHEMA IF NOT EXISTS ${schema_name}

- changeSet:
    id: create-users-table
    author: teamname
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

🔴 Never expose secrets via parameters. Inject them through environment variables already supplied to the JVM by your secrets manager.

---

## Profile-Specific Configuration

### Development

```yaml
# application-dev.yml
spring:
  liquibase:
    contexts: dev
    parameters:
      seed_data: true
```

### Test

```yaml
# application-test.yml
spring:
  liquibase:
    # Option A — use a `test` context to skip seed data
    contexts: test

    # Option B — disable Liquibase entirely (rare; only when @Sql / pre-seeded snapshot)
    # enabled: false
```

### Production

```yaml
# application-prod.yml
spring:
  liquibase:
    contexts: prod
    drop-first: false        # 🔴 Always
    clear-checksums: false   # 🔴 Always
    show-summary: summary
    ui-service: logger
    analytics-enabled: false
    parameters:
      seed_data: false
```

---

## Multi-Datasource Configuration

### Primary + Secondary

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

🟡 With multiple datasources, Spring Boot's `LiquibaseAutoConfiguration` won't apply automatically. The two beans above replace it for both DataSources.

---

## Startup Behavior

By default, Liquibase runs during `ApplicationContext` initialization. The application **will not be marked ready** until migrations complete — this is the desired behavior for nearly every deployment.

🔴 **Do not try to make Liquibase asynchronous via Spring config.** No such property exists. If your migration is too slow for liveness probes, the right answer is one of:

1. **Run migrations as a separate Kubernetes Job / init container** before the app starts (recommended for production)
2. **Increase the readiness probe initial delay** to cover migration time
3. **Move slow data backfills out of Liquibase** into background jobs gated by a feature flag (Expand-Contract pattern — see [zero-downtime.md](zero-downtime.md))

---

## Logging Configuration

### Migration Progress

```yaml
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

🟡 SQL logging is verbose — enable only when debugging a specific changeset, never in production.

---

## Common Properties Reference

| Property | Default | Description |
|---|---|---|
| `spring.liquibase.enabled` | `true` | Enable Liquibase |
| `spring.liquibase.change-log` | `classpath:/db/changelog/db.changelog-master.yaml` | Master changelog |
| `spring.liquibase.contexts` | – | Contexts to apply |
| `spring.liquibase.labels` | – | Labels to apply |
| `spring.liquibase.show-summary` | `summary` | `off` / `summary` / `verbose` (3.4+) |
| `spring.liquibase.ui-service` | `console` | `console` / `logger` (3.4+) |
| `spring.liquibase.analytics-enabled` | `true` | Liquibase OSS telemetry (4.27+) |
| `spring.liquibase.default-schema` | – | Default schema |
| `spring.liquibase.liquibase-schema` | – | Schema for tracking tables |
| `spring.liquibase.database-change-log-table` | `DATABASECHANGELOG` | Changelog table |
| `spring.liquibase.database-change-log-lock-table` | `DATABASECHANGELOGLOCK` | Lock table |
| `spring.liquibase.drop-first` | `false` | 🔴 DANGEROUS — drop DB on start |
| `spring.liquibase.clear-checksums` | `false` | 🔴 Reset checksums on start |
| `spring.liquibase.tag` | – | Roll back to tag (operations) |
| `spring.liquibase.rollback-file` | – | Write rollback SQL to file |
| `spring.liquibase.parameters.*` | – | Custom parameters |

---

## Testing Strategies

### 🟢 Preferred: Testcontainers + `@ServiceConnection`

Spring Boot 3.1+ (default in SB 4) auto-wires the container's JDBC URL — no `@DynamicPropertySource` boilerplate. Liquibase runs against the real container at startup.

```java
@SpringBootTest
@Testcontainers
class IntegrationTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17-alpine");

    @Test
    void liquibaseMigrationsApply() {
        // Liquibase has already migrated the container — assert against schema.
    }
}
```

Load the `common-java-testing` skill (Testcontainers reference) for the full setup (singleton pattern, reusable containers, parallel execution).

### 🟡 Escape hatch: `@DynamicPropertySource`

Only when you need to override properties Spring Boot's auto-config can't derive (e.g. custom datasource bean):

```java
@DynamicPropertySource
static void configureProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
    registry.add("spring.datasource.username", postgres::getUsername);
    registry.add("spring.datasource.password", postgres::getPassword);
}
```

### 🟢 Disable Liquibase entirely (when using `@Sql` or pre-seeded snapshot)

```yaml
# application-test.yml
spring:
  liquibase:
    enabled: false
```

```java
@SpringBootTest
@Sql(scripts = "/test-data.sql")
class OrderServiceTest { /* ... */ }
```

🟡 This bypasses the migration verification you'd normally get from running Liquibase. Prefer the Testcontainers approach unless you have a specific reason to skip migrations.

---

## Troubleshooting

### Lock Table Stuck After Crashed Migration

If a previous run crashed with the lock held:

```sql
-- Manually clear (use with caution; ensure no active migration!)
UPDATE DATABASECHANGELOGLOCK SET LOCKED = false, LOCKEDBY = NULL, LOCKGRANTED = NULL WHERE ID = 1;
```

Or via CLI:

```bash
liquibase release-locks
```

### Checksum Mismatch

```
Validation Failed: 1 changesets check sum was...
```

Solutions, in order of preference:

1. **Create a NEW changeset** for the intended change (don't edit the old one)
2. For a **non-functional edit** only (typo, formatting), add `validCheckSum: any` to the impacted changeset (4.27+):
   ```yaml
   - changeSet:
       id: items-001-create
       author: team
       validCheckSum: any
       changes: [...]
   ```
3. **Dev-only:** `spring.liquibase.clear-checksums: true` — wipes ALL checksums. Never enable in shared environments.

### Migration Order Issues

1. Verify the `include` order in the master changelog matches dependency direction (parents before children)
2. With `includeAll`, ensure filenames carry timestamps (`MMYYYY`) — alphabetic order is the default
3. After moving files, set `logicalFilePath` (see [changelog-structure.md](changelog-structure.md#handling-file-moves--renames))

### Spring Boot 4 Import Failure

If you see `package org.springframework.boot.autoconfigure.liquibase does not exist`, update imports — `LiquibaseProperties` moved in SB 4:

```java
// 🔴 Spring Boot 3.x
import org.springframework.boot.autoconfigure.liquibase.LiquibaseProperties;

// ✅ Spring Boot 4.x
import org.springframework.boot.liquibase.autoconfigure.LiquibaseProperties;
```
