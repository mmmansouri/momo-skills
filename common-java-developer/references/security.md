# Java Security Essentials

> Cryptography, SSL/TLS, authentication patterns, and input validation for Java 8-25.

---

## Table of Contents
1. [Decision Tree: Which Algorithm?](#decision-tree-which-algorithm)
2. [Password Hashing](#password-hashing)
3. [Encryption](#encryption)
4. [Secure Random](#secure-random)
5. [SSL/TLS Configuration](#ssltls-configuration)
6. [JWT Handling](#jwt-handling)
7. [Input Validation](#input-validation)
8. [Secrets Management](#secrets-management)
9. [Code Review Checklist](#code-review-checklist)

---

## Decision Tree: Which Algorithm?

```
What are you securing?
│
├── Password storage?
│   └── BCrypt or Argon2 (NEVER MD5/SHA for passwords)
│
├── Data at rest (encryption)?
│   └── AES-256-GCM (authenticated encryption)
│
├── Data in transit?
│   └── TLS 1.3 (or TLS 1.2 minimum)
│
├── Random token generation (API keys, session IDs)?
│   └── SecureRandom + Base64 encoding
│
├── Digital signature (verify authenticity)?
│   └── ECDSA (preferred) or RSA-PSS
│
├── Hash for integrity (not passwords)?
│   └── SHA-256 or SHA-3
│
└── Key exchange?
    └── ECDH (Elliptic Curve Diffie-Hellman)
```

### Algorithm Quick Reference

| Purpose | Use | Never Use |
|---------|-----|-----------|
| Password storage | BCrypt, Argon2 | MD5, SHA-1, SHA-256 (alone) |
| Symmetric encryption | AES-256-GCM | DES, 3DES, AES-ECB |
| Asymmetric encryption | RSA-OAEP (2048+ bits) | RSA-PKCS1v1.5 |
| Hashing (integrity) | SHA-256, SHA-3 | MD5, SHA-1 |
| Signatures | ECDSA, RSA-PSS | RSA-PKCS1v1.5 |
| Random generation | SecureRandom | Random, Math.random() |
| TLS version | TLS 1.3, TLS 1.2 | TLS 1.0, TLS 1.1, SSL |

---

## Password Hashing

### 🔴 BLOCKING: Never Use MD5/SHA for Passwords

```java
// 🔴 WRONG - MD5/SHA are NOT for passwords (too fast, rainbow tables)
String hash = MessageDigest.getInstance("MD5").digest(password.getBytes());
String hash = MessageDigest.getInstance("SHA-256").digest(password.getBytes());

// 🔴 WRONG - Even with salt, SHA is too fast
String hash = sha256(salt + password);  // Can brute-force billions/second
```

### BCrypt (Recommended)

```java
// Using Spring Security (recommended)
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(12);  // Work factor 12

// Hash password
String hashedPassword = encoder.encode(rawPassword);

// Verify password
boolean matches = encoder.matches(rawPassword, hashedPassword);
```

### Argon2 (Modern Alternative)

```java
// Using Bouncy Castle
import org.bouncycastle.crypto.generators.Argon2BytesGenerator;

// Or using Spring Security 5.3+
import org.springframework.security.crypto.argon2.Argon2PasswordEncoder;

Argon2PasswordEncoder encoder = Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8();
String hash = encoder.encode(rawPassword);
boolean matches = encoder.matches(rawPassword, hash);
```

### Work Factor Guidelines

| Algorithm | Recommended | Minimum |
|-----------|-------------|---------|
| BCrypt | 12 | 10 |
| Argon2 | memory=64MB, iterations=3 | memory=32MB, iterations=2 |

**Rule:** Hashing should take ~100-500ms. Adjust work factor accordingly.

---

## Encryption

### AES-GCM (Authenticated Encryption)

```java
import javax.crypto.*;
import javax.crypto.spec.*;
import java.security.SecureRandom;

public class AesGcmEncryption {

    private static final int GCM_IV_LENGTH = 12;   // 96 bits
    private static final int GCM_TAG_LENGTH = 128; // bits

    public static byte[] encrypt(byte[] plaintext, SecretKey key) throws Exception {
        // Generate random IV (NEVER reuse IV with same key!)
        byte[] iv = new byte[GCM_IV_LENGTH];
        new SecureRandom().nextBytes(iv);

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
        cipher.init(Cipher.ENCRYPT_MODE, key, spec);

        byte[] ciphertext = cipher.doFinal(plaintext);

        // Prepend IV to ciphertext (IV is not secret)
        byte[] result = new byte[iv.length + ciphertext.length];
        System.arraycopy(iv, 0, result, 0, iv.length);
        System.arraycopy(ciphertext, 0, result, iv.length, ciphertext.length);

        return result;
    }

    public static byte[] decrypt(byte[] ciphertextWithIv, SecretKey key) throws Exception {
        // Extract IV
        byte[] iv = Arrays.copyOfRange(ciphertextWithIv, 0, GCM_IV_LENGTH);
        byte[] ciphertext = Arrays.copyOfRange(ciphertextWithIv, GCM_IV_LENGTH, ciphertextWithIv.length);

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
        cipher.init(Cipher.DECRYPT_MODE, key, spec);

        return cipher.doFinal(ciphertext);
    }

    // Generate a secure key
    public static SecretKey generateKey() throws Exception {
        KeyGenerator keyGen = KeyGenerator.getInstance("AES");
        keyGen.init(256);  // AES-256
        return keyGen.generateKey();
    }
}
```

### 🔴 BLOCKING: Common Encryption Mistakes

```java
// 🔴 WRONG - ECB mode (patterns visible)
Cipher.getInstance("AES/ECB/PKCS5Padding");

// 🔴 WRONG - Static/hardcoded IV
byte[] iv = "1234567890123456".getBytes();

// 🔴 WRONG - Reusing IV with same key
// Each encryption MUST use a unique IV

// 🔴 WRONG - Using DES or 3DES (weak/slow)
Cipher.getInstance("DES");
Cipher.getInstance("DESede");

// ✅ CORRECT
Cipher.getInstance("AES/GCM/NoPadding");  // With random IV
```

---

## Secure Random

### Token Generation

```java
import java.security.SecureRandom;
import java.util.Base64;

public class TokenGenerator {

    private static final SecureRandom SECURE_RANDOM = new SecureRandom();

    // API key / session token (32 bytes = 256 bits)
    public static String generateToken() {
        byte[] bytes = new byte[32];
        SECURE_RANDOM.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    // Numeric OTP (6 digits)
    public static String generateOtp() {
        int otp = SECURE_RANDOM.nextInt(1_000_000);
        return String.format("%06d", otp);
    }

    // UUID (already uses SecureRandom internally)
    public static String generateUuid() {
        return UUID.randomUUID().toString();
    }
}
```

### 🔴 BLOCKING: Never Use `Random` for Security

```java
// 🔴 WRONG - Predictable!
Random random = new Random();
byte[] token = new byte[32];
random.nextBytes(token);

// 🔴 WRONG - Also predictable
String token = String.valueOf(Math.random());

// ✅ CORRECT
SecureRandom secureRandom = new SecureRandom();
byte[] token = new byte[32];
secureRandom.nextBytes(token);
```

---

## SSL/TLS Configuration

### HttpClient with Custom SSL Context

```java
import javax.net.ssl.*;
import java.net.http.*;
import java.security.KeyStore;

// Load custom trust store
KeyStore trustStore = KeyStore.getInstance("PKCS12");
try (var is = Files.newInputStream(Path.of("truststore.p12"))) {
    trustStore.load(is, "password".toCharArray());
}

TrustManagerFactory tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
tmf.init(trustStore);

SSLContext sslContext = SSLContext.getInstance("TLS");
sslContext.init(null, tmf.getTrustManagers(), new SecureRandom());

HttpClient client = HttpClient.newBuilder()
    .sslContext(sslContext)
    .build();
```

### Disable Weak Protocols (JVM-wide)

```properties
# In java.security file or via system property
jdk.tls.disabledAlgorithms=SSLv3, TLSv1, TLSv1.1, RC4, DES, MD5withRSA, \
    DH keySize < 1024, EC keySize < 224, 3DES_EDE_CBC, anon, NULL
```

### Spring Boot TLS Configuration

```yaml
# application.yml
server:
  ssl:
    enabled: true
    key-store: classpath:keystore.p12
    key-store-password: ${KEYSTORE_PASSWORD}
    key-store-type: PKCS12
    protocol: TLS
    enabled-protocols: TLSv1.3,TLSv1.2
    ciphers:
      - TLS_AES_256_GCM_SHA384
      - TLS_AES_128_GCM_SHA256
      - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
```

---

## JWT Handling

### JWT Validation (using jjwt)

```java
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;

public class JwtService {

    private final SecretKey key;

    public JwtService(String base64Secret) {
        this.key = Keys.hmacShaKeyFor(Base64.getDecoder().decode(base64Secret));
    }

    public String createToken(String subject, Duration validity) {
        Instant now = Instant.now();
        return Jwts.builder()
            .subject(subject)
            .issuedAt(Date.from(now))
            .expiration(Date.from(now.plus(validity)))
            .signWith(key)
            .compact();
    }

    public Claims validateAndParse(String token) {
        return Jwts.parser()
            .verifyWith(key)
            .build()
            .parseSignedClaims(token)
            .getPayload();
    }
}
```

### JWT Security Checklist

```java
// ✅ Always verify signature
Jwts.parser().verifyWith(key)...

// ✅ Always check expiration
claims.getExpiration().after(new Date())

// ✅ Validate issuer if known
.requireIssuer("https://auth.example.com")

// ✅ Validate audience
.requireAudience("my-app")

// 🔴 WRONG - Never trust unverified claims
String userId = Jwts.parser().build()
    .parseUnsecuredClaims(token)  // NO SIGNATURE CHECK!
    .getPayload()
    .getSubject();
```

### Common JWT Vulnerabilities

| Vulnerability | Prevention |
|--------------|------------|
| Algorithm confusion (`alg: none`) | Explicitly require algorithm |
| Weak secret | Use 256+ bit secret for HS256 |
| No expiration | Always set and validate `exp` |
| Token in URL | Use Authorization header or cookie |
| XSS token theft | Use HttpOnly cookies |

---

## Input Validation

### Bean Validation (Jakarta Validation)

```java
public record CreateUserRequest(
    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    @Size(max = 255)
    String email,

    @NotBlank(message = "Password is required")
    @Size(min = 8, max = 100, message = "Password must be 8-100 characters")
    @Pattern(regexp = ".*[A-Z].*", message = "Password must contain uppercase")
    @Pattern(regexp = ".*[a-z].*", message = "Password must contain lowercase")
    @Pattern(regexp = ".*\\d.*", message = "Password must contain digit")
    String password,

    @Size(max = 100)
    String name
) {}

// In controller
@PostMapping("/users")
public ResponseEntity<User> createUser(@Valid @RequestBody CreateUserRequest request) {
    // request is already validated
}
```

### Custom Validator

```java
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = SafeHtmlValidator.class)
public @interface SafeHtml {
    String message() default "Contains unsafe HTML";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

public class SafeHtmlValidator implements ConstraintValidator<SafeHtml, String> {

    private static final Pattern DANGEROUS = Pattern.compile(
        "<script|javascript:|on\\w+=", Pattern.CASE_INSENSITIVE);

    @Override
    public boolean isValid(String value, ConstraintValidatorContext ctx) {
        if (value == null) return true;
        return !DANGEROUS.matcher(value).find();
    }
}
```

### SQL Injection Prevention

```java
// 🔴 WRONG - SQL injection vulnerability!
String query = "SELECT * FROM users WHERE email = '" + email + "'";
// Input: ' OR '1'='1  → Returns all users!

// ✅ CORRECT - Parameterized query (JPA)
@Query("SELECT u FROM User u WHERE u.email = :email")
Optional<User> findByEmail(@Param("email") String email);

// ✅ CORRECT - Criteria API
cb.equal(root.get("email"), email);

// ✅ CORRECT - JDBC PreparedStatement
PreparedStatement ps = conn.prepareStatement(
    "SELECT * FROM users WHERE email = ?");
ps.setString(1, email);
```

### XSS Prevention

```java
// 🔴 WRONG - Unescaped output
model.addAttribute("message", userInput);
// In template: ${message}  ← XSS if userInput contains <script>

// ✅ CORRECT - Use Thymeleaf th:text (auto-escapes)
// <p th:text="${message}"></p>

// ✅ CORRECT - Manual escaping (when needed)
import org.springframework.web.util.HtmlUtils;
String safe = HtmlUtils.htmlEscape(userInput);

// ✅ CORRECT - Content Security Policy header
response.setHeader("Content-Security-Policy",
    "default-src 'self'; script-src 'self'");
```

---

## Secrets Management

### 🔴 BLOCKING: Never Hardcode Secrets

```java
// 🔴 WRONG - Hardcoded secrets
private static final String DB_PASSWORD = "mypassword123";
private static final String API_KEY = "sk-1234567890abcdef";

// 🔴 WRONG - In application.properties (committed to git)
spring.datasource.password=mypassword123

// ✅ CORRECT - Environment variables
spring.datasource.password=${DB_PASSWORD}

// ✅ CORRECT - External config
spring.config.import=file:/etc/secrets/application.yml

// ✅ CORRECT - Spring Cloud Vault
spring.cloud.vault.kv.backend=secret
```

### Environment Variables Pattern

```java
// Load from environment with fallback
String apiKey = System.getenv("API_KEY");
if (apiKey == null || apiKey.isBlank()) {
    throw new IllegalStateException("API_KEY environment variable not set");
}

// Spring way
@Value("${api.key}")
private String apiKey;  // Loaded from env var API_KEY or config
```

### 🔴 BLOCKING: Never Log Secrets

```java
// 🔴 WRONG
log.info("Connecting with password: {}", password);
log.debug("API key: {}", apiKey);
log.error("Auth failed for token: {}", bearerToken);

// ✅ CORRECT - Mask sensitive data
log.info("Connecting to database as user: {}", username);
log.debug("API key present: {}", apiKey != null);
log.error("Auth failed for user: {}", extractUsername(token));
```

---

## Code Review Checklist

### 🔴 BLOCKING

- [ ] **No MD5/SHA1 for password hashing** → Use BCrypt/Argon2
- [ ] **No hardcoded secrets** → Use environment variables
- [ ] **No SQL string concatenation** → Use parameterized queries
- [ ] **No `Random` for security tokens** → Use `SecureRandom`
- [ ] **No AES-ECB mode** → Use AES-GCM
- [ ] **No static/reused IVs** → Generate random IV per encryption
- [ ] **Secrets not logged** → Mask sensitive data in logs

### 🟡 WARNING

- [ ] **TLS 1.0/1.1 not allowed** → Require TLS 1.2+
- [ ] **JWT signature verified** → Never trust unverified tokens
- [ ] **Input validated server-side** → Don't trust client validation
- [ ] **Error messages don't leak info** → Generic messages for auth failures

### 🟢 BEST PRACTICE

- [ ] **BCrypt work factor >= 12** → Adjust for ~100-500ms hash time
- [ ] **AES-256** → Prefer over AES-128
- [ ] **Content Security Policy** → Mitigate XSS
- [ ] **HTTPS enforced** → Redirect HTTP → HTTPS
- [ ] **Secrets rotated** → Periodic key rotation
- [ ] **Audit logging** → Log security events

---

## Quick Reference

### Password Hashing (Spring Security)

```java
BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(12);
String hash = encoder.encode(password);
boolean valid = encoder.matches(password, hash);
```

### Token Generation

```java
byte[] bytes = new byte[32];
new SecureRandom().nextBytes(bytes);
String token = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
```

### Input Validation

```java
@NotBlank @Email @Size(max = 255) String email
@NotBlank @Size(min = 8, max = 100) String password
```

### SQL Parameterization

```java
@Query("SELECT u FROM User u WHERE u.email = :email")
Optional<User> findByEmail(@Param("email") String email);
```
