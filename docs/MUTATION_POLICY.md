# Repo-Kernel Mutation Policy

Repo-kernel is read-only by default.

## Default Rule

All repo, source, prototype, workflow, and runtime adapters may inspect, list, search, plan, probe, and read approved paths. They must not write, import, delete, overwrite, re-path, rebuild, start, stop, migrate, promote, or execute generated wrappers unless mutation has been explicitly enabled and the specific operation has an approval path.

## Current Enforcement

- `REPO_KERNEL_ALLOW_MUTATION=0` is the default.
- Routed global slices expose approved read/search paths only.
- Mutating upstream paths return a safety block instead of being proxied.
- Promotion is represented as a plan and ledger candidate before any source move.
- Claude `Unification Prototypes` files are evidence only; generated wrappers are superseded by `ModuleAdapter` until manually promoted.

## Promotion Gate

A mutation can only move forward when all of these are true:

- The intended source and target paths are local and explicit.
- The action is represented in the promotion ledger or an equivalent review artifact.
- The controller exposes the operation as a dry-run plan first.
- The user explicitly asks for the mutation after seeing the plan.
- The operation can preserve or report rollback evidence.

## Port Rule

Existing service ports stay as upstream evidence while repo-kernel exposes canonical routes under `/api/global/<system>`. Port reassignment is deferred until each routed slice is stable behind the control layer.
