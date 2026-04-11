# Advanced TypeScript Patterns

> Reference for advanced TypeScript patterns, type-level programming, and real-world solutions.

---

## Discriminated Unions (Tagged Unions)

The most powerful pattern for type-safe state management:

```typescript
// ✅ CORRECT: Discriminated union with literal type discriminator
type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

function handleState<T>(state: AsyncState<T>): string {
  switch (state.status) {
    case 'idle':
      return 'Waiting...';
    case 'loading':
      return 'Loading...';
    case 'success':
      return `Got: ${state.data}`; // data is available here
    case 'error':
      return `Error: ${state.error.message}`; // error is available here
  }
}

// ✅ CORRECT: API response pattern
type ApiResponse<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

async function fetchUser(id: string): Promise<ApiResponse<User>> {
  try {
    const user = await api.get<User>(`/users/${id}`);
    return { ok: true, data: user };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : 'Unknown error' };
  }
}

// Usage with narrowing
const result = await fetchUser('123');
if (result.ok) {
  console.log(result.data.name); // TypeScript knows data exists
} else {
  console.error(result.error); // TypeScript knows error exists
}
```

---

## Type Guards

### User-Defined Type Guards

```typescript
// ✅ CORRECT: Type predicate with `is`
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'email' in value &&
    typeof (value as User).id === 'string' &&
    typeof (value as User).email === 'string'
  );
}

// ✅ CORRECT: Type guard for discriminated unions
function isErrorState<T>(state: AsyncState<T>): state is { status: 'error'; error: Error } {
  return state.status === 'error';
}

// ✅ CORRECT: Array filter with type guard
const mixed: (string | number)[] = [1, 'two', 3, 'four'];
const strings: string[] = mixed.filter((x): x is string => typeof x === 'string');
```

### Assertion Functions

```typescript
// ✅ CORRECT: Assertion function with `asserts`
function assertIsString(value: unknown): asserts value is string {
  if (typeof value !== 'string') {
    throw new Error(`Expected string, got ${typeof value}`);
  }
}

function assertDefined<T>(value: T | null | undefined): asserts value is T {
  if (value === null || value === undefined) {
    throw new Error('Value must be defined');
  }
}

// Usage
function processInput(input: unknown) {
  assertIsString(input);
  // TypeScript now knows input is string
  console.log(input.toUpperCase());
}
```

---

## Conditional Types

### Basic Conditional Types

```typescript
// Syntax: T extends U ? X : Y

// ✅ CORRECT: Extract non-nullable
type NonNullable<T> = T extends null | undefined ? never : T;

// ✅ CORRECT: Flatten arrays
type Flatten<T> = T extends Array<infer U> ? U : T;

type A = Flatten<string[]>;     // string
type B = Flatten<number>;       // number
type C = Flatten<(string | number)[]>; // string | number

// ✅ CORRECT: Extract return type
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

// ✅ CORRECT: Extract promise value
type Awaited<T> = T extends Promise<infer U> ? Awaited<U> : T;

type D = Awaited<Promise<Promise<string>>>; // string
```

### Distributive Conditional Types

```typescript
// Conditional types distribute over unions when T is naked type parameter

type ToArray<T> = T extends any ? T[] : never;

type E = ToArray<string | number>; // string[] | number[]

// ✅ CORRECT: Prevent distribution with tuple
type ToArrayNonDist<T> = [T] extends [any] ? T[] : never;

type F = ToArrayNonDist<string | number>; // (string | number)[]
```

---

## Mapped Types

### Basic Mapped Types

```typescript
// ✅ CORRECT: Make all properties optional
type Partial<T> = {
  [P in keyof T]?: T[P];
};

// ✅ CORRECT: Make all properties required
type Required<T> = {
  [P in keyof T]-?: T[P];
};

// ✅ CORRECT: Make all properties readonly
type Readonly<T> = {
  readonly [P in keyof T]: T[P];
};

// ✅ CORRECT: Remove readonly
type Mutable<T> = {
  -readonly [P in keyof T]: T[P];
};
```

