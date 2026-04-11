---
name: common-developer
description: >-
  Load this skill for architecture decisions, system design, feature design, software design and cross-project work also for ANY code contribution (feature, fix, refactoring, test writing). 
  Contains mandatory best practices (SOLID, DRY, KISS, YAGNI), Clean Code rules, Pragmatic Programmer principles, and testing strategies. Required for all backend, frontend, and fullstack development agents.
---

## ⚠️ Critical Rules (MUST FOLLOW)

These rules are NON-NEGOTIABLE and take precedence over all other guidelines:

- **CRITICAL: Never speculate about code you haven't seen.** Read files you are about to modify. For code you're NOT modifying, trust your provided context (codebase-state.md, Implementation Context, handoff data).
- **CRITICAL: Always mutualize and reuse code.** DRY is enforced through your context layers — check codebase-state.md and Implementation Context for existing patterns before creating new ones. If you suspect duplication but context doesn't cover it, report a CONTEXT GAP.
- **CRITICAL: Never claim success without validation.** Run tests, build the project, check logs. If you cannot validate yourself, say "Please test this and confirm it works."
- **CRITICAL: BUILD MUST PASS BEFORE PR.** Before pushing code or creating a PR, you MUST run a full build locally using the `build.py` wrapper (see Section 7). ALL tests must pass. NO EXCEPTIONS. A failing build = no PR.
- **CRITICAL: Follow the principles below.** SOLID, DRY, KISS, YAGNI, Clean Code, testing strategies,  modern development practices,  are mandatory, not suggestions.
- **Think first**: Read provided context and the files you will modify before making changes
- **Explain changes**: Give high-level explanations of what you changed at every step
- **Simplicity**: Make every change as simple as possible. Avoid massive or complex changes.
- **Refactor proactively**: Don't hesitate to refactor bad code to put in place good practices
- **Detect versions**: Always detect language and framework versions to use their new features
- **Analyze context**: Check provided context for existing patterns, conventions, and reusable code before starting
- **Clean unused code**: Always clean unused code or libraries
- **Elegant solutions**: Use the most simple, elegant, and best-practice approaches

---

## 1. SOLID Principles

### S - Single Responsibility Principle
- A class/function should have only ONE reason to change
- Split large classes into focused, cohesive units
- Ask: "What is this class/function responsible for?"

### O - Open/Closed Principle
- Open for extension, closed for modification
- Use abstractions (interfaces, inheritance) to extend behavior
- New features = new code, not modified existing code

### L - Liskov Substitution Principle
- Subtypes must be substitutable for their base types
- Don't break contracts when extending
- If it looks like a duck but needs batteries, wrong abstraction

### I - Interface Segregation Principle
- Many specific interfaces > one general-purpose interface
- Clients shouldn't depend on methods they don't use
- Split fat interfaces into focused ones

### D - Dependency Inversion Principle
- Depend on abstractions, not concretions
- High-level modules shouldn't depend on low-level modules
- Inject dependencies, don't instantiate them

---

## 2. Core Principles

### DRY - Don't Repeat Yourself
- Every piece of knowledge must have a single, authoritative representation
- Extract common logic into reusable functions/components
- Applies to: code, documentation, schemas, configs
- But: Don't over-abstract prematurely (see YAGNI)

#### When Enforcing DRY (Context-Based)

DRY requires knowing what exists. Use your **context layers** — not broad exploration:

| Source | What it tells you about reuse |
|--------|-------------------------------|
| **codebase-state.md** | All existing modules, services, entities, patterns — check here first |
| **Implementation Context** | Specific reusable code identified by orchestrator for your task |
| **Files you read to modify** | Patterns and utilities visible in the files you're editing |

```
🔴 WRONG — Exploring to enforce DRY:
Glob **/*.java "to check if a similar service exists"
Grep "calculateTotal" across entire codebase "to find reusable logic"

✅ CORRECT — Context-based DRY:
1. Check codebase-state.md → sees PasswordResetRateLimiter exists
2. Follow same pattern for new EmailChangeRateLimiter
3. Read PasswordResetRateLimiter.java (file being used as reference)

✅ CORRECT — Reporting a gap:
"CONTEXT GAP: I'm creating a rate limiter but codebase-state.md
doesn't mention if a generic RateLimiter base class exists.
Impact: proceeding with standalone implementation."
```

