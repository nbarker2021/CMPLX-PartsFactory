from __future__ import annotations

import pytest

from lattice_forge import Forge
from lattice_forge.witness import WitnessEngine


@pytest.fixture
def engine(tmp_path):
    return WitnessEngine(Forge.open(tmp_path / "overlay"))


def test_regime_c_encode_round_trip(engine):
    out = engine.regime_c_encode(max_depth=128)
    assert out["kind"] == "regime_c"
    assert out["status"] == "pass"
    encoded = out["result"]
    assert encoded["length"] >= 1
    assert "word" in encoded


def test_regime_cprime_encode_round_trip(engine):
    out = engine.regime_cprime_encode(max_depth=128)
    assert out["kind"] == "regime_cprime"
    assert out["status"] == "pass"
    assert out["result"]["length"] == 129


def test_syndrome_report_shape(engine):
    out = engine.syndrome_report(syndrome_keys=["ecc_shed", "non_glue"])
    assert out["kind"] == "syndrome"
    syndromes = out["result"]["syndromes"]
    assert len(syndromes) == 2
    assert all("canonical_label" in s for s in syndromes)


def test_proof_bundle_full_quick(engine):
    out = engine.proof_bundle_full(quick=True)
    assert out["kind"] == "proof_bundle_full"
    assert out["status"] in ("pass", "fail")
    assert "proofs" in out["result"]


def test_witness_spec_includes_new_endpoints():
    from lattice_forge.witness.spec import witness_spec_dict

    spec = witness_spec_dict()
    for path in (
        "/witness/regime-c/encode",
        "/witness/regime-cprime/encode",
        "/witness/syndrome",
        "/witness/proof-bundle/full",
    ):
        assert path in spec["endpoints"]
