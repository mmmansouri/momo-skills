---
name: skill-creator
description: >-
  Guide for creating and/or reviewing AI agent skills. Use when: (1) creating a new SKILL.md
  file, (2) editing, reviewing or rewriting an existing SKILL.md, (3) writing or fixing skill
  frontmatter (name, description), (4) creating references/ files for a skill,
  (5) auditing or reviewing skill quality, (6) adding severity markers or restructuring
  skill sections. Triggers on any work involving files in a skills/ directory.
  Contains structure templates, naming conventions, severity markers, and anti-patterns.
---

# Skill Creator Guide
> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

> **Goals:**
>- Create skills that agents can **apply immediately**, not just read.
>- Review skills for **actionability, clarity, optimization and maintainability**.
>- Use **this very file** as the canonical example to mimic (structure, severity tiers, call-outs, checklist).

> **Algorithm Overview**
>
> - **Creating a new skill** — follow `When Starting a New Skill` (Steps 1-6, in order).
> - **Reviewing or auditing an existing skill** — skip the creation flow; check the skill
>   against every rule in `When Writing the SKILL.md`, the `Core Principles`, the
>   `Anti-Patterns` table, `When Sizing a Skill`, and `When Testing Skills`; run the
>   `Checklist` as the final cross-check; report using the `Output Contract — Audit Verdict`.
> - **Bundling scripts** — 📚 **When bundling or auditing scripts shipped with a skill (write, run, validate) → read [scripts-guide.md](references/scripts-guide.md).**

---

## When Designing Any Skill — Core Principles

### 🔴 Concise is Key

The context window is a **public good**. Claude is already very smart — only add context it doesn't already have.
**Why:** every paragraph a skill loads competes with the user's actual task; content Claude can regenerate natively is pure cost.

Challenge each piece: "Does Claude really need this explanation?" / "Does it justify its token cost?" ✅ Prefer concise examples over verbose explanations.

### 🔴 Don't Re-teach Native Knowledge

Never re-teach what the model already knows natively (GoF pattern bodies, WCAG, HTTP semantics, language basics). Keep only decision tables (scenario → choice) and house rules the model cannot guess.
**Why:** re-taught fundamentals cost tokens at every load and go stale silently, while the model's native knowledge is free and current.

### 🔴 Set Appropriate Degrees of Freedom

**Why:** over-constraining creative work degrades results; under-constraining fragile operations produces inconsistent ones. Match the format to the fragility.

- **High freedom**
  - *Use when* : multiple approaches valid, context-dependent
  - *Format* : text instructions
- **Medium freedom**
  - *Use when* : preferred pattern exists, some variation OK
  - *Format* : pseudocode with parameters
- **Low freedom**
  - *Use when* : operations fragile, consistency critical
  - *Format* : specific scripts, few params

### 🔴 Progressive Disclosure

Three-level loading system:

1. **Metadata** (name + description) — Always in context (~100 words)
2. **SKILL.md body** — When skill triggers (<5K words ideal)
3. **Bundled resources** — As needed by Claude (unlimited via file reads)

**Why:** the levels are priced differently — metadata is paid on every session, the body on every trigger, references only on demand; content must live at the cheapest level that still serves it.

**Key patterns:**
- Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy along with clear pointers about where the model using the skill should go next to follow up.
- Keep SKILL.md focused. Move detailed docs to `references/` and link at section start with 📚.
- Reference files clearly from SKILL.md with guidance on when to read them
- **Add a Table of Contents to any reference file >100 lines.** Claude often previews long files; without a TOC, scope is invisible.
- **Keep references one level deep from SKILL.md.** Nested links (SKILL.md → A.md → B.md) cause Claude to preview deeper files with `head -100` and miss content. Every reference must be linkable directly from SKILL.md.
  - When a reference must mention a sibling reference, name it as plain text ("see `security.md`") — never a markdown link.
  - When it needs another skill's material, write "load `<skill>` and read its `references/<file>.md`" — never a relative path into that skill's folder (paths break outside the bridged layout).
