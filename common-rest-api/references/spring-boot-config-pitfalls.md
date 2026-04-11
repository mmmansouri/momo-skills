# Spring Boot Configuration Pitfalls

---

## 1. YAML Duplicate Root Keys

### Severity: 🔴 BLOCKING

YAML spec: duplicate keys at the same nesting level **silently override**. The LAST occurrence wins.
The entire first block under that key is discarded without warning.

```yaml
# application.yml - BROKEN (datasource config silently lost!)
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/mydb
    username: app

# ... 200 lines later in same file ...

spring:                          # Overrides ENTIRE first spring: block
  mail:
    host: smtp.example.com
# spring.datasource is now GONE - app fails at runtime
```

```yaml
# CORRECT - single root key, all children merged
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/mydb
    username: app
  mail:
    host: smtp.example.com
```

### Detection
- Grep for `^spring:` (or any root key) — must appear only ONCE per file
- IDE YAML plugins warn on duplicate keys (IntelliJ shows a warning)
- CI: `yq` can detect duplicate keys

---

## 2. Spring AOP Proxy Annotation Ordering

### Severity: 🟡 WARNING

Spring AOP annotations (`@Async`, `@Transactional`, `@Retry`, `@Cacheable`) each create a proxy layer.
Stacking multiple AOP annotations on the **same method** creates unpredictable proxy ordering.
Calling an annotated method from **within the same class** bypasses the proxy entirely.

### Combination Rules

| Combination | Safe? | Why |
|-------------|-------|-----|
| `@Transactional` + `@Async` on same method | **NO** | `@Async` runs in new thread; `@Transactional` context is lost |
| `@Retry` + `@Async` on same method | **NO** | Retry wraps the async submission, not the actual execution |
| `@Transactional` on caller + `@Async` on separate bean | YES | Separate proxy beans, clear boundaries |
| `@Retry` on one bean + `@Async` on another | YES | Each annotation on its own bean method |

### Pattern: Delegation Instead of Stacking

```java
// WRONG - Stacking @Async + @Retry on same method
@Async
@Retry(name = "emailRetry")
public void sendEmail(String to, String subject) {
    // Which proxy wraps which? Unpredictable behavior.
}

// CORRECT - Separate concerns into separate beans
@Component
public class AsyncEmailSender {
    private final EmailRetryService retryService;

    @Async
    public void sendEmailAsync(String to, String subject) {
        retryService.sendWithRetry(to, subject);  // Delegate to retry bean
    }
}

@Component
public class EmailRetryService {
    @Retry(name = "emailRetry")
    public void sendWithRetry(String to, String subject) {
        // Actual sending logic — retry handled by Resilience4j proxy
    }
}
```

### Self-Invocation Trap

```java
// WRONG - @Async silently ignored (direct method call bypasses proxy)
@Service
public class OrderService {
    public void processOrder(UUID id) {
        sendNotification(id);  // Direct call, NOT through proxy!
    }

    @Async
    public void sendNotification(UUID id) { ... }  // @Async never activates
}

// CORRECT - Use a separate bean
@Service
public class OrderService {
    private final NotificationService notificationService;

    public void processOrder(UUID id) {
        notificationService.sendAsync(id);  // Through proxy — @Async works
    }
}
```

---

## 3. Resilience4j Retry Exception Configuration

### Severity: 🟡 WARNING

When catch-and-rethrow wraps the original exception in a different type,
Resilience4j retry config targeting the original exception type **never triggers**.

```yaml
# Retry config targets MailException
resilience4j:
  retry:
    instances:
      emailRetry:
        retryExceptions:
          - org.springframework.mail.MailException
```

