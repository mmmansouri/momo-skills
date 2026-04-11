# Design Patterns Catalog

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Gang of Four (GoF) patterns with modern Java/TypeScript examples from the Buy Nature domain.

---

## Creational Patterns

### Factory Pattern

**Purpose:** Create objects without specifying exact class
**Use When:** Object creation logic is complex or varies based on context

#### Buy Nature Example: Payment Method Factory

```java
// Factory interface
public interface PaymentMethodFactory {
    PaymentMethod create(PaymentMethodType type, PaymentDetails details);
}

// Concrete factory
@Component
public class DefaultPaymentMethodFactory implements PaymentMethodFactory {

    @Override
    public PaymentMethod create(PaymentMethodType type, PaymentDetails details) {
        return switch (type) {
            case CREDIT_CARD -> new CreditCardPayment(
                details.getCardNumber(),
                details.getExpiryDate(),
                details.getCvv()
            );
            case PAYPAL -> new PayPalPayment(
                details.getEmail(),
                details.getPayPalToken()
            );
            case CRYPTO -> new CryptoPayment(
                details.getWalletAddress(),
                details.getCryptoCurrency()
            );
        };
    }
}

// Usage
@Service
@RequiredArgsConstructor
public class PaymentService {
    private final PaymentMethodFactory factory;

    public PaymentResult processPayment(PaymentRequest request) {
        PaymentMethod method = factory.create(
            request.getType(),
            request.getDetails()
        );

        return method.charge(request.getAmount());
    }
}
```

#### TypeScript Example

```typescript
interface Product {
  id: string;
  name: string;
  price: number;
}

class PhysicalProduct implements Product {
  constructor(
    public id: string,
    public name: string,
    public price: number,
    public weight: number
  ) {}
}

class DigitalProduct implements Product {
  constructor(
    public id: string,
    public name: string,
    public price: number,
    public downloadUrl: string
  ) {}
}

// Factory
class ProductFactory {
  static create(type: 'physical' | 'digital', data: any): Product {
    switch (type) {
      case 'physical':
        return new PhysicalProduct(
          data.id,
          data.name,
          data.price,
          data.weight
        );
      case 'digital':
        return new DigitalProduct(
          data.id,
          data.name,
          data.price,
          data.downloadUrl
        );
    }
  }
}
```

---

### Builder Pattern

**Purpose:** Construct complex objects step by step
**Use When:** Object has many optional parameters or complex construction

#### Buy Nature Example: Order Builder

```java
// Builder for Order
public class Order {
    private UUID id;
    private Customer customer;
    private List<OrderItem> items;
    private Address shippingAddress;
    private Address billingAddress;
    private ShippingMethod shippingMethod;
    private PaymentMethod paymentMethod;
    private OrderStatus status;

    private Order() { }  // Private constructor

    public static OrderBuilder builder() {
        return new OrderBuilder();
    }

    public static class OrderBuilder {
        private final Order order = new Order();

        public OrderBuilder id(UUID id) {
            order.id = id;
            return this;
        }

        public OrderBuilder customer(Customer customer) {
            order.customer = customer;
            return this;
        }

        public OrderBuilder items(List<OrderItem> items) {
            order.items = new ArrayList<>(items);
            return this;
        }

        public OrderBuilder addItem(OrderItem item) {
            if (order.items == null) {
                order.items = new ArrayList<>();
            }
            order.items.add(item);
            return this;
        }

        public OrderBuilder shippingAddress(Address address) {
            order.shippingAddress = address;
            return this;
        }

        public OrderBuilder billingAddress(Address address) {
            order.billingAddress = address;
            return this;
        }

        public OrderBuilder useSameAddressForBilling() {
            order.billingAddress = order.shippingAddress;
            return this;
        }

        public OrderBuilder shippingMethod(ShippingMethod method) {
            order.shippingMethod = method;
            return this;
        }

        public OrderBuilder paymentMethod(PaymentMethod method) {
            order.paymentMethod = method;
            return this;
        }

        public OrderBuilder status(OrderStatus status) {
            order.status = status;
            return this;
        }

        public Order build() {
            // Validation
            Objects.requireNonNull(order.customer, "Customer is required");
            if (order.items == null || order.items.isEmpty()) {
                throw new IllegalStateException("Order must have items");
            }
            Objects.requireNonNull(order.shippingAddress, "Shipping address is required");

            // Defaults
            if (order.billingAddress == null) {
                order.billingAddress = order.shippingAddress;
            }
            if (order.status == null) {
                order.status = OrderStatus.PENDING;
            }
            if (order.id == null) {
                order.id = UUID.randomUUID();
            }

            return order;
        }
    }
}

// Usage
Order order = Order.builder()
    .customer(customer)
    .addItem(new OrderItem(product1, 2))
    .addItem(new OrderItem(product2, 1))
    .shippingAddress(address)
    .useSameAddressForBilling()
    .shippingMethod(ShippingMethod.STANDARD)
    .paymentMethod(PaymentMethod.CREDIT_CARD)
    .build();
```