### Advanced Mapped Types

```typescript
// ✅ CORRECT: Pick specific keys
type Pick<T, K extends keyof T> = {
  [P in K]: T[P];
};

// ✅ CORRECT: Omit specific keys
type Omit<T, K extends keyof any> = Pick<T, Exclude<keyof T, K>>;

// ✅ CORRECT: Transform property types
type Stringify<T> = {
  [P in keyof T]: string;
};

// ✅ CORRECT: Nullable version of all properties
type Nullable<T> = {
  [P in keyof T]: T[P] | null;
};

// ✅ CORRECT: Deep partial
type DeepPartial<T> = T extends object
  ? { [P in keyof T]?: DeepPartial<T[P]> }
  : T;

// ✅ CORRECT: Deep readonly
type DeepReadonly<T> = T extends object
  ? { readonly [P in keyof T]: DeepReadonly<T[P]> }
  : T;
```

### Key Remapping (TypeScript 4.1+)

```typescript
// ✅ CORRECT: Rename keys with `as`
type Getters<T> = {
  [P in keyof T as `get${Capitalize<string & P>}`]: () => T[P];
};

interface Person {
  name: string;
  age: number;
}

type PersonGetters = Getters<Person>;
// { getName: () => string; getAge: () => number; }

// ✅ CORRECT: Filter keys
type FilterByType<T, U> = {
  [P in keyof T as T[P] extends U ? P : never]: T[P];
};

type StringProps = FilterByType<Person, string>;
// { name: string; }
```

---

## Template Literal Types

```typescript
// ✅ CORRECT: Basic template literals
type EventName<T extends string> = `on${Capitalize<T>}`;

type ClickEvent = EventName<'click'>; // 'onClick'

// ✅ CORRECT: Union expansion
type Alignment = 'left' | 'center' | 'right';
type VerticalAlign = 'top' | 'middle' | 'bottom';

type Position = `${Alignment}-${VerticalAlign}`;
// 'left-top' | 'left-middle' | 'left-bottom' | 'center-top' | ...

// ✅ CORRECT: Parse string types
type ExtractRouteParams<T extends string> =
  T extends `${infer _Start}:${infer Param}/${infer Rest}`
    ? Param | ExtractRouteParams<Rest>
    : T extends `${infer _Start}:${infer Param}`
      ? Param
      : never;

type Params = ExtractRouteParams<'/users/:userId/posts/:postId'>;
// 'userId' | 'postId'
```

---

## Generic Constraints & Inference

### Constraining Generics

```typescript
// ✅ CORRECT: Constrain to object with specific property
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// ✅ CORRECT: Constrain to have length property
function longest<T extends { length: number }>(a: T, b: T): T {
  return a.length >= b.length ? a : b;
}

longest('hello', 'hi');           // OK
longest([1, 2, 3], [1, 2]);       // OK
longest({ length: 5 }, { length: 3 }); // OK

// ✅ CORRECT: Constrain with constructor
function createInstance<T>(ctor: new () => T): T {
  return new ctor();
}
```

### Inference with `infer`

```typescript
// ✅ CORRECT: Infer function parameters
type Parameters<T extends (...args: any) => any> =
  T extends (...args: infer P) => any ? P : never;

// ✅ CORRECT: Infer constructor parameters
type ConstructorParameters<T extends abstract new (...args: any) => any> =
  T extends abstract new (...args: infer P) => any ? P : never;

// ✅ CORRECT: Infer array element type
type ElementType<T> = T extends (infer U)[] ? U : never;

// ✅ CORRECT: Infer object value types
type ValueOf<T> = T[keyof T];

// ✅ CORRECT: Infer first element of tuple
type First<T extends any[]> = T extends [infer F, ...any[]] ? F : never;

// ✅ CORRECT: Infer last element of tuple
type Last<T extends any[]> = T extends [...any[], infer L] ? L : never;
```

