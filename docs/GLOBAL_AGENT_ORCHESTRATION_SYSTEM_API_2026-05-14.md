# Global Agent Orchestration System API

Generated: 2026-05-14

## Purpose

The third global system lane is `agent-orchestration`. It unifies identity,
cooperation, daemon, thinktank, spawn, agent-manager, agent UI, and quorum-style
surfaces across registered repos while preserving every repo's own checkout and
settings.

This is a controller and planning layer. It does not spawn agents, start
services, register identities, or mutate agent state. Same-name capabilities are
returned as multiple candidates with module and local path evidence.

## API

General form:

- `GET /api/global-systems`
- `GET /api/global-systems/agent-orchestration`
- `GET /api/global-systems/agent-orchestration/tools`
- `GET /api/global-systems/agent-orchestration/routes`
- `GET /api/global-systems/agent-orchestration/ports`
- `GET /api/global-systems/agent-orchestration/skills`
- `POST /api/global-systems/agent-orchestration/call-plan`

Short alias:

- `GET /api/global/agent-orchestration`
- `GET /api/global/agent-orchestration/tools`
- `GET /api/global/agent-orchestration/routes`
- `GET /api/global/agent-orchestration/ports`
- `GET /api/global/agent-orchestration/skills`
- `POST /api/global/agent-orchestration/call-plan`

MCP mirrors:

- `repo_kernel_global_system` with `system = "agent-orchestration"`
- `repo_kernel_global_system_tools` with `system = "agent-orchestration"`
- `repo_kernel_global_system_skills` with `system = "agent-orchestration"`
- `repo_kernel_global_system_call_plan` with `system = "agent-orchestration"`

## Canonical Port Evidence

| Port | Source | Current Meaning |
| ---: | --- | --- |
| `11030` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-identity` service. |
| `11031` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-coop` cooperation service. |
| `11032` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-daemon` daemon service. |
| `11040` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-thinktank` service. |
| `11161` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-agent-manager` service. |
| `11197` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-spawn` service. |
| `11200` | `CMPLX-TMN-main/docker-compose.yml` | `tmn2-agent` service. |
| `11300` | `CMPLX-TMN-main/README.md` | CMPLXCode agent UI evidence. |

## Current Static Surface

The global `agent-orchestration` system currently aggregates:

- Agent, identity, spawn, daemon, cooperation, thinktank, and quorum tools.
- FastAPI/Next routes matching agent orchestration keywords.
- Runtime port evidence from compose files and README hints.
- Repo-defined `SKILL.md` and `SKILLS.md` files matching the orchestration lane.

The `plan` operation delegates to the existing unified agent orchestration
planner, then reports candidate routes, tools, runtime targets, health checks,
and mutation risk without executing anything.

## Call Plan Example

```powershell
$body = @{
  operation = 'plan'
  name = 'spawn a cooperative coding agent'
  arguments = @{ role = 'spawn' }
  dry_run = $true
} | ConvertTo-Json -Depth 8

Invoke-RestMethod -Method Post `
  -Uri http://localhost:8786/api/global/agent-orchestration/call-plan `
  -ContentType 'application/json' `
  -Body $body
```

The result is a planning record only. Spawn, register, assign, start, stop, and
other mutating orchestration actions remain approval-gated.

## Next System Lane

Continue one system at a time:

1. Identify repos that expose the same service lane.
2. Aggregate all tools, routes, ports, and skills for that lane.
3. Normalize source and history references to `repo_kernel/repos/<module>/...`.
4. Define a global `/api/global/<system>` API and MCP mirror access.
5. Keep execution dry-run until a runtime slice is selected and approved.
