# Spring Data JPA Reference

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
// On entity
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

// In repository
@EntityGraph(value = "Order.details")
Optional<OrderEntity> findWithDetailsById(UUID id);
```

---

## Projections

### Interface Projection

```java
// Define projection
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

// Use in repository
List<OrderSummary> findSummariesByCustomerId(UUID customerId);
```

### Class Projection (DTO)

```java
// DTO record
public record OrderDto(UUID id, BigDecimal total, String customerName) {}

// Constructor expression
@Query("SELECT new com.example.dto.OrderDto(o.id, o.total, c.name) " +
       "FROM OrderEntity o JOIN o.customer c " +
       "WHERE o.status = :status")
List<OrderDto> findDtosByStatus(@Param("status") OrderStatus status);
```

### Dynamic Projection

```java
// Same method, different return types
<T> List<T> findByStatus(OrderStatus status, Class<T> type);

// Usage
List<OrderEntity> entities = repo.findByStatus(status, OrderEntity.class);
List<OrderSummary> summaries = repo.findByStatus(status, OrderSummary.class);
```

---

## Transactions

### Read-Only Transactions

```java
@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepository;

    // 🔴 BLOCKING - Always use readOnly=true for reads
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
@Modifying
@Query("UPDATE OrderEntity o SET o.status = :status WHERE o.id = :id")
int updateStatus(@Param("id") UUID id, @Param("status") OrderStatus status);

// With clear (recommended)
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

### Basic Pagination

```java
// Repository method
Page<OrderEntity> findByCustomerId(UUID customerId, Pageable pageable);

// Usage
Pageable pageable = PageRequest.of(0, 20, Sort.by("createdAt").descending());
Page<OrderEntity> page = repository.findByCustomerId(customerId, pageable);

// Page info
page.getContent();        // List<OrderEntity>
page.getTotalElements();  // Total count
page.getTotalPages();     // Total pages
page.hasNext();           // More pages?
```

### Slice (No Count Query)

```java
// When you don't need total count
Slice<OrderEntity> findSliceByCustomerId(UUID customerId, Pageable pageable);

// Faster than Page - no COUNT query
```

### Sort Only

```java
List<OrderEntity> findByStatus(OrderStatus status, Sort sort);

// Usage
List<OrderEntity> orders = repository.findByStatus(
    OrderStatus.PENDING,
    Sort.by("createdAt").descending().and(Sort.by("total").ascending())
);
```

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
