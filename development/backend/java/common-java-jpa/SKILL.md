---
name: common-java-jpa
description: >-
  JPA, Hibernate 7.x, and Spring Data JPA 4.x best practices for Spring Boot 4.x
  / Spring Framework 7.x projects on Java 25 (Jakarta Persistence 3.2).
  Use when: designing entities, mapping relationships (@ManyToOne/@OneToMany),
  implementing equals/hashCode, optimizing queries (N+1, JOIN FETCH, @EntityGraph),
  configuring batch processing, second-level cache, soft-delete, keyset pagination
  (Window/ScrollPosition), or using DTO projections. Triggers on any work involving
  @Entity, @Repository, EntityManager, or spring-data-jpa.
---

# JPA Developer Guide — Spring Boot 4 / Hibernate 7 / Java 25

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
>
> **Stack baseline (May 2026):**
> - Spring Boot **4.0+**, Spring Framework **7.0+**
> - Spring Data JPA **4.0**, Hibernate ORM **7.1+**
> - Jakarta Persistence **3.2** (Jakarta EE 11)
> - Java **25 LTS**, HikariCP **7.0**

---

## Pattern Selection Decision Tree

```
What are you doing?
│
├── DESIGNING AN ENTITY
│   ├── Mutable business data?              → @Entity + @Table + records-as-Embeddable for value objects
│   ├── Read-only reference data?           → @Immutable (countries, statuses, currencies)
│   ├── Need soft-delete?                   → @SoftDelete(strategy = TIMESTAMP) [Hibernate 7]
│   └── Audit fields (created/updatedAt)?   → @MappedSuperclass + AuditingEntityListener
│
├── MAPPING A RELATIONSHIP
│   ├── N→1 or 1→1?                         → @ManyToOne / @OneToOne + @JoinColumn (LAZY)
│   ├── 1→N bidirectional?                  → @OneToMany(mappedBy=..) + bidirectional helpers
│   ├── N↔M with extra attributes?          → Explicit Join Entity (default)
│   └── N↔M trivial link table?             → @ManyToMany (escape hatch only)
│
├── QUERYING
│   ├── Single entity by id?                → repository.findById(id)
│   ├── Read-only list/detail?              → DTO projection via record (constructor expression)
│   ├── Need related data eagerly?          → @EntityGraph(attributePaths=...)
│   ├── Dynamic filters?                    → Specifications (Spring Data) or QuerySpecification (Hibernate, incubating)
│   ├── Pagination on large dataset?        → Window<T> + ScrollPosition.keyset() [default]
│   ├── Pagination needing total count?     → Page<T> + Pageable (escape hatch)
│   └── Bulk update/delete?                 → @Modifying(clearAutomatically=true) + JPQL
│
├── PERSISTING
│   ├── Single insert/update?               → repository.save(entity)
│   ├── Bulk insert (>50 rows)?             → EntityManager + flush()/clear() per batch_size
│   └── Bulk DML on existing rows?          → StatelessSession.insertMultiple/updateMultiple [Hibernate 7]
│
└── OPTIMIZING
    ├── N+1 detected?                        → JOIN FETCH or @EntityGraph
    ├── Hot read-only entity?                → @Cacheable + @org.hibernate.annotations.Cache
    ├── High-throughput service?             → spring.threads.virtual.enabled=true (verify drivers)
    └── GraalVM native image target?         → spring.jpa.open-in-view=false + DTO projections only
```

---

## When Designing JPA Entities

📚 **When designing `@Entity` classes — annotations, ID strategies, enum/wrapper choices, value objects, audit fields, soft-delete, Lombok constraints → read [entity-design.md](references/entity-design.md).**

### 🔴 BLOCKING

- **Minimum requirements**: `@Entity` + `@Id` + no-arg constructor (public/protected)
  **Why:** Hibernate instantiates entities reflectively before populating fields; missing no-arg constructor throws `InstantiationException` at load time.
- **Use `@Enumerated(EnumType.STRING)`** — Never `ORDINAL`
  **Why:** `ORDINAL` stores the enum's array index. Reordering or inserting a value silently corrupts every persisted row — and the change passes type-checking.
