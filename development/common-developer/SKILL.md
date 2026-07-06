---
name: common-developer
description: >-
  Software craftsmanship principles for any code contribution: SOLID, DRY,
  KISS, YAGNI, Clean Code, and a self-review protocol. Use this skill whenever
  the user asks to write a feature, implement code, fix a bug, refactor a class,
  design an interface, evaluate code quality, improve existing code, or review
  any code contribution in a PR — even when they don't explicitly say "best
  practices". Contains the foundational discipline
  that applies before any language- or framework-specific guidance.
---

# Software Craftsmanship Skill

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
> **Note on examples:** Code samples below use neutral pseudocode (no language-specific syntax). Language-specific worked examples (Java, TypeScript) live in `references/`.

---

## When Reasoning About Software Quality

Apply these foundational stances to every contribution:

1. **Read what you change** — never speculate about a method or file you have not opened.
2. **Validate before reporting** — tests run, build green, behavior observed.
3. **Pick the simplest design** that satisfies the actual requirement.
4. **Refactor opportunistically** — leave code cleaner than you found it (Boy Scout Rule).
5. **Tests are part of the contribution**, not a follow-up.

### 🔴 BLOCKING

#### Read every file you intend to modify before editing it
**Why:** changes based on assumptions are the dominant cause of regressions and silently broken contracts. The seconds of reading prevent the hours of debugging that come from "I thought this method returned X."

#### Never claim success without validation
**Why:** "compiles" is not "works". A reported success that turns out broken erodes trust faster than an honest "I couldn't test this." If you cannot run the code, say "Please test this and confirm it works."

##### WRONG
```
"Feature implemented and build passes."
[no test run, no logs checked, no behavior verified]
```
##### CORRECT
```
"Feature implemented. Ran the test suite: 48 passed, 0 failed.
Manually verified the new endpoint returns 201 + Location header on POST /orders."
```

#### Every production code change ships with tests in the same change
**Why:** code without tests has no executable specification. Every subsequent modification has to re-derive what the code is supposed to do. Untested code commits the team to investigative debt for every later edit.

##### WRONG
```
"Added processOrder() to OrderService. No test file exists for OrderService
so I didn't add tests."
```
##### CORRECT
```
"Added processOrder(). Created the corresponding test suite with 4 cases:
happy path, empty cart, invalid customer, payment declined. All 4 pass."
```

---

## When Applying SOLID

📚 **When designing classes/interfaces, evaluating coupling, or needing worked examples of each SOLID principle → read [solid-examples.md](references/solid-examples.md).**

| Principle | One-line rule |
|-----------|---------------|
| **S** — Single Responsibility | A class/function changes for one reason only. |
| **O** — Open/Closed | Extend behavior via new code, not by modifying existing code. |
| **L** — Liskov Substitution | Subtypes must honor the contract of their parent. |
| **I** — Interface Segregation | Many specific interfaces beat one fat interface. |
| **D** — Dependency Inversion | Depend on abstractions, inject them — don't `new` concretions. |

### 🔴 BLOCKING

#### Never instantiate dependencies inside the class that uses them — inject them
**Why:** internal `new` couples the class to a concrete implementation, makes unit testing impossible without container bootstrap, and blocks environment-based swapping. Inversion is what keeps the domain testable and the infrastructure replaceable.

##### WRONG
```
class OrderService {
    email = new EmailService()           // hard-wired
    repo  = new SqlOrderRepository()     // hard-wired
}
```
##### CORRECT
```
class OrderService {
    constructor(notifier: NotificationPort,
                repo: OrderRepository) {
        // dependencies injected — swappable, mockable in tests
    }
}
```

#### Don't extend a parent type to "get" its fields/methods if your subtype breaks the contract
**Why:** Liskov violations turn polymorphism into a minefield — any caller that legitimately uses the parent type can crash on a subtype. Use composition or a separate interface instead of inheriting incompatible behavior.

##### WRONG
```
class GiftCard extends Product {
    applyDiscount(pct) {
        throw "Gift cards cannot be discounted"
        // any caller iterating List<Product> and calling applyDiscount crashes
    }
}
```
##### CORRECT
```
interface Priceable    { getPrice() }
interface Discountable { applyDiscount(pct) }

class PhysicalProduct  implements Priceable, Discountable
class GiftCard         implements Priceable                // no discount API
```

---

## When Avoiding Duplication and Over-engineering

### 🔴 BLOCKING

#### DRY — every piece of knowledge has one authoritative representation
**Why:** duplicated logic drifts. The two copies start identical, diverge under independent edits, and produce inconsistent behavior at the boundary where they meet. Centralization is what prevents the "we fixed it in service A but forgot service B" class of bugs.

