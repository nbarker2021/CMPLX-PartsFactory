"""
Shell construction — the "reach" bounds for each MORSR stage.

A shell is a set of indices a pulse is allowed to touch from the
current state. Two modes:

  - **Radial**: indices within fractional radius
    `R = clip(base × factor^stage, 0, 1)` of the mask length.
  - **BFS-hop**: indices reachable from active indices within
    `hops = base × factor^stage` neighbor-steps.

Adapted from `CQE_MORSR_NewBest_v1/cqe_plus/morsr.py:_build_shell`.
"""
from __future__ import annotations

from enum import Enum
from typing import Iterable, Optional


class ShellMode(str, Enum):
    RADIAL = "radial"
    BFS = "bfs"


def build_shell(
    mode: ShellMode,
    mask_len: int,
    base: float,
    factor: int,
    stage: int,
    active_idxs: Optional[Iterable[int]] = None,
) -> tuple[set[int], dict]:
    """Return `(allowed_set, meta)`.

    `allowed_set` is the set of indices in `[0, mask_len)` permitted
    at this stage. `meta` is a small dict describing the shell shape
    (`{"R": float}` or `{"hops": int}`).
    """
    if mode == ShellMode.RADIAL:
        R = min(1.0, float(base) * (int(factor) ** int(stage)))
        # Indices whose normalized position is ≤ R land in the shell.
        # Empty mask edge case: return everything.
        if mask_len <= 1:
            return set(range(mask_len)), {"R": R}
        allowed = {
            i for i in range(mask_len)
            if (i / float(mask_len - 1)) <= R
        }
        return allowed, {"R": R}

    if mode == ShellMode.BFS:
        hops = max(0, int(round(float(base) * (int(factor) ** int(stage)))))
        actives = list(active_idxs or [])
        visited = set(actives)
        frontier = set(actives)
        for _ in range(hops):
            next_frontier: set[int] = set()
            for u in frontier:
                # Neighbor relation: ±1 in index space (the canonical form
                # from the source). Pluggable via subclassing this function.
                for v in (u - 1, u + 1):
                    if 0 <= v < mask_len and v not in visited:
                        visited.add(v)
                        next_frontier.add(v)
            if not next_frontier:
                break
            frontier = next_frontier
        return visited, {"hops": hops}

    raise ValueError(f"unknown shell mode: {mode!r}")


def in_shell(
    candidate_indices: Iterable[int],
    allowed: set[int],
) -> bool:
    """`True` iff every candidate index is in the allowed set."""
    return all(i in allowed for i in candidate_indices)
