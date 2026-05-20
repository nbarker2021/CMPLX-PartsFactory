"""
Tests for cmplx.nsl — Noether-Shannon-Landauer conservation scalar.
"""
from __future__ import annotations

import math

import pytest

from cmplx.morphon import MorphonController
from cmplx.nsl import (
    BOLTZMANN_K,
    COUPLING,
    CheckResult,
    DEFAULT_TEMPERATURE,
    GateDecision,
    GateMode,
    LEECH_DIM,
    NSLLedger,
    NSLProvider,
    NSLReceipt,
    NSLSectors,
    NSLTriads,
    TOLERANCE,
    TRIAD_DIM,
    delta_phi,
    enforce_conservation,
    gate,
    is_conserved,
    landauer_cost,
    potential,
    shannon_bound,
)


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# Phi primitives
# ---------------------------------------------------------------------------

def test_constants_have_canonical_values():
    assert COUPLING == 0.030076
    assert TOLERANCE == 1e-10
    assert BOLTZMANN_K == 1.380649e-23
    assert DEFAULT_TEMPERATURE == 300.0


def test_potential_zero_vector_is_zero():
    assert potential([0.0] * 8) == 0.0


def test_potential_unit_vector_is_one_half():
    assert potential([1.0, 0.0, 0.0]) == pytest.approx(0.5)


def test_potential_general():
    # ||(3,4)||² = 25, Φ = 12.5
    assert potential([3.0, 4.0]) == pytest.approx(12.5)


def test_delta_phi_zero_for_same_vector():
    v = [1.0, 2.0, 3.0]
    assert delta_phi(v, v) == 0.0


def test_delta_phi_negative_when_norm_decreases():
    assert delta_phi([2.0, 0.0], [1.0, 0.0]) < 0


def test_delta_phi_positive_when_norm_increases():
    assert delta_phi([1.0, 0.0], [2.0, 0.0]) > 0


def test_shannon_bound_zero_vec_is_zero():
    assert shannon_bound([0.0] * 8) == 0.0


def test_shannon_bound_log2_norm_plus_one():
    # ||v||² = 3 → H = log2(4) = 2
    assert shannon_bound([math.sqrt(3), 0.0]) == pytest.approx(2.0)


def test_landauer_cost_is_positive():
    assert landauer_cost(-1.5) > 0


def test_landauer_cost_uses_abs_delta_phi():
    assert landauer_cost(1.0) == landauer_cost(-1.0)


def test_landauer_cost_formula():
    # E = k_B × T × |ΔΦ|
    assert landauer_cost(2.0, 300.0) == pytest.approx(BOLTZMANN_K * 300.0 * 2.0)


# ---------------------------------------------------------------------------
# Enforce conservation
# ---------------------------------------------------------------------------

def test_enforce_passes_through_conserved():
    v_before = [2.0, 0.0]
    v_after = [1.0, 0.0]  # smaller norm → ΔΦ < 0 → conserved
    adjusted, was_adjusted = enforce_conservation(v_before, v_after)
    assert tuple(adjusted) == (1.0, 0.0)
    assert was_adjusted is False


def test_enforce_scales_down_when_violated():
    v_before = [1.0, 0.0]
    v_after = [3.0, 0.0]  # ΔΦ > 0 → adjust
    adjusted, was_adjusted = enforce_conservation(v_before, v_after)
    assert was_adjusted is True
    # adjusted norm² should == before norm² == 1
    norm_sq = sum(x * x for x in adjusted)
    assert norm_sq == pytest.approx(1.0)


def test_enforce_zero_before_returns_zero():
    adjusted, was_adjusted = enforce_conservation([0.0, 0.0], [3.0, 4.0])
    assert tuple(adjusted) == (0.0, 0.0)
    assert was_adjusted is True


def test_is_conserved():
    assert is_conserved([2.0], [1.0])
    assert not is_conserved([1.0], [2.0])


# ---------------------------------------------------------------------------
# NSLSectors
# ---------------------------------------------------------------------------

def test_sectors_total_is_sum():
    s = NSLSectors(dN=-0.5, dI=0.3, dL=-0.1)
    assert s.total == pytest.approx(-0.3)


def test_sectors_is_conserved():
    assert NSLSectors(dN=-0.5, dI=0.3, dL=0.0).is_conserved()
    assert not NSLSectors(dN=1.0, dI=0.0, dL=0.0).is_conserved()


def test_sectors_to_dict_uses_canonical_keys():
    s = NSLSectors(dN=1.0, dI=2.0, dL=3.0)
    d = s.to_dict()
    assert d["dNoether"] == 1.0
    assert d["dShannon"] == 2.0
    assert d["dLandauer"] == 3.0