### KISS - Keep It Simple, Stupid
- The simplest solution is usually the best
- Avoid unnecessary complexity and cleverness
- If it's hard to explain, it's probably too complex
- "Debugging is twice as hard as writing code. If you write code as cleverly as possible, you are by definition not smart enough to debug it." - Kernighan

### YAGNI - You Ain't Gonna Need It
- Don't implement features until they're actually needed
- Avoid speculative generality and "future-proofing"
- Build for today's requirements, not imaginary future ones
- Delete dead code ruthlessly

---

## 3. Clean Code (Robert C. Martin)

### Naming
- Names should reveal intent
- Avoid abbreviations and cryptic names
- Use pronounceable, searchable names
- Class names = nouns (`Customer`, `OrderService`)
- Method names = verbs (`calculateTotal`, `sendEmail`)

### Functions
- Small (ideally < 20 lines)
- Do one thing only
- One level of abstraction per function
- Minimal arguments (0-2 ideal, 3 max)
- No side effects - do what the name says, nothing more

### Comments
- Code should be self-documenting
- Comments explain WHY, not WHAT
- Don't comment bad code - rewrite it
- Keep comments updated or delete them
- Good: `// Compensates for browser timezone offset`
- Bad: `// Increment counter by 1`

### Error Handling
- Use exceptions, not error codes
- Don't return null - use Optional/empty collections
- Fail fast, fail loud
- Provide context in error messages
- Don't catch generic exceptions silently

### Code Smells to Avoid
- Long methods (> 30 lines)
- Large classes (> 300 lines)
- Duplicate code
- Dead code (unused functions, commented code)
- Magic numbers/strings (use constants)
- Deep nesting (> 3 levels)
- God objects (classes that do everything)

---

## 4. The Pragmatic Programmer (Hunt & Thomas)

### Care About Your Craft
- Take pride in your work
- Think critically about what you're building
- Be a catalyst for change

### Orthogonality
- Keep components independent
- Changes in one area shouldn't affect others
- Eliminate effects between unrelated things

### Tracer Bullets
- Build end-to-end skeleton first
- Get feedback early and often
- Iterate on a working system

### Don't Assume - Verify
- Test assumptions explicitly
- "Select isn't broken" - the bug is probably in your code
- When debugging, prove your assumptions

### Refactor Early, Refactor Often
- Don't let technical debt accumulate
- Leave code cleaner than you found it (Boy Scout Rule)
- Refactoring is not rewriting

### Design by Contract
- Preconditions: what must be true before
- Postconditions: what will be true after
- Invariants: what always stays true
- Be explicit about what functions expect and guarantee

### Don't Outrun Your Headlights
- Take small steps
- Avoid fortune-telling (predicting future requirements)
- Get feedback before going too far

### Broken Windows Theory
- Don't leave "broken windows" (bad code, hacks)
- One broken window leads to more
- Fix or at least mark technical debt

---

## 5. Testing Strategy

> ⛔ **CRITICAL — EVERY PRODUCTION CODE CHANGE MUST HAVE TESTS** ⛔
>
> This is NON-NEGOTIABLE. Code without tests is incomplete code.

### 🔴 BLOCKING — Mandatory Test Coverage

```
Rule 1: New method/function/component → WRITE new tests
Rule 2: Modified method/function → VERIFY existing tests cover it, ADD tests if not
Rule 3: No test file exists → CREATE one ("no existing test" is NOT an excuse to skip)
Rule 4: All tests MUST run and PASS before reporting success
Rule 5: Report MUST include test count (e.g., "Tests: 48 passed, 0 failed")
```

```
🔴 WRONG — Shipping code without tests:
"Feature implemented. Build compiles."
"No test file exists for this component, so none to update."
"Added tests for the listener but not for the refactored service."

✅ CORRECT — Full coverage:
"Created UserSpringServicePasswordTest.java (4 tests: happy path, wrong current password,
 weak new password, event published). Created edit-credentials-dialog.component.spec.ts
 (3 tests: success toast, error toast, dialog close). All 1048 tests pass."
```

