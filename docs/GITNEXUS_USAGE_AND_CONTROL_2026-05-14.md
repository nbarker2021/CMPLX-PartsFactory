# GitNexus Usage And Control

GitNexus is now treated as a read-only evidence lane behind `repo-kernel`.

## Current Runtime

- Server container: `gitnexus-rebuild-server`
- Host port: `4747`
- Web container: `gitnexus-rebuild-web`
- Web host port: `4173`
- Public control layer: `repo-kernel` on `8786`

Callers should prefer the repo-kernel routes:

- `GET /api/gitnexus/status`
- `GET /api/gitnexus/repos`
- `GET /api/gitnexus/repos/{repo}`
- `GET /api/gitnexus/graph-summary?repo=cmplx-partsfactory-root`
- `GET /api/gitnexus/unification-hints`
- `GET /api/gitnexus/repo-unification-worklist`
- `GET /api/gitnexus/slice-candidates?module=CMPLXDevKit`
- `GET /api/gitnexus/slice-candidate-matrix`
- `GET /api/gitnexus/slice-intake-plan?module=CMPLXDevKit&path=src/octa64`
- `GET /api/repo-unification-worklist`
- `GET /api/adapters/CMPLXDevKit/slice-candidates`
- `GET /api/adapters/CMPLXDevKit/slice-intake-plan?path=src/octa64`
- `GET /api/global/code-execution/slices`
- `GET /api/global/code-execution/slices/cmplxdevkit-code-execution-runtime-slice-src-octa64`
- `GET /api/global/code-execution/slices/cmplxdevkit-code-execution-runtime-slice-src-octa64/tree`
- `GET /api/global/code-execution/octa64`
- `GET /api/global/code-execution/octa64/tree`
- `GET /api/global/code-execution/octa64/files/pack.py`
- `POST /api/global/code-execution/octa64/call-plan`
- `GET /api/global/validation/mcp-os`
- `GET /api/global/validation/mcp-os/tree`
- `GET /api/global/validation/mcp-os/files/system_validator.py`
- `POST /api/global/validation/mcp-os/call-plan`
- `GET /api/global/synthesis/cqe-modular`
- `GET /api/global/synthesis/cqe-modular/tree`
- `GET /api/global/synthesis/cqe-modular/files/cqe_sdk.py`
- `POST /api/global/synthesis/cqe-modular/call-plan`
- `GET /api/global/knowledge/devkit-ingest`
- `GET /api/global/knowledge/devkit-ingest/tree`
- `GET /api/global/knowledge/devkit-ingest/files/ingest/ocr_pipeline.py`
- `POST /api/global/knowledge/devkit-ingest/call-plan`
- `GET /api/global/mcp/local-os`
- `GET /api/global/mcp/local-os/tree`
- `GET /api/global/mcp/local-os/files/MCP_OS_INVENTORY.md`
- `POST /api/global/mcp/local-os/call-plan`
- `GET /api/gitnexus/grep?repo=cmplx-partsfactory-root&pattern=GlobalSystemController`
- `GET /api/gitnexus/aggregate`
- `GET /api/gitnexus/aggregate/search?q=memory&limit=10`

## What It Adds

GitNexus provides graph evidence over the active PartsFactory controller and repo-kernel checkouts. The local aggregate database also carries historical report evidence from earlier Manny/Aletheia/CQE review work.

Use it before broad scans to answer:

- Which repos are already indexed?
- Which repos have the largest graph surfaces?
- Which class/function/process/community lanes exist for a repo?
- Which historical reports claim a capability exists?
- Which names appear in more than one system and should be unified under one canonical API?

## Indexed Evidence Observed

The live GitNexus container lists 17 indexed repos, including:

- `cmplx-partsfactory-root`
- `rk-cmplxuni`
- `rk-cmplx-tmn-main`
- `rk-cmplxmcp`
- `rk-cmplx-monorepo`
- `rk-cmplxdevkit`
- `rk-cmplx-manny`
- `rk-cmplx-tmn1`
- `rk-cmplx-formalization`
- historical Manny/Aletheia/CQE report and source indexes

The aggregate report DB at `data/gitnexus_index.sqlite` currently indexes 1,985 historical reports across `cmplx-tmn1`, `cqe`, `aletheia`, and `cmplx-tmn2`.

## Policy

Allowed through repo-kernel:

- GitNexus info and repo inventory
- Canned read-only graph summaries
- Grep over indexed repos
- Local aggregate report summaries and searches
- Derived unification hints that rank large repo graphs and repeated historical names
- Repo-aware unification worklists that join GitNexus aliases to repo-kernel modules, promotion status, adapter ids, and next safe reads
- Bounded slice candidates for noisy repos such as `CMPLXDevKit`, separating promotable tool slices from quarantine evidence
- System-grouped slice matrices and intake plans for turning a selected path into a canonical API capability
- Generic canonical slice routes under `/api/global/<system>/slices` for read-only summary, tree, and call-plan exposure
- Named canonical capability routes such as `/api/global/code-execution/octa64` once a slice is promoted into a specific system lane
- Named validation capability routes such as `/api/global/validation/mcp-os` for suite catalogs, diagnostics evidence, and plan-only activation gates
- Named synthesis capability routes such as `/api/global/synthesis/cqe-modular` for bounded CQE module catalogs and deterministic activation planning
- Named knowledge ingest routes such as `/api/global/knowledge/devkit-ingest` for OCR, embedding/index, and Qwen intake planning
- Named MCP catalog routes such as `/api/global/mcp/local-os` for local MCP server/client/proxy/tool-registry planning
- Historical GitNexus report matches in `/api/global/query` knowledge results

Blocked through repo-kernel:

- `analyze`
- `index`
- `clean`
- `remove`
- `augment`
- embedding generation
- raw graph export as a default path
- write Cypher or other mutation-like graph commands

GitNexus is evidence, not runtime authority. It should guide routing, promotion, gap checks, and later clean-system refactoring, while repo-kernel remains the canonical API and governance layer.