```java
// WRONG - catch-and-rethrow hides MailException from retry
@Retry(name = "emailRetry")
public void sendEmail(String to) {
    try {
        mailSender.send(message);
    } catch (MailException e) {
        throw new EmailSendingException("Failed to send", e);
        // EmailSendingException NOT in retryExceptions -> retry NEVER triggers
    }
}

// CORRECT - let retriable exceptions propagate naturally
@Retry(name = "emailRetry")
public void sendEmail(String to) {
    mailSender.send(message);  // MailException propagates, Resilience4j retries
}

// CORRECT - use fallback for final failure handling
@Retry(name = "emailRetry", fallbackMethod = "sendEmailFallback")
public void sendEmail(String to) {
    mailSender.send(message);
}

public void sendEmailFallback(String to, MailException e) {
    log.error("Email failed after all retries for: {}", to, e);
    // Queue for later, notify admin, etc.
}
```

### Rules
1. Let retriable exceptions propagate — do not catch-and-wrap before `@Retry` can see them
2. OR configure `retryExceptions` with the WRAPPER exception type
3. Catch-and-rethrow inside a `@Retry` method defeats the retry mechanism

---

## 3B. Hardcoded Retry Attempt Count in Fallback

### Severity: 🟡 WARNING

Fallback methods that hardcode retry attempt counts become stale when configuration changes.
The fallback says "3 attempts" but the actual config may specify 5 — misleading logs and alerts.

```java
// WRONG - Hardcoded retry count in fallback
@Retry(name = "emailRetry", fallbackMethod = "sendEmailFallback")
public void sendEmail(String to) {
    mailSender.send(message);
}

public void sendEmailFallback(String to, Exception e) {
    log.error("Email to {} failed after 3 attempts", to, e);  // Hardcoded 3!
}
```

```java
// CORRECT - Read from Resilience4j configuration
@Component
@RequiredArgsConstructor
public class EmailService {
    private final RetryRegistry retryRegistry;

    @Retry(name = "emailRetry", fallbackMethod = "sendEmailFallback")
    public void sendEmail(String to) {
        mailSender.send(message);
    }

    public void sendEmailFallback(String to, Exception e) {
        int maxAttempts = retryRegistry.retry("emailRetry")
            .getRetryConfig().getMaxAttempts();
        log.error("Email to {} failed after {} attempts", to, maxAttempts, e);
    }
}
```

### Rules
1. Never hardcode values that come from configuration — read them at runtime
2. If `RetryRegistry` is not available, use a `@Value` for the config property
3. This applies to all Resilience4j fallback methods: retry count, timeout duration, circuit breaker thresholds

---

## 4. Spring Profile-Specific Configuration

### Severity: 🟡 WARNING

Properties in base `application.yml` apply to **ALL profiles including production**.
Dev-friendly defaults (cache disabled, debug flags, test mail servers) silently degrade production.

### Rules

| Property Type | Where to Define | Examples |
|---------------|----------------|---------|
| Structural (ports, paths, changelog) | Base `application.yml` | `server.port`, `spring.liquibase.change-log` |
| Dev conveniences | `application-dev.yml` ONLY | `spring.thymeleaf.cache: false` |
| Test config | `application-test.yml` ONLY | `spring.mail.host: smtp.mailtrap.io` |
| Security/secrets | Env vars or secret store | `spring.mail.password`, API keys |
| Feature flags | Profile-specific files | `app.feature.x.enabled` |

```yaml
# WRONG - dev defaults in base config affect production
# application.yml
spring:
  thymeleaf:
    cache: false           # Performance killer in prod!
  mail:
    host: smtp.mailtrap.io # Test server used in prod!

# CORRECT - prod-safe defaults in base, dev overrides in profile
# application.yml
spring:
  thymeleaf:
    cache: true            # Safe default for prod
  mail:
    host: ${MAIL_HOST}     # From environment variable

# application-dev.yml
spring:
  thymeleaf:
    cache: false
  mail:
    host: smtp.mailtrap.io
```

### Review Rule
For every property in base `application.yml`, ask: **"Is this safe for production as-is?"**

---

## 5. Unused Properties and Templates