### Test Pyramid
```
        /\
       /E2E\        ← Few, slow, expensive
      /------\
     /Integration\  ← Some, medium speed
    /------------\
   / Unit Tests   \ ← Many, fast, cheap
  /________________\
```

### Unit Tests
- Test single units in isolation
- Fast execution (milliseconds)
- High coverage of business logic
- Mock external dependencies

### Integration Tests
- Test component interactions
- Real dependencies (DB, services)
- Focus on boundaries and contracts
- No-mock philosophy when possible

### E2E Tests
- Test complete user flows
- Most realistic but slowest
- Cover critical paths
- Catch integration issues

### Test Quality
- Tests are documentation
- One assertion per test (ideally)
- Arrange-Act-Assert pattern
- Test behavior, not implementation
- Name tests clearly: `when_condition_should_expectedResult`

### What to Test
- Happy paths
- Edge cases (null, empty, boundaries)
- Error cases
- Security constraints

---

## 6. Modern Development Practices

### Use Latest Language Features
- Stay current with your stack versions
- Modern syntax is often clearer and safer
- Check changelogs for new capabilities
- Leverage new APIs and patterns

### Version Control
- See `common-git` skill for full git workflow, branching rules, and commit conventions

### Code Review Culture
- Review for learning, not blame
- Focus on design and logic, not style
- Automate style checks (linters, formatters)
- Be kind, be specific, be helpful

### Continuous Integration
- Automated builds on every push
- Tests must pass before merge
- Fast feedback loop
- Fix broken builds immediately

---

## 7. When Building Projects

> ⛔ **Running `mvn`, `npm test`, or build commands DIRECTLY will flood your context and crash your session (200K token limit).**

### 🔴 BLOCKING — Always Use build.py Wrapper

```bash
# 🔴 WRONG — Will crash your session with 100K+ lines of output
mvn clean verify
npm run build
npm test

# ✅ CORRECT — Returns small JSON summary, logs captured to file
BUILDER="$(find D:/Work/projects/buy-nature -path '*/common-builder/scripts/build.py' -type f 2>/dev/null | head -1)"
result=$(python3 "$BUILDER" --path /path/to/project --timeout 300)
echo "$result"
```

**JSON output:** `{status, type, exitCode, phases: {requested, executed, skipped, timing}, tests: {run, passed, failed}, duration, logFile}`

**Options:** `--path` (required) | `--type maven|npm` (auto-detected) | `--timeout 600` (default) | `--phases install,build,test` | `--test-include "glob"` (npm) | `--test-class "Name"` (maven) | `--force-install` | `--offline` (maven: skip repo checks)

| On success | On failure |
|------------|------------|
| Push code, then `python3 cleanup.py <logFile>` | Read `<logFile>` (last 100 lines) to diagnose errors, fix, rebuild |

### Fast Feedback Recipes

```bash
# Compile-only check (fastest — ~30-40s)
python3 "$BUILDER" --path $(pwd) --phases build

# Specific tests only (Angular — ~20-30s)
python3 "$BUILDER" --path $(pwd) --phases test --test-include "src/app/pages/checkout/**"

# Specific test class (Maven — ~30-60s)
python3 "$BUILDER" --path $(pwd) --phases test --test-class "OrderServiceTest"

# Maven offline (skip repo checks — ~5-15s faster)
python3 "$BUILDER" --path $(pwd) --offline

# Full build before PR (default — unchanged)
python3 "$BUILDER" --path $(pwd)
```

**Note:** `build.py` auto-detects `mvnd` (Maven Daemon) when available — ~40-60% faster repeated builds.

**Use `--phases build` during iteration, full build only before PR/push.**

---

## 8. Quick Reference Checklist

Before committing, ask yourself:

- [ ] Is the code as simple as possible? (KISS)
- [ ] Did I avoid duplication? (DRY)
- [ ] Did I only build what's needed? (YAGNI)
- [ ] Are functions/classes focused? (SRP)
- [ ] Are names clear and meaningful?
- [ ] **🔴 Did I write tests for EVERY new/modified method?** (see Section 5)
- [ ] **🔴 Do ALL tests pass?** (report exact count)
- [ ] Would a new team member understand this?
- [ ] Did I use modern language features?
- [ ] Did I remove dead code?
- [ ] Did I handle errors properly?

