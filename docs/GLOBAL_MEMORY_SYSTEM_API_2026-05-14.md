# Global Memory System API

Generated: 2026-05-14

## Purpose

The second global system lane is `memory`. It unifies MMDB, atom, receipt,
ledger, family, and MDHG memory surfaces across registered repos while leaving
each repo in its own checkout with its own settings.

This global API is a controller and mapping layer. It does not start services,
write databases, import archives, or mutate source. It aggregates same-name
capabilities from every matching repo and reports their current local paths
under `repo_kernel/repos/<module>/...`.

The first live routing pass is now in place for read-only memory calls. Public
callers can use `repo-kernel` on port `8786`; the controller reaches the memory
services on Docker-internal URLs and keeps their current ports/settings intact.

## API

General form:

- `GET /api/global-systems`
- `GET /api/global-systems/memory`
- `GET /api/global-systems/memory/tools`
- `GET /api/global-systems/memory/routes`
- `GET /api/global-systems/memory/ports`
- `GET /api/global-systems/memory/skills`
- `POST /api/global-systems/memory/call-plan`

Short alias:

- `GET /api/global/memory`
- `GET /api/global/memory/tools`
- `GET /api/global/memory/routes`
- `GET /api/global/memory/ports`
- `GET /api/global/memory/skills`
- `POST /api/global/memory/call-plan`
- `GET /api/global/memory/upstreams`
- `GET /api/global/memory/health`
- `GET /api/global/memory/search?q=<term>`
- `GET /api/global/memory/read/{service}/{path}`

MCP mirrors:

- `repo_kernel_global_system` with `system = "memory"`
- `repo_kernel_global_system_tools` with `system = "memory"`
- `repo_kernel_global_system_skills` with `system = "memory"`
- `repo_kernel_global_system_call_plan` with `system = "memory"`
- `repo_kernel_global_memory_upstreams`
- `repo_kernel_global_memory_read`

## Canonical Port Evidence

| Port | Source | Current Meaning |
| ---: | --- | --- |
| `11002` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-pg` Postgres dependency. |
| `11120` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-mmdb` memory service. |
| `11121` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-mmdb-pg-bridge` bridge service. |
| `11122` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-mmdb-discovery` discovery service. |
| `11123` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-data-steward` memory/data steward service. |
| `11195` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-receipt` receipt service. |

## Live Routed Upstreams

The current Docker-backed memory slice is healthy behind repo-kernel:

- `pocket-memory-api`
- `agenthub-db-bridge`
- `mmdb-unified`
- `mdhg-unified`
- `postgres`
- `postgres-cache`

HTTP reads are allowed through `/api/global/memory/read/{service}/{path}` only
for approved read paths such as `/health`, `/search`, `/stats`, catalog list
routes, receipts, and read-only graph/state views. Mutating paths such as
`/persist`, `/sync`, `/store`, `/add_node`, and create/update routes are blocked
by the global controller in this first memory slice.

Examples:

```powershell
Invoke-RestMethod http://localhost:8786/api/global/memory/upstreams
Invoke-RestMethod http://localhost:8786/api/global/memory/health
Invoke-RestMethod "http://localhost:8786/api/global/memory/read/pocket-memory-api/health"
Invoke-RestMethod "http://localhost:8786/api/global/memory/search?q=receipt"
```

## Current Static Surface

The global `memory` system currently aggregates:

- MMDB and memory MCP tools such as atom, family, receipt, and MDHG operations.
- FastAPI/Next routes matching memory, MMDB, atom, receipt, ledger, family, and
  MDHG evidence.
- Runtime port evidence from compose files and repo runtime hints.
- Repo-defined `SKILL.md` and `SKILLS.md` files matching the memory lane.

Same-name capabilities are accumulated, not overwritten. If multiple repos
define `query_atoms`, `insert_atom`, receipt logging, or family tools, the
global API returns every candidate with its module and local source path.

## Call Plan Examples

Memory query:

```powershell
$body = @{
  operation = 'query'
  name = 'query'
  arguments = @{ family = 'e8' }
  dry_run = $true
} | ConvertTo-Json -Depth 8

Invoke-RestMethod -Method Post `
  -Uri http://localhost:8786/api/global/memory/call-plan `
  -ContentType 'application/json' `
  -Body $body
```

Same-name tool aggregation:

```powershell
$body = @{
  operation = 'tool'
  name = 'query_atoms'
  dry_run = $true
} | ConvertTo-Json -Depth 8

Invoke-RestMethod -Method Post `
  -Uri http://localhost:8786/api/global/memory/call-plan `
  -ContentType 'application/json' `
  -Body $body
```

The result is a planning record only. Memory reads are routed only after health
checks, and memory writes/imports remain approval-gated.

## Next System Lane

Continue one system at a time:

1. Identify repos that expose the same service lane.
2. Aggregate all tools, routes, ports, and skills for that lane.
3. Normalize source and history references to `repo_kernel/repos/<module>/...`.
4. Define a global `/api/global/<system>` API and MCP mirror access.
5. Keep execution dry-run until a runtime slice is selected and approved.
