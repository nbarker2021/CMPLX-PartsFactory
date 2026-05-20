# Repo-Kernel Workfront

Generated: 2026-05-13

## Purpose

This project must not collapse into one tool lane. The workfront keeps multiple
active lanes visible so agents rotate between memory, source cleanup, workflow
promotion, runtime preflight, and broader evidence intake.

## API

- `GET /api/self/workfront`
- MCP tool `repo_kernel_workfront`

## Active Lanes

| Lane | Status | Current Direction |
| --- | --- | --- |
| `source_universe_cleanup` | approval-gated | Review exact duplicate archive policy before any archive/delete action. |
| `memory_import` | design-ready, write-gated | MMDB recipe exists; local staging adapter is next only after approval. |
| `workflow_promotion` | ready for next controller | `knowledge` is implemented; promote `code_execution` next with strict execute guardrails. |
| `runtime_activation` | blocked until selected | Compose remains evidence; do not start non-kernel services without approval. |
| `evidence_intake` | ongoing | Continue bounded inventories, archive manifests, marker scans, and read-only probes across all mounted roots. |

## Rotation

Recommended rotation:

1. Finish one bounded memory/staging planning slice.
2. Use the implemented knowledge workflow controller for bounded agentic search/retrieval planning.
3. Review source cleanup approval policy.
4. Run a fresh evidence intake slice from another source root.
5. Promote the `code_execution` workflow controller with execute/mutation gates.
6. Consider runtime activation only after a service slice is selected and approved.

## Implemented Knowledge Surface

Use these before broad manual scans when the task is about search, retrieval,
KBs, corpus contents, semantic context, or code-context discovery:

- `GET /api/unified/knowledge/capabilities`
- `POST /api/unified/knowledge/plan`
- `GET /api/unified/knowledge/runtime-preflight`
- MCP tools `repo_kernel_knowledge_capabilities`,
  `repo_kernel_knowledge_plan`, and
  `repo_kernel_knowledge_runtime_preflight`

The controller is plan-only. Runtime services are treated as compose/README
evidence until explicitly selected and approved.

## Guardrail

Any future assistant should check the workfront before deepening a single tool
line. The goal is one unified operating substrate, not a pile of excellent but
isolated helpers.
