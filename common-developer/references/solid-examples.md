# SOLID Principles - Complete Examples

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## S - Single Responsibility Principle (SRP)

**Definition:** A class should have only ONE reason to change.

### 🔴 WRONG - Multiple Responsibilities

```java
// BAD: Order class handles business logic, persistence, and notification
public class Order {
    private UUID id;
    private List<Item> items;
    private Customer customer;

    // Business logic
    public BigDecimal calculateTotal() {
        return items.stream()
            .map(Item::getPrice)
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    // Persistence (WRONG: mixing concerns)
    public void save() {
        Connection conn = DriverManager.getConnection("...");
        // SQL save logic
    }

    // Notification (WRONG: mixing concerns)
    public void sendConfirmationEmail() {
        EmailService.send(customer.getEmail(), "Order confirmed");
    }
}
```

**Problems:**
- Changes to email template require modifying Order class
- Database schema changes require modifying Order class
- Business logic changes require modifying Order class

### ✅ CORRECT - Single Responsibility

```java
// Entity: only domain data and behavior
@Entity
@Table(name = "orders")
public class Order {
    @Id
    private UUID id;

    @ManyToOne
    private Customer customer;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderItem> items;

    private OrderStatus status;
    private LocalDateTime createdAt;

    // Business logic ONLY
    public Money calculateTotal() {
        return items.stream()
            .map(OrderItem::getSubtotal)
            .reduce(Money.ZERO, Money::add);
    }

    public void confirm() {
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("Only pending orders can be confirmed");
        }
        this.status = OrderStatus.CONFIRMED;
    }
}

// Repository: persistence responsibility
@Repository
public interface OrderRepository extends JpaRepository<Order, UUID> {
    List<Order> findByCustomerId(UUID customerId);
    List<Order> findByStatus(OrderStatus status);
}

// Service: orchestration responsibility
@Service
@RequiredArgsConstructor
public class OrderService {
    private final OrderRepository orderRepository;
    private final EmailNotificationService emailService;

    @Transactional
    public Order confirmOrder(UUID orderId) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));

        order.confirm();
        Order saved = orderRepository.save(order);

        emailService.sendOrderConfirmation(saved);

        return saved;
    }
}

// Notification: email sending responsibility
@Service
@RequiredArgsConstructor
public class EmailNotificationService {
    private final JavaMailSender mailSender;

    public void sendOrderConfirmation(Order order) {
        MimeMessage message = mailSender.createMimeMessage();
        // Email construction logic
        mailSender.send(message);
    }
}
```

### TypeScript Example (Angular)

```typescript
// ❌ WRONG: Component doing too much
@Component({
  selector: 'app-product-list',
  template: `...`
})
export class ProductListComponent {
  products = signal<Product[]>([]);

  ngOnInit() {
    // HTTP logic (WRONG: should be in service)
    fetch('/api/products')
      .then(res => res.json())
      .then(data => this.products.set(data));
  }

  // Business logic (WRONG: should be in service)
  calculateDiscount(product: Product): number {
    if (product.category === 'organic') {
      return product.price * 0.1;
    }
    return 0;
  }

  // Presentation logic (OK: belongs in component)
  formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  }
}
```

```typescript
// ✅ CORRECT: Separated responsibilities

// Service: HTTP and business logic
@Injectable({ providedIn: 'root' })
export class ProductService {
  private http = inject(HttpClient);

  getProducts(): Observable<Product[]> {
    return this.http.get<Product[]>('/api/products');
  }

  calculateDiscount(product: Product): number {
    if (product.category === 'organic') {
      return product.price * 0.1;
    }
    return 0;
  }
}

// Pipe: Formatting logic
@Pipe({ name: 'currency', standalone: true })
export class CurrencyPipe implements PipeTransform {
  transform(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  }
}

// Component: Presentation logic ONLY
@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [CurrencyPipe],
  template: `
    @for (product of products(); track product.id) {
      <div class="product">
        <h3>{{ product.name }}</h3>
        <p>{{ product.price | currency }}</p>
      </div>
    }
  `
})
export class ProductListComponent {
  private productService = inject(ProductService);
  products = signal<Product[]>([]);

  ngOnInit() {
    this.productService.getProducts()
      .subscribe(products => this.products.set(products));
  }
}
```

---

## O - Open/Closed Principle (OCP)

**Definition:** Open for extension, closed for modification.

### 🔴 WRONG - Modifying existing code for new features

