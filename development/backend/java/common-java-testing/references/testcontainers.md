# Testcontainers Reference

> Real-dependency integration testing with Testcontainers 2.x and Spring Boot 4 `@ServiceConnection`.

---

## Table of Contents

1. [When to Use Testcontainers](#when-to-use-testcontainers)
2. [@ServiceConnection — Default Wiring](#serviceconnection--default-wiring)
3. [Container Lifecycle Strategies](#container-lifecycle-strategies)
4. [PostgreSQL](#postgresql)
5. [Redis](#redis)
6. [Kafka](#kafka)
7. [Generic Container](#generic-container)
8. [Reusable Containers](#reusable-containers)
9. [Parallel Test Execution](#parallel-test-execution)
10. [Local Development with Testcontainers](#local-development-with-testcontainers)
11. [Common Pitfalls](#common-pitfalls)

---

## When to Use Testcontainers

| Scenario | Use Testcontainers? |
|----------|---------------------|
| `@DataJpaTest` against the real DB engine | ✅ Yes — H2 lies |
| `@SpringBootTest` end-to-end with infra | ✅ Yes |
| External HTTP API (Stripe, Mailgun) | ❌ No — use WireMock / MockWebServer (process boundary) |
| Pure unit test (no I/O) | ❌ No — slows the suite |
| Cron / scheduled job logic | ❌ No — inject `Clock` |

**Why a real DB:** every embedded DB diverges silently from production (H2 vs Postgres on `JSONB`, partial indexes, `STRING_AGG`, lateral joins, default `null` ordering). A green H2 test against a broken Postgres migration is the worst outcome.

---

## @ServiceConnection — Default Wiring

Spring Boot 4 enhances `@ServiceConnection` so it derives all `spring.datasource.*` / `spring.data.redis.*` / `spring.kafka.*` properties automatically. Prefer it over `@DynamicPropertySource`.

### 🟢 DEFAULT — Single Container per Test Class

```java
@SpringBootTest
@Testcontainers
class OrderApiTest {

    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17");

    @Autowired OrderRepository repository;

    @Test
    void persistsOrder() {
        var saved = repository.save(new Order(...));
        assertThat(repository.findById(saved.getId())).isPresent();
    }
}
```

`@ServiceConnection` reads the container image, picks the matching `ConnectionDetails`, and overrides every related property — no `@DynamicPropertySource` boilerplate.

### 🟡 ESCAPE HATCH — `@DynamicPropertySource`

<details>
<summary>Only when no <code>ConnectionDetails</code> exists for your container (custom image, exotic service)</summary>

```java
@DynamicPropertySource
static void registerProps(DynamicPropertyRegistry registry) {
    registry.add("custom.endpoint", customContainer::getEndpoint);
}
```
</details>

---

## Container Lifecycle Strategies

| Strategy | When to use | Cost |
|----------|-------------|------|
| `static` field + `@Container` | One container shared across all methods of a class | Low — one start per class |
| Singleton (started once for the JVM) | Container shared across many test classes | Lowest — one start per JVM |
| Per-method (`@BeforeEach`) | Each test needs a fresh DB | High — avoid unless required |

### 🟢 Singleton Pattern (Shared Across the Suite)

```java
public abstract class IntegrationTest {

    @ServiceConnection
    static PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:17")
        .withReuse(true);

    static {
        POSTGRES.start();  // Started once for the JVM, never stopped explicitly
    }
}
```

Subclass for every integration test:
```java
@SpringBootTest
class OrderApiTest extends IntegrationTest { /* ... */ }
```

**Why:** Postgres takes ~2s to start. With 50 integration tests, restarting per-class adds 100s to the suite for no benefit.

---

## PostgreSQL

```java
@ServiceConnection
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17")
    .withDatabaseName("app")
    .withUsername("app")
    .withPassword("app");
```

### Migrations

Liquibase / Flyway run automatically on context start. For tests that mutate schema, isolate with transactional rollback (`@Transactional` on the test) — not container restart.

---

## Redis

```java
@ServiceConnection(name = "redis")
static GenericContainer<?> redis =
    new GenericContainer<>("redis:7-alpine").withExposedPorts(6379);
```

Spring Boot 4 derives `spring.data.redis.host` / `spring.data.redis.port` from the named connection.

---

## Kafka

```java
@ServiceConnection
static KafkaContainer kafka = new KafkaContainer("apache/kafka:3.8.0");
```

For tests asserting on consumed messages, prefer Awaitility:

```java
await().atMost(5, SECONDS).untilAsserted(() ->
    assertThat(consumer.poll(Duration.ZERO))
        .anySatisfy(record -> assertThat(record.value()).contains("expected")));
```

---

## Generic Container

For services without a dedicated module:

```java
@Container
static GenericContainer<?> mailhog = new GenericContainer<>("mailhog/mailhog:v1.0.1")
    .withExposedPorts(1025, 8025);

@DynamicPropertySource
static void mailProps(DynamicPropertyRegistry r) {
    r.add("spring.mail.host", mailhog::getHost);
    r.add("spring.mail.port", () -> mailhog.getMappedPort(1025));
}
```

---

## Reusable Containers

Cuts startup cost across `mvn test` invocations during local dev — disabled in CI.

`~/.testcontainers.properties`:
```properties
testcontainers.reuse.enable=true
```

```java
new PostgreSQLContainer<>("postgres:17").withReuse(true)
```

### 🟡 WARNING — Never enable reuse in CI

Reused containers carry state from previous runs (rows, indexes, sequence values). On a clean CI runner, set `testcontainers.reuse.enable=false`.

---

## Parallel Test Execution

JUnit 5 parallel mode + Testcontainers requires either:

1. **Singleton container** shared across threads (recommended), or
2. **Distinct ports / DBs** per parallel class — let Testcontainers map random ports

```properties
# junit-platform.properties
junit.jupiter.execution.parallel.enabled=true
junit.jupiter.execution.parallel.mode.default=concurrent
junit.jupiter.execution.parallel.mode.classes.default=concurrent
```

---

## Local Development with Testcontainers

Spring Boot 4 ships `spring-boot-testcontainers` for `bootRun` parity with tests:

```java
@TestConfiguration(proxyBeanMethods = false)
public class TestcontainersConfig {

    @Bean
    @ServiceConnection
    public PostgreSQLContainer<?> postgres() {
        return new PostgreSQLContainer<>("postgres:17");
    }
}
```

Launcher:
```java
public class TestApp {
    public static void main(String[] args) {
        SpringApplication.from(MyApp::main)
            .with(TestcontainersConfig.class)
            .run(args);
    }
}
```

`./gradlew bootTestRun` (or the Maven equivalent) starts the app with the same containers as the tests — zero divergence between dev and test infra.

---

## Common Pitfalls

### Forgetting `@Testcontainers`

```java
// 🔴 WRONG — container starts but Testcontainers extension isn't wired
@SpringBootTest
class Broken {
    @ServiceConnection
    static PostgreSQLContainer<?> pg = new PostgreSQLContainer<>("postgres:17");
}

// ✅ CORRECT
@SpringBootTest
@Testcontainers
class Works {
    @ServiceConnection
    static PostgreSQLContainer<?> pg = new PostgreSQLContainer<>("postgres:17");
}
```

### Mixing H2 with @DataJpaTest

```java
// 🔴 WRONG — Boot replaces the DataSource with H2 by default
@DataJpaTest
class OrderRepoTest { /* ... */ }

// ✅ CORRECT
@DataJpaTest
@AutoConfigureTestDatabase(replace = NONE)
@Testcontainers
class OrderRepoTest { /* ... */ }
```

### Slow tests because the image is pulled per class

Use a singleton or set `withReuse(true)` locally. Pin image versions (`postgres:17` not `postgres:latest`) — `latest` re-pulls on every release.

### Testcontainers 2.0 module migration

Testcontainers 2.x renames module coordinates and packages. If `@ServiceConnection` reports *"No ConnectionDetails found"*, the container class is from the old module — update both the dependency and the `import`.
