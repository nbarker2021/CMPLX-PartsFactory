# alena — Interface

**ALENA** (Atomic Lattice E-Nearest-root Analyzer) is the **projection
primitive layer**. It provides the geometric operations that every
carrier in the unified system relies on: snap a vector to its nearest
quantized form, reflect across a symmetry boundary, midpoint with
error correction, project E8 curvature.

ALENA does not produce morphons and does not encode them. It is the
**math layer** other components build on. When `cmplx.transport`
encodes a morphon as audio or pixels, the snap/flip/midpoint
operations come from here.

## Why this is its own package

The historical CQE-GVS bundled ALENAOps inside the E8 module. We're
lifting it out because it serves *multiple* downstream components:

- `cmplx.transport.chirp` carriers use `r_theta_snap` for channel
  projection and `midpoint_ecc` for noise tolerance.
- `cmplx.routing.agrm` will use `weyl_flip` for graph-edge parity
  decisions.
- `cmplx.engine.cqe` will use `project_curvature` for transition
  budgeting (curvature = state-distance cost).
- Any future carrier — image, MIDI, video, voice — uses the same
  primitives.

Having one place these live keeps the math single-source-of-truth.

## What this package exposes

| Symbol | Purpose |
|---|---|
| `ALENA(e8_lattice=None)` | The operator object. Holds reference to the E8 lattice (defaults to a fresh one). |
| `ALENA.r_theta_snap(vector)` | Snap a vector to its nearest Fibonacci-radius point (golden-spiral lattice). |
| `ALENA.weyl_flip(vector)` | Reflect across the nearest Weyl chamber boundary. |
| `ALENA.midpoint_ecc(v1, v2)` | Midpoint with E8-lattice error correction. |
| `ALENA.project_curvature(vector, face_angle=0.0)` | E8 face rotation + stereographic projection → 7-D image + curvature in 8th coord. |
| `ALENA.project_to_channels(vector, channels=(3,6,9))` | Snap to specified DR channels — the projection-encoder primitive. |
| Module-level helpers: | |
| `fibonacci_radii(n_low=-10, n_high=10)` | Sequence of golden-spiral radii: `[φ^n × COUPLING for n in range]`. |
| `COUPLING = 0.03` | The system-wide coupling constant (= 1/F9 ≈ ln(φ)/16). |
| `PHI` | Golden ratio. |

## Mathematical core

### `r_theta_snap(vector)` — Fibonacci-radius polar snap

```
r = ||vector||
nearest_r = argmin |fib_r - r|  over fibonacci_radii()
return (vector / r) × nearest_r        # preserve direction, snap magnitude
```

This is the **projection-encoder primitive** you asked about — a
deterministic snap to a golden-spiral lattice point. Used to bin a
vector into one of finitely many "channels" while preserving its
angular content. The user's earlier ALENA work used this with
hardcoded `projection_channels = [3, 6, 9]`, which is the
3/6/9-rail variant exposed as `project_to_channels()`.

### `weyl_flip(vector)` — chamber-boundary reflection

```
chamber = e8.find_weyl_chamber(vector)   # 1 of 48
normal  = e8.weyl_chambers[chamber]
flipped = vector - 2 × ⟨vector, normal⟩ × normal
return e8.project_to_manifold(flipped)
```

Standard hyperplane reflection. Used for parity alignment — any state
on the "wrong side" of a Weyl chamber boundary gets mirrored back.

### `midpoint_ecc(v1, v2)` — error-correcting midpoint

```
mid = (v1 + v2) / 2
return e8.project_to_lattice(mid)        # snap to actual lattice point
```

The midpoint is unlikely to land on an E8 lattice point exactly. We
snap to the nearest actual root, which is the closest valid codeword.
This is the Leech/Golay-style ECC pattern at the E8 scale.

### `project_curvature(vector, face_angle)` — curvature carrier

```
1. rotated = e8.face_rotation(vector, face_angle)
2. # Stereographic projection from north pole
   if rotated[7] ≈ 1: projected = rotated[:7]          # singularity guard
   else:               projected = rotated[:7] / (1 - rotated[7])
3. # Embed back with curvature in 8th coord
   curved = [*projected, ||projected|| × COUPLING]
4. return e8.project_to_manifold(curved)
```

This is how the GVS encodes spacetime curvature for video rendering —
the 8th coordinate carries the curvature measure. Same operation can
encode any "weighted projection" where one axis is reserved for
metadata.

## Invariants

1. **Deterministic**: same input → same output, every time.
2. **Pure**: no side effects on the vector.
3. **No external dependencies for the core**: depends only on
   `cmplx.geometry.e8` for the lattice + roots + chamber math.
4. **Operates on numpy arrays** (8-tuples, internally). The carriers
   that consume ALENA convert to/from morphons.

## What this package does NOT do

- Doesn't know about morphons. Operates on raw 8-tuples.
- Doesn't encode anything as a carrier signal. That's `cmplx.transport`.
- Doesn't store anything. That's `cmplx.memory.mmdb`.

## How carriers use ALENA

A pattern from the future PixelCarrier:

```python
from cmplx.geometry.alena import ALENA

class PixelCarrier:
    def __init__(self):
        self.alena = ALENA()

    def encode_e8_to_pixel_block(self, e8_coords):
        # Snap to 3/6/9-channel grid for stable RGB encoding
        snapped = self.alena.project_to_channels(e8_coords, channels=(3, 6, 9))
        # CRT rails: R = snapped[4] % 3, G = snapped[5] % 6, B = snapped[6] % 9
        ...
```

This is identical in shape to how the audio carrier uses ALENA for
DTMF channel selection — different carrier, same projection
mathematics.
