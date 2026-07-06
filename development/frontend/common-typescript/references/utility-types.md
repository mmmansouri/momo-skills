# TypeScript Utility Types Reference

> Custom helpers to copy into application code, plus a quick-reference table.
> The built-in utility types (`Partial`, `Pick`, `Omit`, `ReturnType`, `Awaited`, …)
> are standard TypeScript knowledge and are intentionally not re-explained here.
> For type-level programming patterns, see `advanced-patterns.md`.

## Table of Contents

- [Custom: Deep Helpers](#custom-deep-helpers) — `DeepPartial`, `DeepReadonly`, `DeepRequired`
- [Custom: Key Helpers](#custom-key-helpers) — `OptionalKeys`, `RequiredKeys`, `Mutable`, `ValueOf`
- [Custom: Display / Misc](#custom-display--misc) — `Prettify`, `Nullable`, `Maybe`
- [Quick Reference Table](#quick-reference-table)

---

## Custom: Deep Helpers

```typescript
type DeepPartial<T> = T extends object
  ? { [P in keyof T]?: DeepPartial<T[P]> }
  : T;

type DeepReadonly<T> = T extends object
  ? { readonly [P in keyof T]: DeepReadonly<T[P]> }
  : T;

type DeepRequired<T> = T extends object
  ? { [P in keyof T]-?: DeepRequired<T[P]> }
  : T;
```

---

## Custom: Key Helpers

```typescript
type OptionalKeys<T> = {
  [K in keyof T]-?: undefined extends T[K] ? K : never;
}[keyof T];

type RequiredKeys<T> = {
  [K in keyof T]-?: undefined extends T[K] ? never : K;
}[keyof T];

type Mutable<T> = { -readonly [P in keyof T]: T[P]; };

type ValueOf<T> = T[keyof T];

const STATUS = { PENDING: 'pending', SUCCESS: 'success' } as const;
type StatusValue = ValueOf<typeof STATUS>; // 'pending' | 'success'
```

---

## Custom: Display / Misc

```typescript
// Prettify — flatten intersections for clearer IDE hover
type Prettify<T> = { [K in keyof T]: T[K] } & {};

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
| `NoInfer<T>` (5.4+) | Skip a position during inference | Constrain initial state to declared union (worked example in SKILL.md) |
| `DeepPartial<T>` (custom) | Recursive `Partial` | Patch payload for nested config |
| `Mutable<T>` (custom) | Strip `readonly` | Initialize from a frozen config |
| `ValueOf<T>` (custom) | Union of value types | Enum from `as const` object |
| `Prettify<T>` (custom) | Flatten intersections | Better IDE hover on combined types |