- **Domain organization**: when a skill supports multiple domains/frameworks (e.g. aws/gcp/azure), keep SKILL.md as workflow + selection and give each variant its own reference file — Claude reads only the relevant one.

### 🔴 Principle of Lack of Surprise

Skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities. Things like a "roleplay as an XYZ" are OK though.
**Why:** skill bodies execute with the user's full trust and permissions; hidden intent is indistinguishable from an attack.

### 🔴 Single Owner Across Skills

Skills load simultaneously — design yours to compose with others, never assuming it's the only capability available. Each piece of knowledge has exactly ONE owning skill; other skills point to it ("load `<skill>` and read its `references/<file>.md`"), never copy it.
**Why:** cross-skill copies drift independently and double token cost; an agent loading both gets contradictory guidance with no signal for which copy is current.

---

## When Starting a New Skill

Follow these steps in order. Each step prevents a failure mode in later steps.

### Step 1 — 🔴 Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture (e.g., they say "turn this into a skill"). If so, extract answers from the conversation history first — the tools used, the sequence of steps, corrections the user made, input/output formats observed. The user may need to fill the gaps, and should confirm before proceeding to the next step.

1. What should this skill enable Claude to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works? Skills with objectively verifiable outputs (file transforms, data extraction, code generation, fixed workflow steps) benefit from test cases. Skills with subjective outputs (writing style, art) often don't need them. Suggest the appropriate default based on the skill type, but let the user decide.

**Why:** without explicit intent capture, the skill encodes the agent's *interpretation* of the request rather than the user's actual need. The gap surfaces only at use time, when the skill misfires.

### Step 2 — 🔴 Interview & Research

Proactively ask about : edge cases, I/O formats, example files, success criteria, dependencies. Wait to write test prompts until this is ironed out.

Check available MCPs and similar existing skills — research in parallel via subagents when possible, otherwise inline. Come back with context, don't burden the user.

**Why:** gaps discovered after writing cost a rewrite; gaps discovered in interview cost a question.

### Step 3 — 🔴 Define Use Cases

Define **2-3 concrete use cases** :

```
Use Case: [Name]
Trigger: User says "[specific phrases]"
Steps:
1. [Action]
2. [Action]
Result: [What success looks like]
```

For each use case, identify :
- **Scripts** needed (deterministic operations)
- **References** that save rediscovery (schemas, docs, domain knowledge)
- **Assets** for output (templates, icons)

**Why:** use cases decide what deserves a script, a reference, or nothing — without them the skill accretes content with no consumer.

### Step 4 — 🔴 Build Evaluations BEFORE Writing the Skill

Eval-driven development prevents skills that solve imagined problems.

1. Run Claude on representative tasks **without** the skill — log specific failures.
2. Build ≥3 eval scenarios from the gaps observed.
3. Establish a baseline (Claude vanilla score against the rubric).
4. Write the **minimal** SKILL.md needed to pass the evals.
5. Iterate against the baseline ; stop when marginal gains plateau.

**Why:** without baselines, skill quality is invisible — you can't tell if content adds value or is just decoration.

### Step 5 — 🔴 Write the SKILL.md

Based on the user interview, fill in these components :

- **name**: kebab-case, MUST match the folder name. Generic reusable skills are prefixed `common-`; project-specific deltas are prefixed with the project name (e.g. `myproject-git`); meta/spec skills use their plain topic name.
- **description**: When to trigger, what it does. This is the primary triggering mechanism - include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Note: currently Claude has a tendency to "undertrigger" skills -- to not use them when they'd be useful. To combat this, please make the skill descriptions a little bit "pushy". So for instance, instead of "How to build a simple fast dashboard to display internal Anthropic data.", you might write "How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- **the rest of the skill :)**

**Why:** the name is stable identity (bridges, indexes, cross-skill pointers); the description is the only trigger signal — weakness in either is invisible until the skill misfires or misroutes.

#### Skill directory Structure

```
skill-name/
├── SKILL.md              # Required — main instructions
├── references/           # Documentation loaded as needed
│   ├── topic-1.md
│   └── topic-2.md
├── scripts/              # Executable code (Python/Bash)
│   └── helper.py
└── assets/               # Files used in output (templates, icons)
    └── template.pptx
```