def test_sectors_from_dict_round_trip():
    s = NSLSectors(dN=0.1, dI=0.2, dL=0.3)
    s2 = NSLSectors.from_dict(s.to_dict())
    assert s == s2


def test_sectors_from_dict_accepts_short_keys():
    s = NSLSectors.from_dict({"dN": 1.0, "dI": 2.0, "dL": 3.0})
    assert s == NSLSectors(dN=1.0, dI=2.0, dL=3.0)


def test_sectors_arithmetic():
    a = NSLSectors(dN=1.0, dI=2.0, dL=3.0)
    b = NSLSectors(dN=0.1, dI=0.2, dL=0.3)
    assert (a + b).total == pytest.approx(6.6)
    neg = -a
    assert neg.total == -6.0


# ---------------------------------------------------------------------------
# NSLTriads — the 24-D Leech embedding
# ---------------------------------------------------------------------------

def test_triads_dimensions():
    assert TRIAD_DIM == 8
    assert LEECH_DIM == 24


def test_triads_default_is_zero_24d():
    t = NSLTriads()
    assert len(t.noether) == 8
    assert len(t.shannon) == 8
    assert len(t.landauer) == 8
    assert len(t.as_leech_vector) == 24
    assert all(x == 0.0 for x in t.as_leech_vector)


def test_triads_pad_short_inputs():
    t = NSLTriads(noether=[1.0, 2.0], shannon=[], landauer=[3.0])
    assert len(t.noether) == 8 and t.noether[0] == 1.0 and t.noether[7] == 0.0
    assert len(t.shannon) == 8
    assert len(t.landauer) == 8 and t.landauer[0] == 3.0


def test_triads_from_leech_vector_round_trip():
    leech = tuple(float(i) for i in range(24))
    t = NSLTriads.from_leech_vector(leech)
    assert t.as_leech_vector == leech


def test_triads_from_leech_pads_short_vec():
    t = NSLTriads.from_leech_vector([1.0, 2.0, 3.0])
    assert len(t.as_leech_vector) == 24


def test_triads_score_zero_triads_gives_zero_sectors():
    t = NSLTriads()
    sectors = t.score([1.0, 2.0, 3.0])
    assert sectors == NSLSectors(0.0, 0.0, 0.0)


