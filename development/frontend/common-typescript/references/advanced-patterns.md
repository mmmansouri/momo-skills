# TypeScript Advanced Patterns Reference

> Decision surface + the non-obvious patterns worth copying. Standard type-level
> TypeScript (conditional / mapped / template-literal basics, variadic tuples,
> `infer`) is native knowledge — pick from the cheat sheet, then write the idiom
> directly.

## Table of Contents

- [Pattern Cheat Sheet](#pattern-cheat-sheet)
- [Type Guards](#type-guards) — predicate + assertion function
- [Distributive Conditional Types](#distributive-conditional-types)
- [Branded / Nominal Types](#branded--nominal-types)
- [Recursive Dotted Paths](#recursive-dotted-paths)
- [Builder Pattern with Types](#builder-pattern-with-types)

---

## Pattern Cheat Sheet

| Pattern | Use Case | Key Operator |
|---------|----------|--------------|
| Discriminated Union | State machines, API results | literal field `+` `switch` `+` `never` |
| Type Guard (predicate) | Reusable runtime narrowing | `x is T` |
| Assertion Function | Boundary validation that throws | `asserts x is T` |
| Conditional Type | Transform types based on shape | `T extends U ? X : Y` |
| Distributive Conditional | Map over union members | naked `T extends U` |
| Mapped Type | Bulk property transform | `[K in keyof T]` |
| Key Remapping | Rename / filter keys | `[K in keyof T as ...]` |
| Template Literal Type | String type composition | `` `${X}${Y}` `` |
| Branded Type | Nominal safety on structural types | `T & { __brand: B }` |
| Variadic Tuple | Preserve tuple shape through fn | `[...T, ...U]` |
| Recursive Type | Nested structures, dotted paths | self-reference `+` `infer` |
| Staged Builder | Method ordering enforced by types | accumulator type parameter |

---

## Type Guards

```typescript
// Predicate — reusable narrowing, composes with .filter()
function isUser(value: unknown): value is User {
  return typeof value === 'object' && value !== null && 'id' in value;
}

// Assertion function — throws on failure, narrows afterwards
function assertUser(value: unknown): asserts value is User {
  if (!isUser(value)) throw new Error('Not a User');
}
```

---

## Distributive Conditional Types

A conditional type distributes over a union when the checked type is a *naked*
type parameter. Wrap in a tuple to disable distribution.

```typescript
type ToArray<T>        = T extends any   ? T[] : never;
type ToArrayNonDist<T> = [T] extends [any] ? T[] : never;

type E = ToArray<string | number>;          // string[] | number[]
type F = ToArrayNonDist<string | number>;   // (string | number)[]
```

---

## Branded / Nominal Types

```typescript
type Brand<T, B extends string> = T & { readonly __brand: B };

type UserId  = Brand<string, 'UserId'>;
type OrderId = Brand<string, 'OrderId'>;

const createUserId = (id: string): UserId => id as UserId;

function getUser(id: UserId): User { /* … */ }
getUser(createUserId('user-123'));  // ✅ OK
// getUser('user-123');             // ❌ string not assignable to UserId

// ✅ Validated brands — only the validator can produce the type
type Email = Brand<string, 'Email'>;

function parseEmail(input: string): Email | null {
  const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input);
  return ok ? (input as Email) : null;
}
```

Use cases : domain IDs, validated strings (`Email`, `Url`, `NonEmptyString`),
units (`Cents`, `Dollars`, `Milliseconds`).

---

## Recursive Dotted Paths

```typescript
type Path<T, K extends keyof T = keyof T> = K extends string
  ? T[K] extends Record<string, any>
    ? K | `${K}.${Path<T[K]>}`
    : K
  : never;

type PathValue<T, P extends string> = P extends `${infer K}.${infer Rest}`
  ? K extends keyof T ? PathValue<T[K], Rest> : never
  : P extends keyof T ? T[P] : never;

interface Config {
  server:   { port: number; host: string };
  database: { connection: { url: string } };
}

type ConfigPath = Path<Config>;
// 'server' | 'server.port' | 'server.host' | 'database' | 'database.connection' | 'database.connection.url'
type PortType = PathValue<Config, 'server.port'>;  // number
```

---

## Builder Pattern with Types

Staged builders prevent calling `.build()` before required steps are complete.

```typescript
interface QueryBuilder<T extends object = {}> {
  select<K extends string>(fields: K[]):
    QueryBuilder<T & { select: K[] }>;
  from<Table extends string>(table: Table):
    QueryBuilder<T & { from: Table }>;
  where<Field extends string>(field: Field, value: unknown):
    QueryBuilder<T & { where: { field: Field; value: unknown } }>;
  build(): T extends { select: any; from: any } ? string : never;
}

// Usage — `.build()` returns `never` until both `select` and `from` are called
const query = createQuery()
  .select(['id', 'name'])
  .from('users')
  .where('id', 1)
  .build();           // ✅ string

// createQuery().select(['id']).build();  // ❌ Type 'never' is not callable
```
