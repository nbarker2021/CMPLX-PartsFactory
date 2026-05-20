# Repo Kernel Adapter Registry

Generated: 2026-05-13

The repo-kernel now exposes each clean GitHub clone as a safe, read-only module
adapter. The adapter registry is the first promotion gate: modules are inspected,
cataloged, and called through bounded controller actions before any source is
copied into the master workspace.

## Endpoints

- `GET /api/adapters` lists all module adapters and safe actions.
- `GET /api/adapters/{name}` describes one adapter.
- `GET /api/adapters/{name}/surfaces` statically extracts FastAPI routes, MCP
  tools, and Next.js API routes.
- `POST /api/adapters/{name}/call` executes a safe delegated adapter action.

Safe actions:

- `probe`
- `promotion_plan`
- `surface_catalog`
- `search`
- `tree`
- `read_file`

Mutation remains disabled by default.

## First Promoted Adapters

| Module | Adapter | FastAPI Routes | MCP Tools | Next.js Routes | Status |
| --- | --- | ---: | ---: | ---: | --- |
| `CMPLXUNI` | `adapter-cmplxuni` | 176 | 83 | 8 | `adapter_ready` |
| `CMPLX-TMN-main` | `adapter-cmplx-tmn-main` | 633 | 0 | 0 | `adapter_ready` |
| `CMPLXMCP` | `adapter-cmplxmcp` | 14 | 34 | 0 | `adapter_ready` |

## Example Calls

```powershell
Invoke-RestMethod http://localhost:8786/api/adapters
```

```powershell
$body = @{ action='surface_catalog'; args=@{ limit=100 } } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8786/api/adapters/CMPLXUNI/call `
  -ContentType 'application/json' `
  -Body $body
```

```powershell
$body = @{ action='read_file'; args=@{ path='src/cmplx/mcp/mmdb_mcp_server.py'; max_bytes=2000 } } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8786/api/adapters/CMPLXUNI/call `
  -ContentType 'application/json' `
  -Body $body
```

## Promotion Rule

Promote behavior first. A module should pass adapter probes, expose useful
surfaces, and have a smokeable capability path before any internal source is
copied or rewritten into `CMPLX-PartsFactory`.

## Unified Memory Layer

The first workflow-specific API layer is live at `/api/unified/memory`.

It exposes memory capabilities, query plans, and receipt plans by combining:

- `CMPLXUNI` MMDB MCP tools
- `CMPLX-TMN-main` MMDB and receipt service ports/routes
- static adapter surfaces when runtime services are not running

The layer is read/planning-first. Write-capable tools are returned as candidates
only and are not executed automatically.

## Unified MCP Tools Layer

The second workflow-specific API layer is live at `/api/unified/mcp-tools`.

It exposes:

- tool capabilities and categories
- tool search/filter by category
- individual tool detail
- dry-run call plans

The controller currently treats geometric/layered tools as compute actions,
read-like tools as read actions, and insert/store/register/execute-style tools
as mutating. Mutating tools are not executed automatically.

## Runtime Issues

Operational checks are available at `/api/runtime/issues`.

Current known issue classes:

- uncertain README/runtime transport mappings
- no healthy live runtime for a workflow, causing static adapter fallback
- low-confidence manual startup commands
- package/dependency mismatches before direct runtime activation

## Unified Knowledge Layer

The fourth workflow-specific API layer is live at `/api/unified/knowledge`.

It exposes:

- knowledge capabilities by role
- search/retrieval/KB planning
- runtime preflight for knowledge services
- MCP mirrors for agent use

This is the preferred first stop for agentic discovery tasks involving corpus,
KB, semantic, retrieval, or code-context questions. It returns bounded route,
tool, and runtime candidates without starting services or writing indexes.