- **Wrapper types for nullable columns** — `Integer`, `Boolean`, never primitives
  **Why:** Primitives can't hold `NULL`. Hibernate maps a `null` column to `0`/`false`, masking missing data as legitimate values.
- **Never use `@Data`** (Lombok) on entities
  **Why:** `@Data` generates `equals`/`hashCode` over **all** fields including lazy associations and generated IDs — triggers `LazyInitializationException` and breaks `HashSet` semantics across persist boundaries.

### 🟡 WARNING

- **Explicit `@Entity(name = "...")`** — Decouples JPQL from class refactoring
- **Explicit `@Table(name = "...")`** — Clear DB mapping, no implicit naming surprises

### 🟢 BEST PRACTICE

- `BigDecimal` for monetary values with `precision` / `scale`
- `@Immutable` for read-only reference data (skips dirty checks)
- `@SoftDelete(strategy = SoftDeleteType.TIMESTAMP)` for logical deletion (Hibernate 7+)
- Records as `@Embeddable` for value objects (Address, Money, Period)
- Lombok minimum: `@Getter`, `@Setter`, `@NoArgsConstructor(access = PROTECTED)`

---

## When Implementing equals/hashCode

📚 **When implementing `equals`/`hashCode` on entities — choosing a business key, handling generated IDs, avoiding lazy-association traps → read [entity-design.md](references/entity-design.md#equality).**

### 🔴 BLOCKING

- **Never base equality on a generated ID alone**
  **Why:** Before `persist()` the ID is `null`; after persist it changes. An entity added to a `HashSet` pre-persist gets re-bucketed and "disappears" once Hibernate assigns the ID.
- **Exclude associations** from equals
  **Why:** Touching a `@ManyToOne`/`@OneToMany` field in equals triggers lazy initialization and infinite recursion across bidirectional graphs.

### 🟢 Strategies

| Strategy | Use When | Implementation |
|----------|----------|----------------|
| **Business Key** | Natural unique field exists | Use immutable field (email, taxId, ISBN) |
| **ID + constant hashCode** | No natural key | Compare IDs, return constant `hashCode()` (e.g. `31`) |

```java
// 🔴 WRONG — ID null before persist, changes after
@Override
public boolean equals(Object o) {
    return Objects.equals(id, other.id);  // Fails in HashSet before save
}

// ✅ CORRECT — Business key
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (!(o instanceof User other)) return false;
    return Objects.equals(email, other.email);  // Immutable natural key
}
```

---

## When Mapping Relationships

📚 **When mapping `@ManyToOne`/`@OneToMany`/`@OneToOne`/`@ManyToMany`, choosing owning side, writing bidirectional helpers, deciding on cascade and join-entity vs `@ManyToMany` → read [relationships.md](references/relationships.md).**

### 🔴 BLOCKING

- **Always `FetchType.LAZY`** on every association
  **Why:** EAGER loads the graph on every query, including REST endpoints that only need 3 fields. Hibernate even warns this is its top performance anti-pattern.
- **Bidirectional helpers** for `@OneToMany`
  **Why:** JPA only persists the owning side. If you call `parent.getChildren().add(c)` without `c.setParent(parent)`, the FK column stays `null` and the next `flush()` corrupts the relationship.
- **JPA relationships, NOT raw UUID columns**
  **Why:** Raw `UUID customerId` defeats `JOIN FETCH`, `@EntityGraph`, cascading and lazy proxies — every join becomes a manual repository round-trip.

```java
// 🔴 WRONG — Raw UUID
@Column(name = "customer_id")
private UUID customerId;

// ✅ CORRECT — JPA relationship
@ManyToOne(fetch = FetchType.LAZY)
@JoinColumn(name = "customer_id", nullable = false)
private CustomerEntity customer;
```

### 🟡 WARNING

- **Avoid `CascadeType.REMOVE`** unless child lifecycle is truly coupled (true parent-child)
- **Default to an explicit Join Entity** for many-to-many — keeps `@ManyToMany` only as escape hatch when no extra attributes will ever be needed

### 🟢 Relationship Quick Reference

| Type | Owner Side | Inverse Side |
|------|-----------|--------------|
| `@ManyToOne` | Has `@JoinColumn` | — |
| `@OneToMany` | Uses `mappedBy` | Has `@JoinColumn` |
| `@OneToOne` | Has `@JoinColumn` | Uses `mappedBy` |
| `@ManyToMany` | Has `@JoinTable` | Uses `mappedBy` |

---

## When Choosing Inheritance Strategy

### 🟢 Decision Guide

| Strategy | Use When | Trade-off |
|----------|----------|-----------|
| **JOINED** | Normalized schema, FK constraints needed | Requires joins on every query |
| **SINGLE_TABLE** | Performance critical, few subtypes | Many nullable columns |
| **TABLE_PER_CLASS** | Avoid | Poor polymorphic queries (UNION ALL) |

```java
@Entity
@Inheritance(strategy = InheritanceType.JOINED)
public abstract class Payment { }

@Entity
public class CreditCardPayment extends Payment { }
```

For closed hierarchies, prefer **`sealed` Java types + pattern matching at the service layer** over polymorphic JPA inheritance.

---

## When Optimizing Performance

📚 **When fixing N+1 queries, configuring batch inserts/updates, enabling second-level cache, sizing pagination, or tuning Hibernate for throughput → read [performance.md](references/performance.md).**

### 🔴 BLOCKING — N+1 Query Problem
**Why:** A list endpoint that issues 1 + N queries scales linearly with payload size; under load it's the #1 source of database saturation in Spring services.

```java
// 🔴 WRONG — N+1 queries
List<Order> orders = orderRepo.findAll();
orders.forEach(o -> o.getCustomer().getName());  // 1 query per order!

// ✅ CORRECT — JOIN FETCH
@Query("SELECT o FROM Order o JOIN FETCH o.customer")
List<Order> findAllWithCustomer();

// ✅ CORRECT — EntityGraph
@EntityGraph(attributePaths = {"customer", "items"})
List<Order> findByStatus(OrderStatus status);
```

### 🔴 BLOCKING — Batch Processing
**Why:** Without `flush()`/`clear()` every persisted entity stays in the persistence context until commit; on imports of >10k rows you hit `OutOfMemoryError` and a multi-megabyte SQL flush at the end.

```properties
# application.properties
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
```

```java
for (int i = 0; i < entities.size(); i++) {
    em.persist(entities.get(i));
    if (i % 50 == 0) { em.flush(); em.clear(); }
}
```

### 🔴 BLOCKING — Pagination defaults to keyset
**Why:** `OFFSET`-based pagination scans every preceding row; performance collapses past page ~100 on large tables, and concurrent writes break page stability.

```java
// 🟢 PREFERRED — Keyset (cursor) pagination, Spring Data JPA 4
Window<Order> first = repo.findFirst50ByCustomerId(customerId, ScrollPosition.keyset());
Window<Order> next = repo.findFirst50ByCustomerId(customerId, first.positionAtLast());

// 🟡 ESCAPE HATCH — Page only when total count is required (admin tables, exports)
Page<Order> page = repo.findByCustomerId(customerId, PageRequest.of(0, 50));
```

### 🟢 Second-Level Cache (static reference data only)

```java
@Entity
@Cacheable
@org.hibernate.annotations.Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class Category { }
```

---

## When Targeting Virtual Threads or Native Image

📚 **When enabling virtual threads, verifying JDBC driver compatibility, building a GraalVM native image, or tuning `open-in-view` for either → read [performance.md](references/performance.md) (sections "Virtual Threads" and "Native Image / GraalVM").**

### 🔴 BLOCKING — Disable Open-In-View
**Why:** `spring.jpa.open-in-view=true` (Boot's legacy default) keeps the persistence context open for the entire HTTP request, preventing release of DB connections and pinning virtual threads on `synchronized` blocks. In native images it forces lazy proxies that GraalVM can't reflectively load.

```properties
spring.jpa.open-in-view=false
```

### 🟡 WARNING — Virtual Threads require modern JDBC drivers
**Why:** Older drivers use `synchronized` blocks around socket I/O, which **pin** the carrier thread (defeating the virtual-thread benefit). Verified-clean: PostgreSQL JDBC ≥ **42.7**, MySQL Connector/J ≥ **9.0**, Microsoft JDBC for SQL Server ≥ **12**.

```properties
spring.threads.virtual.enabled=true
```

### 🟢 BEST PRACTICE — Native image checklist
- DTO projections (records) only — avoid lazy proxies on the read path
- Explicit `@EntityGraph` — no implicit lazy loading at the controller boundary
- Drop `spring.jpa.database-platform` — let Hibernate auto-detect the dialect at build time

---

## When Using Spring Data JPA

📚 **When writing repositories, derived queries, `@Query`/JPQL, DTO projections, `@Transactional` boundaries, Specifications, or keyset pagination with `Window`/`ScrollPosition` → read [spring-data-jpa.md](references/spring-data-jpa.md).**

### 🔴 BLOCKING

- **`@Transactional(readOnly = true)`** for read operations
  **Why:** Skips Hibernate dirty checks (no automatic UPDATE on flush), enables read-replica routing, and documents intent. On read-heavy services this halves persistence-context overhead.
- **DTO projections** (records) for read-only queries — never full entities
  **Why:** Loading a 30-column entity to read 3 fields wastes bandwidth, defeats query caching and forces unnecessary lazy joins downstream.
- **Parameterized queries** — never string concatenation
  **Why:** Concatenation is SQL injection. Even with internal callers it bypasses Hibernate's prepared-statement caching, killing query plan reuse.

```java
// 🔴 WRONG — String concatenation (SQL injection risk)
@Query("SELECT u FROM User u WHERE u.name = '" + name + "'")

// ✅ CORRECT — Parameters + record projection
public record UserSummary(UUID id, String name, String email) {}

@Query("SELECT new com.example.UserSummary(u.id, u.name, u.email) " +
       "FROM User u WHERE u.name = :name")
List<UserSummary> findByName(@Param("name") String name);
```

### 🟢 BEST PRACTICE

- Interface projections for ad-hoc DTOs, **records for stable contracts**
- `@EntityGraph` on repository methods over `JOIN FETCH` for static fetch plans
- Derived query methods for simple cases, `@Query` for JPQL complexity
- `Window<T>` + `ScrollPosition` over `Page<T>` whenever total count is not needed

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] No `@Enumerated(EnumType.ORDINAL)`
- [ ] No `@Data` on entities
- [ ] No `FetchType.EAGER` on relationships
- [ ] No raw UUID fields instead of JPA relationships
- [ ] No string concatenation in queries
- [ ] `@Transactional(readOnly = true)` on read methods
- [ ] `spring.jpa.open-in-view=false` in production profiles
- [ ] DTO projections (records) for read-only flows

### 🟡 WARNING
- [ ] Bidirectional helpers for `@OneToMany`
- [ ] equals/hashCode not based on generated ID alone
- [ ] No `CascadeType.REMOVE` without clear parent-child lifecycle
- [ ] `Window<T>` + keyset for paginated lists (`Page<T>` only when total count required)
- [ ] No `spring.jpa.database-platform` (rely on auto-detection)
- [ ] Modern JDBC driver versions verified (PG ≥42.7, MySQL ≥9.0, MSSQL JDBC ≥12) for virtual threads

### 🟢 BEST PRACTICE
- [ ] `@EntityGraph` for complex fetching
- [ ] Batch configuration for bulk operations
- [ ] Second-level cache only for static data
- [ ] `@SoftDelete` instead of manual `deleted` flag where logical deletion is needed
- [ ] Records as `@Embeddable` for value objects

---

## Related Skills

- `common-java-developer` — Modern Java 25 patterns, records, sealed types, streams
- `common-java-testing` — `@DataJpaTest`, repository testing, Testcontainers
- `common-rest-api` — Entity ↔ DTO mapping patterns
