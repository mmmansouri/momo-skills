# Spring REST API Reference (Spring Boot 4 / Spring Framework 7)

## What's New in Spring Framework 7 for REST

### Key Changes

| Feature | Spring 6 | Spring 7 |
|---------|----------|----------|
| API Versioning | Manual implementation | First-class support |
| RestTemplate | Deprecated | Being removed (use RestClient) |
| Null Safety | JSR-305 | JSpecify annotations |
| Resilience | External libs | Built-in retry/throttling |
| HTTP Client | RestTemplate, WebClient | RestClient, WebClient, HTTP Interface |

### New API Versioning Support

```java
// Spring Framework 7 built-in versioning
@RestController
@ApiVersion("1")
@RequestMapping("/orders")
public class OrderControllerV1 {

    @GetMapping("/{id}")
    public OrderResponse getOrder(@PathVariable UUID id) {
        // Accessible via /v1/orders/{id}
    }
}

// Configuration
@Configuration
public class ApiVersionConfig implements WebMvcConfigurer {

    @Override
    public void configureApiVersioning(ApiVersionConfigurer configurer) {
        configurer
            .versionPrefix("v")
            .defaultVersion("1");
    }
}
```

### RestClient (Preferred over RestTemplate)

```java
// Spring 7 RestClient (replaces RestTemplate)
@Configuration
public class HttpClientConfig {

    @Bean
    public RestClient restClient(RestClient.Builder builder) {
        return builder
            .baseUrl("https://api.example.com")
            .defaultHeader("Accept", MediaType.APPLICATION_JSON_VALUE)
            .requestInterceptor(new LoggingInterceptor())
            .build();
    }
}

// Usage
@Service
@RequiredArgsConstructor
public class OrderClient {

    private final RestClient restClient;

    public Order getOrder(UUID id) {
        return restClient.get()
            .uri("/orders/{id}", id)
            .retrieve()
            .body(Order.class);
    }

    public Order createOrder(OrderRequest request) {
        return restClient.post()
            .uri("/orders")
            .contentType(MediaType.APPLICATION_JSON)
            .body(request)
            .retrieve()
            .body(Order.class);
    }
}
```

### HTTP Interface Clients (Spring Framework 7)

Define REST clients as interfaces (like Feign, but native Spring):

```java
@HttpExchange("/customers")
public interface CustomerClient {

    @GetExchange("/{id}")
    CustomerResponse getCustomer(@PathVariable UUID id);

    @PostExchange
    CustomerResponse createCustomer(@RequestBody CustomerCreationRequest request);

    @PutExchange("/{id}")
    CustomerResponse updateCustomer(
        @PathVariable UUID id,
        @RequestBody CustomerUpdateRequest request
    );

    @DeleteExchange("/{id}")
    void deleteCustomer(@PathVariable UUID id);

    @GetExchange
    List<CustomerResponse> listCustomers(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    );
}
```

**Configuration:**

```java
@Configuration
public class HttpInterfaceConfig {

    @Bean
    public CustomerClient customerClient(RestClient.Builder builder) {
        RestClient restClient = builder
            .baseUrl("https://api.example.com")
            .build();

        HttpServiceProxyFactory factory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(restClient))
            .build();

        return factory.createClient(CustomerClient.class);
    }
}
```

**Usage in services:**

```java
@Service
public class OrderService {
    private final CustomerClient customerClient;

    public OrderService(CustomerClient customerClient) {
        this.customerClient = customerClient;
    }

    public OrderResponse createOrder(OrderCreationRequest request, String username) {
        CustomerResponse customer = customerClient.getCustomer(request.customerId());
        return orderRepository.save(Order.create(request, customer));
    }
}
```

### Virtual Threads for REST Controllers

Spring Boot 4 with Java 21+ supports virtual threads for high-throughput blocking I/O:

```java
@Configuration
public class VirtualThreadsConfig {

    @Bean
    public TomcatProtocolHandlerCustomizer<?> protocolHandlerVirtualThreadExecutorCustomizer() {
        return protocolHandler -> {
            protocolHandler.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
        };
    }
}
```

**When to use:**
- High concurrency (1000+ concurrent requests)
- Blocking I/O operations (database, external APIs)
- Long-running requests (SSE, polling)

**When NOT to use:**
- CPU-intensive operations (use platform threads)
- Async/reactive code (already non-blocking)

### Comparison: RestTemplate vs RestClient vs HTTP Interface

