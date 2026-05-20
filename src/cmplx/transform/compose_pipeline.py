"""
compose_pipeline — supervisor (mutations) → shell.complete → optional forward.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .index_supervisor import IndexSupervisor
from .shell import MorphonShell
from .transformer import GeometricTransformer
from .types import TransformerOutput


@dataclass
class ComposeResult:
    partial: str
    candidates: list[str] = field(default_factory=list)
    supervisor: dict[str, Any] = field(default_factory=dict)
    forward: Optional[dict[str, Any]] = None
    admitted: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "partial": self.partial,
            "candidates": self.candidates,
            "supervisor": self.supervisor,
            "forward": self.forward,
            "admitted": self.admitted,
        }


def compose_pipeline(
    shell: MorphonShell,
    partial: str,
    *,
    supervisor: Optional[IndexSupervisor] = None,
    transformer: Optional[GeometricTransformer] = None,
    run_forward: bool = False,
    max_candidates: int = 32,
    crystal_manifest: Optional[dict] = None,
    tower_level: Optional[int] = None,
) -> ComposeResult:
    db_path = getattr(shell.store, "db_path", None)
    sup = supervisor
    if sup is None and db_path and crystal_manifest is not None:
        sup = IndexSupervisor.from_manifest(
            db_path,
            crystal_manifest,
            tower_level=tower_level,
        )
    elif sup is None and db_path:
        sup = IndexSupervisor.from_db(db_path, tower_level=tower_level)
    elif sup is None:
        sup = IndexSupervisor.from_db(":memory:")

    seed = partial[:8] if partial else None
    report = sup.walk(partial_seed=seed)
    candidates = shell.complete(partial, max_candidates=max_candidates)
    result = ComposeResult(
        partial=partial,
        candidates=candidates,
        supervisor=report.as_dict(),
        admitted=bool(candidates),
    )
    if run_forward and transformer is not None and candidates:
        token = candidates[0][:8].ljust(8, "a")
        admit = shell.admit(token)
        if admit.admitted:
            out: TransformerOutput = transformer.forward(token)
            result.forward = {
                "cache_key": out.cache_key,
                "ribbon_out": out.ribbon_out,
                "speedlight_hit": out.speedlight_hit,
            }
    return result


__all__ = ["ComposeResult", "compose_pipeline"]
