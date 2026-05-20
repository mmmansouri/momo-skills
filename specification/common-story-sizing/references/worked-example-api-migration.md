# Worked Example — API V2 → V3 Migration Epic

> Companion to `common-story-sizing/SKILL.md`. Shows a real anti-pattern
> decomposition that violated all five sizing rules, and the corrected
> macro-Story breakdown.

## Table of Contents

1. [Context](#context)
2. [The original decomposition (anti-pattern)](#the-original-decomposition-anti-pattern)
   - [Rule violations](#rule-violations)
3. [The corrected decomposition](#the-corrected-decomposition)
   - [Rule compliance](#rule-compliance)
4. [Lessons captured](#lessons-captured)

---

## Context

This example is anonymised from a production Epic that migrated a shipping
provider integration from a legacy v2 API surface to a new v3 surface (DTOs,
endpoints, webhook contract, status enum, return workflow). Three apps were
involved: a backend service, an in-house mock API used in CI, and an admin
UI. The labels below (`[backend]`, `[mock-api]`, `[admin]`) are the per-app
routing labels used by the implementation orchestrator.

---

## The original decomposition (anti-pattern)

The migration Epic was decomposed into **28 Stories** mechanically along
v2/v3 endpoint pairs and architectural layers:

```
Story  1: [backend]  Add ProviderShipmentStatus v3 enum
Story  2: [backend]  Migrate REST client base URL v2 → v3
Story  3: [mock-api] Replace api/v2/parcel/*    by api/v3/shipments/*
Story  4: [mock-api] Replace api/v2/shipping/*  by api/v3/shipping-options
Story  5: [mock-api] Add api/v3/returns/*
...
Story 11: [backend]  Replace V2* DTOs by ProviderShipment{,Carrier,Address}*
Story 12: [backend]  Migrate ProviderService.createParcel → createShipment
Story 13: [backend]  Replace ProviderShippingMethod by ProviderShippingOption
Story 14: [backend]  Wire v3 webhook handler
...
Story 22: [backend]  Delete legacy V2 DTOs and obsolete code
Story 23: [admin]    Remove legacy "Mark Return Shipped" dialog
Story 24: [admin]    Add return timeline component
Story 25: [admin]    Add return actions menu
Story 26: [admin]    Add returnStore signal store
Story 27: [admin]    Wire return list page to v3 API
Story 28: [admin]    Wire return detail page to v3 API
```

Plus **20 E2E companion Stories** auto-generated from the implementation
Stories, including titles such as
*"E2E: Replace V2 DTOs by ProviderShipment{,Carrier,Address}*"* — which
have no executable user scenario.

### Rule violations

| Rule | Violation |
|---|---|
| **Rule 1** (vertical slice) | Stories 11–14, 22, 24–28 are horizontal slices (DTO-only, service-only, store-only). None is demoable alone. |
| **Rule 3** (demoable in isolation) | Story 11 cannot demo without Story 12 + 13 + 22 also merged. Stories 24–28 cannot demo without each other. |
| **Rule 4** (6–10 Stories per Epic) | 28 Stories ≈ 3× the upper band. The Epic becomes a chore-list. |
| **Rule 5** (1 E2E per macro-Story) | 20 auto-generated E2E companions, most pointing at internal artifacts with no user-facing scenario. |

Note: **Rule 1 corollary (one routing label per Story)** is not violated
here because each Story carries a single app label. The decomposition's
problem is purely horizontal slicing within each app, not cross-app
orphaning.

---

## The corrected decomposition

**6 macro-Stories**, each a vertical slice within one deployable, each
demoable in isolation:

| # | Macro-Story | SP | E2E companion |
|---|---|---|---|
| 1 | `[mock-api] Full v3 endpoint surface (shipments + shipping-options + returns + statuses + label-asset) + delete v2` | 13 | mock v3 + webhook regression |
| 2 | `[mock-api] WebhookDispatcher (FIFO + HMAC) + admin "Webhook Settings" page` | 8 | webhook delivery E2E |
| 3 | `[backend] v3 integration (DTOs + services + webhook wrapper + delete v2)` | 13 | outgoing shipping v3 happy path |
| 4 | `[backend] Rename internal domain Parcel → Shipment (entities + repos + endpoints + Liquibase)` | 5 | none — internal refactor |
| 5 | `[backend] Return workflow (entity + state machine + service + customer email)` | 13 | return happy path |
| 6 | `[admin] Return UI (remove legacy dialog + timeline + actions + signal store)` | 9 | return UI E2E |

### Rule compliance

| Rule | Check |
|---|---|
| **Rule 1** ✓ | Each Story is a vertical slice within ONE app, with observable behaviour. |
| **Rule 2** ✓ | Every Story ≤ 13 SP. |
| **Rule 3** ✓ | Each Story is demoable in isolation on the day its PR merges. |
| **Rule 4** ✓ | 6 Stories, within the 6–10 healthy band. |
| **Rule 5** ✓ | 5 E2E companions (Story 4 is an internal rename, no user scenario). |

The corrected plan also drops the foundational micro-Stories (v3 status
enum + REST client base URL) — those had already shipped as part of an
earlier preparation phase and no longer belong in the Epic Story
Breakdown.

---

## Lessons captured

1. **The orchestrator chose endpoint pairs as Story boundaries.**
   Endpoint pairs are a *task* axis, not a *value* axis. The first
   refactor was rejected on Rule 1 grounds; the corrected breakdown
   re-anchored on "what does the customer / admin observe?"

2. **"Delete legacy code" is not a Story.** It is a sub-task of every
   v3 Story that replaces a v2 path. Stories 11–13 + 22 collapsed into
   Story 3 in the corrected plan precisely because each v3 service
   adoption naturally carries the deletion of its v2 counterpart.

3. **Auto-generated E2E companions amplify the anti-pattern.** When
   every implementation Story has its own E2E, horizontal slicing
   becomes invisible: the E2E count "matches" the Story count, giving
   a false sense of coverage. In the corrected plan, 5 E2Es cover 6
   Stories — and that asymmetry is the *signal* that Story 4 is an
   internal refactor, not user-facing work.

4. **Renames deserve their own vertical Story when the rename is the
   value.** Story 4 (`Parcel → Shipment`) is kept separate at 5 SP
   because mixing it into Story 3 would have inflated Story 3 beyond
   13 SP and conflated two distinct change vectors (API surface vs
   internal naming). The rule of thumb: a rename earns its own Story
   when it touches > 30 files OR > 1 deployable boundary.
