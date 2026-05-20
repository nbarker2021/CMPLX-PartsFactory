# cmplx — v2 tool report

> The umbrella specification. Every other family is a chapter of it.

_Canonical: `work/atomic_constructed/cmplx.py` (448,587 bytes, 10,637 lines)_

_Provenance: `work/atomic_constructed/cmplx.py.decisions.jsonl` (170 decisions)_

## Surface — what's in the canonical

- Classes:   **100**
- Functions: **37**
- Assigns:   **32**
- Imports:   **0**

By decision kind:
  - `class`: 100
  - `function`: 37
  - `assign`: 32
  - `module_docstring`: 1

## Most-replicated symbols (highest variant counts)

These are the symbols the ecosystem has re-implemented the most. High replication = highest-confidence canonical pick.

| Kind | Symbol | Variants observed |
|---|---|---:|
| assign | `logger` | 419 |
| assign | `E8_NORM` | 38 |
| assign | `PHI` | 34 |
| assign | `COUPLING` | 30 |
| function | `digital_root` | 24 |
| class | `E8Lattice` | 21 |
| class | `AGRMEdgeValidator` | 18 |
| class | `AGRMController` | 17 |
| class | `AGRMStateBus` | 17 |
| class | `ModulationController` | 17 |
| class | `NavigatorGR` | 17 |
| class | `PathAuditAgent` | 17 |
| class | `PathBuilder` | 17 |
| class | `MDHGHashTable` | 15 |
| class | `AGRMDiagnosticController` | 12 |

## Top witness files (contributed the most chosen sources)

| Witness | # decisions chosen from this file |
|---|---:|
| `.../agrm/mdhg_hierarchy/agrm_core.py` | 23 |
| `.../cmplx/partsfactory/cmplx_core_primitives.py` | 21 |
| `.../cmplx/partsfactory/cmplx_eversion_network.py` | 15 |
| `.../cmplx/partsfactory/cmplx_cli.py` | 9 |
| `.../agrm/mdhg_hierarchy/AGRM.py` | 8 |
| `.../cmplx/partsfactory/cmplx_agent_playbook.py` | 7 |
| `.../cmplx/partsfactory/cmplx_deployment.py` | 7 |
| `.../cmplx/partsfactory/cmplx_wolfram_poc.py` | 6 |
| `.../cmplx/partsfactory/CMPLXThinkTankEngine.py` | 6 |
| `.../cmplx/partsfactory/rebrand_to_cmplx.py` | 5 |

## Destination in the master template

This canonical lands at `src/cmplx/cmplx/cmplx.py` per [MASTER_BUILD_TEMPLATE.md](../MASTER_BUILD_TEMPLATE.md).