| Feature | RestTemplate | RestClient | HTTP Interface |
|---------|--------------|------------|----------------|
| **Release** | Spring 3.0 (2009) | Spring 6.1 / Boot 3.2 | Spring 6.0 / Boot 3.0 |
| **API Style** | Imperative, verbose | Fluent, modern | Declarative |
| **Type Safety** | ⚠️ Weak | ✅ Strong | ✅ Strong |
| **Error Handling** | Exception-based | Fluent + exceptions | Exception-based |
| **Interceptors** | ✅ Yes | ✅ Yes | ✅ Yes (via RestClient) |
| **Async Support** | ❌ No (use WebClient) | ❌ No (use WebClient) | ❌ No |
| **Status** | Maintenance mode | ✅ Preferred | ✅ Preferred |
| **Use Case** | Legacy code | New code, fluent API | Interface-driven, clean |

### Buy Nature Migration Path

**Current (Spring Boot 3.x):**
- Use `RestTemplate` in existing services (don't rewrite)

**New code (Spring Boot 4.x):**
1. **Simple HTTP calls:** Use `RestClient`
2. **Multiple endpoints, clean interface:** Use `@HttpExchange` clients
3. **Async/reactive:** Use `WebClient`

---

## Controller Design

### Basic REST Controller

```java
@RestController
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
@Tag(name = "Orders", description = "Order management API")
public class OrderController {

    private final OrderService orderService;

    @GetMapping
    @Operation(summary = "List all orders")
    public Page<OrderSummaryResponse> listOrders(
            @ParameterObject Pageable pageable) {
        return orderService.findAll(pageable)
            .map(OrderSummaryResponse::from);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get order by ID")
    public OrderResponse getOrder(@PathVariable UUID id) {
        return orderService.findById(id)
            .map(OrderResponse::from)
            .orElseThrow(() -> new ResourceNotFoundException("Order", id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Create a new order")
    public ResponseEntity<OrderResponse> createOrder(
            @Valid @RequestBody OrderCreationRequest request) {
        Order order = orderService.create(request);
        URI location = ServletUriComponentsBuilder.fromCurrentRequest()
            .path("/{id}")
            .buildAndExpand(order.getId())
            .toUri();
        return ResponseEntity.created(location)
            .body(OrderResponse.from(order));
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update an order")
    public OrderResponse updateOrder(
            @PathVariable UUID id,
            @Valid @RequestBody OrderUpdateRequest request) {
        Order order = orderService.update(id, request);
        return OrderResponse.from(order);
    }

    @PatchMapping("/{id}")
    @Operation(summary = "Partially update an order")
    public OrderResponse patchOrder(
            @PathVariable UUID id,
            @Valid @RequestBody OrderPatchRequest request) {
        Order order = orderService.patch(id, request);
        return OrderResponse.from(order);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete an order")
    public void deleteOrder(@PathVariable UUID id) {
        orderService.delete(id);
    }
}
```

### Controller Best Practices

```java
// ✅ DO: Use @RestController for APIs
@RestController  // Combines @Controller + @ResponseBody

// ✅ DO: Group related endpoints
@RequestMapping("/api/v1/orders")

// ✅ DO: Use proper HTTP methods
@GetMapping     // Read
@PostMapping    // Create
@PutMapping     // Replace
@PatchMapping   // Partial update
@DeleteMapping  // Remove

// ✅ DO: Use ResponseEntity for control
public ResponseEntity<OrderResponse> createOrder(...) {
    return ResponseEntity.created(location).body(response);
}

// ✅ DO: Use @ResponseStatus for simple cases
@DeleteMapping("/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void deleteOrder(@PathVariable UUID id) { }

// ✅ DO: Keep controllers thin
// Business logic belongs in services, not controllers
```

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

---

## Exception Handling

### RFC 7807 Problem Details (Spring 6+)

```java
@RestControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {

    // Resource not found
    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail handleNotFound(ResourceNotFoundException ex, WebRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setTitle("Resource Not Found");
        problem.setType(URI.create("https://api.example.com/errors/not-found"));
        problem.setInstance(URI.create(getRequestUri(request)));
        return problem;
    }

    // Business rule violation
    @ExceptionHandler(BusinessException.class)
    public ProblemDetail handleBusinessError(BusinessException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.CONFLICT, ex.getMessage());
        problem.setTitle(ex.getTitle());
        problem.setType(URI.create("https://api.example.com/errors/" + ex.getErrorCode()));
        // Custom properties
        problem.setProperty("errorCode", ex.getErrorCode());
        return problem;
    }

    // Validation errors
    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException ex,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request) {

        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.BAD_REQUEST, "The request contains invalid fields");
        problem.setTitle("Validation Failed");
        problem.setType(URI.create("https://api.example.com/errors/validation-failed"));

        List<Map<String, String>> errors = ex.getBindingResult().getFieldErrors().stream()
            .map(error -> Map.of(
                "field", error.getField(),
                "message", Objects.requireNonNull(error.getDefaultMessage()),
                "rejectedValue", String.valueOf(error.getRejectedValue())))
            .toList();
        problem.setProperty("errors", errors);

        return ResponseEntity.badRequest().body(problem);
    }

    // Constraint violation (path/query params)
    @ExceptionHandler(ConstraintViolationException.class)
    public ProblemDetail handleConstraintViolation(ConstraintViolationException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.BAD_REQUEST, "Invalid request parameters");
        problem.setTitle("Constraint Violation");

        List<Map<String, String>> errors = ex.getConstraintViolations().stream()
            .map(violation -> Map.of(
                "field", violation.getPropertyPath().toString(),
                "message", violation.getMessage()))
            .toList();
        problem.setProperty("errors", errors);

        return problem;
    }

    // Fallback for unexpected errors
    @ExceptionHandler(Exception.class)
    public ProblemDetail handleUnexpected(Exception ex) {
        log.error("Unexpected error", ex);
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.INTERNAL_SERVER_ERROR, "An unexpected error occurred");
        problem.setTitle("Internal Server Error");
        problem.setType(URI.create("https://api.example.com/errors/internal-error"));
        return problem;
    }

    private String getRequestUri(WebRequest request) {
        return ((ServletWebRequest) request).getRequest().getRequestURI();
    }
}
```

### Custom Exception Classes

```java
// Base business exception
public abstract class BusinessException extends RuntimeException {
    private final String errorCode;
    private final String title;

    protected BusinessException(String errorCode, String title, String message) {
        super(message);
        this.errorCode = errorCode;
        this.title = title;
    }

    public String getErrorCode() { return errorCode; }
    public String getTitle() { return title; }
}

// Specific exceptions
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String resourceType, Object id) {
        super(resourceType + " with ID '" + id + "' was not found");
    }
}

public class DuplicateResourceException extends BusinessException {
    public DuplicateResourceException(String field, String value) {
        super("duplicate-resource",
              "Duplicate Resource",
              "A resource with " + field + " '" + value + "' already exists");
    }
}

public class InsufficientStockException extends BusinessException {
    public InsufficientStockException(String productName, int available, int requested) {
        super("insufficient-stock",
              "Insufficient Stock",
              "Product '" + productName + "' has " + available +
              " units available, but " + requested + " were requested");
    }
}
```

---

## Pagination

### Spring Data Pagination

```java
@GetMapping
public Page<OrderSummaryResponse> listOrders(
        @ParameterObject Pageable pageable) {
    return orderService.findAll(pageable)
        .map(OrderSummaryResponse::from);
}

// Request: GET /orders?page=0&size=20&sort=createdAt,desc
```

### Custom Pagination Response

```java
public record PageResponse<T>(
    List<T> content,
    PageMetadata page
) {
    public record PageMetadata(
        int number,
        int size,
        long totalElements,
        int totalPages,
        boolean first,
        boolean last
    ) {}

    public static <T, R> PageResponse<R> from(Page<T> page, Function<T, R> mapper) {
        return new PageResponse<>(
            page.getContent().stream().map(mapper).toList(),
            new PageMetadata(
                page.getNumber(),
                page.getSize(),
                page.getTotalElements(),
                page.getTotalPages(),
                page.isFirst(),
                page.isLast()
            )
        );
    }
}

// Usage
@GetMapping
public PageResponse<OrderSummaryResponse> listOrders(Pageable pageable) {
    Page<Order> orders = orderService.findAll(pageable);
    return PageResponse.from(orders, OrderSummaryResponse::from);
}
```

### Cursor-Based Pagination

```java
public record CursorPageRequest(
    @Min(1) @Max(100) int limit,
    String after,
    String before
) {
    public CursorPageRequest {
        if (limit <= 0) limit = 20;
    }
}

public record CursorPageResponse<T>(
    List<T> data,
    CursorInfo cursors,
    boolean hasMore
) {
    public record CursorInfo(String before, String after) {}
}

@GetMapping
public CursorPageResponse<OrderSummaryResponse> listOrders(
        @Valid CursorPageRequest request) {
    return orderService.findAllWithCursor(request);
}
```

---

## API Documentation (OpenAPI)

### Dependencies

```xml
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.8.5</version>
</dependency>
```

### Configuration

```yaml
# application.yml
springdoc:
  api-docs:
    path: /v3/api-docs
  swagger-ui:
    path: /swagger-ui.html
    operationsSorter: method
    tagsSorter: alpha
  default-consumes-media-type: application/json
  default-produces-media-type: application/json
```

### Global Configuration

```java
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("Order Management API")
                .version("1.0.0")
                .description("API for managing orders and related resources")
                .contact(new Contact()
                    .name("API Team")
                    .email("api@example.com"))
                .license(new License()
                    .name("Apache 2.0")
                    .url("https://www.apache.org/licenses/LICENSE-2.0")))
            .addSecurityItem(new SecurityRequirement().addList("bearer-jwt"))
            .components(new Components()
                .addSecuritySchemes("bearer-jwt", new SecurityScheme()
                    .type(SecurityScheme.Type.HTTP)
                    .scheme("bearer")
                    .bearerFormat("JWT")
                    .description("JWT Authentication")));
    }
}
```

### Controller Annotations

```java
@RestController
@RequestMapping("/api/v1/orders")
@Tag(name = "Orders", description = "Order management operations")
public class OrderController {

    @Operation(
        summary = "Create a new order",
        description = "Creates an order for the specified customer with the given items"
    )
    @ApiResponses({
        @ApiResponse(
            responseCode = "201",
            description = "Order created successfully",
            headers = @Header(name = "Location", description = "URI of created order"),
            content = @Content(schema = @Schema(implementation = OrderResponse.class))
        ),
        @ApiResponse(
            responseCode = "400",
            description = "Validation error",
            content = @Content(schema = @Schema(implementation = ProblemDetail.class))
        ),
        @ApiResponse(
            responseCode = "404",
            description = "Customer not found",
            content = @Content(schema = @Schema(implementation = ProblemDetail.class))
        )
    })
    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(
            @io.swagger.v3.oas.annotations.parameters.RequestBody(
                description = "Order creation details",
                required = true
            )
            @Valid @RequestBody OrderCreationRequest request) {
        // ...
    }
}
```

### Schema Annotations

```java
@Schema(description = "Request to create a new order")
public record OrderCreationRequest(
    @Schema(description = "ID of the customer placing the order", example = "550e8400-e29b-41d4-a716-446655440000")
    @NotNull UUID customerId,

    @Schema(description = "List of items to order", minLength = 1, maxLength = 100)
    @NotEmpty List<@Valid OrderItemRequest> items,

    @Schema(description = "Optional notes for the order", maxLength = 500)
    String notes
) {}

@Schema(description = "Order details in response")
public record OrderResponse(
    @Schema(description = "Unique order identifier")
    UUID id,

    @Schema(description = "Current order status", example = "PENDING")
    OrderStatus status,

    @Schema(description = "Order total amount", example = "99.99")
    BigDecimal total,

    @Schema(description = "Order creation timestamp")
    Instant createdAt
) {}
```

---

## HATEOAS with Spring

### Dependencies

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-hateoas</artifactId>
</dependency>
```

### EntityModel (Single Resource)

```java
@GetMapping("/{id}")
public EntityModel<OrderResponse> getOrder(@PathVariable UUID id) {
    Order order = orderService.findById(id).orElseThrow();
    OrderResponse response = OrderResponse.from(order);

    return EntityModel.of(response,
        linkTo(methodOn(OrderController.class).getOrder(id)).withSelfRel(),
        linkTo(methodOn(OrderController.class).getOrderItems(id)).withRel("items"),
        linkTo(methodOn(CustomerController.class).getCustomer(order.getCustomerId())).withRel("customer"),
        linkTo(methodOn(OrderController.class).listOrders(Pageable.unpaged())).withRel("collection"));
}
```

### CollectionModel (Multiple Resources)

```java
@GetMapping
public CollectionModel<EntityModel<OrderSummaryResponse>> listOrders() {
    List<Order> orders = orderService.findAll();

    List<EntityModel<OrderSummaryResponse>> orderModels = orders.stream()
        .map(order -> EntityModel.of(
            OrderSummaryResponse.from(order),
            linkTo(methodOn(OrderController.class).getOrder(order.getId())).withSelfRel()))
        .toList();

    return CollectionModel.of(orderModels,
        linkTo(methodOn(OrderController.class).listOrders()).withSelfRel());
}
```

### PagedModel (Paginated Resources)

```java
@GetMapping
public PagedModel<EntityModel<OrderSummaryResponse>> listOrders(
        @ParameterObject Pageable pageable,
        PagedResourcesAssembler<Order> assembler) {

    Page<Order> orders = orderService.findAll(pageable);

    return assembler.toModel(orders, order ->
        EntityModel.of(
            OrderSummaryResponse.from(order),
            linkTo(methodOn(OrderController.class).getOrder(order.getId())).withSelfRel()));
}
```

---

## Content Negotiation

### Configuration

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
        configurer
            .defaultContentType(MediaType.APPLICATION_JSON)
            .favorParameter(false)
            .ignoreAcceptHeader(false)
            .mediaType("json", MediaType.APPLICATION_JSON)
            .mediaType("xml", MediaType.APPLICATION_XML)
            .mediaType("csv", new MediaType("text", "csv"));
    }
}
```

### Multiple Representations

```java
@GetMapping(value = "/{id}", produces = {
    MediaType.APPLICATION_JSON_VALUE,
    MediaType.APPLICATION_XML_VALUE
})
public OrderResponse getOrder(@PathVariable UUID id) {
    return orderService.findById(id)
        .map(OrderResponse::from)
        .orElseThrow();
}

// CSV export
@GetMapping(value = "/export", produces = "text/csv")
public ResponseEntity<Resource> exportOrders() {
    String csv = orderService.exportToCsv();
    return ResponseEntity.ok()
        .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=orders.csv")
        .body(new ByteArrayResource(csv.getBytes()));
}
```

---

## Testing REST APIs

### MockMvc Tests

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderService orderService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void createOrder_ValidRequest_Returns201() throws Exception {
        // Given
        var request = new OrderCreationRequest(
            UUID.randomUUID(),
            List.of(new OrderItemRequest(UUID.randomUUID(), 2, BigDecimal.TEN)),
            null
        );
        var order = Order.builder().id(UUID.randomUUID()).build();
        when(orderService.create(any())).thenReturn(order);

        // When/Then
        mockMvc.perform(post("/api/v1/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(header().exists("Location"))
            .andExpect(jsonPath("$.id").value(order.getId().toString()));
    }

    @Test
    void createOrder_InvalidRequest_Returns400() throws Exception {
        // Given
        var request = new OrderCreationRequest(null, List.of(), null);

        // When/Then
        mockMvc.perform(post("/api/v1/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.title").value("Validation Failed"))
            .andExpect(jsonPath("$.errors").isArray());
    }

    @Test
    void getOrder_NotFound_Returns404() throws Exception {
        // Given
        UUID id = UUID.randomUUID();
        when(orderService.findById(id)).thenReturn(Optional.empty());

        // When/Then
        mockMvc.perform(get("/api/v1/orders/{id}", id))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.title").value("Resource Not Found"));
    }
}
```

### RestClient Tests

```java
@RestClientTest(OrderClient.class)
class OrderClientTest {

    @Autowired
    private OrderClient orderClient;

    @Autowired
    private MockRestServiceServer server;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void getOrder_Success() throws Exception {
        // Given
        UUID id = UUID.randomUUID();
        Order expected = new Order(id, "PENDING");

        server.expect(requestTo("/orders/" + id))
            .andExpect(method(HttpMethod.GET))
            .andRespond(withSuccess(
                objectMapper.writeValueAsString(expected),
                MediaType.APPLICATION_JSON));

        // When
        Order result = orderClient.getOrder(id);

        // Then
        assertThat(result).isEqualTo(expected);
    }
}
```

---

## Performance Tips

### Response Compression

```yaml
server:
  compression:
    enabled: true
    min-response-size: 1024
    mime-types: application/json,application/xml,text/html
```

### ETags for Caching

```java
@GetMapping("/{id}")
public ResponseEntity<OrderResponse> getOrder(@PathVariable UUID id) {
    Order order = orderService.findById(id).orElseThrow();
    OrderResponse response = OrderResponse.from(order);

    return ResponseEntity.ok()
        .eTag(String.valueOf(order.getVersion()))
        .cacheControl(CacheControl.maxAge(1, TimeUnit.HOURS))
        .body(response);
}
```

### Async Endpoints

```java
@GetMapping("/export")
public CompletableFuture<ResponseEntity<Resource>> exportOrders() {
    return CompletableFuture.supplyAsync(() -> {
        Resource file = orderService.generateExport();
        return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=export.csv")
            .body(file);
    });
}
```
