# Spring Data JPA Reference

> Spring Data JPA 4.x on Spring Boot 4 / Spring Framework 7 / Hibernate 7 / Java 25.
> Repository patterns, projections, transactions, scrolling, specifications, auditing, HQL extensions.

---

## Table of Contents

1. [Repository Basics](#repository-basics)
2. [Query Methods](#query-methods)
3. [@EntityGraph](#entitygraph)
4. [Projections](#projections)
5. [Transactions](#transactions)
6. [Modifying Queries](#modifying-queries)
7. [Pagination & Sorting](#pagination--sorting)
8. [Window / ScrollPosition (Keyset Pagination)](#window--scrollposition-keyset-pagination)
9. [Specifications (Dynamic Queries)](#specifications-dynamic-queries)
10. [HQL JSON / XML Functions (Hibernate 7)](#hql-json--xml-functions-hibernate-7)
11. [QuerySpecification (Hibernate Incubating)](#queryspecification-hibernate-incubating)
12. [Auditing](#auditing)
13. [Hibernate Data Repositories — When (Not) to Use](#hibernate-data-repositories--when-not-to-use)

---

## Repository Basics

### Standard Repository

```java
public interface OrderRepository extends JpaRepository<OrderEntity, UUID> {

    // Derived query methods
    List<OrderEntity> findByStatus(OrderStatus status);
    Optional<OrderEntity> findByIdAndCustomerId(UUID id, UUID customerId);
    boolean existsByCustomerIdAndStatus(UUID customerId, OrderStatus status);

    // Count
    long countByStatus(OrderStatus status);
}
```

### Custom Repository

```java
// Interface
public interface OrderRepositoryCustom {
    List<Order> findOrdersWithComplexCriteria(OrderSearchCriteria criteria);
}

// Implementation (suffix must be "Impl")
@RequiredArgsConstructor
public class OrderRepositoryCustomImpl implements OrderRepositoryCustom {

    private final EntityManager entityManager;

    @Override
    public List<Order> findOrdersWithComplexCriteria(OrderSearchCriteria criteria) {
        // Custom implementation
    }
}

// Extend both
public interface OrderRepository
    extends JpaRepository<OrderEntity, UUID>, OrderRepositoryCustom {
}
```

---

## Query Methods

### Derived Queries (Simple Cases)

```java
// By field
List<Product> findByCategory(Category category);

// Multiple conditions
List<Product> findByCategoryAndPriceGreaterThan(Category cat, BigDecimal price);

// Ordering
List<Product> findByCategoryOrderByPriceDesc(Category category);

// Limiting
List<Product> findTop10ByCategoryOrderByPriceDesc(Category category);
Optional<Product> findFirstByCategory(Category category);

// Distinct
List<Product> findDistinctByCategory(Category category);
```

### @Query (Complex Cases)

```java
// JPQL
@Query("SELECT o FROM OrderEntity o WHERE o.customer.email = :email")
List<OrderEntity> findByCustomerEmail(@Param("email") String email);

// Native SQL
@Query(value = "SELECT * FROM orders WHERE status = ?1", nativeQuery = true)
List<OrderEntity> findByStatusNative(String status);

// With JOIN FETCH
@Query("SELECT o FROM OrderEntity o " +
       "JOIN FETCH o.customer " +
       "JOIN FETCH o.items " +
       "WHERE o.id = :id")
Optional<OrderEntity> findWithDetailsByIdQuery(@Param("id") UUID id);
```

---

## @EntityGraph

### Ad-hoc Graph (Preferred)

```java
@EntityGraph(attributePaths = {"customer"})
List<OrderEntity> findByStatus(OrderStatus status);

@EntityGraph(attributePaths = {"customer", "items", "items.product"})
Optional<OrderEntity> findWithDetailsByIdGraph(UUID id);
```

### Named Graph

```java
@Entity
@NamedEntityGraphs({
    @NamedEntityGraph(
        name = "Order.summary",
        attributeNodes = @NamedAttributeNode("customer")
    ),
    @NamedEntityGraph(
        name = "Order.details",
        attributeNodes = {
            @NamedAttributeNode("customer"),
            @NamedAttributeNode(value = "items", subgraph = "items-product")
        },
        subgraphs = @NamedSubgraph(
            name = "items-product",
            attributeNodes = @NamedAttributeNode("product")
        )
    )
})
public class OrderEntity { }

@EntityGraph(value = "Order.details")
Optional<OrderEntity> findWithDetailsById(UUID id);
```

---

## Projections

### 🟢 Class Projection — Java Record (Default)

Records are now the standard projection target (Jakarta Persistence 3.2 + Hibernate 7).

```java
public record OrderDto(UUID id, BigDecimal total, String customerName) {}

@Query("SELECT new com.example.dto.OrderDto(o.id, o.total, c.name) " +
       "FROM OrderEntity o JOIN o.customer c " +
       "WHERE o.status = :status")
List<OrderDto> findDtosByStatus(@Param("status") OrderStatus status);
```

### Interface Projection (Ad-Hoc)

```java
public interface OrderSummary {
    UUID getId();
    BigDecimal getTotal();
    OrderStatus getStatus();

    // Nested projection
    CustomerSummary getCustomer();

    interface CustomerSummary {
        String getName();
        String getEmail();
    }
}

List<OrderSummary> findSummariesByCustomerId(UUID customerId);
```

### Dynamic Projection

```java
// Same method, different return types
<T> List<T> findByStatus(OrderStatus status, Class<T> type);

// Usage
List<OrderEntity> entities = repo.findByStatus(status, OrderEntity.class);
List<OrderSummary> summaries = repo.findByStatus(status, OrderSummary.class);
List<OrderDto> dtos = repo.findByStatus(status, OrderDto.class);
```

---

## Transactions

### Read-Only Transactions

```java
@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepository;

    // 🔴 BLOCKING — Always use readOnly=true for reads
    @Transactional(readOnly = true)
    public List<Order> findAllByCustomer(UUID customerId) {
        return orderRepository.findByCustomerId(customerId)
            .stream()
            .map(OrderEntity::toDomain)
            .toList();
    }

    @Transactional  // Default: readOnly=false
    public Order create(Order order) {
        OrderEntity entity = OrderEntity.fromDomain(order);
        return orderRepository.save(entity).toDomain();
    }
}
```

### Why readOnly=true?

- Hibernate skips dirty checks
- Database may optimize (read replicas, no locks)
- Documents intent

---

## Modifying Queries

### Update

```java
@Modifying(clearAutomatically = true)
@Query("UPDATE OrderEntity o SET o.status = :status WHERE o.id = :id")
int updateStatus(@Param("id") UUID id, @Param("status") OrderStatus status);

@Modifying(clearAutomatically = true)
@Query("UPDATE ProductEntity p SET p.price = p.price * :factor")
int updateAllPrices(@Param("factor") BigDecimal factor);
```

### Delete

```java
@Modifying
@Query("DELETE FROM OrderItemEntity i WHERE i.order.id = :orderId")
int deleteByOrderId(@Param("orderId") UUID orderId);

// Derived delete
void deleteByStatus(OrderStatus status);
long deleteByCustomerId(UUID customerId);
```

---

## Pagination & Sorting

For large result sets prefer `Window<T>` (next section). `Page`/`Slice` remain for the cases below.

### `Page<T>` — When Total Count Is Required

```java
Page<OrderEntity> findByCustomerId(UUID customerId, Pageable pageable);

Pageable pageable = PageRequest.of(0, 20, Sort.by("createdAt").descending());
Page<OrderEntity> page = repository.findByCustomerId(customerId, pageable);

page.getContent();        // List<OrderEntity>
page.getTotalElements();  // Total count — the reason to choose Page
page.getTotalPages();
page.hasNext();
```

### Sort Only

```java
List<OrderEntity> findByStatus(OrderStatus status, Sort sort);

List<OrderEntity> orders = repository.findByStatus(
    OrderStatus.PENDING,
    Sort.by("createdAt").descending().and(Sort.by("total").ascending())
);
```

---

## Window / ScrollPosition (Keyset Pagination)

### 🟢 DEFAULT — Keyset for All List Endpoints

`Window<T>` + `ScrollPosition.keyset()` is the **default pagination primitive** in Spring Data JPA 4. It uses cursor-based SQL (`WHERE created_at > :cursor`) instead of `OFFSET`, scaling to arbitrarily deep pages without performance collapse and without "drift" under concurrent writes.

```java
public interface OrderRepository extends JpaRepository<OrderEntity, UUID> {

    // The ScrollPosition parameter drives both the first call and subsequent calls
    Window<OrderEntity> findFirst50ByCustomerIdOrderByCreatedAtDesc(
        UUID customerId,
        ScrollPosition position
    );
}

// First page
Window<OrderEntity> first = repo.findFirst50ByCustomerIdOrderByCreatedAtDesc(
    customerId,
    ScrollPosition.keyset()
);

// Next page
Window<OrderEntity> next = repo.findFirst50ByCustomerIdOrderByCreatedAtDesc(
    customerId,
    first.positionAtLast()
);

// Iterate the entire dataset in pages of 1000
WindowIterator<OrderEntity> walker = WindowIterator
    .of(pos -> repo.findFirst1000ByCustomerIdOrderByCreatedAtDesc(customerId, pos))
    .startingAt(ScrollPosition.keyset());

walker.forEachRemaining(o -> /* process */);
```

### Result Type — `Window<T>` Methods

| Method | Returns |
|--------|---------|
| `getContent()` | `List<T>` |
| `hasNext()` | Whether more rows exist beyond the cursor |
| `positionAtLast()` | `ScrollPosition` to pass to the next call |
| `positionAt(int index)` | Position of a specific element in the window |
| `map(Function)` | Project the window into a new type |

### Offset-Based Scrolling (`ScrollPosition.offset()`)

If you must keep offset semantics (e.g. exposing page numbers to a UI):

```java
Window<OrderEntity> page = repo.findByStatus(status, ScrollPosition.offset(100));
```

This is the same cost as `Page` without the count query.

---

## Specifications (Dynamic Queries)

```java
// Enable specifications
public interface OrderRepository
    extends JpaRepository<OrderEntity, UUID>,
            JpaSpecificationExecutor<OrderEntity> {
}

// Define specifications
public class OrderSpecs {

    public static Specification<OrderEntity> hasStatus(OrderStatus status) {
        return (root, query, cb) -> cb.equal(root.get("status"), status);
    }

    public static Specification<OrderEntity> createdAfter(Instant date) {
        return (root, query, cb) -> cb.greaterThan(root.get("createdAt"), date);
    }

    public static Specification<OrderEntity> totalGreaterThan(BigDecimal amount) {
        return (root, query, cb) -> cb.greaterThan(root.get("total"), amount);
    }
}

// Combine dynamically
Specification<OrderEntity> spec = Specification
    .where(OrderSpecs.hasStatus(OrderStatus.PENDING))
    .and(OrderSpecs.createdAfter(lastWeek))
    .and(OrderSpecs.totalGreaterThan(BigDecimal.valueOf(100)));

List<OrderEntity> orders = repository.findAll(spec);
```

---

## HQL JSON / XML Functions (Hibernate 7)

Hibernate 7 implements the SQL-standard `JSON_*` and `XML_*` function family in HQL and Criteria. Useful when columns store JSON (PostgreSQL `jsonb`, MySQL `JSON`, MSSQL/Oracle JSON types).

```java
// Read a JSON property as a typed value
@Query("""
    SELECT new com.example.dto.UserPref(u.id, json_value(u.preferences, '$.locale'))
    FROM UserEntity u
    WHERE json_value(u.preferences, '$.locale') = :locale
    """)
List<UserPref> findByLocale(@Param("locale") String locale);

// Build a JSON object as a result
@Query("""
    SELECT json_object('id': o.id, 'total': o.total, 'status': o.status)
    FROM OrderEntity o
    WHERE o.id = :id
    """)
String findOrderAsJson(@Param("id") UUID id);

// Aggregate as JSON array
@Query("""
    SELECT json_arrayagg(o.id)
    FROM OrderEntity o
    WHERE o.customer.id = :customerId
    """)
String findOrderIdsAsJsonArray(@Param("customerId") UUID customerId);
```

Set-returning helpers (`unnest`, `generate_series`, `json_table`) are also exposed in HQL — use for batch lookups against a parameterised list without a temp table.

---

## QuerySpecification (Hibernate Incubating)

Hibernate 7 introduces a fluent **`QuerySpecification`** + `Restriction` + `Range` builder as a parallel API to Spring Data `Specification`. **Status: incubating** — use `Specification` (above) as the default; reach for `QuerySpecification` only when you need composability that the Criteria-based `Specification` makes painful.

```java
// Hibernate-native fluent restriction (incubating)
QuerySpecification<OrderEntity> spec = QuerySpecification
    .where(OrderEntity.class)
    .restrict(Restriction.equal("status", OrderStatus.PENDING))
    .restrict(Restriction.range("total", Range.atLeast(BigDecimal.valueOf(100))));

List<OrderEntity> orders = session.createSelectionQuery(spec).getResultList();
```

Re-evaluate at every Hibernate minor release until it leaves incubating.

---

## Auditing

### Enable Auditing

```java
@Configuration
@EnableJpaAuditing
public class JpaConfig {

    @Bean
    public AuditorAware<String> auditorProvider() {
        return () -> Optional.ofNullable(SecurityContextHolder.getContext())
            .map(SecurityContext::getAuthentication)
            .map(Authentication::getName);
    }
}
```

### Audited Entity

```java
@Entity
@EntityListeners(AuditingEntityListener.class)
public class OrderEntity {

    @CreatedDate
    @Column(updatable = false)
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;

    @CreatedBy
    @Column(updatable = false)
    private String createdBy;

    @LastModifiedBy
    private String updatedBy;
}
```

### Base Audited Entity

```java
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
@Getter
public abstract class AuditedEntity {

    @CreatedDate
    @Column(updatable = false)
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;
}

@Entity
public class OrderEntity extends AuditedEntity {
    // Inherits audit fields
}
```

---

## Hibernate Data Repositories — When (Not) to Use

Hibernate 7 ships **Hibernate Data Repositories** — Jakarta Data-style repositories driven by an annotation processor that generates static implementations from `@Find`, `@HQL`, `@SQL` declarations. **Spring Data JPA remains the recommendation** in this skill.

### Spring Data JPA (default)

- Mature ecosystem (auditing, projections, specifications, scrolling, REST)
- Tight Spring Boot integration (`@EnableJpaAuditing`, transaction propagation, observability)
- Active issue tracking & migration guides

### Hibernate Data Repositories (mention)

- Static, compile-time-generated implementations (zero reflection — useful for native image)
- No Spring Data dependency (lighter for Hibernate-only stacks)
- Jakarta Data alignment

```java
// Example — Hibernate Data Repository (do not use as default)
public interface Orders {
    @Find
    Optional<OrderEntity> byId(UUID id);

    @HQL("FROM OrderEntity o WHERE o.customer.email = :email")
    List<OrderEntity> byCustomerEmail(String email);
}
// Implementation generated at compile time by hibernate-processor.
```

**Decision rule:** stay on Spring Data JPA unless you target a Hibernate-only / Jakarta-Data-only stack and need build-time codegen for AOT/native.
