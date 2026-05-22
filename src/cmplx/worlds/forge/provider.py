"""
WorldsForgeProvider — the `worlds` port (slot-19 lattice-forge).

Thin wrapper over the installable ``lattice_forge.Forge`` package. Rule 30 and
ledger logic stay in ``packages/lattice-forge``; this module wires bootstrap,
receipt minting, and optional HTTP manufacturing.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Optional

from ._receipt_bridge import mint_forge_operation


class WorldsForgeProvider:
    """The `worlds` port — Rule 30 witness + admissibility API."""

    name: str = "worlds_forge_provider"

    def __init__(self, root: str | Path | None = None) -> None:
        from lattice_forge import Forge

        if root is None:
            root = os.environ.get(
                "FORGE_OVERLAY_ROOT",
                Path(tempfile.gettempdir()) / "cmplx-forge-overlay",
            )
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._forge = Forge.open(self._root)

    @property
    def forge(self) -> Any:
        return self._forge

    def health(self) -> dict[str, Any]:
        status = self._forge.status()
        return {
            "status": "ok",
            "provider": self.name,
            "seed_integrity": status.get("seed_integrity"),
            "overlay_root": str(self._root),
        }

    def status(self) -> dict[str, Any]:
        return self._forge.status()

    def verify_rule30_proof_obligations(
        self,
        max_depth: int = 128,
        page_count: int = 2,
        page_size: int = 128,
        block_size: int = 8,
        max_order: int = 4,
        *,
        mint_receipt: bool = True,
    ) -> dict[str, Any]:
        envelope = self._forge.verify_rule30_proof_obligations(
            max_depth=max_depth,
            page_count=page_count,
            page_size=page_size,
            block_size=block_size,
            max_order=max_order,
        )
        result = envelope.get("result", envelope)
        if mint_receipt:
            mint_forge_operation(
                "verify_rule30_proof_obligations",
                {
                    "status": result.get("status"),
                    "open_gap_count": result.get("open_gap_count"),
                    "blocking": (result.get("release_summary") or {}).get(
                        "blocking_obligations"
                    ),
                    "max_depth": max_depth,
                    "page_size": page_size,
                },
                atom_id="rule30_proof_obligation_ledger",
            )
        return envelope

    def rule30_proof_obligations(
        self,
        max_depth: int = 128,
        page_count: int = 2,
        page_size: int = 128,
        block_size: int = 8,
        max_order: int = 4,
    ) -> dict[str, Any]:
        return self._forge.rule30_proof_obligations(
            max_depth=max_depth,
            page_count=page_count,
            page_size=page_size,
            block_size=block_size,
            max_order=max_order,
        )

    def verify_morphonics(self) -> dict[str, Any]:
        envelope = self._forge.verify_morphonics()
        result = envelope.get("result", envelope)
        mint_forge_operation(
            "verify_morphonics",
            {"status": result.get("status")},
            atom_id="morphonics_model",
        )
        return envelope
