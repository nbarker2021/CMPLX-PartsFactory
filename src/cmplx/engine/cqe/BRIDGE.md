# engine.cqe — Bridge

## Port provided

`engine` — `CQEProvider` is the canonical provider. Components that
need the full orchestrated CQE pipeline call through this port.

## Ports consumed

CQE is the **conductor**, so it consumes more ports than any other
package:

| Port | What CQE does with it |
|---|---|
| `conservation` (NSL) | ΔΦ ≤ 0 enforcement; sector breakdown on every operation |
| `receipt` | Mints a Receipt for every pipeline stage |
| `diagnostic` (MORSR) | Optional Phase-3 pulse exploration in `solve_problem` |
| `crystal` (planned) | When CQE produces stable atoms, mints them as Crystal nodes |
| `snap` (planned) | Phase-2 channel extraction can use SNAPLabel.all_labels |
| `cache` (SpeedLight, planned) | Memoize repeat `solve_problem` calls on same problem id |
| `addressing` (MDHG, planned) | Map CQE atom → MDHGAddress for routing |
| `memory` (MMDB, planned) | Durable Receipt + atom persistence |
| `constraints` (Aletheia) | Coexists with CQEGovernance; both can validate |

## Static imports

| Imports from | What | Why |
|---|---|---|
| `cmplx.morphon` | `Morphon` | Base atom; CQEAtom IS a Morphon with CQE fields. |
| `cmplx.nsl` | `NSLProvider`, `NSLSectors`, `GateMode` | Conservation scalar + gate. |
| `cmplx.receipt` | `ReceiptProvider`, `ReceiptType` | Pipeline-stage provenance. |
| `cmplx.morsr` | `Overlay` (inside `solve_problem` only) | MORSR seed construction. |

## What other components import FROM engine.cqe

| Importer (planned) | What |
|---|---|
| Apps / services | `CQEProvider.process_text(...)` and `solve_problem(...)` as the main entry. |
| `cmplx.worlds.forge` (planned) | `CQERunner` to drive world-state evolution cycles. |
| Test harnesses | `CQEAtom.forge(payload)` to create canonical test atoms. |

## Cross-component semantics

CQE is where **all the pieces come together**. The pipeline composes:

```
input
   │
   ├── domain_adapter.adapt(...) ────────────── (CQE-native)
   │                                            │ 8-D E8 vector
   │                                            ▼
   ├── e8_embed (or DomainAdapter.embed_text)
   │
   ├── mandelbrot.analyze_string ────────────── (CQE-native)
   │   → behavior: BOUNDED / *_ESCAPE
   │
   ├── toroidal.generate_toroidal_shell ─────── (CQE-native)
   │   → patterns: poloidal/toroidal/meridional/helical
   │
   ├── objective.evaluate ───────────────────── (CQE-native)
   │   → phi_total + parity/chamber/separation/kissing
   │   ↓ delegates ΔΦ sectors to cmplx.nsl
   │
   ├── (optional) morsr.pulse ──────────────── ← consumes `diagnostic` port
   │   → optimized vector
   │
   ├── governance.validate ──────────────────── (CQE-native, policy layer)
   │   ↓ consults cmplx.nsl for ΔΦ ≤ 0
   │
   ├── banding.compute_v_total → band_for ──── (CQE-native)
   │   → BREAKTHROUGH / PEER_READY / EXPLORATORY
   │
   └── receipts.mint(...) for every stage ───── ← consumes `receipt` port
       chain index → atom_id → operation → delta_phi → payload
```

The Coexistence Pattern (per user direction): `CQEGovernance` and
`cmplx.constraints.aletheia` are both valid governance entry points.
- Aletheia: per-law fine-grained admission gates (one law, one check)
- CQEGovernance: policy-level coarse-grained enforcement (named
  policies that select constraint subsets + enforcement rules)

A caller can use either or both. Receipts from both flow into the
same `receipt` port chain.

The CQEAtom-Morphon identity (per user direction): CQE was the
pre-CMPLX identity tag of every system. CQEAtoms ARE Morphons; the
extra fields (quad_encoding, parity_channels, sacred_frequency,
digital_root, fractal_coordinate) are populated on the Morphon
directly by `CQEAtom.forge()` or `CQEAtom(morphon)`.
