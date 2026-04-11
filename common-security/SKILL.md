---
name: common-security
description: >-
  Application security best practices for web applications. Use when: preventing
  OWASP Top 10 vulnerabilities (injection, XSS, CSRF), implementing authentication
  (JWT, OAuth2, MFA), configuring authorization (RBAC), hashing passwords (BCrypt,
  Argon2), securing APIs, or configuring Spring Security 7 / Spring Boot 4.
---

# Security Developer Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## When Preventing Injection Attacks

📚 **References:** [security-fundamentals.md](references/security-fundamentals.md), [java-security.md](references/java-security.md)

### 🔴 SQL Injection Prevention

```java
// 🔴 WRONG - String concatenation
String query = "SELECT * FROM users WHERE email = '" + email + "'";

// ✅ CORRECT - Parameterized query
@Query("SELECT u FROM User u WHERE u.email = :email")
User findByEmail(@Param("email") String email);
```

### 🔴 Command Injection Prevention

```java
// 🔴 WRONG - Shell command with user input
Runtime.getRuntime().exec("ping " + hostname);

// ✅ CORRECT - Use Java API
InetAddress.getByName(hostname).isReachable(5000);
```

### 🔴 XSS Prevention

- Use strict allowlist input validation
- Limit input size (50 chars when feasible)
- Use OWASP Java Encoder for output escaping

### 🔴 Log Injection Prevention

```java
// 🔴 WRONG
logger.info("Login failed for user: " + username);

// ✅ CORRECT - Parameterized logging
logger.info("Login failed for user: {}", username);
```

---

## When Validating Input

📚 **References:** [security-fundamentals.md](references/security-fundamentals.md)

### 🔴 Always Validate Untrusted Data

- Validate early (at API entry points)
- Re-validate before security-sensitive operations
- Use allowlist (not denylist) approach
- Never trust: user input, external APIs, deserialized objects, file uploads

### 🟡 Size Limits for DoS Prevention

- Limit decompressed size, not compressed
- Check without integer overflow: `current > max - extra` (not `current + extra > max`)

---

## When Handling Passwords

📚 **References:** [java-security.md](references/java-security.md), [spring-security.md](references/spring-security.md)

### 🔴 Use Strong Hashing Algorithms

| Algorithm | Recommendation | OWASP Minimum Parameters |
|-----------|----------------|--------------------------|
| **Argon2id** | Preferred (OWASP 2025) | 19 MiB memory, 2 iterations, 1 parallelism |
| **BCrypt** | Good default | Work factor 10+ (72-byte password limit) |
| **PBKDF2** | FIPS-140 compliant | 600,000+ iterations with HMAC-SHA-256 |

### 🟢 Spring Security Configuration

```java
// ✅ Argon2 (recommended for new apps)
@Bean
public PasswordEncoder passwordEncoder() {
    return new Argon2PasswordEncoder(16, 32, 1, 19456, 2);
}
```

---

## When Implementing Authentication

📚 **References:** [spring-security.md](references/spring-security.md) — JWT Resource Server, OAuth2, MFA, UserDetailsService

### 🔴 JWT Best Practices

| Rule | Why |
|------|-----|
| Short-lived tokens (15 min max) | Limits exposure window |
| Secure refresh token storage | HTTP-only cookies preferred |
| Validate signature, iss, aud, exp | Prevents token manipulation |
| Use asymmetric keys (RS256/ES256) | Enables key rotation |

### 🟢 Stateful vs Stateless

| Use Case | Recommendation |
|----------|----------------|
| Monolith web app | Session-based (simpler) |
| Microservices/APIs | JWT/OAuth2 (scalable) |
| Mobile apps | JWT with refresh tokens |

---

## When Implementing Authorization

📚 **References:** [spring-security.md](references/spring-security.md) — Method security, custom AuthorizationManager, URL-based auth

### 🔴 Method Security

```java
@PreAuthorize("hasRole('ADMIN')")
public void deleteUser(UUID id) { }

@PreAuthorize("#order.customerId == authentication.principal.id")
public void cancelOrder(Order order) { }
```

### 🟡 Spring Security 7 Migration Notes

```java
// 🔴 REMOVED in Spring Security 7
http.authorizeRequests()...  // Use authorizeHttpRequests()
http.csrf().and()...         // Use lambda DSL
new AntPathRequestMatcher()  // Use PathPatternRequestMatcher
```

---

## When Designing Secure Features (A04 - Insecure Design)

