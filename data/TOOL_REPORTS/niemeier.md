# niemeier — v2 tool report

> Complete enumeration of 24-D even unimodular lattices. The morphon's Niemeier coordinate picks the right substrate.

_Canonical: `work/atomic_constructed/niemeier.py` (37,717 bytes, 932 lines)_

_Provenance: `work/atomic_constructed/niemeier.py.decisions.jsonl` (74 decisions)_

## Surface — what's in the canonical

- Classes:   **4**
- Functions: **19**
- Assigns:   **48**
- Imports:   **0**

By decision kind:
  - `assign`: 50
  - `function`: 19
  - `class`: 4
  - `module_docstring`: 1

## Most-replicated symbols (highest variant counts)

These are the symbols the ecosystem has re-implemented the most. High replication = highest-confidence canonical pick.

| Kind | Symbol | Variants observed |
|---|---|---:|
| function | `digital_root` | 24 |
| assign | `e8` | 15 |
| assign | `fig` | 12 |
| function | `cartan_A` | 7 |
| function | `cartan_D` | 6 |
| assign | `all_roots` | 5 |
| assign | `ax1` | 5 |
| assign | `ax2` | 5 |
| assign | `ax3` | 5 |
| assign | `ax4` | 5 |
| assign | `ax5` | 5 |
| assign | `ax6` | 5 |
| assign | `ax7` | 5 |
| assign | `gs` | 5 |
| function | `dark_ax` | 5 |

## Top witness files (contributed the most chosen sources)

| Witness | # decisions chosen from this file |
|---|---:|
| `.../niemeier/partsfactory/niemeier_analysis.py` | 36 |
| `.../morphon/morphonic/meta_morphon_and_48d.py` | 14 |
| `.../niemeier/partsfactory/NiemeierSpecs1.py` | 5 |
| `.../niemeier/partsfactory/niemeier_genomic_aligner.py` | 3 |
| `.../niemeier/partsfactory/d40847e5f19f__CQEPlus_auto_full_docs__b4005e4d7d__niemeier_complete.py` | 3 |
| `.../morphon/morphonic/experiment_04_triadic_morphon.py` | 2 |
| `.../niemeier/partsfactory/NiemeierSpecs.py` | 2 |
| `.../<spec>` | 1 |
| `.../leech/partsfactory/leech24__1.py` | 1 |
| `.../cqe/partsfactory/corrected_cqe_benchmarks.py` | 1 |

## No-witness — spec named, index didn't carry

These names appeared in the spec (so they're conceptually part of the family) but no top-level definition with that exact name was found in the indexed source pool.

  - assign `ade_cols`
  - assign `ade_vals`

## Destination in the master template

This canonical lands at `src/cmplx/geometry/niemeier.py` per [MASTER_BUILD_TEMPLATE.md](../MASTER_BUILD_TEMPLATE.md).
