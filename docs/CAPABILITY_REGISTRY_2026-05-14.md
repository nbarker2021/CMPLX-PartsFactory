# Capability Registry - 2026-05-14

The clean system image needs a stable inventory of capabilities before code is moved. Repo-kernel now exposes that staging layer without beginning the refactor.

## API

- `GET /api/capability-registry`
- MCP mirror: `repo_kernel_capability_registry`

## Purpose

The registry turns current routed systems and static adapters into canonical capability records:

- stable capability id
- owning system
- current service or adapter
- read-path samples
- source-truth level
- safety policy
- promotion state

It also identifies shared services that appear in more than one system. Those are the first places where the clean image needs canonical contracts instead of duplicated or conflicting API shapes.

## Current Role

This is staging, not refactoring. The registry does not move code, start runtimes, execute tools, or promote implementations. It prepares the later clean image work by making duplicated and shared abilities visible.

## Promotion Lanes

- `merge_shared_services`: unify duplicate service capabilities behind canonical contracts.
- `define_capability_ids`: make every promoted ability addressable before code is moved.
- `attach_best_implementation`: choose the best repo/runtime implementation while preserving alternate evidence.
