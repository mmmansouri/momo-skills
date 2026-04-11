---
name: common-typescript
description: >-
  Modern TypeScript development guide (4.x-5.x). Use when: writing TypeScript code,
  designing type-safe interfaces, using generics, handling async/await, or applying
  TypeScript patterns. Contains strict mode best practices, utility types, type narrowing,
  and common pitfalls to avoid.
---

# TypeScript Developer Guide (4.x - 5.x)

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

📚 **References:** [utility-types.md](references/utility-types.md) | [advanced-patterns.md](references/advanced-patterns.md)

---

## TypeScript Version Features

| Version | Key Features |
|---------|--------------|
| **4.7** | ESM support, moduleSuffixes |
| **4.9** | `satisfies` operator, auto-accessors |
| **5.0** | Decorators (stage 3), const type parameters |
| **5.1** | Easier implicit returns for undefined |
| **5.2** | `using` declarations (explicit resource management) |
| **5.3** | Import attributes, narrowing improvements |
| **5.4** | `NoInfer` utility type, preserved narrowing in closures |
| **5.5** | Inferred type predicates, regex syntax checking |

---

## When Configuring tsconfig.json

### 🔴 BLOCKING - Strict Mode Required

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "exactOptionalPropertyTypes": true
  }
}
```

### 🟡 WARNING

- **Enable `verbatimModuleSyntax`** → Clearer import/export behavior
- **Use `moduleResolution: "bundler"`** → For modern bundlers (Vite, esbuild)

---

## When Defining Types

### 🔴 BLOCKING

| Rule | Why |
|------|-----|
| **Prefer `interface` for object shapes** | Extendable, better error messages |
| **Use `type` for unions, intersections, mapped types** | More flexible for complex types |
| **Never use `any`** | Defeats type safety; use `unknown` instead |
| **Avoid non-null assertion (!)** | Hides potential runtime errors |

### Examples

```typescript
// 🔴 WRONG - Using `any`
function process(data: any) {
  return data.value; // No type checking
}

// ✅ CORRECT - Using `unknown` with narrowing
function process(data: unknown) {
  if (isValidData(data)) {
    return data.value; // Type-safe
  }
  throw new Error('Invalid data');
}

// 🔴 WRONG - Interface for union
interface Status {
  type: 'loading' | 'success' | 'error';
}

// ✅ CORRECT - Type for union (discriminated union)
type Status = 
  | { type: 'loading' }
  | { type: 'success'; data: string }
  | { type: 'error'; error: Error };
```

---

## When Using Generics

### 🔴 BLOCKING

| Rule | Why |
|------|-----|
| **Constrain generics when possible** | `<T extends object>` is safer than `<T>` |
| **Use meaningful names** | `TItem`, `TKey`, `TValue` not just `T`, `U` |
| **Avoid excessive generic parameters** | >3 generics = code smell |

### 🟢 BEST PRACTICE

| Pattern | Use Case |
|---------|----------|
| `<T extends Record<string, unknown>>` | Generic objects |
| `<T extends readonly unknown[]>` | Generic arrays |
| `<const T>` (5.0+) | Preserve literal types |

### Examples

```typescript
// 🔴 WRONG - Unconstrained, unclear naming
function merge<T, U>(a: T, b: U): T & U {
  return { ...a, ...b }; // Error: spread only on object types
}

// ✅ CORRECT - Constrained, clear naming
function merge<TBase extends object, TExtension extends object>(
  base: TBase,
  extension: TExtension
): TBase & TExtension {
  return { ...base, ...extension };
}

// ✅ CORRECT - Const type parameter (5.0+)
function createConfig<const T extends readonly string[]>(keys: T): Record<T[number], unknown> {
  return {} as Record<T[number], unknown>;
}

const config = createConfig(['host', 'port'] as const);
// Type: Record<'host' | 'port', unknown>
```

---

## When Narrowing Types

### 🔴 BLOCKING

| Rule | Why |
|------|-----|
| **Use discriminated unions** | Exhaustive checking, clear intent |
| **Prefer `in` operator for property checks** | Type-safe property narrowing |
| **Use type predicates for complex checks** | Reusable, self-documenting |

### Examples

```typescript
// 🔴 WRONG - Type assertion
function handleResponse(res: Success | Error) {
  if ((res as Success).data) { // Unsafe cast
    console.log((res as Success).data);
  }
}

// ✅ CORRECT - Discriminated union with `in`
function handleResponse(res: Success | Error) {
  if ('data' in res) {
    console.log(res.data); // TypeScript knows it's Success
  } else {
    console.error(res.error); // TypeScript knows it's Error
  }
}

// ✅ CORRECT - Type predicate
function isSuccess(res: Success | Error): res is Success {
  return 'data' in res;
}

if (isSuccess(res)) {
  console.log(res.data); // Narrowed to Success
}
```

---

## When Handling Null/Undefined

### 🔴 BLOCKING

| Rule | Why |
|------|-----|
| **Use optional chaining `?.`** | Safe property access |
| **Use nullish coalescing `??`** | Handles null/undefined only (not falsy) |
| **Avoid non-null assertion (!)** | Runtime errors waiting to happen |

### Examples

```typescript
// 🔴 WRONG - Non-null assertion
const name = user!.profile!.name;

