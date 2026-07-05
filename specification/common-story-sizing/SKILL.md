---
name: common-story-sizing
description: >-
  Story sizing and splitting heuristics. Use when planning an Epic and choosing
  Story-breakdown granularity, refining a draft Story that feels too big,
  deciding whether to merge two siblings into one macro-Story, or auditing a
  Story Breakdown table for over- or under-decomposition. Companion to
  `spec-content` (INVEST table) — this skill holds the deep treatment: vertical
  slicing, SPIDR (Cohn), Lawrence's 9 patterns, the 8 SP warning / 13 SP hard cap,
  the runner-budget sized rule (≤ 10 ACs / ≤ 8 SP / ≤ 200 KB spec ADF), the
  demoable-in-isolation test, and the worked anti-pattern catalog. Make sure
  to use it whenever the user mentions sizing, splitting, decomposition,
  granularity, vertical slice, macro-Story, SPIDR, story points threshold, or
  "how many Stories per Epic" — even without saying "common-story-sizing". Do
  NOT use for sprint-planning logistics (velocity, capacity, sprint goals),
  Story-body content authoring (load `spec-content`), or generic Agile
  methodology.
---

# Common Story Sizing

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

This skill answers a single question: **is this Story the right size, and if not,
how do I split it?** It is project-agnostic — examples use neutral app labels
(`[backend]`, `[admin]`, `[mock-api]`); for the project-specific routing labels
that map to these in your codebase, load the matching `<project>-jira` skill.
For companion guidance on WHAT to write in a Story body (INVEST, AC quality)
load `spec-content`; for the HOW sequence (planning vs refinement steps) load
`spec-workflow`. See "Related Skills" at the bottom for the full list.

The six 🔴 BLOCKING rules at the top are the contract. The catalogue of
splitting techniques (SPIDR, Lawrence) and the worked examples are how you
apply the rules in practice.

---

## 🔴 BLOCKING — The Six Sizing Rules

### Rule 1 — Every Story is a VERTICAL SLICE (within a single deployable unit)

A Story must cut across architectural layers (UI + business logic + persistence
+ tests) as needed to deliver observable behaviour. **Never** plan a Story per
layer, per endpoint, per DTO, per migration, per service class.

**Vertical = per deployable unit / per routable app, NOT cross-app.** In a
monorepo where each app is its own deployable (and where the implementation
routing agent picks ONE routing label per Story → ONE app directory →
implements there only), a Story that carries multiple app labels is
**orphaned at execution time**: only one app will be implemented, the other
side is dropped silently. If a feature genuinely spans N apps, plan **N
vertically-sliced Stories** (one per app) linked by `Depends On` — never one
bi-app Story. The combined demo of the feature lives on the last Story in
the chain.

**Why:** horizontal Stories ("rewrite DTOs", "rename entity", "add migration")
have no observable value on their own. They cannot be demoed, cannot be tested
end-to-end, and cannot be released independently. They violate INVEST-V
(Valuable) and INVEST-T (Testable) by construction. Cross-app Stories are the
multi-app variant of the same anti-pattern: they pretend to be vertical, but
the per-app routing system that picks them up cannot honour the bi-label
contract.

**Anti-patterns to refuse outright** (generic shipping-provider migration
example, project labels neutralised):

```
🔴 WRONG — horizontal slices, one per layer:
"[backend] Replace V2* DTOs by ProviderShipmentRequest/Response"
"[backend] Migrate ProviderService.createParcel → createShipment"
"[admin]   Add returnStore signal store"
"[backend] Delete legacy V2 DTOs and obsolete code"

🔴 WRONG — cross-app Story (orphaned at routing):
"[backend+admin] Process customer returns end-to-end with v3 conformity"
                 ↑ routing agent picks ONE label → other app dropped silently

✅ CORRECT — vertical slice within ONE app, chained via Depends On:
Story-D: "[backend] Process customer returns end-to-end (v3 webhook conformity)"
Story-E: "[admin]   Return UI + remove legacy dialog (depends on Story-D)"
         ↑ each Story routes to one app cleanly; combined demo lives on Story-E

✅ CORRECT — single-app vertical slice, observable from outside:
"[backend]  Ship customer orders through provider v3 (rate + create + label + status)"
"[mock-api] Serve full v3 API surface and replace v2 admin console"
```

