# Global Static Control Slices - 2026-05-14

Repo-kernel now exposes the remaining high-risk systems through static control adapters:

- `mcp`
- `agent-orchestration`
- `code-execution`

These systems have large repo-discovered tool, route, and compose surfaces, but no single approved live runtime should be selected automatically. The controller therefore exposes evidence and activation candidates without executing anything.

## API

- `GET /api/global/{system}/upstreams`
- `GET /api/global/{system}/health`
- `GET /api/global/{system}/read/repo-kernel-adapter/summary`
- `GET /api/global/{system}/read/repo-kernel-adapter/ports`
- `GET /api/global/{system}/read/repo-kernel-adapter/activation-candidates`

## Policy

- MCP calls are still plan-only.
- Agent spawning/orchestration is still plan-only.
- Code execution and sandbox activation are still blocked.
- Candidate ports are evidence only until a specific runtime is selected and health-proved.

## Why Static First

The MCP and agent orchestration surfaces are large enough that full `/tools` reads can be slow. The static control slice gives the controller a fast, stable route for summaries and activation candidates while preserving the existing detailed surface APIs for deeper inspection.
