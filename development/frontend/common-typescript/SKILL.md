---
name: common-typescript
description: >-
  Modern TypeScript (5.x) authoring guide. Use whenever the user mentions
  TypeScript, `tsconfig.json`, `strict` mode, generics, discriminated unions,
  `unknown` vs `any`, `satisfies`, type predicates, `NoInfer`, branded types,
  `noUncheckedIndexedAccess`, `verbatimModuleSyntax`, `--erasableSyntaxOnly`
  (Node native TS), or debugging compiler errors like "TS2322 Type 'X' is not
  assignable", "TS2532 Object is possibly undefined", "TS18048 'x' is possibly
  undefined", "Excessive stack depth comparing types", or when reviewing a PR
  touching TypeScript files (`*.ts`, `tsconfig*.json`) — even when they don't
  explicitly say "TypeScript". Do NOT use for runtime JavaScript debugging
  (use Node/browser tools), Angular template syntax (use common-frontend-angular),
  Node runtime errors, or build tooling configuration (Vite/esbuild/webpack).
---

# TypeScript Developer Guide (5.x)

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
> **Stack baseline:** TypeScript 5.x (tested with 5.8) · Node 22 LTS · `strict: true` · `moduleResolution: "bundler"` or `nodenext` · ESM-first. Features tied to a minor version are tagged inline (e.g. TS 5.4+).

📚 **When picking a utility type or copying custom helpers (`DeepPartial` / `Mutable` / `ValueOf` / `Prettify`) → read the quick-reference table in [utility-types.md](references/utility-types.md).**

📚 **When choosing a type-level pattern (cheat sheet) or copying the non-obvious ones — type guards, distributive conditionals, branded/nominal types, recursive dotted paths, staged builders → read [advanced-patterns.md](references/advanced-patterns.md).**

---

## Pattern Selection Decision Tree

| Scenario | Use | Avoid |
|----------|-----|-------|
| Object shape, will be extended | `interface User { ... }` | `type User = { ... }` |
| Union, intersection, mapped, conditional | `type Status = A \| B` | `interface Status` (cannot union) |
| External / untrusted input | `unknown` + narrowing | `any` |
| Object literal with literal-type preservation | `} satisfies T` | `: T` annotation (widens) |
| Validate without losing inference | `as const satisfies T` | bare `as T` cast |
| Reusable runtime narrowing | type predicate `x is T` | inline `as T` |
| Defensive narrowing inside one function | assertion fn `asserts x is T` | repeated `if`-throw blocks |
| Domain ID confused with raw `string` | branded type `Brand<string, 'UserId'>` | bare `string` parameter |
| Optional handler value | `x?.y ?? fallback` | `x! .y \|\| fallback` |
| Iterating a stream once | Iterator Helpers `iter.map(...).take(10)` (TS 5.6+) | `Array.from(iter).map(...)` (eager) |

---

## TypeScript Version Features

| Version | Released | Key Features |
|---------|----------|--------------|
| **4.7** | May 2022 | ESM support, `moduleSuffixes` |
| **4.9** | Nov 2022 | `satisfies` operator, auto-accessors |
| **5.0** | Mar 2023 | Stage-3 decorators, `const` type parameters |
| **5.2** | Aug 2023 | `using` declarations (explicit resource management) |
| **5.4** | Mar 2024 | `NoInfer<T>`, preserved narrowing in closures |
| **5.5** | Jun 2024 | Inferred type predicates, regex syntax checking |
| **5.6** | Sep 2024 | Iterator Helper methods, dead-code detection, `--noCheck`, region-prioritized diagnostics |
| **5.7** | Nov 2024 | `--rewriteRelativeImportExtensions`, uninitialized checks in nested functions |
| **5.8** | Mar 2025 | Granular conditional return-type checks, `--erasableSyntaxOnly` (Node native TS), `--module node18` stable |

For releases newer than this table, check the official TypeScript release notes — do not assume features or flags from memory.

---

## When Configuring tsconfig.json