---

## Behavioral Patterns

### Strategy Pattern

**Purpose:** Define family of algorithms, make them interchangeable
**Use When:** Multiple ways to perform same operation, chosen at runtime

#### Buy Nature Example: Discount Strategies

```java
// Strategy interface
public interface DiscountStrategy {
    Money applyDiscount(Money originalPrice, DiscountContext context);
    boolean isApplicable(DiscountContext context);
}

// Context
public record DiscountContext(
    Customer customer,
    Product product,
    int quantity,
    LocalDate purchaseDate
) { }

// Concrete strategies
@Component
public class BulkDiscountStrategy implements DiscountStrategy {
    private static final int MIN_QUANTITY = 10;
    private static final Percentage DISCOUNT_RATE = Percentage.of(15);

    @Override
    public Money applyDiscount(Money originalPrice, DiscountContext context) {
        return originalPrice.multiply(1 - DISCOUNT_RATE.value());
    }

    @Override
    public boolean isApplicable(DiscountContext context) {
        return context.quantity() >= MIN_QUANTITY;
    }
}

@Component
public class SeasonalDiscountStrategy implements DiscountStrategy {
    private static final Percentage DISCOUNT_RATE = Percentage.of(20);

    @Override
    public Money applyDiscount(Money originalPrice, DiscountContext context) {
        return originalPrice.multiply(1 - DISCOUNT_RATE.value());
    }

    @Override
    public boolean isApplicable(DiscountContext context) {
        Month month = context.purchaseDate().getMonth();
        return month == Month.NOVEMBER || month == Month.DECEMBER;
    }
}

@Component
public class FirstTimeBuyerDiscountStrategy implements DiscountStrategy {
    private static final Percentage DISCOUNT_RATE = Percentage.of(10);

    @Override
    public Money applyDiscount(Money originalPrice, DiscountContext context) {
        return originalPrice.multiply(1 - DISCOUNT_RATE.value());
    }

    @Override
    public boolean isApplicable(DiscountContext context) {
        return context.customer().isFirstTimeBuyer();
    }
}

// Service using strategies
@Service
@RequiredArgsConstructor
public class PricingService {
    private final List<DiscountStrategy> discountStrategies;

    public Money calculateFinalPrice(Product product, int quantity, Customer customer) {
        Money basePrice = product.getPrice().multiply(quantity);

        DiscountContext context = new DiscountContext(
            customer,
            product,
            quantity,
            LocalDate.now()
        );

        // Apply first applicable discount
        return discountStrategies.stream()
            .filter(strategy -> strategy.isApplicable(context))
            .findFirst()
            .map(strategy -> strategy.applyDiscount(basePrice, context))
            .orElse(basePrice);
    }
}
```

---

### Observer Pattern