🔴 **Content in SKILL.md OR references/, not both.**
**Why:** duplicated content drifts apart silently; the agent then applies whichever copy it read first.

### Step 6 — 🔴 Test the Skill

Testing patterns (trigger / functional / multi-model / Claude A-B) live in the `When Testing Skills` section below.

**Iteration loop** :
1. Run tests (Trigger first ; then Functional / Multi-model / Claude A-B as applicable).
2. On failure → diagnose the gap → return to Step 5 to refine SKILL.md.
3. Re-run failing tests.
4. Stop when all 🔴 Trigger Tests pass AND the skill matches or beats the Step 4 baseline.

**Why:** without explicit post-write validation, skills ship with under-/over-triggering bugs that surface only at use-time, when the cost of fixing them is highest.

---

## When Writing the SKILL.md

### 🔴 Skill Description Rules

**Why:** the description is injected verbatim into the system prompt and is the ONLY signal available at trigger time — every rule below protects that signal.

- Write in third person ("Processes…", "Generates…") : matches how skill metadata is rendered to the model
- Include trigger phrases users would say : Claude matches description to user input
- Add negative triggers ("Do NOT use for...") if needed : Prevents over-triggering
- Under 1024 characters : Hard limit
- No XML tags (`<` `>`) : Security: frontmatter appears in system prompt

#### 🔴 Combat under-triggering with a pushy description
Claude tends to *not* load skills when they would actually be useful. Counter this with explicit context-of-use phrasing. **Why:** the description is the only signal Claude has at trigger-time. A neutral description loses to silence ; a pushy one loads the skill in adjacent contexts where it would help.

### 🔴 Skill Content Rules

**Why:** each rule below maps to a measured agent failure mode — skipped sections, ignored priorities, unopened references, missed buried instructions.

- Workflow-oriented sections ("When X"): agent knows WHEN to apply, not just WHAT exists
- Use severity markers so agent prioritizes blocking issues first
- Provide WRONG/CORRECT examples: agent recognizes patterns to fix
- Inline references at section start using `📚 **When <trigger> → read <ref>**` format (see `🔴 Reference Call-Out Format`) : agent matches context before opening the file
- Critical instructions at top, flagged with a `CRITICAL:` prefix: agent reads top-down; buried rules get missed
- **Use scripts for deterministic validation** — code is deterministic, language interpretation isn't
- Be specific, not ambiguous — "Use When" descriptions on patterns tell the agent when to apply them, not just that they exist
- Use Quick reference tables for fast lookup during coding, no need to re-read paragraphs
- No duplication: content must be in either SKILL.md OR references, not both: saves tokens, prevents stale content

### 🔴 Define the Output Contract

If your skill **produces, transforms, or audits content** (validators, generators, reviewers, extractors), define the exact form of output:

- **Schema** — e.g., JSON envelope `{value, source, confidence, errors: []}`
- **Template** — fixed markdown structure with named sections
- **Worked example** — input → command → exact output

Add an `## Output Format` section to SKILL.md OR document the schema in `references/output-schema.md`.

**Why:** without an explicit contract, agents drift toward inconsistent outputs. The contract is what makes the skill's output reusable downstream.

### 🔴 Writing Style

**Why:** agents execute imperatives, treat conditionals as optional, and lose relationships in flat prose — style IS compliance.

**Imperative mood** — Write all instructions as direct commands.
**Negation with alternative** — Every negation ("Don't", "Never", "Avoid") must include a concrete alternative. If the right alternative is unclear, ask the user before deciding.
**Hierarchical indented structure** — Organize instructions as Section > Subsection > Rule > Detail > Example. Flat lists lose relationships between concepts.

### 🔴 Section Naming

Use "When X" Format for rule and workflow sections, not generic labels. This tells the agent WHEN to apply the rules, not just WHAT the rules are.
**Why:** an agent scanning headers picks sections by matching its current context; a generic label never matches, so the content silently drops out.

