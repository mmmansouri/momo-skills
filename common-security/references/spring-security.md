# Spring Security 7 / Spring Boot 4 Reference

## What's New in Spring Security 7

### Key Changes

| Feature | Spring Security 6 | Spring Security 7 |
|---------|-------------------|-------------------|
| MFA | Manual implementation | Native support |
| CSRF for SPA | Custom config | `csrf.spa()` method |
| Path Matching | `AntPathRequestMatcher` | `PathPatternRequestMatcher` |
| DSL Style | `.and()` chaining | Lambda DSL only |
| Password Encoders | BouncyCastle Argon2 | Password4j support |
| Authorization Server | Separate project | Integrated in core |

### Removed APIs (Migration Required)

```java
// 🔴 REMOVED in Spring Security 7
http.authorizeRequests()              // Use authorizeHttpRequests()
http.csrf().and().cors().and()...     // Use lambda DSL
new AntPathRequestMatcher("/api/**")  // Use PathPatternRequestMatcher
new MvcRequestMatcher(...)            // Use PathPatternRequestMatcher
AuthorizationManager#check(...)       // Use #authorize()

// ✅ Spring Security 7 equivalent
http.authorizeHttpRequests(auth -> auth
    .requestMatchers("/api/**").authenticated())
    .csrf(csrf -> csrf.spa())
    .cors(cors -> cors.configurationSource(corsSource()));
```

---

## Basic Security Configuration

### Minimal Configuration

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .formLogin(Customizer.withDefaults())
            .build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return PasswordEncoderFactories.createDelegatingPasswordEncoder();
    }
}
```

### REST API Configuration (Stateless)

```java
@Configuration
@EnableWebSecurity
public class ApiSecurityConfig {

    @Bean
    public SecurityFilterChain apiFilterChain(HttpSecurity http) throws Exception {
        return http
            .securityMatcher("/api/**")
            .csrf(csrf -> csrf.disable())  // Stateless = no CSRF
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED)))
            .build();
    }
}
```

---

## Authentication

### JWT Resource Server

```java
@Configuration
@EnableWebSecurity
public class JwtSecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthConverter())))
            .build();
    }

    @Bean
    public JwtDecoder jwtDecoder() {
        return NimbusJwtDecoder.withPublicKey(rsaPublicKey).build();
    }

    @Bean
    public JwtAuthenticationConverter jwtAuthConverter() {
        JwtGrantedAuthoritiesConverter authConverter = new JwtGrantedAuthoritiesConverter();
        authConverter.setAuthoritiesClaimName("roles");
        authConverter.setAuthorityPrefix("ROLE_");

        JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
        converter.setJwtGrantedAuthoritiesConverter(authConverter);
        return converter;
    }
}
```

```yaml
# application.yml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com
          # OR
          jwk-set-uri: https://auth.example.com/.well-known/jwks.json
```

### OAuth2 Login (Social Login)

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/", "/login/**").permitAll()
            .anyRequest().authenticated())
        .oauth2Login(oauth2 -> oauth2
            .loginPage("/login")
            .defaultSuccessUrl("/dashboard")
            .userInfoEndpoint(userInfo -> userInfo
                .userService(customOAuth2UserService)))
        .build();
}
```

```yaml
# application.yml
spring:
  security:
    oauth2:
      client:
        registration:
          google:
            client-id: ${GOOGLE_CLIENT_ID}
            client-secret: ${GOOGLE_CLIENT_SECRET}
            scope: openid, profile, email
          github:
            client-id: ${GITHUB_CLIENT_ID}
            client-secret: ${GITHUB_CLIENT_SECRET}
```

### Custom UserDetailsService

```java
@Service
@RequiredArgsConstructor
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    @Override
    public UserDetails loadUserByUsername(String username) {
        return userRepository.findByEmail(username)
            .map(user -> User.builder()
                .username(user.getEmail())
                .password(user.getPasswordHash())
                .authorities(user.getRoles().stream()
                    .map(role -> new SimpleGrantedAuthority("ROLE_" + role.name()))
                    .toList())
                .accountLocked(!user.isActive())
                .build())
            .orElseThrow(() -> new UsernameNotFoundException(
                "User not found: " + username));
    }
}
```