**Purpose:** Notify multiple objects when state changes
**Use When:** One-to-many dependency, event-driven architecture

#### Buy Nature Example: Order Events

```java
// Event
public record OrderConfirmedEvent(
    UUID orderId,
    Customer customer,
    Money total,
    LocalDateTime confirmedAt
) { }

// Observers (listeners)
@Component
@RequiredArgsConstructor
public class EmailNotificationListener {
    private final EmailService emailService;

    @EventListener
    public void onOrderConfirmed(OrderConfirmedEvent event) {
        emailService.sendOrderConfirmation(
            event.customer(),
            event.orderId(),
            event.total()
        );
    }
}

@Component
@RequiredArgsConstructor
public class InventoryUpdateListener {
    private final InventoryService inventoryService;

    @EventListener
    public void onOrderConfirmed(OrderConfirmedEvent event) {
        inventoryService.reserveItems(event.orderId());
    }
}

@Component
@RequiredArgsConstructor
public class AnalyticsListener {
    private final AnalyticsService analyticsService;

    @EventListener
    @Async
    public void onOrderConfirmed(OrderConfirmedEvent event) {
        analyticsService.trackOrderPlaced(event);
    }
}

// Publisher
@Service
@RequiredArgsConstructor
public class OrderService {
    private final OrderRepository orderRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Transactional
    public Order confirmOrder(UUID orderId) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));

        order.confirm();
        Order saved = orderRepository.save(order);

        // Publish event - all listeners will be notified
        eventPublisher.publishEvent(new OrderConfirmedEvent(
            saved.getId(),
            saved.getCustomer(),
            saved.getTotal(),
            LocalDateTime.now()
        ));

        return saved;
    }
}
```

#### TypeScript Example (RxJS)

```typescript
import { Subject } from 'rxjs';

// Event
interface CartUpdatedEvent {
  items: CartItem[];
  total: number;
}

// Observable subject
@Injectable({ providedIn: 'root' })
export class CartService {
  private cartUpdated$ = new Subject<CartUpdatedEvent>();

  // Subscribe to events
  onCartUpdated(): Observable<CartUpdatedEvent> {
    return this.cartUpdated$.asObservable();
  }

  // Publish event
  addToCart(item: CartItem): void {
    // ... add item logic
    this.cartUpdated$.next({
      items: this.items,
      total: this.calculateTotal()
    });
  }
}

// Observers
@Component({...})
export class CartIconComponent {
  private cartService = inject(CartService);
  itemCount = signal(0);

  ngOnInit() {
    this.cartService.onCartUpdated().subscribe(event => {
      this.itemCount.set(event.items.length);
    });
  }
}

@Component({...})
export class CheckoutComponent {
  private cartService = inject(CartService);
  total = signal(0);

  ngOnInit() {
    this.cartService.onCartUpdated().subscribe(event => {
      this.total.set(event.total);
    });
  }
}
```

---

### Template Method Pattern

**Purpose:** Define skeleton of algorithm, let subclasses override steps
**Use When:** Common algorithm with varying steps

#### Buy Nature Example: Order Processing Template

