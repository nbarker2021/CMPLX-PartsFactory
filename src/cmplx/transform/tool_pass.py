"""
TokenToolPass — TarPit-first linked tool chain per translation_key.

Order: TarPit → NSL → SNAP → NLAECNF → cache (receipt stub per step).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

from cmplx.morphon import Morphon
from cmplx.primitives.core import NLAECNFChain
from cmplx.snap import SNAPEngine
from cmplx.symbolic.tarpit.provider import TarPitSymbolicProvider

from .bridge import get_cache_provider, get_receipt_provider, has_provider
from .e6_lift import lift_concat
from .metrics import compute_morph_signature
from .morph_signature_store import MorphSignatureStore, StoredMorphSignature
from .token_geometry import GeometryRow, TokenGeometryStore
from .translation_store import TranslationLinkStore


@dataclass
class ToolPassReceipt:
    step: str
    translation_key: str
    stream: str
    concat: str
    snap_key: str
    ok: bool
    detail: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class ToolPassResult:
    translation_key: str
    receipts: list[ToolPassReceipt] = field(default_factory=list)
    receipt_errors: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "translation_key": self.translation_key,
            "receipt_errors": self.receipt_errors,
            "receipts": [
                {
                    "step": r.step,
                    "stream": r.stream,
                    "concat": r.concat,
                    "snap_key": r.snap_key,
                    "ok": r.ok,
                    "detail": r.detail,
                }
                for r in self.receipts
            ],
        }


class TokenToolPass:
    """Run tool chain for all streams sharing a translation_key."""

    def __init__(
        self,
        links: TranslationLinkStore,
        *,
        geometry: Optional[TokenGeometryStore] = None,
        morph_sigs: Optional[MorphSignatureStore] = None,
        tarpit: Optional[TarPitSymbolicProvider] = None,
        snap: Optional[SNAPEngine] = None,
        strict_receipts: bool = False,
    ) -> None:
        self.links = links
        self.geometry = geometry
        self.morph_sigs = morph_sigs
        self.tarpit = tarpit or TarPitSymbolicProvider()
        self.snap = snap or SNAPEngine()
        self.strict_receipts = strict_receipts

    @classmethod
    def from_db(cls, db_path: str | Path) -> "TokenToolPass":
        links = TranslationLinkStore(db_path)
        geom = TokenGeometryStore.from_connection(links._conn, str(db_path))
        morph = MorphSignatureStore.from_connection(links._conn, str(db_path))
        return cls(links, geometry=geom, morph_sigs=morph)

    def run(
        self,
        translation_key: str,
        *,
        streams: Optional[Sequence[str]] = None,
    ) -> ToolPassResult:
        rows = self.links.by_translation_key(translation_key)
        if streams is not None:
            allowed = {str(s) for s in streams}
            rows = [r for r in rows if r.stream in allowed]
        result = ToolPassResult(translation_key=translation_key)
        en_concat: Optional[str] = None
        for row in rows:
            if row.stream == "en":
                en_concat = row.concat
            result.receipts.extend(
                self._run_one(row.stream, row.concat, translation_key, en_concat=en_concat)
            )
        return result

    def _run_one(
        self,
        stream: str,
        concat: str,
        translation_key: str,
        *,
        en_concat: Optional[str] = None,
    ) -> list[ToolPassReceipt]:
        canonical = NLAECNFChain.full_chain(concat)
        snap_key = str(canonical["snap_key"])
        receipts: list[ToolPassReceipt] = []
        if self.geometry is not None:
            witness = lift_concat(concat, translation_key=translation_key, stream=stream)
            self.geometry.upsert(
                GeometryRow(
                    concat=concat,
                    stream=stream,
                    snap_key=witness.snap_key,
                    e6_coords=witness.e6_coords,
                    e8_coords=witness.e8_coords,
                    translation_key=translation_key,
                )
            )
        if en_concat and stream != "en" and self.morph_sigs is not None:
            sig = compute_morph_signature(en_concat, concat)
            self.morph_sigs.upsert(
                StoredMorphSignature(
                    concat_base=en_concat,
                    concat_variant=concat,
                    generator="tool_pass",
                    delta_snap=sig.delta_snap,
                    delta_lane=int(sig.delta_lane),
                    delta_dr=sig.delta_dr,
                    verdict=sig.verdict,
                    payload=sig.as_dict(),
                )
            )
        for step in ("tarpit", "nsl", "snap", "nlaecnf", "cache"):
            ok, detail = self._execute_step(step, concat, canonical)
            receipts.append(
                ToolPassReceipt(
                    step=step,
                    translation_key=translation_key,
                    stream=stream,
                    concat=concat,
                    snap_key=snap_key,
                    ok=ok,
                    detail=detail,
                )
            )
            if has_provider("receipt"):
                try:
                    get_receipt_provider().mint(
                        receipt_type="PROCESS",
                        atom_id=concat,
                        operation=f"transform.tool_pass.{step}",
                        payload={"translation_key": translation_key, "stream": stream, **detail},
                    )
                except Exception as exc:
                    if self.strict_receipts:
                        raise RuntimeError(
                            f"receipt mint failed for {step}::{translation_key}"
                        ) from exc
        return receipts

    def _execute_step(self, step: str, concat: str, canonical: dict) -> tuple[bool, dict]:
        if step == "tarpit":
            morphon = Morphon.forge(payload={"concat": concat})
            report = self.tarpit.derive(morphon)
            summary = report.summary or {}
            if "final_mass" in summary:
                mass = float(summary["final_mass"])
            elif "mean_mass" in summary:
                mass = float(summary["mean_mass"])
            else:
                mass = 0.0
            return True, {
                "morphon_id": morphon.id,
                "final_mass": mass,
                "mean_mass": mass,
                "trace_len": len(report.trace),
                "halted": bool(summary.get("halted", False)),
            }
        if step == "nsl":
            return True, {"digital_root": int(canonical["digital_root"])}
        if step == "snap":
            label_result = self.snap.label(concat, key=concat, context={"concat": concat})
            labels = sorted(label_result.all_labels)
            if labels:
                self.snap.labeler.register_dynamic_label(str(canonical["snap_key"]), labels[0])
            return True, {
                "snap_key": str(canonical["snap_key"])[:32],
                "labels": labels[:8],
                "label_count": len(labels),
            }
        if step == "nlaecnf":
            return True, {"lane": str(canonical["lane"])}
        if step == "cache" and has_provider("cache"):
            key = f"tool_pass::{concat}"
            try:
                get_cache_provider().put(key, canonical)
                return True, {"cache_key": key}
            except Exception as exc:
                if self.strict_receipts:
                    raise RuntimeError(f"cache put failed for {concat}") from exc
                return False, {"error": str(exc)}
        return True, {"skipped": step == "cache"}


def run_tool_pass_batch(
    db_path: str | Path,
    *,
    max_keys: Optional[int] = None,
    streams: Optional[Sequence[str]] = None,
    strict_receipts: bool = False,
) -> dict[str, Any]:
    """Run tool-pass for distinct translation keys (bounded ops batch)."""
    runner = TokenToolPass.from_db(db_path)
    runner.strict_receipts = strict_receipts
    try:
        keys = runner.links.distinct_translation_keys(
            limit=max_keys if max_keys is not None else 10_000
        )
        if max_keys is not None:
            keys = keys[: int(max_keys)]
        results: list[dict[str, Any]] = []
        errors = 0
        for key in keys:
            try:
                out = runner.run(key, streams=streams)
                results.append(out.as_dict())
                if not all(r.ok for r in out.receipts):
                    errors += 1
            except Exception as exc:
                errors += 1
                if strict_receipts:
                    raise
                results.append(
                    {"translation_key": key, "error": str(exc), "receipt_errors": 1}
                )
        return {
            "keys_processed": len(keys),
            "step_errors": errors,
            "strict_receipts": strict_receipts,
            "results": results,
        }
    finally:
        if runner.geometry is not None:
            runner.geometry.close()
        runner.links.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cmplx.transform.tool_pass")
    parser.add_argument("--db", required=True, help="SQLite bundle with translation_links.")
    parser.add_argument(
        "--max-keys",
        type=int,
        default=None,
        help="Cap distinct translation_key batch size.",
    )
    parser.add_argument(
        "--streams",
        default="",
        help="Comma-separated streams to process (default: all).",
    )
    parser.add_argument(
        "--strict-receipts",
        action="store_true",
        help="Fail loud on receipt mint or cache errors.",
    )
    parser.add_argument(
        "--translation-key",
        default="",
        help="Run a single key instead of a batch.",
    )
    args = parser.parse_args(argv)
    streams = [s.strip() for s in args.streams.split(",") if s.strip()] or None
    if args.translation_key:
        runner = TokenToolPass.from_db(args.db)
        runner.strict_receipts = args.strict_receipts
        try:
            result = runner.run(args.translation_key, streams=streams)
        finally:
            if runner.geometry is not None:
                runner.geometry.close()
            runner.links.close()
        if args.strict_receipts and not all(r.ok for r in result.receipts):
            return 1
        json.dump(result.as_dict(), sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0
    report = run_tool_pass_batch(
        args.db,
        max_keys=args.max_keys,
        streams=streams,
        strict_receipts=args.strict_receipts,
    )
    json.dump(report, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0 if report.get("step_errors", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ToolPassReceipt",
    "ToolPassResult",
    "TokenToolPass",
    "run_tool_pass_batch",
    "main",
]