### Rule 2 — 8 Story Points is the WARNING threshold, 13 SP is the HARD CAP

If a Story estimates at **≥ 8 SP**, that is a signal to attempt a vertical
split via SPIDR or Lawrence patterns (catalogue below). If after honest analysis
no clean vertical split exists, document the rationale and proceed.

If a Story estimates at **≥ 13 SP**, that is a 🔴 BLOCK — split is mandatory.

**Why the threshold moved 13 → 8 (warning) / never → 13 (BLOCK):** 13 SP was
the Fibonacci-warning convention in agile literature (Mountain Goat /
Atlassian community) — calibrated for human pair-programming weeks, not for
an LLM agent with a hard runtime ceiling. The agile intuition that "13 SP
vertical is healthier than two 6 SP horizontal halves" remains correct *for
human teams*; it fails for the agent runner, where cost grows super-linearly
with run length — see the Rule 6 cost incident (BNAT-432 vs BNAT-431) for
the measured numbers.

**Estimation scale used by this skill:**

| 1 | 2 | 3 | 5 | 8 | 13 | ~~21~~ |
|---|---|---|---|---|---|---|
| trivial | small | small-medium | medium | warning threshold | **BLOCK — must split** | **stop — this is an Epic, not a Story** |

🔴 **BLOCKING corollary:** any work estimated at 21+ SP is by definition an
Epic. Convert it to an Epic and apply this skill's full breakdown process —
do not push it to the backlog as a single Story.

**Why:** at 21 SP the team is no longer estimating, it is guessing — the
Fibonacci gap between 13 and 21 (a 60 % jump) signals that confidence
intervals exceed the estimate itself. A 21+ SP Story silently absorbs
scope creep because the team has no shared mental model of what "done"
means; an Epic forces the decomposition that surfaces that scope and lets
each sub-Story be re-estimated with confidence.

### Rule 3 — Every Story is DEMOABLE IN ISOLATION

The Story owner must be able to demo "it works" to a stakeholder without
depending on the merge of another Story in the same Epic. If the demo
requires *"once Story B is merged, you'll see..."* — the Story is not
independently testable. Either merge A and B into one Story, or re-sequence
so A's demo is self-contained.

**Why:** this is the sharper form of INVEST-T (Testable) and INVEST-I
(Independent). The original INVEST-I definition ("prioritizable independently
from technical dependencies") is necessary but not sufficient — many teams
satisfy INVEST-I on paper and still ship Stories that cannot be demoed alone.
Use the demoable-in-isolation test as the operational check.

**Self-test before pushing a Story Breakdown to Jira:**

> *Could I record a 60-second screen-capture of this Story working, end-to-end,
> the day its PR merges to develop — without checking out any other Story's
> branch?*

If no → the Story is horizontal or premature. Split or merge.

### Rule 4 — An Epic holds 6 to 10 Stories (relative to team velocity)

The Humanizing Work / Richard Lawrence guidance is *"by the time a Story makes
it to the top of your backlog, you should be able to fit 6 to 10 into a
sprint."* This translates at Epic level to: **a healthy Epic holds 6 to 10
Stories**, scaled to team capacity. ≥ 15 Stories per Epic is a red flag —
decomposition is too fine, almost certainly horizontal.

**Why:** beyond ~10 Stories the Jira admin overhead exceeds the delivery
benefit. The Epic becomes a chore-list, not a coherent feature. ≥ 15 Stories
also means the user-visible feature has been sliced into invisible internal
sub-tasks, violating Rule 1.

The 11→14 window exists because some genuinely large features land between
"clean Epic" and "should-have-been-two-Epics". In that window every Story
must individually pass Rule 1 + Rule 3 — if even one of them is horizontal,
the breakdown is wrong and the Epic count is masking the real problem.

**Sanity check:** before approving a Story Breakdown table, count the rows.

| Count | Interpretation |
|---|---|
| 1-5 | Probably under-decomposed if the Epic is non-trivial. Either the Epic is small (fine), or some Stories are 13+ SP and want a vertical split. |
| 6-10 | Healthy band. Likely well-decomposed. |
| 11-14 | Yellow zone. Verify each Story passes Rule 1 + Rule 3 individually. If one fails, the band is *masking* horizontal slicing — re-decompose, do not just accept the higher count. |
| ≥ 15 | Red flag. The decomposition is mechanical — almost certainly one Story per endpoint / layer. **Re-decompose**, or split the Epic in two. |

### Rule 5 — E2E companions are 1 per macro-Story (not per implementation Story)

An E2E companion exists to validate a user-facing scenario. **One E2E per
vertical-slice Story.** Skip E2E for pure technical Stories (foundation enum,
base URL switch, deletion of legacy code, internal rename). If you are
auto-generating an E2E for every Story, the decomposition is wrong — see
Rule 1.

**Why:** auto-generated E2E companions on horizontal Stories produce
E2E titles like *"E2E: Replace V2 DTOs by ProviderShipmentRequest/Response"*
that have no executable scenario. The E2E exists to test a user path, not
to mirror the implementation Story 1:1.

**E2E granularity rule of thumb:** if you cannot name the user scenario in
one sentence ("customer ships an order and receives DELIVERED notification"),
do not create an E2E companion.

**🔴 Annotate every skip explicitly.** When the Story Breakdown table omits
the E2E for a Story, the row's `E2E` column MUST contain a one-sentence
rationale (e.g. `no-E2E: backend-only, covered by Story-E companion` or
`no-E2E: internal rename, no user-facing scenario`) — never leave it blank.
Silent skips are indistinguishable from forgetting at audit time and remove
the planner's accountability for the choice.

**🔴 No batching across Stories.** Never assign one E2E companion to N>1
source Stories. If two Stories truly share a single user scenario, they
fail Rule 1 (vertical slice) — merge them into one macro-Story. Otherwise,
each E2E targets exactly one source Story. A 1:N batched E2E is a horizontal
slice in disguise: it hides which Story actually owns the user-visible
behaviour.

### Rule 6 — Runner-Budget Sized (mandatory for any agent-runner project)

A Story must be implementable in a single agent runner pass without exceeding
the runner's soft-deadline (~70 % of hard timeout — for the buy-nature
`claude -p` runner that means ≤ ~30 min of productive work). When a Story
exceeds the hard caps below, splitting is **mandatory** — even when each
resulting half remains vertical (Rule 1) and demoable (Rule 3).

