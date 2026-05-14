# Spring Controllers & Content Negotiation

## Table of Contents

1. [Controller Design](#controller-design) — `@RestController` skeleton
2. [Controller Best Practices](#controller-best-practices)
3. [Content Negotiation](#content-negotiation) — configuration, multiple representations

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
// DO: Use @RestController for APIs
@RestController  // Combines @Controller + @ResponseBody

// DO: Group related endpoints
@RequestMapping("/api/v1/orders")

// DO: Use proper HTTP methods
@GetMapping     // Read
@PostMapping    // Create
@PutMapping     // Replace
@PatchMapping   // Partial update
@DeleteMapping  // Remove

// DO: Use ResponseEntity for control
public ResponseEntity<OrderResponse> createOrder(...) {
    return ResponseEntity.created(location).body(response);
}

// DO: Use @ResponseStatus for simple cases
@DeleteMapping("/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void deleteOrder(@PathVariable UUID id) { }

// DO: Keep controllers thin
// Business logic belongs in services, not controllers
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
