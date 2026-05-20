# leech — v2 tool report

> 24-D substrate. Three E8 slices compose one Leech point. Hosts the Golay code.

_Canonical: `work/atomic_constructed/leech.py` (83,881 bytes, 2,315 lines)_

_Provenance: `work/atomic_constructed/leech.py.decisions.jsonl` (43 decisions)_

## Surface — what's in the canonical

- Classes:   **17**
- Functions: **11**
- Assigns:   **14**
- Imports:   **0**

By decision kind:
  - `class`: 17
  - `assign`: 14
  - `function`: 11
  - `module_docstring`: 1

## Most-replicated symbols (highest variant counts)

These are the symbols the ecosystem has re-implemented the most. High replication = highest-confidence canonical pick.

| Kind | Symbol | Variants observed |
|---|---|---:|
| assign | `logger` | 419 |
| function | `digital_root` | 24 |
| assign | `NIEMEIER_TYPES` | 21 |
| assign | `__all__` | 14 |
| class | `Leech24` | 11 |
| class | `LeechVector` | 8 |
| class | `LeechLattice` | 7 |
| class | `GolayCode` | 7 |
| class | `E8Full` | 5 |
| assign | `NIEMEIER_SPECS` | 4 |
| class | `LeechSnapResult` | 4 |
| class | `NiemeierLattice` | 4 |
| class | `RootSystem` | 4 |
| assign | `LEECH_DIM` | 2 |
| assign | `HOST_GATEWAY` | 2 |

## Top witness files (contributed the most chosen sources)

| Witness | # decisions chosen from this file |
|---|---:|
| `.../leech/partsfactory/leech_ops.py` | 6 |
| `.../leech/partsfactory/leech_lattice_24d.py` | 5 |
| `.../leech/partsfactory/leech__1.py` | 3 |
| `.../leech/partsfactory/leech_climate_embedder.py` | 3 |
| `.../golay/partsfactory/golay_code.py` | 3 |
| `.../leech/partsfactory/_leech_original.py` | 3 |
| `.../leech/partsfactory/leech__3.py` | 2 |
| `.../leech/partsfactory/leech_lattice.py` | 2 |
| `.../leech/partsfactory/leech_octad_witness_controller.py` | 2 |
| `.../niemeier/partsfactory/d40847e5f19f__CQEPlus_auto_full_docs__b4005e4d7d__niemeier_complete.py` | 2 |

## Destination in the master template

This canonical lands at `src/cmplx/geometry/leech.py` per [MASTER_BUILD_TEMPLATE.md](../MASTER_BUILD_TEMPLATE.md).
