# Repo Kernel - 2026-05-13

The repo-kernel layer treats each `nbarker2021` GitHub repository as a clean,
manifest-pinned module. It avoids nesting those git histories into the active
PartsFactory workspace.

## Files

- Compose layer: `docker-compose.repo-kernel.yml`
- Service: `services/repo-kernel/server.py`
- Sync script: `scripts/repo_kernel_sync.py`
- Manifest: `repo_kernel/manifest/repos.json`
- Clean clones: `repo_kernel/repos/`

`repo_kernel/repos/*` is ignored by git so cloned repositories do not become
part of the PartsFactory repository.

## Running Service

The service is currently running as Docker container `repo-kernel`.

- REST API: `http://localhost:8786`
- Health: `http://localhost:8786/api/health`
- Modules: `http://localhost:8786/api/modules`
- MCP SSE: `http://localhost:8786/mcp/sse`

Start or rebuild:

```powershell
docker compose -f docker-compose.repo-kernel.yml up -d --build
```

Stop:

```powershell
docker compose -f docker-compose.repo-kernel.yml down
```

## Syncing Modules

Refresh GitHub metadata only:

```powershell
python scripts\repo_kernel_sync.py --manifest-only
```

Clone or fetch all modules and pin commits:

```powershell
python scripts\repo_kernel_sync.py --clone
```

Current status: 12/12 repos cloned and clean.

## API Shape

- `GET /api/modules`
- `GET /api/modules/{name}`
- `GET /api/modules/{name}/tree?path=.&max_depth=2`
- `GET /api/modules/{name}/file?path=README.md`
- `GET /api/modules/{name}/raw?path=README.md`
- `GET /api/modules/{name}/search?q=FastAPI&limit=5`
- `POST /api/controller/search`
- `POST /api/controller/compose-plan`

MCP tools:

- `repo_kernel_list_modules`
- `repo_kernel_inspect_module`
- `repo_kernel_module_tree`
- `repo_kernel_read_file`
- `repo_kernel_search`

## Notes

- Mutation is disabled by default: `REPO_KERNEL_ALLOW_MUTATION=0`.
- Runtime `git status` is disabled by default because large repos such as
  `CMPLX-1T` can exceed request-time budgets. The service trusts the manifest
  dirty state unless `REPO_KERNEL_RUNTIME_GIT_STATUS=1` is explicitly set.
- `CMPLX-1T` required `core.longpaths=true` for Windows checkout.
- `CMPLX-PartsFactory` cloned as an empty/no-commit GitHub repo; it has no pinned
  commit in the manifest.
