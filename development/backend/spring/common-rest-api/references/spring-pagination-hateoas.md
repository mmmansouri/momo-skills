# Spring Pagination, HATEOAS & Performance

## Table of Contents

1. [Pagination](#pagination) — Spring Data `Pageable`, custom `PageResponse`, cursor-based
2. [HATEOAS with Spring](#hateoas-with-spring) — `EntityModel`, `CollectionModel`, `PagedModel`
3. [Performance Tips](#performance-tips) — compression, ETag caching, async endpoints

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
