# Sub-Frame: Port-Trigger Map (v1)

**Status:** v1 frozen — design ready, implementations open
**Parent frame:** [ATTRACTOR_FRAME.md](../ATTRACTOR_FRAME.md)
**Parent slots affected:** 11 (morphon-controller), 14 (crystal-fabric), 15 (agrm), 22 (lambda), 26-28 (atlas/julia/dispatch), 33 (daemon-crt), all L0-L4 cmplx port slots
**Triggered by user direction:** 2026-05-17 — "port triggers are going to be handled by daemons, and local controls, so each system needs to explicitly know and be known for where and when its porting occurs."

---

## 0. Why this sub-frame exists

After Wave 0 + Slots 19/24/25 landed, 13 cmplx ports are registered and callable. But "callable" isn't the same as "triggered" — right now every port invocation comes from explicit consumer code (`MorphonController.get(port).method()`). The architectural intent, repeatedly surfaced across the formalization docs, is that ports fire in **structured contexts**: daemon ticks, event boundaries, local-control overrides, dispatch-tree steps.

Without a typed trigger model:
- Slot 15 (AGRM/routing) can't be wired because nothing knows when routing should fire — every call into AGRM today must be explicit, but the design intent is that AGRM fires on daemon E8-orientation publications.
- Slot 22 (lambda) can't be wired because lambda evaluation has multiple triggering contexts (explicit eval, embed-driven, geometry-driven) with no shared shape.
- Slot 14 (crystal) can't be added to KNOWN_PORTS until we know what triggers crystal-fabric operations.
- Slot 33 (daemon-crt) already runs 24+ coprime-period channels but has no formal mapping to port operations.

This sub-frame defines the trigger model so those implementations can be designed against a stable contract.

## 1. Trigger classes

Every port operation falls into exactly one of four trigger classes. Most ports support multiple operations with different classes (e.g., `memory.store` is event-driven, `memory.by_e8_coordinates` is user-driven, a future `memory.compact` would be daemon-periodic).

### A. User-driven (explicit call)

The operation fires only when user code explicitly calls it. No daemon involvement, no event triggering. Idempotent in the sense that calling N times produces N effects.

**Examples:** `engine.evolve`, `receipt.mint`, `embed.decompose`, `geometry.e8_coordinates` (when called directly), `symbolic.run_program`.

### B. Event-driven (boundary crossing)

The operation fires automatically when a boundary event occurs. The boundary is one of: morphon admit, state transition, store, receipt mint, edge creation. Event-driven operations are the "reactive" layer — they fire in response to other system activity, not on a clock.

**Examples:** `constraints.admit` (fires inside `admit_and_store`), `geometry.e8_coordinates` (fires inside `admit_and_store`), `addressing.channel_for` (same), `memory.store` (same).

### C. Daemon-periodic (CRT-scheduled)

The operation fires on a clock — specifically, a daemon CRT channel tick. Each periodic operation is associated with one daemon channel and a prime-period multiple of that channel's tick rate. The CRT scheduling ensures no two periodic operations interfere within a finite window.

**Examples:** `diagnostic.morsr_pulse` (every N ticks of the "brain_sync" channel), `cache.flush` (every M ticks of "report_generate"), `conservation.ledger_compact` (every K ticks of "knowledge_sync"), `routing.recompute_lanes` (every J ticks once orientation is published).

### D. Local-control (per-Morphon configured)

The operation fires when a specific Morphon's local configuration says so. Local control is the most flexible trigger class — a Morphon can declare "when my state transitions to VALIDATING, invoke `symbolic.derive` on myself," and that fires automatically when the transition happens. The configuration lives in the Morphon's payload or in a sidecar.

**Examples:** a Morphon's `triggers` config might say `{"on_state_change": "symbolic.derive", "on_evidence_update": "constraints.admit"}`. These fire from the controller's mediation layer, but only for Morphons that opted in.

## 2. The trigger map: ports × operations × classes

The table below is the v1 canonical map. New port operations declare their trigger class as part of their Protocol contract.

