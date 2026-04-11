# Security Fundamentals Reference

## OWASP Top 10 (2025)

| # | Risk | Prevention |
|---|------|------------|
| A01 | Broken Access Control | Deny by default, enforce ownership, disable directory listing |
| A02 | Cryptographic Failures | Use strong algorithms (AES-256, RSA-2048+), secure key storage |
| A03 | Injection | Parameterized queries, input validation, output encoding |
| A04 | Insecure Design | Threat modeling, secure design patterns, defense in depth |
| A05 | Security Misconfiguration | Hardened configs, remove defaults, automated verification |
| A06 | Vulnerable Components | Dependency scanning, patch management, SBOM |
| A07 | Auth & Session Failures | MFA, secure session management, password policies |
| A08 | Software Integrity | Code signing, CI/CD security, dependency verification |
| A09 | Logging & Monitoring | Audit logs, alerting, incident response |
| A10 | SSRF | URL validation, allowlisting, network segmentation |

---

## Security Principles

### Defense in Depth

Multiple layers of security controls:

```
[User] → [WAF] → [Load Balancer] → [API Gateway] → [App] → [Database]
           ↓           ↓                ↓            ↓          ↓
        DDoS      Rate Limit        Auth/AuthZ   Validation  Encryption
```

### Least Privilege

Grant minimum permissions required:

```java
// 🔴 WRONG - Overly permissive
@PreAuthorize("isAuthenticated()")
public void deleteAnyUser(UUID id) { }

// ✅ CORRECT - Specific permission
@PreAuthorize("hasAuthority('ADMIN') or #id == authentication.principal.id")
public void deleteUser(UUID id) { }
```

### Fail Secure

Default to secure state on failure:

```java
// 🔴 WRONG - Fails open
public boolean isAuthorized(User user) {
    try {
        return authService.check(user);
    } catch (Exception e) {
        return true;  // Dangerous!
    }
}

// ✅ CORRECT - Fails closed
public boolean isAuthorized(User user) {
    try {
        return authService.check(user);
    } catch (Exception e) {
        log.error("Auth check failed", e);
        return false;  // Deny on error
    }
}
```

### Zero Trust

Never trust, always verify:

- Verify every request (even internal)
- Validate all input regardless of source
- Encrypt data in transit and at rest
- Use short-lived credentials

---

## Input Validation

### Allowlist vs Denylist

```java
// 🔴 WRONG - Denylist (blocklist) - Easy to bypass
public boolean isValid(String input) {
    return !input.contains("<script>") && !input.contains("DROP TABLE");
}

// ✅ CORRECT - Allowlist - Define what IS allowed
private static final Pattern VALID_NAME = Pattern.compile("^[a-zA-Z0-9\\s-]{1,100}$");

public boolean isValid(String input) {
    return VALID_NAME.matcher(input).matches();
}
```

### Validation Layers

| Layer | What to Validate |
|-------|------------------|
| Client | UX feedback (never trust!) |
| Controller | Format, size, required fields |
| Service | Business rules, permissions |
| Repository | Parameterized queries |

### Common Validation Patterns

```java
// Email
Pattern.compile("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$");

// UUID
Pattern.compile("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$");

// Phone (E.164)
Pattern.compile("^\\+[1-9]\\d{1,14}$");

// URL (safe protocols only)
Pattern.compile("^https://[a-zA-Z0-9.-]+(/.*)?$");
```

---

## Output Encoding

### Context-Specific Encoding

| Context | Encoding | Example |
|---------|----------|---------|
| HTML body | HTML entity | `<` → `&lt;` |
| HTML attribute | HTML entity + quotes | `"` → `&quot;` |
| JavaScript | JS escape | `'` → `\'` |
| URL parameter | URL encode | `&` → `%26` |
| CSS | CSS escape | `\` → `\\` |

### OWASP Encoder Usage

```java
import org.owasp.encoder.Encode;

// HTML context
String safe = Encode.forHtml(userInput);

// HTML attribute
String attr = Encode.forHtmlAttribute(userInput);

// JavaScript
String js = Encode.forJavaScript(userInput);

// URL parameter
String url = Encode.forUriComponent(userInput);
```

---

## Secrets Management

### What Counts as a Secret?

- API keys and tokens
- Database credentials
- Encryption keys
- OAuth client secrets
- JWT signing keys
- Private certificates
- Third-party service credentials

### Storage Hierarchy (Best to Worst)

| Method | Security | Use Case |
|--------|----------|----------|
| HSM (Hardware Security Module) | Highest | Signing keys, PKI |
| Cloud KMS (AWS, Azure, GCP) | High | Production secrets |
| HashiCorp Vault | High | Self-hosted secrets |
| Environment variables | Medium | CI/CD, containers |
| Encrypted config files | Medium | Legacy systems |
| Plain text config | None | Never use! |

### Environment Variables

```bash
# .env (gitignored)
DATABASE_PASSWORD=secret123
JWT_SECRET=long-random-string

