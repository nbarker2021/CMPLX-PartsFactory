# Repo Layout Survey — historical/promoted CMPLX-* builds

Source: `repo_kernel/repos/<name>`. Each repo's first level of directories, .py counts per top dir, and the conventional markers present.

## CMPLX

**Markers**: `README.md`, `pyproject.toml`, `setup.cfg`, `docker-compose.yml`, `tox.ini`, `.gitignore`, `AGENTS.md`

**Top-level files**: `.dockerignore`, `.env.example`, `.env.virtualdisks.example`, `AGENT-ACTIVITY-REVIEW.md`, `AUDIT-REPORT-VSCODE-DOCKER.md`, `CAPSULE-IMAGE-SYSTEM.md`, `CHATCONTROLLER-PORTAL-PLAN.md`, `CLAW-DOCKER-MANAGER-GUIDE.md`, `CMPLX-LOCAL-SETUP-GUIDE.md`, `CMPLX-TECHNICAL-SPECIFICATION.md` (+52 more)

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|
| `cmplx_submodules/` | 5760 |  |
| `core/` | 2794 |  |
| `deployment/` | 1 |  |
| `docker/` | 0 | DOCS |
| `LICENSES/` | 0 |  |
| `reference/` | 327 |  |
| `scripts/` | 1 |  |
| `src/` | 3433 |  |
| `tests/` | 11 | pkg TEST |
| `tools/` | 12 |  |

## CMPLX-1T

**Markers**: `README.md`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.gitignore`, `AGENTS.md`

**Top-level files**: `ARCHITECTURE-V5.md`, `CONTRIBUTING.md`, `DISCLAIMER.md`, `Dockerfile.polyglot`, `INDEX-V5.md`, `LICENSE.md`, `NAVIGATION.md`, `NOTICE`, `QUICKSTART-V5.md`, `README-DOCKER.md` (+5 more)

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|
| `archives/` | 0 |  |
| `checkpoints/` | 0 |  |
| `cmplx-1t-hook/` | 1 |  |
| `config/` | 0 |  |
| `configs/` | 0 |  |
| `data/` | 0 |  |
| `docker/` | 8986 | pkg DOCS |
| `docs/` | 11582 | DOCS |
| `document_output/` | 0 | DOCS |
| `home/` | 0 |  |
| `images/` | 1 |  |
| `intake-system/` | 3 |  |
| `LICENSES/` | 0 |  |
| `monitoring/` | 0 |  |
| `nginx/` | 0 |  |
| `organized/` | 0 |  |
| `pipeline/` | 24 | pkg main |
| `plans/` | 0 |  |
| `qwenwrapper/` | 0 |  |
| `reports/` | 0 |  |
| `repos/` | 10 |  |
| `scripts/` | 37 |  |
| `security-reports/` | 0 |  |
| `SHOWROOM/` | 14 |  |
| `src/` | 55 |  |
| `TODO/` | 0 |  |
| `toolkit/` | 0 |  |
| `Wolfram study/` | 62 | pkg server |

## CMPLX-Formalization

**Markers**: `README.md`, `.gitignore`, `AGENTS.md`

**Top-level files**: `CONTRIBUTING.md`, `DISCLAIMER.md`, `LICENSE.md`, `NOTICE`, `REUSE.toml`, `TODO.md`

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|
| `bibliography/` | 0 |  |
| `cross-cutting/` | 0 |  |
| `formal-specs/` | 0 |  |
| `geometric-design-principles/` | 0 |  |
| `LICENSES/` | 0 |  |
| `mathematical-framework/` | 0 |  |
| `papers/` | 0 |  |
| `presentations/` | 0 |  |
| `scripts/` | 0 |  |
| `semantic-reasoning-theory/` | 0 |  |
| `source-docs/` | 0 | DOCS |
| `templates/` | 0 |  |

## CMPLX-Manny

**Markers**: `.gitignore`, `AGENTS.md`

**Top-level files**: `INIT_RUNBOOK.md`, `Manny Unification 2.code-workspace`, `opencode.json`, `start-main-stack.ps1`, `status-main-stack.ps1`, `stop-main-stack.ps1`

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|
| `Working Prototyping/` | 5 |  |

## CMPLX-Monorepo

**Markers**: `README.md`, `.gitignore`, `AGENTS.md`

**Top-level files**: `# PC specs.txt`, `.env.example`, `.gitmodules`, `CONTRIBUTING.md`, `DISCLAIMER.md`, `LICENSE.md`, `NAVIGATION.md`, `NOTICE`, `REUSE.toml`, `TODO.md`

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|
| `backlog_adapters/` | 9 | pkg |
| `cqe_website/` | 385 | pkg __main__ server |
| `devkit/` | 2 |  |
| `docs/` | 7 | DOCS |
| `LICENSES/` | 0 |  |
| `mmdb/` | 0 |  |
| `plans/` | 0 |  |
| `product/` | 5 |  |
| `projects/` | 80 |  |
| `scripts/` | 0 |  |
| `services/` | 4 |  |
| `support/` | 1 |  |
| `tests/` | 2 | TEST |

