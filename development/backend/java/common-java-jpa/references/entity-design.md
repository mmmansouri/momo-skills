# Entity Design Reference

> Hibernate 7 / Jakarta Persistence 3.2 / Java 25 idioms for designing JPA entities.

---

## Table of Contents

1. [Minimum Entity Requirements](#minimum-entity-requirements)
2. [Field Type Guidelines](#field-type-guidelines)
3. [Lombok Configuration](#lombok-configuration)
4. [Equality Implementation](#equality)
5. [Immutable Entities](#immutable-entities)
6. [Soft Delete (Hibernate 7)](#soft-delete-hibernate-7)
7. [Records as @Embeddable](#records-as-embeddable)
8. [@EmbeddedColumnNaming (Hibernate 7)](#embeddedcolumnnaming-hibernate-7)
9. [Entity Naming](#entity-naming)
10. [Domain Conversion Pattern](#domain-conversion-pattern)

---

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
// 🔴 WRONG — primitive can't be null
@Column(nullable = true)
private int quantity;  // Defaults to 0, not NULL

// ✅ CORRECT — wrapper handles null
@Column(nullable = true)
private Integer quantity;  // Can be NULL
```

### Enum Persistence

```java
// 🔴 WRONG — ORDINAL breaks on reorder
@Enumerated(EnumType.ORDINAL)
private OrderStatus status;  // Stored as 0, 1, 2...

// ✅ CORRECT — STRING is readable and safe
@Enumerated(EnumType.STRING)
@Column(nullable = false, length = 20)
private OrderStatus status;  // Stored as "PENDING", "SHIPPED"...
```

### Monetary Values

```java
// 🔴 WRONG — floating point precision issues
private double price;

// ✅ CORRECT — BigDecimal with precision
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

### 🔴 BLOCKING — Never Use @Data

```java
// 🔴 WRONG — @Data generates broken equals/hashCode
@Data
@Entity
public class User { }

// ✅ CORRECT — Explicit annotations
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
        return 31;  // Constant — prevents rehashing after persist
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

    // No setters — truly immutable
}
```

---

## Soft Delete (Hibernate 7)

### 🟢 Use the Built-in `@SoftDelete` Annotation

Hibernate 7 standardises soft-delete; do not roll your own `deleted` boolean filter.

```java
// 🟢 Boolean strategy (default) — adds a `deleted boolean` column, filters automatically
@Entity
@Table(name = "users")
@SoftDelete  // Default strategy: ACTIVE / DELETED boolean
public class UserEntity {

    @Id
    private UUID id;

    private String email;
}
```

```java
// 🟢 Timestamp strategy — adds a `deleted_at timestamp` column (NULL = alive)
@Entity
@Table(name = "orders")
@SoftDelete(strategy = SoftDeleteType.TIMESTAMP)
public class OrderEntity {

    @Id
    private UUID id;

    @Enumerated(EnumType.STRING)
    private OrderStatus status;
}
```

### What `@SoftDelete` does

- Adds an indicator column automatically (`deleted` / `deleted_at`)
- Translates `repository.delete(...)` into `UPDATE ... SET deleted_at = now()`
- Adds a `WHERE deleted_at IS NULL` filter to **every** generated query (including `JOIN FETCH`)
- Plays nicely with `@Filter` if you need an "include deleted" admin view

### 🟡 WARNING — `@SoftDelete` and unique constraints

```java
// 🔴 WRONG — soft-deleted email blocks new registration
@Column(unique = true)
private String email;

// ✅ CORRECT — partial unique index excluding soft-deleted rows (Postgres)
// CREATE UNIQUE INDEX users_email_active_idx ON users (email) WHERE deleted_at IS NULL;
```

---

## Records as @Embeddable

Jakarta Persistence 3.2 standardises Java `record` support for `@Embeddable`. Prefer records for value objects (Address, Money, Period, Coordinates).

### 🟢 Record Embeddable

```java
@Embeddable
public record Address(
    @Column(name = "street") String street,
    @Column(name = "city") String city,
    @Column(name = "zip_code") String zipCode,
    @Column(name = "country") String country
) {
    // Compact validation (Jakarta 3.2 calls the canonical constructor)
    public Address {
        Objects.requireNonNull(street);
        Objects.requireNonNull(country);
    }
}

@Entity
@Table(name = "users")
public class UserEntity {

    @Id
    private UUID id;

    @Embedded
    private Address address;
}
```

### 🟢 Money as a Record

```java
@Embeddable
public record Money(
    @Column(name = "amount", precision = 19, scale = 4) BigDecimal amount,
    @Column(name = "currency", length = 3) String currency
) {
    public Money {
        Objects.requireNonNull(amount);
        Objects.requireNonNull(currency);
    }

    public Money add(Money other) {
        if (!currency.equals(other.currency)) {
            throw new IllegalArgumentException("Currency mismatch");
        }
        return new Money(amount.add(other.amount), currency);
    }
}
```

### 🟡 Limitation — Records are immutable

`record`-based embeddables can't be mutated; replace the whole instance:

```java
// 🔴 WRONG — record is immutable
user.getAddress().setCity("Paris");  // No setter exists

// ✅ CORRECT — produce a new record and re-assign
user.setAddress(new Address(
    user.getAddress().street(),
    "Paris",
    user.getAddress().zipCode(),
    user.getAddress().country()
));
```

---

## @EmbeddedColumnNaming (Hibernate 7)

When the same `@Embeddable` is used twice in the same entity (e.g. `homeAddress` + `workAddress`), Hibernate 7 supports prefix patterns to avoid manual `@AttributeOverrides` clutter.

### 🔴 WRONG — Verbose `@AttributeOverrides`

```java
@Entity
public class UserEntity {

    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "street",  column = @Column(name = "home_street")),
        @AttributeOverride(name = "city",    column = @Column(name = "home_city")),
        @AttributeOverride(name = "zipCode", column = @Column(name = "home_zip_code")),
        @AttributeOverride(name = "country", column = @Column(name = "home_country"))
    })
    private Address homeAddress;

    @Embedded
    @AttributeOverrides({ /* same 4 lines, "work_" prefix */ })
    private Address workAddress;
}
```

### ✅ CORRECT — `@EmbeddedColumnNaming` pattern

```java
@Entity
public class UserEntity {

    @Embedded
    @EmbeddedColumnNaming("home_%")  // % = original column name
    private Address homeAddress;

    @Embedded
    @EmbeddedColumnNaming("work_%")
    private Address workAddress;
}
```

Result: `home_street`, `home_city`, …, `work_street`, `work_city`, …

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
