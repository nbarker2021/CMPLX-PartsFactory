"""Tests for the F_2 / Majorana primitives and the contributions registry."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.f2_majorana import (
    F2Quadratic,
    can_glue_edges,
    rule30_correction_quadratic,
    rule30_correction_arf,
    verify_f2_majorana,
)
from lattice_forge.contributions_registry import Registry
from lattice_forge.contribution_validators import install_default_validators


def test_known_arf_invariants():
    """Trivial Arf=0, hyperbolic Arf=0, elliptic Arf=1."""
    assert F2Quadratic([[0, 0], [0, 0]]).arf_invariant() == 0
    assert F2Quadratic([[0, 1], [0, 0]]).arf_invariant() == 0
    assert F2Quadratic([[1, 1], [0, 1]]).arf_invariant() == 1


def test_rule30_correction_is_hyperbolic():
    """The Rule 30 correction CR + C has Arf invariant 0."""
    assert rule30_correction_arf() == 0


def test_can_glue_matching_arf():
    """Same-Arf forms glue; different-Arf forms do not."""
    q0 = F2Quadratic([[0, 0], [0, 0]])  # Arf 0
    qh = F2Quadratic([[0, 1], [0, 0]])  # Arf 0
    qe = F2Quadratic([[1, 1], [0, 1]])  # Arf 1
    assert can_glue_edges(q0, qh)["can_glue"]
    assert can_glue_edges(qh, q0)["can_glue"]
    assert not can_glue_edges(q0, qe)["can_glue"]
    assert not can_glue_edges(qh, qe)["can_glue"]


def test_full_verifier_passes():
    r = verify_f2_majorana()
    assert r["status"] == "pass"


def test_bilinear_form_symmetry():
    """B(v, w) = B(w, v) over F_2 for the symmetric bilinear form."""
    q = F2Quadratic([[1, 1, 0], [0, 0, 1], [0, 0, 1]])
    for v in [[1, 0, 0], [0, 1, 0], [1, 1, 0], [1, 1, 1]]:
        for w in [[0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1]]:
            assert q.bilinear(v, w) == q.bilinear(w, v)


def test_bilinear_form_polarization_identity():
    """B(v, w) = Q(v+w) + Q(v) + Q(w) over F_2 by construction."""
    q = F2Quadratic([[1, 1, 0], [0, 0, 1], [0, 0, 1]])
    for v_bits in range(8):
        for w_bits in range(8):
            v = [(v_bits >> i) & 1 for i in range(3)]
            w = [(w_bits >> i) & 1 for i in range(3)]
            vw = [(a ^ b) for a, b in zip(v, w)]
            polar = (q.evaluate(vw) ^ q.evaluate(v) ^ q.evaluate(w)) & 1
            assert q.bilinear(v, w) == polar


# ---------------------------------------------------------------------------
# Contributions registry tests
# ---------------------------------------------------------------------------

def test_registry_accepts_valid_lucas_term():
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "registry.db")
        reg = Registry(path)
        install_default_validators(reg)
        out = reg.propose(
            kind="lucas_term",
            key={"d": 3, "x": 1},
            value={"bit": 1},
            provenance="test_registry_accepts_valid_lucas_term",
            validator_name="lucas_recurrence",
        )
        assert out["status"] == "accepted"
        rec = reg.lookup("lucas_term", {"d": 3, "x": 1})
        assert rec is not None
        assert rec["value"] == {"bit": 1}
        reg.close()
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_registry_rejects_invalid_lucas_term():
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "registry.db")
        reg = Registry(path)
        install_default_validators(reg)
        out = reg.propose(
            kind="lucas_term",
            key={"d": 3, "x": 1},
            value={"bit": 0},  # WRONG: lucas_bit(3, 1) is actually 1
            provenance="test_registry_rejects_invalid_lucas_term",
            validator_name="lucas_recurrence",
        )
        assert out["status"] == "rejected"
        rec = reg.lookup("lucas_term", {"d": 3, "x": 1})
        assert rec is None
        reg.close()
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_registry_accepts_valid_f2_arf():
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "registry.db")
        reg = Registry(path)
        install_default_validators(reg)
        out = reg.propose(
            kind="f2_arf",
            key={"A": [[1, 1], [0, 1]]},  # Arf=1
            value={"arf": 1},
            provenance="test_registry_accepts_valid_f2_arf",
            validator_name="f2_arf",
        )
        assert out["status"] == "accepted"
        reg.close()
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_registry_rejects_wrong_arf():
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "registry.db")
        reg = Registry(path)
        install_default_validators(reg)
        out = reg.propose(
            kind="f2_arf",
            key={"A": [[1, 1], [0, 1]]},  # actually Arf=1
            value={"arf": 0},               # claimed Arf=0
            provenance="test_registry_rejects_wrong_arf",
            validator_name="f2_arf",
        )
        assert out["status"] == "rejected"
        reg.close()
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_registry_idempotent_double_accept():
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "registry.db")
        reg = Registry(path)
        install_default_validators(reg)
        out1 = reg.propose(
            kind="lucas_term",
            key={"d": 3, "x": 1},
            value={"bit": 1},
            provenance="first",
            validator_name="lucas_recurrence",
        )
        out2 = reg.propose(
            kind="lucas_term",
            key={"d": 3, "x": 1},
            value={"bit": 1},
            provenance="second",
            validator_name="lucas_recurrence",
        )
        assert out1["status"] == "accepted"
        assert out2["status"] == "already_present"
        reg.close()
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_registry_stats_after_three_proposals():
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "registry.db")
        reg = Registry(path)
        install_default_validators(reg)
        reg.propose("lucas_term", {"d": 3, "x": 1}, {"bit": 1}, "p1", "lucas_recurrence")
        reg.propose("lucas_term", {"d": 4, "x": 0}, {"bit": 0}, "p2", "lucas_recurrence")
        reg.propose("lucas_term", {"d": 4, "x": 1}, {"bit": 1}, "p3", "lucas_recurrence")  # WRONG: should be 0
        stats = reg.stats()
        assert stats["accepted_count"] == 2
        # 2 accepted proposals, 1 rejected proposal
        assert stats["proposals_by_status"].get("accepted", 0) == 2
        assert stats["proposals_by_status"].get("rejected", 0) == 1
        reg.close()
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_registry_rule30_center_bit_validation():
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "registry.db")
        reg = Registry(path)
        install_default_validators(reg)
        # Depth 1: Rule 30 single-cell seed produces center bit 1 at depth 1.
        out = reg.propose(
            kind="rule30_center_bit",
            key={"N": 1},
            value={"bit": 1},
            provenance="depth-1 trivial check",
            validator_name="rule30_decomposition",
        )
        assert out["status"] == "accepted"
        reg.close()
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
