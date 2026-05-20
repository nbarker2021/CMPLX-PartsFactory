# Repo Kernel Unified Workflows

Generated: 2026-05-13T14:24:09.797662+00:00

## Runtime Topology

| Module | Runtime URLs | Compose Services | README Ports | Port Ranges |
| --- | ---: | ---: | ---: | --- |
| `CMPLXUNI` | 1 | 0 | 1 | - |
| `CMPLX-TMN-main` | 94 | 93 | 2 | 11000-11205 |
| `CMPLXMCP` | 1 | 0 | 1 | - |

## Workflow Coverage

| Workflow | Modules | Routes | MCP Tools | Runtime Targets |
| --- | ---: | ---: | ---: | ---: |
| `memory` | 3 | 73 | 21 | 4 |
| `mcp_tools` | 3 | 24 | 117 | 1 |
| `agent_orchestration` | 3 | 111 | 19 | 8 |
| `knowledge` | 3 | 181 | 15 | 13 |
| `training` | 2 | 29 | 0 | 3 |
| `geometry` | 3 | 69 | 44 | 5 |
| `code_execution` | 3 | 155 | 3 | 7 |
| `pipeline` | 2 | 49 | 0 | 6 |
| `external_ai_portal` | 2 | 42 | 0 | 4 |

## First API Layer Recommendation

Start with `memory`, then `mcp_tools`, then `agent_orchestration`.

The unified API should health-check documented runtime ports first, then fall back to static adapter surfaces when a repo service is not running.

Do not call mutating endpoints automatically; require an explicit approved workflow before writes.

## Implemented First Layer

The first concrete workflow layer is now exposed:

- `GET /api/unified/memory`
- `GET /api/unified/memory/capabilities`
- `POST /api/unified/memory/query`
- `POST /api/unified/memory/receipt-plan`
- `GET /api/unified/memory/runtime-preflight`
- `POST /api/unified/memory/corpus-import-plan`

This layer plans memory reads across `CMPLXUNI` MMDB MCP tools, `CMPLX-TMN-main`
MMDB/receipt services, and static adapter routes. It checks documented runtime
ports first and falls back to static surfaces when services are not currently
running.

The memory runtime preflight combines compose evidence, service names, ports,
build/image hints, volumes, env files, and health checks for the focused memory
slice. It does not start services or write Postgres.

The memory corpus import plan reads corpus archive manifests and database member
markers, hashes bounded SQLite-like members, and produces approval gates before
any extraction, schema inspection, or Postgres write.

The follow-on source layer now supports an approval-gated SQLite quarantine
probe:

- `POST /api/sources/{source_id}/archive-sqlite-quarantine-probe`
- MCP tool `repo_kernel_archive_sqlite_quarantine_probe`

This copies one selected database member from a zip archive into
`/kernel/quarantine`, then opens the quarantined copy read-only to list schema,
columns, and row counts. It does not mutate the source archive or write
Postgres.

Quarantined SQLite row previews are exposed as:

- `POST /api/sources/quarantine/sqlite-preview`
- MCP tool `repo_kernel_quarantine_sqlite_preview`

This returns capped sample rows, per-cell hashes, table role classifications,
and memory-mapping hints for future agents. It is read-only and quarantine-only.

The read-only MMDB import dry-run is exposed as:

- `POST /api/sources/quarantine/mmdb-import-dry-run`
- MCP tool `repo_kernel_mmdb_import_dry_run`

It maps quarantined MMDB tables into candidate `memory_atom`, `memory_edge`,
and `receipt` records, validates JSON columns, creates deterministic source row
hashes, and estimates import size. It does not write Postgres.

The memory workflow compatibility planner is exposed as:

- `POST /api/unified/memory/mmdb-import-compatibility`
- MCP tool `repo_kernel_memory_mmdb_import_compatibility`

It compares the MMDB dry-run recipe against discovered memory write tools,
routes, and runtime health. Current recommendation is
`repo_kernel_staging_adapter_first`: atoms and receipts have strong candidate
surfaces, memory edges need neutral graph staging, and all live memory runtimes
must remain untouched until approved and healthy.

For oversized or parse-hostile evidence, the fallback planner is exposed as:

- `POST /api/sources/file-breakdown-plan`
- MCP tool `repo_kernel_file_breakdown_plan`

It plans chunking strategies only; it does not materialize chunks.

## Implemented Second Layer

The second concrete workflow layer is now exposed:

- `GET /api/unified/mcp-tools`
- `GET /api/unified/mcp-tools/capabilities`
- `GET /api/unified/mcp-tools/tools`
- `GET /api/unified/mcp-tools/tools/{tool_name}`
- `POST /api/unified/mcp-tools/call-plan`

This layer unifies MCP tool declarations from `CMPLXUNI` and `CMPLXMCP`,
including geometric, MMDB, universal crystal, governance, interface, and system
tools. It returns call plans and runtime candidates, but does not execute tools
unless a future live runtime transport is explicitly enabled.

## Runtime Activation Planning

The runtime layer now exposes:

- `POST /api/runtime/activation-plan`
- `GET /api/runtime/issues`

This returns repo-native preflight hints for workflow-specific runtime targets
while honoring each repo's declared ports. It is plan-only and does not start
containers or processes.

Compose files are now treated as evidence, not as the application layer. A
compose file is a compact checklist of service names, ports, env files,
dependency order, profiles, volumes, and build contexts. The controller and
adapter layers decide what to activate, one capability at a time.

The compose evidence layer is exposed at:

- `GET /api/evidence/compose`
- `GET /api/modules/{name}/compose-evidence`
- MCP tool `repo_kernel_compose_evidence`

Activation plans now include both container and host working directories. Health
checks distinguish HTTP services from TCP services such as Postgres and Redis.
`CMPLXMCP` has a probed stdio runtime shim, so the remaining transport issue is
that HTTP/SSE bridging has not been added yet.

## Implemented Third Layer

The third workflow layer is now exposed:

- `GET /api/unified/agent-orchestration`
- `GET /api/unified/agent-orchestration/capabilities`
- `POST /api/unified/agent-orchestration/plan`
- MCP tools `repo_kernel_agent_orchestration_capabilities` and
  `repo_kernel_agent_orchestration_plan`

This layer groups identity, cooperation, daemon, thinktank, spawn, station, and
agent-manager surfaces across promoted modules. It uses compose-derived service
names and ports as preflight evidence, then combines those hints with static
routes/MCP tools and health checks. It does not spawn or mutate live agents.

## Implemented Fourth Layer

The fourth workflow layer is now exposed:

- `GET /api/unified/knowledge`
- `GET /api/unified/knowledge/capabilities`
- `POST /api/unified/knowledge/plan`
- `GET /api/unified/knowledge/runtime-preflight`
- MCP tools `repo_kernel_knowledge_capabilities`,
  `repo_kernel_knowledge_plan`, and
  `repo_kernel_knowledge_runtime_preflight`

This layer groups library, query, semantic, KB, code-context, ingestion, and
atlas-style knowledge surfaces across promoted modules. It is meant to help
Codex and other local agents offload bounded capability planning to the Docker
kernel before broad filesystem scans.

Current verified surface:

- 162 route candidates
- 25 MCP tool candidates
- 13 runtime targets from compose/README evidence

Runtime health checks currently show these knowledge services are not running,
so the layer remains static-surface-first. Search/query/read candidates are safe
to plan; index, ingest, store, update, and other mutating operations remain
approval-gated.
