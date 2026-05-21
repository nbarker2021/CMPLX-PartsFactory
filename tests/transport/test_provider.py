"""
F-5 facade tests — TransportProviderFacade against TransportProvider Protocol.

Verifies:
  1. Protocol compliance + registration on `transport` port.
  2. encode/decode round-trip via DTMFCarrier.
  3. Empty registry → LookupError on encode.
  4. ETP delegation + fallback parity.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import (
    Morphon,
    MorphonController,
    TransportProvider,
)
from cmplx.symbolic.tarpit import TarPitSymbolicProvider
from cmplx.transport import (
    CarrierRegistry,
    TransportProviderFacade,
)
from cmplx.transport.chirp.chirp import DTMFCarrier


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def _projected_morphon(payload=None):
    """Build a morphon with cached projections so DTMFCarrier can encode it
    without requiring the addressing/geometry ports to be registered."""
    m = Morphon.forge(payload=payload or {"k": "v"})
    m.dr_channel = 7
    m.e8_coordinates = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
    m.leech_point = "leech::abcdef01"
    return m


@pytest.fixture
def facade():
    reg = CarrierRegistry()
    reg.register(DTMFCarrier())
    return TransportProviderFacade(reg, default_carrier="dtmf")


# ---------------------------------------------------------------------------
# 1. Protocol compliance
# ---------------------------------------------------------------------------

def test_facade_satisfies_transport_protocol(facade):
    assert isinstance(facade, TransportProvider)


def test_facade_registers_on_transport_port(facade):
    MorphonController.get().register("transport", facade)
    assert MorphonController.get().has("transport")


# ---------------------------------------------------------------------------
# 2. encode / decode round-trip
# ---------------------------------------------------------------------------

def test_encode_returns_bytes(facade):
    m = _projected_morphon()
    payload = facade.encode(m)
    assert isinstance(payload, bytes)
    assert len(payload) > 0


def test_decode_recovers_morphon_identity(facade):
    m = _projected_morphon()
    payload = facade.encode(m)
    decoded = facade.decode(payload)
    assert isinstance(decoded, Morphon)
    # The transport contract preserves identity + carrier metadata, not payload.
    assert decoded.payload["morphon_id"] == m.id
    assert decoded.payload["carrier_name"] == "dtmf"
    assert decoded.payload["transport_decode"] is True


def test_decode_payload_includes_channel(facade):
    """Channel comes from the morphon — pre-projected so addressing port unneeded."""
    m = _projected_morphon()
    payload = facade.encode(m)
    decoded = facade.decode(payload)
    assert decoded.payload["channel"] == 7


# ---------------------------------------------------------------------------
# 3. Empty registry
# ---------------------------------------------------------------------------

def test_encode_raises_when_no_carriers_registered():
    facade = TransportProviderFacade(CarrierRegistry())
    m = Morphon.forge(payload={"k": "v"})
    with pytest.raises(LookupError, match="no registered carriers"):
        facade.encode(m)


# ---------------------------------------------------------------------------
# 4. ETP delegation + fallback parity
# ---------------------------------------------------------------------------

def test_encode_to_etp_fallback_when_symbolic_unregistered(facade):
    m = Morphon.forge(payload={"k": "v"})
    program = facade.encode_to_etp(m)
    assert isinstance(program, str)
    assert all(c in "}<>+01" for c in program)


def test_encode_to_etp_delegates_when_symbolic_registered(facade):
    symbolic = TarPitSymbolicProvider()
    MorphonController.get().register("symbolic", symbolic)
    m = Morphon.forge(payload={"k": "v"})
    via_facade = facade.encode_to_etp(m)
    via_symbolic = symbolic.encode_to_etp(m)
    assert via_facade == via_symbolic


def test_fallback_etp_parity_with_symbolic(facade):
    symbolic = TarPitSymbolicProvider(program_length=32)
    m = Morphon.forge(payload={"k": "v"})
    assert facade.encode_to_etp(m) == symbolic.encode_to_etp(m)


def test_decode_from_etp_empty(facade):
    m = facade.decode_from_etp([])
    assert m.payload["etp_decode"] == "empty_ledger"
    assert m.payload.get("identity_kind") == "morphon"


def test_decode_from_etp_captures_final_row(facade):
    symbolic = TarPitSymbolicProvider(default_max_steps=50)
    result = symbolic.run_program("}0}1>")
    decoded = facade.decode_from_etp(result["ledger"])
    assert decoded.payload["etp_decode"] is True


# ---------------------------------------------------------------------------
# 5. Health / repr
# ---------------------------------------------------------------------------

def test_health_reports_registered_carriers(facade):
    h = facade.health
    assert h["ok"] is True
    assert h["service"] == "transport_provider_facade"
    assert "dtmf" in h["carriers"]
    assert h["default_carrier"] == "dtmf"


def test_repr_includes_carrier_names(facade):
    r = repr(facade)
    assert "dtmf" in r
