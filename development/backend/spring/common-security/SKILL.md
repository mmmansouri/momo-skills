---
name: common-security
description: >-
  Application security guide for Spring Boot 4 / Spring Security 7 (Java 17
  minimum, tested with Java 25) aligned with OWASP Top 10 (2025). Use whenever the user mentions injection
  (SQL, command, XSS, log, XPath, LDAP, XXE), authentication (login, JWT,
  OAuth2, OIDC, MFA, password hashing), authorization (RBAC, @PreAuthorize,
  AccessDeniedException, "403 Forbidden"), CORS / CSRF, secrets management,
  cryptography, SSRF, deserialization, security headers, audit logging,
  rate limiting, dependency CVE scanning, the Spring Security 6 → 7 migration
  (`authorizeHttpRequests`, `PathPatternRequestMatcher`, `csrf.spa()`),
  hardening Spring Boot Actuator, or when reviewing a PR touching auth, JWT,
  crypto, input validation, or security configuration — even when they don't
  explicitly say "security". Do NOT use for infrastructure security (firewalls, WAF, network
  segmentation), penetration testing methodology, or self-hosted Vault setup.
---

# Security Developer Guide

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
>
> **Stack baseline:** Spring Boot 4.x · Spring Framework 7.x · Spring Security 7.x · Java 17 minimum (tested with Java 25) · OWASP Top 10 (2025) · Argon2id (Password4j) preferred for new password hashing. Rules tied to a newer version name their boundary inline (e.g. "REMOVED in Spring Security 7").

---

## Decision Trees

### Authentication Style

```
What kind of client?
│
├── Server-rendered web app (Thymeleaf)?     → Session-based + form login + CSRF on
├── Single-Page App on same domain?          → Session cookie + csrf.spa() + SameSite=Lax
├── REST API consumed by SPA on other domain → JWT (oauth2ResourceServer) + CORS
├── Mobile / native client?                  → JWT + refresh token (HTTP-only cookie when possible)
├── B2B / federated login?                   → OAuth2 / OIDC (oauth2Login)
└── Service-to-service inside the cluster?   → mTLS or signed JWT with short TTL
```

### Password Hashing

```
What's the constraint?
│
├── New application, no FIPS requirement?    → Argon2id (Password4j) — 19 MiB / 2 iter / 1 parallelism
├── Need broad library compatibility?        → BCrypt — work factor 12+
├── FIPS-140 compliance required?            → PBKDF2-HMAC-SHA-256 — 600 000+ iterations
└── Migrating from legacy MD5 / SHA1?        → DelegatingPasswordEncoder + rehash on next login
```

### CSRF

```
What's the session model?
│
├── Stateless JWT API?                       → csrf.disable() (safe — no ambient credentials)
├── SPA with session cookie?                 → csrf.spa() (deferred token, BREACH-safe)
├── Cookie token readable by JS (double-submit)? → CookieCsrfTokenRepository.withHttpOnlyFalse()
└── Server-rendered (Thymeleaf, JSP)?        → CSRF on (default), token in form
```

---

## When Preventing Injection Attacks

### 🔴 BLOCKING — Never concatenate untrusted input into queries, commands, or markup

**Why:** every injection class (SQL, command, XPath, LDAP, XXE, XSS, log) shares the same root cause — untrusted data parsed in a privileged context. String concatenation is the universal anti-pattern; parameterization / encoding is the universal fix.

**Pattern table (see [java-security.md](references/java-security.md) for full code):**

| Sink | Wrong | Correct |
|---|---|---|
| SQL | `"... WHERE id = " + id` | `PreparedStatement` / `@Query` + `@Param` |
| OS command | `Runtime.exec("ping " + h)` | `InetAddress.getByName(h).isReachable(...)` or `ProcessBuilder` array form |
| XPath | `"//u[name='" + n + "']"` | `XPathVariableResolver` |
| LDAP | `"(uid=" + u + ")"` | escape `\ * ( ) \0` per RFC 4515 |
| XML | default `DocumentBuilder` | disable DTDs, external entities, XInclude |
| HTML output | string interpolation | OWASP Java Encoder (`Encode.forHtml`, `forHtmlAttribute`, `forJavaScript`) |
| Logging | `"... user: " + name` | parameterized: `log.info("... user: {}", name)` |