```markdown
## When Writing New Code       # ✅ Actionable
## When Handling Exceptions    # ✅ Tells agent WHEN to apply
## Best Practices              # 🔴 WRONG — too vague
## Overview                    # 🔴 WRONG — agent skips this
```

**Canonical structural sections are exempt.** These names are allowed as-is because they
describe the skill's fixed apparatus, not domain rules: `Output Contract` / `Output Format`,
`Code Review Checklist` / `Checklist`, `Related Skills`, `Anti-Patterns`,
`Decision Tree(s)`, `Quick Reference`. Purely descriptive names outside this list
("Best Practices", "Overview", "Summary") remain WRONG.

### 🔴 Severity Markers

Use these to signal which rules are non-negotiable, which are important but not deal-breakers, and which are nice-to-haves.
**Why:** without a shared priority scale the agent treats every rule as equally binding and wastes effort — or worse, negotiates away the critical ones.

- 🔴 **BLOCKING**
  - *Meaning* : fails code review, must fix
  - *Agent behavior* : fixes BEFORE other work
- 🟡 **WARNING**
  - *Meaning* : should fix, not blocking
  - *Agent behavior* : fixes if time permits
- 🟢 **BEST PRACTICE**
  - *Meaning* : recommended improvement
  - *Agent behavior* : applies when writing new code

### 🔴 Reference Call-Out Format

Every mention of a reference file in SKILL.md MUST follow this format — **trigger first, directive last** :

```markdown
📚 **When <trigger context> → read [<ref-name>](references/<ref-name>.md).**
```

- `<trigger context>` — precise description of *when* the agent should consult the reference (the work it's doing, the question it's answering)
- The read directive comes **last** so the agent first matches its current context, then follows the directive

**Why:** a bare link (`📚 [ref.md](...)`) carries no signal about *when* to open it — agents skip references that look generic. Putting the trigger first lets the agent decide in one pass whether the reference applies, instead of opening it speculatively. Putting the directive first forces the agent to read past the link before knowing if it's relevant — wasted context.

```markdown
# 🔴 WRONG — bare link, no trigger
📚 **References:** [changelog-structure.md](references/changelog-structure.md)

# 🔴 WRONG — directive first, trigger buried
📚 **Read [changelog-structure.md](references/changelog-structure.md)** when organizing master changelogs.

# ✅ CORRECT — trigger first, directive last
📚 **When organizing master changelogs, naming files, or moving/renaming
changeset files → read [changelog-structure.md](references/changelog-structure.md).**
```

The trigger should be specific enough that an agent in an unrelated context won't open the reference, but broad enough to cover all legitimate use cases of the file. Write `When <trigger>`, not `For <content>` — a content list describes the payload, not the moment the agent needs it.

### 🔴 Explain the Why

Every 🔴 BLOCKING **named rule** MUST be followed by a one-line `**Why:**` justification anchored in domain reasoning. A named rule is a 🔴 heading or a normative 🔴 bullet that states a requirement.

**Exempt (no Why needed):** the severity-legend line, items in recap checklists (they point back to rules justified where defined), 🔴 occurrences inside output templates or WRONG/CORRECT examples, and table cells.
**Why:** the Why line forces the agent to reason about the domain *before* applying the rule — but duplicating it onto every recap item would restate each justification twice per skill, violating Concise is Key. Audits count named rules, not raw 🔴 occurrences.

```markdown
# 🔴 WRONG — rule without rationale
### 🔴 BLOCKING — Reject titles ending with a period
- Treat as validation error

# ✅ CORRECT — rule with Why
### 🔴 BLOCKING — Trailing period is a warning, not an error
**Why** : Conventional Commits 1.0 doesn't prohibit it normatively. Failing on style would reject spec-compliant titles.
- Treat as warning; don't fail validation
```

---

## When Bundling Scripts

📚 **When your skill includes scripts the agent needs to execute (write, run, validate) → read [scripts-guide.md](references/scripts-guide.md).**

---

## When Testing Skills

### 🔴 Trigger Tests

Test that your skill loads at the right times.
**Why:** under-triggering makes the skill dead weight; over-triggering pollutes unrelated sessions — both are invisible without explicit should/should-NOT cases.

