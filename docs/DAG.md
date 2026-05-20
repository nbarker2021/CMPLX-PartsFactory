# cmplx — Component DAG

Live map of which components are built, what ports they provide,
what ports they consume, and what static cross-imports exist.

## Conventions

- **provides** — the runtime port the component registers on `MorphonController`.
- **consumes (port)** — runtime port the component requests through `MorphonController`.
- **consumes (import)** — static Python-level import for shared types/constants.
- A component can use only ports of components further "up" the DAG; the
  morphon controller mediates everything.

## Current graph (after morphon + mdhg(+promoted) + geometry + mmdb + aletheia + chirp + alena + carrier framework + pixel + crystal + snap)

```
                       ┌──────────────────────────────────┐
                       │             morphon              │ 18 tests
                       │  exposes: Morphon, MorphonState, │
                       │     MorphonController, Receipt   │
                       │  consumes (ports):               │
                       │    addressing ✓  geometry ✓      │
                       │    memory ✓      constraints ✓   │
                       │    transport ✓   engine (TBD)    │
                       │    symbolic (TBD) routing (TBD)  │
                       └──────────────────────────────────┘
                              ▲   ▲   ▲   ▲   ▲   ▲
                              │   │   │   │   │   │
              ┌───────────────┘   │   │   │   │   └────────────────┐
              │                   │   │   │   │                    │
              │       ┌───────────┘   │   │   └────────────┐       │
              │       │               │   │                │       │
              │       │       ┌───────┘   └─────────┐      │       │
              │       │       │                     │      │       │
              ▼       ▼       ▼                     ▼      ▼       ▼
        ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐ ┌──────────┐
        │addressing │geometry│ │memory │ │ constraints  │ │transport │
        │  mdhg   │ │ e8+leech│ │  mmdb │ │  aletheia    │ │  chirp   │
        │ 12 tests│ │13 tests│ │11 tests│ │  12 tests    │ │ 18 tests │
        │ stdlib  │ │ stdlib │ │ stdlib │ │  stdlib      │ │ stdlib + │
        │ only    │ │ only   │ │ +sqlite3│ │  only        │ │ imports  │
        └────────┘ └────────┘ └────────┘ └──────────────┘ └─────┬────┘
              │                                                  │
              │           static cross-imports                   │
              └──────────────────────────────────────────────────┘
                    chirp.carriers imports
                    Channel, Triad from mdhg
                    (shared structural types,
                     not a runtime port)
              chirp.chirp imports LEECH_PREFIX from geometry.leech
                    (shared constant)
              chirp.chirp consumes addressing+geometry ports lazily
                    (only invoked when projections aren't pre-cached)
```

## Component status

| Component | State | Provides | Consumes (port) | Consumes (import) | Tests |
|---|---|---|---|---|---:|
| `cmplx.morphon` | ✓ | (unit type) | addressing, geometry, memory, constraints, engine, transport, symbolic, routing | — | 18 |
| `cmplx.addressing.mdhg` | ✓ | `addressing` | — | — | 12 |
| `cmplx.geometry` | ✓ | `geometry` | — | — | 13 |
| `cmplx.memory.mmdb` | ✓ | `memory` | — | — | 11 |
| `cmplx.constraints.aletheia` | ✓ | `constraints` | — | — | 12 |
| `cmplx.transport.carrier` | ✓ | (abstract; consumed via registry) | — | — | (part of carrier suite) |
| `cmplx.transport.chirp` (incl. `DTMFCarrier`) | ✓ | `transport` (as Carrier) | addressing, geometry (lazy) | `cmplx.addressing.mdhg.Channel/Triad`, `cmplx.geometry.leech.LEECH_PREFIX`, `cmplx.transport.carrier.Carrier/CarrierFrame` | 18 |
| `cmplx.transport.pixel` (`PixelCarrier`) | ✓ | `transport` (as Carrier) | addressing, geometry (lazy) | `cmplx.geometry.leech.LEECH_PREFIX`, `cmplx.transport.carrier.Carrier/CarrierFrame` | (covered by carrier suite) |
| `cmplx.geometry.alena` | ✓ | — (static-import primitive layer) | — | `cmplx.geometry.e8` | 17 |
| Carrier suite tests (`test_carrier.py`) | ✓ | — | — | — | 15 |
| `cmplx.transport.video` (stub) | stub | `transport` (Carrier) | — | `cmplx.transport.carrier`, `cmplx.geometry.alena` (planned) | 0 |
| `cmplx.transport.numbers_station` (stub) | stub | `transport` (Carrier) | — | `cmplx.transport.carrier` | 0 |
| `cmplx.crystal` | ✓ | `crystal` | (optional) memory, addressing, geometry | `cmplx.geometry.alena.COUPLING/PHI` | 30 |
| `cmplx.snap` | ✓ | `snap` | — | stdlib only (hashlib, inspect, re) | 41 |
| `cmplx.addressing.mdhg` (promoted) | ✓ | `addressing` | — | — | 12 + 20 |
| `cmplx.symbolic.tarpit` | ✓ | `symbolic` | geometry, crystal, addressing (all optional) | `cmplx.geometry.alena` | 44 |
| `cmplx.speedlight` | ✓ | `cache` | memory, addressing (optional) | `cmplx.geometry.alena`, `cmplx.crystal.fabric` | 59 |
| `cmplx.morsr` | ✓ | `diagnostic` | conservation (NSL), geometry, cache (optional) | `cmplx.nsl`, `cmplx.geometry.alena` | 63 |
| `cmplx.nsl` | ✓ | `conservation` | memory, geometry (optional) | `cmplx.geometry.alena.COUPLING` | 51 |
| `cmplx.receipt` | ✓ | `receipt` | memory, conservation, addressing (optional) | stdlib only | 48 |
| `cmplx.engine.cqe` | ✓ | `engine` | conservation, receipt, diagnostic, crystal, snap, cache, addressing, memory, constraints | `cmplx.morphon`, `cmplx.nsl`, `cmplx.receipt`, `cmplx.morsr` | 72 |
| `cmplx.routing.agrm` | — | `routing` | addressing, geometry, memory, snap (lens bank) | (TBD) | — |
| `cmplx.worlds.forge` (planned, from GVS) | — | `worlds` | geometry (alena), transport, crystal | `cmplx.geometry.alena.*` | — |

