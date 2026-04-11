# JPA Performance Reference

## N+1 Query Problem

### What Is It?

```java
// 1 query to fetch orders
List<OrderEntity> orders = orderRepository.findAll();

// N queries to fetch each customer
for (OrderEntity order : orders) {
    String name = order.getCustomer().getName();  // 1 query per order!
}
// Total: 1 + N queries
```

### Solution 1: JOIN FETCH

```java
@Query("SELECT o FROM OrderEntity o JOIN FETCH o.customer")
List<OrderEntity> findAllWithCustomer();

@Query("SELECT o FROM OrderEntity o " +
       "JOIN FETCH o.customer " +
       "JOIN FETCH o.items i " +
       "JOIN FETCH i.product")
List<OrderEntity> findAllWithDetails();
```

### Solution 2: @EntityGraph

```java
public interface OrderRepository extends JpaRepository<OrderEntity, UUID> {

    // Named entity graph
    @EntityGraph(value = "Order.withCustomer")
    List<OrderEntity> findByStatus(OrderStatus status);

    // Ad-hoc entity graph
    @EntityGraph(attributePaths = {"customer", "items"})
    Optional<OrderEntity> findWithDetailsById(UUID id);
}

// Define named graph on entity
@Entity
@NamedEntityGraph(
    name = "Order.withCustomer",
    attributeNodes = @NamedAttributeNode("customer")
)
public class OrderEntity { }
```

### 🔴 Anti-Pattern: FetchType.EAGER

```java
// 🔴 WRONG - Always loads, even when not needed
@ManyToOne(fetch = FetchType.EAGER)
private CustomerEntity customer;

// ✅ CORRECT - Load on demand with EntityGraph
@ManyToOne(fetch = FetchType.LAZY)
private CustomerEntity customer;
```

---

## Batch Processing

### Configuration

```properties
# application.properties
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
spring.jpa.properties.hibernate.batch_versioned_data=true
```

### Bulk Insert Pattern

```java
@Transactional
public void bulkInsert(List<Product> products) {
    int batchSize = 50;

    for (int i = 0; i < products.size(); i++) {
        ProductEntity entity = ProductEntity.fromDomain(products.get(i));
        entityManager.persist(entity);

        // Flush and clear every batch
        if (i > 0 && i % batchSize == 0) {
            entityManager.flush();
            entityManager.clear();
        }
    }

    // Final flush
    entityManager.flush();
    entityManager.clear();
}
```

### Why Flush & Clear?

- **flush()** → Sends pending SQL to database
- **clear()** → Detaches entities, frees memory
- Without clear: OutOfMemoryError on large imports

---

## Bulk Update/Delete (JPA 2.1+)

### JPQL Bulk Operations

```java
// Bulk update - single SQL statement
@Modifying
@Query("UPDATE ProductEntity p SET p.price = p.price * :multiplier " +
       "WHERE p.category = :category")
int updatePricesByCategory(
    @Param("multiplier") BigDecimal multiplier,
    @Param("category") Category category
);

// Bulk delete - single SQL statement
@Modifying
@Query("DELETE FROM ProductEntity p WHERE p.discontinued = true")
int deleteDiscontinued();
```

### Criteria API Bulk Operations

```java
CriteriaBuilder cb = entityManager.getCriteriaBuilder();

// Bulk update
CriteriaUpdate<Product> update = cb.createCriteriaUpdate(Product.class);
Root<Product> root = update.from(Product.class);
update.set(root.get("price"), cb.prod(root.get("price"), 1.1));
update.where(cb.equal(root.get("category"), category));
entityManager.createQuery(update).executeUpdate();
```

---

## Second-Level Cache

### When to Use

| Scenario | Cache? |
|----------|--------|
| Reference data (countries, categories) | ✅ Yes |
| Configuration tables | ✅ Yes |
| Frequently read, rarely changed | ✅ Yes |
| Frequently updated data | ❌ No |
| User-specific data | ❌ No |
| Large entities | ❌ No |

### Configuration (EHCache)

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
# application.properties
spring.jpa.properties.hibernate.cache.use_second_level_cache=true
spring.jpa.properties.hibernate.cache.region.factory_class=jcache
spring.jpa.properties.javax.cache.provider=org.ehcache.jsr107.EhcacheCachingProvider
```

### Entity Configuration

```java
@Entity
@Cacheable
@org.hibernate.annotations.Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class CategoryEntity {
    // Static reference data
}
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

### When to Use

- Same JPQL executed repeatedly with same parameters
- Results rarely change
- Combined with second-level cache

```properties
spring.jpa.properties.hibernate.cache.use_query_cache=true
```

```java
@QueryHints(@QueryHint(name = "org.hibernate.cacheable", value = "true"))
@Query("SELECT c FROM Category c WHERE c.active = true")
List<Category> findActiveCategories();
```

---

## Connection Pooling (HikariCP)

```properties
# application.properties
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

For SSD: ~10-20 connections typically sufficient.

---

## DTO Projections

### Why?

```java
// 🔴 WRONG - Loads entire entity for 3 fields
List<OrderEntity> orders = repository.findAll();
orders.stream().map(o -> new OrderDto(o.getId(), o.getTotal(), o.getStatus()));

// ✅ CORRECT - Only selects needed columns
@Query("SELECT new com.example.dto.OrderDto(o.id, o.total, o.status) " +
       "FROM OrderEntity o WHERE o.customerId = :customerId")
List<OrderDto> findOrderSummaries(@Param("customerId") UUID customerId);
```

### Interface Projections

```java
public interface OrderSummary {
    UUID getId();
    BigDecimal getTotal();
    OrderStatus getStatus();
}

List<OrderSummary> findByCustomerId(UUID customerId);
```

---

## Pagination

### Always Paginate Large Results

```java
// 🔴 WRONG - Loads all 1M records
List<OrderEntity> orders = repository.findAll();

// ✅ CORRECT - Paginated
Page<OrderEntity> orders = repository.findAll(PageRequest.of(0, 50));

// With sorting
Page<OrderEntity> orders = repository.findAll(
    PageRequest.of(0, 50, Sort.by("createdAt").descending())
);
```

### Keyset Pagination (Better for Large Datasets)

```java
@Query("SELECT o FROM OrderEntity o WHERE o.createdAt < :cursor " +
       "ORDER BY o.createdAt DESC")
List<OrderEntity> findNextPage(
    @Param("cursor") Instant cursor,
    Pageable pageable
);
```

---

## Monitoring & Debugging

### Enable SQL Logging (Development Only)

```properties
# application.properties (DEV ONLY)
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
logging.level.org.hibernate.SQL=DEBUG
logging.level.org.hibernate.type.descriptor.sql.BasicBinder=TRACE
```

### Hibernate Statistics

```properties
spring.jpa.properties.hibernate.generate_statistics=true
logging.level.org.hibernate.stat=DEBUG
```

### Detect N+1 in Tests

```java
@Test
void shouldNotCauseNPlusOne() {
    // Reset statistics
    statistics.clear();

    // Execute query
    List<Order> orders = orderService.findAllWithCustomers();

    // Assert single query
    assertThat(statistics.getQueryExecutionCount()).isEqualTo(1);
}
```
