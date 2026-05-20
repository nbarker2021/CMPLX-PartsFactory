"""Integration tests for TokenToolPass with real TarPit/SNAP and geometry rows."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cmplx.primitives.core import NLAECNFChain
from cmplx.transform.token_geometry import TokenGeometryStore
from cmplx.transform.tool_pass import TokenToolPass
from cmplx.transform.translation_store import TranslationLinkStore


@pytest.fixture
def linked_db(tmp_path):
    db = str(tmp_path / "lib.sqlite")
    links = TranslationLinkStore(db)
    en = "baaaaaab"
    native = "baaaaaab"
    snap = str(NLAECNFChain.full_chain(en)["snap_key"])
    tkey = "doc:chunk:0"
    links.upsert(translation_key=tkey, stream="en", concat=en, snap_key=snap)
    links.upsert(translation_key=tkey, stream="native", concat=native, snap_key=snap)
    geom = TokenGeometryStore.from_connection(links._conn, db)
    tool = TokenToolPass(links, geometry=geom)
    yield db, tkey, tool, links, geom
    links.close()
    geom.close()


def test_tool_pass_tarpit_trace_in_receipt(linked_db):
    _db, tkey, tool, _links, _geom = linked_db
    with patch("cmplx.transform.tool_pass.has_provider", return_value=False):
        result = tool.run(tkey)
    tarpit = [r for r in result.receipts if r.step == "tarpit"]
    assert len(tarpit) >= 2
    assert tarpit[0].detail.get("trace_len", 0) >= 0
    assert "mean_mass" in tarpit[0].detail


def test_tool_pass_snap_labels(linked_db):
    _db, tkey, tool, _links, _geom = linked_db
    with patch("cmplx.transform.tool_pass.has_provider", return_value=False):
        result = tool.run(tkey)
    snap_steps = [r for r in result.receipts if r.step == "snap"]
    assert snap_steps
    assert "labels" in snap_steps[0].detail or "label_count" in snap_steps[0].detail


def test_geometry_rows_for_both_streams(linked_db):
    db, tkey, tool, _links, geom = linked_db
    with patch("cmplx.transform.tool_pass.has_provider", return_value=False):
        tool.run(tkey)
    assert geom.by_concat("baaaaaab", stream="en") is not None
    assert geom.by_concat("baaaaaab", stream="native") is not None


def test_tool_pass_from_db_factory(linked_db):
    db, tkey, _tool, _links, _geom = linked_db
    with patch("cmplx.transform.tool_pass.has_provider", return_value=False):
        runner = TokenToolPass.from_db(db)
        result = runner.run(tkey)
    assert result.receipts
