# Claude Prototype Evidence Bridge - 2026-05-14

Repo-kernel now treats `D:/PartsFactory/Unification Prototypes` as a read-only evidence source, not as a live runtime.

## New API

- `GET /api/prototype-evidence`
- `GET /api/prototype-evidence/docs?limit=50`
- `GET /api/prototype-evidence/bridges?limit=50`
- `GET /api/prototype-evidence/search?q=adapter`
- `GET /api/prototype-evidence/read?path=CLAIMS_VS_CODE.md`
- `GET /api/global/knowledge/prototype-claims?q=adapter`

MCP mirrors:

- `repo_kernel_prototype_evidence`
- `repo_kernel_prototype_evidence_docs`
- `repo_kernel_prototype_evidence_bridges`
- `repo_kernel_prototype_evidence_search`
- `repo_kernel_prototype_evidence_read`

## What It Uses

- `CLAIMS_VS_CODE.md` and `tools/<system>/docs/*.md` become knowledge-claim evidence.
- `bridges/<pair>/` and `_scripts/bridge_files.csv` become cross-system routing priority evidence.
- `STACKS.md` and `_scripts/phase4_stack_catalog.csv` become historical compose/runtime evidence.
- Generated `controller.py`, `api.py`, and `mcp_server.py` wrappers are marked superseded by repo-kernel `ModuleAdapter`.

## Current Local Findings

The prototype workspace is present at `D:/PartsFactory/Unification Prototypes`.

Observed high-signal artifacts:

- `_scripts/inventory.csv`
- `_scripts/bridge_files.csv`
- `_scripts/phase4_stack_catalog.csv`
- `_scripts/phase5_claims_detail.csv`
- `CLAIMS_VS_CODE.md`
- `STACKS.md`
- `tools/*/docs/*.md`
- `bridges/*`

The largest bridge pair observed locally is `cmplx_tmn`, followed by `cmplx_cqe_tmn`, `agrm_cmplx`, `agrm_mdhg`, and `aletheia_cqe`.

## Integration Rule

Repo-kernel remains the live control plane. Claude's prototype outputs are evidence lanes that help decide what to route, claim, compare, or promote next. They do not execute mutations and they do not replace the clean repo checkout adapters.

Prototype claims are now included in `/api/global/query` whenever the `knowledge` system is selected. These results use the same canonical result shape as other global query records, with `source=claude-unification-prototypes`.
