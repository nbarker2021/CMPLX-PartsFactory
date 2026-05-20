# Repo Promotion Ledger - 2026-05-13

This ledger ranks clean repo-kernel modules for the master CMPLX rebuild.
It is a decision layer, not a deletion list.

## Promotion States

- `promoted_candidate`: build adapters/tests first; likely first-wave source.
- `canonical_doctrine`: promote as doctrine/specification, not runtime code.
- `filtered_candidate`: valuable but too noisy to promote wholesale.
- `reference_candidate`: use for provenance/cross-checking.
- `needs_slice_index`: do not full-root index; index selected subdirectories.
- `archive_reference`: keep for archive/evidence unless a dependency emerges.

## Ranked Ledger

| Rank | Module | Status | Role | Score | Risk | GitNexus | Key signal | Action |
| ---: | --- | --- | --- | ---: | ---: | --- | --- | --- |
| 1 | `CMPLXUNI` | `promoted_candidate` | `unified_system_build` | 89.2 | 0.0 | yes | 135 routes, 14 tools, 300 flows, 143,285 symbols | build adapters and capability tests first |
| 2 | `CMPLX-TMN-main` | `promoted_candidate` | `tmn_primary` | 86.4 | 0.0 | yes | 393 routes, 218 flows, 8,931 symbols | build adapters and capability tests first |
| 3 | `CMPLXMCP` | `promoted_candidate` | `mcp_layer` | 71.9 | 0.0 | yes | 14 routes, 83 flows, 3,294 symbols | build adapters and capability tests first |
| 4 | `CMPLX-Monorepo` | `reference_candidate` | `historical_monorepo_reference` | 61.6 | 0.0 | yes | 47 routes, 300 flows, 18,558 symbols | use for provenance and cross-checking, not first canonical source |
| 5 | `CMPLXDevKit` | `filtered_candidate` | `developer_toolkit` | 59.2 | 10.0 | yes | 52 routes, 299 flows, 220,727 symbols | mine for reusable tools after filtering external/vendor shards |
| 6 | `CMPLX-TMN1` | `reference_candidate` | `tmn_historical_build` | 52.2 | 0.0 | yes | 86 routes, 25 flows, 1,599 symbols | use for provenance and cross-checking, not first canonical source |
| 7 | `CMPLX-Formalization` | `canonical_doctrine` | `mathematical_doctrine` | 50.9 | 0.0 | yes | 20 symbols | promote docs/specs as doctrine layer; no runtime merge needed |
| 8 | `CMPLX-Manny` | `candidate_review` | `manny_identity_system` | 50.1 | 0.0 | yes | 2 flows, 146 symbols | review memory/identity assets and promote only active pieces |
| 9 | `scout-demo-service` | `archive_reference` | `external_service_reference` | 23.9 | 0.0 | yes | 7 symbols | archive unless a direct service dependency emerges |
| 10 | `CMPLX` | `unindexed_review` | `baseline_core` | 2.0 | 62.0 | no | 12,428 code files | index bounded subdirectories or inspect manually |
| 11 | `CMPLX-PartsFactory` | `workspace_root` | `active_unification_root` | 0.0 | 35.0 | no | 0 code files | keep as orchestration root; do not promote as source module until GitHub repo has a real pinned commit |
| 12 | `CMPLX-1T` | `needs_slice_index` | `geometric_system_build` | 0.0 | 82.0 | no | 22,224 code files | index selected subdirectories; do not full-root scan |

## First-Wave Promotions

- `CMPLXUNI`: High-value module with clear API/controller implementation surface. Action: build adapters and capability tests first.
- `CMPLX-TMN-main`: High-value module with clear API/controller implementation surface. Action: build adapters and capability tests first.
- `CMPLXMCP`: High-value module with clear API/controller implementation surface. Action: build adapters and capability tests first.
- `CMPLX-Formalization`: Small, focused formalization source. Action: promote docs/specs as doctrine layer; no runtime merge needed.

## Needs Filtering Or Slicing

- `CMPLXDevKit`: Large toolkit source, but noisy and overbroad. Local shape: 5,013 files, 94.2 MB, 19 large files. Action: mine for reusable tools after filtering external/vendor shards.
- `CMPLX`: No completed GitNexus index yet. Local shape: 12,899 files, 943.5 MB, 123 large files. Action: index bounded subdirectories or inspect manually.
- `CMPLX-1T`: Potentially valuable but too large/noisy for direct promotion. Local shape: 38,681 files, 1.2 GB, 212 large files. Action: index selected subdirectories; do not full-root scan.

## Route And Tool Signals

### CMPLXUNI

