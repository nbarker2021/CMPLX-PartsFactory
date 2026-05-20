# tarpit — v2 tool report

> Symbolic-compute fold on E6. MLambda calculus on morphons. Decidable subspace.

_Canonical: `work/atomic_constructed/tarpit.py` (327,382 bytes, 8,736 lines)_

_Provenance: `work/atomic_constructed/tarpit.py.decisions.jsonl` (251 decisions)_

## Surface — what's in the canonical

- Classes:   **100**
- Functions: **100**
- Assigns:   **51**
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
| class | `E6Codec` | 38 |
| class | `E6Token` | 38 |
| class | `RelativityEnvelope` | 38 |
| function | `bits6_str` | 38 |
| function | `_demo` | 38 |
| function | `check_envelope` | 38 |
| function | `collect_grains` | 38 |
| function | `count_dusts_and_triads` | 38 |
| function | `gram_effective_dim` | 38 |
| function | `merge_from_bf` | 38 |
| function | `orthonormal_basis_from_seed` | 38 |
| function | `seed_from_program` | 38 |
| function | `split_bc_quads` | 38 |
| function | `split_bf_octs` | 38 |

## Top witness files (contributed the most chosen sources)

| Witness | # decisions chosen from this file |
|---|---:|
| `.../tarpit/cryptography/unified_tarpit.py` | 125 |
| `.../tarpit/cryptography/e6_tarpit_bridge.py` | 23 |
| `.../tarpit/cryptography/tarpit_tool_analysis.py` | 13 |
| `.../tarpit/cryptography/tarpit.py` | 13 |
| `.../cqe/partsfactory/cqe_port.py` | 8 |
| `.../tarpit/cryptography/tarpit_engine.py` | 5 |
| `.../tarpit/cryptography/e6_tarpit_bridge_v8.py` | 5 |
| `.../tarpit/cryptography/custom_normalization_tarpit.py` | 4 |
| `.../tarpit/cryptography/tarpit_bridge.py` | 3 |
| `.../tarpit/cryptography/e6_tarpit_bridge_v3.py` | 3 |

## Destination in the master template

This canonical lands at `src/cmplx/symbolic/tarpit.py` per [MASTER_BUILD_TEMPLATE.md](../MASTER_BUILD_TEMPLATE.md).
