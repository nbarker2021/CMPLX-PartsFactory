# Global Runtime Slice Plan

Generated: 2026-05-14

## Purpose

The global controller now has a next-step planner for routing live systems
behind `repo-kernel` before any port reassignment.

The planner combines:

- global system coverage from all selected registered repos
- canonical `/api/global/<system>` hosted paths
- current live Docker upstream evidence
- optional health checks for those upstreams

It is still planning-first. It does not edit compose files, move source folders,
or restart services.

The tool workbook is the companion inventory for live use. It records the
currently routed tools, example calls, safety blocks, and API-layer needs.

## API

- `GET /api/global-runtime-slices`
- `GET /api/global-tool-workbook`
- MCP tool `repo_kernel_global_runtime_slices`
- MCP tool `repo_kernel_global_tool_workbook`

Useful query parameters:

- `modules`: optional repeated repo module filter
- `check_health`: `false` by default; set `true` for live upstream probing
- `timeout_seconds`: health-check timeout
- `limit`: number of ranked systems to return

Example:

```text
GET /api/global-runtime-slices?limit=8
GET /api/global-runtime-slices?check_health=true&limit=6
```

## Current Ranked Slice

Using all eligible repos, the next best routing order is:

1. `memory` -> `/api/global/memory`
2. `geometry` -> `/api/global/geometry`
3. `knowledge` -> `/api/global/knowledge`
4. `operations` -> `/api/global/operations`
5. `ai-runtime` -> `/api/global/ai-runtime`

The planner ranks these first because they have current Docker upstreams and
meaningful discovered surface area. The first move for each is to health-check
the upstreams, then bind the healthy targets behind the global control endpoint.

## Live Health Snapshot

Health-checked against the current Docker stack with the fast working slice
`CMPLXUNI` + `CMPLX-TMN-main`:

- `memory`: ready, 6/6 upstreams healthy
- `geometry`: ready, 4/4 upstreams healthy
- `operations`: ready, 3/3 upstreams healthy
- `ai-runtime`: ready, 2/2 upstreams healthy
- `validation`: ready, 2/2 upstreams healthy
- `synthesis`: ready, 2/2 upstreams healthy
- `external-ai-portal`: ready, 2/2 upstreams healthy
- `knowledge`: ready for its enabled upstreams, 2/2 healthy; Jupyter evidence is
  disabled pending an explicit start/fix

The disabled knowledge evidence is `research-api-jupyter` at
`http://research-api:8888/`, which refused connections from the repo-kernel
container. The API side of `research-api` and `db-aggregator-api` are healthy.

## First Routed Slice

`memory` is now the first routed slice:

- `GET /api/global/memory/upstreams`
- `GET /api/global/memory/health`
- `GET /api/global/memory/search?q=<term>`
- `GET /api/global/memory/read/{service}/{path}`

This is read-only routing. The controller blocks mutating upstream paths and
keeps all upstream service ports unchanged.

## Second Routed Slice

`geometry` is now the second routed slice:

- `GET /api/global/geometry/upstreams`
- `GET /api/global/geometry/health`
- `GET /api/global/geometry/read/{service}/{path}`

This is also read-only routing. The controller routes safe geometry/state
queries to `snap-unified`, `mdhg-unified`, `tarpit-api`, and
`unique-systems-api`, while blocking create/add/process/update paths.

## Third Routed Slice

`operations` is now the third routed slice:

- `GET /api/global/operations/upstreams`
- `GET /api/global/operations/health`
- `GET /api/global/operations/read/{service}/{path}`

This is read-only control-plane routing. `repo-kernel` self health is returned
in-process to avoid recursive HTTP calls, `gitnexus-rebuild-web` can expose its
SPA root, and `gitnexus-rebuild-server` is health-tracked but not read-proxied
until a clean safe backend status route is identified.

## Fourth Routed Slice

`knowledge` is now the fourth routed slice:

- `GET /api/global/knowledge/upstreams`
- `GET /api/global/knowledge/health`
- `GET /api/global/knowledge/search?q=<term>`
- `GET /api/global/knowledge/read/{service}/{path}`

This is read-only knowledge/catalog routing over the enabled `research-api` and
`db-aggregator-api` upstreams. The route contract carries API-layer needs for
canonical search response design, research API endpoint discovery, and the
disabled `research-api-jupyter` evidence.

## Port Policy

No bulk port moves.

The activation order is:

1. Keep the existing container host ports in place.
2. Route the selected system through `repo-kernel` on public port `8786`.
3. Verify the selected `/api/global/<system>` path.
4. Only then decide whether upstream host ports should be hidden, reassigned, or
   kept as internal compose-local evidence.

This lets the merge continue one system at a time without destabilizing the
currently running Docker stack.
