# nsl — Bridge

## Port provided

`conservation` — `NSLProvider` is the canonical provider. Any
component that needs to (a) compute ΔΦ for a state change, (b)
report it for cumulative auditing, or (c) make a gate decision goes
through this port.

## Ports consumed (optional)

- `memory` — durable persistence for `NSLLedger`. Without it, the
  ledger is in-process only.
- `geometry` — for Leech-lattice operations on the 24-D triad-as-Leech
  embedding. Currently uses local stdlib.

## Static imports

| Imports from | What | Why |
|---|---|---|
| `cmplx.geometry.alena` | `COUPLING` | Universal coupling constant. Verified to match `cmplx.nsl.COUPLING = 0.030076`. |

The NSL package is intentionally tiny and dependency-free beyond
ALENA so it can be imported by every other component without cycles.

## What other components import FROM nsl

| Importer (current + planned) | What |
|---|---|
| `cmplx.constraints.aletheia` (next pass) | `NSLSectors`, `delta_phi` for `NSLConservationLaw` law. |
| `cmplx.snap.SNAPLedger` (planned wiring) | `NSLSectors` attached to every transaction. |
| `cmplx.crystal.types.Crystal` (planned wiring) | `receipt_chain.extend(sectors)` replaces the tag-only form. |
| `cmplx.symbolic.tarpit.WallEmitter` (planned wiring) | `OutputWall.residual_digits` computed from NSL sectors. |
| `cmplx.morsr` (this pass) | Acceptance gate: pulse candidate is accepted iff `NSLSectors(...).total ≤ -ε`. |
| `cmplx.engine.cqe` (planned) | The whole executor delegates conservation to NSL. |

## Cross-component semantics

NSL is the **conservation spine**. The pattern is:

```
component
   │  v_before, v_after  (state vectors, 8-D or 24-D)
   ▼
nsl.delta_phi(v_before, v_after) → ΔΦ (scalar)
   │
   ▼ (if 3-sector breakdown needed)
NSLTriads.score(v_after - v_before) → NSLSectors(dN, dI, dL)
   │
   ▼
NSLProvider.gate(sectors, mode=GOVERN, budget=0)
   │
   ├── accepted? → caller proceeds; NSLLedger.append(receipt)
   │
   └── rejected? → caller either:
            - blocks (mode=GOVERN)
            - amortizes against budget (mode=AMORTIZE)
            - signals (mode=SIGNAL) and proceeds
   │
   ▼
NSLLedger.cumulative ≤ 0  ← cumulative conservation invariant
```

The Leech structure shows up because the 3 sector triads (8-D each)
together form a 24-D vector that lives on the Leech lattice. When the
Niemeier package lands, NSL triads can be type-checked as Leech
points; for now they're just (8,8,8) tuples.
