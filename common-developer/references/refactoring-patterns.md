# Refactoring Patterns

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Refactoring is restructuring existing code without changing its external behavior.

---

## Extract Method

**When:** Function is too long or does multiple things
**Why:** Improves readability, enables reuse, makes testing easier

### Before

```java
@Transactional
public void processOrder(UUID orderId) {
    // Validation
    Order order = orderRepository.findById(orderId)
        .orElseThrow(() -> new OrderNotFoundException(orderId));

    if (order.getStatus() != OrderStatus.PENDING) {
        throw new InvalidOrderStateException("Only pending orders can be processed");
    }

    // Calculate total
    BigDecimal total = BigDecimal.ZERO;
    for (OrderItem item : order.getItems()) {
        BigDecimal itemTotal = item.getPrice().multiply(new BigDecimal(item.getQuantity()));
        if (item.getProduct().isDiscounted()) {
            BigDecimal discount = itemTotal.multiply(new BigDecimal("0.10"));
            itemTotal = itemTotal.subtract(discount);
        }
        total = total.add(itemTotal);
    }

    // Apply shipping
    if (total.compareTo(new BigDecimal("50")) < 0) {
        total = total.add(new BigDecimal("5.99"));
    }

    // Process payment
    PaymentRequest paymentRequest = new PaymentRequest();
    paymentRequest.setAmount(total);
    paymentRequest.setCustomerId(order.getCustomer().getId());
    paymentRequest.setPaymentMethod(order.getPaymentMethod());

    PaymentResult result = paymentGateway.charge(paymentRequest);

    if (result.isSuccess()) {
        order.setStatus(OrderStatus.CONFIRMED);
        order.setTotal(total);
        orderRepository.save(order);

        // Send email
        String emailBody = "Your order " + order.getId() + " has been confirmed. Total: $" + total;
        emailService.send(order.getCustomer().getEmail(), "Order Confirmed", emailBody);
    } else {
        throw new PaymentFailedException(result.getErrorMessage());
    }
}
```

### After

```java
@Transactional
public void processOrder(UUID orderId) {
    Order order = loadAndValidateOrder(orderId);
    Money total = calculateTotal(order);
    processPayment(order, total);
    confirmOrder(order, total);
    notifyCustomer(order);
}

private Order loadAndValidateOrder(UUID orderId) {
    Order order = orderRepository.findById(orderId)
        .orElseThrow(() -> new OrderNotFoundException(orderId));

    if (order.getStatus() != OrderStatus.PENDING) {
        throw new InvalidOrderStateException("Only pending orders can be processed");
    }

    return order;
}

private Money calculateTotal(Order order) {
    Money itemsTotal = calculateItemsTotal(order.getItems());
    Money shippingCost = calculateShippingCost(itemsTotal);
    return itemsTotal.add(shippingCost);
}

private Money calculateItemsTotal(List<OrderItem> items) {
    return items.stream()
        .map(this::calculateItemTotal)
        .reduce(Money.ZERO, Money::add);
}

private Money calculateItemTotal(OrderItem item) {
    Money itemTotal = item.getPrice().multiply(item.getQuantity());

    if (item.getProduct().isDiscounted()) {
        return itemTotal.applyDiscount(Percentage.of(10));
    }

    return itemTotal;
}

private Money calculateShippingCost(Money total) {
    return total.isLessThan(FREE_SHIPPING_THRESHOLD)
        ? STANDARD_SHIPPING_COST
        : Money.ZERO;
}

private void processPayment(Order order, Money amount) {
    PaymentRequest request = PaymentRequest.builder()
        .amount(amount)
        .customerId(order.getCustomer().getId())
        .paymentMethod(order.getPaymentMethod())
        .build();

    PaymentResult result = paymentGateway.charge(request);

    if (!result.isSuccess()) {
        throw new PaymentFailedException(result.getErrorMessage());
    }
}

private void confirmOrder(Order order, Money total) {
    order.confirm(total);
    orderRepository.save(order);
}

private void notifyCustomer(Order order) {
    notificationService.sendOrderConfirmation(order);
}
```

---

## Extract Class

**When:** Class has too many responsibilities
**Why:** Adheres to Single Responsibility Principle

### Before