📚 **References:** [security-fundamentals.md](references/security-fundamentals.md#threat-modeling) — STRIDE framework, Defense in Depth examples

### 🔴 BLOCKING

- **Identify threats before coding** → Use STRIDE (Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation)
- **Fail closed** → Deny access on errors or unexpected states
- **Defense in depth** → Multiple security layers (URL auth + method auth + business validation)
- **No security by obscurity** → Proper auth/authz, not hidden URLs

### 🟢 Principle of Least Privilege

- Grant minimum permissions needed, use RBAC, time-limited when possible

---

## When Configuring CORS & CSRF

📚 **References:** [spring-security.md](references/spring-security.md) — Full CORS config, SPA CSRF, cookie-based CSRF

### 🔴 CORS Must Process Before Security

- Configure via `cors(cors -> cors.configurationSource(...))` in SecurityFilterChain
- Use specific origins (never `*` in production with credentials)
- Set `allowCredentials(true)` + `maxAge(3600L)`

### 🟡 CSRF Decision Matrix

| App Type | Session | CSRF |
|----------|---------|------|
| Traditional web (Thymeleaf) | Yes | **Enable** |
| SPA + session cookies | Yes | **Enable** (`csrf.spa()`) |
| REST API + JWT | No | Disable |
| Mobile backend + JWT | No | Disable |

---

## When Managing Secrets

📚 **References:** [security-fundamentals.md](references/security-fundamentals.md)

### 🔴 Never Hardcode Secrets

```java
// 🔴 WRONG
private static final String API_KEY = "sk-abc123...";

// ✅ CORRECT - Spring externalized config
@Value("${app.api-key}")
private String apiKey;
```

### 🔴 Secrets Management

| Environment | Solution |
|-------------|----------|
| Development | `.env` files (gitignored) |
| CI/CD | Pipeline secrets (GitHub, GitLab) |
| Production | Vault, AWS Secrets Manager, Azure Key Vault |

---

## When Securing Spring Boot Actuator

📚 **References:** [spring-security.md](references/spring-security.md) — Full actuator security chain, YAML config

### 🔴 Protect Sensitive Endpoints

- `health`, `info` → `permitAll()`
- `metrics`, `prometheus` → `hasRole("METRICS")`
- Everything else → `hasRole("ACTUATOR")`
- Use separate `@Order(1)` SecurityFilterChain with `EndpointRequest` matcher

---

## When Using Cryptography

📚 **References:** [java-security.md](references/java-security.md) — AES-GCM, RSA, Digital Signatures, Secure Random

### 🔴 BLOCKING
- **Never write your own crypto** → Use Google Tink, Bouncy Castle, or JCA/JCE
- **Use AES-GCM** for symmetric encryption (12-byte nonce, unique per encryption)
- **Use RSA-4096 or Ed25519** for asymmetric keys
- **Never store keys in code or config** → Use KMS, rotate regularly

---

## When Making Server-Side HTTP Calls (A10 - SSRF Prevention)

📚 **References:** [security-fundamentals.md](references/security-fundamentals.md#ssrf-prevention-a10) — Full code examples, URL parsing bypasses, DNS rebinding

### 🔴 BLOCKING
- **Validate user-provided URLs** against an allowlist of domains
- **Block internal IPs** (loopback, private ranges, link-local, multicast)
- **Use HTTPS only** for outbound requests
- **Fail closed** → Unknown host = reject

---

## When Handling Serialization

📚 **References:** [java-security.md](references/java-security.md#serialization-security)

### 🔴 BLOCKING
- **Avoid Java serialization** → Use JSON with `ObjectMapper`
- If required: use `ObjectInputFilter` (Java 9+) with depth/size/class limits

---

## When Handling Errors

📚 **References:** [security-fundamentals.md](references/security-fundamentals.md)

### 🔴 Never Expose Internal Details

```java
// 🔴 WRONG - Exposes stack trace
return ResponseEntity.status(500).body(e.getMessage());

// ✅ CORRECT - Generic message, log details
log.error("Internal error", e);
return ResponseEntity.status(500).body(Map.of("error", "An unexpected error occurred"));
```

---

## When Implementing Security Logging (A09)

📚 **References:** [security-fundamentals.md](references/security-fundamentals.md#audit-logging) — Structured logging examples, AOP aspect, log retention

### 🔴 What to Log
- Authentication attempts (success/failure), authorization failures, input validation failures
- Password changes, MFA enrollment, admin operations, API rate limit hits

### 🔴 What to NEVER Log
- Passwords (plaintext or hashed), session tokens, JWTs, API keys, credit card numbers, PII

### 🟢 Use structured logging with context (JSON key-value pairs, not free text)

---

## When Keeping Dependencies Secure

📚 **References:** [security-fundamentals.md](references/security-fundamentals.md)

### 🔴 Scan for Vulnerabilities

| Tool | Purpose |
|------|---------|
| OWASP Dependency-Check | CVE scanning |
| Snyk | Real-time vulnerability alerts |
| Trivy | Container image scanning |
| Dependabot | Automated dependency updates |

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] No SQL/command/XSS injection vectors
- [ ] Parameterized queries used everywhere
- [ ] Passwords hashed with BCrypt/Argon2 (not MD5/SHA1)
- [ ] No secrets in code or config files
- [ ] Input validated at trust boundaries
- [ ] Authentication required for sensitive endpoints
- [ ] Authorization checks on protected resources
- [ ] Threat modeling completed for new features (A04)
- [ ] User-provided URLs validated against allowlist (A10)

### 🟡 WARNING
- [ ] CSRF enabled for session-based auth
- [ ] CORS configured with specific origins (not `*`)
- [ ] Actuator endpoints protected
- [ ] Error messages don't expose internals
- [ ] Logging doesn't contain sensitive data

### 🟢 BEST PRACTICE
- [ ] JWT tokens short-lived (15 min)
- [ ] Dependency vulnerability scan in CI
- [ ] Security headers configured (CSP, X-Frame-Options)
- [ ] Rate limiting on authentication endpoints
- [ ] Structured logging with context (JSON)

---

## Related Skills

- `common-java-developer` — Secure coding patterns
- `common-rest-api` — REST API security
- `common-architecture` — Security architecture design
- `buy-nature-backend-coding-guide` — Buy Nature security implementation
