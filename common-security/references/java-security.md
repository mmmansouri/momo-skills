# Java Security Reference

## Injection Prevention

### SQL Injection

```java
// 🔴 WRONG - String concatenation
String query = "SELECT * FROM users WHERE id = " + userId;
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery(query);

// ✅ CORRECT - PreparedStatement
String query = "SELECT * FROM users WHERE id = ?";
PreparedStatement ps = conn.prepareStatement(query);
ps.setLong(1, userId);
ResultSet rs = ps.executeQuery();

// ✅ CORRECT - Named parameters (JPA)
@Query("SELECT u FROM User u WHERE u.email = :email AND u.status = :status")
List<User> findByEmailAndStatus(
    @Param("email") String email,
    @Param("status") Status status);
```

### Command Injection

```java
// 🔴 WRONG - Shell command with user input
String cmd = "ping -c 4 " + hostname;
Runtime.getRuntime().exec(cmd);

// 🔴 WRONG - ProcessBuilder with shell
new ProcessBuilder("sh", "-c", "ls " + directory).start();

// ✅ CORRECT - Use Java API
InetAddress addr = InetAddress.getByName(hostname);
boolean reachable = addr.isReachable(5000);

// ✅ CORRECT - If command necessary, use array form
ProcessBuilder pb = new ProcessBuilder("ls", "-la", directory);
pb.directory(new File("/safe/base/path"));
Process p = pb.start();
```

### XPath Injection

```java
// 🔴 WRONG - String concatenation
String expr = "//users/user[name='" + username + "']";
XPath xpath = XPathFactory.newInstance().newXPath();
xpath.evaluate(expr, doc);

// ✅ CORRECT - XPathVariableResolver
xpath.setXPathVariableResolver(name -> {
    if ("username".equals(name.getLocalPart())) {
        return username;
    }
    return null;
});
xpath.evaluate("//users/user[name=$username]", doc);
```

### LDAP Injection

```java
// 🔴 WRONG - Direct concatenation
String filter = "(uid=" + username + ")";

// ✅ CORRECT - Escape special characters
String safeUsername = username
    .replace("\\", "\\5c")
    .replace("*", "\\2a")
    .replace("(", "\\28")
    .replace(")", "\\29")
    .replace("\0", "\\00");
String filter = "(uid=" + safeUsername + ")";
```

### XML External Entity (XXE)

```java
// ✅ Secure XML parsing
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();

// Disable external entities and DTDs
dbf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
dbf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
dbf.setXIncludeAware(false);
dbf.setExpandEntityReferences(false);

DocumentBuilder db = dbf.newDocumentBuilder();
Document doc = db.parse(inputStream);
```

---

## Serialization Security

### Avoid Java Serialization

Java serialization is inherently dangerous with untrusted data.

```java
// 🔴 DANGEROUS - Deserializing untrusted data
ObjectInputStream ois = new ObjectInputStream(untrustedInput);
Object obj = ois.readObject();  // Remote code execution possible!

// ✅ CORRECT - Use JSON instead
ObjectMapper mapper = new ObjectMapper();
MyClass obj = mapper.readValue(jsonString, MyClass.class);
```

### If Serialization Required

```java
// ✅ Use ObjectInputFilter (Java 9+)
ObjectInputStream ois = new ObjectInputStream(input);
ois.setObjectInputFilter(filterInfo -> {
    if (filterInfo.depth() > 5) return Status.REJECTED;
    if (filterInfo.references() > 100) return Status.REJECTED;
    if (filterInfo.streamBytes() > 1_000_000) return Status.REJECTED;

    Class<?> clazz = filterInfo.serialClass();
    if (clazz != null) {
        // Allowlist of permitted classes
        if (clazz == MyClass.class || clazz == String.class) {
            return Status.ALLOWED;
        }
        return Status.REJECTED;
    }
    return Status.UNDECIDED;
});

// ✅ Global filter (application-wide)
ObjectInputFilter.Config.setSerialFilter(
    ObjectInputFilter.Config.createFilter(
        "maxdepth=5;maxrefs=100;maxbytes=1000000;" +
        "com.myapp.**;java.base/**;!*"));
```

### Secure Serializable Classes

```java
public class SecureData implements Serializable {
    private static final long serialVersionUID = 1L;

    // Mark sensitive fields transient
    private transient String password;
    private transient SecretKey key;

    // Validate on deserialization
    private void readObject(ObjectInputStream ois)
            throws IOException, ClassNotFoundException {
        ois.defaultReadObject();

        // Perform same validation as constructor
        if (name == null || name.isEmpty()) {
            throw new InvalidObjectException("Invalid name");
        }
        if (value < 0) {
            throw new InvalidObjectException("Value must be positive");
        }
    }

    // Prevent subclass attacks
    private void readObjectNoData() throws ObjectStreamException {
        throw new InvalidObjectException("Stream data required");
    }
}
```

