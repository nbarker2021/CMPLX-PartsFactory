# Clean System Image Plan - 2026-05-14

The repo-kernel controller has done the first job: gather clean repo checkouts, live services, prototype evidence, docs, compose history, and control routes behind one API. That shape is useful for discovery, but it should not become the final product.

The next goal is one clean governed system image: a modular controller/runtime that absorbs the best capabilities from all prior repo states while preserving old repos as evidence and implementation sources until each part is promoted.

## Current Problem

The current `server.py` is intentionally dense because it gathered many concerns quickly:

- HTTP routes
- MCP tools
- request models
- repo adapters
- live-service adapters
- static activation adapters
- prototype evidence
- self-state
- route allowlists
- mutation policy text
- system contracts

That was acceptable for bootstrapping. It is not the desired long-term shape.

## Target Shape

The clean image should split into:

- `repo_kernel_app/main.py`
- `repo_kernel_app/models/`
- `repo_kernel_app/routes/`
- `repo_kernel_app/mcp_tools/`
- `repo_kernel_app/controllers/`
- `repo_kernel_app/adapters/`
- `repo_kernel_app/systems/`
- `repo_kernel_app/runtime/`
- `repo_kernel_app/evidence/`
- `repo_kernel_app/governance/`
- `repo_kernel_app/state/`

Public routes under `/api/global/<system>` should stay stable while the internal shape is cleaned.

## Source Truth Levels

1. Live control contract: repo-kernel routes currently served.
2. Live runtime observation: running Docker service read through repo-kernel.
3. Clean repo surface: static repo surfaces under `repo_kernel/repos`.
4. Prototype evidence: Claude/archaeological outputs for claims, bridges, and gaps.
5. Historical hint: old README, docs, compose, or path references not yet proven.

## Promotion Lanes

- Contract-first refactor: split `server.py` behind the same tests and routes.
- Capability canon: merge duplicate skills into canonical capability ids.
- Runtime canon: select live runtimes for MCP, agent orchestration, and code execution.
- Index and cache: persist compact route/tool/port/claim summaries.
- Governed execution: centralize mutation enforcement, dry-runs, approvals, and rollback evidence.

## First Moves

1. Keep `/api/clean-system-image-plan` as the shared plan endpoint.
2. Build a durable capability registry from global routes, prototype claims, and repo surfaces.
3. Extract low-coupling modules first: models, prototype evidence, static/live slice contracts.
4. Add compact surface caches for MCP, agent orchestration, and code execution.
5. Select one static slice runtime candidate for live promotion without enabling execution yet.
