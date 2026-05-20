# Control Layer Live State

Generated: 2026-05-14

## Current Control Layer

`repo-kernel` is the active global control layer.

- Container: `repo-kernel`
- Public port: `8786`
- Base URL: `http://localhost:8786`
- Health: `GET /api/health`
- Global location map: `GET /api/global-locations`
- Global coverage map: `GET /api/global-coverage`
- Port reassignment plan: `GET /api/global-port-plan`
- Runtime slice plan: `GET /api/global-runtime-slices`
- Live tool workbook: `GET /api/global-tool-workbook`
- Compact global state: `GET /api/global-state`
- Global query fanout: `GET /api/global/query`
- First routed slice: `GET /api/global/memory/upstreams`
- Second routed slice: `GET /api/global/geometry/upstreams`
- Third routed slice: `GET /api/global/operations/upstreams`
- Fourth routed slice: `GET /api/global/knowledge/upstreams`

## Compose Change

`docker-compose.repo-kernel.yml` now bind-mounts the local controller file into
the running container:

- source: `./services/repo-kernel/server.py`
- target: `/app/server.py`

The repo/source mounts remain separate:

- `./repo_kernel` -> `/kernel`
- `./reports` -> `/reports`
- `D:/PartsFactory` -> `/sources/PartsFactory`
- `D:/Manny Unification 2` -> `/sources/MannyUnification2`
- `D:/OC build` -> `/sources/OCbuild`

Restart `repo-kernel` after controller edits:

```powershell
docker compose -f docker-compose.repo-kernel.yml restart repo-kernel
```

## Port Policy

Ports have not been bulk-moved.

The plan is:

1. Freeze current service ports as upstream evidence.
2. Route public callers through `repo-kernel` on `8786`.
3. Use `/api/global/<system>` as the public control path for each system lane.
4. Select one runtime slice at a time with `/api/global-runtime-slices`.
5. Health-check that slice.
6. Reassign or hide upstream service ports only after explicit approval.

This keeps existing Docker services stable while the single control layer becomes
the routing authority.

## Verified Live Endpoints

The live Docker service exposes:

- `/api/global-locations`
- `/api/global-coverage`
- `/api/global-port-plan`
- `/api/global-runtime-slices`
- `/api/global-tool-workbook`
- `/api/global-state`
- `/api/global/query`
- `/api/global/{system}`
- `/api/global/{system}/location`
- `/api/global/memory/upstreams`
- `/api/global/memory/health`
- `/api/global/memory/read/{service}/{path}`
- `/api/global/geometry/upstreams`
- `/api/global/geometry/health`
- `/api/global/geometry/read/{service}/{path}`
- `/api/global/operations/upstreams`
- `/api/global/operations/health`
- `/api/global/operations/read/{service}/{path}`
- `/api/global/knowledge/upstreams`
- `/api/global/knowledge/health`
- `/api/global/knowledge/search`
- `/api/global/knowledge/read/{service}/{path}`

All-repo live coverage currently reports about `96%` assigned across the 10
eligible repos, excluding `CMPLX-PartsFactory` and `scout-demo-service`.

The first active routing slice is `memory`. It routes approved read-only calls
through `repo-kernel` while leaving all memory upstream ports and service
settings untouched.

The second active routing slice is `geometry`. It routes approved read-only
geometry/state calls through `repo-kernel` while leaving SNAP, MDHG, tarpit, and
unique-system upstream ports and service settings untouched.

The third active routing slice is `operations`. It routes approved read-only
control-plane status through `repo-kernel`, synthesizes repo-kernel self health
without recursive HTTP calls, and keeps GitNexus upstream ports/settings
untouched.

The fourth active routing slice is `knowledge`. It routes approved read-only
knowledge/search/catalog calls through `repo-kernel`, keeps Jupyter as disabled
evidence until fixed, and records API-layer needs in the route contract.

The live tool workbook is the active inventory for what I can use in live work:
`/api/global-tool-workbook`.

The first unified API-layer endpoint above the slices is live at
`/api/global/query`. It fans out read-only across memory, knowledge, geometry,
and operations.

The compact state endpoint is live at `/api/global-state`; it avoids slow
all-repo scans during ordinary live work.