```java
// Abstract template
public abstract class OrderProcessor {

    // Template method (final - cannot be overridden)
    public final OrderResult processOrder(Order order) {
        validateOrder(order);
        Money total = calculateTotal(order);
        PaymentResult payment = processPayment(order, total);

        if (payment.isSuccess()) {
            updateInventory(order);
            notifyCustomer(order);
            return OrderResult.success(order.getId());
        } else {
            handlePaymentFailure(order, payment);
            return OrderResult.failure(payment.getErrorMessage());
        }
    }

    // Steps - some concrete, some abstract

    protected void validateOrder(Order order) {
        if (order.getItems().isEmpty()) {
            throw new EmptyOrderException();
        }
    }

    protected Money calculateTotal(Order order) {
        return order.getItems().stream()
            .map(OrderItem::getSubtotal)
            .reduce(Money.ZERO, Money::add);
    }

    // Abstract - must be implemented by subclasses
    protected abstract PaymentResult processPayment(Order order, Money total);

    protected abstract void updateInventory(Order order);

    protected void notifyCustomer(Order order) {
        // Default implementation (can be overridden)
        System.out.println("Sending confirmation to: " + order.getCustomer().getEmail());
    }

    protected void handlePaymentFailure(Order order, PaymentResult result) {
        // Default implementation
        System.err.println("Payment failed: " + result.getErrorMessage());
    }
}

// Concrete implementations
@Component
public class StandardOrderProcessor extends OrderProcessor {

    @Autowired
    private PaymentGateway paymentGateway;

    @Autowired
    private InventoryService inventoryService;

    @Autowired
    private EmailService emailService;

    @Override
    protected PaymentResult processPayment(Order order, Money total) {
        return paymentGateway.charge(total, order.getPaymentMethod());
    }

    @Override
    protected void updateInventory(Order order) {
        inventoryService.reduceStock(order.getItems());
    }

    @Override
    protected void notifyCustomer(Order order) {
        emailService.sendOrderConfirmation(order);
    }
}

@Component
public class SubscriptionOrderProcessor extends OrderProcessor {

    @Autowired
    private RecurringPaymentService recurringPaymentService;

    @Autowired
    private SubscriptionService subscriptionService;

    @Override
    protected PaymentResult processPayment(Order order, Money total) {
        // Set up recurring payment
        return recurringPaymentService.setupRecurring(
            order.getCustomer(),
            total,
            Period.ofMonths(1)
        );
    }

    @Override
    protected void updateInventory(Order order) {
        // Subscriptions don't affect inventory
    }

    @Override
    protected void notifyCustomer(Order order) {
        subscriptionService.sendWelcomeEmail(order.getCustomer());
    }
}
```

---

## Structural Patterns

### Adapter Pattern

**Purpose:** Convert interface to another interface clients expect
**Use When:** Integrating with external APIs or legacy code

#### Buy Nature Example: Payment Gateway Adapter

```java
// Target interface (what our app expects)
public interface PaymentGateway {
    PaymentResult charge(Money amount, PaymentMethod method);
    PaymentResult refund(String transactionId, Money amount);
}

// Adaptee (external library/API - different interface)
public class StripeAPI {
    public StripeCharge createCharge(int amountInCents, String token) {
        // Stripe's API
    }

    public StripeRefund createRefund(String chargeId, int amountInCents) {
        // Stripe's API
    }
}

// Adapter
@Service
public class StripePaymentAdapter implements PaymentGateway {
    private final StripeAPI stripeAPI;

    public StripePaymentAdapter(StripeAPI stripeAPI) {
        this.stripeAPI = stripeAPI;
    }

    @Override
    public PaymentResult charge(Money amount, PaymentMethod method) {
        // Adapt our domain model to Stripe's API
        int amountInCents = amount.toCents();
        String token = method.getToken();

        try {
            StripeCharge charge = stripeAPI.createCharge(amountInCents, token);

            return PaymentResult.success(
                charge.getId(),
                Money.fromCents(charge.getAmount())
            );
        } catch (StripeException e) {
            return PaymentResult.failure(e.getMessage());
        }
    }

    @Override
    public PaymentResult refund(String transactionId, Money amount) {
        int amountInCents = amount.toCents();

        try {
            StripeRefund refund = stripeAPI.createRefund(transactionId, amountInCents);

            return PaymentResult.success(
                refund.getId(),
                Money.fromCents(refund.getAmount())
            );
        } catch (StripeException e) {
            return PaymentResult.failure(e.getMessage());
        }
    }
}

// Another adapter for a different payment provider
@Service
public class PayPalPaymentAdapter implements PaymentGateway {
    private final PayPalSDK paypalSDK;

    @Override
    public PaymentResult charge(Money amount, PaymentMethod method) {
        // Adapt to PayPal's API (different interface)
        // ...
    }

    @Override
    public PaymentResult refund(String transactionId, Money amount) {
        // Adapt to PayPal's refund API
        // ...
    }
}
```

