# Entity Design Reference

## Minimum Entity Requirements

```java
@Entity                                    // Required
@Table(name = "users")                     // Explicit table name
public class UserEntity {

    @Id                                    // Required
    private UUID id;

    // ... fields

    protected UserEntity() {}              // Required: no-arg constructor
}
```

---

## Field Type Guidelines

### Nullable Columns

```java
// 🔴 WRONG - primitive can't be null
@Column(nullable = true)
private int quantity;  // Defaults to 0, not NULL

// ✅ CORRECT - wrapper handles null
@Column(nullable = true)
private Integer quantity;  // Can be NULL
```

### Enum Persistence

```java
// 🔴 WRONG - ORDINAL breaks on reorder
@Enumerated(EnumType.ORDINAL)
private OrderStatus status;  // Stored as 0, 1, 2...

// ✅ CORRECT - STRING is readable and safe
@Enumerated(EnumType.STRING)
@Column(nullable = false, length = 20)
private OrderStatus status;  // Stored as "PENDING", "SHIPPED"...
```

### Monetary Values

```java
// 🔴 WRONG - floating point precision issues
private double price;

// ✅ CORRECT - BigDecimal with precision
@Column(nullable = false, precision = 19, scale = 4)
private BigDecimal price;
```

### Timestamps

```java
@Column(name = "created_at", nullable = false, updatable = false)
private Instant createdAt;

@Column(name = "updated_at", nullable = false)
private Instant updatedAt;
```

---

## Lombok Configuration

### 🔴 BLOCKING - Never Use @Data

```java
// 🔴 WRONG - @Data generates broken equals/hashCode
@Data
@Entity
public class User { }

// ✅ CORRECT - Explicit annotations
@Entity
@Getter
@Setter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class UserEntity {
    // ...
}
```

### Recommended Setup

```java
@Entity
@Table(name = "users")
@Getter
@Setter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
public class UserEntity {

    @Id
    private UUID id;

    @EqualsAndHashCode.Include  // Only email in equals
    @Column(nullable = false, unique = true)
    private String email;

    @ManyToOne(fetch = FetchType.LAZY)
    @ToString.Exclude  // Prevent lazy loading in toString
    private DepartmentEntity department;
}
```

---

## Equality Implementation {#equality}

### Strategy 1: Business Key (Preferred)

Use when a natural unique field exists:

```java
@Entity
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
public class UserEntity {

    @Id
    private UUID id;

    @EqualsAndHashCode.Include
    @Column(nullable = false, unique = true)
    private String email;  // Immutable business key
}
```

### Strategy 2: ID + Constant HashCode

Use when no natural key exists but entity needs Set/Map storage:

```java
@Entity
public class OrderItemEntity {

    @Id
    private UUID id;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof OrderItemEntity other)) return false;
        // Transient entities (id == null) are only equal to themselves
        return id != null && Objects.equals(id, other.id);
    }

    @Override
    public int hashCode() {
        return 31;  // Constant - prevents rehashing after persist
    }
}
```

### Why Constant HashCode?

```java
Set<OrderItem> items = new HashSet<>();
OrderItem item = new OrderItem();  // id = null, hashCode = 31
items.add(item);                   // Stored in bucket for hash 31

repository.save(item);             // id = UUID, but hashCode STILL 31
items.contains(item);              // ✅ Found! Same bucket

// If hashCode used id:
// After save, hashCode changes → item "disappears" from HashSet!
```

---

## Immutable Entities

For read-only reference data (categories, statuses, countries):

```java
@Entity
@Immutable  // Hibernate skips dirty checks
@Table(name = "countries")
public class CountryEntity {

    @Id
    private String code;  // "FR", "US"

    private String name;

    // No setters - truly immutable
}
```

---

## Entity Naming

```java
// Explicit name for JPQL stability
@Entity(name = "User")  // JPQL: SELECT u FROM User u
@Table(name = "users")  // Database: users table
public class UserEntity {
    // Class can be renamed without breaking JPQL
}
```

---

## Domain Conversion Pattern

```java
@Entity
@Table(name = "orders")
public class OrderEntity {

    @Id
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    private CustomerEntity customer;

    private Instant createdAt;

    // Entity → Domain
    public Order toDomain() {
        return new Order(
            id,
            customer.toDomain(),
            createdAt
        );
    }

    // Domain → Entity
    public static OrderEntity fromDomain(Order order) {
        OrderEntity entity = new OrderEntity();
        entity.id = order.getId();
        entity.customer = CustomerEntity.fromDomain(order.getCustomer());
        entity.createdAt = order.getCreatedAt();
        return entity;
    }
}
```
