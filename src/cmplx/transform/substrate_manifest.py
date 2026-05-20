"""
Substrate manifest helpers — superpermutation + NHyper fields for crystals.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from cmplx.primitives.superperm import (
    all_statuses,
    coverage_checksum,
    load_superperm_record,
    octad_version,
    provenance_class,
    status_for_n,
    superperm_length,
)

from .nhyper_tower import build_nhyper_escrow_state, nhyper_active_n


def build_superpermutation_manifest_block(
    *,
    active_n: int = 4,
    tower_level: int | None = None,
) -> dict[str, Any]:
    n = int(active_n)
    if tower_level is not None:
        n = nhyper_active_n(tower_level)
    rec = load_superperm_record(n)
    sp_status = status_for_n(n)
    block: dict[str, Any] = {
        "active_n": n,
        "sp_length": rec.get("length") or (superperm_length(n) if sp_status == "validated" else None),
        "sp_checksum": rec.get("coverage_checksum") or (
            coverage_checksum(n=n) if sp_status == "validated" else None
        ),
        "provenance_class": rec.get("provenance_class") or provenance_class(n),
        "octad_version": octad_version(),
        "octad_layout": rec.get("octad_layout") or "1_palindrome_7_trees",
        "n4_status": status_for_n(4),
        "n5_status": status_for_n(5),
        "n6_status": status_for_n(6),
        "n7_status": status_for_n(7),
        "n8_status": status_for_n(8),
        "n4_length": load_superperm_record(4).get("length"),
        "n4_checksum": load_superperm_record(4).get("coverage_checksum"),
    }
    block.update(all_statuses())
    if n == 5 and sp_status == "validated":
        block["n5_octad_layout"] = rec.get("octad_layout") or "1_palindrome_7_trees"
        block["n5_alternate_count"] = rec.get("alternate_count")
        block["n5_tree_alternate_count"] = rec.get("tree_alternate_count", 7)
        block["n5_journal"] = rec.get("journal")
        labeled = rec.get("labeled_alternates") or []
        block["n5_alternate_labels"] = [e.get("label") for e in labeled]
        block["n5_palindrome_label"] = next(
            (e.get("label") for e in labeled if e.get("is_palindrome")), None
        )
    return block


def enrich_crystal_manifest(
    manifest: dict[str, Any],
    *,
    tower_level: int | None = None,
    active_n: int | None = None,
    atomic_db: Path | str | None = None,
) -> dict[str, Any]:
    """Attach superperm + NHyper blocks (in-place copy)."""
    out = dict(manifest)
    resolved_n = active_n
    if resolved_n is None and tower_level is not None:
        resolved_n = nhyper_active_n(tower_level)
    if resolved_n is None:
        sp_block = out.get("superpermutation") or {}
        resolved_n = sp_block.get("active_n", 4)
    out["superpermutation"] = build_superpermutation_manifest_block(
        active_n=int(resolved_n),
        tower_level=tower_level,
    )
    out["nhyper_tower"] = build_nhyper_escrow_state(
        tower_level=tower_level,
        atomic_db=atomic_db,
    ).as_dict()
    return out


__all__ = [
    "build_superpermutation_manifest_block",
    "enrich_crystal_manifest",
]