Routes:
- `/api/chat` in `cmplx-nextjs/src/app/api/chat/route.ts`
- `/api/memory/recall` in `cmplx-nextjs/src/app/api/memory/recall/route.ts`
- `/api/onboarding/start` in `cmplx-nextjs/src/app/api/onboarding/start/route.ts`
- `/api/memory/[agentId]` in `cmplx-nextjs/src/app/api/memory/[agentId]/route.ts`
- `/ingress` in `lfai/api_server.py`
- `/octet/run` in `lfai/api_server.py`
- `/unfold/run` in `lfai/api_server.py`
- `/planner/run` in `lfai/api_server.py`

Tools:
- `list_families` in `src/cmplx/mcp/mmdb_mcp_server.py`
- `get_family_stats` in `src/cmplx/mcp/mmdb_mcp_server.py`
- `insert_atom` in `src/cmplx/mcp/mmdb_mcp_server.py`
- `get_atom` in `src/cmplx/mcp/mmdb_mcp_server.py`
- `query_atoms` in `src/cmplx/mcp/mmdb_mcp_server.py`
- `insert_receipt` in `src/cmplx/mcp/mmdb_mcp_server.py`
- `get_receipts_for_atom` in `src/cmplx/mcp/mmdb_mcp_server.py`
- `log_e8_operation` in `src/cmplx/mcp/mmdb_mcp_server.py`

### CMPLX-TMN-main

Routes:
- `/health` in `src/trainer/trainer.py`
- `/train` in `src/trainer/trainer.py`
- `/evaluate` in `src/trainer/trainer.py`
- `/training_runs` in `src/trainer/trainer.py`
- `/agent/{agent_id}/metrics` in `src/trainer/trainer.py`
- `/checkpoint` in `src/trainer/trainer.py`
- `/reason` in `src/thinktank/thinktank.py`
- `/deliberate` in `src/thinktank/thinktank.py`

### CMPLXMCP

Routes:
- `/health` in `polyglot/polyglot-server/main.py`
- `/languages` in `polyglot/polyglot-server/main.py`
- `/execute` in `polyglot/polyglot-server/main.py`
- `/detect` in `polyglot/polyglot-server/main.py`
- `/execution/{execution_id}` in `polyglot/polyglot-server/main.py`
- `/status` in `polyglot/polyglot-server/main.py`
- `/mcp/tools` in `polyglot/polyglot-server/main.py`
- `/mcp/tools/{tool_name}` in `polyglot/polyglot-server/main.py`

### CMPLX-Monorepo

Routes:
- `/speedlight/cache` in `cqe_website/cqe_tools_api.py`
- `/speedlight/stats` in `cqe_website/cqe_tools_api.py`
- `/speedlight/ledger` in `cqe_website/cqe_tools_api.py`
- `/moonshine/add` in `cqe_website/cqe_tools_api.py`
- `/moonshine/get/{item_id}` in `cqe_website/cqe_tools_api.py`
- `/moonshine/search` in `cqe_website/cqe_tools_api.py`
- `/moonshine/list` in `cqe_website/cqe_tools_api.py`
- `/moonshine/stats` in `cqe_website/cqe_tools_api.py`

### CMPLXDevKit

Routes:
- `/` in `src/cqe_organized/d6086600e784__allennlp_service__config_explorer.py`
- `/debug/` in `src/cqe_organized/d6086600e784__allennlp_service__config_explorer.py`
- `/api/config/` in `src/cqe_organized/d6086600e784__allennlp_service__config_explorer.py`
- `/api/health` in `src/cqe_organized/c0749a5fb708__elysia_api__app.py`
- `/{user_id}/{conversation_id}` in `src/cqe_organized/a4d23542d8b4__api_routes__tree_config.py`
- `/{user_id}/{conversation_id}/new` in `src/cqe_organized/a4d23542d8b4__api_routes__tree_config.py`
- `/{user_id}/{conversation_id}/{config_id}/load` in `src/cqe_organized/a4d23542d8b4__api_routes__tree_config.py`
- `/models` in `src/cqe_organized/9c7b15557109__api_routes__user_config.py`

### CMPLX-TMN1

Routes:
- `/health` in `infrastructure/paper_harvester.py`
- `/status` in `infrastructure/paper_harvester.py`
- `/status/{domain}` in `infrastructure/paper_harvester.py`
- `/harvest` in `infrastructure/paper_harvester.py`
- `/papers/{domain}` in `infrastructure/paper_harvester.py`
- `/domains` in `infrastructure/paper_harvester.py`
- `/tools` in `infrastructure/gateway.py`
- `/tools/{category}` in `infrastructure/gateway.py`

## Recommended Next Work

1. Build adapter skeletons for `CMPLXMCP`, `CMPLXUNI`, and `CMPLX-TMN-main`.
2. Add capability tests around routes/tools rather than repo-native test suites.
3. Slice-index `CMPLX-1T` and selected `CMPLX` directories instead of full-root scans.
4. Filter `CMPLXDevKit` before promotion, especially `src/cqe_organized/` external/test shards.
5. Use `CMPLX-Formalization` as canonical doctrine and provenance language.