#### KISS — pick the simplest design that satisfies the requirement
**Why:** complexity is borrowed time. Every cleverness costs the next reader (often you, in 6 months) more time than it saved when written. "Debugging is twice as hard as writing code. If you write it as cleverly as possible, you are by definition not smart enough to debug it." (Kernighan)

#### YAGNI — don't build for hypothetical future requirements
**Why:** speculative generality consistently misses where real flexibility ends up being needed. Features built for an imagined future create maintenance burden today and rarely fit the actual future when it arrives — by which time the unused code has rotted.

##### WRONG
```
// Building a "PluginRegistry" because we might want plugins someday
interface Plugin<T> {
    register(ctx: PluginContext<T>)
}
abstract class AbstractPluginLoader<T> { /* 200 lines */ }
```
##### CORRECT
```
// Direct call. Add the abstraction when a second concrete need actually appears.
orderProcessor.process(order)
```

### 🟡 WARNING

#### Don't extract an abstraction from a single use case
**Why:** abstractions need 2-3 concrete instances to identify the right shape. Extracting from one produces interfaces that fit only the first case and force the second case into contortions.

---

## When Writing Clean Code

📚 **When naming variables/functions, sizing functions/classes, handling comments, errors, or formatting → read [clean-code-catalog.md](references/clean-code-catalog.md).**

📚 **When detecting code smells, restructuring legacy code, or applying a specific refactoring technique (extract method, replace conditional with polymorphism, etc.) → read [refactoring-patterns.md](references/refactoring-patterns.md).**

📚 **When choosing which Gang-of-Four pattern fits a recurring design problem → read the decision table in [design-patterns-catalog.md](references/design-patterns-catalog.md)** — the GoF implementations themselves are standard knowledge and are intentionally not restated.

### 🔴 BLOCKING

#### Names reveal intent — no abbreviations, no cryptic prefixes
**Why:** code is read 10× more than it is written. A name that takes 3 seconds to grasp instead of one compounds across thousands of reads. Cryptic naming is a tax on every future reader (including yourself).

##### WRONG
```
d              // elapsed time in days
ls             // ?
tmp            // ?
flg
```
##### CORRECT
```
elapsedDays
activeOrders
customerEmail
shippingAddressValidated
```

#### Functions do one thing at one level of abstraction
**Why:** a function that does N things has up to 2^N execution paths to test and a name that lies at the call site. Splitting by responsibility produces call sites that read like prose and tests that need few inputs each.

##### WRONG
```
processOrder(order) {
    // validate
    if (order.items.isEmpty) throw ...
    // calculate
    total = sum(order.items.map(price))
    // persist
    db.execute("INSERT INTO orders ...")
    // notify
    smtp.send(order.customer.email, "...")
}
```
##### CORRECT
```
processOrder(order) {
    validate(order)
    priced = price(order)
    saved  = repository.save(priced)
    notifier.confirm(saved)
    return saved
}
```

### 🟡 WARNING

#### Comments explain WHY, not WHAT
**Why:** the WHAT is in the code below the comment — duplicating it produces drift the moment the code changes. The WHY (spec quirk, compensating workaround, non-obvious invariant) is what cannot be recovered from the code itself.

##### WRONG
```
// Increment counter by 1
counter++
```
##### CORRECT
```
// Tax engine returns gross prices for B2C and net for B2B; normalize to net here.
return invoice.isB2C ? raw - (raw * VAT_RATE) : raw
```

### 🟢 BEST PRACTICE

- Functions ideally < 20 lines, classes < 300 lines.
- Maximum 3 arguments per function — beyond that, introduce a parameter object.
- Nesting depth ≤ 3 — extract methods or use early returns past that.
- No magic numbers/strings — name constants.
- Use exceptions over error codes; never return `null` for collections — return an empty collection instead.

---

## When Writing Tests (Any Language or Framework)

These foundations are language-agnostic and owned here. Framework mechanics live in the satellite skills (`common-java-testing`, `common-frontend-testing`, `common-e2e-playwright`) — they apply these rules, they don't restate them.

### 🔴 BLOCKING

#### Test behavior, not implementation
**Why:** tests coupled to internals (private methods, call counts on collaborators, DOM structure) break on every refactor even when behavior is intact — the team learns to ignore red builds. A test that exercises observable behavior survives any refactor that preserves the contract.

##### WRONG
```
expect(service.internalCache.size).toBe(3)      // internal state
verify(repository, times(2)).findById(any())    // call-count choreography
```
##### CORRECT
```
expect(getCartTotal()).toBe(59.98)              // observable outcome
assertThat(response.status).isEqualTo(201)
```

#### Each test is isolated — fresh state, no shared mutable fixtures, no order dependence
**Why:** a test that depends on another test's leftovers passes or fails depending on execution order and parallelism. The failure appears in the wrong test, pointing away from the actual defect.

