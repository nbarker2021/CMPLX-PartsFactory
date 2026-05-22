"""Worlds forge provider smoke — reduced depth, honest pass_with_open_gaps."""
from __future__ import annotations

import pytest

from cmplx.morphon import MorphonController
from cmplx.receipt.provider import ReceiptProvider
from cmplx.worlds.forge import WorldsForgeProvider


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


@pytest.fixture
def provider(tmp_path):
    return WorldsForgeProvider(root=tmp_path / "forge-overlay")


def test_health_seed_ok(provider):
    h = provider.health()
    assert h["status"] == "ok"
    assert h["seed_integrity"] == "ok"


def test_verify_proof_obligations_reduced_depth(provider):
    envelope = provider.verify_rule30_proof_obligations(
        max_depth=32,
        page_count=2,
        page_size=32,
        block_size=8,
        max_order=4,
        mint_receipt=False,
    )
    result = envelope["result"]
    assert result["status"] == "pass_with_open_gaps"
    blocking = result["release_summary"]["blocking_obligations"]
    assert "rule30.sheet_operator.power_law" in blocking
    assert "rule30.prize.depth_only_shortcut" in blocking


def test_mints_on_receipt_when_enabled(provider, monkeypatch):
    monkeypatch.setenv("FORGE_MINT_RECEIPT", "1")
    MorphonController.get().register("receipt", ReceiptProvider())
    provider.verify_rule30_proof_obligations(
        max_depth=32,
        page_size=32,
        page_count=2,
        mint_receipt=True,
    )
    chain = MorphonController.get().get_provider("receipt").chain
    assert len(chain._chain) >= 1


def test_bootstrap_registers_worlds(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from runtime.cmplx_bootstrap import register_all

    status = register_all()
    assert status["worlds"].startswith("registered")
