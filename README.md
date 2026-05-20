# CMPLX-PartsFactory

Unified CMPLX build: `src/cmplx/` landing pad (attractor frame), services, repo-kernel control plane, and tests.

## Quick start

```powershell
pip install -e ".[dev]"
pytest tests/ -q
docker compose -f docker-compose.repo-kernel.yml up -d
```

Repo-kernel health: `http://localhost:8786/api/health`

## What ships in git

Tracked: `src/cmplx/`, `services/`, `repo_kernel/` (manifest only), `tests/`, `docs/`, compose files, `pyproject.toml`.

Not tracked (local catalogs / iteration trail): `CMPLX-1T/`, `CMPLX-Manny/`, `CMPLXUNI/`, `staging/`, `data/*.sqlite` — see `.gitignore`.

## IDE

Open **`CMPLX-PartsFactory.code-workspace`** (or this folder alone) for fast Pyright indexing.  
Do not open the full `D:\PartsFactory` tree as the workspace root unless you need curation work there.

See `docs/GIT_PUBLISHING.md` for first push checklist.
