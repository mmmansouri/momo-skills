# Spring REST Clients & Spring 7 Features

## Table of Contents

1. [What's New in Spring Framework 7 for REST](#whats-new-in-spring-framework-7-for-rest) — key changes
2. [New API Versioning Support](#new-api-versioning-support) — `@ApiVersion`, `ApiVersionConfigurer`
3. [RestClient (Preferred over RestTemplate)](#restclient-preferred-over-resttemplate)
4. [HTTP Interface Clients (Spring Framework 7)](#http-interface-clients-spring-framework-7) — `@HttpExchange`
5. [Virtual Threads for REST Controllers](#virtual-threads-for-rest-controllers)
6. [Comparison: RestTemplate vs RestClient vs HTTP Interface](#comparison-resttemplate-vs-restclient-vs-http-interface)
7. [Migration Path](#migration-path-resttemplate--restclient--httpexchange)

---

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
| **Type Safety** | Weak | Strong | Strong |
| **Error Handling** | Exception-based | Fluent + exceptions | Exception-based |
| **Interceptors** | Yes | Yes | Yes (via RestClient) |
| **Async Support** | No (use WebClient) | No (use WebClient) | No |
| **Status** | Maintenance mode | Preferred | Preferred |
| **Use Case** | Legacy code | New code, fluent API | Interface-driven, clean |

### Migration Path (RestTemplate → RestClient / @HttpExchange)

**Existing (Spring Boot 3.x or earlier):**
- Keep `RestTemplate` in existing services — don't rewrite for the sake of rewriting

**New code (Spring Boot 4.x):**
1. **Simple HTTP calls:** Use `RestClient`
2. **Multiple endpoints, clean interface:** Use `@HttpExchange` clients
3. **Async/reactive:** Use `WebClient`
