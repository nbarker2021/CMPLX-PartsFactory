# mmdb — v2 tool report

> Manifold-partitioned memory. Storage discipline keyed by MDHG, partitioned by geometry.

_Canonical: `work/atomic_constructed/mmdb.py` (308,190 bytes, 8,363 lines)_

_Provenance: `work/atomic_constructed/mmdb.py.decisions.jsonl` (210 decisions)_

## Surface — what's in the canonical

- Classes:   **59**
- Functions: **100**
- Assigns:   **50**
- Imports:   **0**

By decision kind:
  - `function`: 100
  - `class`: 59
  - `assign`: 50
  - `module_docstring`: 1

## Most-replicated symbols (highest variant counts)

These are the symbols the ecosystem has re-implemented the most. High replication = highest-confidence canonical pick.

| Kind | Symbol | Variants observed |
|---|---|---:|
| assign | `logger` | 419 |
| assign | `E8_NORM` | 38 |
| function | `_digital_root` | 24 |
| class | `Receipt` | 22 |
| assign | `PG_URL` | 19 |
| assign | `BLOCK` | 16 |
| assign | `__all__` | 14 |
| class | `LatticeEdge` | 10 |
| class | `LatticeNode` | 10 |
| assign | `__getattr__` | 9 |
| assign | `MMDB_URL` | 8 |
| assign | `MAJOR_SYSTEMS` | 8 |
| assign | `MMDB_ROOT` | 8 |
| assign | `UNIFIED_FAMILIES` | 8 |
| assign | `FNV_OFFSET` | 8 |

## Top witness files (contributed the most chosen sources)

| Witness | # decisions chosen from this file |
|---|---:|
| `.../mmdb/mmdb_memory/mmdb__3.py` | 24 |
| `.../mmdb/mmdb_memory/mmdb__8.py` | 12 |
| `.../mmdb/mmdb_memory/mmdb_mcp_server.py` | 12 |
| `.../mmdb/mmdb_memory/mmdb_discovery.py` | 11 |
| `.../mmdb/mmdb_memory/vector_mmdb_tools.py` | 11 |
| `.../mmdb/mmdb_memory/mmdb_kernel.py` | 10 |
| `.../mmdb/mmdb_memory/mmdb_tools.py` | 10 |
| `.../mmdb/mmdb_memory/mmdb_pg_bridge.py` | 9 |
| `.../mmdb/mmdb_memory/postgres_mmdb_integration.py` | 8 |
| `.../mmdb/mmdb_memory/sap_mmdb.py` | 7 |

## Destination in the master template

This canonical lands at `src/cmplx/memory/mmdb.py` per [MASTER_BUILD_TEMPLATE.md](../MASTER_BUILD_TEMPLATE.md).