**Hard caps — any ONE violation triggers 🔴 BLOCK:**

| Signal | Hard cap | Why |
|---|---|---|
| Acceptance Criteria count | > 10 | More than 10 ACs cannot be both implemented and tested in a single runner pass without thrashing the cache. |
| Story Points | > 8 | Intersects with Rule 2; runner cost grows super-linearly past 8 SP. |
| Refined spec ADF size | > 200 KB | Large spec means large prefetch; every sub-agent turn replays the brief in cache. |
| Architectural concerns | > 3 | E.g. back domain + back service + UI page = 3 ✅; add admin layer = 4 ⇒ split. |

**Soft warns — ≥ 2 triggers 🟡 WARN, ≥ 3 triggers 🔴 BLOCK:**

- new files estimated > 15
- Story touches > 2 layers (backend + UI + E2E counts as 3)
- concurrency / threading in scope (per-resource lock, ExecutorService, retry poller, etc.)
- new background scheduler or long-running task in scope
- combines non-trivial backend work with "+ admin UI" or "+ admin page"

**Why:** the agent runner is constrained by a hard timeout (typical 25-45 min)
and the LLM prompt cache replays the cumulative conversation on every turn.
Cache_read cost grows super-linearly with run length. A 13 SP "vertical
demoable" Story can blow the budget despite passing Rules 1-5 — see the
BNAT-432 cost incident: **12 ACs / 13 SP / 247 KB spec / dispatcher + UI =
$132 burned at hard timeout for 80 % of the work non-committed**, while
BNAT-431 (10 ACs / 8 SP) succeeded in 14 min 59 / $9.24 with similar surface
area.

**How to split under Rule 6:**

1. Apply SPIDR / Lawrence first to find a clean vertical seam.
2. Default pattern for backend-with-admin-UI Stories:
   - Story A: "backend X core + tests" (vertical slice — operator can verify
     via curl + logs + admin API).
   - Story B: "admin UI for X" linked by `Depends On` Story A (rides the
     infrastructure; demoable as a UI workflow).
   This is the **Major-Effort** split (Lawrence pattern 6).
3. Forbidden splits (these violate Rule 1):
   - "tests vs no-tests"
   - "happy path vs error paths"
   - "DTOs only vs service only"
   - "data layer vs business logic"

