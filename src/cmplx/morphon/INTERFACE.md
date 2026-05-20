# morphon — Interface

The **morphon** is the system's atomic-and-outer-bound primitive.
Every operation in the unified system folds back to it. A morphon
is the unit at which the substrate (E8 / Leech / Niemeier),
addressing (MDHG digital-root), storage (MMDB), transport (chirp),
admission (Aletheia), and evolution (CQE/MORSR) all agree on what
they're operating on.

This document is the public interface of the `cmplx.morphon`
package. It precedes implementation: anything implementing here
must conform to this contract, not the other way around.

## Conceptual shape

A morphon is a labeled, geometrically-situated unit of meaning
that carries three things internally:

1. **A payload** — the content it represents.
2. **A coefficient table** — one row per geometry in which the
   morphon participates, with the morphon's position in that
   geometry. At minimum this includes its E8 vector, Leech point,
   and digital-root channel.
3. **A receipt chain** — the history of operations that produced
   this morphon's current state.

The same morphon is simultaneously a vector in E8, a point in the
Leech lattice, an entry in MMDB, a channel under MDHG, and a chord
in the chirp transport. These are not separate objects; they are
projections of one object's coefficient table.

## The two classes this package exposes

### `Morphon`

The primary type. Constructed by user code or by a `MorphonForge`,
then evolved through the lifecycle states defined in `MorphonState`.

```python
from cmplx.morphon import Morphon, MorphonState

m = Morphon.forge(payload={"text": "hello"})
assert m.state is MorphonState.CREATED
```

Fields on the public surface:

| Field | Type | Meaning |
|---|---|---|
| `id` | `str` | Unique identity (UUID by default) |
| `created_at` | `datetime` | Forge time |
| `payload` | `Mapping[str, Any]` | The content this morphon carries |
| `state` | `MorphonState` | Lifecycle state |
| `e8_coordinates` | `tuple[float, ...] \| None` | 8-D E8 projection |
| `leech_point` | `str \| None` | 24-D Leech projection (encoded) |
| `dr_channel` | `int \| None` | Digital-root channel 1-9 |
| `parent` | `str \| None` | ID of a parent morphon (if forged from one) |
| `children` | `tuple[str, ...]` | IDs of forged children |
| `receipts` | `tuple[Receipt, ...]` | Chain of receipts |

Fields and methods carried in from the composed historical
variants (E8/Leech/Niemeier coordinates, Mandelbrot context,
SpeedLight receipts, conservation constraints) are accessible
but considered *extended surface* — see `EXTENDED.md` (not yet
written) for those.

### `MorphonState`

Enum of lifecycle states. The canonical flow:

```
CREATED → VALIDATING → POLICY_CHECK → ROUTING → QUEUED
       → EXECUTING → CONSOLIDATING → COMPLETED
                                  → FAILED
                                  → CANCELLED
```

Plus two side-states for the executing branch:

- `AWAITING_TOOL` — paused, waiting for an external tool to return
- `AWAITING_DATA` — paused, waiting for a memory query to return

## The operations this package supports

| Operation | Signature | What it does |
|---|---|---|
| `Morphon.forge(payload, **kwargs)` | classmethod | Construct a new morphon at state `CREATED`. |
| `morphon.transition_to(new_state)` | method | Advance the state machine. Validates the transition is legal. |
| `morphon.attach_receipt(receipt)` | method | Append to the receipt chain (immutable extension). |
| `morphon.with_payload(payload)` | method | Return a new morphon with the same id but a new payload. Used by evolution. |
| `morphon.project_to_e8()` | method | Compute / return the E8 coordinate. Requires a geometry bridge. |
| `morphon.project_to_channel()` | method | Compute / return the DR channel. Requires an addressing bridge. |
| `morphon.serialize()` | method | Produce a JSON-safe dict representation. |
| `Morphon.deserialize(data)` | classmethod | Round-trip from `serialize()` output. |

## Invariants

The package is responsible for preserving these:

1. **Identity is stable**: a morphon's `id` never changes after
   creation. `with_payload()` returns a NEW morphon with a fresh
   id and a parent pointer back.
2. **State transitions are monotone**: certain transitions are
   illegal (e.g., `COMPLETED → CREATED`). The state machine
   refuses them.
3. **Receipts are append-only**: `attach_receipt()` never
   replaces existing receipts.
4. **Projections are pure**: `project_to_e8()` etc. don't mutate
   the morphon; they return values.
5. **Children carry parent**: any morphon born inside another's
   evolution records its parent id.

## What this package does NOT do

Deliberately left to other components:

- **Persistence** — storing a morphon goes through `cmplx.memory`
  (MMDB). The morphon doesn't know how to save itself.
- **Addressing** — computing the actual DR channel from the
  payload goes through `cmplx.addressing` (MDHG). The morphon
  holds the cached channel but doesn't compute it.
- **Admission** — checking that a morphon satisfies conservation
  laws goes through `cmplx.constraints` (Aletheia).
- **Evolution** — advancing a morphon's payload via CQE
  transformations is in `cmplx.engine`.
- **Transport** — encoding the morphon as a chirp tone is in
  `cmplx.transport`.

The morphon package is **structural**: it defines what a morphon
IS and provides the verbs for moving it through the lifecycle.
The verbs that change its substance live in other packages.

## How other components talk to this one

Through the controller defined in `BRIDGE.md`. Other packages do
not import from `cmplx.morphon` directly except for the two
exposed types (`Morphon`, `MorphonState`); all *operations* are
mediated.
