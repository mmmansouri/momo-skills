# JPA Relationships Reference

> Mapping rules and helpers for `@ManyToOne`, `@OneToMany`, `@OneToOne`, `@ManyToMany` on Hibernate 7 / Jakarta Persistence 3.2.

---

## Table of Contents

1. [Relationship Overview](#relationship-overview)
2. [@ManyToOne (Most Common)](#manytoone-most-common)
3. [@OneToMany (Bidirectional)](#onetomany-bidirectional)
4. [@OneToOne](#onetoone)
5. [@ManyToMany — Default to Join Entity](#manytomany--default-to-join-entity)
6. [Cascade Types](#cascade-types)
7. [orphanRemoval](#orphanremoval)
8. [Fetch Strategies](#fetch-strategies)
9. [Batch Loading by ID (Hibernate 7)](#batch-loading-by-id-hibernate-7)
10. [Common Pitfalls](#common-pitfalls)

---

## Relationship Overview

| Annotation | Cardinality | Example |
|------------|-------------|---------|
| `@ManyToOne` | N:1 | Many Orders → One Customer |
| `@OneToMany` | 1:N | One Order → Many OrderItems |
| `@OneToOne` | 1:1 | One Customer → One User |
| `@ManyToMany` | N:M | Many Items ↔ Many Tags (escape hatch only) |

---

## @ManyToOne (Most Common)

```java
@Entity
@Table(name = "orders")
public class OrderEntity {

    @Id
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)  // Always LAZY
    @JoinColumn(name = "customer_id", nullable = false)
    private CustomerEntity customer;

    public Order toDomain() {
        return new Order(id, customer.toDomain());
    }
}
```

---

## @OneToMany (Bidirectional)

### Parent Side (Inverse)

```java
@Entity
@Table(name = "orders")
public class OrderEntity {

    @Id
    private UUID id;

    @OneToMany(
        mappedBy = "order",           // Inverse side
        cascade = CascadeType.ALL,    // Cascade persist/merge/remove
        orphanRemoval = true          // Delete orphaned children
    )
    private List<OrderItemEntity> items = new ArrayList<>();

    // 🔴 CRITICAL: Bidirectional helper methods
    public void addItem(OrderItemEntity item) {
        items.add(item);
        item.setOrder(this);
    }

    public void removeItem(OrderItemEntity item) {
        items.remove(item);
        item.setOrder(null);
    }
}
```

### Child Side (Owner)

```java
@Entity
@Table(name = "order_items")
public class OrderItemEntity {

    @Id
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "order_id", nullable = false)
    private OrderEntity order;  // Owns the relationship

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "product_id", nullable = false)
    private ProductEntity product;

    private int quantity;
}
```

---

## @OneToOne

### With Foreign Key

```java
@Entity
@Table(name = "customers")
public class CustomerEntity {

    @Id
    private UUID id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private UserEntity user;
}
```

### With Shared Primary Key

```java
@Entity
@Table(name = "customer_profiles")
public class CustomerProfileEntity {

    @Id
    private UUID id;  // Same as customer.id

    @OneToOne(fetch = FetchType.LAZY)
    @MapsId  // Share primary key with Customer
    @JoinColumn(name = "id")
    private CustomerEntity customer;
}
```

---

## @ManyToMany — Default to Join Entity

### 🟢 DEFAULT — Explicit Join Entity

Use an explicit join entity in **all** new code. It scales without rework when (not if) you need extra attributes (audit columns, status flags, ordering, soft-delete).

```java
@Entity
@Table(name = "item_tags")
public class ItemTagEntity {

    @EmbeddedId
    private ItemTagId id;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("itemId")
    private ItemEntity item;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("tagId")
    private TagEntity tag;

    private Instant addedAt;  // Extra attribute — easy to add
    private String addedBy;
}

@Embeddable
public record ItemTagId(UUID itemId, UUID tagId) implements Serializable {}
```

### 🟡 ESCAPE HATCH — Plain `@ManyToMany`

<details>
<summary>Only when the link will <strong>never</strong> carry extra data (e.g. immutable taxonomy)</summary>

```java
@Entity
public class ItemEntity {

    @ManyToMany
    @JoinTable(
        name = "item_tags",
        joinColumns = @JoinColumn(name = "item_id"),
        inverseJoinColumns = @JoinColumn(name = "tag_id")
    )
    private Set<TagEntity> tags = new HashSet<>();

    // Helper methods still required
    public void addTag(TagEntity tag) {
        tags.add(tag);
        tag.getItems().add(this);
    }
}
```

**Why this is the escape hatch, not the default:** migrating from `@ManyToMany` to a join entity requires a schema migration and rewriting every query that traverses the link. Starting with a join entity costs ~5 extra lines and zero migration debt.
</details>

---

## Cascade Types

| Type | Effect | Use When |
|------|--------|----------|
| `PERSIST` | Save children when parent saved | Parent creates children |
| `MERGE` | Update children when parent updated | Parent owns children |
| `REMOVE` | Delete children when parent deleted | True parent-child (rarely!) |
| `ALL` | All above + REFRESH + DETACH | Tight lifecycle coupling |

### 🟡 WARNING: CascadeType.REMOVE

```java
// 🟡 DANGER — Use only for true parent-child
@OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
private List<OrderItemEntity> items;  // OK — items belong to order

// 🔴 WRONG — Customer exists independently
@ManyToOne(cascade = CascadeType.REMOVE)
private CustomerEntity customer;  // Deleting order deletes customer!
```

---

## orphanRemoval

```java
@OneToMany(mappedBy = "order", orphanRemoval = true)
private List<OrderItemEntity> items;

// Usage:
order.getItems().remove(0);  // Item automatically deleted from DB
order.getItems().clear();    // All items deleted
```

---

## Fetch Strategies

### Default: Always LAZY

```java
@ManyToOne(fetch = FetchType.LAZY)   // Load on access
@OneToMany(fetch = FetchType.LAZY)   // Load on access (default)
@OneToOne(fetch = FetchType.LAZY)    // Load on access
```

### When You Need Eager: Use @EntityGraph

```java
public interface OrderRepository extends JpaRepository<OrderEntity, UUID> {

    // Fetch customer eagerly for this query only
    @EntityGraph(attributePaths = {"customer"})
    Optional<OrderEntity> findWithCustomerById(UUID id);

    // Fetch customer AND items
    @EntityGraph(attributePaths = {"customer", "items", "items.product"})
    Optional<OrderEntity> findWithDetailsById(UUID id);
}
```

---

## Batch Loading by ID (Hibernate 7)

Hibernate 7 introduces `findMultiple` / `getMultiple` for efficient by-ID batch fetches — replaces the N+1 anti-pattern of looping `findById`.

### 🟢 Session.findMultiple (managed entities)

```java
@Service
@RequiredArgsConstructor
public class OrderLookupService {

    private final EntityManager em;

    @Transactional(readOnly = true)
    public List<Order> findAll(List<UUID> ids) {
        Session session = em.unwrap(Session.class);
        // Single SQL: SELECT ... FROM orders WHERE id IN (?, ?, ?, ...)
        return session.findMultiple(OrderEntity.class, ids).stream()
            .map(OrderEntity::toDomain)
            .toList();
    }
}
```

### 🟢 StatelessSession.getMultiple (no first-level cache)

For high-volume bulk reads where the persistence context overhead is wasteful:

```java
try (StatelessSession ss = sessionFactory.openStatelessSession()) {
    List<OrderEntity> orders = ss.getMultiple(OrderEntity.class, ids);
    // No dirty checking, no L1 cache, no cascade — pure read
}
```

**Note (Hibernate 7 change):** `StatelessSession` now interacts with the **L2 cache by default**, but **automatic JDBC batching is disabled** — call `insertMultiple` / `updateMultiple` / `deleteMultiple` explicitly for batch DML.

---

## Common Pitfalls

### Updating Only One Side

```java
// 🔴 WRONG — Only updates one side
order.getItems().add(newItem);
// newItem.order is still null!

// ✅ CORRECT — Use helper method
order.addItem(newItem);  // Sets both sides
```

### LazyInitializationException

```java
// 🔴 WRONG — Access lazy relation outside transaction
Order order = orderService.findById(id);
order.getItems().size();  // LazyInitializationException!

// ✅ CORRECT — Load within transaction using EntityGraph
@Transactional(readOnly = true)
public Order findWithItems(UUID id) {
    return orderRepository.findWithItemsById(id)
        .map(OrderEntity::toDomain)
        .orElseThrow();
}
```

### N+1 Query Problem

```java
// 🔴 WRONG — N+1 queries
List<Order> orders = orderRepo.findAll();  // 1 query
orders.forEach(o ->
    o.getCustomer().getName()              // N queries!
);

// ✅ CORRECT — JOIN FETCH
@Query("SELECT o FROM OrderEntity o JOIN FETCH o.customer")
List<OrderEntity> findAllWithCustomer();   // 1 query
```
