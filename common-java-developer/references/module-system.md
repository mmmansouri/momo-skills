# Java Module System (JPMS)

> Strong encapsulation, module-info.java, and migration strategies for Java 9+.

---

## Table of Contents
1. [Decision Tree: Modularize or Not?](#decision-tree-modularize-or-not)
2. [When to Use Modules](#when-to-use-modules)
3. [module-info.java Structure](#module-infojava-structure)
4. [Directives Reference](#directives-reference)
5. [Strong Encapsulation](#strong-encapsulation)
6. [Migration Strategy](#migration-strategy)
7. [Common Issues](#common-issues)
8. [Code Review Checklist](#code-review-checklist)

---

## Decision Tree: Modularize or Not?

```
Should you modularize?
│
├── Building a library for external consumption?
│   └── ✅ YES - Modules provide clear API boundaries
│
├── Need strong encapsulation (hide internals)?
│   └── ✅ YES - Modules enforce it at compile time
│
├── Large monolith with clear internal boundaries?
│   └── ✅ CONSIDER - Helps enforce architecture
│
├── All dependencies support modules?
│   ├── Yes → ✅ Easy migration
│   └── No → ⚠️ More complex (automatic modules)
│
├── Small application, rapid iteration?
│   └── ❌ PROBABLY NOT - Overhead may not be worth it
│
├── Using reflection-heavy frameworks (Spring, Hibernate)?
│   └── ⚠️ CAREFUL - Need explicit `opens` directives
│
└── Team unfamiliar with JPMS?
    └── ⚠️ TRAINING NEEDED - Modules add complexity
```

---

## When to Use Modules

### ✅ Good Use Cases

| Scenario | Why Modules Help |
|----------|-----------------|
| **Library development** | Clear public API, hide implementation |
| **Large applications** | Enforce architectural boundaries |
| **Security-sensitive** | Minimize attack surface |
| **Microservices shared core** | Reusable modules across services |
| **Plugin systems** | Service loader with module isolation |

### ❌ When to Skip

| Scenario | Why Skip |
|----------|----------|
| **Small applications** | Overhead not justified |
| **Rapid prototyping** | Slows iteration |
| **Legacy codebase** | Migration cost too high |
| **Dependencies not modular** | Automatic modules are messy |
| **Heavy reflection use** | Constant `opens` battles |

---

## module-info.java Structure

Located at `src/main/java/module-info.java` (source root).

### Basic Module

```java
module com.example.myapp {
    // Dependencies
    requires java.sql;
    requires java.logging;

    // Transitive dependencies (consumers also get this)
    requires transitive com.example.common;

    // Export public API packages
    exports com.example.myapp.api;
    exports com.example.myapp.model;

    // Open packages for reflection (frameworks)
    opens com.example.myapp.dto to com.fasterxml.jackson.databind;
    opens com.example.myapp.entity to org.hibernate.orm.core;

    // Provide service implementation
    provides com.example.api.Plugin
        with com.example.myapp.plugin.MyPlugin;

    // Consume services
    uses com.example.api.Plugin;
}
```

### Naming Convention

```
Module name: reverse domain + project name
com.example.myapp           ✅ Good
com.example.myapp.core      ✅ Good (sub-module)
myapp                       ❌ Bad (too short, no namespace)
```

---

## Directives Reference

| Directive | Purpose | Example |
|-----------|---------|---------|
| `requires` | Declare dependency | `requires java.sql;` |
| `requires transitive` | Dependency visible to consumers | `requires transitive com.example.api;` |
| `requires static` | Compile-time only (optional at runtime) | `requires static lombok;` |
| `exports` | Make package public | `exports com.example.api;` |
| `exports ... to` | Export to specific modules | `exports internal to com.example.impl;` |
| `opens` | Allow runtime reflection | `opens dto to jackson.databind;` |
| `opens ... to` | Reflection for specific modules | `opens entity to hibernate.core;` |
| `provides ... with` | Provide service impl | `provides Api with Impl;` |
| `uses` | Consume service | `uses com.example.Api;` |

### When to Use Each

```java
// Public API - anyone can use
exports com.example.api;

// Internal sharing - only specific modules
exports com.example.internal to com.example.impl;

// Framework reflection (Jackson, Hibernate, Spring)
opens com.example.dto to com.fasterxml.jackson.databind;

// Full reflection access (testing, DI frameworks)
opens com.example.internal;  // Opens to all

// Optional dependency (annotations, build tools)
requires static lombok;
```

---

## Strong Encapsulation

### Before Modules (Classpath)

```
┌─────────────────────────────────────────────────┐
│                 Classpath                        │
│  ┌──────────────────┐  ┌──────────────────┐     │
│  │ Library A        │  │ Your App         │     │
│  │ ├── api/         │  │ ├── Main.java    │     │
│  │ └── internal/    │←─┼─│ (can access!)  │     │
│  └──────────────────┘  └──────────────────┘     │
│                                                  │
│  ALL public classes accessible!                 │
└─────────────────────────────────────────────────┘
```

### After Modules

```
┌────────────────────────────────────────────────────────┐
│                 Module Path                             │
│  ┌─────────────────────┐   ┌─────────────────────┐     │
│  │ module library.a    │   │ module myapp        │     │
│  │ exports api;        │   │ requires library.a; │     │
│  │ ├── api/         ──┼───┼→│ (can access)       │     │
│  │ └── internal/   ✗──┼───┼→│ (CANNOT access!)   │     │
│  └─────────────────────┘   └─────────────────────┘     │
│                                                         │
│  Only EXPORTED packages accessible!                    │
└────────────────────────────────────────────────────────┘
```

### Encapsulation Rules

| Scenario | Accessible? |
|----------|-------------|
| Exported package, public class | ✅ Yes |
| Non-exported package | ❌ No (compile error) |
| Opened package (reflection) | ✅ Yes (at runtime) |
| Private class in exported package | ❌ No |

---

## Migration Strategy

### Step 1: Add Automatic Module Name

Before full module-info.java, add manifest entry:

```
# META-INF/MANIFEST.MF
Automatic-Module-Name: com.example.mylib
```

This reserves your module name without full migration.

### Step 2: Analyze Dependencies

```bash
# Check what your JAR requires
jdeps --module-path libs -s myapp.jar

# Find JDK internal usage
jdeps --jdk-internals myapp.jar
```

### Step 3: Create module-info.java

```java
module com.example.myapp {
    // Add requires for each dependency
    requires java.sql;
    requires com.google.gson;       // From module path
    requires some.automatic.module; // Non-modular JAR

    // Export your public API
    exports com.example.myapp.api;

    // Open for frameworks
    opens com.example.myapp.model to com.google.gson;
}
```

### Step 4: Handle Reflection

```java
// Error: module myapp does not open com.example.dto to jackson
// Solution: Add opens directive
opens com.example.dto to com.fasterxml.jackson.databind;

// For Spring (scans everything)
opens com.example to spring.core, spring.beans, spring.context;
```

### Quick Migration Checklist

1. [ ] Run `jdeps` to analyze dependencies
2. [ ] Add `Automatic-Module-Name` to manifest
3. [ ] Create `module-info.java` with `requires`
4. [ ] Add `exports` for public API packages
5. [ ] Add `opens` for framework reflection
6. [ ] Test with `--module-path` instead of `-classpath`

---

## Common Issues

### Split Packages

Same package in multiple modules (forbidden).

```
com.example.util exists in:
  - module.a (com/example/util/StringUtils.class)
  - module.b (com/example/util/DateUtils.class)

Error: Package com.example.util exists in multiple modules
```

**Solution:** Rename packages or merge into single module.

### Unnamed Module

Classpath code becomes "unnamed module".

```java
// Code on classpath can read all modules
// But cannot be required by named modules

module myapp {
    requires unnamed.module;  // ❌ ERROR - cannot require unnamed
}
```

**Solution:** Move dependency to module path or use automatic module.

### Automatic Modules

Non-modular JARs on module path become automatic modules.

```java
// JAR: gson-2.10.jar → automatic module: gson
// JAR: commons-lang3-3.12.jar → automatic module: commons.lang3

module myapp {
    requires gson;          // Works (automatic module)
    requires commons.lang3; // Works (automatic module)
}
```

**Risks:**
- Automatic modules export ALL packages
- Name derived from JAR filename (unstable)
- Prefer libraries with proper module-info.java

### Reflection Access Denied

```
java.lang.reflect.InaccessibleObjectException:
Unable to make field private final String User.name accessible:
module myapp does not "opens com.example.model" to module jackson.databind
```

**Solution:**
```java
module myapp {
    opens com.example.model to com.fasterxml.jackson.databind;
}
```

### Common Framework Opens

```java
module myapp {
    // Jackson (JSON serialization)
    opens com.example.dto to com.fasterxml.jackson.databind;

    // Hibernate (JPA)
    opens com.example.entity to org.hibernate.orm.core;

    // Spring (DI, AOP)
    opens com.example to spring.core, spring.beans, spring.context;
    opens com.example.config to spring.context;

    // JUnit (reflection in tests)
    opens com.example to org.junit.platform.commons;
}
```

---

## Code Review Checklist

### 🔴 BLOCKING

- [ ] **No internal packages exported** → Only export public API
- [ ] **No wildcard opens** → Be specific about what's opened
- [ ] **Split packages resolved** → One package, one module
- [ ] **Module name follows convention** → `com.company.project`

### 🟡 WARNING

- [ ] **Avoid automatic modules in production** → Prefer proper modules
- [ ] **`requires transitive` used sparingly** → Don't leak dependencies
- [ ] **`opens` only for legitimate reflection** → Not to bypass encapsulation

### 🟢 BEST PRACTICE

- [ ] **Minimal exports** → Only what consumers actually need
- [ ] **Specific `opens ... to`** → Named modules, not blanket opens
- [ ] **`Automatic-Module-Name` for libraries** → Even before full migration
- [ ] **Service loader for plugins** → `provides` / `uses` pattern
- [ ] **Tests as separate module** → Test isolation

---

## Quick Reference

### Minimal Module

```java
module com.example.mylib {
    exports com.example.mylib.api;
}
```

### Library Module

```java
module com.example.mylib {
    requires transitive com.example.common;  // Pass to consumers

    exports com.example.mylib.api;
    exports com.example.mylib.model;

    // Internal packages NOT exported
}
```

### Application Module with Frameworks

```java
module com.example.myapp {
    requires java.sql;
    requires spring.boot;
    requires spring.boot.autoconfigure;
    requires com.fasterxml.jackson.databind;

    exports com.example.myapp.api;

    opens com.example.myapp to spring.core, spring.beans, spring.context;
    opens com.example.myapp.config to spring.context;
    opens com.example.myapp.dto to com.fasterxml.jackson.databind;
    opens com.example.myapp.entity to org.hibernate.orm.core;
}
```

### Commands

```bash
# Compile with modules
javac -d out --module-source-path src $(find src -name "*.java")

# Run module
java --module-path out -m com.example.myapp/com.example.myapp.Main

# Package as modular JAR
jar --create --file myapp.jar --main-class=com.example.myapp.Main -C out .

# Analyze dependencies
jdeps --module-path libs -s myapp.jar
jdeps --jdk-internals myapp.jar
```