```
Should trigger:
- "Help me set up a new workspace"
- "I need to create a project"          # Paraphrased
- "Initialize project for Q4 planning"  # Variation

Should NOT trigger:
- "What's the weather?"
- "Help me write Python code"
- "Create a spreadsheet"                # Unless skill handles this
```

**Debugging:** Ask Claude: *"When would you use the [skill name] skill?"* — it will quote the description back. Adjust based on what's missing.

### 🔴 Functional Tests

Verify the skill produces correct outputs.
**Why:** a skill that triggers correctly but produces drifting output fails silently at every use — the contract needs at least one Given/When/Then guard.

```
Test: [scenario name]
Given: [input conditions]
When: Skill executes workflow
Then:
  - [expected output 1]
  - [expected output 2]
  - No errors
```

### 🟡 Test Across Models

Run the skill against every model that may load it :

- **Haiku** — does it have enough guidance to act?
- **Sonnet** — are instructions clear and efficient?
- **Opus** — is the skill over-explaining things Opus already knows?

Skills tuned only for Opus often under-guide Haiku.

### 🟡 Iterate with Claude A / Claude B

- **Claude A** (skill author session) — uses your domain context to draft and refine the skill.
- **Claude B** (fresh session, skill loaded) — executes real tasks; reveals gaps.
- Loop : observe Claude B failure → bring back to Claude A with the specific failure → refine SKILL.md → re-test.

**Why:** Claude A can't see its own blind spots. Claude B's behavior on real tasks is the only ground truth.

### Iteration Signals

| Signal | Problem | Fix |
|---|---|---|
| Skill doesn't load when it should | under-triggering | add keywords and trigger phrases to description |
| Users manually enabling it | under-triggering | add more "Use when" variations |
| Skill loads for unrelated queries | over-triggering | add negative triggers ("Do NOT use for..."), be more specific |
| Inconsistent results | execution issue | improve instructions, add error handling, use scripts |
| Responses degraded / slow | context too large | move content to references/, keep SKILL.md under 5K words |

---

## Anti-Patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| **Information dump** (500 lines of prose) | agent gets lost, skips content | use tables, bullets, WRONG/CORRECT pairs |
| **No priority indicators** | everything looks equally important | add 🔴/🟡/🟢 severity markers |
| **References only at bottom, or bare links** | agent sees the link too late, or without knowing *when* to read it | put 📚 at section start using `📚 **When <trigger> → read <ref>**` |
| **Duplicate content** (SKILL.md AND references/, or copied across skills) | wasted tokens, copies drift apart | ONE place only — single owning skill, others point to it |
| **Generic section names** ("Best Practices") | agent doesn't know when to apply | use "When X" naming (structural exemptions above) |
| **Vague instructions** ("validate properly") | Claude interprets loosely | be specific, use scripts |
| **Passive/conditional voice** ("You should...") | agent treats it as optional | use imperative mood ("Validate...", "Add...") |
| **Negation without alternative** ("Don't use X") | agent knows what NOT to do but not what TO do | always provide a concrete alternative |
| **Flat lists without hierarchy** | relationships between concepts are lost | use indented structure (Rule > Detail > Example) |
| **Windows-style paths** (`scripts\helper.py`) | breaks on Unix; Claude often runs in Linux sandbox | always forward slashes (`scripts/helper.py`) |
| **Time-sensitive content** ("after August 2025…") | becomes wrong silently | move legacy details into `## Old patterns` with `<details>` collapsibles |
| **Inconsistent terminology** ("endpoint"/"URL"/"path") | pattern matching fails when wording drifts | pick one term per concept, keep it everywhere |
| **Too many options** ("use X or Y or Z…") | decision paralysis, agent picks randomly | provide a default + one escape hatch |

---

## When Sizing a Skill

- **Focused** (single topic) — 100–200 lines ; references optional
- **Standard** (domain area) — 200–350 lines ; 1–3 reference files
- **Comprehensive** (full guide) — 300–500 lines ; 3–6 reference files

