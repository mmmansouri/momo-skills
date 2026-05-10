# JPA Performance Reference

> Hibernate 7 / Spring Data JPA 4 / Spring Boot 4 performance patterns.
> N+1, batch processing, second-level cache, pagination, virtual threads, AOT/native.

---

## Table of Contents

1. [N+1 — Detection & Solutions Beyond the Basics](#n1--detection--solutions-beyond-the-basics)
2. [Batch Processing — Beyond `flush/clear`](#batch-processing--beyond-flushclear)
3. [Bulk Update / Delete (JPQL & Criteria)](#bulk-update--delete-jpql--criteria)
4. [Second-Level Cache Setup](#second-level-cache-setup)
5. [Query Cache](#query-cache)
6. [Connection Pooling (HikariCP 7)](#connection-pooling-hikaricp-7)
7. [DTO Projections](#dto-projections)
8. [Pagination — Window/Keyset First](#pagination--windowkeyset-first)
9. [Virtual Threads](#virtual-threads)
10. [Native Image / GraalVM](#native-image--graalvm)
11. [Type-Safe Find Options (Hibernate 7)](#type-safe-find-options-hibernate-7)
12. [Monitoring & Debugging](#monitoring--debugging)

---

## N+1 — Detection & Solutions Beyond the Basics

The basic JOIN FETCH / `@EntityGraph` solutions are documented in `SKILL.md`. This section covers detection and the cases where they are not enough.

### Detect N+1 in Tests

```java
@Test
void shouldNotCauseNPlusOne() {
    Statistics stats = sessionFactory.unwrap(SessionFactory.class).getStatistics();
    stats.clear();
    stats.setStatisticsEnabled(true);

    List<Order> orders = orderService.findAllWithCustomers();

    assertThat(stats.getPrepareStatementCount()).isEqualTo(1);
}
```

### When `JOIN FETCH` Becomes a Cartesian Product

Multiple `JOIN FETCH` on collections explode result rows. Two safe options:

```java
// 🔴 WRONG — Cartesian product (orders × items × shipments)
@Query("SELECT o FROM OrderEntity o " +
       "JOIN FETCH o.items " +
       "JOIN FETCH o.shipments")
List<OrderEntity> findAllWithItemsAndShipments();

// ✅ CORRECT — Two queries via @EntityGraph + secondary repository call
// or split the fetch plan across two methods
@EntityGraph(attributePaths = "items")
List<OrderEntity> findWithItemsByStatus(OrderStatus status);
```

### `@BatchSize` for Lazy Collections You Will Touch

```java
@OneToMany(mappedBy = "order", fetch = FetchType.LAZY)
@BatchSize(size = 50)  // Loads 50 parents' children in one IN(...) query
private List<OrderItemEntity> items;
```

---

## Batch Processing — Beyond `flush/clear`

The basic flush/clear loop is in `SKILL.md`. Production-grade batch import needs more:

### Property Bundle (Boot 4)

```properties
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
spring.jpa.properties.hibernate.batch_versioned_data=true
# Disable in batch jobs to skip JDBC fetch-size negotiation
spring.jpa.properties.hibernate.jdbc.fetch_size=200
```

### Stateless Session for Pure Inserts (Hibernate 7)

```java
// 🟢 Bypass first-level cache & dirty checking entirely
try (StatelessSession ss = sessionFactory.openStatelessSession()) {
    Transaction tx = ss.beginTransaction();
    // Hibernate 7 batch DML — explicit since auto-batching is now off
    ss.insertMultiple(productEntities);
    tx.commit();
}
```

### Why Flush & Clear?

- **flush()** → Sends pending SQL to database
- **clear()** → Detaches entities, frees memory
- Without clear: `OutOfMemoryError` on large imports

---

## Bulk Update / Delete (JPQL & Criteria)

### JPQL Bulk Operations

```java
// Bulk update — single SQL statement
@Modifying(clearAutomatically = true)
@Query("UPDATE ProductEntity p SET p.price = p.price * :multiplier " +
       "WHERE p.category = :category")
int updatePricesByCategory(
    @Param("multiplier") BigDecimal multiplier,
    @Param("category") Category category
);

// Bulk delete — single SQL statement
@Modifying
@Query("DELETE FROM ProductEntity p WHERE p.discontinued = true")
int deleteDiscontinued();
```

### Criteria API Bulk Operations

```java
CriteriaBuilder cb = entityManager.getCriteriaBuilder();

CriteriaUpdate<ProductEntity> update = cb.createCriteriaUpdate(ProductEntity.class);
Root<ProductEntity> root = update.from(ProductEntity.class);
update.set(root.get("price"), cb.prod(root.get("price"), 1.1));
update.where(cb.equal(root.get("category"), category));
entityManager.createQuery(update).executeUpdate();
```

---

## Second-Level Cache Setup

### When to Use

| Scenario | Cache? |
|----------|--------|
| Reference data (countries, categories) | ✅ Yes |
| Configuration tables | ✅ Yes |
| Frequently read, rarely changed | ✅ Yes |
| Frequently updated data | ❌ No |
| User-specific data | ❌ No |
| Large entities | ❌ No |

### Configuration (EHCache 3 / JCache, Spring Boot 4)

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.hibernate.orm</groupId>
    <artifactId>hibernate-jcache</artifactId>
</dependency>
<dependency>
    <groupId>org.ehcache</groupId>
    <artifactId>ehcache</artifactId>
</dependency>
```

```properties
spring.jpa.properties.hibernate.cache.use_second_level_cache=true
spring.jpa.properties.hibernate.cache.region.factory_class=jcache
spring.jpa.properties.hibernate.javax.cache.provider=org.ehcache.jsr107.EhcacheCachingProvider
```

### Entity Configuration

```java
@Entity
@Cacheable
@org.hibernate.annotations.Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class CategoryEntity { /* static reference data */ }
```

### Cache Strategies

| Strategy | Use When |
|----------|----------|
| `READ_ONLY` | Never updated after creation |
| `READ_WRITE` | Updated occasionally, consistency important |
| `NONSTRICT_READ_WRITE` | Updated occasionally, stale reads acceptable |
| `TRANSACTIONAL` | JTA transactions, strict consistency |

---

## Query Cache

```properties
spring.jpa.properties.hibernate.cache.use_query_cache=true
```

```java
@QueryHints(@QueryHint(name = "org.hibernate.cacheable", value = "true"))
@Query("SELECT c FROM CategoryEntity c WHERE c.active = true")
List<CategoryEntity> findActiveCategories();
```

🟡 Combine **only** with second-level cache + immutable / rarely-changing data. Cache invalidation on writes is per-table.

---

## Connection Pooling (HikariCP 7)

```properties
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.idle-timeout=300000
spring.datasource.hikari.connection-timeout=30000
spring.datasource.hikari.max-lifetime=1800000
```

### Sizing Formula

```
Pool Size = (CPU cores × 2) + effective spindle count
```

For SSD: ~10–20 connections typically sufficient.

### 🟡 Sizing for Virtual Threads

Virtual threads can saturate the pool with thousands of waiters. Use a **bounded pool + queue timeout**, not an unbounded one — the pool is your back-pressure mechanism.

---

## DTO Projections

### 🟢 Default — Constructor Projection with `record`

```java
public record OrderDto(UUID id, BigDecimal total, OrderStatus status) {}

@Query("SELECT new com.example.dto.OrderDto(o.id, o.total, o.status) " +
       "FROM OrderEntity o WHERE o.customerId = :customerId")
List<OrderDto> findOrderSummaries(@Param("customerId") UUID customerId);
```

### Interface Projections (Ad-Hoc)

```java
public interface OrderSummary {
    UUID getId();
    BigDecimal getTotal();
    OrderStatus getStatus();
}

List<OrderSummary> findByCustomerId(UUID customerId);
```

---

## Pagination — Window/Keyset First

### 🟢 DEFAULT — `Window<T>` + Keyset Pagination (Spring Data JPA 4)

Keyset (cursor) pagination is now first-class. Use it for **all** list endpoints unless a total count is required.

```java
public interface OrderRepository extends JpaRepository<OrderEntity, UUID> {

    // Window<T> drives both the first page and subsequent pages
    Window<OrderEntity> findFirst50ByCustomerId(UUID customerId, ScrollPosition position);
}

// Service layer
@Transactional(readOnly = true)
public Window<Order> page(UUID customerId, ScrollPosition position) {
    Window<OrderEntity> entities = orderRepo.findFirst50ByCustomerId(customerId, position);
    return entities.map(OrderEntity::toDomain);
}

// Controller — first call uses keyset(), subsequent use the last position
Window<Order> first  = service.page(customerId, ScrollPosition.keyset());
Window<Order> next   = service.page(customerId, first.positionAtLast());
boolean hasNext      = first.hasNext();
```

### Walk Every Window with `WindowIterator`

```java
WindowIterator<OrderEntity> all = WindowIterator
    .of(pos -> orderRepo.findFirst1000ByCustomerId(customerId, pos))
    .startingAt(ScrollPosition.keyset());

all.forEachRemaining(entity -> /* process */);
```

### 🟡 ESCAPE HATCH — `Page<T>` Only When Total Count Is Required

```java
// Admin tables, exports — the COUNT query is unavoidable
Page<OrderEntity> page = repository.findByCustomerId(
    customerId,
    PageRequest.of(0, 50, Sort.by("createdAt").descending())
);
page.getTotalElements();  // ← This is what justifies Page over Window
```

### 🟡 `Slice<T>` Now Largely Superseded

`Slice<T>` (no count, but offset-based) is still supported. **Prefer `Window<T>`** unless you have a legacy reason to keep offsets.

---

## Virtual Threads

### Enable

```properties
spring.threads.virtual.enabled=true
```

This makes Tomcat request handling, `@Async`, scheduled tasks, and JPA repository calls execute on virtual threads.

### 🔴 BLOCKING — Driver Compatibility
**Why:** Older JDBC drivers `synchronized`-block around socket I/O, **pinning** the carrier thread (which defeats virtual threads entirely — performance can drop below platform threads). Verified-clean baseline (May 2026):

| Database | Minimum driver |
|----------|----------------|
| PostgreSQL | `org.postgresql:postgresql` ≥ **42.7** |
| MySQL | `com.mysql:mysql-connector-j` ≥ **9.0** |
| Microsoft SQL Server | `com.microsoft.sqlserver:mssql-jdbc` ≥ **12.x** |
| Oracle | `com.oracle.database.jdbc:ojdbc11` ≥ **23.4** |

### 🟡 Detect Pinning in Tests

```bash
-Djdk.tracePinnedThreads=full
```

Any pinned-thread stack trace from a JDBC call is a regression.

---

## Native Image / GraalVM

### 🔴 BLOCKING — Disable Open-In-View
**Why:** `spring.jpa.open-in-view=true` keeps the persistence context open for the whole HTTP request, requiring lazy proxies and reflective initialization that GraalVM cannot perform without runtime metadata.

```properties
spring.jpa.open-in-view=false
```

### 🟢 Native-Friendly Patterns

- **DTO projections (records) only** on the read path — no lazy proxies cross the controller boundary
- **Explicit `@EntityGraph`** — fetch plans known at build time
- **Drop `spring.jpa.database-platform`** — Hibernate auto-detects the dialect at AOT processing
- **Avoid runtime-only annotations** like custom `@Filter` or programmatic `Session` creation that bypass AOT

### Build with AOT

```bash
./mvnw -Pnative native:compile
```

Boot 4's AOT processor pre-computes Hibernate's metamodel, dialect, and entity graphs at build time — no reflection at runtime.

---

## Type-Safe Find Options (Hibernate 7)

Hibernate 7 replaces `Map<String, Object>` query hints with type-safe option objects.

### 🔴 WRONG — Untyped Hint Map

```java
Map<String, Object> hints = Map.of(
    "javax.persistence.fetchgraph", graph,
    "org.hibernate.readOnly", true
);
OrderEntity order = em.find(OrderEntity.class, id, hints);
```

### ✅ CORRECT — `FindOption` / `LockOption` / `RefreshOption`

```java
EntityGraph<OrderEntity> graph = em.createEntityGraph(OrderEntity.class);
graph.addAttributeNodes("customer", "items");

OrderEntity order = em.find(
    OrderEntity.class,
    id,
    new EntityGraphOption(graph, GraphSemantic.FETCH),
    ReadOnlyMode.READ_ONLY,
    new BatchSize(50)
);
```

Available option types: `EntityGraphOption`, `BatchSize`, `ReadOnlyMode`, `CacheStoreMode`, `CacheRetrieveMode`, `LockMode`, `Timeout`.

---

## Monitoring & Debugging

### Enable SQL Logging (Development Only)

```properties
# application.properties (DEV ONLY)
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
logging.level.org.hibernate.SQL=DEBUG
logging.level.org.hibernate.orm.jdbc.bind=TRACE
```

### Hibernate Statistics

```properties
spring.jpa.properties.hibernate.generate_statistics=true
logging.level.org.hibernate.stat=DEBUG
```

### Slow Query Logging

```properties
spring.jpa.properties.hibernate.session.events.log.LOG_QUERIES_SLOWER_THAN_MS=200
```
