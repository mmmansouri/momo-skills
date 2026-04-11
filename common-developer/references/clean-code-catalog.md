# Clean Code Catalog

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Naming Conventions

### 🔴 BLOCKING - Names Must Reveal Intent

**Bad naming requires comments. Good naming is self-documenting.**

#### Classes

```java
// ❌ WRONG: Vague, cryptic names
class Data { }
class Manager { }
class Processor { }
class Helper { }

// ✅ CORRECT: Specific, descriptive nouns
class Order { }
class OrderService { }
class PaymentGateway { }
class EmailNotificationService { }
```

#### Methods

```java
// ❌ WRONG: Unclear what it does
public void process() { }
public void handle(Object data) { }
public int calc() { }

// ✅ CORRECT: Verbs that describe action
public void sendOrderConfirmation() { }
public Money calculateOrderTotal() { }
public boolean isEligibleForDiscount() { }
public Optional<Customer> findByEmail(String email) { }
```

#### Variables

```java
// ❌ WRONG: Abbreviations, single letters (except loops)
int d;  // days? distance? duration?
String pn;  // product name? phone number?
List<Order> o;

// ✅ CORRECT: Full words, searchable
int durationInDays;
String productName;
List<Order> pendingOrders;
```

### Buy Nature Naming Examples

```java
// DTO Naming
public record ItemCreationRequest(String name, Money price) { }
public record ItemUpdateRequest(UUID id, String name) { }
public record ItemRetrievalResponse(UUID id, String name, Money price) { }

// Service Naming
@Service
public class OrderService { }  // Domain service
@Service
public class StripePaymentGateway implements PaymentGateway { }  // Infrastructure service

// Repository Naming
public interface OrderRepository extends JpaRepository<Order, UUID> {
    List<Order> findByCustomerId(UUID customerId);  // Query method
    List<Order> findByStatusAndCreatedAtAfter(OrderStatus status, LocalDateTime date);
}

// Boolean Methods
public boolean isExpired() { }
public boolean hasDiscount() { }
public boolean canBeCancelled() { }
```

### TypeScript Naming

```typescript
// ❌ WRONG
let x;
let data;
function get() { }

// ✅ CORRECT
let selectedProductId: string;
let cartItems: CartItem[];
function fetchProducts(): Observable<Product[]> { }

// Signals
const products = signal<Product[]>([]);
const isLoading = signal<boolean>(false);
const selectedProduct = signal<Product | null>(null);

// Computed signals
const totalPrice = computed(() =>
  products().reduce((sum, p) => sum + p.price, 0)
);
```

---

## Function Design

### 🔴 BLOCKING - Functions Should Be Small

**Ideal:** < 20 lines
**Maximum:** 30 lines
**If longer:** Extract sub-functions

#### Single Responsibility

```java
// ❌ WRONG: Does multiple things
@Transactional
public void processOrder(UUID orderId) {
    // 1. Load order (database)
    Order order = orderRepository.findById(orderId)
        .orElseThrow(() -> new OrderNotFoundException(orderId));

    // 2. Validate inventory (business logic)
    for (OrderItem item : order.getItems()) {
        Product product = productRepository.findById(item.getProductId())
            .orElseThrow();
        if (product.getStock() < item.getQuantity()) {
            throw new InsufficientStockException(product);
        }
    }

    // 3. Process payment (external service)
    PaymentRequest paymentRequest = new PaymentRequest(
        order.getTotal(),
        order.getCustomer().getPaymentMethodId()
    );
    paymentGateway.charge(paymentRequest);

    // 4. Update inventory (database)
    for (OrderItem item : order.getItems()) {
        Product product = productRepository.findById(item.getProductId()).get();
        product.reduceStock(item.getQuantity());
        productRepository.save(product);
    }

    // 5. Send notification (external service)
    emailService.sendOrderConfirmation(order);

    // 6. Update order status (business logic)
    order.setStatus(OrderStatus.CONFIRMED);
    orderRepository.save(order);
}
```