### 🔴 BLOCKING — Validate at every trust boundary, not only at the controller

**Why:** controllers are not the only entry point. Message-queue listeners, scheduled jobs, deserialization callbacks, and internal service-to-service calls all cross trust boundaries. A controller-only check is bypassed the moment an internal caller appears.

- Validate on entry (controller, listener, consumer)
- Re-validate before security-sensitive operations (payment, deletion, role change)
- Use **allowlist** patterns, never denylist (denylists leak with every new bypass)
- Cap input size to prevent DoS — compare with `current > max - extra` (avoids integer overflow)

---

## When Handling Passwords

### 🔴 BLOCKING — Never store passwords with general-purpose hashes (MD5, SHA-1, SHA-256)

**Why:** these are designed to be fast. A consumer GPU brute-forces billions of SHA-256 hashes per second. Password hashes must be **slow and memory-hard** so an attacker who exfiltrates the hash table cannot crack it offline at scale.

| Algorithm | Recommendation | Minimum parameters (OWASP 2025) |
|---|---|---|
| **Argon2id** | Preferred for new apps | 19 MiB memory · 2 iterations · 1 parallelism |
| **BCrypt** | Good default, broad compat | Work factor ≥ 10 (72-byte password limit) |
| **PBKDF2-HMAC-SHA-256** | FIPS-140 compliance | ≥ 600 000 iterations |

