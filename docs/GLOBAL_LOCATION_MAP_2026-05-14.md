# Global Location Map

Generated: 2026-05-14

## Purpose

The global wrapper now has enough lanes that path, port, and hosted-location
ownership need a single control surface. The location map is that first layer.

It records where each global system should be addressed, which repo-local
folders contribute to it, which ports are canonical for the lane, and which
runtime ports were observed from compose or README evidence.

## API

- `GET /api/global-locations`
- `GET /api/global-locations/{system}`
- `GET /api/global/{system}/location`
- `GET /api/global-port-plan`
- `GET /api/global-runtime-slices`
- MCP tool `repo_kernel_global_location_map`
- MCP tool `repo_kernel_global_port_plan`
- MCP tool `repo_kernel_global_runtime_slices`

The map is intentionally planning-first. It does not move source, rewrite files,
start services, or claim a runtime is healthy. It gives the next pass a stable
target for those moves.

Port reassignment is also planning-first. The current control port is
`repo-kernel` on `8786`; existing service ports remain upstream evidence until a
system lane is selected, health-checked, and approved for a compose/runtime
change.

Runtime slice selection is exposed through `/api/global-runtime-slices`. It
ranks which live Docker-backed system should be routed next while still keeping
host port changes approval-gated.

The global hosted-path layer also has generic aliases:

- `GET /api/global/{system}`
- `GET /api/global/{system}/tools`
- `GET /api/global/{system}/routes`
- `GET /api/global/{system}/ports`
- `GET /api/global/{system}/skills`
- `POST /api/global/{system}/call-plan`

Existing explicit aliases such as `/api/global/memory` remain available. The
generic aliases are the reorganized hosted path for future lanes.

## Location Record Shape

Each system record includes:

- `hosted_locations`: canonical `/api/global/<system>` paths, generic
  `/api/global-systems/<system>` paths, and the repo-kernel controller file.
- `path_map`: contributing module roots under `repo_kernel/repos/<module>`.
- `port_map`: canonical port ownership plus observed runtime evidence.
- `move_plan`: the safe order for future path and hosting changes.

## Current Systems

The location map currently covers:

- `mcp`
- `memory`
- `agent-orchestration`
- `knowledge`
- `geometry`
- `training`
- `code-execution`
- `pipeline`
- `external-ai-portal`
- `formalization`
- `ai-runtime`
- `operations`
- `eventing`
- `community`
- `economy`
- `validation`
- `synthesis`
- `simulation`

## Reorganization Policy

The initial move is a routing move, not a source move:

1. Keep repo checkouts where they are under `repo_kernel/repos`.
2. Route callers through `/api/global/<system>`.
3. Use canonical ports as ownership targets.
4. Treat observed ports as evidence until selected and health-checked.
5. Rewrite stale historical paths to the location map before editing service
   code.
