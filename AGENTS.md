# CMPLX-PartsFactory

Python multi-agent service framework with geometric computing, E8 routing, and manifold-based tool composition.

## Package Structure

src/
  cmplx/              # Public API (re-exports from submodules)
  catalog/            # SQLite artifact index + tool registry
  compose/            # Tool composition harness + templates
  composition/        # In-Python tool wiring and execution
  discovery/          # PostgreSQL/SQLite/filesystem discovery
  personal_node/      # Agent session + preference storage
  tools/              # Tool stubs and implementations

Entry: from cmplx import X (PYTHONPATH=src). Install with pip install -e ".[dev]".

## Development Commands

pip install -e ".[dev]"   # Install with pytest, mypy, black
pytest tests/             # Run smoke tests

## Docker Orchestration

Start-CMPLXStack.ps1      # Staged wave startup (Windows PowerShell)
Start-Simple.ps1          # Minimal startup
docker compose up -d --build
docker compose --profile full up -d --build  # + cognitive services
self-compose logs -f      # In-container helper

### Receipt Chain (slot-01, port 8010)

```powershell
docker compose -f docker-compose.receipt.yml up -d
curl http://localhost:8010/health
```

Env: `RECEIPT_STRICT_TYPES=0` (default permissive), `RECEIPT_STORAGE=memory`, optional `PG_URL`.

### SpeedLight Worldline (slot-04, port 8843)

```powershell
docker compose -f docker-compose.speedlight.yml up -d
curl http://localhost:8843/health
```

Env: `SPEEDLIGHT_MINT_RECEIPT=1` (POST mint on cache miss via receipt port), `SPEEDLIGHT_PORT=8843`.

Windows pytest (if runs hang): `$env:PYTHONPATH='src'; $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest tests/speedlight/ -q`

### TarPit symbolic (slot-18, port 8844)

```powershell
docker compose -f docker-compose.tarpit.yml up -d
curl http://localhost:8844/health
curl http://localhost:8844/canonical-forms
```

Env: `TARPIT_MINT_RECEIPT=1`, `TARPIT_PORT=8844`. Canonical forms: `evolving_tarpit`, `glyphic_tarpit`, `unified_tarpit` (see `identity_review/registers/tarpit-canonical-forms.md`).

### SNAP stratification (slot-17, port 8823)

```powershell
docker compose -f docker-compose.snap.yml up -d
curl http://localhost:8823/health
```

Env: `SNAP_MINT_RECEIPT=1` (POST/GATE/PROCESS on receipt port), `SNAP_PORT=8823`.

### Lattice Forge / worlds (slot-19, port 8845)

Dev canonical: `D:\PartsFactory\work\lattice-forge`. Git package: `packages/lattice-forge` (sync via `scripts/sync_lattice_forge_package.ps1`).

```powershell
pip install -e .\packages\lattice-forge
docker compose -f docker-compose.lattice-forge.yml up -d
curl http://localhost:8845/health
curl http://localhost:8845/rule30/proof-obligations/verify?max_depth=128&page_size=128
```

Port `worlds` via `cmplx.worlds.forge.WorldsForgeProvider`. Env: `FORGE_MINT_RECEIPT=1`, `LATTICE_FORGE_PORT=8845`, optional `FORGE_OVERLAY_ROOT`.

## Repo-Kernel Control Layer

Use `repo-kernel` as the canonical control plane for repo unification work.

- Start/restart: `docker compose -f docker-compose.repo-kernel.yml up -d --build`
- Health: `GET http://localhost:8786/api/health`
- Live workbook: `GET http://localhost:8786/api/global-tool-workbook`
- Compact state: `GET http://localhost:8786/api/global-state`
- GitNexus evidence: `GET http://localhost:8786/api/gitnexus/status`
- VS Code workspace: `CMPLX-PartsFactory.code-workspace`

Named read-only capabilities currently surfaced through the controller:

- `GET /api/global/knowledge/devkit-ingest`
- `GET /api/global/mcp/local-os`
- `GET /api/global/code-execution/octa64`
- `GET /api/global/validation/mcp-os`
- `GET /api/global/synthesis/cqe-modular`

Prefer `/api/global/...` controller routes over direct upstream ports. Use
`/call-plan` routes for execution or mutation intent until a promotion explicitly
enables runtime behavior.

Profiles: default | cognitive | bond | field | discord | full

## Three-Space Architecture

Space            Host                        Container
Creative yard    /mnt/d/PartsFactory         PartsFactory    rw
Evidence substrate /mnt/d/Manny Unification 2 MannyUnification2 ro
Design doctrine  /mnt/d/OC build             OCbuild         ro

## Available Skills

catalog-build      Rebuild catalog database from discovered tools
composition-test   Test tool compositions and record results
tool-discovery     Scan PostgreSQL/SQLite/filesystem for tools

## Hard Constraints

- Never edit /workspace/MannyUnification2 (read-only evidence)
- Never write to Postgres without approval
- Never deploy compose drafts without approval
- Never run destructive git commands

## Environment Setup

cp .env.template .env
# Set: NGROK_AUTHTOKEN, OPENCODE_SERVER_PASSWORD, DISCORD_BOT_TOKEN

## Key Files for Memory Review

work/unified/src/cmplx/cmplx_brain.py - Unified brain (48K lines)
work/unified/src/cmplx/memory.py - Lane-first memory (63K lines)
catalog/artifact_index.sqlite - Tool catalog