```java
// ✅ CORRECT: Extract cohesive functions
@Transactional
public void processOrder(UUID orderId) {
    Order order = loadOrder(orderId);
    validateInventory(order);
    processPayment(order);
    reduceInventory(order);
    confirmOrder(order);
    notifyCustomer(order);
}

private Order loadOrder(UUID orderId) {
    return orderRepository.findById(orderId)
        .orElseThrow(() -> new OrderNotFoundException(orderId));
}

private void validateInventory(Order order) {
    inventoryService.validateAvailability(order.getItems());
}

private void processPayment(Order order) {
    paymentGateway.charge(buildPaymentRequest(order));
}

private void reduceInventory(Order order) {
    inventoryService.reduceStock(order.getItems());
}

private void confirmOrder(Order order) {
    order.confirm();
    orderRepository.save(order);
}

private void notifyCustomer(Order order) {
    notificationService.sendOrderConfirmation(order);
}
```

### Function Arguments

```java
// 🔴 BLOCKING: Max 3 arguments, ideally 0-2

// ❌ WRONG: Too many arguments
public Order createOrder(
    UUID customerId,
    List<UUID> productIds,
    List<Integer> quantities,
    String shippingAddress,
    String billingAddress,
    String paymentMethod
) { }

// ✅ CORRECT: Use parameter object
public Order createOrder(OrderCreationRequest request) { }

public record OrderCreationRequest(
    UUID customerId,
    List<OrderItemRequest> items,
    Address shippingAddress,
    Address billingAddress,
    PaymentMethod paymentMethod
) { }
```

### Avoid Flag Arguments

```java
// ❌ WRONG: Boolean flag changes behavior
public List<Product> getProducts(boolean includeOutOfStock) {
    if (includeOutOfStock) {
        return productRepository.findAll();
    } else {
        return productRepository.findByStockGreaterThan(0);
    }
}

// ✅ CORRECT: Separate methods
public List<Product> getAllProducts() {
    return productRepository.findAll();
}

public List<Product> getInStockProducts() {
    return productRepository.findByStockGreaterThan(0);
}
```

---

## Comments

### 🔴 BLOCKING - Comment WHY, Not WHAT

Code explains WHAT. Comments explain WHY.

```java
// ❌ WRONG: Comments that repeat code
// Set price to 100
price = 100;

// Loop through items
for (Item item : items) {
    // Add item price to total
    total += item.getPrice();
}

// ✅ CORRECT: Explain non-obvious decisions
// Compensates for browser timezone offset in Safari
adjustedDate = date.plusHours(clientTimezoneOffset);

// Cache expires after 5 minutes to balance freshness and performance
@Cacheable(ttl = 300)
public List<Product> getFeaturedProducts() { }

// Use pessimistic locking to prevent double-booking
@Lock(LockModeType.PESSIMISTIC_WRITE)
Optional<Appointment> findById(UUID id);
```

### When Comments Are Acceptable

```java
// ✅ GOOD: Legal/licensing information
/*
 * Copyright (c) 2025 Buy Nature
 * Licensed under MIT License
 */

// ✅ GOOD: TODO with Jira ticket
// TODO(BNAT-123): Implement bulk discount calculation

// ✅ GOOD: Warning about consequences
// WARNING: Changing this breaks backward compatibility with mobile app v1.x

// ✅ GOOD: Complex algorithm explanation
/**
 * Implements Luhn algorithm (mod 10) for credit card validation.
 * See: https://en.wikipedia.org/wiki/Luhn_algorithm
 */
public boolean isValidCreditCard(String number) { }
```

### When to Avoid Comments