### 🔴 BLOCKING — `strict: true` is mandatory

**Why** : every flag inside `strict` (`strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `alwaysStrict`, `useUnknownInCatchVariables`, `strictBuiltinIteratorReturn`) closes a soundness hole that turns into a runtime crash. Disabling any of them silently re-introduces `any` in dozens of code paths.

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,        // arr[i] → T | undefined
    "noImplicitOverride": true,              // requires `override` keyword
    "noPropertyAccessFromIndexSignature": true,
    "exactOptionalPropertyTypes": true,      // `?:` ≠ `| undefined`
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true     // TS 5.6+
  }
}
```

### 🔴 BLOCKING — Choose `moduleResolution` deliberately

**Why** : `node` (legacy) silently resolves paths in ways modern bundlers don't. `bundler` matches Vite/esbuild/Rollup. `nodenext` is the only safe choice when emitting ESM for Node runtime (enforces explicit `.js` extensions).

| Target runtime | `moduleResolution` |
|----------------|--------------------|
| Vite, esbuild, Rollup, Webpack 5 | `"bundler"` |
| Node ≥ 22 emitting ESM/CJS | `"nodenext"` |
| Library shipping both ESM and CJS | `"nodenext"` + dual-package exports |

### 🟡 WARNING — Enable `verbatimModuleSyntax`

Forces explicit `import type` / `export type` separation — required for TS 5.8+ Node native execution (`--erasableSyntaxOnly`).

---

## When Defining Types

### 🔴 BLOCKING — Never use `any`

**Why** : `any` disables type checking *transitively* — every value derived from an `any` becomes `any`. A single `any` at an API boundary erases types across hundreds of downstream lines. `unknown` forces narrowing at the consumption site, keeping the type system honest.

```typescript
// 🔴 WRONG
function process(data: any) {
  return data.value;        // no check, propagates any to the caller
}

// ✅ CORRECT
function process(data: unknown): string {
  if (typeof data === 'object' && data !== null && 'value' in data) {
    return String(data.value);
  }
  throw new Error('Invalid data');
}
```

### 🔴 BLOCKING — Never use non-null assertion (`!`) as a shortcut

**Why** : `!` tells the compiler "trust me, not null" with no runtime check — when wrong, the call site throws `Cannot read properties of undefined` instead of failing fast at the type level. Use proper narrowing or assertion functions instead.

```typescript
// 🔴 WRONG
const name = user!.profile!.name;

// ✅ CORRECT
const name = user?.profile?.name ?? 'Anonymous';
```

### 🔴 BLOCKING — `interface` for object shapes, `type` for unions/intersections/mapped

**Why** : `interface` supports declaration merging and produces clearer error messages on extension chains. `type` is the only way to express unions, intersections, mapped types, conditional types, and template-literal types. Mixing them inverts the affordance — using `interface` for a union forces a discriminator field invention.

```typescript
// 🔴 WRONG — interface for a union (impossible cleanly)
interface Status { type: 'loading' | 'success' | 'error'; }

// ✅ CORRECT — discriminated union
type Status =
  | { type: 'loading' }
  | { type: 'success'; data: string }
  | { type: 'error'; error: Error };
```

---

## When Using Generics

### 🔴 BLOCKING — Constrain every generic

**Why** : an unconstrained `<T>` accepts `unknown`, including primitives, `null`, and `undefined`. The body cannot safely access any property without first narrowing — at which point the constraint should have been declared.

```typescript
// 🔴 WRONG
function merge<T, U>(a: T, b: U): T & U { return { ...a, ...b }; }
//                                                ↑ TS error: spread on non-object

// ✅ CORRECT
function merge<TBase extends object, TExtension extends object>(
  base: TBase,
  extension: TExtension,
): TBase & TExtension {
  return { ...base, ...extension };
}
```

### 🔴 BLOCKING — Meaningful generic names

**Why** : `T`, `U`, `V` carry no domain signal. After two type parameters the reader has to scroll back to the signature on every usage. Prefix with `T` and name the role (`TItem`, `TKey`, `TPayload`).

### 🟡 WARNING — More than 3 generic parameters is a code smell

Refactor into two functions or use an options object with a single generic.

### 🟢 BEST PRACTICE — `<const T>` (TS 5.0+) and `NoInfer<T>` (TS 5.4+)

```typescript
// const type parameter — preserves literal types without `as const` at call site
function defineRoutes<const T extends readonly { path: string }[]>(routes: T): T {
  return routes;
}
const r = defineRoutes([{ path: '/' }, { path: '/about' }]);
// r is readonly [{ readonly path: '/' }, { readonly path: '/about' }]

// NoInfer — exclude one position from inference
function createFSM<T extends string>(initial: NoInfer<T>, states: readonly T[]) {}
createFSM('a', ['a', 'b', 'c'] as const);  // OK
createFSM('d', ['a', 'b', 'c'] as const);  // ❌ 'd' not in 'a' | 'b' | 'c'
```

---

## When Narrowing Types

### 🔴 BLOCKING — Discriminated unions over type assertions

**Why** : a cast (`as T`) silences the compiler at compile time but does no runtime check. A discriminated union with `switch` on the discriminator is exhaustive — adding a new variant forces every consumer to handle it.

```typescript
// 🔴 WRONG
function handle(res: Success | Failure) {
  if ((res as Success).data) console.log((res as Success).data);
}

// ✅ CORRECT — `in` operator narrows safely
function handle(res: Success | Failure) {
  if ('data' in res) console.log(res.data);
  else console.error(res.error);
}

// ✅ CORRECT — exhaustive switch with `never` check
function handle(res: Success | Failure | Pending): string {
  switch (res.status) {
    case 'success': return res.data;
    case 'failure': return res.error.message;
    case 'pending': return '...';
    default: {
      const _exhaustive: never = res;
      throw new Error(`Unhandled: ${JSON.stringify(_exhaustive)}`);
    }
  }
}
```

### 🟢 BEST PRACTICE — Type predicates and assertion functions

📚 **When a narrowing check is reused in 3+ call sites or needs to throw on failure → read [advanced-patterns.md](references/advanced-patterns.md) (Type Guards section).**

---

## When Handling Null / Undefined

### 🔴 BLOCKING — Use `?.` and `??`, never `||` for defaults

**Why** : `||` falls back on every falsy value (`0`, `''`, `false`, `NaN`) — silently corrupts numeric counters, empty-string flags, and boolean toggles. `??` falls back only on `null` / `undefined`.

```typescript
// 🔴 WRONG
const count = data.count || 10;       // count=0 becomes 10
const enabled = config.enabled || true; // enabled=false becomes true

// ✅ CORRECT
const count = data.count ?? 10;
const enabled = config.enabled ?? true;
```

---

## When Working with Arrays

### 🔴 BLOCKING — Enable `noUncheckedIndexedAccess` and handle `T | undefined`

**Why** : without this flag, `arr[0]` is typed `T` even when the array may be empty — a guaranteed runtime crash on `.toUpperCase()` of `undefined`. The flag forces the developer to acknowledge the gap.

```typescript
// With noUncheckedIndexedAccess: true
function getFirst<T>(items: readonly T[]): T {
  const first = items[0];                       // T | undefined
  if (first === undefined) throw new Error('Array is empty');
  return first;
}
```

### 🔴 BLOCKING — `readonly` for parameters that should not mutate

**Why** : a function accepting `T[]` may sort, splice, or reverse the array in place — the caller cannot tell from the signature. `readonly T[]` makes the contract explicit and the compiler enforces it.

---

## When Using Async / Await

### 🔴 BLOCKING — Always declare `Promise<T>` return types on `async` functions

**Why** : an inferred return type of `Promise<any>` (when calling `res.json()` without typing) propagates `any` to every caller. Explicit `Promise<User>` puts a soundness boundary at the I/O edge.

### 🔴 BLOCKING — Never use `async` void except for true fire-and-forget event handlers

**Why** : an `async` function returning `void` silently swallows rejections — Node terminates with `UnhandledPromiseRejection` and the original stack is lost. Wrap event handlers with explicit `try/catch` and log the error.

```typescript
// 🔴 WRONG — typed nothing, swallows JSON parse errors, swallows non-2xx
async function fetchUser(id: string) {
  const res = await fetch(`/api/users/${id}`);
  return res.json();
}

// ✅ CORRECT
async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
  return (await res.json()) as User;
}
```

### 🟢 BEST PRACTICE — Result type for expected failures

```typescript
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };

async function fetchUserSafe(id: string): Promise<Result<User>> {
  try { return { ok: true, value: await fetchUser(id) }; }
  catch (error) { return { ok: false, error: error as Error }; }
}
```

---

## When Validating Object Literals

### 🟢 BEST PRACTICE — `satisfies` (TS 4.9+) for literal preservation + validation

**Use** : config maps, route tables, theme objects, action maps where you need both schema validation and preserved literal types.

```typescript
// 🔴 WRONG — annotation widens the literals
const routes: Record<string, { path: string }> = {
  home: { path: '/' },
  about: { path: '/about' },
};
routes.home.path; // type: string (widened)

// ✅ CORRECT
const routes = {
  home: { path: '/' },
  about: { path: '/about' },
} satisfies Record<string, { path: string }>;
routes.home.path; // type: '/' (literal preserved)
```

---

## When Working with Iterators (TS 5.6+)

### 🟢 BEST PRACTICE — Iterator Helper methods over eager array conversion

```typescript
// 🔴 WRONG — materializes the entire stream
const first10 = Array.from(stream).map(parse).slice(0, 10);

// ✅ CORRECT — lazy, terminates after 10
const first10 = stream.map(parse).take(10).toArray();
```

---

## When Modeling Domain IDs

### 🟢 BEST PRACTICE — Branded types for nominal safety

📚 **When two `string` IDs must not be interchangeable (`UserId` vs `OrderId`), or when validating an `Email` should produce a non-falsifiable type → read [advanced-patterns.md](references/advanced-patterns.md) (Branded/Nominal Types section).**

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] No `any` types — `unknown` + narrowing instead
- [ ] No non-null assertion (`!`) — proper narrowing or assertion function
- [ ] `strict: true` + `noUncheckedIndexedAccess: true` in `tsconfig.json`
- [ ] All exported / public functions have explicit return types
- [ ] All generics are constrained with `extends`
- [ ] All public `async` functions declare `Promise<T>`
- [ ] Every `switch` on a discriminated union ends with a `never` exhaustiveness check
- [ ] No `||` for defaults of nullable values — use `??`

### 🟡 WARNING
- [ ] `interface` for object shapes, `type` for unions/intersections/mapped
- [ ] `readonly` for non-mutating parameters and immutable data
- [ ] No `async` function returning `void` (except DOM event handlers with internal `try/catch`)
- [ ] Generic parameters named `TItem` / `TKey` / `TPayload`, not `T` / `U` / `V`
- [ ] No more than 3 generic parameters per function
- [ ] `verbatimModuleSyntax` enabled if targeting Node native TS execution

### 🟢 BEST PRACTICE
- [ ] `satisfies` for validated literal constants
- [ ] `as const` for readonly tuples and literal arrays
- [ ] `<const T>` type parameters where literal preservation matters (TS 5.0+)
- [ ] `NoInfer<T>` to exclude positions from inference (TS 5.4+)
- [ ] Branded types for domain IDs that must not be interchangeable
- [ ] Iterator Helpers (`.map().take()`) over eager `Array.from(...).slice()` (TS 5.6+)

---

## Related Skills

- `common-frontend-angular` — TypeScript inside Angular components and services
- `common-frontend-testing` — Type-safe test fixtures and mocks
- `common-developer` — General coding principles (naming, comments, error handling)
- `common-rest-api` — REST contract design (request / response DTOs)