---

## Builder Pattern with Types

```typescript
// ✅ CORRECT: Type-safe builder pattern
interface QueryBuilder<T extends object = {}> {
  select<K extends string>(
    fields: K[]
  ): QueryBuilder<T & Record<'select', K[]>>;
  
  from<Table extends string>(
    table: Table
  ): QueryBuilder<T & Record<'from', Table>>;
  
  where<Field extends string>(
    field: Field,
    value: unknown
  ): QueryBuilder<T & Record<'where', { field: Field; value: unknown }>>;
  
  build(): T extends { select: any; from: any } ? string : never;
}

function createQuery(): QueryBuilder {
  const state: any = {};
  
  return {
    select(fields) {
      state.select = fields;
      return this as any;
    },
    from(table) {
      state.from = table;
      return this as any;
    },
    where(field, value) {
      state.where = { field, value };
      return this as any;
    },
    build() {
      if (!state.select || !state.from) {
        throw new Error('select and from are required');
      }
      return `SELECT ${state.select.join(', ')} FROM ${state.from}` +
        (state.where ? ` WHERE ${state.where.field} = ?` : '');
    }
  };
}

// Usage - build() only available after select() and from()
const query = createQuery()
  .select(['id', 'name'])
  .from('users')
  .where('id', 1)
  .build(); // OK

// This would fail type checking:
// createQuery().select(['id']).build(); // Error: from is required
```

---

## Branded/Nominal Types

TypeScript uses structural typing, but sometimes you need nominal types:

```typescript
// ✅ CORRECT: Branded types for type safety
type Brand<T, B> = T & { __brand: B };

type UserId = Brand<string, 'UserId'>;
type OrderId = Brand<string, 'OrderId'>;

function createUserId(id: string): UserId {
  return id as UserId;
}

function createOrderId(id: string): OrderId {
  return id as OrderId;
}

function getUser(id: UserId): User {
  // ...
}

const userId = createUserId('user-123');
const orderId = createOrderId('order-456');

getUser(userId);  // OK
// getUser(orderId); // Error: OrderId is not assignable to UserId
// getUser('user-123'); // Error: string is not assignable to UserId

// ✅ CORRECT: Validated types
type Email = Brand<string, 'Email'>;
type NonEmptyString = Brand<string, 'NonEmptyString'>;

function validateEmail(input: string): Email | null {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(input) ? (input as Email) : null;
}

function validateNonEmpty(input: string): NonEmptyString | null {
  return input.trim().length > 0 ? (input as NonEmptyString) : null;
}
```

---

## Variadic Tuple Types (TypeScript 4.0+)

```typescript
// ✅ CORRECT: Spread in tuple types
type Concat<T extends any[], U extends any[]> = [...T, ...U];

type A = Concat<[1, 2], [3, 4]>; // [1, 2, 3, 4]

// ✅ CORRECT: Function that preserves tuple types
function concat<T extends any[], U extends any[]>(
  arr1: [...T],
  arr2: [...U]
): [...T, ...U] {
  return [...arr1, ...arr2];
}

const result = concat([1, 'hello'] as const, [true, 42] as const);
// Type: [1, "hello", true, 42]

// ✅ CORRECT: Partial application
type PartialApply<
  F extends (...args: any) => any,
  Applied extends any[]
> = F extends (...args: [...Applied, ...infer Rest]) => infer R
  ? (...args: Rest) => R
  : never;

function add(a: number, b: number, c: number): number {
  return a + b + c;
}

type Add1 = PartialApply<typeof add, [number]>; // (b: number, c: number) => number
type Add2 = PartialApply<typeof add, [number, number]>; // (c: number) => number
```

---

## Recursive Types

