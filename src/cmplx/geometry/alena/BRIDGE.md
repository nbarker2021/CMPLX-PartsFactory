# alena — Bridge

## Port provided

**None.** ALENA does not register with `MorphonController` directly.
It is a *primitive layer*, used by other components via static
import.

## Ports consumed

**None.** Depends only on `cmplx.geometry.e8` (sibling package, also
static import).

## Static imports (the cross-component edges)

| Imports from | What | Why |
|---|---|---|
| `cmplx.geometry.e8` | `E8` namespace, `e8_roots`, `nearest_root`, `DIMENSION` | The lattice + root system the snap/flip/midpoint operations work over. |

| Imported by (current + planned) | What they use |
|---|---|
| `cmplx.transport.chirp.carriers` | `r_theta_snap`, `project_to_channels`, `midpoint_ecc` |
| `cmplx.routing.agrm` (planned) | `weyl_flip` for chamber-parity routing decisions |
| `cmplx.engine.cqe` (planned) | `project_curvature` for transition-cost calculation |
| `cmplx.worlds.forge` (planned, from GVS) | All four primary ops |

## Why this is a static-import-only package

The pattern matches `mdhg.Channel`/`Triad` enums: shared *types and
operations* that aren't runtime services. ALENA is pure math — it
doesn't change state, doesn't talk to other components dynamically,
doesn't need configuration. Treating it as a port would add ceremony
without benefit.

The DAG has two edge kinds for exactly this reason:
1. **Runtime port edges** — components that need dynamic dispatch
   (memory could be SQLite or Postgres; constraints could be Aletheia
   or something else).
2. **Static import edges** — components that are inherent (E8 IS the
   lattice; ALENA IS the projection math; the chirp DTMF carriers ARE
   the 9-channel grid).

ALENA is the largest piece of the second kind so far — much of the
mathematical content of the system lives here.

## Test fixtures

Tests verify:

- `r_theta_snap` snaps direction-preserving (output direction matches
  input direction).
- `r_theta_snap` snaps magnitude to one of the Fibonacci radii.
- `weyl_flip` reflects across a Weyl chamber boundary (output is on
  the other side of the chamber).
- `midpoint_ecc(v, v)` returns the nearest lattice point to `v`.
- `midpoint_ecc(v1, v2)` returns an E8 root.
- `project_curvature(v, 0)` is the identity in the angular sense.
- `project_curvature(v, θ)` produces an 8-D output with the 8th
  coordinate carrying the projected magnitude × COUPLING.
- `project_to_channels(v, (3, 6, 9))` constrains output components
  to be commensurate with those channel rails.
- Deterministic: same input always gives same output.
- Operations don't mutate inputs.