**Total tests passing: 544/544.**

## Ports landed across the build

- **`crystal`** — `CrystalRegistry` (data crystals + tool crystals + 10-level fabric).
- **`snap`** — `SNAPEngine` (labeler + lenses + Gate369 + ledger).
- **`symbolic`** — `TarpitEcology` (Morphonic Ribbon Ecology: grains/dust/walls/mirror).
- **`cache`** — `SpeedLightProvider` (idempotent compute + E8 proximity + equivalence learning).
- **`conservation`** — `NSLProvider` (3-sector ΔΦ + Leech-triad embedding + gate modes).
- **`diagnostic`** — `MORSRProvider` (pulse + traversal + sonar).
- **`receipt`** — `ReceiptProvider` (Merkle-chained ops + DAG edges).
- **`engine`** — `CQEProvider` (the orchestrator that wires everything).

`KNOWN_PORTS` is now: `{addressing, geometry, memory, constraints, engine, transport, symbolic, routing, crystal, snap, cache, conservation, diagnostic, receipt}`.

## The bind-everything pipeline

The user-described "giraffe pipeline" now has all its components in
the live build (some still need their final glue layer in `cqe`):

```
content
   │
   ▼
SNAPLabeler.label(item) → SNAPLabel (5 dimensions)
   │
   ▼
LensBank.best_lens(state).evaluate() → pass | refine
   │
   ▼ (if pass)
Gate369Engine.process(bodies, predicates)
   ├── triad: top-3 by lens score
   ├── hexad: pairwise polarity invariants
   └── ennead: 9-body containment package → crystallized iff c>0.7
   │
   ▼
SNAPLedger.append("crystallize", ...) ── auditable receipt
   │
   ▼
ALENA.project_to_channels(e8) → rail-snapped vector
   │
   ▼
MDHGAddress.from_e8(coords) + assign_address(...) → mdhg_address
   │
   ▼
CrystalRegistry.add_node(crystal_id, content,
                         e8_coords=..., labels=label.all_labels)
   → E8Node with snap_labels + mdhg_address + e8_coords stored together
   → Crystal.receipt_chain extended (sha256 chain)
   │
   ▼
PixelCarrier.encode(crystal_node) → RGB block (current carrier)
VideoCarrier / NumbersStation / future SNAP-driven renderer (planned)
   │
   ▼
MDHGMultiScale.admit_all_layers(vec24) ── SpeedLight cache analog
   fast: per-tick worldline
   med:  keyframes / drift surfaces
   slow: archive / canonical
```

Every arrow leaves a receipt — `SNAPLedger` (semantic), `Crystal.receipt_chain` (binding), `MDHGMultiScale` slot drift events (admission). The whole spine is auditable.

## Carrier framework

