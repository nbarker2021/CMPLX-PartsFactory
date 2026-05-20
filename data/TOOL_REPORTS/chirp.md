# chirp — v2 tool report

> Geometry-native transport. Three-layer acoustic encoding (DTMF carrier + E8 harmonics + superperm subharmonics).

_Canonical: `work/atomic_constructed/chirp.py` (32,991 bytes, 731 lines)_

_Provenance: `work/atomic_constructed/chirp.py.decisions.jsonl` (28 decisions)_

## Surface — what's in the canonical

- Classes:   **9**
- Functions: **17**
- Assigns:   **1**
- Imports:   **0**

By decision kind:
  - `function`: 17
  - `class`: 9
  - `module_docstring`: 1
  - `assign`: 1

## Most-replicated symbols (highest variant counts)

These are the symbols the ecosystem has re-implemented the most. High replication = highest-confidence canonical pick.

| Kind | Symbol | Variants observed |
|---|---|---:|
| class | `ConfigManager` | 4 |
| function | `construct_superpermutation` | 4 |
| function | `generate_candidates` | 4 |
| assign | `DATA_FILENAME` | 2 |
| class | `DTT` | 2 |
| class | `Grid` | 2 |
| class | `LayoutMemory` | 2 |
| function | `calculate_score` | 2 |
| function | `calculate_overlap` | 2 |
| function | `generate_permutations` | 2 |
| function | `hash_permutation` | 2 |
| function | `is_valid_permutation` | 2 |
| function | `unhash_permutation` | 2 |
| class | `CBCPlanner` | 1 |
| class | `Gate` | 1 |

## Top witness files (contributed the most chosen sources)

| Witness | # decisions chosen from this file |
|---|---:|
| `.../chirp/partsfactory/superperm_code.py` | 11 |
| `.../snap/partsfactory/unified_snaplat.py` | 9 |
| `.../chirp/partsfactory/58038175e5ca__src_superperm__cbc_planner.py` | 2 |
| `.../agrm/mdhg_hierarchy/agrm_core.py` | 2 |
| `.../<spec>` | 1 |
| `.../chirp/partsfactory/construct_superpermutation.py` | 1 |
| `.../chirp/partsfactory/46a8e07d80a8__cqe_unified_src__superperm_config.py` | 1 |
| `.../chirp/governance_snap/snap_superperm.py` | 1 |

## Destination in the master template

This canonical lands at `src/cmplx/transport/chirp.py` per [MASTER_BUILD_TEMPLATE.md](../MASTER_BUILD_TEMPLATE.md).