| Port | Operation | Trigger class | Daemon channel | Notes |
|---|---|---|---|---|
| `receipt` | `mint` / `mint_*` | A (user) | — | Every cmplx component calls this directly |
| `receipt` | `verify_chain` | C (periodic) | `audit` | Daemon runs verify on a slow tick; emits health |
| `conservation` | `phi(morphon)` | A (user) | — | Read on demand |
| `conservation` | `ledger_compact` | C (periodic) | `knowledge_sync` | Drop old grains beyond retention window |
| `diagnostic` | `pulse(seed)` | A or C | `brain_sync` | User-driven OR periodic; daemon mode for steady ripples |
| `diagnostic` | `spectral.report` | C (periodic) | `report_generate` | Slot 24 — runs on report tick |
| `diagnostic` | `causal.attribution` | A (user) | — | Slot 25 — explicit query on outcomes |
| `geometry` | `e8_coordinates` | B (event) | — | Fires inside `admit_and_store` |
| `geometry` | `leech_point` | B (event) | — | Same |
| `constraints` | `admit` | B (event) | — | Fires at the admission boundary |
| `engine` | `evolve` | A (user) | — | Explicit CQE operation invocation |
| `transport` | `encode` / `decode` | A (user) | — | Caller-driven I/O |
| `symbolic` | `derive(morphon)` | A or D | — | User-driven or local-control via Morphon config |
| `symbolic` | `run_program` | A (user) | — | Direct ETP execution |
| `routing` (F-6) | `solve(start, end)` | A (user) | — | Path-finding is on-demand |
| `routing` (F-6) | `recompute_lanes` | C (periodic) | `service_discover` | Slow refresh of hash-lane index |
| `routing` (F-6) | `ingest_orientation` | C (periodic) | `tmn2_pulse` | Consume daemon-published E8 orientation |
| `lambda` (F-7) | `evaluate(term)` | A (user) | — | Explicit eval call |
| `lambda` (F-7) | `evaluate_on_state_change` | D (local) | — | Per-Morphon: eval this term whenever this Morphon transitions |
| `crystal` (new) | `forge / register` | A (user) | — | Setup-time registry calls |
| `crystal` (new) | `tier_promote` | C (periodic) | `tier_promote` | Cron-driven promotion based on activity |
| `memory` | `store` / `fetch` | B (event) or A | — | Mostly event-driven via `admit_and_store` |
| `memory` | `prune_stale` | C (periodic) | `aggregate` | Periodic cleanup |
| `addressing` | `channel_for` / `quantize24` | A or B | — | User-driven, fires inside admit_and_store |
| `snap` | `label(morphon)` | B (event) | — | Fires during admit; classification at boundary |
| `snap` | `gate369` | A (user) | — | Explicit gate evaluation |
| `cache` | `cache_get` / `cache_put` | A (user) | — | Direct API |
| `cache` | `evict_cold` | C (periodic) | `compose_round` | Periodic eviction |
| `embed` | `decompose` | A or D | — | User-driven; or local-control: "decompose me whenever my state changes" |

## 3. Daemon channel ↔ port operation binding

The 24 daemon channels established in [src/daemon/](../../src/daemon/) are repurposed as **trigger sources** for class-C operations:

| Channel | Period (ticks) | Bound to | Purpose |
|---|---|---|---|
| `health_ping` | 2 | service health probes | (unchanged) |
| `service_discover` | 3 | `routing.recompute_lanes` | Refresh hash-lane index |
| `pipeline_process` | 5 | (reserved for workflow hub) | |
| `brain_sync` | 7 | `diagnostic.pulse` (steady-mode) | Background MORSR pulses |
| `wallet_check` | 11 | (existing) | |
| `identity_audit` | 13 | (existing) | |
| `report_generate` | 17 | `diagnostic.spectral.report` | Periodic spectral-health snapshot |
| `data_aggregate` | 19 | `memory.prune_stale` | Slow cleanup of unreferenced morphons |
| `expert_review` | 23 | (existing) | |
| `compose_round` | 29 | `cache.evict_cold` | LRU eviction sweep |
| `governance_check` | 31 | `receipt.verify_chain` | Slow integrity audit |
| `knowledge_sync` | 37 | `conservation.ledger_compact` | NSL ledger windowing |
| `tmn2_pulse` | (TMN2 daemon) | `routing.ingest_orientation` | Daemon publishes E8 orientation; routing consumes |

Channels with no port binding (yet) remain free for later assignment. The daemon's prime-period scheduling means no two bound channels fire simultaneously, so port-driven background work is naturally throttled.

## 4. Local-control schema