#### One behavior per test, structured Arrange-Act-Assert (Given-When-Then)
**Why:** a test asserting N behaviors fails on the first and hides the other N−1; the AAA sections make the tested contract readable at a glance. Multiple asserts are fine when they verify facets of the *same* behavior.

#### Mock only process boundaries (HTTP, DB, clock, randomness, file system) — never the code under test's collaborators within the same process
**Why:** mocking internal collaborators re-encodes the implementation in the test — it passes when the real wiring is broken and breaks when the wiring is refactored. Real objects in-process, test doubles at the boundary.

#### Fixed test data, never random or time-dependent
**Why:** random input makes failures non-reproducible ("works on re-run"); `now()` makes tests flake at midnight, month ends, and DST. Pin values (`2026-01-15T10:00:00Z`, `"user-42"`) and inject clocks.

### 🟡 WARNING

#### Test names state behavior + condition, not method names
`rejects_checkout_when_cart_is_empty` beats `testProcessOrder2` — the failure list should read as a spec.

#### One scenario, one level of the pyramid
Cover a rule in a unit test; do not re-test it in an integration test and again in E2E. Higher levels verify *wiring*, not re-verify *logic* — duplicated coverage multiplies maintenance without adding confidence.

#### Select UI elements by an explicit test contract, not styling or structure
A dedicated test attribute (e.g. `data-testid`) survives redesigns; CSS classes and XPath positions do not. Framework-specific selector ladders live in the satellite skills.

---

## When Performing Self-Code-Review (Definition of Done)

### 🔴 BLOCKING

#### Self-review is mandatory before declaring a task complete
**Why:** every author is more critical of their own code right after writing it than at any other moment. Skipping self-review pushes defects into the team review cycle, where they cost ~10× more to find and fix. The 5-category pass below catches what fresh eyes won't.

### When to Perform

After all code changes are written and tests pass — **before** commit. This is the last step of the VERIFY phase.

### 5-Category Review

Review your changes through each category:

| # | Category | What to Look For |
|---|----------|------------------|
| 1 | **Optimization** | Unnecessary computations, redundant queries, N+1 patterns, inefficient loops, missing pagination, repeated API calls |
| 2 | **Refactoring / Elegance** | Long methods (>20 l), deep nesting (>3 levels), unclear names, missing modern language features, complex conditionals to extract |
| 3 | **DRY / Mutualization** | Duplicated logic within your changes, existing utilities you should have reused, repeated patterns to extract |
| 4 | **Bug Detection** | Null/undefined not handled, missing edge cases, off-by-one, race conditions, unclosed resources, missing error handling, wrong return types |
| 5 | **Security** | User input not validated, injection vectors (SQL, XSS, command), secrets in code, missing auth checks, sensitive data in logs/responses |

### Token-Efficient Review Rules

| DO | DO NOT |
|----|--------|
| Review from memory — you just wrote the code | Re-read modified files from disk |
| Fix immediately with the editor | Grep broadly for duplicates |
| One targeted read if you suspect DRY with a known file | Write a verbose review document |
| Note large refactors as "Deferred" | Spend more than ~30 tool uses on review fixes |

### Fix vs Defer

| Issue | Action |
|-------|--------|
| Quick fix (rename, extract method, add null check) | Fix immediately |
| Moderate fix (extract shared utility, refactor conditional) | Fix immediately |
| Large refactor beyond task scope (rearchitect a module) | Note as **Deferred** |
| Issue in pre-existing code you didn't write | Note under **Discoveries** |

---

## Output Contract

When producing artifacts, deliver each in this exact form:

| Artifact | Required Form |
|----------|---------------|
| **Self-Review Output** | Markdown block with three lines (`Checked`, `Fixed`, `Deferred`). See template below. |
| **Test report** | Single line: `Tests: <N> passed, <M> failed`, plus a one-line summary if any failed. |
| **WRONG/CORRECT explanation** | Two fenced code blocks labeled `##### WRONG` and `##### CORRECT`, no prose in between. |

### Self-Review Template
```
### Self-Review
- **Checked**: 5/5 categories (Optimization, Refactoring, DRY, Bugs, Security)
- **Fixed**: <N issues — one-line description each>, or "none"
- **Deferred**: <N items — one-line description each>, or "none"
```

##### WRONG
```
"Tests pass. Build successful. Task complete."
[no self-review performed]
```
##### CORRECT
```
### Self-Review
- Checked: 5/5 categories
- Fixed: 2 issues
  - Refactoring: extracted repeated validation logic into validateOrderTransition()
  - Security: added input validation on the request DTO at the controller boundary
- Deferred: 1 item
  - DRY: OrderService and ReturnService share state-machine logic — candidate for a shared base
```