**Compatibility with Rule 1:** Rule 6 splits ARE vertical inside each half.
The backend-only Story is demoable from outside (curl / admin API / log
inspection), and the UI Story rides on it. Both pass Rule 3 by design.

**Validation procedure:** before pushing a refined Story description to Jira,
run the four hard-cap checks (AC count, SP, spec KB, concerns count). One
violation = re-decompose. The check costs <1 minute; the alternative is a
$130+ runner failure on the first implementation attempt.

---

## When Producing an Audit Output

When this skill is invoked to audit an existing Story Breakdown (Epic plan,
draft Story list, refinement candidate), the output MUST follow this
contract — not a flat enumeration of every rule that is not perfect.

### Output Schema

```yaml
verdict: BLOCK | WARN | PASS          # BLOCK if ≥1 BLOCKING rule violated
deepest_defect:                       # single most damaging issue, REQUIRED on BLOCK
  rule: 1 | 2 | 3 | 4 | 5 | 6
  story_ids: [BNAT-XXX, ...]          # or row numbers when no Jira key
  symptom: "<one sentence>"
  fix: "<one sentence — collapse / split / re-label / drop>"
rule_violations:                      # all violations, ordered by severity
  - rule: <N>
    severity: BLOCK | WARN
    story_ids: [...]
    symptom: "<...>"
    fix: "<...>"
breakdown_count: <int>
healthy_band: "6-10"
notes: "<free-form context, optional>"
```

### 🔴 BLOCKING — Lead with the single deepest defect

**Why:** audit reports that enumerate every issue side-by-side flatten the
signal. The reader cannot tell which fix unlocks the others. The deepest
defect is almost always the root cause — fix it and several downstream
violations evaporate. In the worked example (28 Stories → 6), the root
cause was Rule 1 (horizontal slicing); Rules 3, 4, 5 violations were
*consequences*. An audit that listed all four side-by-side would have
invited the team to negotiate each one separately.

**Selection rule for `deepest_defect`:**

1. If any Story violates Rule 1 (vertical slice) → that is the deepest defect.
2. Else if any Story violates Rule 3 (demoable in isolation) → that is the deepest.
3. Else if any Story violates Rule 6 (runner-budget hard cap) → that is the deepest.
4. Else if Rule 4 is violated (count outside 6-10) → that is the deepest.
5. Else if any Story violates Rule 2 (≥ 8 SP warning / ≥ 13 SP BLOCK without rationale) → that is the deepest.
6. Else if Rule 5 is violated (E2E inflation) → that is the deepest.

The order reflects causality: Rule 1 violations cause Rule 3 + 4 + 6 violations;
fixing Rule 1 collapses the cascade. Rule 6 ranks above Rule 4 because a
Story that blows the runner budget cannot ship at all — fixing it forces
re-counting the Epic anyway.

### Verdict Mapping

| Condition | Verdict |
|---|---|
| ≥ 1 BLOCKING rule violated (Rule 1, 2, 3, 4, 5, or 6) | `BLOCK` |
| Only 🟡 WARNING items from the Quick Self-Check | `WARN` |
| All 🔴 BLOCKING checks pass and ≤ 1 🟡 WARNING item | `PASS` |

### Example Output (worked example, abridged)

```yaml
verdict: BLOCK
deepest_defect:
  rule: 1
  story_ids: [Story-11, Story-12, Story-13, Story-22, Story-24..28]
  symptom: "9 Stories are horizontal slices (DTO-only, service-only, store-only) — none is demoable alone."
  fix: "Collapse into 3 vertical macro-Stories per app (backend v3 integration / return workflow / admin return UI)."
rule_violations:
  - rule: 1
    severity: BLOCK
    story_ids: [Story-11, ..., Story-28]
    symptom: "Stories cut by layer, not by user-observable behaviour."
    fix: "Re-anchor each Story on a user scenario; fold deletion of legacy v2 into the v3 Story that replaces it."
  - rule: 4
    severity: BLOCK
    story_ids: [all]
    symptom: "28 Stories in one Epic — 3× the upper band."
    fix: "Collapse to 6 macro-Stories (see deepest_defect fix)."
  - rule: 5
    severity: BLOCK
    story_ids: [E2E-11, E2E-22, ...]
    symptom: "20 auto-generated E2E companions including titles with no user scenario."
    fix: "Drop E2E companions on horizontal Stories; after re-decomposition, 5 E2Es cover 6 Stories."
breakdown_count: 28
healthy_band: "6-10"
notes: "Story 4 in the corrected plan is an internal rename — no E2E by design."
```

