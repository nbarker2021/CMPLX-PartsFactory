"""Repo-kernel MorphonicBridge import smoke (no HTTP)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from cmplx.transform.token_index import (
    CaseMode,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    any_filter,
)

_REPO = Path(__file__).resolve().parents[2]
_KERNEL = _REPO / "services" / "repo-kernel"
if str(_KERNEL) not in sys.path:
    sys.path.insert(0, str(_KERNEL))

from morphonic_bridge import MorphonicBridge  # noqa: E402


@pytest.fixture
def indexed_db(tmp_path):
    db = tmp_path / "token_index.sqlite"
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=(1, 2),
            alphabet=tuple("abcde"),
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=str(db),
            progress_every=0,
            max_entries=80,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    return db


def test_bridge_status_without_http(indexed_db: Path):
    bridge = MorphonicBridge(default_db=indexed_db)
    status = bridge.status()
    assert status["tool"] == "morphonic"
    assert status["db_exists"] is True
    assert "GET /api/morphonic/status" in status["safe_api"]["read_routes"]


def test_bridge_template_stats(indexed_db: Path):
    bridge = MorphonicBridge(default_db=indexed_db)
    out = bridge.template_stats()
    assert out["ok"] is True
    assert "report" in out


def test_bridge_crystal_info_missing_bundle(indexed_db: Path):
    missing = indexed_db.parent / "__no_such_crystal_bundle__"
    bridge = MorphonicBridge(default_db=indexed_db, default_crystal=missing)
    out = bridge.crystal_info()
    assert out["ok"] is False