```java
public class Order {
    private UUID id;
    private Customer customer;
    private List<OrderItem> items;

    // Shipping data (different responsibility)
    private String shippingStreet;
    private String shippingCity;
    private String shippingState;
    private String shippingZipCode;
    private String shippingCountry;

    // Billing data (different responsibility)
    private String billingStreet;
    private String billingCity;
    private String billingState;
    private String billingZipCode;
    private String billingCountry;

    // Methods dealing with shipping
    public String getFullShippingAddress() {
        return shippingStreet + ", " + shippingCity + ", " +
               shippingState + " " + shippingZipCode + ", " + shippingCountry;
    }

    public boolean isDomesticShipping() {
        return "USA".equals(shippingCountry);
    }

    // Methods dealing with billing
    public String getFullBillingAddress() {
        return billingStreet + ", " + billingCity + ", " +
               billingState + " " + billingZipCode + ", " + billingCountry;
    }
}
```

### After

```java
@Embeddable
public class Address {
    private String street;
    private String city;
    private String state;
    private String zipCode;
    private String country;

    public String getFullAddress() {
        return String.format("%s, %s, %s %s, %s",
            street, city, state, zipCode, country);
    }

    public boolean isDomestic() {
        return "USA".equals(country);
    }

    public boolean isSameAs(Address other) {
        return this.equals(other);
    }
}

@Entity
public class Order {
    @Id
    private UUID id;

    @ManyToOne
    private Customer customer;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderItem> items;

    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "street", column = @Column(name = "shipping_street")),
        @AttributeOverride(name = "city", column = @Column(name = "shipping_city")),
        @AttributeOverride(name = "state", column = @Column(name = "shipping_state")),
        @AttributeOverride(name = "zipCode", column = @Column(name = "shipping_zip_code")),
        @AttributeOverride(name = "country", column = @Column(name = "shipping_country"))
    })
    private Address shippingAddress;

    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "street", column = @Column(name = "billing_street")),
        @AttributeOverride(name = "city", column = @Column(name = "billing_city")),
        @AttributeOverride(name = "state", column = @Column(name = "billing_state")),
        @AttributeOverride(name = "zipCode", column = @Column(name = "billing_zip_code")),
        @AttributeOverride(name = "country", column = @Column(name = "billing_country"))
    })
    private Address billingAddress;

    public boolean isDomesticShipping() {
        return shippingAddress.isDomestic();
    }
}
```

---

## Replace Conditional with Polymorphism

**When:** Conditional logic based on object type
**Why:** Open/Closed Principle - add new types without modifying existing code

### Before

```java
public class ShippingCostCalculator {
    public BigDecimal calculateShippingCost(Order order) {
        String shippingMethod = order.getShippingMethod();

        if ("STANDARD".equals(shippingMethod)) {
            return new BigDecimal("5.99");
        } else if ("EXPRESS".equals(shippingMethod)) {
            if (order.getTotal().compareTo(new BigDecimal("100")) > 0) {
                return new BigDecimal("9.99");
            }
            return new BigDecimal("14.99");
        } else if ("OVERNIGHT".equals(shippingMethod)) {
            return new BigDecimal("24.99");
        } else if ("PICKUP".equals(shippingMethod)) {
            return BigDecimal.ZERO;
        }

        throw new UnsupportedShippingMethodException(shippingMethod);
    }
}
```

### After

