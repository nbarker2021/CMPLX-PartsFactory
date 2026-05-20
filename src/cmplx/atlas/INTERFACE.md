# cmplx.atlas — Mandelbrot deployment boundary + Julia c-assignment

## Contract

The `atlas` port keeps the **Morphon-Mandelbrot Isomorphism** honest. Per the Atlas Microkernel Architecture: each Morphon IS a Julia set with fixed c; the operational deployment boundary IS a Mandelbrot set.

This port implements both halves of that isomorphism:

- **Julia c-assignment**: derives a deterministic complex c-value from each Morphon's identity components (`id`, `payload`, `parent`). The c-value is cached on the morphon's `fractal_coordinate` field.
- **Mandelbrot deployment boundary**: tests whether a Morphon's c-value lies inside the Mandelbrot set. Out-of-set morphons are rejected from deployment.

## Provider surface

`AtlasProvider` implements `cmplx.morphon.AtlasProvider`:

```python
class AtlasProvider:
    def julia_c(self, morphon: Morphon) -> complex: ...
    def in_boundary(self, c: complex, *, max_iter: int | None = None) -> bool: ...
    def admit_to_deployment(self, morphon: Morphon) -> tuple[bool, str]: ...
    def evict(self, morphon_id: str) -> bool: ...
    def deployment_stats(self) -> dict: ...
    def boundary_recompute(self) -> dict: ...
    def encode_to_etp(self, morphon: Morphon) -> str: ...
    def decode_from_etp(self, ledger: list[dict]) -> Morphon: ...
```

## How c-assignment works

`derive_c(morphon)` (in `julia.py`):

1. Serialize the morphon's identity as canonical JSON bytes.
2. SHA-256 the bytes.
3. Take the first 8 bytes, split into two unsigned 32-bit integers.
4. Map both into the Mandelbrot interest window `[-2, 0.5] × [-1.25, 1.25]` — biased toward the cardioid + main bulb so generic morphons land in-set with reasonable probability.
5. Return `complex(c_real, c_imag)`.

If the morphon already has `fractal_coordinate` set (e.g., the CQE atom flow populated it), `julia_c` returns the cached value unchanged.

## Deployment admission

`admit_to_deployment(morphon)` returns `(True, "")` on success or `(False, reason)` on rejection. Two rejection paths:

1. **Out of boundary**: c-value is outside the Mandelbrot set within the iteration budget.
2. **Capacity exhausted**: deployment has 196,560 morphons (the Leech lattice kissing number — the natural capacity from the formalization's Voronoi-cell organization).

On successful admission, the morphon is added to an internal deployed set. Re-admitting an already-deployed morphon is a no-op.

## Integration with `admit_and_store`

When the atlas port is registered, `MorphonController.admit_and_store` automatically calls `atlas.admit_to_deployment` after constraints admission and before addressing. The full flow becomes:

1. `constraints.admit(morphon)` → reject if laws violated
2. `atlas.admit_to_deployment(morphon)` → reject if boundary/capacity fails *(NEW)*
3. `addressing.channel_for(morphon)` → cache DR channel
4. `geometry.e8_coordinates(morphon)` → cache E8 + Leech projections (if geometry registered)
5. `memory.store(morphon)` → persist

Without atlas registered, the existing 4-step flow runs unchanged (backwards compatible).

## Trigger classes

Per [docs/sub_frames/port_trigger_map.md](../../../docs/sub_frames/port_trigger_map.md):

| Operation | Trigger class | Notes |
|---|---|---|
| `julia_c` | A (user) or B (event-driven at forge) | Cached on morphon |
| `in_boundary` | A (user query) | Read-only test |
| `admit_to_deployment` | B (event-driven inside `admit_and_store`) | The integration point |
| `deployment_stats` | A (read-only) | |
| `boundary_recompute` | C (daemon-periodic) | Bound to `brain_sync` channel (period 7 ticks) when wired |
| `evict` | A (user) | Manual eviction |

## Status

- ✅ canonical for Slots 26 + 27 (first build)
- The boundary_recompute → daemon-channel wiring requires the §6 trigger infrastructure (currently designed; minimum implementation is a near-term follow-up).
- Persistence (deployed-set snapshotting across restarts) is a Wave-2 concern.
