# morsr — Bridge

## Port provided

`diagnostic` — `MORSRProvider` is the canonical provider. Components
that need recursive diagnostic scans, geometric exploration, or
240-direction sonar coverage go through this port.

## Ports consumed

- `conservation` (required) — NSL provider for acceptance gating.
  Every pulse candidate is scored as `NSLSectors` and gated by the
  chosen `GateMode`. Without NSL registered, MORSR uses a stub
  acceptance (`is_conserved` on the raw position delta) as a fallback,
  but the canonical use registers NSL first.

- `geometry` (optional) — for Weyl-chamber-aware traversal in
  `CompleteTraversal(strategy="chamber_guided")`. Without it, falls
  back to sequential / distance-ordered traversal.

- `cache` (optional) — for memoizing pulse handshakes by
  `(overlay_id, operator, theta)` so the same pulse never re-executes.
  Without it, every pulse computes fresh.

- `memory` (optional) — for durable handshake log persistence.

## Static imports

| Imports from | What | Why |
|---|---|---|
| `cmplx.nsl` | `NSLSectors`, `GateMode`, `delta_phi`, `potential`, `enforce_conservation` | Acceptance metric & gate. |
| `cmplx.geometry.alena` | `COUPLING`, `PHI` | Universal constants. |

The MORSR engine is intentionally stdlib + NSL + ALENA only. Heavier
integrations (geometry/cache/memory) plug in through ports.

## What other components import FROM morsr

| Importer (planned) | What |
|---|---|
| `cmplx.engine.cqe` | `MORSREngine.pulse` to drive optimization cycles. |
| `cmplx.routing.agrm` | `SonarScan` for "what touches this node" route discovery. |
| `cmplx.snap.Gate369Engine` | `Handshake` log as input to the ennead packaging step. |
| `cmplx.worlds.forge` | `CompleteTraversal` for world-state-space exploration. |

## Cross-component semantics

MORSR is the **diagnostic spine**. The pattern:

```
caller chooses an entry point:
   │
   ├─→ pulse(seed)        — the recursive ripple/subripple cycle
   │                         (NSL-gated, shell-bounded, ΦΦ-tracked)
   │
   ├─→ traverse(seed, …)  — the 240-node complete-lattice variant
   │                         (every E8 root scored exactly once)
   │
   └─→ scan(coords, atoms)— the 240-direction sonar variant
                             (which roots touch / which don't)

each path emits:
   │
   ├─ Handshake log (audit trail; mirrors NSL receipt structure)
   ├─ Region        (the accepted state graph)
   └─ Metrics       (per-stage / per-strategy / per-shell breakdown)

acceptance is delegated to:
   │
   └─ cmplx.nsl.NSLProvider.gate(sectors, mode=GOVERN|AMORTIZE|SIGNAL)
```

The diagnostic claim: after a MORSR run, the handshake log + region
together capture **everything that touched the wave plus what
interfered with it**. That's the original "fully diagnostic via
sonar-like wave pulse examination" intent.