def test_triads_score_inner_product():
    t = NSLTriads(
        noether=[1.0] + [0.0] * 7,
        shannon=[0.0, 1.0] + [0.0] * 6,
        landauer=[0.0, 0.0, 1.0] + [0.0] * 5,
    )
    sectors = t.score([2.0, 3.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    assert sectors.dN == 2.0
    assert sectors.dI == 3.0
    assert sectors.dL == 5.0


def test_triads_hebbian_update_returns_self():
    t = NSLTriads()
    out = t.hebbian_update([1.0] * 8, reward=-0.5)
    assert out is t
    # noether should be non-zero now since reward < 0 → +1 sign
    assert any(x != 0.0 for x in t.noether)


def test_triads_hebbian_landauer_costs_couple_units():
    t = NSLTriads()
    t.hebbian_update([1.0] * 8, reward=1.0)
    # Landauer decreased by COUPLING * 1.0 * COUPLING per index
    assert t.landauer[0] == pytest.approx(-COUPLING * COUPLING)


# ---------------------------------------------------------------------------
# Gate modes
# ---------------------------------------------------------------------------

def test_gate_govern_accepts_conserved():
    d = gate(NSLSectors(dN=-0.5, dI=0.0, dL=0.0), GateMode.GOVERN)
    assert d.accepted is True
    assert d.reason == "conserved"


def test_gate_govern_rejects_positive():
    d = gate(NSLSectors(dN=0.5, dI=0.0, dL=0.0), GateMode.GOVERN)
    assert d.accepted is False
    assert d.reason == "rejected_govern"


def test_gate_amortize_accepts_within_budget():
    d = gate(NSLSectors(dN=0.3), GateMode.AMORTIZE, budget=1.0)
    assert d.accepted is True
    assert d.reason == "amortized"
    assert d.remaining_budget == pytest.approx(0.7)


def test_gate_amortize_rejects_over_budget():
    d = gate(NSLSectors(dN=2.0), GateMode.AMORTIZE, budget=1.0)
    assert d.accepted is False
    assert d.reason == "budget_exceeded"
    assert d.remaining_budget == 1.0


def test_gate_signal_always_accepts_but_marks_violation():
    d = gate(NSLSectors(dN=5.0), GateMode.SIGNAL)
    assert d.accepted is True
    assert d.reason == "signaled_violation"


# ---------------------------------------------------------------------------
# NSLReceipt + NSLLedger
# ---------------------------------------------------------------------------

def test_receipt_auto_id_and_timestamp():
    r = NSLReceipt(sectors=NSLSectors(dN=-0.5))
    assert r.receipt_id
    assert r.timestamp > 0
    assert r.delta_phi == -0.5


def test_receipt_to_dict_canonical_shape():
    r = NSLReceipt(sectors=NSLSectors(dN=1.0, dI=2.0, dL=3.0))
    d = r.to_dict()
    assert d["kind"] == "snapdna"
    assert d["delta_phi"] == 6.0
    assert d["sectors"] == {"dNoether": 1.0, "dShannon": 2.0, "dLandauer": 3.0}


def test_receipt_from_dict_round_trip():
    r1 = NSLReceipt(
        sectors=NSLSectors(dN=0.1, dI=0.2, dL=0.3),
        agent_id="agent1", operation="op1",
    )
    r2 = NSLReceipt.from_dict(r1.to_dict())
    assert r2.sectors == r1.sectors
    assert r2.agent_id == "agent1"
    assert r2.delta_phi == pytest.approx(0.6)


def test_ledger_append_updates_cumulative():
    ledger = NSLLedger()
    ledger.append(NSLReceipt(sectors=NSLSectors(dN=-0.3)))
    ledger.append(NSLReceipt(sectors=NSLSectors(dN=-0.2)))
    assert ledger.cumulative == pytest.approx(-0.5)
    assert ledger.violations == 0
    assert ledger.is_valid


def test_ledger_flags_positive_dphi_as_violation():
    ledger = NSLLedger()
    ledger.append(NSLReceipt(sectors=NSLSectors(dN=0.5)))
    assert ledger.violations == 1
    assert not ledger.is_valid


def test_ledger_by_agent_breakdown():
    ledger = NSLLedger()
    ledger.append(NSLReceipt(sectors=NSLSectors(dN=-1.0), agent_id="alice"))
    ledger.append(NSLReceipt(sectors=NSLSectors(dN=-0.5), agent_id="alice"))
    ledger.append(NSLReceipt(sectors=NSLSectors(dN=-0.3), agent_id="bob"))
    assert ledger.by_agent("alice")["cumulative_dphi"] == pytest.approx(-1.5)
    assert ledger.by_agent("bob")["cumulative_dphi"] == pytest.approx(-0.3)


def test_ledger_audit_detects_clean_chain():
    ledger = NSLLedger()
    ledger.append(NSLReceipt(sectors=NSLSectors(dN=-0.1)))
    ledger.append(NSLReceipt(sectors=NSLSectors(dN=-0.2)))
    audit = ledger.audit()
    assert audit["valid"]
    assert audit["drift"] < 1e-8


def test_ledger_clear():
    ledger = NSLLedger()
    ledger.append(NSLReceipt(sectors=NSLSectors(dN=-0.5)))
    ledger.clear()
    assert len(ledger) == 0
    assert ledger.cumulative == 0.0


# ---------------------------------------------------------------------------
# NSLProvider (the port)
# ---------------------------------------------------------------------------

def test_provider_compute_sectors_returns_three_terms():
    p = NSLProvider()
    sectors = p.compute_sectors([1.0, 0.0], [0.5, 0.0])
    assert isinstance(sectors, NSLSectors)


def test_provider_check_and_record_accepts_norm_decrease():
    p = NSLProvider()
    result = p.check_and_record(
        v_before=[2.0, 0.0], v_after=[1.0, 0.0],
        agent_id="test", operation="reduce",
    )
    assert isinstance(result, CheckResult)
    # Shannon-bound delta is negative when norm decreases → accepted
    assert result.accepted is True
    assert len(p.ledger) == 1


def test_provider_check_and_record_with_govern_rejects_increase():
    p = NSLProvider(default_mode=GateMode.GOVERN)
    result = p.check_and_record(
        v_before=[1.0, 0.0], v_after=[3.0, 0.0],
        agent_id="test", operation="grow",
    )
    # Shannon delta is positive; with zero triads dN=dL=0 → total=dI>0
    assert result.accepted is False


def test_provider_enforce_passthrough():
    p = NSLProvider()
    adjusted, was_adj = p.enforce([1.0, 0.0], [0.5, 0.0])
    assert was_adj is False


def test_provider_registers_on_conservation_port():
    mc = MorphonController.get()
    p = NSLProvider()
    mc.register("conservation", p)
    assert mc.get_provider("conservation") is p


def test_provider_health_keys():
    p = NSLProvider()
    h = p.health
    assert h["ok"] is True
    assert h["service"] == "nsl_provider"
    assert h["default_mode"] == "govern"
    assert "ledger" in h


def test_provider_custom_mode_and_budget():
    p = NSLProvider(default_mode=GateMode.AMORTIZE, default_budget=0.5)
    assert p.default_mode == GateMode.AMORTIZE
    assert p.default_budget == 0.5