# docker-compose.yml
services:
  app:
    environment:
      - DATABASE_PASSWORD
    env_file:
      - .env
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  database-password: c2VjcmV0MTIz  # base64 encoded
```

---

## Security Headers

### Essential Headers

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0  # Deprecated, use CSP instead
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=()
```

### Spring Security Headers

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .headers(headers -> headers
            .contentSecurityPolicy(csp ->
                csp.policyDirectives("default-src 'self'"))
            .frameOptions(frame -> frame.deny())
            .httpStrictTransportSecurity(hsts ->
                hsts.maxAgeInSeconds(31536000).includeSubDomains(true)))
        .build();
}
```

---

## Logging Security Events

### What to Log

| Event | Priority | Details to Include |
|-------|----------|-------------------|
| Authentication success/failure | High | Username, IP, user-agent |
| Authorization denied | High | User, resource, action |
| Password change | High | User, timestamp |
| Privilege escalation | Critical | User, old/new roles |
| Sensitive data access | High | User, resource type |
| Configuration change | Medium | User, what changed |

### What NOT to Log

- Passwords (even failed attempts)
- Full credit card numbers
- Social security numbers
- Session tokens
- API keys
- Personal health information

### Structured Security Logging

```java
import net.logstash.logback.argument.StructuredArguments;

log.info("Authentication failed",
    StructuredArguments.kv("event", "auth_failure"),
    StructuredArguments.kv("username", username),
    StructuredArguments.kv("ip", request.getRemoteAddr()),
    StructuredArguments.kv("reason", "invalid_password"));
```

---

## SSRF Prevention (A10)

### Validate User-Provided URLs

```java
// 🔴 WRONG - Direct use of user-provided URL
@PostMapping("/api/fetch")
public ResponseEntity<String> fetchUrl(@RequestBody FetchRequest request) {
    RestClient client = RestClient.create();
    return client.get()
        .uri(request.url()) // User controls URL - SSRF vulnerability!
        .retrieve()
        .body(String.class);
}

// ✅ CORRECT - Allowlist validation
@PostMapping("/api/fetch")
public ResponseEntity<String> fetchUrl(@RequestBody FetchRequest request) {
    if (!isAllowedUrl(request.url())) {
        throw new BadRequestException("URL not allowed");
    }
    RestClient client = RestClient.create();
    return client.get()
        .uri(request.url())
        .retrieve()
        .body(String.class);
}

private boolean isAllowedUrl(String url) {
    try {
        URI uri = new URI(url);
        if (!"https".equals(uri.getScheme())) {
            return false;
        }
        String host = uri.getHost();
        return ALLOWED_HOSTS.contains(host);
    } catch (URISyntaxException e) {
        return false;
    }
}

private static final Set<String> ALLOWED_HOSTS = Set.of(
    "api.stripe.com",
    "api.example.com"
);
```

### Block Internal IPs

```java
private boolean isInternalIP(String host) {
    try {
        InetAddress address = InetAddress.getByName(host);
        if (address.isLoopbackAddress()) return true;   // 127.0.0.1, ::1
        if (address.isSiteLocalAddress()) return true;   // 10.x, 192.168.x, 172.16-31.x
        if (address.isLinkLocalAddress()) return true;   // 169.254.x.x
        if (address.isMulticastAddress()) return true;
        return false;
    } catch (UnknownHostException e) {
        return true; // Fail closed
    }
}
```

### URL Parsing Bypasses

```java
// 🔴 WRONG - Vulnerable to bypasses
if (url.startsWith("https://api.example.com")) {
    // Bypass: https://api.example.com@attacker.com
    // Bypass: https://api.example.com.attacker.com
}

// ✅ CORRECT - Parse and validate
URI uri = new URI(url);
if (!"https".equals(uri.getScheme()) ||
    !"api.example.com".equals(uri.getHost())) {
    throw new BadRequestException("Invalid URL");
}
```

### DNS Rebinding

**Problem:** Attacker domain resolves to public IP at validation, then internal IP at request.

**Mitigation:**
- Re-validate URL just before making request
- Use short DNS cache TTL
- Block internal IPs at network level (firewall)

### Network Segmentation

```
Internet → Load Balancer → Application Servers (DMZ)
                               ↓ (restricted)
                        Internal Services (Private Network)
                               ↓ (restricted)
                           Databases (Isolated)
```

Application servers should NOT have direct access to:
- Internal admin panels
- Databases (use service layer)
- Cloud metadata endpoints (169.254.169.254)

---

## Threat Modeling (STRIDE)

### STRIDE Framework

| Threat | Example | Mitigation |
|--------|---------|------------|
| **Spoofing** | Attacker pretends to be another user | Strong authentication (MFA, JWT) |
| **Tampering** | Modifying data in transit | HTTPS, digital signatures |
| **Repudiation** | User denies action | Audit logging, non-repudiation |
| **Information Disclosure** | Exposing sensitive data | Encryption, access control |
| **Denial of Service** | Overwhelming system | Rate limiting, input validation |
| **Elevation of Privilege** | Gaining unauthorized access | Authorization checks, least privilege |

### Defense in Depth Example

```java
@RestController
@RequestMapping("/api/orders")
public class OrderController {

