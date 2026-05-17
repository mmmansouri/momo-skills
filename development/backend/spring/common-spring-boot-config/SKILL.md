---
name: common-spring-boot-config
description: >-
  Spring Boot 4 / Spring Framework 7 application configuration pitfalls and best
  practices (YAML structure, profiles, AOP proxy ordering, Resilience4j retries,
  @ConditionalOnProperty scope). Use whenever the user mentions application.yml,
  Spring profiles, @Async / @Retry / @Transactional / @Cacheable annotations,
  Resilience4j, conditional beans, or debugging "BeanCreationException" /
  "config silently overridden" / "@Async ignored" / "retry never fires" issues,
  or when reviewing a PR touching `application*.yml`, profiles, `@Async`/`@Retry`/
  `@Transactional`/`@Cacheable` annotations, or Resilience4j config — even when
  they don't explicitly say "Spring config". Do NOT use for runtime
  REST behavior (use common-rest-api), Spring Security (use common-security), or
  JPA configuration (use common-java-jpa).
---

# Spring Boot Configuration Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

This skill covers Spring Boot **configuration-time** pitfalls — the subtle
failure modes where the application boots but behaves silently wrong (overridden
YAML keys, ignored AOP annotations, retries that never trigger, beans missing
when a feature flag flips).

📚 **When debugging any of the pitfalls below, or reviewing a Spring Boot
configuration file or AOP-annotated bean → read [spring-boot-config-pitfalls.md](references/spring-boot-config-pitfalls.md).**

---

## When Writing application.yml / application-{profile}.yml

### 🔴 BLOCKING — No duplicate root keys in a single YAML file

Each root key (`spring:`, `server:`, `management:`, etc.) must appear **only once** per file. Duplicates silently override the first block.

**Why** : YAML 1.2 spec resolves duplicate mapping keys by keeping the last occurrence; the entire first block is discarded with no warning. A `spring.datasource` block followed 200 lines later by another `spring:` block deletes the datasource config — the app fails at runtime with no compile-time signal.

### 🔴 BLOCKING — Production-safe defaults in base config

Every property in base `application.yml` applies to **all profiles, including production**. Dev-friendly defaults (`thymeleaf.cache: false`, test mail servers, debug flags) belong in `application-dev.yml` only.

**Why** : a forgotten `cache: false` in base config silently degrades production performance for the lifetime of the deployment. Profile files are the only place where dev-only behavior cannot leak.

---

## When Stacking AOP Annotations (@Async, @Retry, @Transactional, @Cacheable)

### 🟡 WARNING — Never stack two AOP annotations on the same method

Each annotation creates its own proxy layer. Stacking them produces unpredictable proxy ordering. Calling an annotated method from **inside the same class** bypasses the proxy entirely.

**Pattern** : delegate between separate beans — one bean per AOP concern.

```java
// 🔴 WRONG — stacked, ordering undefined
@Async
@Retry(name = "emailRetry")
public void sendEmail(String to) { ... }

// ✅ CORRECT — delegation between beans
@Component
public class AsyncEmailSender {
    private final EmailRetryService retryService;
    @Async
    public void sendEmailAsync(String to) {
        retryService.sendWithRetry(to);
    }
}
```

---

## When Configuring Resilience4j @Retry

### 🟡 WARNING — Catch-and-rethrow inside @Retry defeats the retry

If the retry config targets `MailException` but the method catches `MailException` and rethrows `EmailSendingException`, the proxy never sees a retriable exception and **retries never fire**.

**Rules** :
1. Let retriable exceptions propagate naturally
2. OR list the wrapper exception type in `retryExceptions`
3. Use `fallbackMethod` for final-failure handling, not catch-and-rethrow

### 🟡 WARNING — Never hardcode the retry attempt count in fallback logs

Read the value from `RetryRegistry` at runtime — hardcoded counts go stale when config changes and produce misleading alerts.

---

## When Using @ConditionalOnProperty

### 🔴 BLOCKING — Guard the entire dependency chain, not just the @Configuration

If the `@Configuration` class is conditional but the `@Service` that depends on its beans is not, component scanning still creates the service → `BeanCreationException` when the property is disabled.

**Why** : `@Configuration` classes and `@Service` classes are independent component-scan candidates. Guarding only one breaks the chain. Repeat the same `@ConditionalOnProperty` on every bean in the feature, or use `@ConditionalOnBean` on dependents.

```java
// ✅ CORRECT — every bean in the feature is guarded
@Configuration
@ConditionalOnProperty(prefix = "app.email", name = "enabled", havingValue = "true")
public class EmailConfig { ... }

@Service
@ConditionalOnProperty(prefix = "app.email", name = "enabled", havingValue = "true")
public class EmailService { ... }
```

**Test rule** : boot the app with the property disabled and confirm no missing-bean errors.

---

## When Reviewing Configuration Files

### 🟢 No unused YAML properties

Every property must be referenced by `@Value`, `@ConfigurationProperties`, or Spring auto-config. Dead properties suggest features are wired when they are not.

### 🟢 No orphan template files

Every Thymeleaf/Freemarker template must be referenced from a controller or service.

### 🟡 Comments must reflect actual implementation

A `# i18n-ready` comment with no locale detection, or a `// Cached for performance` line with no `@Cacheable`, misleads reviewers. Track aspirational features in a ticket, not a misleading comment.

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] No duplicate root keys in any `application*.yml` file
- [ ] No dev-only defaults (`cache: false`, test mail servers, debug flags) in base `application.yml`
- [ ] Every bean in a `@ConditionalOnProperty`-guarded feature is itself guarded
- [ ] App boots cleanly with each conditional feature flag in both states (on/off)

### 🟡 WARNING
- [ ] No two AOP annotations (`@Async` + `@Retry`, `@Async` + `@Transactional`, etc.) on the same method
- [ ] No AOP-annotated method called from within its own class (self-invocation bypasses the proxy)
- [ ] No catch-and-rethrow inside a `@Retry`-annotated method (unless the wrapper is in `retryExceptions`)
- [ ] No hardcoded retry counts or timeouts in fallback methods (read from `RetryRegistry`)
- [ ] No misleading comments claiming unimplemented features

### 🟢 BEST PRACTICE
- [ ] No unused YAML properties (every property is referenced in code)
- [ ] No orphan template files

---

## Related Skills

- `common-rest-api` — REST controller design (uses Spring Boot but for the REST surface)
- `common-java-developer` — Modern Java patterns (records, virtual threads, etc.)
- `common-java-jpa` — JPA / Hibernate configuration (separate domain)
- `common-security` — Spring Security configuration
