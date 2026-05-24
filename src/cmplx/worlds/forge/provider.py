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

    def witness_classify(
        self,
        *,
        source_id: str | None = None,
        target_id: str | None = None,
        morphism_id: str | None = None,
        mint_receipt: bool = True,
    ) -> dict[str, Any]:
        from lattice_forge.witness import WitnessEngine

        envelope = WitnessEngine(self._forge).classify(
            source_id=source_id,
            target_id=target_id,
            morphism_id=morphism_id,
        )
        if mint_receipt:
            mint_forge_operation(
                "witness_classify",
                {"status": envelope.get("status"), "honesty": envelope.get("honesty")},
                atom_id="lf_witness",
            )
        return envelope

    def witness_regime_a_query(
        self,
        *,
        n: int,
        max_depth: int = 4096,
        base_page: int = 64,
        mint_receipt: bool = True,
    ) -> dict[str, Any]:
        from lattice_forge.witness import WitnessEngine

        envelope = WitnessEngine(self._forge).regime_a_query(
            n=n,
            max_depth=max_depth,
            base_page=base_page,
        )
        if mint_receipt:
            mint_forge_operation(
                "witness_regime_a_query",
                {"status": envelope.get("status"), "n": n, "honesty": envelope.get("honesty")},
                atom_id="lf_regime_a",
            )
        return envelope

    def witness_proof_bundle(
        self,
        max_depth: int = 128,
        page_count: int = 2,
        page_size: int = 128,
        block_size: int = 8,
        max_order: int = 4,
        *,
        verify: bool = True,
        mint_receipt: bool = True,
    ) -> dict[str, Any]:
        from lattice_forge.witness import WitnessEngine

        envelope = WitnessEngine(self._forge).proof_bundle(
            max_depth=max_depth,
            page_count=page_count,
            page_size=page_size,
            block_size=block_size,
            max_order=max_order,
            verify=verify,
        )
        if mint_receipt:
            status = envelope.get("status", "")
            mint_forge_operation(
                "witness_proof_bundle",
                {
                    "status": status,
                    "honesty": envelope.get("honesty"),
                    "open_gap_count": (envelope.get("result", {}).get("result") or {}).get(
                        "open_gap_count"
                    ),
                },
                atom_id="rule30_proof_obligation_ledger",
            )
        return envelope

    def witness_regime_c_encode(
        self,
        *,
        max_depth: int = 512,
        mint_receipt: bool = False,
    ) -> dict[str, Any]:
        from lattice_forge.witness import WitnessEngine

        envelope = WitnessEngine(self._forge).regime_c_encode(max_depth=max_depth)
        if mint_receipt:
            mint_forge_operation(
                "witness_regime_c_encode",
                {"status": envelope.get("status"), "max_depth": max_depth},
                atom_id="lf_regime_c",
            )
        return envelope

    def witness_regime_cprime_encode(
        self,
        *,
        max_depth: int = 512,
        mint_receipt: bool = False,
    ) -> dict[str, Any]:
        from lattice_forge.witness import WitnessEngine

        envelope = WitnessEngine(self._forge).regime_cprime_encode(max_depth=max_depth)
        if mint_receipt:
            mint_forge_operation(
                "witness_regime_cprime_encode",
                {"status": envelope.get("status"), "max_depth": max_depth},
                atom_id="lf_regime_cprime",
            )
        return envelope

    def witness_syndrome(
        self,
        *,
        syndrome_keys: list[str] | None = None,
        mint_receipt: bool = False,
    ) -> dict[str, Any]:
        from lattice_forge.witness import WitnessEngine

        envelope = WitnessEngine(self._forge).syndrome_report(syndrome_keys=syndrome_keys)
        if mint_receipt:
            mint_forge_operation(
                "witness_syndrome",
                {"status": envelope.get("status")},
                atom_id="lf_witness",
            )
        return envelope

    def witness_proof_bundle_full(
        self,
        *,
        quick: bool = False,
        max_depth: int | None = None,
        mint_receipt: bool = True,
    ) -> dict[str, Any]:
        from lattice_forge.witness import WitnessEngine

        envelope = WitnessEngine(self._forge).proof_bundle_full(
            quick=quick, max_depth=max_depth
        )
        if mint_receipt:
            mint_forge_operation(
                "witness_proof_bundle_full",
                {
                    "status": envelope.get("status"),
                    "honesty": envelope.get("honesty"),
                },
                atom_id="rule30_proof_obligation_ledger",
            )
        return envelope
