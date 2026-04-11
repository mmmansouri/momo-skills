# Context Overflow Prevention Guide

## 🚨 The Problem

Build tools (Maven, npm, Gradle) produce **massive log output**:
- Maven `clean verify`: ~10,000-50,000 lines
- npm `run build`: ~5,000-20,000 lines  
- Angular `ng test`: ~3,000-10,000 lines

When these logs stream into an agent's context → **200K+ tokens** → **SIGKILL crash**.

## 💀 Real Crashes (Documented)

| Session ID | Agent | Command | Tokens | Outcome | Date |
|------------|-------|---------|--------|---------|------|
| BNAT-181 | backend-java-dev | `mvn clean verify` | 217K | SIGKILL | 2026-02-07 |
| mild-sab | (unknown) | Direct build | >200K | SIGKILL | 2026-02-08 |
| glow-nex | (unknown) | Direct build | >200K | Exit 1 | 2026-02-08 |

**Pattern:** Agent ignores `common-builder` → runs `mvn`/`npm` directly → context overflow → crash.

## ❌ Commands That WILL Crash You

```bash
# Maven
mvn clean compile
mvn clean verify
mvn clean install
mvn test
./mvnw <any-goal>

# NPM / Node
npm run build
npm run test
npm test
npm install   # (large projects with many dependencies)

# Angular
ng build
ng test
ng serve

# Gradle
gradle build
gradle test
./gradlew <any-task>
```

## ✅ Safe Alternatives (ALWAYS Use These)

### Maven Projects (Java/Spring Boot)

```bash
# ✅ CORRECT
BUILDER=$(dirname "$(find ~ -path "*/common-builder/scripts/build.py" -type f 2>/dev/null | head -1)")
result=$($BUILDER/build.py --path $(pwd) --timeout 300)

# Check result
echo "$result" | jq '.'

# If failed, read ONLY the error tail (not full logs)
if [[ $(echo "$result" | jq -r '.status') == "failure" ]]; then
  log_file=$(echo "$result" | jq -r '.logFile')
  tail -100 "$log_file"  # Only last 100 lines
fi
```

### NPM Projects (Angular/TypeScript)

```bash
# ✅ CORRECT
BUILDER=$(dirname "$(find ~ -path "*/common-builder/scripts/build.py" -type f 2>/dev/null | head -1)")
result=$($BUILDER/build.py --path $(pwd) --timeout 600)

# Check result
echo "$result" | jq '.'

# If failed, read ONLY the error tail
if [[ $(echo "$result" | jq -r '.status') == "failure" ]]; then
  log_file=$(echo "$result" | jq -r '.logFile')
  tail -100 "$log_file"
fi
```

## 🛡️ Self-Protection Checklist

Before running ANY command, ask yourself:

1. ✅ **Is this a build/test command?**
   - If YES → Must use `build.py`

2. ✅ **Will this produce verbose output?**
   - If YES → Redirect to file or use wrapper

3. ✅ **Have I loaded the `common-builder` skill?**
   - If NO → Load it first

4. ✅ **Am I about to type `mvn`, `npm`, `ng`, or `gradle`?**
   - If YES → Use `build.py` instead

## 📊 Safe Token Usage

| Operation | Tokens | Safe? |
|-----------|--------|-------|
| `build.py` JSON result | ~200-500 | ✅ YES |
| `tail -100 <logfile>` | ~1,000-3,000 | ✅ YES |
| `mvn clean verify` full output | 150K-250K | ❌ NO — CRASH |
| `npm run build` full output | 50K-150K | ❌ NO — CRASH |

## 🎯 Emergency Context Check

If you suspect you're approaching token limits:

```bash
# Check current token usage (if available in session)
# session_status shows context usage

# If context > 150K → STOP immediately
# - Do NOT run any more commands
# - Summarize findings
# - Exit gracefully
```

## 📝 Recovery Plan (If You Crash)

**If your session crashes from context overflow:**

1. **Document the crash** in `MEMORY.md` → "Context Overflow Hall of Shame"
2. **Identify the command** that caused it
3. **Update this guide** with the new crash example
4. **Notify Rahman** so agent instructions can be reinforced

## ⚡ Fast Feedback Recipes

Use phase control for faster iterations during development:

```bash
BUILDER="$(find D:/Work/projects/buy-nature -path '*/common-builder/scripts/build.py' -type f 2>/dev/null | head -1)"

# Compile-only check (fastest — ~30-40s, no tests, skips install if deps fresh)
python3 "$BUILDER" --path $(pwd) --phases build

# Run specific tests only (Angular — ~20-30s)
python3 "$BUILDER" --path $(pwd) --phases test --test-include "src/app/pages/checkout/**"

# Run specific test class (Maven — ~30-60s)
python3 "$BUILDER" --path $(pwd) --phases test --test-class "OrderServiceTest"

# Build + test (skip install — ~60-90s)
python3 "$BUILDER" --path $(pwd) --phases build,test

# Full build before PR (default behavior, unchanged)
python3 "$BUILDER" --path $(pwd)
```

**When to use which:**

| Situation | Recipe |
|-----------|--------|
| Just wrote code, check it compiles | `--phases build` |
| Fixing a test failure | `--phases test --test-include "path/to/spec"` |
| Ready to push/PR | Default (all phases) |
| Dependencies changed | `--force-install` |
| Maven offline (skip repo checks) | `--offline` |

## 🔗 See Also

- `common-builder` skill (full documentation)
- `backend-java-dev.md` agent instructions
- `MEMORY.md` section "2026-02-05 — Sub-Agent Context Overflow"