---

## When Splitting a Large Story — SPIDR (Cohn)

Apply SPIDR in order, top-down. The first match wins.

| Technique | When | Example |
|---|---|---|
| **S** — Spike | The team does not know enough to estimate / design the Story | Extract a 2-day Spike: "Compare commercial OCR libraries", then plan the implementation Story afterwards |
| **P** — Path | Users reach the same goal through multiple routes | Share a video: "via URL" / "via social media" / "via embed code" → 3 Stories, each end-to-end |
| **I** — Interface | The UI is the bulk of complexity, deliverable in stages | "Share button: text only" → "Share button: dropdown" → "Share button: rich gallery" |
| **D** — Data | Story handles multiple data shapes, can ship one first | "Upload MP4" first → "Upload AVI/MOV/MKV" later |
| **R** — Rules | The Story bundles many business rules, can ship a subset first | "Validate file size" first → "Validate copyright" later |

If none of the five fit, the Story is **not splittable cleanly** — keep it as
one Story (documenting the no-split rationale per Rule 2) rather than forcing
a horizontal split.

---

## When Splitting a Large Story — Richard Lawrence's 9 Patterns

Use this list when SPIDR yields no candidate.

1. **Workflow Steps** — break a sequential process. Checkout: address → payment → confirmation.
2. **CRUD operations** — split "manage X" into Create / Read / Update / Delete.
3. **Business Rule Variations** — separate distinct rule implementations (e.g. flexible date search options).
4. **Variations in Data** — handle data complexity progressively (geography, localization, locale, currency).
5. **Data Entry Methods** — split simple form from fancy/complex input (CSV import, drag-drop).
6. **Major Effort** — defer low-complexity variants when infrastructure carries most effort (first integration the hard one; copies for the others come cheaply).
7. **Simple / Complex** — extract the simplest version; move variations into separate Stories.
8. **Defer Performance** — build for correctness first; optimize later in a follow-up Story.
9. **Spike** — time-boxed investigation when implementation is poorly understood (same as SPIDR-S).

**Rule of thumb:** prefer SPIDR for the common cases. Fall back to Lawrence
when the Story's complexity comes from process flow, CRUD multiplicity, or
deferred non-functional concerns (performance, accessibility, security).

---

## When Refusing to Split — the legitimate cases

In the 8-12 SP warning band it is correct to keep a Story whole (with the
documented no-split rationale Rule 2 requires) when splitting would produce:

1. **Horizontal layers** — "Replace DTOs" + "Migrate service" + "Update
   controller" violates Rule 1; a V2→V3 replacement touching DTOs + service
   + controller + tests is **one** vertical Story.
2. **Undemoable halves** — "Add Return entity (Liquibase + JPA)" alone is not
   demoable (Rule 3); merge the entity work into the customer-facing Story.
3. **Cross-Story technical dependencies inside the same sprint** — if A and B
   touch the same files and B cannot demo without A's merge, they are one Story.

