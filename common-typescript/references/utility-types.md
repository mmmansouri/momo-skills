# TypeScript Utility Types Reference

## Built-in Utility Types

### Object Manipulation

```typescript
// Partial<T> - All properties optional
interface User { id: string; name: string; }
type PartialUser = Partial<User>;
// { id?: string; name?: string; }

// Required<T> - All properties required
type Config = { host?: string; port?: number; };
type RequiredConfig = Required<Config>;
// { host: string; port: number; }

// Readonly<T> - All properties readonly
type ReadonlyUser = Readonly<User>;
// { readonly id: string; readonly name: string; }

// Pick<T, K> - Select properties
type UserName = Pick<User, 'name'>;
// { name: string; }

// Omit<T, K> - Exclude properties
type UserWithoutId = Omit<User, 'id'>;
// { name: string; }

// Record<K, V> - Object type with keys K and values V
type UserRoles = Record<'admin' | 'user' | 'guest', boolean>;
// { admin: boolean; user: boolean; guest: boolean; }
```

### Union Manipulation

```typescript
// Exclude<T, U> - Remove types from union
type Status = 'pending' | 'success' | 'error';
type NonPending = Exclude<Status, 'pending'>;
// 'success' | 'error'

// Extract<T, U> - Keep only matching types
type OnlyStrings = Extract<string | number | boolean, string>;
// string

// NonNullable<T> - Remove null and undefined
type MaybeString = string | null | undefined;
type DefiniteString = NonNullable<MaybeString>;
// string
```

### Function Types

```typescript
// ReturnType<T> - Extract return type
function getUser() { return { id: '1', name: 'John' }; }
type User = ReturnType<typeof getUser>;
// { id: string; name: string; }

// Parameters<T> - Extract parameters as tuple
function createUser(name: string, age: number) {}
type CreateUserParams = Parameters<typeof createUser>;
// [name: string, age: number]

// ConstructorParameters<T> - Extract constructor params
class Service { constructor(public url: string, private key: string) {} }
type ServiceParams = ConstructorParameters<typeof Service>;
// [url: string, key: string]

// InstanceType<T> - Extract instance type from class
type ServiceInstance = InstanceType<typeof Service>;
// Service
```

### Promise/Async Types

```typescript
// Awaited<T> - Unwrap Promise type
type AsyncUser = Promise<{ id: string }>;
type User = Awaited<AsyncUser>;
// { id: string }

// Works with nested promises
type DeepAsync = Promise<Promise<Promise<string>>>;
type Resolved = Awaited<DeepAsync>;
// string
```

### String Manipulation (Template Literal Types)

```typescript
// Uppercase<T>
type Upper = Uppercase<'hello'>; // 'HELLO'

// Lowercase<T>
type Lower = Lowercase<'HELLO'>; // 'hello'

// Capitalize<T>
type Cap = Capitalize<'hello'>; // 'Hello'

// Uncapitalize<T>
type Uncap = Uncapitalize<'Hello'>; // 'hello'
```

---

## Custom Utility Types

### Deep Partial

```typescript
type DeepPartial<T> = T extends object
  ? { [P in keyof T]?: DeepPartial<T[P]> }
  : T;

interface Config {
  server: { host: string; port: number };
  db: { url: string };
}

type PartialConfig = DeepPartial<Config>;
// { server?: { host?: string; port?: number }; db?: { url?: string } }
```

### Deep Readonly

```typescript
type DeepReadonly<T> = T extends object
  ? { readonly [P in keyof T]: DeepReadonly<T[P]> }
  : T;
```

### Nullable

```typescript
type Nullable<T> = T | null;
type NullableString = Nullable<string>; // string | null
```

### Optional Keys

```typescript
type OptionalKeys<T> = {
  [K in keyof T]-?: undefined extends T[K] ? K : never;
}[keyof T];

interface Example { a: string; b?: number; c: boolean | undefined; }
type OptKeys = OptionalKeys<Example>; // 'b'
```