```java
// ❌ WRONG: Commented-out code (use git instead)
// public void oldMethod() {
//     // old implementation
// }

// ❌ WRONG: Redundant JavaDoc
/**
 * Gets the name.
 * @return the name
 */
public String getName() {
    return name;
}

// ✅ CORRECT: Meaningful JavaDoc
/**
 * Retrieves active subscriptions that require renewal within the specified period.
 * Excludes cancelled and expired subscriptions.
 *
 * @param period The period from now to check for renewals
 * @return List of subscriptions requiring renewal, ordered by renewal date
 */
public List<Subscription> findSubscriptionsRequiringRenewal(Period period) { }
```

---

## Error Handling

### 🔴 BLOCKING - Use Exceptions, Not Error Codes

```java
// ❌ WRONG: Error codes
public int saveOrder(Order order) {
    if (order == null) {
        return -1;  // Error: null order
    }
    if (order.getItems().isEmpty()) {
        return -2;  // Error: empty items
    }
    orderRepository.save(order);
    return 0;  // Success
}

// Caller has to check error codes
int result = saveOrder(order);
if (result == -1) {
    // handle null
} else if (result == -2) {
    // handle empty
}
```

```java
// ✅ CORRECT: Exceptions with context
public Order saveOrder(Order order) {
    Objects.requireNonNull(order, "Order cannot be null");

    if (order.getItems().isEmpty()) {
        throw new EmptyOrderException("Order must contain at least one item");
    }

    return orderRepository.save(order);
}

// Caller uses try-catch
try {
    Order saved = saveOrder(order);
    return ResponseEntity.ok(saved);
} catch (EmptyOrderException e) {
    return ResponseEntity.badRequest().body(e.getMessage());
}
```

### Don't Return Null - Use Optional

```java
// ❌ WRONG: Null checks everywhere
public Customer findCustomerByEmail(String email) {
    Customer customer = customerRepository.findByEmail(email);
    return customer;  // Can be null
}

// Caller must remember to check
Customer customer = findCustomerByEmail("test@example.com");
if (customer != null) {  // Easy to forget
    customer.getName();
}
```

```java
// ✅ CORRECT: Optional makes null explicit
public Optional<Customer> findCustomerByEmail(String email) {
    return customerRepository.findByEmail(email);
}

// Caller forced to handle empty case
findCustomerByEmail("test@example.com")
    .ifPresentOrElse(
        customer -> System.out.println(customer.getName()),
        () -> System.out.println("Customer not found")
    );

// Or with default
Customer customer = findCustomerByEmail("test@example.com")
    .orElse(Customer.guest());
```

### Fail Fast

```java
// ✅ BEST PRACTICE: Validate at the boundary
@PostMapping("/orders")
public ResponseEntity<OrderRetrievalResponse> createOrder(
    @Valid @RequestBody OrderCreationRequest request  // @Valid = fail fast
) {
    Order order = orderService.createOrder(request);
    return ResponseEntity.ok(OrderRetrievalResponse.from(order));
}

public record OrderCreationRequest(
    @NotNull(message = "Customer ID is required")
    UUID customerId,

    @NotEmpty(message = "Order must contain at least one item")
    @Valid
    List<OrderItemRequest> items
) { }
```

---

## Code Smells to Avoid

### 🔴 BLOCKING - Magic Numbers/Strings

```java
// ❌ WRONG: Magic values
if (customer.getAge() > 18) {  // Why 18?
    applyDiscount(order, 0.15);  // Why 15%?
}

if (order.getStatus().equals("PENDING")) {  // Typo-prone
    processOrder(order);
}

// ✅ CORRECT: Named constants
private static final int ADULT_AGE = 18;
private static final BigDecimal ADULT_DISCOUNT_RATE = new BigDecimal("0.15");

if (customer.getAge() > ADULT_AGE) {
    applyDiscount(order, ADULT_DISCOUNT_RATE);
}

if (order.getStatus() == OrderStatus.PENDING) {  // Type-safe enum
    processOrder(order);
}
```

### Deep Nesting