```java
// BAD: Adding new payment methods requires modifying this class
public class PaymentProcessor {
    public void processPayment(String type, BigDecimal amount) {
        if (type.equals("CREDIT_CARD")) {
            // Credit card logic
            System.out.println("Processing credit card: " + amount);
        } else if (type.equals("PAYPAL")) {
            // PayPal logic
            System.out.println("Processing PayPal: " + amount);
        } else if (type.equals("CRYPTO")) {  // NEW: modification required
            // Crypto logic
            System.out.println("Processing crypto: " + amount);
        }
        // Adding more payment types = more if/else = violation
    }
}
```

### ✅ CORRECT - Extension through abstraction

```java
// Interface: contract for payment methods
public interface PaymentMethod {
    PaymentResult process(Money amount, PaymentDetails details);
    boolean supports(PaymentType type);
}

// Implementations: extend without modifying existing code
@Component
public class CreditCardPayment implements PaymentMethod {
    @Override
    public PaymentResult process(Money amount, PaymentDetails details) {
        // Credit card processing logic
        return PaymentResult.success(generateTransactionId());
    }

    @Override
    public boolean supports(PaymentType type) {
        return type == PaymentType.CREDIT_CARD;
    }
}

@Component
public class PayPalPayment implements PaymentMethod {
    @Override
    public PaymentResult process(Money amount, PaymentDetails details) {
        // PayPal processing logic
        return PaymentResult.success(generateTransactionId());
    }

    @Override
    public boolean supports(PaymentType type) {
        return type == PaymentType.PAYPAL;
    }
}

// NEW payment method: just add implementation (no modification)
@Component
public class CryptoPayment implements PaymentMethod {
    @Override
    public PaymentResult process(Money amount, PaymentDetails details) {
        // Crypto processing logic
        return PaymentResult.success(generateTransactionId());
    }

    @Override
    public boolean supports(PaymentType type) {
        return type == PaymentType.CRYPTO;
    }
}

// Orchestrator: uses abstraction
@Service
@RequiredArgsConstructor
public class PaymentProcessor {
    private final List<PaymentMethod> paymentMethods; // Spring injects all implementations

    public PaymentResult processPayment(PaymentType type, Money amount, PaymentDetails details) {
        return paymentMethods.stream()
            .filter(method -> method.supports(type))
            .findFirst()
            .map(method -> method.process(amount, details))
            .orElseThrow(() -> new UnsupportedPaymentMethodException(type));
    }
}
```

### TypeScript Example (Strategy Pattern)

```typescript
// Interface
interface PriceCalculator {
  calculate(basePrice: number, quantity: number): number;
}

// Implementations
class StandardPriceCalculator implements PriceCalculator {
  calculate(basePrice: number, quantity: number): number {
    return basePrice * quantity;
  }
}

class BulkDiscountCalculator implements PriceCalculator {
  constructor(private threshold: number, private discountPercent: number) {}

  calculate(basePrice: number, quantity: number): number {
    const total = basePrice * quantity;
    if (quantity >= this.threshold) {
      return total * (1 - this.discountPercent / 100);
    }
    return total;
  }
}

class SeasonalDiscountCalculator implements PriceCalculator {
  constructor(private discountPercent: number) {}

  calculate(basePrice: number, quantity: number): number {
    return basePrice * quantity * (1 - this.discountPercent / 100);
  }
}

// Usage
@Injectable()
export class PricingService {
  private calculators = new Map<string, PriceCalculator>([
    ['standard', new StandardPriceCalculator()],
    ['bulk', new BulkDiscountCalculator(10, 15)],
    ['seasonal', new SeasonalDiscountCalculator(20)]
  ]);

  calculatePrice(type: string, basePrice: number, quantity: number): number {
    const calculator = this.calculators.get(type) ?? this.calculators.get('standard')!;
    return calculator.calculate(basePrice, quantity);
  }
}
```

---

## L - Liskov Substitution Principle (LSP)

**Definition:** Subtypes must be substitutable for their base types.

### 🔴 WRONG - Violating contracts

