"""Port bootstrap smoke — ensure_bootstrapped without full Docker stack."""
from __future__ import annotations

import numpy as np
import pytest

from cmplx.morphon import Morphon
from cmplx.transform.bridge import (
    ensure_bootstrapped,
    get_cache_provider,
    get_conservation_provider,
    get_diagnostic_provider,
    get_receipt_provider,
    get_symbolic_provider,
    has_provider,
    reset_bootstrap_state,
)
from cmplx.transform.config import LayerConfig
from cmplx.transform.layer import GeometricTransformerLayer
from cmplx.transform.types import HiddenState


@pytest.fixture
def ports_bootstrapped():
    reset_bootstrap_state()
    ensure_bootstrapped(mmdb_path=":memory:")
    yield
    reset_bootstrap_state()


def test_ensure_bootstrapped_registers_core_ports(ports_bootstrapped):
    for port in ("diagnostic", "symbolic", "conservation", "cache", "receipt"):
        assert has_provider(port), f"missing port: {port}"


def test_diagnostic_provider_smoke(ports_bootstrapped):
    provider = get_diagnostic_provider()
    assert provider is not None
    assert hasattr(provider, "pulse") or hasattr(provider, "traverse") or hasattr(provider, "scan")


def test_cache_provider_roundtrip(ports_bootstrapped):
    cache = get_cache_provider()
    cache.put("port_contract::probe", {"ok": True})
    assert cache.get("port_contract::probe") == {"ok": True}


def test_receipt_provider_mint(ports_bootstrapped):
    receipt = get_receipt_provider().mint(
        receipt_type="PROCESS",
        atom_id="probe",
        operation="test.port_contract",
        payload={"probe": True},
    )
    assert receipt is not None


def test_conservation_provider_available(ports_bootstrapped):
    assert get_conservation_provider() is not None


def test_symbolic_provider_encode(ports_bootstrapped):
    morphon = Morphon.forge(payload={"probe": True})
    etp = get_symbolic_provider().encode_to_etp(morphon)
    assert isinstance(etp, str)


def test_layer_nsl_reject_path(ports_bootstrapped):
    if not has_provider("diagnostic"):
        pytest.skip("diagnostic provider not registered")
    layer = GeometricTransformerLayer(LayerConfig(nsl_mode="govern", nsl_budget=0.0))
    morphon = Morphon.forge(payload={"x": 1})
    state = HiddenState(
        tensor=np.zeros((3, 8), dtype=np.float64),
        morphon=morphon,
    )
    out_state, trace = layer.forward(state, 0, cache_namespace="port_test")
    assert trace.layer_idx == 0
    assert out_state.tensor.shape == state.tensor.shape
