"""
NHyperTower integration — escrow stub until PENDING_REVIEW promotion.

Does not invent combinatorial tower bodies. Witness paths come from
``atomic_index.sqlite``; compose uses ``IndexSupervisor.tower_level`` only.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ATOMIC_INDEX = _REPO_ROOT / "data" / "atomic_index.sqlite"
_NHYPER_SQL = (
    "SELECT path FROM files "
    "WHERE path LIKE '%NHyperTower%' OR path LIKE '%nhyper%' "
    "ORDER BY path LIMIT ?"
)


@dataclass
class NHyperTowerState:
    """Crystal-manifest block for NHyper tower scheduling."""

    status: str = "escrow"
    tower_level: Optional[int] = None
    witness_paths: list[str] = field(default_factory=list)
    pending_review_path: str = "src/cmplx_pending/n/NHyperTower.py"

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "tower_level": self.tower_level,
            "witness_paths": self.witness_paths,
            "pending_review_path": self.pending_review_path,
            "note": (
                "Escrow: full NHyperTower body not merged. "
                "tower_level caps IndexSupervisor template depth when set."
            ),
        }


def query_nhyper_witness_paths(
    *,
    atomic_db: Path | str | None = None,
    limit: int = 20,
) -> list[str]:
    """Return indexed witness paths for NHyperTower (no filesystem walk)."""
    db_path = Path(atomic_db) if atomic_db else _DEFAULT_ATOMIC_INDEX
    if not db_path.is_file():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(_NHYPER_SQL, (int(limit),)).fetchall()
        return [str(r[0]) for r in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def build_nhyper_escrow_state(
    *,
    tower_level: Optional[int] = None,
    atomic_db: Path | str | None = None,
) -> NHyperTowerState:
    witnesses = query_nhyper_witness_paths(atomic_db=atomic_db)
    return NHyperTowerState(
        status="escrow",
        tower_level=tower_level,
        witness_paths=witnesses,
    )


def load_nhyper_from_manifest(manifest: dict[str, Any]) -> NHyperTowerState:
    block = manifest.get("nhyper_tower") or {}
    return NHyperTowerState(
        status=str(block.get("status", "escrow")),
        tower_level=block.get("tower_level"),
        witness_paths=list(block.get("witness_paths") or []),
        pending_review_path=str(
            block.get("pending_review_path", "src/cmplx_pending/n/NHyperTower.py")
        ),
    )


# Doctrine: tower level k schedules superpermutation at n = k + 4 (level 0 → n=4).
_TOWER_TO_ACTIVE_N: dict[int, int] = {0: 4, 1: 5, 2: 6, 3: 7, 4: 8}


def nhyper_active_n(tower_level: Optional[int]) -> int:
    """Map NHyper tower level to superpermutation alphabet size n."""
    if tower_level is None:
        return 4
    return _TOWER_TO_ACTIVE_N.get(int(tower_level), 4)


def active_n_from_manifest(
    manifest: dict[str, Any],
    *,
    tower_level: Optional[int] = None,
) -> int:
    """Resolve active_n: explicit manifest field, else tower_level → n table."""
    sp_block = manifest.get("superpermutation") or {}
    if sp_block.get("active_n") is not None:
        return int(sp_block["active_n"])
    level = tower_level
    if level is None:
        level = load_nhyper_from_manifest(manifest).tower_level
    if level is not None:
        return nhyper_active_n(level)
    return 4


def tower_level_for_supervisor(
    manifest: dict[str, Any],
    *,
    override: Optional[int] = None,
) -> Optional[int]:
    """
    Resolve ``tower_level`` for ``IndexSupervisor``.

    Escrow crystals may set a numeric cap; ``None`` means no filter.
    """
    if override is not None:
        return override
    state = load_nhyper_from_manifest(manifest)
    if state.status == "escrow" and state.tower_level is None:
        return None
    return state.tower_level


__all__ = [
    "NHyperTowerState",
    "active_n_from_manifest",
    "build_nhyper_escrow_state",
    "load_nhyper_from_manifest",
    "nhyper_active_n",
    "query_nhyper_witness_paths",
    "tower_level_for_supervisor",
]