A Morphon opts into local-control triggers by including a `triggers` key in its payload (or a separate sidecar payload, when the morphon payload shape can't be touched).

Schema:

```python
{
    "triggers": {
        "on_state_change": [
            {"port": "symbolic", "operation": "derive", "args": {}},
        ],
        "on_evidence_update": [
            {"port": "constraints", "operation": "admit", "args": {}},
        ],
        "on_transition": {
            "VALIDATING": [{"port": "embed", "operation": "decompose"}],
            "EXECUTING": [{"port": "diagnostic", "operation": "pulse"}],
        },
    }
}
```

When the controller mediates an operation that produces one of these events on the Morphon, it consults the morphon's `triggers` config and dispatches the configured port operations. The configured operations are class-D triggers.

**Constraints:**
- Triggers can only target ports already registered. Unregistered ports → ignored with a `GATE` receipt logged.
- Trigger dispatch is synchronous within a single morphon's mediation; cross-morphon trigger chaining is a future extension.
- Trigger failures don't abort the parent mediation; they emit `DEATH` receipts.

## 5. Local-control vs daemon-periodic — when to use which

| Situation | Choose |
|---|---|
| Every morphon of this type should do X on transition | Local-control |
| The system should do X every N ticks regardless of morphons | Daemon-periodic |
| X is a one-off response to a specific event | Event-driven (B) |
| X is invoked by user code | User-driven (A) |

In practice, a port often supports operations across all four classes. The Protocol contract for the port should document which classes each method supports, and consumers pick the right invocation path.

## 6. Implementation requirements

The trigger model is fully usable in v1 with these additions to the codebase, none of which exist yet:

### 6.1 Port-operation Protocol metadata

Each Protocol in [controller.py](../../src/cmplx/morphon/controller.py) should declare, per method, the trigger classes it supports. Initial proposal: a `__trigger_classes__: dict[str, set[str]]` attribute on each Protocol class, mapping method name → set of valid trigger classes (subset of `{"A", "B", "C", "D"}`).

### 6.2 Daemon trigger registration

[src/daemon/](../../src/daemon/) needs a `register_channel_trigger(channel_name, port, operation, period_multiplier=1)` API. When the channel fires, the daemon calls `MorphonController.get(port).<operation>()`. Misconfigured triggers raise at registration, not at tick time.

### 6.3 Controller mediation extensions

`MorphonController.admit_and_store` already mediates the admit→address→geometry→store sequence (class B). Add a per-morphon trigger dispatcher: after every B-class step, consult morphon.payload.get("triggers") and dispatch any matching class-D operations.

### 6.4 Trigger-receipt grammar

Every trigger firing emits a receipt:
- Class A firing → `PROCESS` (current behavior)
- Class B firing → `CROSSING` (current behavior, but tag with trigger class)
- Class C firing → `POST` with `trigger_source: "daemon:<channel>"`
- Class D firing → `ASSIGN` with `trigger_source: "local:<event>"`

The receipt-grammar extension is a small addition to [src/cmplx/receipt/types.py](../../src/cmplx/receipt/types.py) — add `trigger_class` and `trigger_source` as optional payload conventions, not new receipt types.

## 7. Slot-unblocking effect

With this map in place:

- **Slot 15 (AGRM)** — F-6 can be designed: AGRM exposes `solve` (class A) and `ingest_orientation` (class C, bound to `tmn2_pulse`). The Protocol declares both classes; the implementation accepts orientation data via the registered class-C trigger.
- **Slot 22 (lambda)** — F-7 can be designed: lambda exposes `evaluate` (class A), `evaluate_on_state_change` (class D, opt-in per morphon). Lambda gets added to `KNOWN_PORTS`. Crystal port follows the same pattern.
- **Slot 26 (atlas-mandelbrot)** + **Slot 27 (julia-c-assignment)** — both have natural class-B firing inside Morphon forge (julia c-assignment) and class-C firing on a `boundary_recompute` daemon channel.
- **Slot 28 (dispatch-tree IR)** — the dispatch tree IS the orchestrator that resolves step-by-step what classes of triggers fire when. The trigger map gives it a vocabulary to use.

## 8. Open questions

1. **Class precedence on conflict.** If a morphon has a class-D trigger for `constraints.admit` and the controller would naturally fire `constraints.admit` as class B during admit_and_store, do both fire, or does D override B? Proposed default: B fires (system safety), D fires after as a refinement.
2. **Async / sync.** Daemon-periodic operations run on the daemon's thread. Should class-D triggers also run synchronously inside the controller mediation, or post to a queue? Proposed default: synchronous for now; async is a v2 concern.
3. **Crystal port semantics.** The crystal-fabric (Slot 14) is a *composite* port — it owns sub-fabrics across 10 layers. Should `crystal.tier_promote` fire one class-C tick per layer (10 daemon channels) or one tick that promotes all layers (one channel)? Proposed default: one tick per layer, so each layer can have its own cadence.

## 9. v1 status

This document is the contract. No code changes are made by this sub-frame — the trigger model is paper-only until it's ready to be applied. The next builds (F-6, F-7, crystal port, atlas, dispatch-tree IR) consume this document as part of their design phase.

When any of those builds lands, it adds an explicit `trigger_class` declaration to its Protocol contract and (if class-C) requests a daemon channel via the binding table in §3. The first build to do this also lands the §6 implementation requirements as foundational infrastructure.

---

**End of port-trigger map v1. The slots that were waiting on this are now unblocked.**