---

## Cryptography

### Never Write Your Own Crypto

Use established libraries:
- **Google Tink** - Recommended, safe defaults
- **Bouncy Castle** - Comprehensive, low-level
- **JCA/JCE** - Built-in, requires careful configuration

### Symmetric Encryption (AES-GCM)

```java
// ✅ Google Tink (recommended)
KeysetHandle keysetHandle = KeysetHandle.generateNew(
    AeadKeyTemplates.AES256_GCM);
Aead aead = keysetHandle.getPrimitive(Aead.class);

byte[] ciphertext = aead.encrypt(plaintext, associatedData);
byte[] decrypted = aead.decrypt(ciphertext, associatedData);

// ✅ JCA/JCE (manual configuration)
// Generate key
KeyGenerator keyGen = KeyGenerator.getInstance("AES");
keyGen.init(256);
SecretKey key = keyGen.generateKey();

// Generate unique nonce (12 bytes for GCM)
byte[] nonce = new byte[12];
SecureRandom.getInstanceStrong().nextBytes(nonce);

// Encrypt
Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
GCMParameterSpec spec = new GCMParameterSpec(128, nonce);
cipher.init(Cipher.ENCRYPT_MODE, key, spec);
byte[] ciphertext = cipher.doFinal(plaintext);

// Store nonce + ciphertext together
// Nonce is not secret, must be unique per encryption
```

### Asymmetric Encryption (RSA)

```java
// Generate key pair
KeyPairGenerator keyGen = KeyPairGenerator.getInstance("RSA");
keyGen.initialize(4096);  // Minimum 2048, prefer 4096
KeyPair keyPair = keyGen.generateKeyPair();

// Encrypt with public key
Cipher cipher = Cipher.getInstance("RSA/ECB/OAEPWithSHA-256AndMGF1Padding");
cipher.init(Cipher.ENCRYPT_MODE, keyPair.getPublic());
byte[] ciphertext = cipher.doFinal(plaintext);

// Decrypt with private key
cipher.init(Cipher.DECRYPT_MODE, keyPair.getPrivate());
byte[] decrypted = cipher.doFinal(ciphertext);
```

### Digital Signatures

```java
// Sign
Signature sig = Signature.getInstance("SHA256withRSA");
sig.initSign(privateKey);
sig.update(data);
byte[] signature = sig.sign();

// Verify
sig.initVerify(publicKey);
sig.update(data);
boolean valid = sig.verify(signature);
```

### Secure Random

```java
// ✅ For cryptographic purposes
SecureRandom secureRandom = SecureRandom.getInstanceStrong();

// Generate random bytes
byte[] randomBytes = new byte[32];
secureRandom.nextBytes(randomBytes);

// Generate random token
String token = new BigInteger(256, secureRandom).toString(32);

// 🔴 WRONG - Not cryptographically secure
Random random = new Random();  // Predictable!
```

---

## Password Hashing

### BCrypt

```java
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

// Configure encoder
BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(12);  // Work factor 12

// Hash password
String hash = encoder.encode(rawPassword);

// Verify password
boolean matches = encoder.matches(rawPassword, hash);
```

### Argon2

```java
import org.springframework.security.crypto.argon2.Argon2PasswordEncoder;

// Configure encoder (saltLength, hashLength, parallelism, memory, iterations)
Argon2PasswordEncoder encoder = new Argon2PasswordEncoder(16, 32, 1, 19456, 2);

// Hash password
String hash = encoder.encode(rawPassword);

// Verify password
boolean matches = encoder.matches(rawPassword, hash);
```

### Algorithm Comparison

| Algorithm | Pros | Cons |
|-----------|------|------|
| **Argon2id** | Memory-hard, GPU/ASIC resistant, modern | Newer, requires BouncyCastle |
| **BCrypt** | Battle-tested, widely supported | 72-byte limit, CPU-only |
| **SCrypt** | Memory-hard | Complex tuning |
| **PBKDF2** | FIPS-140 compliant | Not memory-hard |

### OWASP 2025 Recommendations

```java
// Argon2id (preferred)
new Argon2PasswordEncoder(
    16,      // Salt length
    32,      // Hash length
    1,       // Parallelism (min 1)
    19456,   // Memory in KB (min 19 MiB = 19456)
    2        // Iterations (min 2)
);

// BCrypt
new BCryptPasswordEncoder(10);  // Work factor 10+

// PBKDF2 (FIPS compliance)
new Pbkdf2PasswordEncoder("", 16, 600000,
    Pbkdf2PasswordEncoder.SecretKeyFactoryAlgorithm.PBKDF2WithHmacSHA256);
```

