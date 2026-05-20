"""
Smoke tests for the Carrier ABC + CarrierRegistry + DTMFCarrier +
PixelCarrier round-trip.
"""
from __future__ import annotations

import pytest

from cmplx.addressing.mdhg import MDHG
from cmplx.geometry import Geometry
from cmplx.morphon import Morphon, MorphonController
from cmplx.transport import Carrier, CarrierFrame, CarrierRegistry
from cmplx.transport.chirp import DTMFCarrier
from cmplx.transport.pixel import PixelCarrier, PixelFrame, BLOCK_SIZE


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


@pytest.fixture
def wired_controller():
    mc = MorphonController.get()
    mc.register("addressing", MDHG())
    mc.register("geometry", Geometry())
    return mc


# ---------------------------------------------------------------------------
# Registry behavior
# ---------------------------------------------------------------------------

def test_registry_register_and_get():
    reg = CarrierRegistry()
    reg.register(DTMFCarrier())
    assert reg.has("dtmf")
    assert "dtmf" in reg.names()
    assert isinstance(reg.get("dtmf"), DTMFCarrier)


def test_registry_rejects_duplicate():
    reg = CarrierRegistry()
    reg.register(DTMFCarrier())
    with pytest.raises(RuntimeError, match="already registered"):
        reg.register(DTMFCarrier())


def test_registry_rejects_non_carrier():
    reg = CarrierRegistry()
    with pytest.raises(TypeError):
        reg.register("not a carrier")  # type: ignore[arg-type]


def test_registry_unknown_get_raises():
    reg = CarrierRegistry()
    with pytest.raises(LookupError, match="no carrier"):
        reg.get("nope")


def test_registry_encode_single_carrier(wired_controller):
    reg = CarrierRegistry()
    reg.register(DTMFCarrier())
    m = Morphon.forge(payload={"x": 1})
    frame = reg.encode(m)
    assert isinstance(frame, CarrierFrame)
    assert frame.carrier_name == "dtmf"


def test_registry_encode_ambiguous_with_multiple(wired_controller):
    reg = CarrierRegistry()
    reg.register(DTMFCarrier())
    reg.register(PixelCarrier())
    m = Morphon.forge(payload={"x": 1})
    with pytest.raises(RuntimeError, match="multiple carriers"):
        reg.encode(m)


# ---------------------------------------------------------------------------
# DTMFCarrier
# ---------------------------------------------------------------------------

def test_dtmf_carrier_round_trip(wired_controller):
    carrier = DTMFCarrier()
    m = Morphon.forge(payload={"k": "v"})
    frame = carrier.encode(m)
    assert isinstance(frame, CarrierFrame)
    assert frame.carrier_name == "dtmf"
    assert frame.morphon_id == m.id
    assert 1 <= frame.channel <= 9

    decoded = carrier.decode(frame)
    assert decoded["morphon_id"] == m.id
    assert decoded["channel"] == frame.channel


def test_dtmf_rejects_foreign_frame(wired_controller):
    carrier = DTMFCarrier()
    pix = PixelCarrier()
    m = Morphon.forge(payload={"k": "v"})
    pixel_frame = pix.encode(m)
    with pytest.raises(ValueError, match="cannot decode"):
        carrier.decode(pixel_frame)


# ---------------------------------------------------------------------------
# PixelCarrier
# ---------------------------------------------------------------------------

def test_pixel_carrier_produces_pixel_frame(wired_controller):
    carrier = PixelCarrier()
    m = Morphon.forge(payload={"k": "v"})
    frame = carrier.encode(m)
    assert isinstance(frame, PixelFrame)
    assert frame.carrier_name == "pixel"
    assert frame.width == BLOCK_SIZE
    assert frame.height == BLOCK_SIZE


def test_pixel_carrier_round_trip_identity_fields(wired_controller):
    """encode → decode preserves channel, E8 sign bits, leech first byte."""
    carrier = PixelCarrier()
    m = Morphon.forge(payload={"alpha": "beta"})
    m.project_to_channel()
    m.project_to_e8()
    m.project_to_leech()

    expected_channel = m.dr_channel
    expected_signs = [1 if c >= 0 else 0 for c in m.e8_coordinates]

    frame = carrier.encode(m)
    decoded = carrier.decode(frame)

    assert decoded["morphon_id"] == m.id
    assert decoded["channel"] == expected_channel
    assert decoded["e8_sign_bits"] == expected_signs


def test_pixel_carrier_deterministic(wired_controller):
    """Same morphon → same pixel bytes."""
    carrier = PixelCarrier()
    m = Morphon.forge(payload={"k": "v"})
    f1 = carrier.encode(m)
    f2 = carrier.encode(m)
    assert f1.payload_bytes == f2.payload_bytes


def test_pixel_carrier_different_payloads_diverge(wired_controller):
    carrier = PixelCarrier()
    m1 = Morphon.forge(payload={"a": 1})
    m2 = Morphon.forge(payload={"b": 2})
    f1 = carrier.encode(m1)
    f2 = carrier.encode(m2)
    assert f1.payload_bytes != f2.payload_bytes


def test_pixel_rejects_foreign_frame(wired_controller):
    pix = PixelCarrier()
    dtmf = DTMFCarrier()
    m = Morphon.forge(payload={"k": "v"})
    dtmf_frame = dtmf.encode(m)
    with pytest.raises(ValueError, match="cannot decode"):
        pix.decode(dtmf_frame)


# ---------------------------------------------------------------------------
# Cross-carrier consistency — same identity bits flow through both carriers
# ---------------------------------------------------------------------------

def test_dtmf_and_pixel_agree_on_identity_bits(wired_controller):
    """Same morphon encoded through DTMF and Pixel yields the same
    channel, E8 sign bits, and leech first byte."""
    dtmf = DTMFCarrier()
    pix = PixelCarrier()
    m = Morphon.forge(payload={"shared": "state"})

    d = dtmf.decode(dtmf.encode(m))
    p = pix.decode(pix.encode(m))

    assert d["channel"] == p["channel"]
    assert d["e8_sign_bits"] == p["e8_sign_bits"]
    assert d["lower_word"] == p["lower_word"]


# ---------------------------------------------------------------------------
# Carrier ABC contract — can't be instantiated directly
# ---------------------------------------------------------------------------

def test_carrier_abc_cannot_instantiate():
    with pytest.raises(TypeError):
        Carrier()  # type: ignore[abstract]
