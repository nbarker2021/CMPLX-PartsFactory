"""Additional coverage toward matrix completeness (deep pass)."""
from __future__ import annotations

import pytest

from cmplx.snap import (
    LegalityLens,
    LensBank,
    NoveltyLens,
    SNAPEngine,
    SNAPLabeler,
    SymmetryLens,
)
from cmplx.snap.gate369 import Body, Gate369Engine, Predicate


def test_lens_bank_has_four_named_lenses():
    bank = LensBank()
    names = set(bank.names())
    assert {"base", "legality", "novelty", "symmetry"}.issubset(names)


def test_lens_bank_best_lens_returns_instance():
    bank = LensBank()
    lens = bank.best_lens({"prefer": "novelty"})
    assert lens.name in bank.names()


def test_legality_lens_pass_without_violation():
    state = {"violates_policy": False, "mirror_pass": True, "polarity_conflict": 0.0, "containment_c": 0.9}
    assert LegalityLens().evaluate(state) == "pass"


def test_gate369_engine_history_grows():
    eng = Gate369Engine()
    eng.process([Body(id=str(i)) for i in range(6)], [Predicate(name="p")])
    assert len(eng.history) >= 3


def test_engine_crystallize_mints_ledger_and_verifies():
    eng = SNAPEngine()
    from cmplx.snap.gate369 import EnneadPackage

    eng.crystallize(EnneadPackage(facets=[Body(id=str(i)) for i in range(9)], containment_c=0.85))
    assert eng.ledger.verify()


def test_labeler_rule_count_positive():
    assert SNAPLabeler().rule_count > 5


@pytest.mark.parametrize("lens_cls", [NoveltyLens, SymmetryLens])
def test_specialized_lenses_instantiate(lens_cls):
    assert lens_cls().name


def test_snap_mint_receipt_env_off(monkeypatch):
    monkeypatch.setenv("SNAP_MINT_RECEIPT", "0")
    from cmplx.snap._receipt_bridge import snap_mint_receipt_enabled

    assert not snap_mint_receipt_enabled()


def test_snap_mint_receipt_env_on(monkeypatch):
    monkeypatch.setenv("SNAP_MINT_RECEIPT", "1")
    from cmplx.snap._receipt_bridge import snap_mint_receipt_enabled

    assert snap_mint_receipt_enabled()
