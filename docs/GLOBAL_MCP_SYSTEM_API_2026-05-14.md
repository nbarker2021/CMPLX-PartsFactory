# Global MCP System API

Generated: 2026-05-14

## Purpose

The first global system lane is `mcp`. It unifies MCP/tool surfaces across the
registered repos while preserving each repo's own checkout, settings, and local
path root.

The global API does not start runtimes and does not rewrite source. It reports a
consistent route, port, skill, and local-path map so the next pass can repath old
history references into `repo_kernel/repos/...`.

## API

General form:

- `GET /api/global-systems`
- `GET /api/global-systems/mcp`
- `GET /api/global-systems/mcp/tools`
- `GET /api/global-systems/mcp/routes`
- `GET /api/global-systems/mcp/ports`
- `GET /api/global-systems/mcp/skills`
- `POST /api/global-systems/mcp/call-plan`

Short alias:

- `GET /api/global/mcp`
- `GET /api/global/mcp/tools`
- `GET /api/global/mcp/routes`
- `GET /api/global/mcp/ports`
- `GET /api/global/mcp/skills`
- `POST /api/global/mcp/call-plan`

MCP mirrors:

- `repo_kernel_global_system`
- `repo_kernel_global_system_tools`
- `repo_kernel_global_system_skills`
- `repo_kernel_global_system_call_plan`

## Canonical Port Evidence

| Port | Source | Current Meaning |
| ---: | --- | --- |
| `8900` | `CMPLXMCP` and `CMPLXUNI` README evidence | MCP HTTP/SSE target or stdio bridge target; transport needs live bridge verification. |
| `8902` | `CMPLXUNI/THE_LIBRARY_DESIGN.md` | Library MCP chain service. |
| `11113` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-kb-mcp` compose service. |

## Current Static Surface

The global `mcp` system currently aggregates:

- MCP tools from all matching registered repo surfaces.
- FastAPI/Next routes matching MCP/tool/service keywords.
- Runtime port evidence from README and compose files.
- Repo-defined `SKILL.md` and `SKILLS.md` files matching the MCP lane.

Same-name capabilities are accumulated, not overwritten. If multiple repos
define the same tool or skill family, the global API returns all candidates with
their module and `repo_kernel/repos/<module>/...` local source path.

## Call Plan Example

```powershell
$body = @{
  operation = 'tool'
  name = 'l2_e8_project'
  arguments = @{ vector = @(1,2,3,4,5,6,7,8) }
  dry_run = $true
} | ConvertTo-Json -Depth 8

Invoke-RestMethod -Method Post `
  -Uri http://localhost:8786/api/global/mcp/call-plan `
  -ContentType 'application/json' `
  -Body $body
```

The result is a route/runtime plan only. Live MCP execution remains disabled
until the selected service is started, health-checked, and explicitly approved.

## Next System Lane

Repeat this same pattern one system at a time:

1. Identify repos that expose the same system/service lane.
2. Aggregate all tools, routes, ports, and skills for that lane.
3. Normalize local path references to `repo_kernel/repos/<module>/...`.
4. Define a global `/api/global/<system>` API.
5. Keep execution dry-run until a runtime slice is selected and approved.