### Severity: 🟢 BEST PRACTICE

YAML properties defined but never referenced in code, or template files created but never
rendered, create misleading configuration suggesting features are wired when they are not.

### Detection
- Every YAML property should be referenced by `@Value("${...}")`, `@ConfigurationProperties`, or Spring auto-configuration
- Every template file (Thymeleaf, Freemarker) must be referenced in a service or controller
- Search for the property/template name in the codebase — if zero hits, it is dead config

### Rules
1. Remove dead YAML properties before merge
2. Remove orphan template files before merge
3. If a property is intentionally "for future use," add a TODO comment explaining when it will be wired

---

## 6. Incomplete @ConditionalOnProperty Scope

### Severity: 🔴 BLOCKING

When a `@Configuration` class is guarded by `@ConditionalOnProperty` but its dependent `@Service` is NOT,
component scanning still creates the service. The service's `@Autowired` dependencies (defined only in the guarded config) are missing → **runtime BeanCreationException**.

```java
// WRONG - Only config is guarded, service is always created
@Configuration
@ConditionalOnProperty(prefix = "app.email", name = "enabled", havingValue = "true")
public class EmailConfig {
    @Bean
    public JavaMailSender mailSender() { ... }

    @Bean
    public TaskExecutor emailTaskExecutor() { ... }
}

@Service  // Always created by component scanning!
public class EmailService {
    private final JavaMailSender mailSender;      // Missing when email disabled!
    private final TaskExecutor emailTaskExecutor;  // Missing when email disabled!
}
// Result: BeanCreationException when app.email.enabled=false
```

```java
// CORRECT - Guard ALL beans in the feature's dependency chain
@Configuration
@ConditionalOnProperty(prefix = "app.email", name = "enabled", havingValue = "true")
public class EmailConfig {
    @Bean
    public JavaMailSender mailSender() { ... }

    @Bean
    public TaskExecutor emailTaskExecutor() { ... }
}

@Service
@ConditionalOnProperty(prefix = "app.email", name = "enabled", havingValue = "true")
public class EmailService {
    private final JavaMailSender mailSender;
    private final TaskExecutor emailTaskExecutor;
}
// Result: Neither config NOR service created when email disabled
```

### Alternative: Use @ConditionalOnBean

```java
@Service
@ConditionalOnBean(JavaMailSender.class)  // Only created if mailSender bean exists
public class EmailService { ... }
```

### Rules
1. ALL beans in a feature's dependency chain must be guarded by the same condition
2. Prefer repeating `@ConditionalOnProperty` on each bean for explicitness
3. `@ConditionalOnBean` is acceptable but less explicit — harder to trace which property controls it
4. Test with the property disabled to verify no missing bean errors

---

## Pitfall 8: Misleading Comments About Unimplemented Features

### Problem

Comments claiming features exist (i18n support, caching, async processing) when the implementation is absent. These mislead reviewers and future developers into thinking functionality is present.

### Example

```yaml
# 🔴 WRONG - Comment claims i18n-ready, but no locale detection exists
spring:
  mail:
    templates:
      welcome:
        subject: "Welcome to Buy Nature"  # i18n-ready
```

```java
// 🔴 WRONG - Comment claims caching, no @Cacheable anywhere
@Service
public class ProductService {
    // Cached for performance
    public List<Product> findAll() {
        return productRepository.findAll();  // No cache at all!
    }
}
```

### Rule

**Comments must reflect actual implementation, not aspirational features.** If you plan to add i18n/caching/async later, create a Jira ticket instead of a misleading comment.

```yaml
# ✅ CORRECT - No misleading comment
spring:
  mail:
    templates:
      welcome:
        subject: "Welcome to Buy Nature"
```

```java
// ✅ CORRECT - Comment matches reality
@Service
public class ProductService {
    @Cacheable("products")  // Comment matches implementation
    public List<Product> findAll() {
        return productRepository.findAll();
    }
}
```