```java
// Strategy interface
public interface ShippingStrategy {
    Money calculateCost(Order order);
    boolean supports(ShippingMethod method);
}

// Implementations
@Component
public class StandardShipping implements ShippingStrategy {
    private static final Money COST = Money.of(5.99);

    @Override
    public Money calculateCost(Order order) {
        return COST;
    }

    @Override
    public boolean supports(ShippingMethod method) {
        return method == ShippingMethod.STANDARD;
    }
}

@Component
public class ExpressShipping implements ShippingStrategy {
    private static final Money REGULAR_COST = Money.of(14.99);
    private static final Money DISCOUNTED_COST = Money.of(9.99);
    private static final Money DISCOUNT_THRESHOLD = Money.of(100);

    @Override
    public Money calculateCost(Order order) {
        return order.getTotal().isGreaterThan(DISCOUNT_THRESHOLD)
            ? DISCOUNTED_COST
            : REGULAR_COST;
    }

    @Override
    public boolean supports(ShippingMethod method) {
        return method == ShippingMethod.EXPRESS;
    }
}

@Component
public class OvernightShipping implements ShippingStrategy {
    private static final Money COST = Money.of(24.99);

    @Override
    public Money calculateCost(Order order) {
        return COST;
    }

    @Override
    public boolean supports(ShippingMethod method) {
        return method == ShippingMethod.OVERNIGHT;
    }
}

@Component
public class StorePickup implements ShippingStrategy {
    @Override
    public Money calculateCost(Order order) {
        return Money.ZERO;
    }

    @Override
    public boolean supports(ShippingMethod method) {
        return method == ShippingMethod.PICKUP;
    }
}

// Orchestrator
@Service
@RequiredArgsConstructor
public class ShippingCostCalculator {
    private final List<ShippingStrategy> strategies;

    public Money calculateShippingCost(Order order) {
        return strategies.stream()
            .filter(strategy -> strategy.supports(order.getShippingMethod()))
            .findFirst()
            .map(strategy -> strategy.calculateCost(order))
            .orElseThrow(() -> new UnsupportedShippingMethodException(order.getShippingMethod()));
    }
}
```

**Benefits:**
- Adding new shipping method = new class, no modifications
- Each strategy is testable in isolation
- Clear separation of concerns

---

## Introduce Parameter Object

**When:** Group of parameters frequently passed together
**Why:** Reduces parameter count, improves readability

### Before

```java
public Order createOrder(
    UUID customerId,
    String shippingStreet,
    String shippingCity,
    String shippingState,
    String shippingZipCode,
    String billingStreet,
    String billingCity,
    String billingState,
    String billingZipCode,
    String paymentMethod
) {
    // 10 parameters!
}
```

### After

```java
public record OrderCreationRequest(
    UUID customerId,
    Address shippingAddress,
    Address billingAddress,
    PaymentMethod paymentMethod
) { }

public Order createOrder(OrderCreationRequest request) {
    // Clean, single parameter
}
```

---

## Replace Magic Number with Constant

**When:** Literal values appear in code
**Why:** Makes code self-documenting, enables reuse

### Before

```java
public boolean isAdult(Customer customer) {
    return customer.getAge() >= 18;
}

public Money calculateDiscount(Money total) {
    if (total.isGreaterThan(Money.of(100))) {
        return total.multiply(0.10);
    }
    return Money.ZERO;
}

public boolean isExpired(Order order) {
    return order.getCreatedAt().isBefore(LocalDateTime.now().minusDays(30));
}
```

### After

```java
public class OrderConstants {
    public static final int ADULT_AGE = 18;
    public static final Money DISCOUNT_THRESHOLD = Money.of(100);
    public static final Percentage DISCOUNT_RATE = Percentage.of(10);
    public static final Duration ORDER_EXPIRY_DURATION = Duration.ofDays(30);
}

public boolean isAdult(Customer customer) {
    return customer.getAge() >= ADULT_AGE;
}

public Money calculateDiscount(Money total) {
    if (total.isGreaterThan(DISCOUNT_THRESHOLD)) {
        return total.multiply(DISCOUNT_RATE);
    }
    return Money.ZERO;
}

public boolean isExpired(Order order) {
    LocalDateTime expiryThreshold = LocalDateTime.now().minus(ORDER_EXPIRY_DURATION);
    return order.getCreatedAt().isBefore(expiryThreshold);
}
```

---

## Decompose Conditional

**When:** Complex if/else with lots of logic
**Why:** Improves readability

### Before

```java
public Money calculatePrice(Product product, int quantity, Customer customer) {
    Money basePrice = product.getPrice().multiply(quantity);

    if (customer.isPremium() && quantity > 10 &&
        product.getCategory() == Category.ORGANIC &&
        !product.isOnSale()) {
        return basePrice.multiply(0.85);
    }

    if (customer.isFirstTimeBuyer() && product.getPrice().isGreaterThan(Money.of(50))) {
        return basePrice.multiply(0.95);
    }

    return basePrice;
}
```

### After

