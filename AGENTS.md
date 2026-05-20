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