```java
// BAD: Square violates Rectangle contract
public class Rectangle {
    protected int width;
    protected int height;

    public void setWidth(int width) {
        this.width = width;
    }

    public void setHeight(int height) {
        this.height = height;
    }

    public int getArea() {
        return width * height;
    }
}

public class Square extends Rectangle {
    @Override
    public void setWidth(int width) {
        this.width = width;
        this.height = width;  // VIOLATION: unexpected side effect
    }

    @Override
    public void setHeight(int height) {
        this.width = height;
        this.height = height;  // VIOLATION: unexpected side effect
    }
}

// This breaks with Square:
void testRectangle(Rectangle rect) {
    rect.setWidth(5);
    rect.setHeight(4);
    assert rect.getArea() == 20;  // FAILS for Square (25 instead of 20)
}
```

### ✅ CORRECT - Proper abstraction

```java
// Correct: use composition or separate interfaces
public interface Shape {
    int getArea();
}

public class Rectangle implements Shape {
    private final int width;
    private final int height;

    public Rectangle(int width, int height) {
        this.width = width;
        this.height = height;
    }

    @Override
    public int getArea() {
        return width * height;
    }
}

public class Square implements Shape {
    private final int side;

    public Square(int side) {
        this.side = side;
    }

    @Override
    public int getArea() {
        return side * side;
    }
}
```

### Buy Nature Example

```java
// ❌ WRONG: Violating substitution
public abstract class Product {
    protected UUID id;
    protected String name;
    protected BigDecimal price;

    public void applyDiscount(BigDecimal percentage) {
        this.price = price.subtract(price.multiply(percentage));
    }
}

public class GiftCard extends Product {
    @Override
    public void applyDiscount(BigDecimal percentage) {
        throw new UnsupportedOperationException("Gift cards cannot be discounted");
        // VIOLATION: breaks contract
    }
}
```

```java
// ✅ CORRECT: Proper hierarchy
public interface Priceable {
    Money getPrice();
}

public interface Discountable {
    void applyDiscount(Percentage discount);
}

@Entity
public class PhysicalProduct implements Priceable, Discountable {
    private Money price;

    @Override
    public Money getPrice() {
        return price;
    }

    @Override
    public void applyDiscount(Percentage discount) {
        this.price = price.multiply(1 - discount.value());
    }
}

@Entity
public class GiftCard implements Priceable {
    private Money value;

    @Override
    public Money getPrice() {
        return value;  // No discount support (not Discountable)
    }
}
```

---

## I - Interface Segregation Principle (ISP)

**Definition:** Many specific interfaces > one general-purpose interface.

### 🔴 WRONG - Fat interface

```java
// BAD: Forcing all products to implement unused methods
public interface Product {
    UUID getId();
    String getName();
    BigDecimal getPrice();

    // Physical product methods
    Double getWeight();
    Dimensions getDimensions();

    // Digital product methods
    String getDownloadUrl();
    Long getFileSizeInBytes();

    // Subscription methods
    Period getBillingPeriod();
    LocalDate getRenewalDate();
}

// Implementations forced to throw exceptions or return null
public class EBook implements Product {
    // ... useful methods ...

    @Override
    public Double getWeight() {
        throw new UnsupportedOperationException("eBooks don't have weight");
    }

    @Override
    public Dimensions getDimensions() {
        throw new UnsupportedOperationException("eBooks don't have dimensions");
    }
}
```

### ✅ CORRECT - Segregated interfaces

```java
// Base interface
public interface Product {
    UUID getId();
    String getName();
    Money getPrice();
}

// Specific interfaces
public interface PhysicalProduct extends Product {
    Weight getWeight();
    Dimensions getDimensions();
    ShippingClass getShippingClass();
}

public interface DigitalProduct extends Product {
    URI getDownloadUrl();
    FileSize getFileSize();
    Duration getAccessDuration();
}

public interface Subscription extends Product {
    Period getBillingPeriod();
    LocalDate getRenewalDate();
    SubscriptionStatus getStatus();
}

// Implementations only implement what they need
@Entity
public class Book implements PhysicalProduct {
    // Only physical product methods
}

@Entity
public class EBook implements DigitalProduct {
    // Only digital product methods
}

@Entity
public class MembershipSubscription implements Subscription {
    // Only subscription methods
}
```

### Angular Example

```typescript
// ❌ WRONG: Forcing all components to implement unused methods
interface FormComponent {
  // Used by all forms
  submit(): void;
  reset(): void;

  // Only used by multi-step forms
  nextStep(): void;
  previousStep(): void;
  goToStep(step: number): void;

  // Only used by draft-enabled forms
  saveDraft(): void;
  loadDraft(): void;
}
```

