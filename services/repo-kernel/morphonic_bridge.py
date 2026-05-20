"""Read-only Morphonic substrate bridge for repo-kernel."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional


def _cmplx_src() -> Path:
    env = os.environ.get("CMPLX_PARTS_FACTORY_SRC")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "src"


def _ensure_cmplx_import() -> None:
    src = _cmplx_src()
    src_s = str(src)
    if src_s not in sys.path:
        sys.path.insert(0, src_s)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_token_index_db() -> Path:
    env = os.environ.get("MORPHONIC_TOKEN_INDEX_DB")
    if env:
        return Path(env)
    return _repo_root() / "data" / "token_index_identity_review.sqlite"


def _default_crystal_bundle() -> Path:
    env = os.environ.get("MORPHONIC_CRYSTAL_BUNDLE")
    if env:
        return Path(env)
    return _repo_root() / "crystals" / "identity_review.crystal"


class MorphonicBridge:
    """Read-only crystal / template-stats queries (no mutation routes)."""

    READ_ROUTES = [
        "GET /api/morphonic/status",
        "GET /api/morphonic/crystal-info",
        "GET /api/morphonic/template-stats",
    ]

    def __init__(
        self,
        *,
        default_db: Path | None = None,
        default_crystal: Path | None = None,
    ) -> None:
        self.default_db = default_db or _default_token_index_db()
        self.default_crystal = default_crystal or _default_crystal_bundle()

    def status(self) -> dict[str, Any]:
        src = _cmplx_src()
        db_ok = self.default_db.is_file()
        return {
            "tool": "morphonic",
            "status": "ready" if src.is_dir() and db_ok else "degraded",
            "cmplx_src": str(src),
            "default_db": str(self.default_db),
            "db_exists": db_ok,
            "safe_api": {
                "read_routes": self.READ_ROUTES,
                "write": "not routed — use cmplx.transform CLI for ingest/refine",
            },
        }

    def template_stats(self, db: Optional[str | Path] = None) -> dict[str, Any]:
        path = Path(db) if db else self.default_db
        if not path.is_file():
            return {"ok": False, "error": f"db not found: {path}"}
        _ensure_cmplx_import()
        from cmplx.transform.token_index.template_frame import template_report

        return {"ok": True, "db": str(path), "report": template_report(path)}

    def crystal_info(self, bundle: Optional[str | Path] = None) -> dict[str, Any]:
        bundle_path = Path(bundle) if bundle else self.default_crystal
        if not bundle_path or str(bundle_path) in ("", ".") or not bundle_path.exists():
            return {
                "ok": False,
                "error": "bundle path required (query ?bundle= or MORPHONIC_CRYSTAL_BUNDLE)",
            }
        _ensure_cmplx_import()
        from cmplx.transform.crystal_pack import CrystalPackager

        return {"ok": True, "bundle": str(bundle_path), "info": CrystalPackager.info(bundle_path)}


__all__ = ["MorphonicBridge"]
