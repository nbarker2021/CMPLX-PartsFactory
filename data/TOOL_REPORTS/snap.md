# snap — v2 tool report

> SNAP clustering — population-level discovery layer. Often paired with hash systems.

_Canonical: `work/atomic_constructed/snap.py` (222,947 bytes, 5,382 lines)_

_Provenance: `work/atomic_constructed/snap.py.decisions.jsonl` (251 decisions)_

## Surface — what's in the canonical

- Classes:   **100**
- Functions: **100**
- Assigns:   **49**
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
| assign | `log` | 29 |
| assign | `PORT` | 20 |
| assign | `PG_URL` | 19 |
| class | `ContextScore` | 18 |
| class | `AGRMEdgeValidator` | 18 |
| class | `AGRMController` | 17 |
| class | `AGRMStateBus` | 17 |
| assign | `__all__` | 14 |
| class | `Policy` | 13 |
| assign | `PIPELINE_URL` | 11 |
| assign | `__adapter__` | 10 |
| assign | `__layer__` | 10 |

## Top witness files (contributed the most chosen sources)

| Witness | # decisions chosen from this file |
|---|---:|
| `.../snap/partsfactory/unified_snap.py` | 83 |
| `.../snap/partsfactory/unified_snaplat.py` | 44 |
| `.../snap/governance_snap/snap_engine.py` | 28 |
| `.../mdhg/mdhg_hierarchy/unified_agrm_mdhg.py` | 20 |
| `.../snap/partsfactory/6117cfa2_snap_atom.py` | 5 |
| `.../cqe/partsfactory/8a163c7d76bb__Bestbuild101325_2__Best_build_101325__CQE_GVS_MONOLITH.py` | 4 |
| `.../snap/governance_snap/snap_classifier_v0_1_2025_08_13.py` | 4 |
| `.../agrm/mdhg_hierarchy/AGRM.py` | 3 |
| `.../morphon/partsfactory/unified_morphonic.py` | 2 |
| `.../tarpit/cryptography/unified_tarpit.py` | 2 |

## Failed decisions (AST validation refused)

  - assign `DB`: ESCALATE: all 1 variant candidates failed AST validation

## Destination in the master template

This canonical lands at `src/cmplx/snap/snap.py` per [MASTER_BUILD_TEMPLATE.md](../MASTER_BUILD_TEMPLATE.md).
