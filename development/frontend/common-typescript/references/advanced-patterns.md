# Advanced TypeScript Patterns

> Type-level programming and real-world patterns. For built-in utility types
> (`Partial`, `Pick`, `Omit`, `Awaited`, `NoInfer`, etc.) and custom helpers
> (`DeepPartial`, `Mutable`, `ValueOf`), see `utility-types.md`.

## Table of Contents

- [Discriminated Unions (Tagged Unions)](#discriminated-unions-tagged-unions) — type-safe state, API responses
- [Type Guards](#type-guards) — user-defined predicates, assertion functions
- [Conditional Types](#conditional-types) — `T extends U ? X : Y`, `infer`, distributive types
- [Mapped Types](#mapped-types) — bulk property transforms, key remapping (TS 4.1+)
- [Template Literal Types](#template-literal-types) — string composition, route param extraction
- [Generic Constraints & Inference](#generic-constraints--inference) — `extends keyof`, `infer` patterns
- [Branded / Nominal Types](#branded--nominal-types) — `UserId` vs `OrderId`, validated `Email`
- [Variadic Tuple Types (TS 4.0+)](#variadic-tuple-types-ts-40) — spread tuples, partial application
- [Recursive Types](#recursive-types) — JSON, dotted-path access
- [Builder Pattern with Types](#builder-pattern-with-types) — staged builders
- [Real-World: Type-Safe Event Emitter](#real-world-type-safe-event-emitter)
- [Real-World: Type-Safe API Client](#real-world-type-safe-api-client)
- [Pattern Cheat Sheet](#pattern-cheat-sheet)

---

## Discriminated Unions (Tagged Unions)

The most powerful pattern for type-safe state and result modeling. A literal
field (`status`, `type`, `kind`, `ok`) acts as the discriminator — narrowing
on it enables exhaustiveness checking.

```typescript
// ✅ State machine with literal discriminator
type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

function render<T>(state: AsyncState<T>): string {
  switch (state.status) {
    case 'idle':    return 'Waiting…';
    case 'loading': return 'Loading…';
    case 'success': return `Got: ${state.data}`;     // data narrowed in
    case 'error':   return `Err: ${state.error.message}`; // error narrowed in
    default: {
      const _exhaustive: never = state;              // forces handling new variants
      throw new Error(`Unhandled: ${JSON.stringify(_exhaustive)}`);
    }
  }
}

// ✅ API result envelope
type ApiResponse<T> =
  | { ok: true;  data: T }
  | { ok: false; error: string };

const result = await fetchUser('123');
if (result.ok) console.log(result.data.name);  // narrowed
else            console.error(result.error);   // narrowed
```

---

## Type Guards

### User-Defined Type Guards (predicate `x is T`)

```typescript
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' && value !== null &&
    'id' in value && 'email' in value &&
    typeof (value as User).id === 'string' &&
    typeof (value as User).email === 'string'
  );
}

// ✅ Narrowing variants of a union
function isErrorState<T>(s: AsyncState<T>): s is { status: 'error'; error: Error } {
  return s.status === 'error';
}

// ✅ Filter with type predicate — array element type narrows
const mixed: (string | number)[] = [1, 'two', 3, 'four'];
const strings: string[] = mixed.filter((x): x is string => typeof x === 'string');
```

> TS 5.5+ infers type predicates automatically from simple boolean returns;
> the explicit `x is T` annotation remains required for object-shape checks.

### Assertion Functions (`asserts x is T`)

Throws when narrowing fails — useful at boundaries (parsed config, decoded JWT).

```typescript
function assertIsString(value: unknown): asserts value is string {
  if (typeof value !== 'string') throw new Error(`Expected string, got ${typeof value}`);
}

function assertDefined<T>(value: T | null | undefined): asserts value is T {
  if (value === null || value === undefined) throw new Error('Value must be defined');
}

function processInput(input: unknown) {
  assertIsString(input);
  console.log(input.toUpperCase());  // input narrowed to string from here
}
```

---

## Conditional Types

```typescript
// Syntax: T extends U ? X : Y

type Flatten<T> = T extends Array<infer U> ? U : T;
type A = Flatten<string[]>;            // string
type B = Flatten<number>;              // number
type C = Flatten<(string | number)[]>; // string | number

type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
type MyAwaited<T>    = T extends Promise<infer U> ? MyAwaited<U> : T;
type D = MyAwaited<Promise<Promise<string>>>; // string
```

### Distributive Conditional Types

A conditional type distributes over a union when the checked type is a *naked*
type parameter. Wrap in a tuple to disable distribution.

```typescript
type ToArray<T>        = T extends any   ? T[] : never;
type ToArrayNonDist<T> = [T] extends [any] ? T[] : never;

type E = ToArray<string | number>;          // string[] | number[]
type F = ToArrayNonDist<string | number>;   // (string | number)[]
```

---

## Mapped Types

```typescript
// ✅ Reimplementations of built-ins (use the built-in versions in real code)
type MyPartial<T>   = { [P in keyof T]?: T[P]; };
type MyRequired<T>  = { [P in keyof T]-?: T[P]; };
type MyReadonly<T>  = { readonly [P in keyof T]: T[P]; };
type MyMutable<T>   = { -readonly [P in keyof T]: T[P]; };

// ✅ Transform property types
type Stringify<T>   = { [P in keyof T]: string; };
type NullableAll<T> = { [P in keyof T]: T[P] | null; };
```

### Key Remapping with `as` (TS 4.1+)

```typescript
// ✅ Rename keys
type Getters<T> = {
  [P in keyof T as `get${Capitalize<string & P>}`]: () => T[P];
};

interface Person { name: string; age: number; }
type PersonGetters = Getters<Person>;
// { getName: () => string; getAge: () => number; }

// ✅ Filter keys by value type — `as never` removes the key
type FilterByType<T, U> = {
  [P in keyof T as T[P] extends U ? P : never]: T[P];
};

type StringProps = FilterByType<{ name: string; age: number }, string>;
// { name: string }

// ✅ Prefix keys
type PrefixedKeys<T, P extends string> = {
  [K in keyof T as `${P}${string & K}`]: T[K];
};
type Prefixed = PrefixedKeys<{ name: string }, 'user_'>;  // { user_name: string }
```

---

## Template Literal Types

```typescript
// ✅ Compose strings
type EventName<T extends string> = `on${Capitalize<T>}`;
type ClickEvent = EventName<'click'>;  // 'onClick'

// ✅ Cartesian product over unions
type Alignment     = 'left' | 'center' | 'right';
type VerticalAlign = 'top' | 'middle' | 'bottom';
type Position      = `${Alignment}-${VerticalAlign}`;
// 'left-top' | 'left-middle' | … | 'right-bottom'

// ✅ Parse route params
type ExtractRouteParams<T extends string> =
  T extends `${string}:${infer Param}/${infer Rest}`
    ? Param | ExtractRouteParams<Rest>
    : T extends `${string}:${infer Param}`
      ? Param
      : never;

type Params = ExtractRouteParams<'/users/:userId/posts/:postId'>;
// 'userId' | 'postId'
```

---

## Generic Constraints & Inference

### Constraining Generics

```typescript
// ✅ keyof for property access
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// ✅ Structural constraint
function longest<T extends { length: number }>(a: T, b: T): T {
  return a.length >= b.length ? a : b;
}
longest('hello', 'hi');           // OK (string has length)
longest([1, 2, 3], [1, 2]);       // OK (array has length)
longest({ length: 5 }, { length: 3 }); // OK (object literal)

// ✅ Constructor constraint
function createInstance<T>(ctor: new () => T): T {
  return new ctor();
}
```

### Inference with `infer`

```typescript
type ElementType<T> = T extends (infer U)[] ? U : never;
type ValueOf<T>     = T[keyof T];

// First / last tuple element
type First<T extends readonly unknown[]> = T extends readonly [infer F, ...unknown[]] ? F : never;
type Last<T  extends readonly unknown[]> = T extends readonly [...unknown[], infer L] ? L : never;

type X = First<[1, 2, 3]>;  // 1
type Y = Last<[1, 2, 3]>;   // 3
```

---

## Branded / Nominal Types

TypeScript is structurally typed — two `string`s are interchangeable even when
they represent different domain concepts. Branded types add a phantom marker.

```typescript
type Brand<T, B> = T & { readonly __brand: B };

type UserId  = Brand<string, 'UserId'>;
type OrderId = Brand<string, 'OrderId'>;

const createUserId  = (id: string): UserId  => id as UserId;
const createOrderId = (id: string): OrderId => id as OrderId;

function getUser(id: UserId): User { /* … */ }

const userId  = createUserId('user-123');
const orderId = createOrderId('order-456');

getUser(userId);          // ✅ OK
// getUser(orderId);      // ❌ OrderId not assignable to UserId
// getUser('user-123');   // ❌ string not assignable to UserId

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

## Variadic Tuple Types (TS 4.0+)

```typescript
// ✅ Concatenate tuple types
type Concat<T extends any[], U extends any[]> = [...T, ...U];
type AB = Concat<[1, 2], [3, 4]>;  // [1, 2, 3, 4]

// ✅ Function preserving tuple types
function concat<T extends any[], U extends any[]>(
  arr1: [...T],
  arr2: [...U],
): [...T, ...U] {
  return [...arr1, ...arr2];
}
const result = concat([1, 'hello'] as const, [true, 42] as const);
// type: readonly [1, 'hello', true, 42]

// ✅ Partial application
type PartialApply<F extends (...args: any) => any, Applied extends any[]> =
  F extends (...args: [...Applied, ...infer Rest]) => infer R
    ? (...args: Rest) => R
    : never;

function add(a: number, b: number, c: number): number { return a + b + c; }
type Add1 = PartialApply<typeof add, [number]>;          // (b: number, c: number) => number
type Add2 = PartialApply<typeof add, [number, number]>;  // (c: number) => number
```

---

## Recursive Types

```typescript
// ✅ JSON
type JsonPrimitive = string | number | boolean | null;
type JsonArray     = Json[];
type JsonObject    = { [key: string]: Json };
type Json          = JsonPrimitive | JsonArray | JsonObject;

// ✅ Dotted-path enumeration
type Path<T, K extends keyof T = keyof T> = K extends string
  ? T[K] extends Record<string, any>
    ? K | `${K}.${Path<T[K]>}`
    : K
  : never;

interface Config {
  server:   { port: number; host: string };
  database: { connection: { url: string } };
}

type ConfigPath = Path<Config>;
// 'server' | 'server.port' | 'server.host' | 'database' | 'database.connection' | 'database.connection.url'

// ✅ Get type at path
type PathValue<T, P extends string> = P extends `${infer K}.${infer Rest}`
  ? K extends keyof T ? PathValue<T[K], Rest> : never
  : P extends keyof T ? T[P] : never;

type PortType = PathValue<Config, 'server.port'>;             // number
type UrlType  = PathValue<Config, 'database.connection.url'>; // string
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

---

## Real-World: Type-Safe Event Emitter

```typescript
type EventMap = Record<string, any>;

interface TypedEventEmitter<Events extends EventMap> {
  on<K extends keyof Events>(event: K, listener: (data: Events[K]) => void): void;
  off<K extends keyof Events>(event: K, listener: (data: Events[K]) => void): void;
  emit<K extends keyof Events>(event: K, data: Events[K]): void;
}

interface AppEvents {
  userLoggedIn:  { userId: string; timestamp: Date };
  userLoggedOut: { userId: string };
  error:         Error;
}

declare const emitter: TypedEventEmitter<AppEvents>;

emitter.on('userLoggedIn', data => console.log(data.userId));               // ✅
emitter.emit('userLoggedIn', { userId: '123', timestamp: new Date() });     // ✅
// emitter.emit('userLoggedIn', { userId: '123' });                         // ❌ missing timestamp
```

---

## Real-World: Type-Safe API Client

```typescript
interface ApiEndpoints {
  '/users': {
    GET:  { response: User[] };
    POST: { body: CreateUserDto; response: User };
  };
  '/users/:id': {
    GET:    { response: User };
    PUT:    { body: UpdateUserDto; response: User };
    DELETE: { response: void };
  };
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

type ApiRequest<P extends keyof ApiEndpoints, M extends keyof ApiEndpoints[P]> =
  ApiEndpoints[P][M] extends { body: infer B } ? B : never;

type ApiResponse<P extends keyof ApiEndpoints, M extends keyof ApiEndpoints[P]> =
  ApiEndpoints[P][M] extends { response: infer R } ? R : never;

async function apiCall<
  P extends keyof ApiEndpoints,
  M extends keyof ApiEndpoints[P] & HttpMethod,
>(
  path: P,
  method: M,
  ...args: ApiRequest<P, M> extends never ? [] : [body: ApiRequest<P, M>]
): Promise<ApiResponse<P, M>> {
  return {} as any;
}

const users   = await apiCall('/users', 'GET');                                          // User[]
const newOne  = await apiCall('/users', 'POST', { name: 'John', email: 'j@e.com' });     // User
// apiCall('/users', 'POST');                                                            // ❌ body required
```

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
