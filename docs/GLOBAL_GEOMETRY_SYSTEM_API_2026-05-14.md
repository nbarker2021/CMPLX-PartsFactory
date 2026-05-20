# Global Geometry System API

Generated: 2026-05-14

## Purpose

The second live routed slice is `geometry`. It routes geometry, SNAP, MDHG,
tarpit atom, and unique-system evidence through `repo-kernel` while leaving the
underlying containers and host ports unchanged.

This is a read-only routing pass. Mutating geometry operations remain planning
only until a later write gate is approved.

## API

- `GET /api/global/geometry`
- `GET /api/global/geometry/tools`
- `GET /api/global/geometry/routes`
- `GET /api/global/geometry/ports`
- `GET /api/global/geometry/skills`
- `POST /api/global/geometry/call-plan`
- `GET /api/global/geometry/upstreams`
- `GET /api/global/geometry/health`
- `GET /api/global/geometry/read/{service}/{path}`

MCP mirrors:

- `repo_kernel_global_geometry_upstreams`
- `repo_kernel_global_geometry_read`

## Live Routed Upstreams

The current Docker-backed geometry slice is healthy behind repo-kernel:

- `snap-unified`
- `mdhg-unified`
- `tarpit-api`
- `unique-systems-api`

Approved read examples include:

- `snap-unified`: `/health`, `/taxonomy`, `/angles`, `/candidate`,
  `/evidence`, `/dna_snapshot`, `/metrics/*`, `/snap_state`
- `mdhg-unified`: `/health`, `/graph/{session_id}`, `/depth/{session_id}`,
  `/session/{session_id}`, `/planet/observe/{planet_id}`, `/planets`,
  `/universes`, `/dynamic/state/{session_id}`, `/chain/state/{chain_id}`
- `tarpit-api`: `/health`, `/atoms`, `/atoms/{atom_id}`, `/stats`
- `unique-systems-api`: `/`, `/health`, `/systems`, `/systems/{system_id}`,
  `/abilities`, `/promotion-states`, `/summary`

Blocked examples include `/process`, `/atomize`, `/add_node`,
`/planet/create`, `/universe/create`, `/store`, and other create/add/update
routes.

## Examples

```powershell
Invoke-RestMethod http://localhost:8786/api/global/geometry/upstreams
Invoke-RestMethod http://localhost:8786/api/global/geometry/health
Invoke-RestMethod http://localhost:8786/api/global/geometry/read/snap-unified/health
Invoke-RestMethod http://localhost:8786/api/global/geometry/read/unique-systems-api/summary
```

## Policy

1. Public callers use `repo-kernel` on port `8786`.
2. `repo-kernel` reaches upstreams over Docker-internal names.
3. Existing upstream ports and settings remain untouched.
4. GET reads are allowlisted.
5. Mutations remain call-plan only.
