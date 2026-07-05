# TypeScript Utility Types Reference

> Built-in utility types shipped with TypeScript, plus custom helpers commonly
> needed in application code. For type-level programming (conditional types,
> mapped types, template literals, branded types, real-world patterns), see
> `advanced-patterns.md`.

## Table of Contents

- [Built-in: Object Manipulation](#built-in-object-manipulation) — `Partial`, `Required`, `Readonly`, `Pick`, `Omit`, `Record`
- [Built-in: Union Manipulation](#built-in-union-manipulation) — `Exclude`, `Extract`, `NonNullable`
- [Built-in: Function Types](#built-in-function-types) — `ReturnType`, `Parameters`, `ConstructorParameters`, `InstanceType`, `ThisParameterType`, `OmitThisParameter`
- [Built-in: Promise / Async](#built-in-promise--async) — `Awaited`
- [Built-in: String Manipulation](#built-in-string-manipulation) — `Uppercase`, `Lowercase`, `Capitalize`, `Uncapitalize`
- [Built-in: NoInfer (TS 5.4+)](#built-in-noinfer-ts-54) — exclude positions from inference
- [Custom: Deep Helpers](#custom-deep-helpers) — `DeepPartial`, `DeepReadonly`, `DeepRequired`
- [Custom: Key Helpers](#custom-key-helpers) — `OptionalKeys`, `RequiredKeys`, `Mutable`, `ValueOf`
- [Custom: Display / Misc](#custom-display--misc) — `Prettify`, `Nullable`, `Maybe`
- [Quick Reference Table](#quick-reference-table)

---

## Built-in: Object Manipulation

```typescript
interface User { id: string; name: string; }

type PartialUser  = Partial<User>;            // { id?: string; name?: string }
type RequiredUser = Required<{ id?: string; name?: string }>; // { id: string; name: string }
type ReadonlyUser = Readonly<User>;            // { readonly id: string; readonly name: string }
type UserName     = Pick<User, 'name'>;        // { name: string }
type UserNoId     = Omit<User, 'id'>;          // { name: string }
type UserRoles    = Record<'admin' | 'user', boolean>; // { admin: boolean; user: boolean }
```

---

## Built-in: Union Manipulation

```typescript
type Status      = 'pending' | 'success' | 'error';
type NonPending  = Exclude<Status, 'pending'>;          // 'success' | 'error'
type OnlyStrings = Extract<string | number, string>;     // string
type Definite    = NonNullable<string | null | undefined>; // string
```

---

## Built-in: Function Types

```typescript
function getUser() { return { id: '1', name: 'John' }; }
type User = ReturnType<typeof getUser>;     // { id: string; name: string }

function createUser(name: string, age: number) {}
type Params = Parameters<typeof createUser>; // [name: string, age: number]

class Service { constructor(public url: string, private key: string) {} }
type ServiceParams   = ConstructorParameters<typeof Service>; // [url: string, key: string]
type ServiceInstance = InstanceType<typeof Service>;          // Service

// `this` parameter helpers
function format(this: Date, suffix: string) { return this.toISOString() + suffix; }
type FormatThis = ThisParameterType<typeof format>;   // Date
type FormatBare = OmitThisParameter<typeof format>;   // (suffix: string) => string
```

---

## Built-in: Promise / Async

```typescript
type AsyncUser = Promise<{ id: string }>;
type User      = Awaited<AsyncUser>;             // { id: string }

// Recursively unwraps nested Promises
type DeepAsync = Promise<Promise<Promise<string>>>;
type Resolved  = Awaited<DeepAsync>;             // string
```

---

## Built-in: String Manipulation

```typescript
type Upper = Uppercase<'hello'>;     // 'HELLO'
type Lower = Lowercase<'HELLO'>;     // 'hello'
type Cap   = Capitalize<'hello'>;    // 'Hello'
type Uncap = Uncapitalize<'Hello'>;  // 'hello'
```

For dynamic key transformations using these (e.g. `getName` from `name`),
see the Template Literal Types section in `advanced-patterns.md`.

---

## Built-in: NoInfer (TS 5.4+)

`NoInfer<T>` excludes a position from generic inference, forcing the inference
to come from another position only.

```typescript
// Without NoInfer — `T` inferred from BOTH positions, swallowing the constraint
function createFSM<T extends string>(initial: T, states: readonly T[]) {}
createFSM('d', ['a', 'b', 'c'] as const);
// T inferred as 'a' | 'b' | 'c' | 'd' — 'd' silently accepted ❌

// With NoInfer — `T` inferred from `states` only; `initial` must conform
function createFSM<T extends string>(initial: NoInfer<T>, states: readonly T[]) {}
createFSM('a', ['a', 'b', 'c'] as const);  // ✅ OK
createFSM('d', ['a', 'b', 'c'] as const);  // ❌ '"d"' is not assignable to '"a" | "b" | "c"'
```

Common applications: state-machine APIs, builder constraints, locale-keyed
translation lookups.

---

## Custom: Deep Helpers

### DeepPartial — recursively make all properties optional

```typescript
type DeepPartial<T> = T extends object
  ? { [P in keyof T]?: DeepPartial<T[P]> }
  : T;

interface Config {
  server: { host: string; port: number };
  db:     { url: string };
}
type PartialConfig = DeepPartial<Config>;
// { server?: { host?: string; port?: number }; db?: { url?: string } }
```

### DeepReadonly — recursively freeze every property

```typescript
type DeepReadonly<T> = T extends object
  ? { readonly [P in keyof T]: DeepReadonly<T[P]> }
  : T;
```

### DeepRequired — recursively strip `?` markers

```typescript
type DeepRequired<T> = T extends object
  ? { [P in keyof T]-?: DeepRequired<T[P]> }
  : T;
```

---

## Custom: Key Helpers

### OptionalKeys / RequiredKeys — extract optional or required keys

```typescript
type OptionalKeys<T> = {
  [K in keyof T]-?: undefined extends T[K] ? K : never;
}[keyof T];

type RequiredKeys<T> = {
  [K in keyof T]-?: undefined extends T[K] ? never : K;
}[keyof T];

interface Example { a: string; b?: number; c: boolean | undefined; }
type Opt = OptionalKeys<Example>; // 'b'
type Req = RequiredKeys<Example>; // 'a' | 'c'
```

### Mutable — strip `readonly` modifiers

```typescript
type Mutable<T> = { -readonly [P in keyof T]: T[P]; };
type MutableUser = Mutable<Readonly<{ id: string }>>; // { id: string }
```

### ValueOf — union of all property values

```typescript
type ValueOf<T> = T[keyof T];

const STATUS = { PENDING: 'pending', SUCCESS: 'success' } as const;
type StatusValue = ValueOf<typeof STATUS>; // 'pending' | 'success'
```

---

## Custom: Display / Misc

### Prettify — flatten intersections for clearer IDE hover

```typescript
type Prettify<T> = { [K in keyof T]: T[K] } & {};

type Complex = { a: string } & { b: number };
type Pretty  = Prettify<Complex>; // shown as { a: string; b: number } in tooltips
```

### Nullable / Maybe

```typescript
type Nullable<T> = T | null;
type Maybe<T>    = T | null | undefined;
```

---

## Quick Reference Table

| Helper | Purpose | Example |
|--------|---------|---------|
| `Partial<T>` | All properties optional | Update DTO from full entity |
| `Required<T>` | All properties required | Strip `?:` after defaults applied |
| `Readonly<T>` | All properties `readonly` | Freeze a config object |
| `Pick<T,K>` | Select named keys | Public-view DTO |
| `Omit<T,K>` | Exclude named keys | Server-only fields stripped |
| `Record<K,V>` | Object indexed by `K` | Translation map, route table |
| `Exclude<T,U>` | Remove union members | Status minus `'pending'` |
| `Extract<T,U>` | Keep union intersection | Filter union to one shape |
| `NonNullable<T>` | Remove `null \| undefined` | After narrowing check |
| `ReturnType<F>` | Function return type | Infer reducer state shape |
| `Parameters<F>` | Function args as tuple | Wrap a function with same signature |
| `ConstructorParameters<C>` | Constructor args as tuple | Forward to factory |
| `InstanceType<C>` | Class instance type | Reference DI bean type |
| `Awaited<T>` | Unwrap `Promise<T>` | Reducer over async result |
| `Uppercase<S>` / `Capitalize<S>` | String literal transforms | Compose template literal types |
| `NoInfer<T>` (5.4+) | Skip a position during inference | Constrain initial state to declared union |
| `DeepPartial<T>` (custom) | Recursive `Partial` | Patch payload for nested config |
| `Mutable<T>` (custom) | Strip `readonly` | Initialize from a frozen config |
| `ValueOf<T>` (custom) | Union of value types | Enum from `as const` object |
| `Prettify<T>` (custom) | Flatten intersections | Better IDE hover on combined types |
