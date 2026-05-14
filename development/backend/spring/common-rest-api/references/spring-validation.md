# Spring Request Validation

## Table of Contents

1. [Bean Validation Annotations](#bean-validation-annotations) — `@NotNull`, `@Size`, etc.
2. [Common Validation Annotations](#common-validation-annotations) — reference table
3. [Custom Validators](#custom-validators) — `@Constraint`, `ConstraintValidator`
4. [Validation Groups](#validation-groups) — `OnCreate`, `OnUpdate`

---

## Request Validation

### Bean Validation Annotations

```java
public record OrderCreationRequest(
    @NotNull(message = "Customer ID is required")
    UUID customerId,

    @NotEmpty(message = "Order must have at least one item")
    @Size(max = 100, message = "Order cannot exceed 100 items")
    List<@Valid OrderItemRequest> items,

    @Size(max = 500, message = "Notes cannot exceed 500 characters")
    String notes,

    @Future(message = "Delivery date must be in the future")
    LocalDate requestedDeliveryDate
) {}

public record OrderItemRequest(
    @NotNull(message = "Product ID is required")
    UUID productId,

    @Min(value = 1, message = "Quantity must be at least 1")
    @Max(value = 1000, message = "Quantity cannot exceed 1000")
    int quantity,

    @DecimalMin(value = "0.01", message = "Price must be positive")
    @Digits(integer = 10, fraction = 2, message = "Invalid price format")
    BigDecimal unitPrice
) {}
```

### Common Validation Annotations

| Annotation | Use Case |
|------------|----------|
| `@NotNull` | Field must not be null |
| `@NotEmpty` | String/Collection must not be empty |
| `@NotBlank` | String must have non-whitespace content |
| `@Size(min, max)` | Length/size constraints |
| `@Min`, `@Max` | Numeric bounds |
| `@Email` | Valid email format |
| `@Pattern` | Regex pattern match |
| `@Past`, `@Future` | Date constraints |
| `@Valid` | Cascade validation to nested objects |

### Custom Validators

```java
// Annotation
@Target({FIELD, PARAMETER})
@Retention(RUNTIME)
@Constraint(validatedBy = UniqueEmailValidator.class)
public @interface UniqueEmail {
    String message() default "Email already exists";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

// Validator
@Component
@RequiredArgsConstructor
public class UniqueEmailValidator implements ConstraintValidator<UniqueEmail, String> {

    private final UserRepository userRepository;

    @Override
    public boolean isValid(String email, ConstraintValidatorContext context) {
        if (email == null) return true;  // @NotNull handles null
        return !userRepository.existsByEmail(email);
    }
}

// Usage
public record UserCreationRequest(
    @UniqueEmail
    @Email
    String email
) {}
```

### Validation Groups

```java
// Define groups
public interface OnCreate {}
public interface OnUpdate {}

// Apply to DTO
public record UserRequest(
    @Null(groups = OnCreate.class)
    @NotNull(groups = OnUpdate.class)
    UUID id,

    @NotBlank(groups = {OnCreate.class, OnUpdate.class})
    String name
) {}

// Use in controller
@PostMapping
public UserResponse create(@Validated(OnCreate.class) @RequestBody UserRequest request) { }

@PutMapping("/{id}")
public UserResponse update(@Validated(OnUpdate.class) @RequestBody UserRequest request) { }
```
