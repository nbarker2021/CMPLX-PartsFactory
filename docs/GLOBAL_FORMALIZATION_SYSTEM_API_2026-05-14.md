# Global Formalization System API

Generated: 2026-05-14

## Purpose

The `formalization` lane owns proof, theorem, axiom, planner, octet, unfold,
handshake, and formal property surfaces that were previously showing up as
unassigned coverage gaps.

This lane is part of the merge/unification pass: coverage identified the gap,
then the global controller gained a canonical system for it.

## API

- `GET /api/global/formalization`
- `GET /api/global/formalization/tools`
- `GET /api/global/formalization/routes`
- `GET /api/global/formalization/ports`
- `GET /api/global/formalization/skills`
- `POST /api/global/formalization/call-plan`

The generic forms also work:

- `GET /api/global-systems/formalization`
- `GET /api/global/formalization/location`
- MCP tool `repo_kernel_global_system` with `system = "formalization"`
- MCP tool `repo_kernel_global_coverage`

## Current Role

The first concrete surfaces are from `CMPLXUNI` LFAI routes such as:

- `/octet/run`
- `/unfold/run`
- `/planner/run`
- `/planner/config`
- `/proof/state`
- `/handshake/start`
- `/channel/prefire`
- `/channel/post`
- `/channel/finish`

`CMPLX-Formalization` remains the source/document evidence repo for this lane,
while extracted live route surfaces currently come from implementation repos
such as `CMPLXUNI`.

## Policy

Formalization routes remain planning-only through the global controller. Live
proof/planner execution needs a selected runtime, health check, and explicit
approval.