📚 **When implementing password hashing or migrating encoders → read [spring-security.md#password-encoders](references/spring-security.md#password-encoders) and [java-security.md#password-hashing](references/java-security.md#password-hashing).**

---

## When Implementing Authentication

📚 **When implementing a JWT resource server, OAuth2 login, a custom UserDetailsService or Spring Security 7 MFA → read [spring-security.md](references/spring-security.md).**

### 🔴 BLOCKING — Validate every JWT claim that affects trust

**Why:** a JWT is just a signed JSON. If you skip `iss`, `aud`, or `exp` validation, an attacker can replay tokens from another tenant, audience, or past session. Signature alone proves provenance, not freshness or scope.

| Rule | Reason |
|---|---|
| Validate signature, `iss`, `aud`, `exp`, `nbf` | Prevents token reuse across tenants / sessions |
| Short access tokens (≤ 15 min) | Limits exposure window if leaked |
| Refresh tokens in HTTP-only Secure cookies | Mitigates XSS theft |
| Asymmetric keys (RS256 / ES256) | Enables key rotation without resigning every secret |

### 🟢 Stateful vs Stateless

| Use case | Recommendation |
|---|---|
| Monolithic web app | Session-based (simpler, server-side revoke) |
| Microservices / public APIs | JWT / OAuth2 (scalable, no shared session store) |
| Mobile apps | JWT with refresh token rotation |

---

## When Implementing Authorization

📚 **When implementing method security, a custom `AuthorizationManager`, or URL-based authorization in Spring Security 7 → read [spring-security.md](references/spring-security.md).**

### 🔴 BLOCKING — Authorize on the resource, not only the role

**Why:** role checks (`hasRole('USER')`) prove *what the user is*, not *what they own*. Without an ownership check, any authenticated user can act on any resource by guessing the ID — IDOR (A01 in OWASP Top 10).

```java
// 🔴 WRONG — any authenticated user can cancel any order
@PreAuthorize("hasRole('USER')")
public void cancelOrder(UUID orderId) { ... }

// ✅ CORRECT — ownership + role
@PreAuthorize("#order.customerId == authentication.principal.id or hasRole('ADMIN')")
public void cancelOrder(Order order) { ... }
```

### 🟡 Spring Security 6 → 7 migration

```java
// 🔴 REMOVED in Spring Security 7
http.authorizeRequests()...           // → authorizeHttpRequests()
http.csrf().and()...                  // → lambda DSL only
new AntPathRequestMatcher("/api/**")  // → PathPatternRequestMatcher
new MvcRequestMatcher(...)            // → PathPatternRequestMatcher
AuthorizationManager#check(...)       // → #authorize()
```

📚 **When migrating a Spring Security 6 configuration to 7 (lambda DSL, renamed matchers and managers) → read [spring-security.md#whats-new-in-spring-security-7](references/spring-security.md#whats-new-in-spring-security-7).**

---

## When Designing Secure Features (A04 — Insecure Design)

📚 **When threat-modeling a new feature or applying defense-in-depth design → read [security-fundamentals.md#threat-modeling-stride](references/security-fundamentals.md#threat-modeling-stride).**

### 🔴 BLOCKING — Threat-model before writing the first endpoint

**Why:** A04 (Insecure Design) is the OWASP category that cannot be patched after the fact. A missing rate limit or trust boundary baked into the design surfaces only in production, where the cost of a redesign is highest. STRIDE takes 30 minutes; a rebuild takes weeks.

- **Identify** threats with STRIDE (Spoofing, Tampering, Repudiation, Information disclosure, DoS, Elevation of privilege)
- **Fail closed** on errors and unexpected states (default deny)
- **Defense in depth** — URL auth + method auth + business validation, never one layer alone
- **Never rely on obscurity** (hidden URLs, secret query params) instead of authorization

### 🟢 Principle of Least Privilege

Grant the minimum permissions needed; prefer time-bounded scopes (token TTL, session timeout, JIT admin elevation).

---

## When Configuring CORS & CSRF

📚 **When configuring the CORS chain or wiring CSRF for an SPA or JS client → read [spring-security.md#cors-configuration](references/spring-security.md#cors-configuration).**

### 🔴 BLOCKING — CORS must be configured inside the SecurityFilterChain, not as a global filter

**Why:** Spring Security's filter chain runs **before** any global CORS filter. If CORS is configured outside the chain, preflight `OPTIONS` requests get a 401 before reaching the CORS handler — browsers then reject the actual request and you debug a "CORS bug" that is actually an authentication bug.

- Wire via `cors(cors -> cors.configurationSource(corsSource()))`
- Specific origins only (never `*` with `allowCredentials(true)` — browsers refuse the combination)
- `allowCredentials(true)` only when the API uses cookies; otherwise leave false
- Set `maxAge(3600L)` to cut preflight chatter

### 🟡 CSRF Decision Matrix

| App type | Session? | CSRF |
|---|---|---|
| Traditional web (Thymeleaf / JSP) | Yes | **Enable** (default) |
| SPA + session cookie | Yes | **Enable** with `csrf.spa()` |
| REST API + JWT in `Authorization` header | No | **Disable** (no ambient credentials) |
| Mobile backend + JWT | No | **Disable** |

---

## When Managing Secrets

📚 **When choosing where to store secrets or wiring Kubernetes Secrets → read [security-fundamentals.md#secrets-management](references/security-fundamentals.md#secrets-management).**

### 🔴 BLOCKING — Never hardcode secrets in source or committed config

**Why:** once a secret is in git history, it is compromised forever — `git filter-repo` removes the file but every clone, fork, and CI cache still holds it. Treat secret leakage as irrevocable: the only fix is rotation.

```java
// 🔴 WRONG — secret in source
private static final String API_KEY = "sk-abc123...";

// ✅ CORRECT — Spring externalized config
@Value("${app.api-key}")
private String apiKey;
```

| Environment | Storage |
|---|---|
| Development | `.env` files (gitignored) |
| CI/CD | Pipeline secret store (GitHub Actions, GitLab CI) |
| Production | Cloud KMS (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager) or HashiCorp Vault |

---

## When Securing Spring Boot Actuator

📚 **When securing the Actuator endpoints (dedicated `@Order(1)` chain, `EndpointRequest` matcher, separate management port) → read [spring-security.md#actuator-security](references/spring-security.md#actuator-security).**

### 🔴 BLOCKING — Treat actuator as a privileged surface, never as default-public

**Why:** actuator endpoints expose memory dumps, environment variables, thread states and bean graphs — enough for an attacker to map the application internals and find unprotected secrets. The default `permitAll` posture from older guides has caused real production breaches; the current default exposes only `/health` and `/info` for that reason.

- `health`, `info` → `permitAll()`
- `metrics`, `prometheus` → `hasRole("METRICS")` (scrape via service account)
- Everything else → `hasRole("ACTUATOR")`
- Use a separate `@Order(1)` `SecurityFilterChain` with `EndpointRequest.toAnyEndpoint()`
- Bind management to a separate port not exposed to the public LB

---

## When Using Cryptography

📚 **When implementing symmetric or asymmetric encryption, digital signatures, or secure random → read [java-security.md#cryptography](references/java-security.md#cryptography).**

### 🔴 BLOCKING — Use vetted libraries, never roll your own primitives

**Why:** crypto failures are silent — a wrong nonce reuse, a missing constant-time compare, a downgrade-friendly cipher selection produces output that *looks* encrypted but is broken. Vetted libraries (Tink, Bouncy Castle, JCA) embed decades of attack mitigation; hand-rolled code repeats every known mistake.

- **Symmetric:** AES-GCM, 12-byte nonce, **unique per encryption** (reusing a nonce with the same key breaks confidentiality)
- **Asymmetric:** RSA-4096 or Ed25519
- **Random:** `SecureRandom.getInstanceStrong()` — never `java.util.Random` for security
- **Keys:** stored in KMS / HSM, rotated on a schedule, never in code or config

---

## When Making Server-Side HTTP Calls (A10 — SSRF Prevention)

📚 **When making a server-side HTTP call to a user-influenced URL (SSRF, parser bypasses, DNS rebinding) → read [security-fundamentals.md#ssrf-prevention-a10](references/security-fundamentals.md#ssrf-prevention-a10).**

### 🔴 BLOCKING — Validate every user-influenced URL against a host allowlist

**Why:** SSRF lets an attacker pivot from your application into your private network — cloud metadata endpoints (`169.254.169.254`), internal admin panels, and unauthenticated databases all become reachable. The application becomes the attacker's HTTP proxy. Allowlist + internal-IP block + HTTPS-only is the only reliable shape; substring checks are bypassable.

- Parse with `URI` and validate `scheme` + `host` separately (no `startsWith` checks)
- Block loopback, site-local, link-local, multicast addresses (`InetAddress.is*Address()`)
- HTTPS only for outbound calls
- Fail closed — unknown / unresolvable host = reject

---

## When Handling Serialization

📚 **When deserializing untrusted data or hardening a `Serializable` type → read [java-security.md#serialization-security](references/java-security.md#serialization-security).**

### 🔴 BLOCKING — Never deserialize untrusted Java-serialized data

**Why:** Java's `ObjectInputStream` instantiates arbitrary classes and runs their `readObject` callbacks — that gives an attacker who controls the bytes a path to remote code execution via gadget chains in libraries you depend on. Switching to JSON moves the parser to a data-only format with no callback semantics.

- Use JSON via `ObjectMapper` (Jackson) for cross-process payloads
- If Java serialization is unavoidable: configure `ObjectInputFilter` (Java 9+) with depth, reference count, byte budget, and class allowlist
- Mark sensitive fields `transient`; validate inside `readObject`

---

## When Handling Errors

### 🔴 BLOCKING — Never echo internal details to the client

**Why:** stack traces, SQL fragments, and library version strings are reconnaissance gold — they tell the attacker exactly which CVE to target. The client gets a generic message; the operator gets the full context in logs.

```java
// 🔴 WRONG — exposes stack trace and internal exception type
return ResponseEntity.status(500).body(e.getMessage());

// ✅ CORRECT — generic message to client, full detail in logs
log.error("Internal error", e);
return ResponseEntity.status(500).body(Map.of("error", "An unexpected error occurred"));
```

📚 **When returning RFC 7807 Problem Details for a security error → read [spring-security.md#exception-handling](references/spring-security.md#exception-handling).**

---

## When Implementing Security Logging (A09)

📚 **When implementing structured audit logging or an authorization-failure aspect → read [security-fundamentals.md#audit-logging](references/security-fundamentals.md#audit-logging).**

### 🔴 BLOCKING — Log every security-relevant event, with structure

**Why:** A09 (Security Logging and Monitoring Failures) blocks incident response. Without a structured audit trail you cannot answer "when did this start, who was affected, what did the attacker touch" — the legally required questions during a breach disclosure.

**Always log:** authentication success / failure, authorization failures, input validation rejections, password / MFA changes, admin operations, rate-limit hits.

### 🔴 BLOCKING — Never log secrets, tokens, or PII

**Why:** logs are typically replicated, shipped to SIEM, and retained for months. A password that hits stdout once now lives in dozens of immutable systems. Treat logs as low-trust storage — anything written there is effectively public to anyone with read access to logging infra.

**Never log:** plaintext or hashed passwords, session tokens, JWTs, API keys, full credit card numbers, government IDs, health data.

### 🟢 Use structured key-value logging (JSON) — `kv("event", "auth_failure")` — not free-text concatenation.

---

## When Keeping Dependencies Secure

### 🔴 BLOCKING — Run a CVE scan in CI on every build

**Why:** A06 (Vulnerable and Outdated Components) is consistently in the OWASP Top 10 because *transitive* dependencies update faster than humans audit. A daily Dependabot PR or a CI scan that fails on CVSS ≥ 7 is the only way to keep up; manual review at release time is always too late.

| Tool | Purpose |
|---|---|
| OWASP Dependency-Check | CVE scanning of Maven/Gradle deps, fail build on CVSS threshold |
| Snyk | Real-time vulnerability alerts + remediation PRs |
| Trivy | Container image scanning |
| Dependabot / Renovate | Automated dependency-update PRs |

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] No SQL/command/XPath/LDAP/log injection vectors (parameterized everywhere)
- [ ] HTML output encoded via OWASP Java Encoder (no raw interpolation)
- [ ] Passwords hashed with Argon2id / BCrypt (≥ 10) / PBKDF2 (≥ 600k iter), never MD5/SHA-1/SHA-256
- [ ] No secrets in source or committed config
- [ ] Input validated at every trust boundary (controller, listener, consumer)
- [ ] Authentication required for sensitive endpoints
- [ ] Authorization checks include **ownership**, not just role
- [ ] JWTs validate signature + `iss` + `aud` + `exp`
- [ ] Threat model (STRIDE) completed for new features (A04)
- [ ] User-influenced URLs validated against host allowlist + internal-IP block (A10)
- [ ] No raw `ObjectInputStream` on untrusted data
- [ ] Actuator endpoints behind dedicated `@Order(1)` SecurityFilterChain

### 🟡 WARNING
- [ ] CSRF enabled for any session-based auth (form or SPA cookie)
- [ ] CORS lists specific origins, never `*` with credentials
- [ ] Error responses generic; full detail only in logs
- [ ] Logs contain no passwords, tokens, JWTs, full PANs, or PII
- [ ] CVE scan runs in CI and fails on CVSS ≥ 7

### 🟢 BEST PRACTICE
- [ ] Access tokens ≤ 15 min, refresh tokens in HTTP-only cookies
- [ ] Security headers configured (CSP, HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy)
- [ ] Rate limiting on authentication and password-reset endpoints
- [ ] Structured JSON logging with stable event names
- [ ] Dependency-update bot enabled on the repo

---

## Related Skills

- `common-java-developer` — Secure coding patterns (sealed classes, records, defensive copies)
- `common-rest-api` — REST API design (status codes, RFC 7807, OpenAPI)
- `common-spring-boot-config` — YAML / profiles / AOP configuration pitfalls
- `common-architecture` — Security architecture, trust boundaries, network segmentation