// ✅ CORRECT - Optional chaining with fallback
const name = user?.profile?.name ?? 'Anonymous';

// 🔴 WRONG - Using || for defaults (catches all falsy)
const count = data.count || 10; // Bug: 0 becomes 10

// ✅ CORRECT - Using ?? (only null/undefined)
const count = data.count ?? 10; // 0 stays 0
```

---

## When Working with Arrays

### 🔴 BLOCKING

| Rule | Why |
|------|-----|
| **Use `readonly` for immutable arrays** | Prevents accidental mutation |
| **Enable `noUncheckedIndexedAccess`** | Array access returns `T | undefined` |
| **Prefer `.find()` over index access** | Clearer intent, handles undefined |

### Examples

```typescript
// 🔴 WRONG - Assuming array access is safe
function getFirst<T>(items: T[]): T {
  return items[0]; // Could be undefined!
}

// ✅ CORRECT - With noUncheckedIndexedAccess
function getFirst<T>(items: T[]): T | undefined {
  return items[0]; // Type is T | undefined
}

// ✅ CORRECT - Using .at() with explicit handling
function getFirst<T>(items: T[]): T {
  const first = items.at(0);
  if (first === undefined) {
    throw new Error('Array is empty');
  }
  return first;
}

// ✅ CORRECT - Readonly arrays for immutability
function process(items: readonly string[]) {
  // items.push('x'); // Error: push doesn't exist on readonly
  return items.map(x => x.toUpperCase()); // OK: map returns new array
}
```

---

## When Using Async/Await

### 🔴 BLOCKING

| Rule | Why |
|------|-----|
| **Always type Promise returns** | `async function(): Promise<Type>` |
| **Handle errors with try/catch or .catch()** | Unhandled rejections crash Node |
| **Avoid async void except for event handlers** | Can't catch errors |

### 🟢 BEST PRACTICE

```typescript
// 🔴 WRONG - Untyped, no error handling
async function fetchUser(id: string) {
  const res = await fetch(`/api/users/${id}`);
  return res.json();
}

// ✅ CORRECT - Typed, with error handling
async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch user: ${res.status}`);
  }
  return res.json() as Promise<User>;
}

// ✅ CORRECT - Result type pattern
type Result<T, E = Error> = 
  | { ok: true; value: T }
  | { ok: false; error: E };

async function fetchUserSafe(id: string): Promise<Result<User>> {
  try {
    const user = await fetchUser(id);
    return { ok: true, value: user };
  } catch (error) {
    return { ok: false, error: error as Error };
  }
}
```

---

## When Using Utility Types

📚 **Reference:** [utility-types.md](references/utility-types.md)

### Essential Utility Types

| Type | Use Case |
|------|----------|
| `Partial<T>` | Make all properties optional |
| `Required<T>` | Make all properties required |
| `Pick<T, K>` | Select specific properties |
| `Omit<T, K>` | Exclude specific properties |
| `Record<K, V>` | Object with keys K and values V |
| `Readonly<T>` | Make all properties readonly |
| `NonNullable<T>` | Remove null and undefined |
| `ReturnType<T>` | Extract function return type |
| `Parameters<T>` | Extract function parameters as tuple |
| `Awaited<T>` | Unwrap Promise type |
| `NoInfer<T>` (5.4+) | Prevent inference in generic position |

### Examples

```typescript
interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

// Update payload - all optional
type UserUpdate = Partial<Omit<User, 'id' | 'createdAt'>>;

// API response with metadata
type ApiResponse<T> = {
  data: T;
  meta: { timestamp: Date };
};

// Extract data type from response
type UserData = ApiResponse<User>['data']; // User
```

---

## When Using `satisfies` (4.9+)

### 🟢 BEST PRACTICE

Use `satisfies` when you want:
- Type checking without widening
- Preserved literal types
- Validation without type assertion

```typescript
// 🔴 WRONG - Type annotation widens literals
const routes: Record<string, { path: string }> = {
  home: { path: '/' },
  about: { path: '/about' },
};
routes.home.path; // string (widened)

// ✅ CORRECT - satisfies preserves literals
const routes = {
  home: { path: '/' },
  about: { path: '/about' },
} satisfies Record<string, { path: string }>;

routes.home.path; // '/' (literal preserved)
routes.invalid; // Error: property doesn't exist
```

---

## Code Review Checklist

### 🔴 BLOCKING

- [ ] No `any` types (use `unknown` + narrowing)
- [ ] No non-null assertions (use proper checks)
- [ ] Strict mode enabled in tsconfig
- [ ] All functions have explicit return types
- [ ] Generics are properly constrained
- [ ] Discriminated unions for complex state

### 🟡 WARNING

- [ ] Prefer `interface` for object shapes
- [ ] Use `readonly` for immutable data
- [ ] Async functions return `Promise<T>`
- [ ] Error handling for all async operations

### 🟢 BEST PRACTICE

- [ ] Use `satisfies` for validated literals
- [ ] Use utility types instead of manual types
- [ ] Type predicates for reusable narrowing
- [ ] `const` assertions for literal preservation

---

## Related Skills

- `common-frontend-angular` — TypeScript in Angular context
- `common-frontend-testing` — Type-safe test patterns
- `common-developer` — General coding principles
- `buy-nature-frontend-coding-guide` — Buy Nature TypeScript conventions