## CMPLX-PartsFactory

**Markers**: (none)

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|

## CMPLX-TMN-main

**Markers**: `README.md`, `docker-compose.yml`, `.gitignore`, `CLAUDE.md`

**Top-level files**: `CONTRIBUTING.md`, `Dockerfile.base`, `LICENSE`

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|
| `capsules/` | 0 |  |
| `configs/` | 0 |  |
| `scripts/` | 2 |  |
| `src/` | 88 |  |

## CMPLX-TMN1

**Markers**: `README.md`, `.gitignore`, `CLAUDE.md`

**Top-level files**: `AUDIT_2026-03-26.txt`, `CONNECT.md`, `DESIGNERNOTE.md.md`, `LICENSE`, `PORTAL-API.md`, `TMN1-ARCHITECTURE.md`, `TMN1-CHANNELS.md`, `TMN1-DOCKER.md`, `TMN1-ECONOMY.md`, `TMN1-ECOSYSTEM.md` (+4 more)

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|
| `databases/` | 2 |  |
| `formalizations/` | 0 |  |
| `hooks/` | 1 |  |
| `infrastructure/` | 11 |  |
| `intake/` | 0 |  |
| `showcase/` | 0 |  |

## CMPLXDevKit

**Markers**: `README.md`, `.gitignore`

**Top-level files**: `CONTRIBUTING.md`, `DISCLAIMER.md`, `LICENSE.md`, `NAVIGATION.md`, `NOTICE`, `REUSE.toml`, `TODO.md`

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|
| `CMPLXDevKit/` | 47 |  |
| `CMPLXLOCALMCP/` | 47 |  |
| `devkit/` | 2 |  |
| `Handshake Entry-Build Guide/` | 0 |  |
| `LICENSES/` | 0 |  |
| `src/` | 4846 |  |

## CMPLXMCP

**Markers**: `README.md`, `setup.py`, `.gitignore`, `AGENTS.md`

**Top-level files**: `CONTRIBUTING.md`, `DISCLAIMER.md`, `LICENSE.md`, `NAVIGATION.md`, `NOTICE`, `REUSE.toml`, `TODO.md`, `__init__.py`, `__main__.py`, `chunk_limit_fix.py` (+6 more)

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|
| `adapters/` | 5 | pkg |
| `agrm_mdhg_integration/` | 5 | pkg |
| `agrm_snap/` | 40 | pkg |
| `client/` | 2 | pkg |
| `cmplx_integration/` | 4 | pkg |
| `codec/` | 2 | pkg |
| `controllers/` | 5 | pkg |
| `cqe_unified_family/` | 1 |  |
| `LICENSES/` | 0 |  |
| `modules/` | 3 | pkg |
| `polyglot/` | 5 |  |
| `server/` | 5 | pkg __main__ server |
| `universal/` | 6 | pkg |
| `validation/` | 7 | pkg |

## CMPLXUNI

**Markers**: `README.md`, `pyproject.toml`, `.gitignore`, `AGENTS.md`

**Top-level files**: `CMPLX_NEXTJS_ARCHITECTURE.md`, `CONTRIBUTING.md`, `DISCLAIMER.md`, `EXPANDED_SWARM_DOCUMENTATION.md`, `LICENSE.md`, `MCP_CONFIGURATION_GUIDE.md`, `MCP_SETUP_COMPLETE.md`, `NAVIGATION.md`, `NOTICE`, `REUSE.toml` (+10 more)

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|
| `cmplx-nextjs/` | 0 |  |
| `lfai/` | 19 | pkg |
| `LICENSES/` | 0 |  |
| `mmdb/` | 0 |  |
| `src/` | 2793 |  |
| `the-library/` | 1 |  |

## scout-demo-service

**Markers**: `README.md`, `Dockerfile`, `.gitignore`, `package.json`

**Top-level files**: `.dockerignore`, `.eslintrc`, `.gitattributes`, `app.js`

**Top-level dirs** (.py counts):

| Dir | .py count | Notes |
|---|---:|---|
