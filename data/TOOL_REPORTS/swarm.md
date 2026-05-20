# swarm — v2 tool report

> Multi-agent coordination projection. Many small agents in lockstep on AgentHub.

_Canonical: `work/atomic_constructed/swarm.py` (68,140 bytes, 1,754 lines)_

_Provenance: `work/atomic_constructed/swarm.py.decisions.jsonl` (40 decisions)_

## Surface — what's in the canonical

- Classes:   **10**
- Functions: **25**
- Assigns:   **4**
- Imports:   **0**

By decision kind:
  - `function`: 25
  - `class`: 10
  - `assign`: 4
  - `module_docstring`: 1

## Most-replicated symbols (highest variant counts)

These are the symbols the ecosystem has re-implemented the most. High replication = highest-confidence canonical pick.

| Kind | Symbol | Variants observed |
|---|---|---:|
| assign | `logger` | 419 |
| assign | `PROJECT_ROOT` | 5 |
| assign | `SCRIPT_DIR` | 5 |
| class | `SwarmBridge` | 2 |
| class | `SwarmTask` | 2 |
| function | `_read_json` | 2 |
| function | `_to_int` | 2 |
| assign | `_GATES_CORE` | 1 |
| class | `AgentResult` | 1 |
| class | `ChatMessage` | 1 |
| class | `SwarmController` | 1 |
| class | `SwarmMCPTools` | 1 |
| class | `SwarmRole` | 1 |
| class | `SwarmScope` | 1 |
| class | `SwarmSession` | 1 |

## Top witness files (contributed the most chosen sources)

| Witness | # decisions chosen from this file |
|---|---:|
| `.../swarm/partsfactory/run_swarm_meta_review.py` | 16 |
| `.../swarm/partsfactory/build_swarm_concurrency_playbook.py` | 9 |
| `.../swarm/partsfactory/swarm_mcp_tools.py` | 7 |
| `.../mmdb/mmdb_memory/vector_mmdb_tools.py` | 2 |
| `.../swarm/partsfactory/swarm_bridge.py` | 2 |
| `.../<spec>` | 1 |
| `.../agrm/mdhg_hierarchy/agrm_bridge.py` | 1 |
| `.../e8/partsfactory/e8_embedding_ingest_controller.py` | 1 |
| `.../mdhg/partsfactory/run_mdhg_thinktank_chain.py` | 1 |

## Destination in the master template

This canonical lands at `projections/swarm/swarm.py` per [MASTER_BUILD_TEMPLATE.md](../MASTER_BUILD_TEMPLATE.md).