Above 13 SP there is no legitimate refusal: Rules 2 and 6 make the split
mandatory — find the vertical seam (Major-Effort split, "How to split under
Rule 6").

---

## When Validating Against the Worked Example

A real production Epic migrated a shipping-provider integration from a
legacy v2 API to a new v3 surface across three apps (backend service,
in-house mock API, admin UI). The first decomposition produced **28
horizontal Stories + 20 auto-generated E2E companions** and violated
Rules 1, 3, 4, 5 simultaneously. The corrected decomposition collapsed
this to **6 macro-Stories**, each a vertical slice within one app, each
demoable in isolation.

📚 **When auditing a real Story Breakdown against the six rules, when
explaining horizontal slicing to a stakeholder, or when needing a concrete
rule-by-rule violation pattern with its corrective decomposition → read
[worked-example-api-migration.md](references/worked-example-api-migration.md).**

The key takeaway in one sentence: **endpoint pairs are a task axis, not
a value axis** — re-anchor every Story on the user-observable behaviour
it delivers, then let the deletion of the v2 counterpart fall out
naturally inside each v3 Story.

---

## When Spotting an Anti-Pattern in a Story Breakdown

| Anti-pattern | Symptom in Story Breakdown | Fix |
|---|---|---|
| **1 Story = 1 endpoint** | "Replace endpoint X by endpoint Y" repeated N times | Merge endpoint Stories into one vertical "Migrate API surface" Story |
| **1 Story = 1 layer** | "Add DTOs" / "Migrate service" / "Update controller" siblings | Merge into one vertical "Feature X" Story |
| **1 Story = 1 migration** | "Add Liquibase migration for Y" as standalone | Fold the migration into the user-facing Story it supports |
| **Delete-en-bloc Story** | "Delete legacy V2 code" as a separate Story | Distribute the deletion across the V3 Stories that replace each V2 path |
| **Rename-en-bloc Story** | "Rename Parcel → Shipment everywhere" as one mega-Story | Acceptable when scope is narrow (internal refactor, < 5 SP), otherwise distribute into the V3 Stories |
| **Cross-app Story (multi-label)** | One Story carries 2+ app routing labels (e.g. `[backend+admin]`) | Split into N mono-app Stories linked by `Depends On`. Per-app routing systems pick one label and orphan the rest — see Rule 1 corollary |
| **Auto-generated E2E per Story** | Every Story has an E2E companion with a non-user-facing title | Apply Rule 5 — 1 E2E per macro-Story, skip technical Stories |
| **"Part 1 / Part 2 / Part 3" titles** | Sequential numbered Stories | The user cannot consume Part 1 alone — the decomposition is wrong, merge |
| **All Stories carry `Parallel = Yes`** | No declared dependencies in a multi-Story Epic | Implausible; re-examine — true parallelism usually exists for 2-3 Stories, not all |

---

## Quick Self-Check Before Pushing a Story Breakdown

Run through this list before writing the envelope JSON.

🔴 **BLOCKING:**

- [ ] Each Story is a vertical slice (touches all layers needed to deliver
      observable behaviour) — Rule 1.
- [ ] Each Story carries EXACTLY ONE app routing label — Rule 1 corollary
      (cross-app Stories are orphaned by per-app routing).
- [ ] No Story estimates above 13 SP; Stories ≥ 8 SP have a documented
      no-split rationale — Rule 2.
- [ ] Each Story is demoable in isolation — Rule 3 self-test passed.
- [ ] Story count is in the 6-10 band (or justified outside it) — Rule 4.
- [ ] E2E companions: 1-per-Story OR row annotated `no-E2E: <rationale>`;
      no batching (1 E2E for N>1 Stories) — Rule 5.
- [ ] Each Story passes Rule 6 hard caps: AC count ≤ 10, SP ≤ 8, refined
      spec ADF ≤ 200 KB, architectural concerns ≤ 3 — Rule 6.
- [ ] No Story carries ≥ 3 Rule 6 soft-warn signals (new files > 15,
      > 2 layers touched, concurrency, scheduler, "+ admin UI" alongside
      non-trivial backend).

🟡 **WARNING:**

- [ ] No Story title starts with a verb that names an internal artifact ("Add
      DTOs", "Migrate service", "Refactor X") — those signal horizontal slicing.
- [ ] No Story title contains "Part 1 / Part 2" sequence markers.
- [ ] No Story title is a verbatim copy of a V2 → V3 endpoint pair (those are
      task descriptions, not user-value statements).
- [ ] Each E2E companion title names a user-facing scenario, not an
      implementation detail.
- [ ] No Story carries 2 Rule 6 soft-warn signals (one signal alone is fine;
      two together is a yellow flag — re-examine the split rationale).

🟢 **BEST PRACTICE:**

- [ ] Each Story's title can be read aloud and understood by a non-technical
      stakeholder.
- [ ] Each Story's E2E companion has a clear "Given / When / Then" scenario
      sketch in the description.
- [ ] The Story Breakdown table has at most 3 Stories per app — if more,
      challenge the per-app decomposition.

---

## Related Skills

- `spec-content` — INVEST table, AC quality, label rule, Quality Checklist.
- `spec-workflow` — step sequence for feature planning and Story refinement.
- `jira-adf` — ADF format for Story Breakdown table.
- `<project>-jira` — project-specific labels (label mapping drives the "one
  routing label per Story" check that intersects with Rule 1).

