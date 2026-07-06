# Spring OpenAPI Documentation & Testing

## Table of Contents

1. [API Documentation (OpenAPI)](#api-documentation-openapi) — Springdoc setup
2. [Global Configuration](#global-configuration) — `OpenAPI` bean, security schemes
3. [Controller Annotations](#controller-annotations) — `@Operation`, `@ApiResponses`
4. [Schema Annotations](#schema-annotations) — `@Schema` on DTOs
5. [Testing REST APIs](#testing-rest-apis) — MockMvc, `@RestClientTest`

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

## Testing REST APIs

### MockMvc Tests

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
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