    @PostMapping
    @PreAuthorize("hasRole('CUSTOMER')") // Layer 1: Role check
    public ResponseEntity<OrderResponse> createOrder(
        @Valid @RequestBody OrderCreationRequest request, // Layer 2: Input validation
        Authentication auth
    ) {
        // Layer 3: Business logic validation
        if (!orderService.canUserCreateOrder(auth.getName(), request)) {
            throw new ForbiddenException("User cannot create order");
        }
        // Layer 4: Rate limiting (via filter/interceptor)
        return ResponseEntity.ok(orderService.create(request, auth.getName()));
    }
}
```

### Secure Design Patterns

**Fail Securely:**
```java
// ✅ Deny on error
public boolean hasAccess(User user, Resource resource) {
    try {
        return accessControlService.checkPermission(user, resource);
    } catch (Exception e) {
        logger.error("Access check failed", e);
        return false;
    }
}
```

**Avoid Security by Obscurity:**
```java
// 🔴 WRONG - Hiding instead of securing
@GetMapping("/api/secret-admin-panel-xyz123")
public String adminPanel() { ... }

// ✅ CORRECT - Proper authorization
@GetMapping("/api/admin")
@PreAuthorize("hasRole('ADMIN')")
public String adminPanel(Authentication auth) { ... }
```

---

## Audit Logging

### Structured Security Logging

```java
@Component
public class SecurityAuditLogger {
    private static final Logger logger = LoggerFactory.getLogger("SECURITY_AUDIT");

    public void logAuthenticationSuccess(String username, String ipAddress) {
        logger.info("Authentication successful",
            kv("event", "auth_success"),
            kv("username", username),
            kv("ip", ipAddress),
            kv("timestamp", Instant.now())
        );
    }

    public void logAuthenticationFailure(String username, String ipAddress, String reason) {
        logger.warn("Authentication failed",
            kv("event", "auth_failure"),
            kv("username", username),
            kv("ip", ipAddress),
            kv("reason", reason),
            kv("timestamp", Instant.now())
        );
    }

    public void logAuthorizationFailure(String username, String resource, String action) {
        logger.warn("Authorization denied",
            kv("event", "authz_failure"),
            kv("username", username),
            kv("resource", resource),
            kv("action", action),
            kv("timestamp", Instant.now())
        );
    }
}
```

### Centralized Logging with AOP

```java
@Aspect
@Component
public class SecurityLoggingAspect {

    @AfterThrowing(
        pointcut = "@annotation(preAuthorize)",
        throwing = "ex"
    )
    public void logAuthorizationFailure(
        JoinPoint joinPoint,
        PreAuthorize preAuthorize,
        AccessDeniedException ex
    ) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        auditLogger.logAuthorizationFailure(
            auth.getName(),
            joinPoint.getSignature().toString(),
            ex.getMessage()
        );
    }
}
```

### Log Retention

| Log Type | Retention | Reason |
|----------|-----------|--------|
| Authentication events | 90 days | Detect brute force attacks |
| Authorization failures | 90 days | Detect privilege escalation |
| Admin operations | 1 year | Compliance, forensics |
| Session logs | 30 days | Debug issues |
| Application errors | 30 days | Debug issues |

---

## Rate Limiting

### Why Rate Limit?

- Prevent brute force attacks
- Mitigate DoS attacks
- Control API costs
- Fair resource allocation

### Rate Limit Strategies

| Strategy | Use Case |
|----------|----------|
| Per IP | Anonymous endpoints |
| Per User | Authenticated APIs |
| Per API Key | Third-party integrations |
| Sliding Window | Most common, smooth limits |
| Token Bucket | Allows bursts |

### Spring Boot Implementation

```java
// Using Bucket4j
@Bean
public Bucket bucket() {
    return Bucket.builder()
        .addLimit(Bandwidth.classic(100, Refill.greedy(100, Duration.ofMinutes(1))))
        .build();
}

// Rate limit filter
@Component
public class RateLimitFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(...) {
        if (bucket.tryConsume(1)) {
            filterChain.doFilter(request, response);
        } else {
            response.setStatus(429);
            response.getWriter().write("Rate limit exceeded");
        }
    }
}
```

---

## Dependency Security

### OWASP Dependency-Check

```xml
<plugin>
    <groupId>org.owasp</groupId>
    <artifactId>dependency-check-maven</artifactId>
    <version>9.0.0</version>
    <configuration>
        <failBuildOnCVSS>7</failBuildOnCVSS>
    </configuration>
</plugin>
```

### CI Pipeline Integration

```yaml
# GitHub Actions
- name: OWASP Dependency Check
  uses: dependency-check/Dependency-Check_Action@main
  with:
    path: '.'
    format: 'HTML'
    args: '--failOnCVSS 7'
```

### Keeping Dependencies Updated

```xml
<!-- Maven Versions Plugin -->
<plugin>
    <groupId>org.codehaus.mojo</groupId>
    <artifactId>versions-maven-plugin</artifactId>
    <version>2.16.2</version>
</plugin>
```

```bash
# Check for updates
mvn versions:display-dependency-updates
mvn versions:display-plugin-updates
```