```typescript
// ✅ CORRECT: JSON type
type JsonPrimitive = string | number | boolean | null;
type JsonArray = Json[];
type JsonObject = { [key: string]: Json };
type Json = JsonPrimitive | JsonArray | JsonObject;

// ✅ CORRECT: Recursive path type
type Path<T, K extends keyof T = keyof T> = K extends string
  ? T[K] extends Record<string, any>
    ? K | `${K}.${Path<T[K]>}`
    : K
  : never;

interface Config {
  server: {
    port: number;
    host: string;
  };
  database: {
    connection: {
      url: string;
    };
  };
}

type ConfigPath = Path<Config>;
// 'server' | 'server.port' | 'server.host' | 'database' | 'database.connection' | 'database.connection.url'

// ✅ CORRECT: Get type at path
type PathValue<T, P extends string> = P extends `${infer K}.${infer Rest}`
  ? K extends keyof T
    ? PathValue<T[K], Rest>
    : never
  : P extends keyof T
    ? T[P]
    : never;

type PortType = PathValue<Config, 'server.port'>; // number
type UrlType = PathValue<Config, 'database.connection.url'>; // string
```

---

## Real-World Patterns

### Type-Safe Event Emitter

```typescript
type EventMap = Record<string, any>;

interface TypedEventEmitter<Events extends EventMap> {
  on<K extends keyof Events>(event: K, listener: (data: Events[K]) => void): void;
  off<K extends keyof Events>(event: K, listener: (data: Events[K]) => void): void;
  emit<K extends keyof Events>(event: K, data: Events[K]): void;
}

// Usage
interface AppEvents {
  userLoggedIn: { userId: string; timestamp: Date };
  userLoggedOut: { userId: string };
  error: Error;
}

declare const emitter: TypedEventEmitter<AppEvents>;

emitter.on('userLoggedIn', (data) => {
  console.log(data.userId); // OK, typed correctly
});

emitter.emit('userLoggedIn', { userId: '123', timestamp: new Date() }); // OK
// emitter.emit('userLoggedIn', { userId: '123' }); // Error: missing timestamp
```

### Type-Safe API Client

```typescript
interface ApiEndpoints {
  '/users': {
    GET: { response: User[] };
    POST: { body: CreateUserDto; response: User };
  };
  '/users/:id': {
    GET: { response: User };
    PUT: { body: UpdateUserDto; response: User };
    DELETE: { response: void };
  };
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

type ApiRequest<
  Path extends keyof ApiEndpoints,
  Method extends keyof ApiEndpoints[Path]
> = ApiEndpoints[Path][Method] extends { body: infer B } ? B : never;

type ApiResponse<
  Path extends keyof ApiEndpoints,
  Method extends keyof ApiEndpoints[Path]
> = ApiEndpoints[Path][Method] extends { response: infer R } ? R : never;

async function apiCall<
  Path extends keyof ApiEndpoints,
  Method extends keyof ApiEndpoints[Path] & HttpMethod
>(
  path: Path,
  method: Method,
  ...args: ApiRequest<Path, Method> extends never
    ? []
    : [body: ApiRequest<Path, Method>]
): Promise<ApiResponse<Path, Method>> {
  // Implementation
  return {} as any;
}

// Usage
const users = await apiCall('/users', 'GET'); // User[]
const newUser = await apiCall('/users', 'POST', { name: 'John', email: 'john@example.com' }); // User
// apiCall('/users', 'POST'); // Error: body required
```

---

## Summary

| Pattern | Use Case |
|---------|----------|
| Discriminated Unions | Type-safe state, API responses |
| Type Guards | Runtime type checking with TS awareness |
| Conditional Types | Transform types based on conditions |
| Mapped Types | Bulk property transformations |
| Template Literals | String type manipulation |
| Branded Types | Nominal typing, validation |
| Variadic Tuples | Preserve tuple types through operations |
| Recursive Types | Nested structures, paths |
