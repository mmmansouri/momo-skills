---
name: common-java-jpa
description: >-
  JPA, Hibernate 6.x, and Spring Data JPA 3.x best practices for Java 17+ projects.
  Use when: designing entities, mapping relationships (@ManyToOne/@OneToMany),
  implementing equals/hashCode, optimizing queries (N+1, JOIN FETCH, @EntityGraph),
  configuring batch processing, second-level cache, or using DTO projections.
  Assumes Spring Boot 3.x+ with Hibernate 6.x.
---

# JPA Developer Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## When Designing JPA Entities

📚 **References:** [entity-design.md](references/entity-design.md)

### 🔴 BLOCKING
- **Minimum requirements**: `@Entity` + `@Id` + no-arg constructor (public/protected)
- **Use `@Enumerated(EnumType.STRING)`** → Never ORDINAL (breaks on reorder)
- **Wrapper types for nullable columns** → `Integer`, `Boolean`, not primitives
- **Never use `@Data`** (Lombok) → Generates broken equals/hashCode for JPA

### 🟡 WARNING
- **Explicit `@Entity(name)`** → Decouples JPQL from class refactoring
- **Explicit `@Table(name)`** → Clear mapping, no surprises

### 🟢 BEST PRACTICE
- `BigDecimal` for monetary values (with precision/scale)
- `@Immutable` for read-only reference data (skips dirty checks)
- Lombok: `@Getter`, `@Setter`, `@NoArgsConstructor(access = PROTECTED)`

---

## When Implementing equals/hashCode

📚 **References:** [entity-design.md](references/entity-design.md#equality)

### 🔴 BLOCKING
- **Never base equality on generated ID alone** → Breaks before persist
- **Exclude associations** from equals → Prevents lazy loading & recursion

### 🟢 Strategies

| Strategy | Use When | Implementation |
|----------|----------|----------------|
| **Business Key** | Natural unique field exists | Use immutable field (email, taxId) |
| **ID + constant hashCode** | No natural key | Compare IDs, return constant `hashCode()` |

```java
// 🔴 WRONG - ID null before persist, changes after
@Override
public boolean equals(Object o) {
    return Objects.equals(id, other.id);  // Fails in HashSet before save
}

// ✅ CORRECT - Business key
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (!(o instanceof User other)) return false;
    return Objects.equals(email, other.email);  // Immutable natural key
}
```

---

## When Mapping Relationships

📚 **References:** [relationships.md](references/relationships.md)

### 🔴 BLOCKING
- **Always `FetchType.LAZY`** → Never eager by default
- **Bidirectional helpers** for `@OneToMany` → Sync both sides
- **JPA relationships, NOT raw UUIDs** → Enables proper fetching

```java
// 🔴 WRONG - Raw UUID
@Column(name = "customer_id")
private UUID customerId;

// ✅ CORRECT - JPA relationship
@ManyToOne(fetch = FetchType.LAZY)
@JoinColumn(name = "customer_id", nullable = false)
private CustomerEntity customer;
```

### 🟡 WARNING
- **Avoid `CascadeType.REMOVE`** unless child lifecycle truly coupled
- **Avoid `@ManyToMany`** → Prefer explicit join entity for control

### 🟢 Relationship Quick Reference

| Type | Owner Side | Inverse Side |
|------|-----------|--------------|
| `@ManyToOne` | Has `@JoinColumn` | - |
| `@OneToMany` | Uses `mappedBy` | Has `@JoinColumn` |
| `@OneToOne` | Has `@JoinColumn` | Uses `mappedBy` |

---

## When Choosing Inheritance Strategy

### 🟢 Decision Guide

| Strategy | Use When | Trade-off |
|----------|----------|-----------|
| **JOINED** | Normalized schema, constraints needed | Requires joins |
| **SINGLE_TABLE** | Performance critical, few subtypes | Nullable columns |
| **TABLE_PER_CLASS** | Avoid | Poor polymorphic queries |

```java
@Entity
@Inheritance(strategy = InheritanceType.JOINED)
public abstract class Payment { }

@Entity
public class CreditCardPayment extends Payment { }
```

---

## When Optimizing Performance

📚 **References:** [performance.md](references/performance.md)

### 🔴 N+1 Query Problem

```java
// 🔴 WRONG - N+1 queries
List<Order> orders = orderRepo.findAll();
orders.forEach(o -> o.getCustomer().getName());  // 1 query per order!

// ✅ CORRECT - JOIN FETCH
@Query("SELECT o FROM Order o JOIN FETCH o.customer")
List<Order> findAllWithCustomer();

// ✅ CORRECT - EntityGraph
@EntityGraph(attributePaths = {"customer", "items"})
List<Order> findByStatus(OrderStatus status);
```

### 🔴 Batch Processing

```properties
# application.properties
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
```

```java
// Flush & clear periodically in bulk operations
for (int i = 0; i < entities.size(); i++) {
    em.persist(entities.get(i));
    if (i % 50 == 0) {
        em.flush();
        em.clear();
    }
}
```

### 🟢 Second-Level Cache

```java
@Entity
@Cacheable
@org.hibernate.annotations.Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class Category { }  // Static reference data only!
```

---

## When Using Spring Data JPA

📚 **References:** [spring-data-jpa.md](references/spring-data-jpa.md)

### 🔴 BLOCKING
- **`@Transactional(readOnly = true)`** for read operations
- **DTO projections** for read-only queries → Not full entities
- **Parameterized queries** → Never string concatenation

```java
// 🔴 WRONG - String concatenation (SQL injection risk)
@Query("SELECT u FROM User u WHERE u.name = '" + name + "'")

// ✅ CORRECT - Parameters
@Query("SELECT u FROM User u WHERE u.name = :name")
List<User> findByName(@Param("name") String name);
```

### 🟢 BEST PRACTICE
- Interface projections for simple DTOs
- `@EntityGraph` on repository methods
- Derived query methods for simple queries
- `@Query` for complex JPQL

```java
// Interface projection - only selected columns
public interface OrderSummary {
    UUID getId();
    String getCustomerName();
    BigDecimal getTotal();
}

@Query("SELECT o.id as id, c.name as customerName, o.total as total " +
       "FROM Order o JOIN o.customer c WHERE o.status = :status")
List<OrderSummary> findSummariesByStatus(@Param("status") OrderStatus status);
```

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] No `@Enumerated(EnumType.ORDINAL)`
- [ ] No `@Data` on entities
- [ ] No `FetchType.EAGER` on relationships
- [ ] No raw UUID fields instead of JPA relationships
- [ ] No string concatenation in queries
- [ ] `@Transactional(readOnly = true)` on read methods

### 🟡 WARNING
- [ ] Bidirectional helpers for `@OneToMany`
- [ ] equals/hashCode not based on generated ID alone
- [ ] No `CascadeType.REMOVE` without clear parent-child lifecycle

### 🟢 BEST PRACTICE
- [ ] DTO projections for read-only operations
- [ ] `@EntityGraph` for complex fetching
- [ ] Batch configuration for bulk operations
- [ ] Second-level cache only for static data

---

## Related Skills

- `common-java-developer` — Modern Java patterns, records, streams
- `common-java-testing` — @DataJpaTest, repository testing
- `common-rest-api` — Entity-DTO mapping patterns
- `buy-nature-backend-coding-guide` — Buy Nature entity conventions