---

## 9. Self-Code-Review Protocol (Definition of Done)

> 🔴 **BLOCKING — Mandatory before declaring task complete**
>
> You MUST perform a self-review of ALL your changes before committing.
> A task is NOT complete until self-review is done and issues are fixed.

### When to Perform

After all code changes and tests pass — BEFORE commit. This is the last step of the VERIFY phase.

### 5-Category Review

Review your changes systematically through each category:

| # | Category | What to Look For |
|---|----------|------------------|
| 1 | **Optimization** | Unnecessary computations, redundant DB queries, N+1 patterns, inefficient loops, missing pagination, unnecessary object creation, repeated API calls |
| 2 | **Refactoring / Elegance** | Long methods (>20 lines), deep nesting (>3 levels), unclear names, missing modern language features (Java: records, pattern matching, sealed classes; Angular: @if/@for, signal inputs, new control flow), complex conditionals that should be extracted |
| 3 | **DRY / Mutualization** | Duplicated logic within your changes, existing utilities in codebase-state.md you should have reused, repeated patterns that should be extracted into shared methods/components |
| 4 | **Bug Detection** | Null/undefined not handled, missing edge cases, off-by-one errors, race conditions, unclosed resources, missing error handling, incorrect state transitions, wrong return types |
| 5 | **Security** | User input not validated, injection vectors (SQL, XSS, command), secrets/credentials in code, missing auth checks, sensitive data in logs/responses, CORS misconfiguration |

### Token-Efficient Review Rules

| DO | DO NOT                                        |
|----|-----------------------------------------------|
| Review from memory — you just wrote the code, it's in your context | Re-read modified files from disk              |
| Fix immediately with Edit tool  | Grep broadly for duplicates                   |
| Do one targeted read if suspecting DRY with an existing file | Write a verbose review document               |
| Note large refactors as "Deferred" | Spend more than ~30 tool uses on review fixes |
| Check codebase-state.md for existing patterns to reuse | Glob `**/*.java` to "check for similar code"  |

### Fix vs Defer

| Issue Found | Action |
|-------------|--------|
| Quick fix (rename, extract method, add null check, use modern syntax) | Fix immediately |
| Moderate fix (extract shared utility, refactor conditional logic) | Fix immediately |
| Large refactor beyond task scope (rearchitect module, cross-domain change) | Note as **Deferred** in output |
| Issue in existing code you didn't write | Note under **Key Discoveries** in output |

### Self-Review Output

After completing the review, include this block in your task output (Handoff Summary):

```
### Self-Review
- **Checked**: 5/5 categories (Optimization, Refactoring, DRY, Bugs, Security)
- **Fixed**: [N issues — one-line description each]
- **Deferred**: [N items — one-line description each, or "none"]
```

### Examples

```
🔴 WRONG — Skipping self-review:
"Tests pass. Build successful. Task complete."

🔴 WRONG — Rubber-stamping:
"Self-review: no issues found." (without actually reviewing)

✅ CORRECT — Thorough self-review with fixes:
"### Self-Review
- Checked: 5/5 categories
- Fixed: 2 issues
  - Refactoring: extracted repeated validation logic into validateOrderTransition() helper
  - Security: added @Valid annotation on request DTO parameter
- Deferred: none"

✅ CORRECT — Self-review with deferred items:
"### Self-Review
- Checked: 5/5 categories
- Fixed: 1 issue
  - Optimization: replaced N+1 query with JOIN FETCH in findOrdersWithItems()
- Deferred: 1 item
  - DRY: OrderService and ReturnService share similar state machine logic — candidate for shared AbstractStateMachine base"
```

---

## 10. Golden Rules

> "Any fool can write code that a computer can understand. Good programmers write code that humans can understand." - Martin Fowler

> "Premature optimization is the root of all evil." - Donald Knuth

> "Make it work, make it right, make it fast." - Kent Beck

> "Programs must be written for people to read, and only incidentally for machines to execute." - Abelson & Sussman