```java
// ❌ WRONG: Deep nesting
public void processOrder(Order order) {
    if (order != null) {
        if (order.getCustomer() != null) {
            if (order.getItems().size() > 0) {
                if (order.getTotal().compareTo(MIN_ORDER_AMOUNT) >= 0) {
                    // Process order
                }
            }
        }
    }
}

// ✅ CORRECT: Guard clauses (early return)
public void processOrder(Order order) {
    if (order == null) {
        throw new IllegalArgumentException("Order cannot be null");
    }

    if (order.getCustomer() == null) {
        throw new InvalidOrderException("Order must have a customer");
    }

    if (order.getItems().isEmpty()) {
        throw new EmptyOrderException("Order must contain items");
    }

    if (order.getTotal().compareTo(MIN_ORDER_AMOUNT) < 0) {
        throw new MinimumOrderAmountException(MIN_ORDER_AMOUNT);
    }

    // Process order (no nesting)
    doProcessOrder(order);
}
```

### Dead Code

```java
// ❌ WRONG: Commented code (use git history)
public class OrderService {
    // public void oldCalculation() {
    //     // old logic
    // }

    public void newCalculation() {
        // new logic
    }

    // private void unusedMethod() {
    //     // never called
    // }
}

// ✅ CORRECT: Delete it
public class OrderService {
    public void newCalculation() {
        // new logic
    }
}
```

---

## TypeScript Specific Patterns

### Strict Null Checks

```typescript
// ✅ Enable strict mode in tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "strictNullChecks": true
  }
}

// ❌ WRONG: Unsafe nullable access
function getCustomerName(customer: Customer | null): string {
  return customer.name;  // Error: customer might be null
}

// ✅ CORRECT: Safe null handling
function getCustomerName(customer: Customer | null): string {
  return customer?.name ?? 'Guest';  // Optional chaining + nullish coalescing
}

// OR with guard
function getCustomerName(customer: Customer | null): string {
  if (customer === null) {
    return 'Guest';
  }
  return customer.name;
}
```

### Type Narrowing

```typescript
// ✅ Use type guards
function processPayment(payment: CreditCard | PayPal | Crypto) {
  if ('cardNumber' in payment) {
    // TypeScript knows it's CreditCard
    validateCardNumber(payment.cardNumber);
  } else if ('email' in payment) {
    // TypeScript knows it's PayPal
    validatePayPalEmail(payment.email);
  } else {
    // TypeScript knows it's Crypto
    validateWalletAddress(payment.walletAddress);
  }
}
```

---

## Buy Nature Specific Examples

### DTO Naming

```java
// ✅ CORRECT: Consistent naming pattern
public record ItemCreationRequest(
    @NotBlank String name,
    @NotNull @Positive BigDecimal price,
    String description
) { }

public record ItemUpdateRequest(
    @NotBlank String name,
    @Positive BigDecimal price  // Nullable = optional update
) { }

public record ItemRetrievalResponse(
    UUID id,
    String name,
    BigDecimal price,
    String description,
    LocalDateTime createdAt,
    LocalDateTime updatedAt
) {
    public static ItemRetrievalResponse from(Item item) {
        return new ItemRetrievalResponse(
            item.getId(),
            item.getName(),
            item.getPrice(),
            item.getDescription(),
            item.getCreatedAt(),
            item.getUpdatedAt()
        );
    }
}
```

---

## Quick Checklist

Before committing code:

- [ ] All names reveal intent (no abbreviations, no cryptic names)
- [ ] Functions are small (< 20 lines ideally)
- [ ] Functions do ONE thing
- [ ] Max 3 arguments (use parameter objects if needed)
- [ ] No magic numbers/strings (use constants/enums)
- [ ] Comments explain WHY, not WHAT
- [ ] No commented-out code (deleted)
- [ ] No deep nesting (guard clauses, early returns)
- [ ] Use Optional instead of null returns
- [ ] Exceptions for errors, not error codes
- [ ] TypeScript strict mode enabled