---

## Immutability for Security

### Why Immutability Matters

Mutable objects can be modified after security checks:

```java
// 🔴 WRONG - Mutable return value
public class User {
    private List<String> roles;

    public List<String> getRoles() {
        return roles;  // Caller can modify!
    }
}

// ✅ CORRECT - Defensive copy
public List<String> getRoles() {
    return List.copyOf(roles);
}

// ✅ CORRECT - Unmodifiable view
public List<String> getRoles() {
    return Collections.unmodifiableList(roles);
}
```

### Defensive Copies

```java
// 🔴 WRONG - Stores reference to mutable input
public void setExpiration(Date date) {
    this.expiration = date;  // Caller can modify after!
}

// ✅ CORRECT - Defensive copy on input
public void setExpiration(Date date) {
    this.expiration = new Date(date.getTime());
}

// ✅ BETTER - Use immutable types
public void setExpiration(Instant instant) {
    this.expiration = instant;  // Instant is immutable
}
```

### Static Final Fields

```java
// 🔴 WRONG - Mutable static field
public static final List<String> ALLOWED = new ArrayList<>();

// ✅ CORRECT - Immutable static field
public static final List<String> ALLOWED = List.of("GET", "POST", "PUT");

// ✅ CORRECT - Unmodifiable wrapper
public static final List<String> ALLOWED =
    Collections.unmodifiableList(Arrays.asList("GET", "POST", "PUT"));
```

---

## Access Control

### Class Accessibility

```java
// 🔴 WRONG - Public when not needed
public class InternalHelper { }

// ✅ CORRECT - Package-private by default
class InternalHelper { }

// ✅ Use sealed classes to control inheritance
public sealed class Permission permits ReadPermission, WritePermission { }
```

### Method Accessibility

```java
public class SecureService {
    // Public API
    public Result process(Input input) {
        validate(input);
        return doProcess(input);
    }

    // 🔴 WRONG - Exposes internal logic
    public void validate(Input input) { }

    // ✅ CORRECT - Hide internal methods
    private void validate(Input input) { }

    private Result doProcess(Input input) { }
}
```

### Native Method Wrapping

```java
// 🔴 WRONG - Public native method
public native void unsafeOperation(String data);

// ✅ CORRECT - Private native with Java wrapper
private native void nativeOperation(byte[] data);

public void safeOperation(String data) {
    // Validate in Java before native call
    if (data == null || data.length() > MAX_LENGTH) {
        throw new IllegalArgumentException("Invalid data");
    }
    nativeOperation(data.getBytes(StandardCharsets.UTF_8));
}
```

---

## Error Handling

### Sanitize Exception Messages

```java
// 🔴 WRONG - Exposes internal details
public User findById(Long id) {
    try {
        return repository.findById(id).orElseThrow();
    } catch (Exception e) {
        throw new RuntimeException("SQL: " + e.getMessage());
    }
}

// ✅ CORRECT - Generic message, log details
public User findById(Long id) {
    try {
        return repository.findById(id)
            .orElseThrow(() -> new NotFoundException("User not found"));
    } catch (DataAccessException e) {
        log.error("Database error for user id={}", id, e);
        throw new ServiceException("Unable to retrieve user");
    }
}
```

### Don't Log Sensitive Data

```java
// 🔴 WRONG
log.info("User {} logged in with password {}", username, password);
log.debug("Processing card: {}", creditCardNumber);

// ✅ CORRECT
log.info("User {} logged in", username);
log.debug("Processing card ending in {}", lastFourDigits(creditCardNumber));
```

---

## Resource Management

### Always Close Resources

```java
// ✅ Try-with-resources (preferred)
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql);
     ResultSet rs = ps.executeQuery()) {
    // Process results
}  // All resources closed automatically

// ✅ Finally block (legacy code)
Connection conn = null;
try {
    conn = dataSource.getConnection();
    // Use connection
} finally {
    if (conn != null) {
        try {
            conn.close();
        } catch (SQLException e) {
            log.warn("Failed to close connection", e);
        }
    }
}
```

### Prevent Resource Exhaustion

```java
// ✅ Limit file size before processing
if (file.length() > MAX_FILE_SIZE) {
    throw new SecurityException("File too large");
}

// ✅ Limit decompressed size (ZIP bomb protection)
ZipInputStream zis = new ZipInputStream(input);
long totalSize = 0;
while ((entry = zis.getNextEntry()) != null) {
    totalSize += entry.getSize();
    if (totalSize > MAX_TOTAL_SIZE) {
        throw new SecurityException("Decompressed content too large");
    }
}
```
