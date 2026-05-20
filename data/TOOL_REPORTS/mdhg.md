# mdhg — v2 tool report

> Digital-root hierarchical hashing. Names every morphon by its channel and lattice position.

_Canonical: `work/atomic_constructed/mdhg.py` (378,317 bytes, 8,724 lines)_

_Provenance: `work/atomic_constructed/mdhg.py.decisions.jsonl` (251 decisions)_

## Surface — what's in the canonical

- Classes:   **100**
- Functions: **100**
- Assigns:   **50**
- Imports:   **0**

By decision kind:
  - `class`: 100
  - `function`: 100
  - `assign`: 50
  - `module_docstring`: 1

## Most-replicated symbols (highest variant counts)

These are the symbols the ecosystem has re-implemented the most. High replication = highest-confidence canonical pick.

| Kind | Symbol | Variants observed |
|---|---|---:|
| assign | `logger` | 419 |
| assign | `PHI` | 34 |
| assign | `COUPLING` | 30 |
| function | `digital_root` | 24 |
| assign | `PORT` | 20 |
| assign | `PG_URL` | 19 |
| class | `AGRMEdgeValidator` | 18 |
| class | `AGRMController` | 17 |
| class | `AGRMStateBus` | 17 |
| class | `ModulationController` | 17 |
| class | `NavigatorGR` | 17 |
| class | `PathAuditAgent` | 17 |
| class | `PathBuilder` | 17 |
| class | `SalesmanValidator` | 17 |
| class | `MDHGHashTable` | 15 |

## Top witness files (contributed the most chosen sources)

| Witness | # decisions chosen from this file |
|---|---:|
| `.../mdhg/mdhg_hierarchy/unified_agrm_mdhg.py` | 49 |
| `.../mdhg/partsfactory/mdhg.py` | 28 |
| `.../mdhg/partsfactory/mdhg_sandbox.py` | 21 |
| `.../agrm/mdhg_hierarchy/agrm_core.py` | 21 |
| `.../mdhg/partsfactory/16ba4176_mdhg_ca.py` | 17 |
| `.../mdhg/partsfactory/run_mdhg_thinktank_chain.py` | 15 |
| `.../agrm/mdhg_hierarchy/AGRM.py` | 9 |
| `.../mdhg/partsfactory/mdhg_aggregate.py` | 6 |
| `.../mdhg/partsfactory/mdhg_sim_manifold.py` | 5 |
| `.../mdhg/partsfactory/mdhg_sandbox__1.py` | 5 |

## Destination in the master template

This canonical lands at `src/cmplx/addressing/mdhg.py` per [MASTER_BUILD_TEMPLATE.md](../MASTER_BUILD_TEMPLATE.md).