### Multi-Factor Authentication (Spring Security 7)

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/mfa/**").hasAuthority("PRE_AUTH")
            .requestMatchers("/api/**").fullyAuthenticated()
            .anyRequest().authenticated())
        .formLogin(form -> form
            .successHandler(mfaSuccessHandler()))
        .build();
}

// MFA success handler redirects to MFA page if required
@Bean
public AuthenticationSuccessHandler mfaSuccessHandler() {
    return (request, response, authentication) -> {
        User user = (User) authentication.getPrincipal();
        if (user.isMfaEnabled()) {
            // Grant PRE_AUTH, redirect to MFA
            SecurityContextHolder.getContext().setAuthentication(
                new PreAuthenticatedAuthenticationToken(user, null,
                    List.of(new SimpleGrantedAuthority("PRE_AUTH"))));
            response.sendRedirect("/mfa/verify");
        } else {
            response.sendRedirect("/dashboard");
        }
    };
}
```

---

## Authorization

### Method Security

```java
@Configuration
@EnableMethodSecurity  // Replaces @EnableGlobalMethodSecurity
public class MethodSecurityConfig { }

@Service
public class OrderService {

    // Role-based
    @PreAuthorize("hasRole('ADMIN')")
    public void deleteOrder(UUID id) { }

    // Permission-based
    @PreAuthorize("hasAuthority('order:cancel')")
    public void cancelOrder(UUID id) { }

    // SpEL with method arguments
    @PreAuthorize("#customerId == authentication.principal.id or hasRole('ADMIN')")
    public List<Order> getOrders(UUID customerId) { }

    // Post-authorization (filter results)
    @PostAuthorize("returnObject.customerId == authentication.principal.id")
    public Order getOrder(UUID id) { }

    // Filter collections
    @PostFilter("filterObject.customerId == authentication.principal.id")
    public List<Order> getAllOrders() { }
}
```

### Custom Authorization Manager

```java
@Component
public class OrderAuthorizationManager implements AuthorizationManager<MethodInvocation> {

    @Override
    public AuthorizationDecision authorize(
            Supplier<Authentication> authentication,
            MethodInvocation invocation) {

        UUID orderId = (UUID) invocation.getArguments()[0];
        Order order = orderRepository.findById(orderId).orElse(null);

        if (order == null) {
            return new AuthorizationDecision(false);
        }

        Authentication auth = authentication.get();
        boolean isOwner = order.getCustomerId().equals(getPrincipalId(auth));
        boolean isAdmin = auth.getAuthorities().stream()
            .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"));

        return new AuthorizationDecision(isOwner || isAdmin);
    }
}
```

---

## CORS Configuration

### Global CORS

```java
@Bean
public CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration config = new CorsConfiguration();

    // Specific origins (never use * in production with credentials)
    config.setAllowedOrigins(List.of(
        "https://app.example.com",
        "https://admin.example.com"
    ));

    // Or pattern-based
    config.setAllowedOriginPatterns(List.of("https://*.example.com"));

    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
    config.setAllowedHeaders(List.of("Authorization", "Content-Type", "X-Requested-With"));
    config.setExposedHeaders(List.of("X-Total-Count", "X-Page-Number"));
    config.setAllowCredentials(true);
    config.setMaxAge(3600L);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/api/**", config);
    return source;
}

@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .cors(cors -> cors.configurationSource(corsConfigurationSource()))
        // ... rest of config
        .build();
}
```

---

## CSRF Configuration

### SPA Configuration (Spring Security 7)

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        // New SPA-friendly CSRF (deferred loading, BREACH protection)
        .csrf(csrf -> csrf.spa())
        .build();
}
```

### Cookie-Based CSRF (for JavaScript access)

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .csrf(csrf -> csrf
            .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
            .csrfTokenRequestHandler(new SpaCsrfTokenRequestHandler()))
        .build();
}

// SPA handler for deferred CSRF
public class SpaCsrfTokenRequestHandler extends CsrfTokenRequestAttributeHandler {
    private final CsrfTokenRequestHandler delegate = new XorCsrfTokenRequestAttributeHandler();

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
                       Supplier<CsrfToken> csrfToken) {
        this.delegate.handle(request, response, csrfToken);
    }

    @Override
    public String resolveCsrfTokenValue(HttpServletRequest request, CsrfToken csrfToken) {
        return this.delegate.resolveCsrfTokenValue(request, csrfToken);
    }
}
```

### Disable CSRF for Stateless APIs

```java
@Bean
public SecurityFilterChain apiFilterChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/api/**")
        .csrf(csrf -> csrf.disable())  // Safe for stateless JWT APIs
        .sessionManagement(session ->
            session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .build();
}
```

---

## Security Headers

### Default Headers

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .headers(headers -> headers
            // Content Security Policy
            .contentSecurityPolicy(csp -> csp
                .policyDirectives("default-src 'self'; " +
                    "script-src 'self' 'unsafe-inline'; " +
                    "style-src 'self' 'unsafe-inline'; " +
                    "img-src 'self' data: https:; " +
                    "font-src 'self' https://fonts.gstatic.com"))

            // Prevent clickjacking
            .frameOptions(frame -> frame.deny())

            // HSTS (HTTPS enforcement)
            .httpStrictTransportSecurity(hsts -> hsts
                .maxAgeInSeconds(31536000)
                .includeSubDomains(true)
                .preload(true))

            // Prevent MIME sniffing
            .contentTypeOptions(Customizer.withDefaults())

            // Referrer policy
            .referrerPolicy(referrer -> referrer
                .policy(ReferrerPolicyHeaderWriter.ReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN))

            // Permissions policy
            .permissionsPolicy(permissions -> permissions
                .policy("geolocation=(), camera=(), microphone=()")))
        .build();
}
```

---

## Password Encoders

### Delegating Encoder (Recommended)

```java
@Bean
public PasswordEncoder passwordEncoder() {
    // Supports migration between algorithms
    // Default: bcrypt, supports: argon2, scrypt, pbkdf2
    return PasswordEncoderFactories.createDelegatingPasswordEncoder();
}
```

### Argon2 (Spring Security 7 - Password4j)

```java
@Bean
public PasswordEncoder passwordEncoder() {
    // New Password4j-based encoder in Spring Security 7
    return new Argon2Password4jPasswordEncoder();
}
```

### Custom Delegating Encoder

```java
@Bean
public PasswordEncoder passwordEncoder() {
    String defaultEncoder = "argon2";

    Map<String, PasswordEncoder> encoders = new HashMap<>();
    encoders.put("argon2", new Argon2PasswordEncoder(16, 32, 1, 19456, 2));
    encoders.put("bcrypt", new BCryptPasswordEncoder(12));
    encoders.put("scrypt", new SCryptPasswordEncoder());

    return new DelegatingPasswordEncoder(defaultEncoder, encoders);
}
```

---

## Actuator Security

### Separate Security Chain for Actuator

```java
@Bean
@Order(1)
public SecurityFilterChain actuatorFilterChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher(EndpointRequest.toAnyEndpoint())
        .authorizeHttpRequests(auth -> auth
            // Public health check
            .requestMatchers(EndpointRequest.to("health", "info")).permitAll()
            // Metrics require authentication
            .requestMatchers(EndpointRequest.to("metrics", "prometheus"))
                .hasRole("METRICS")
            // Admin endpoints
            .anyRequest().hasRole("ACTUATOR"))
        .httpBasic(Customizer.withDefaults())
        .build();
}

@Bean
@Order(2)
public SecurityFilterChain defaultFilterChain(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .build();
}
```

```yaml
# application.yml
management:
  endpoints:
    web:
      exposure:
        include: health, info, metrics, prometheus
  endpoint:
    health:
      show-details: when_authorized
      show-components: when_authorized
  server:
    port: 8081  # Separate port for actuator
```

---

## Exception Handling

### Custom Authentication Entry Point

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .exceptionHandling(ex -> ex
            .authenticationEntryPoint((request, response, authException) -> {
                response.setContentType(MediaType.APPLICATION_JSON_VALUE);
                response.setStatus(HttpStatus.UNAUTHORIZED.value());
                response.getWriter().write("""
                    {"error": "Unauthorized", "message": "Authentication required"}
                    """);
            })
            .accessDeniedHandler((request, response, accessDeniedException) -> {
                response.setContentType(MediaType.APPLICATION_JSON_VALUE);
                response.setStatus(HttpStatus.FORBIDDEN.value());
                response.getWriter().write("""
                    {"error": "Forbidden", "message": "Insufficient permissions"}
                    """);
            }))
        .build();
}
```

### RFC 7807 Problem Details

```java
@Component
public class SecurityProblemDetailsHandler implements
        AuthenticationEntryPoint, AccessDeniedHandler {

    private final ObjectMapper objectMapper;

    @Override
    public void commence(HttpServletRequest request, HttpServletResponse response,
                         AuthenticationException authException) throws IOException {
        writeProblem(response, HttpStatus.UNAUTHORIZED,
            "Authentication Required", authException.getMessage());
    }

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
                       AccessDeniedException accessDeniedException) throws IOException {
        writeProblem(response, HttpStatus.FORBIDDEN,
            "Access Denied", accessDeniedException.getMessage());
    }

    private void writeProblem(HttpServletResponse response, HttpStatus status,
                              String title, String detail) throws IOException {
        response.setContentType(MediaType.APPLICATION_PROBLEM_JSON_VALUE);
        response.setStatus(status.value());

        Map<String, Object> problem = Map.of(
            "type", "about:blank",
            "title", title,
            "status", status.value(),
            "detail", detail
        );
        objectMapper.writeValue(response.getOutputStream(), problem);
    }
}
```

---

## Testing Security

### MockMvc with Security

```java
@WebMvcTest(OrderController.class)
@Import(SecurityConfig.class)
class OrderControllerSecurityTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void getOrders_unauthenticated_returns401() throws Exception {
        mockMvc.perform(get("/api/orders"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "USER")
    void getOrders_authenticated_returns200() throws Exception {
        mockMvc.perform(get("/api/orders"))
            .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "USER")
    void deleteOrder_asUser_returns403() throws Exception {
        mockMvc.perform(delete("/api/orders/{id}", orderId))
            .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void deleteOrder_asAdmin_returns204() throws Exception {
        mockMvc.perform(delete("/api/orders/{id}", orderId))
            .andExpect(status().isNoContent());
    }
}
```

### Custom Security Context

```java
@Test
@WithUserDetails(value = "admin@example.com", userDetailsServiceBeanName = "customUserDetailsService")
void adminOperation_withCustomUser_succeeds() throws Exception {
    mockMvc.perform(post("/api/admin/action"))
        .andExpect(status().isOk());
}

// Or programmatically
@Test
void withCustomPrincipal() throws Exception {
    CustomUser user = new CustomUser("test@example.com", List.of("ROLE_USER"));

    mockMvc.perform(get("/api/profile")
            .with(SecurityMockMvcRequestPostProcessors.user(user)))
        .andExpect(status().isOk());
}
```

### JWT Testing

```java
@Test
void apiCall_withValidJwt_succeeds() throws Exception {
    mockMvc.perform(get("/api/orders")
            .with(jwt().authorities(new SimpleGrantedAuthority("ROLE_USER"))))
        .andExpect(status().isOk());
}

@Test
void apiCall_withJwtClaims_succeeds() throws Exception {
    mockMvc.perform(get("/api/orders")
            .with(jwt()
                .jwt(jwt -> jwt
                    .claim("sub", "user@example.com")
                    .claim("roles", List.of("ROLE_USER")))))
        .andExpect(status().isOk());
}
```