```typescript
// ✅ CORRECT: Segregated interfaces
interface BasicForm {
  submit(): void;
  reset(): void;
}

interface MultiStepForm extends BasicForm {
  nextStep(): void;
  previousStep(): void;
  goToStep(step: number): void;
}

interface DraftableForm extends BasicForm {
  saveDraft(): void;
  loadDraft(): void;
}

// Components implement only what they need
@Component({...})
export class CheckoutComponent implements MultiStepForm, DraftableForm {
  submit() { /* ... */ }
  reset() { /* ... */ }
  nextStep() { /* ... */ }
  previousStep() { /* ... */ }
  goToStep(step: number) { /* ... */ }
  saveDraft() { /* ... */ }
  loadDraft() { /* ... */ }
}

@Component({...})
export class ContactFormComponent implements BasicForm {
  submit() { /* ... */ }
  reset() { /* ... */ }
  // No multi-step or draft methods needed
}
```

---

## D - Dependency Inversion Principle (DIP)

**Definition:** Depend on abstractions, not concretions.

### 🔴 WRONG - Depending on concrete classes

```java
// BAD: OrderService depends on concrete EmailService
public class OrderService {
    private EmailService emailService = new EmailService();  // WRONG: new keyword
    private OrderRepository orderRepository = new JpaOrderRepository();  // WRONG

    public void placeOrder(Order order) {
        orderRepository.save(order);
        emailService.sendConfirmation(order.getCustomer().getEmail());
    }
}
```

**Problems:**
- Cannot test OrderService without sending real emails
- Cannot swap email provider without modifying OrderService
- Tight coupling to implementations

### ✅ CORRECT - Dependency Injection with abstractions

```java
// Abstractions
public interface NotificationService {
    void sendOrderConfirmation(Customer customer, Order order);
}

public interface OrderRepository extends JpaRepository<Order, UUID> {
    // Repository methods
}

// Service depends on abstractions
@Service
@RequiredArgsConstructor  // Constructor injection
public class OrderService {
    private final OrderRepository orderRepository;
    private final NotificationService notificationService;

    @Transactional
    public Order placeOrder(OrderCreationRequest request, Customer customer) {
        Order order = Order.from(request, customer);
        Order saved = orderRepository.save(order);

        notificationService.sendOrderConfirmation(customer, saved);

        return saved;
    }
}

// Implementations
@Service
public class EmailNotificationService implements NotificationService {
    @Override
    public void sendOrderConfirmation(Customer customer, Order order) {
        // Email implementation
    }
}

@Service
@Profile("sms")
public class SmsNotificationService implements NotificationService {
    @Override
    public void sendOrderConfirmation(Customer customer, Order order) {
        // SMS implementation (can swap via profile)
    }
}
```

### Testing with DIP

```java
// Easy to test with mocks
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock
    private OrderRepository orderRepository;

    @Mock
    private NotificationService notificationService;

    @InjectMocks
    private OrderService orderService;

    @Test
    void whenPlaceOrder_shouldSaveAndNotify() {
        // Given
        OrderCreationRequest request = new OrderCreationRequest(/* ... */);
        Customer customer = TestData.customer();
        Order order = Order.from(request, customer);

        when(orderRepository.save(any())).thenReturn(order);

        // When
        Order result = orderService.placeOrder(request, customer);

        // Then
        verify(orderRepository).save(any(Order.class));
        verify(notificationService).sendOrderConfirmation(customer, order);
        assertThat(result).isEqualTo(order);
    }
}
```

---

## Summary: When to Apply Each Principle

| Principle | Apply When | Buy Nature Example |
|-----------|------------|-------------------|
| **SRP** | Class has multiple reasons to change | Separate Order entity, OrderRepository, OrderService, EmailService |
| **OCP** | New features require modifying existing code | Payment methods via PaymentMethod interface |
| **LSP** | Subtypes break parent contracts | Product hierarchy (Physical, Digital, Subscription) |
| **ISP** | Clients forced to implement unused methods | Product interfaces (Priceable, Discountable, Shippable) |
| **DIP** | Service depends on concrete implementations | Inject NotificationService, not EmailService directly |

---

## Quick Checklist

- [ ] Each class has a single, well-defined responsibility (SRP)
- [ ] New features added via new classes, not modifying existing ones (OCP)
- [ ] Subtypes can replace parent types without breaking behavior (LSP)
- [ ] Interfaces are focused and specific (ISP)
- [ ] Dependencies are abstractions, injected via constructor (DIP)
