# Spring Boot 4 / Spring Framework 7 Testing Reference

> Slice tests, bean overrides, and context management for Spring Boot 4.x on Spring Framework 7.x.

---

## Table of Contents

1. [Bean Overrides — @MockitoBean / @MockitoSpyBean / @TestBean](#bean-overrides)
2. [@SpringBootTest — Full Context](#springboottest--full-context)
3. [@DataJpaTest — JPA Slice](#datajpatest--jpa-slice)
4. [@WebMvcTest + MockMvcTester](#webmvctest--mockmvctester)
5. [WebTestClient — Reactive / Full Stack](#webtestclient--reactive--full-stack)
6. [@RestClientTest — HTTP Client Slice](#restclienttest--http-client-slice)
7. [@JsonTest — Serialization Slice](#jsontest--serialization-slice)
8. [Test Context Pausing (SF7)](#test-context-pausing-sf7)
9. [@Nested + SpringExtension DI](#nested--springextension-di)
10. [@ParameterizedClass (JUnit 5.13+)](#parameterizedclass-junit-513)
11. [What's Removed in Spring Boot 4](#whats-removed-in-spring-boot-4)

---

## Bean Overrides

Spring Framework 6.2 promoted bean override annotations from Spring Boot to the framework itself. Spring Boot 4 **removed** the deprecated `@MockBean` / `@SpyBean`.

### 🔴 BLOCKING — Always Use the Framework Annotations

```java
// 🔴 WRONG — removed in Spring Boot 4
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.boot.test.mock.mockito.SpyBean;

// ✅ CORRECT — Spring Framework 7
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;
import org.springframework.test.context.bean.override.convention.TestBean;
```

**Why:** `@MockBean` / `@SpyBean` were Spring Boot extensions duplicating framework concerns. The framework now owns bean overrides natively, so all test slices and `@SpringBootTest` use the same mechanism — and Boot 4 deletes the old types.

### 🟢 @MockitoBean — Replace with a Mockito Mock

```java
@SpringBootTest
class OrderServiceTest {

    @MockitoBean
    private StripeClient stripeClient;  // External boundary — fine to mock

    @Autowired
    private OrderService orderService;

    @Test
    void whenChargeFails_orderIsRejected() {
        when(stripeClient.charge(any())).thenThrow(new StripeException("declined"));

        assertThatThrownBy(() -> orderService.place(order))
            .isInstanceOf(PaymentRejectedException.class);
    }
}
```

### 🟢 @MockitoSpyBean — Spy on the Real Bean

```java
@SpringBootTest
class AuditServiceTest {

    @MockitoSpyBean
    private AuditService auditService;  // Real bean, but verifiable

    @Test
    void shouldAudit() {
        orderService.place(order);
        verify(auditService).log(eq(EventType.ORDER_CREATED), any());
    }
}
```

### 🟢 @TestBean — Replace with a Test-Provided Instance

Use when you want a real (non-mock) implementation, controlled by the test:

```java
@SpringBootTest
class ScheduledJobTest {

    @TestBean
    private Clock clock;

    static Clock clock() {  // Convention: same name + no-arg static method
        return Clock.fixed(Instant.parse("2026-01-15T09:00:00Z"), ZoneOffset.UTC);
    }
}
```

**Why prefer `@TestBean` over `@MockitoBean(answer = …)`:** real instances behave like production code (no `null` returns by default, no mock-leak between methods).

### 🟡 WARNING — Known Differences vs `@MockBean`

`@MockitoBean` is **not** supported on `@Configuration` classes nor on `@Component` classes — only inside test classes. If you migrated and tests fail to start, check that the annotation is on a `@SpringBootTest` / slice test class, not on a config class.

---

## @SpringBootTest — Full Context

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
@AutoConfigureMockMvc
@Testcontainers
class OrderE2ETest {

    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17");

    @Autowired private MockMvcTester mvc;
    @MockitoBean private StripeClient stripe;

    @Test
    void placeOrderReturns201() {
        when(stripe.charge(any())).thenReturn(new ChargeResult("ok", "txn-1"));

        assertThat(mvc.post().uri("/orders").contentType(APPLICATION_JSON).content(json))
            .hasStatus(CREATED)
            .bodyJson().extractingPath("$.id").asString().isNotEmpty();
    }
}
```

Use when the test crosses multiple slices (controller → service → repository → external).

---

## @DataJpaTest — JPA Slice

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = NONE)  // Use real DB via @ServiceConnection
@Testcontainers
class OrderRepositoryTest {

    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17");

    @Autowired private OrderRepository repository;

    @Test
    void findByCustomer_returnsAllCustomerOrders() {
        // Given
        repository.saveAll(List.of(orderFor(customer), orderFor(otherCustomer)));

        // When
        var found = repository.findByCustomerId(customer.getId());

        // Then
        assertThat(found).hasSize(1).allMatch(o -> o.getCustomerId().equals(customer.getId()));
    }
}
```

**Why `replace = NONE` + Testcontainers:** the embedded H2 default produces false greens — H2 silently accepts SQL Postgres rejects (e.g. `STRING_AGG` quirks, `JSONB`, partial indexes). Test against the same engine as production.

---

## @WebMvcTest + MockMvcTester

Spring Framework 7 introduces **`MockMvcTester`** — an AssertJ-native fluent API that supersedes the Hamcrest-style `MockMvc` for new tests.

### 🟢 Default — MockMvcTester

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired private MockMvcTester mvc;
    @MockitoBean private OrderService orderService;

    @Test
    void getOrder_whenFound_returns200() {
        when(orderService.findById(orderId)).thenReturn(Optional.of(order));

        assertThat(mvc.get().uri("/orders/{id}", orderId))
            .hasStatusOk()
            .hasContentType(APPLICATION_JSON)
            .bodyJson()
            .extractingPath("$.status").isEqualTo("CREATED");
    }

    @Test
    void getOrder_whenMissing_returns404() {
        when(orderService.findById(orderId)).thenReturn(Optional.empty());

        assertThat(mvc.get().uri("/orders/{id}", orderId))
            .hasStatus(NOT_FOUND);
    }
}
```

### 🟡 Behavioural Difference vs MockMvc

`MockMvcTester` does **not** throw unresolved exceptions directly — they surface on the `MvcTestResult`. If a controller test passes unexpectedly, check `assertThat(result).hasFailed().failure().hasRootCauseInstanceOf(...)` rather than wrapping the call in a try/catch.

---

## WebTestClient — Reactive / Full Stack

For WebFlux endpoints or Servlet apps tested over a real port:

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
class OrderApiTest {

    @Autowired private WebTestClient client;

    @Test
    void postOrder_returns201() {
        client.post().uri("/orders")
            .contentType(APPLICATION_JSON)
            .bodyValue(request)
            .exchange()
            .expectStatus().isCreated()
            .expectBody()
            .jsonPath("$.id").isNotEmpty()
            .jsonPath("$.status").isEqualTo("CREATED");
    }
}
```

---

## @RestClientTest — HTTP Client Slice

For testing a Spring `RestClient`, `WebClient`, or `@HttpExchange` interface in isolation, with `MockRestServiceServer`:

```java
@RestClientTest(StripeClient.class)
class StripeClientTest {

    @Autowired private StripeClient client;
    @Autowired private MockRestServiceServer server;

    @Test
    void charge_postsExpectedPayload() {
        server.expect(requestTo("/v1/charges"))
            .andExpect(method(POST))
            .andExpect(jsonPath("$.amount").value(2500))
            .andRespond(withSuccess(stripeJson, APPLICATION_JSON));

        var result = client.charge(new ChargeRequest("usd", 2500, "tok_visa"));

        assertThat(result.id()).isEqualTo("ch_123");
        server.verify();
    }
}
```

---

## @JsonTest — Serialization Slice

Validate Jackson `ObjectMapper` configuration without booting the full app:

```java
@JsonTest
class OrderJsonTest {

    @Autowired private JacksonTester<Order> json;

    @Test
    void serializeMoneyAsString() throws Exception {
        var order = new Order(id, Money.of("99.99", "EUR"));

        assertThat(json.write(order))
            .extractingJsonPathStringValue("$.amount").isEqualTo("99.99");
    }
}
```

---

## Test Context Pausing (SF7)

Spring Framework 7 automatically **pauses** cached `ApplicationContext`s when no test is using them and resumes them on demand. Components implementing `Lifecycle` / `SmartLifecycle` enter a stopped state during the pause.

### 🟡 WARNING — `Lifecycle` beans must be idempotent on stop/start

```java
// 🔴 WRONG — start() opens a new connection, stop() never closes the previous one
@Component
public class KafkaListener implements Lifecycle {
    public void start() { connection = newConnection(); }
    public void stop()  { /* leak — connection field never cleared */ }
}

// ✅ CORRECT — clean stop, idempotent restart
@Component
public class KafkaListener implements Lifecycle {
    public void start() { if (connection == null) connection = newConnection(); }
    public void stop()  { if (connection != null) { connection.close(); connection = null; } }
}
```

**Why:** with context pausing, tests now drive the `Lifecycle` callbacks during a run. Resource leaks that used to surface only at shutdown now appear mid-suite.

---

## @Nested + SpringExtension DI

Spring Framework 7 lets `@Nested` test classes share the same `ApplicationContext` as the outer class and receive **constructor / field injection** consistently.

```java
@SpringBootTest
class OrderServiceTest {

    @Autowired OrderService orderService;

    @Nested
    class WhenCustomerIsLoyal {
        @Autowired LoyaltyService loyalty;  // 7+: works in @Nested

        @Test void appliesDiscount() { /* ... */ }
    }
}
```

---

## @ParameterizedClass (JUnit 5.13+)

Parameterise the **whole class** instead of a single method — useful when many tests share the same parameters:

```java
@ParameterizedClass
@CsvSource({
    "USD, 2500, $25.00",
    "EUR, 2500, €25.00",
    "JPY, 2500, ¥2500"
})
class MoneyFormatterTest {

    @Parameter(0) String currency;
    @Parameter(1) long minorUnits;
    @Parameter(2) String expected;

    @Test void format() {
        assertThat(formatter.format(Money.of(currency, minorUnits))).isEqualTo(expected);
    }

    @Test void parseRoundTrip() {
        assertThat(formatter.parse(expected)).isEqualTo(Money.of(currency, minorUnits));
    }
}
```

---

## What's Removed in Spring Boot 4

| Removed in Boot 4 | Replacement |
|---|---|
| `@MockBean` | `@MockitoBean` (`org.springframework.test.context.bean.override.mockito`) |
| `@SpyBean` | `@MockitoSpyBean` |
| `MockMvcResultMatchers` only style | `MockMvcTester` (AssertJ fluent — kept compatible) |
| Embedded H2 as auto-default for `@DataJpaTest` | Use `@ServiceConnection` + Testcontainers |
| `@DynamicPropertySource` for connection details | `@ServiceConnection` |
| `spring.dao.exceptiontranslation.enabled` | `spring.persistence.exceptiontranslation.enabled` |

OpenRewrite recipe: `org.openrewrite.java.spring.boot4.ReplaceMockBeanAndSpyBean` migrates `@MockBean` / `@SpyBean` automatically.
