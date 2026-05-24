"""Witness state key grammar and witnessed_lookup stub."""

from __future__ import annotations

import tempfile
from pathlib import Path

from lattice_forge.forge import Forge
from lattice_forge.witness.engine import WitnessEngine
from lattice_forge.witness.state_keys import make_regime_encode_key, parse_state_key


def test_state_key_grammar_valid():
    parsed = parse_state_key("lf/state/C/encode/from_A/depth_256")
    assert parsed["valid"] is True
    assert parsed["regime"] == "C"


def test_state_key_grammar_invalid():
    parsed = parse_state_key("bad/key")
    assert parsed["valid"] is False


def test_witnessed_lookup_not_witnessed_before_encode():
    forge = Forge.open(Path(tempfile.mkdtemp(prefix="lf-witness-")))
    key = make_regime_encode_key(from_regime="A", to_regime="C", max_depth=128)
    out = forge.witnessed_lookup(key)
    result = out["result"]
    assert result["answer"] == "NOT_WITNESSED"
    assert result["witnessed"] is False


def test_regime_encode_records_state_keys_and_lookup():
    forge = Forge.open(Path(tempfile.mkdtemp(prefix="lf-witness-")))
    engine = WitnessEngine(forge)
    payload = engine.regime_c_encode(max_depth=64)
    keys = payload["result"]["state_keys"]
    assert keys
    assert all(parse_state_key(k)["valid"] for k in keys)
    primary = make_regime_encode_key(from_regime="A", to_regime="C", max_depth=64)
    looked = forge.witnessed_lookup(primary)["result"]
    assert looked["witnessed"] is True
    assert looked["answer"] == "WITNESSED"
    stub_key = f"{primary}/witness_stub"
    stub = forge.witnessed_lookup(stub_key)["result"]
    assert stub["witnessed"] is False