The `transport` port is now backed by an explicit abstraction: any
`Carrier` (DTMF, Pixel, Video, NumbersStation, ...) implements
`encode(morphon) → CarrierFrame` and `decode(frame) → dict`. Multiple
carriers coexist via `CarrierRegistry`; identity fields (channel, E8
sign bits, leech first byte) round-trip through every carrier.

```
                        morphon
                           │
                           ▼
                  ┌────────────────┐
                  │   transport    │  ← port
                  │ CarrierRegistry│
                  └────────┬───────┘
              ┌────────────┼────────────┬─────────────┐
              ▼            ▼            ▼             ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────────┐
        │  dtmf   │  │  pixel  │  │  video  │  │  numbers   │
        │ (chirp) │  │ (E8→RGB)│  │ (stub)  │  │  station   │
        └─────────┘  └─────────┘  └─────────┘  │  (stub)    │
                                                └────────────┘
```

`cmplx.geometry.alena` sits **below** transport as a static-import
primitive (no port) — pixel and future video carriers consume its
`project_to_channels`, `r_theta_snap`, etc. directly.

## What's been demonstrated end-to-end

The `admit_and_store` flow exercises 4 components in sequence:

```
morphon → constraints (Aletheia) → addressing (MDHG) → geometry → memory (MMDB)
```

`encode_frame` exercises 3 components:

```
morphon → addressing (MDHG) → geometry → transport (Chirp.encode)
                                            ↓
                                          ChirpFrame
                                          (channel + carrier + 8b + 8b + id)
```

Both flows are real (no fakes) in their tests.

## What this build pass exposed

### From aletheia

- **Strict mode is a real value-add.** The compound `admit_and_store`
  could be upgraded to use `aletheia.admit_strict()` instead of the
  current `(ok, reason)` pattern — would simplify the error path.
  Held back because the current controller pattern is consistent
  across all ports; future refactor.
- **Default law set is opinionated.** `PayloadIsMappingLaw`,
  `PayloadNotEmptyLaw`, `StateTransitionWellFormedLaw`,
  `PayloadSizeLimitLaw(1MB)`. Easy to override via `Aletheia(laws=[])`
  or `Aletheia(laws=[custom_set])`.
- **Law-raising-exception handled gracefully** — buggy laws don't
  crash admission, they refuse with the exception text. Test caught
  this case.
- **Future need**: when Golay correction is added, it will consume
  the `geometry` port to find the nearest valid Leech codeword.
  Pattern: **optional consume** — check `MorphonController.has("geometry")`
  before attempting correction; degrade if absent.

### From chirp

- **First multi-port consumer** — chirp uses BOTH `addressing` and
  `geometry`. The lazy pattern (skip the port if the morphon already
  has the cached projection) is reusable for any future
  multi-port consumer.
- **First static cross-import surfaced**: `Channel` and `Triad` from
  mdhg are shared structural types, not runtime ops. They live in
  mdhg and chirp's `carriers.py` imports them. Same with
  `LEECH_PREFIX` from geometry.leech. **The DAG must now distinguish
  port-based runtime dependencies from import-time shared-type
  dependencies.**
- **Frame validation matters**: `ChirpFrame.__post_init__` rejects
  out-of-range channel / word values. Test caught a typo'd value
  before it could propagate.
- **Decoded form is partial by design** — a chirp transmits identity
  + a few salient bits, not the whole payload. To recover the full
  morphon, the receiver looks it up in MMDB by id. This **exposes
  the design point that chirp + mmdb are paired**: chirp without
  shared memory loses payloads on the wire.

## What's still TBD on morphon's controller

3 ports without providers yet:

- `engine` — for the evolve compound op. Likely consumer needs:
  memory, constraints, symbolic.
- `symbolic` — for derive-by-MLambda. Likely consumer needs: geometry
  (E6 sub-lattice), engine.
- `routing` — for AGRM graph navigation. Likely consumer needs:
  addressing, geometry, memory.

Each will pull in its own predicted ports plus surface new ones.

## How the DAG grows

Two kinds of edges to track per component:

1. **Runtime port edges** — managed by `MorphonController`. New ports
   added to `KNOWN_PORTS`; Protocols defined in `controller.py`.
2. **Static import edges** — managed by Python's import system. These
   are shared types and constants; not mediated. Tracked here in the
   "Consumes (import)" column for visibility.

The fact that we have both kinds of edges, and they're different in
kind, is itself a finding from this build: **the manifold-in-manifold
pattern has two layers — the structural (shared types) and the
operational (runtime ports)**. Both need to be visible to keep the
DAG honest.
