# tmn — v2 tool report

> The gateway, four generations. HTTP, MCP, raw protocol, internal RPC.

_Canonical: `work/atomic_constructed/tmn.py` (463,136 bytes, 10,388 lines)_

_Provenance: `work/atomic_constructed/tmn.py.decisions.jsonl` (236 decisions)_

## Surface — what's in the canonical

- Classes:   **85**
- Functions: **100**
- Assigns:   **44**
- Imports:   **0**

By decision kind:
  - `function`: 100
  - `class`: 85
  - `assign`: 50
  - `module_docstring`: 1

## Most-replicated symbols (highest variant counts)

These are the symbols the ecosystem has re-implemented the most. High replication = highest-confidence canonical pick.

| Kind | Symbol | Variants observed |
|---|---|---:|
| assign | `logger` | 419 |
| assign | `PORT` | 20 |
| function | `_get` | 20 |
| assign | `PG_URL` | 19 |
| assign | `BLOCK` | 16 |
| class | `QueryRequest` | 14 |
| function | `_normalize` | 12 |
| assign | `BOARD_URL` | 10 |
| assign | `TMN1_DB` | 9 |
| assign | `__getattr__` | 9 |
| assign | `app` | 7 |
| class | `ToolCall` | 7 |
| function | `_dot` | 7 |
| class | `ExpertModule` | 6 |
| class | `TriadicState` | 6 |

## Top witness files (contributed the most chosen sources)

| Witness | # decisions chosen from this file |
|---|---:|
| `.../tmn/core_engine/tmn1_portal.py` | 35 |
| `.../tmn/core_engine/tmn1_daemon.py` | 29 |
| `.../tmn/core_engine/tmn1_coop_service.py` | 19 |
| `.../tmn/core_engine/tmn1_mint_service.py` | 19 |
| `.../tmn/core_engine/tmn1_teaching_service.py` | 17 |
| `.../tmn/core_engine/tmn1_sap_service.py` | 12 |
| `.../tmn/core_engine/tmn1_hook.py` | 12 |
| `.../tmn/core_engine/tmn1_thinktank_service.py` | 12 |
| `.../tmn/core_engine/tmn_mcp_crystal.py` | 12 |
| `.../tmn/core_engine/tmn1_port_controller.py` | 8 |

## No-witness — spec named, index didn't carry

These names appeared in the spec (so they're conceptually part of the family) but no top-level definition with that exact name was found in the indexed source pool.

  - assign `ATLAS`
  - assign `_DOWN_CHANNELS`
  - assign `_E8_DOWN_ROOT`
  - assign `_E8_UP_ROOT`
  - assign `_META_CHANNELS`
  - assign `_UP_CHANNELS`

## Destination in the master template

This canonical lands at `src/cmplx/tmn/tmn.py` per [MASTER_BUILD_TEMPLATE.md](../MASTER_BUILD_TEMPLATE.md).
