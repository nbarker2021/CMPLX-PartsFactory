"""
F-2 facade tests — MDHGAddressingProvider against AddressingProvider Protocol.

Verifies:
  1. Protocol compliance + registration on `addressing` port.
  2. channel_for delegates to MDHG and returns 1-9.
  3. quantize24 returns a 24-tuple of integer bin indices.
  4. slot_id is deterministic per q24.
  5. encode_to_etp falls back when symbolic is unregistered; delegates
     when symbolic is registered.
  6. encode_to_etp matches TarPitSymbolicProvider's output (parity).
  7. decode_from_etp produces a derived morphon.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import (
    AddressingProvider,
    Morphon,
    MorphonController,
)
from cmplx.addressing.mdhg import MDHGAddressingProvider
from cmplx.symbolic.tarpit import TarPitSymbolicProvider


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# 1. Protocol compliance
# ---------------------------------------------------------------------------

def test_provider_satisfies_addressing_protocol():
    provider = MDHGAddressingProvider()
    assert isinstance(provider, AddressingProvider)


def test_provider_registers_on_addressing_port():
    provider = MDHGAddressingProvider()
    MorphonController.get().register("addressing", provider)
    assert MorphonController.get().has("addressing")


# ---------------------------------------------------------------------------
# 2. channel_for
# ---------------------------------------------------------------------------

def test_channel_for_returns_1_to_9():
    provider = MDHGAddressingProvider()
    m = Morphon.forge(payload={"k": "v"})
    channel = provider.channel_for(m)
    assert 1 <= channel <= 9


def test_channel_for_is_deterministic():
    provider = MDHGAddressingProvider()
    m = Morphon.forge(payload={"k": "v"})
    assert provider.channel_for(m) == provider.channel_for(m)


# ---------------------------------------------------------------------------
# 3-4. Multi-scale extensions
# ---------------------------------------------------------------------------

def test_quantize24_returns_24_tuple():
    provider = MDHGAddressingProvider()
    m = Morphon.forge(payload={"k": "v"})
    q24 = provider.quantize24(m)
    assert isinstance(q24, tuple)
    assert len(q24) == 24
    assert all(isinstance(x, int) for x in q24)


def test_quantize24_bins_are_in_range():
    provider = MDHGAddressingProvider(bins=16)
    m = Morphon.forge(payload={"k": "v"})
    q24 = provider.quantize24(m)
    assert all(0 <= x < 16 for x in q24)


def test_quantize24_is_deterministic():
    provider = MDHGAddressingProvider()
    m = Morphon.forge(payload={"k": "v"})
    assert provider.quantize24(m) == provider.quantize24(m)


def test_quantize24_differs_for_distinct_payloads():
    provider = MDHGAddressingProvider()
    m1 = Morphon.forge(payload={"k": "v1"})
    m2 = Morphon.forge(payload={"k": "v2"})
    assert provider.quantize24(m1) != provider.quantize24(m2)


def test_slot_id_is_16_hex_chars():
    provider = MDHGAddressingProvider()
    q24 = tuple(range(24))
    sid = provider.slot_id(q24)
    assert len(sid) == 16
    assert all(c in "0123456789abcdef" for c in sid)


def test_slot_id_is_deterministic():
    provider = MDHGAddressingProvider()
    q24 = tuple(range(24))
    assert provider.slot_id(q24) == provider.slot_id(q24)


# ---------------------------------------------------------------------------
# 5-6. ETP delegation and fallback parity
# ---------------------------------------------------------------------------

def test_encode_to_etp_fallback_when_symbolic_unregistered():
    """No symbolic port → fallback encoder produces valid ETP."""
    provider = MDHGAddressingProvider()
    m = Morphon.forge(payload={"k": "v"})
    program = provider.encode_to_etp(m)
    assert isinstance(program, str)
    assert len(program) > 0
    assert all(c in "}<>+01" for c in program)


def test_encode_to_etp_delegates_when_symbolic_registered():
    """Symbolic port registered → addressing delegates to it."""
    symbolic = TarPitSymbolicProvider()
    addressing = MDHGAddressingProvider()
    MorphonController.get().register("symbolic", symbolic)
    MorphonController.get().register("addressing", addressing)

    m = Morphon.forge(payload={"k": "v"})
    program_via_addressing = addressing.encode_to_etp(m)
    program_via_symbolic = symbolic.encode_to_etp(m)
    assert program_via_addressing == program_via_symbolic


def test_encode_to_etp_fallback_matches_symbolic():
    """Fallback encoder produces the same output as symbolic for the same morphon.

    This is the parity invariant — without it, registering symbolic would
    change addressing's behavior in a way that breaks downstream consumers.
    """
    symbolic = TarPitSymbolicProvider(program_length=32)
    addressing = MDHGAddressingProvider()

    m = Morphon.forge(payload={"k": "v"})
    fallback_program = addressing.encode_to_etp(m)  # no symbolic registered
    symbolic_program = symbolic.encode_to_etp(m)
    assert fallback_program == symbolic_program


# ---------------------------------------------------------------------------
# 7. decode_from_etp
# ---------------------------------------------------------------------------

def test_decode_from_etp_empty_returns_marker():
    provider = MDHGAddressingProvider()
    m = provider.decode_from_etp([])
    assert m.payload["etp_decode"] == "empty_ledger"
    assert m.payload.get("identity_kind") == "morphon"


def test_decode_from_etp_captures_final_row():
    addressing = MDHGAddressingProvider()
    symbolic = TarPitSymbolicProvider(default_max_steps=50)
    result = symbolic.run_program("}0}1>")
    decoded = addressing.decode_from_etp(result["ledger"])
    assert decoded.payload["etp_decode"] is True
    assert decoded.payload["wall10"] == result["ledger"][-1]["wall10"]


def test_health_endpoint_returns_metadata():
    provider = MDHGAddressingProvider(bins=8)
    h = provider.health
    assert h["ok"] is True
    assert h["service"] == "mdhg_addressing_provider"
    assert h["bins"] == 8
    assert h["quant_dims"] == 24