### Required Keys

```typescript
type RequiredKeys<T> = {
  [K in keyof T]-?: undefined extends T[K] ? never : K;
}[keyof T];

type ReqKeys = RequiredKeys<Example>; // 'a' | 'c'
```

### Mutable (remove readonly)

```typescript
type Mutable<T> = {
  -readonly [P in keyof T]: T[P];
};

type MutableUser = Mutable<Readonly<User>>;
```

### Value Of

```typescript
type ValueOf<T> = T[keyof T];

const STATUS = { PENDING: 'pending', SUCCESS: 'success' } as const;
type StatusValue = ValueOf<typeof STATUS>; // 'pending' | 'success'
```

### Prettify (flatten intersections for better IDE display)

```typescript
type Prettify<T> = {
  [K in keyof T]: T[K];
} & {};

type Complex = { a: string } & { b: number };
type Pretty = Prettify<Complex>; // { a: string; b: number }
```

---

## Conditional Types

### Basic Pattern

```typescript
type IsString<T> = T extends string ? true : false;

type A = IsString<'hello'>; // true
type B = IsString<42>;      // false
```

### Infer Keyword

```typescript
// Extract array element type
type ElementOf<T> = T extends (infer E)[] ? E : never;
type Elem = ElementOf<string[]>; // string

// Extract function return type (manual ReturnType)
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

// Extract Promise value
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;
```

### Distributive Conditional Types

```typescript
// Distributes over union
type ToArray<T> = T extends any ? T[] : never;
type Result = ToArray<string | number>; // string[] | number[]

// Prevent distribution with tuple
type ToArrayNonDist<T> = [T] extends [any] ? T[] : never;
type Result2 = ToArrayNonDist<string | number>; // (string | number)[]
```

---

## Template Literal Types

### Basic Patterns

```typescript
type EventName<T extends string> = `on${Capitalize<T>}`;
type ClickEvent = EventName<'click'>; // 'onClick'

type Getters<T extends string> = `get${Capitalize<T>}`;
type Setters<T extends string> = `set${Capitalize<T>}`;
```

### Object Key Transformations

```typescript
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

interface Person { name: string; age: number; }
type PersonGetters = Getters<Person>;
// { getName: () => string; getAge: () => number; }
```

### Route Params

```typescript
type ExtractParams<T extends string> = 
  T extends `${string}:${infer Param}/${infer Rest}`
    ? Param | ExtractParams<Rest>
    : T extends `${string}:${infer Param}`
    ? Param
    : never;

type Params = ExtractParams<'/users/:userId/posts/:postId'>;
// 'userId' | 'postId'
```

---

## Mapped Types

### Basic Pattern

```typescript
type Optional<T> = {
  [K in keyof T]?: T[K];
};
```

### Key Remapping (4.1+)

```typescript
type PrefixedKeys<T, P extends string> = {
  [K in keyof T as `${P}${string & K}`]: T[K];
};

type Prefixed = PrefixedKeys<{ name: string }, 'user_'>;
// { user_name: string }
```

### Filter Keys

```typescript
type FilterByType<T, U> = {
  [K in keyof T as T[K] extends U ? K : never]: T[K];
};

interface Mixed { name: string; age: number; active: boolean; }
type StringKeys = FilterByType<Mixed, string>;
// { name: string }
```

---

## NoInfer (5.4+)

Prevents type inference at specific positions:

```typescript
// Without NoInfer - T inferred from both args
function createFSM<T extends string>(initial: T, states: T[]) {}
createFSM('a', ['a', 'b', 'c']); // T = 'a' | 'b' | 'c' ❌

// With NoInfer - T inferred only from states
function createFSM<T extends string>(initial: NoInfer<T>, states: T[]) {}
createFSM('a', ['a', 'b', 'c']); // T = 'a' | 'b' | 'c', initial must be one of them ✅
createFSM('d', ['a', 'b', 'c']); // Error: 'd' not in 'a' | 'b' | 'c'
```
