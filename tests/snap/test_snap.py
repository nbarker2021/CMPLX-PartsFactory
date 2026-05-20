"""
Tests for cmplx.snap — labels, labeler, lenses, gate369, ledger,
provider.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import MorphonController
from cmplx.snap import (
    BaseLens,
    Body,
    EnneadPackage,
    Gate369Engine,
    LabelRule,
    LegalityLens,
    LensBank,
    NoveltyLens,
    Predicate,
    SNAPEngine,
    SNAPLabel,
    SNAPLabeler,
    SNAPLedger,
    SNAPRole,
    SymmetryLens,
)


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# SNAPLabel + SNAPRole
# ---------------------------------------------------------------------------

def test_snap_role_enum_values():
    assert SNAPRole.INPUT.value == "input"
    assert SNAPRole.TRANSFORM.value == "transform"


def test_snap_label_all_labels_unions_dimensions():
    lbl = SNAPLabel(
        item_key="x",
        structural={"class"},
        domain={"e8"},
        custom={"role": {"input"}},
    )
    assert lbl.all_labels == {"class", "e8", "input"}


def test_snap_label_has_returns_membership():
    lbl = SNAPLabel(item_key="x", quality={"documented"})
    assert lbl.has("documented")
    assert not lbl.has("untyped")


def test_snap_label_to_dict_sorts():
    lbl = SNAPLabel(item_key="x", semantic={"b", "a"})
    d = lbl.to_dict()
    assert d["semantic"] == ["a", "b"]


# ---------------------------------------------------------------------------
# SNAPLabeler — builtin rules
# ---------------------------------------------------------------------------

def test_labeler_labels_string():
    labeler = SNAPLabeler()
    lbl = labeler.label("hello world", key="greet")
    assert "string" in lbl.structural
    assert "text" in lbl.structural


def test_labeler_labels_dict():
    labeler = SNAPLabeler()
    lbl = labeler.label({"k": 1}, key="d")
    assert "dict" in lbl.structural
    assert "mapping" in lbl.structural


def test_labeler_labels_class():
    labeler = SNAPLabeler()
    lbl = labeler.label(int, key="int")
    assert "class" in lbl.structural


def test_labeler_domain_match_via_text_context():
    labeler = SNAPLabeler()
    lbl = labeler.label("text about e8 lattice", key="t1")
    assert "e8" in lbl.domain


def test_labeler_domain_match_multiple_in_one_text():
    labeler = SNAPLabeler()
    lbl = labeler.label("morphon and leech_lattice and conservation", key="t2")
    assert "morphonic" in lbl.domain
    assert "leech" in lbl.domain
    assert "conservation" in lbl.domain


def test_labeler_quality_documented():
    labeler = SNAPLabeler()
    def well_documented():
        """A docstring."""
        return 1
    lbl = labeler.label(well_documented, key="fn")
    assert "documented" in lbl.quality


def test_labeler_risk_exec_string():
    labeler = SNAPLabeler()
    lbl = labeler.label("result = exec(code)", key="risky")
    assert "uses_exec" in lbl.risk
    assert "security_relevant" in lbl.risk


def test_labeler_custom_dimension_via_rule():
    labeler = SNAPLabeler()
    labeler.add_rule(LabelRule(
        name="always_starred",
        dimension="custom:starred",
        labels=["yes"],
        matcher=lambda it, _: True,
    ))
    lbl = labeler.label("anything", key="x")
    assert lbl.custom.get("starred") == {"yes"}


def test_labeler_caches_results():
    labeler = SNAPLabeler()
    lbl = labeler.label("hello", key="cached")
    assert labeler.get_cached("cached") is lbl


def test_labeler_query_by_label():
    labeler = SNAPLabeler()
    labeler.label({"k": 1}, key="d1")
    labeler.label("text e8 lattice", key="t1")
    hits = labeler.query_by_label("dict")
    assert any(h.item_key == "d1" for h in hits)
    assert not any(h.item_key == "t1" for h in hits)


def test_labeler_buggy_rule_doesnt_crash():
    labeler = SNAPLabeler()
    labeler.add_rule(LabelRule(
        name="explosive",
        dimension="structural",
        labels=["boom"],
        matcher=lambda it, _: 1 / 0,  # ZeroDivisionError
    ))
    lbl = labeler.label("ok", key="resilient")
    # Builtin string rule still fired
    assert "string" in lbl.structural
    assert "boom" not in lbl.structural


# ---------------------------------------------------------------------------
# Lenses
# ---------------------------------------------------------------------------

def test_base_lens_pass_when_thresholds_met():
    lens = BaseLens()
    state = {
        "mirror_pass": True,
        "polarity_conflict": 0.1,
        "containment_c": 0.8,
    }
    assert lens.evaluate(state) == "pass"


def test_base_lens_refine_when_no_mirror():
    assert BaseLens().evaluate({}) == "refine"


def test_base_lens_refine_when_conflict_too_high():
    state = {
        "mirror_pass": True,
        "polarity_conflict": 0.5,
        "containment_c": 0.8,
    }
    assert BaseLens().evaluate(state) == "refine"


def test_legality_lens_fails_on_policy():
    assert LegalityLens().evaluate({"violates_policy": True}) == "fail"


def test_novelty_lens_bonus():
    base = BaseLens().score_reward({}, {"delta_u": 1.0})
    nov = NoveltyLens().score_reward({}, {"delta_u": 1.0, "novelty": 0.5})
    assert nov > base


def test_symmetry_lens_bonus():
    base = BaseLens().score_reward({}, {"delta_u": 1.0})
    sym = SymmetryLens().score_reward({}, {"delta_u": 1.0, "symmetry_score": 0.4})
    assert sym > base


def test_lens_bank_default_has_four_lenses():
    bank = LensBank()
    assert set(bank.names()) == {"base", "legality", "novelty", "symmetry"}


def test_lens_bank_best_lens_routes_by_state():
    bank = LensBank()
    assert bank.best_lens({"violates_policy": True}).name == "legality"
    assert bank.best_lens({"novelty": 0.5}).name == "novelty"
    assert bank.best_lens({"symmetry_score": 0.6}).name == "symmetry"
    assert bank.best_lens({}).name == "base"


def test_base_lens_pick_predicate_requires_candidates():
    with pytest.raises(ValueError):
        BaseLens().pick_predicate([], {})


def test_base_lens_pick_predicate_orders_by_expected_du_per_cost():
    p1 = Predicate(name="p1", meta={"expected_du": 1.0}, cost=10.0)
    p2 = Predicate(name="p2", meta={"expected_du": 5.0}, cost=1.0)
    picked = BaseLens().pick_predicate([p1, p2], {})
    assert picked is p2


# ---------------------------------------------------------------------------
# Gate369Engine
# ---------------------------------------------------------------------------

def _bodies(n: int) -> list[Body]:
    return [Body(id=f"b{i}", payload=i) for i in range(n)]


def test_gate369_triad_yields_three_members():
    eng = Gate369Engine()
    rec = eng.triad(_bodies(5),
                    [Predicate(name="p", meta={"expected_du": 1.0})],
                    state={"mirror_pass": True})
    assert rec.kind == "triad"
    assert len(rec.members) == 3


def test_gate369_triad_handles_fewer_than_three():
    eng = Gate369Engine()
    rec = eng.triad(_bodies(2), [Predicate(name="p")])
    assert len(rec.members) == 2


def test_gate369_hexad_pairs_records():
    eng = Gate369Engine()
    r1 = eng.triad(_bodies(3), [Predicate(name="p")])
    r2 = eng.triad(_bodies(3), [Predicate(name="q")])
    invariants = eng.hexad([r1, r2])
    assert len(invariants) == 1


def test_gate369_ennead_caps_at_nine_facets():
    eng = Gate369Engine()
    records = [
        eng.triad(_bodies(5), [Predicate(name="p")]) for _ in range(5)
    ]
    package = eng.ennead(records)
    assert len(package.facets) <= 9


def test_gate369_process_full_pipeline():
    eng = Gate369Engine()
    bodies = _bodies(9)
    predicates = [Predicate(name="p", meta={"expected_du": 1.0})]
    trace = eng.process(bodies, predicates)
    assert "triad" in trace
    assert "hexad" in trace
    assert "ennead" in trace
    assert "crystallized" in trace["ennead"]
    assert len(eng.history) == 3


def test_gate369_history_records_each_gate():
    eng = Gate369Engine()
    eng.process(_bodies(6), [Predicate(name="p")])
    gates = [h["gate"] for h in eng.history]
    assert gates == [3, 6, 9]


# ---------------------------------------------------------------------------
# SNAPLedger
# ---------------------------------------------------------------------------

def test_ledger_starts_empty_with_genesis_head():
    ledger = SNAPLedger()
    assert ledger.length == 0
    assert ledger.head == SNAPLedger.GENESIS_HASH


def test_ledger_append_chains_hashes():
    ledger = SNAPLedger()
    tx1 = ledger.append("op1", {"k": 1})
    tx2 = ledger.append("op2", {"k": 2})
    assert tx1.prev_hash == SNAPLedger.GENESIS_HASH
    assert tx2.prev_hash == tx1.hash
    assert ledger.head == tx2.hash


def test_ledger_verify_passes_on_clean_chain():
    ledger = SNAPLedger()
    for i in range(5):
        ledger.append("op", {"i": i})
    assert ledger.verify() is True


def test_ledger_verify_fails_on_tampered_entry():
    ledger = SNAPLedger()
    ledger.append("a", {})
    ledger.append("b", {})
    # Tamper: replace an entry with mutated payload but old hash
    bad = ledger.entries()[0]
    object.__setattr__(bad, "op", "MUTATED")
    # frozen=True so we used object.__setattr__; ledger now corrupt
    assert ledger.verify() is False


# ---------------------------------------------------------------------------
# SNAPEngine (provider)
# ---------------------------------------------------------------------------

def test_engine_label_records_transaction():
    eng = SNAPEngine()
    before = eng.ledger.length
    eng.label("text e8", key="t")
    assert eng.ledger.length == before + 1
    assert eng.ledger.entries()[-1].op == "label"


def test_engine_process_gate369_records_transaction():
    eng = SNAPEngine()
    bodies = _bodies(6)
    preds = [Predicate(name="p")]
    eng.process_gate369(bodies, preds)
    assert eng.ledger.entries()[-1].op == "gate369"


def test_engine_crystallize_records_transaction():
    eng = SNAPEngine()
    ennead = EnneadPackage(facets=_bodies(9), containment_c=0.9)
    tx = eng.crystallize(ennead)
    assert tx.op == "crystallize"
    assert tx.payload["containment_c"] == 0.9


def test_engine_ledger_verifies_after_operations():
    eng = SNAPEngine()
    eng.label("a", key="a")
    eng.process_gate369(_bodies(3), [Predicate(name="p")])
    assert eng.ledger.verify() is True


def test_engine_registers_on_snap_port():
    mc = MorphonController.get()
    eng = SNAPEngine()
    mc.register("snap", eng)
    assert mc.get_provider("snap") is eng


def test_engine_health_reports_subsystem_state():
    eng = SNAPEngine()
    h = eng.health
    assert h["rules"] > 0
    assert h["lenses"] == 4
    assert h["ledger_length"] == 0