```java
public Money calculatePrice(Product product, int quantity, Customer customer) {
    Money basePrice = product.getPrice().multiply(quantity);

    if (isEligibleForPremiumDiscount(product, quantity, customer)) {
        return applyPremiumDiscount(basePrice);
    }

    if (isEligibleForFirstTimeBuyerDiscount(product, customer)) {
        return applyFirstTimeBuyerDiscount(basePrice);
    }

    return basePrice;
}

private boolean isEligibleForPremiumDiscount(Product product, int quantity, Customer customer) {
    return customer.isPremium()
        && quantity > BULK_QUANTITY_THRESHOLD
        && product.getCategory() == Category.ORGANIC
        && !product.isOnSale();
}

private boolean isEligibleForFirstTimeBuyerDiscount(Product product, Customer customer) {
    return customer.isFirstTimeBuyer()
        && product.getPrice().isGreaterThan(FIRST_TIMER_THRESHOLD);
}

private Money applyPremiumDiscount(Money price) {
    return price.multiply(PREMIUM_DISCOUNT_RATE);
}

private Money applyFirstTimeBuyerDiscount(Money price) {
    return price.multiply(FIRST_TIMER_DISCOUNT_RATE);
}
```

---

## TypeScript Refactoring Examples

### Extract Function

```typescript
// Before
@Component({...})
export class ProductListComponent {
  products = signal<Product[]>([]);

  ngOnInit() {
    this.http.get<Product[]>('/api/products').subscribe({
      next: (data) => {
        const filtered = data.filter(p => p.stock > 0);
        const sorted = filtered.sort((a, b) => a.name.localeCompare(b.name));
        const mapped = sorted.map(p => ({
          ...p,
          displayPrice: new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
          }).format(p.price)
        }));
        this.products.set(mapped);
      }
    });
  }
}

// After
@Component({...})
export class ProductListComponent {
  private productService = inject(ProductService);
  products = signal<Product[]>([]);

  ngOnInit() {
    this.productService.getAvailableProducts()
      .subscribe(products => this.products.set(products));
  }
}

@Injectable()
export class ProductService {
  private http = inject(HttpClient);

  getAvailableProducts(): Observable<Product[]> {
    return this.http.get<Product[]>('/api/products').pipe(
      map(products => this.filterInStock(products)),
      map(products => this.sortByName(products)),
      map(products => this.addDisplayPrice(products))
    );
  }

  private filterInStock(products: Product[]): Product[] {
    return products.filter(p => p.stock > 0);
  }

  private sortByName(products: Product[]): Product[] {
    return [...products].sort((a, b) => a.name.localeCompare(b.name));
  }

  private addDisplayPrice(products: Product[]): Product[] {
    return products.map(p => ({
      ...p,
      displayPrice: this.formatPrice(p.price)
    }));
  }

  private formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  }
}
```

---

## Buy Nature Refactoring Checklist

Before committing refactored code:

- [ ] Tests still pass (refactoring doesn't change behavior)
- [ ] Extracted methods have clear names
- [ ] Magic numbers replaced with constants
- [ ] Complex conditionals decomposed
- [ ] Classes have single responsibility
- [ ] Parameter count reduced (use DTOs)
- [ ] Polymorphism used instead of type checks
- [ ] Code is more readable than before

---

## When to Refactor

**DO refactor when:**
- Adding a new feature (Boy Scout Rule: leave code cleaner)
- Code is hard to understand
- You see duplication (DRY violation)
- Function is too long (> 20 lines)
- Class is too large (> 300 lines)
- You need to copy-paste code

**DON'T refactor when:**
- Code works and is clear
- Just before a deadline (risk)
- Without tests (unsafe)
- External API/library code (not yours to change)

---

## Refactoring Safety Net

Always have tests before refactoring:

```java
// 1. Write tests for existing behavior
@Test
void whenCalculateShippingCost_withStandardShipping_shouldReturn599() {
    Order order = TestData.orderWithStandardShipping();
    Money cost = calculator.calculateShippingCost(order);
    assertThat(cost).isEqualTo(Money.of(5.99));
}

// 2. Refactor
// ... (refactor code)

// 3. Tests still pass = behavior unchanged ✓
```

**No tests? Write them first, then refactor.**
