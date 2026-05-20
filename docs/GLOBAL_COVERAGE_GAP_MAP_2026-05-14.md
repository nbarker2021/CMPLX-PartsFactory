# Global Coverage Gap Map

Generated: 2026-05-14

## Purpose

The global merge now has a coverage layer. It compares discovered repo surfaces
against the known global systems and reports what is already assigned, what is
still unassigned, and what matches multiple systems.

This is the implementation-needs identifier for the combined bundle.

## API

- `GET /api/global-coverage`
- MCP tool `repo_kernel_global_coverage`

## What It Checks

For each selected registered repo, coverage evaluates:

- FastAPI routes
- Next.js API routes
- MCP tool declarations
- Runtime URL and compose/README port evidence

Each item is matched against the global system keyword sets. Unmatched items are
returned as `unassigned_samples`. Items matching more than one system are
returned as `multi_owner_samples`.

## Current Use

The first focused check across `CMPLXMCP`, `CMPLXUNI`, and `CMPLX-TMN-main`
showed a large unassigned cluster around formalization/proof/planner/channel
surfaces. That cluster is now owned by the `formalization` lane at
`/api/global/formalization`.

## Policy

Coverage is read-only. It does not move source, rewrite paths, start services,
or execute tools. It tells the next merge pass where a new lane, keyword update,
or routing-precedence decision is needed.