---

### Decorator Pattern

**Purpose:** Add responsibilities to objects dynamically
**Use When:** Extend functionality without modifying original class

#### Buy Nature Example: Product Price Decorators

```java
// Component interface
public interface PriceCalculator {
    Money calculate(Product product, int quantity);
}

// Concrete component
public class BasePriceCalculator implements PriceCalculator {
    @Override
    public Money calculate(Product product, int quantity) {
        return product.getPrice().multiply(quantity);
    }
}

// Decorators
public abstract class PriceCalculatorDecorator implements PriceCalculator {
    protected final PriceCalculator wrapped;

    public PriceCalculatorDecorator(PriceCalculator wrapped) {
        this.wrapped = wrapped;
    }
}

public class TaxDecorator extends PriceCalculatorDecorator {
    private final Percentage taxRate;

    public TaxDecorator(PriceCalculator wrapped, Percentage taxRate) {
        super(wrapped);
        this.taxRate = taxRate;
    }

    @Override
    public Money calculate(Product product, int quantity) {
        Money basePrice = wrapped.calculate(product, quantity);
        return basePrice.multiply(1 + taxRate.value());
    }
}

public class ShippingDecorator extends PriceCalculatorDecorator {
    private final Money shippingCost;

    public ShippingDecorator(PriceCalculator wrapped, Money shippingCost) {
        super(wrapped);
        this.shippingCost = shippingCost;
    }

    @Override
    public Money calculate(Product product, int quantity) {
        Money basePrice = wrapped.calculate(product, quantity);
        return basePrice.add(shippingCost);
    }
}

public class DiscountDecorator extends PriceCalculatorDecorator {
    private final Percentage discountRate;

    public DiscountDecorator(PriceCalculator wrapped, Percentage discountRate) {
        super(wrapped);
        this.discountRate = discountRate;
    }

    @Override
    public Money calculate(Product product, int quantity) {
        Money basePrice = wrapped.calculate(product, quantity);
        return basePrice.multiply(1 - discountRate.value());
    }
}

// Usage - chain decorators
PriceCalculator calculator = new BasePriceCalculator();
calculator = new DiscountDecorator(calculator, Percentage.of(10));
calculator = new TaxDecorator(calculator, Percentage.of(8.5));
calculator = new ShippingDecorator(calculator, Money.of(5.99));

Money finalPrice = calculator.calculate(product, 2);
```

---

## Anti-Patterns to Avoid

### Singleton (Overused Anti-Pattern)

```java
// ❌ WRONG: Manual singleton (use Spring @Service instead)
public class OrderService {
    private static OrderService instance;

    private OrderService() { }

    public static OrderService getInstance() {
        if (instance == null) {
            instance = new OrderService();
        }
        return instance;
    }
}

// ✅ CORRECT: Let Spring manage singleton
@Service
public class OrderService {
    // Spring creates and manages single instance
}
```

---

## Pattern Decision Guide

| Need | Pattern | Buy Nature Example |
|------|---------|-------------------|
| Create objects flexibly | Factory | PaymentMethodFactory |
| Build complex objects | Builder | Order.builder() |
| Multiple algorithms | Strategy | DiscountStrategy |
| Notify multiple objects | Observer | OrderConfirmedEvent |
| Algorithm template | Template Method | OrderProcessor |
| Adapt external API | Adapter | StripePaymentAdapter |
| Add features dynamically | Decorator | PriceCalculator decorators |

---

## Quick Checklist

- [ ] Pattern solves a real problem (not over-engineering)
- [ ] Pattern makes code more maintainable
- [ ] Pattern is well-known (team understands it)
- [ ] Pattern fits the domain model
- [ ] Simpler solution doesn't exist
