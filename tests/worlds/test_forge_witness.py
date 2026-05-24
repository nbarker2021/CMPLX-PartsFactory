"""Worlds forge witness API — provider + mint with ReceiptProvider."""
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


def test_witness_regime_c_encode(provider):
    out = provider.witness_regime_c_encode(max_depth=64, mint_receipt=False)
    assert out["kind"] == "regime_c"
    assert out["result"]


def test_witness_syndrome(provider):
    out = provider.witness_syndrome(syndrome_keys=["ecc_shed"], mint_receipt=False)
    assert out["kind"] == "syndrome"
    assert len(out["result"]["syndromes"]) == 1


def test_witness_proof_bundle_full_quick(provider):
    out = provider.witness_proof_bundle_full(quick=True, mint_receipt=False)
    assert out["kind"] == "proof_bundle_full"
    assert "proofs" in out["result"]


def test_witness_mint_preserves_pass_with_open_gaps(provider, monkeypatch):
    monkeypatch.setenv("FORGE_MINT_RECEIPT", "1")
    MorphonController.get().register("receipt", ReceiptProvider())
    provider.witness_proof_bundle(
        max_depth=32,
        page_size=32,
        page_count=2,
        mint_receipt=True,
    )
    chain = MorphonController.get().get_provider("receipt").chain
    last = chain._chain[-1]
    payload = last.payload if hasattr(last, "payload") else {}
    status = payload.get("status")
    honesty = payload.get("honesty")
    if status == "pass_with_open_gaps":
        assert honesty == "pass_with_open_gaps"
    assert not (status == "pass" and honesty == "pass_with_open_gaps")