### If SKILL.md > 500 lines
Extract detailed examples to references/, keep only WRONG/CORRECT pairs in SKILL.md, or split into multiple skills.

---

## Output Contract — Audit Verdict

When this skill is used to audit or review an existing skill, report with this schema —
lead with the single deepest defect, never a flat enumeration:

```yaml
verdict: BLOCK | WARN | PASS        # BLOCK if ≥1 BLOCKING rule violated
deepest_defect:                     # REQUIRED on BLOCK — the one fix that unlocks the others
  rule: "<rule or checklist item name>"
  location: "<file:line>"
  symptom: "<one sentence>"
  fix: "<one sentence>"
violations:                         # all confirmed violations, most severe first
  - rule: "<...>"
    severity: BLOCK | WARN | BEST_PRACTICE
    location: "<file:line>"
    symptom: "<...>"
    fix: "<...>"
false_positives:                    # raw-counter hits dismissed on inspection
  - "<what was flagged and why it does not count — e.g. 🔴 inside an output template>"
notes: "<free-form context, optional>"
```

**Why:** flat audit reports flatten the signal — the reader cannot tell which fix unlocks the others; and without a `false_positives` field, mechanical counters (🔴 occurrences, bad-callout greps) get re-reported and re-"fixed" on every audit pass.

---

## Checklist

### 🔴 BLOCKING
- [ ] Built ≥3 evaluations BEFORE writing the skill, with a baseline
- [ ] Defined 2-3 concrete use cases before writing
- [ ] YAML frontmatter with `name` and `description`
- [ ] Description written in **third person** ("Processes…", not "I can…")
- [ ] Description includes trigger phrases ("Use when...")
- [ ] Description under 1024 characters, no XML tags
- [ ] Sections use "When X" naming (canonical structural sections exempt)
- [ ] Severity markers (🔴/🟡/🟢) on rules
- [ ] WRONG/CORRECT code examples
- [ ] Inline references at section start using `📚 **When <trigger> → read <ref>**` format
- [ ] **References one level deep from SKILL.md** (no nested chains; sibling refs as plain text, cross-skill as "load `<skill>`")
- [ ] Reference files >100 lines have a Table of Contents
- [ ] Instructions use imperative mood
- [ ] Every negation includes a concrete alternative
- [ ] Content uses hierarchical indented structure (Section > Rule > Detail)
- [ ] Every 🔴 BLOCKING **named rule** has a `**Why:**` line (recap checklists, legends, templates exempt)
- [ ] No re-taught native knowledge (decision tables + house rules only); duplicated topics have a single owning skill
- [ ] Output contract defined (schema/template/worked example) if skill produces content
- [ ] End-to-end Input→Output example included (not only rule-level WRONG/CORRECT)
- [ ] If skill bundles scripts: each handles errors explicitly + no voodoo constants + execute-vs-read intent stated
- [ ] If skill bundles a validator script: tested against ≥5 spec-cited examples (positive + negative)
- [ ] If skill is an audit/review skill: leads with single deepest defect (not flat enumeration)
- [ ] Trigger tests pass (should/should NOT trigger)

### 🟡 WARNING
- [ ] Tested with **Haiku, Sonnet, AND Opus**
- [ ] No duplicate content between SKILL.md and references
- [ ] SKILL.md under 500 lines
- [ ] Quick reference tables for common lookups
- [ ] **Forward slashes in all paths** (no `\`)
- [ ] No time-sensitive references in the body (legacy → `## Old patterns` w/ `<details>`)
- [ ] Consistent terminology throughout (one term per concept)
- [ ] No "too many options" — provide a default + one escape hatch
- [ ] MCP tool refs use fully qualified `ServerName:tool_name`
- [ ] No extraneous files (README, CHANGELOG)

### 🟢 BEST PRACTICE
- [ ] Functional tests defined (Given/When/Then)
- [ ] Iterated using Claude A / Claude B loop
- [ ] Code Review Checklist at end
- [ ] Examples match target language/framework conventions
- [ ] Progressive disclosure used for large content
- [ ] Negative triggers added if over-triggering risk
