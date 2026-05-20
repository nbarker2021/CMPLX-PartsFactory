"""
Smoke tests for cmplx.transport.chirp — the geometry-native transport.
"""
from __future__ import annotations

import pytest

from cmplx.addressing.mdhg import MDHG, Channel, Triad
from cmplx.geometry import Geometry
from cmplx.transport.chirp import (
    Chirp,
    ChirpFrame,
    DTMF_CARRIERS,
    decode_frame,
    encode_frame,
)
from cmplx.morphon import Morphon, MorphonController


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


@pytest.fixture
def wired_controller():
    """A morphon controller with mdhg + geometry registered.
    Chirp encoding requires both."""
    mc = MorphonController.get()
    mc.register("addressing", MDHG())
    mc.register("geometry", Geometry())
    return mc


# ---------------------------------------------------------------------------
# DTMF carrier table
# ---------------------------------------------------------------------------

def test_dtmf_carriers_match_standard_grid():
    # Row freqs by triad
    assert DTMF_CARRIERS[1][0] == 697
    assert DTMF_CARRIERS[4][0] == 770
    assert DTMF_CARRIERS[7][0] == 852
    # Column freqs by position
    assert DTMF_CARRIERS[1][1] == 1209
    assert DTMF_CARRIERS[5][1] == 1336
    assert DTMF_CARRIERS[9][1] == 1477


def test_dtmf_carriers_complete_for_1_to_9():
    assert sorted(DTMF_CARRIERS.keys()) == list(range(1, 10))


def test_dtmf_carriers_use_only_three_low_freqs_and_three_high_freqs():
    lows = {pair[0] for pair in DTMF_CARRIERS.values()}
    highs = {pair[1] for pair in DTMF_CARRIERS.values()}
    assert lows == {697, 770, 852}
    assert highs == {1209, 1336, 1477}


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def test_encode_produces_frame_with_channel_in_range(wired_controller):
    m = Morphon.forge(payload={"hello": "world"})
    frame = encode_frame(m)
    assert isinstance(frame, ChirpFrame)
    assert 1 <= frame.channel <= 9


def test_frame_carrier_matches_dtmf_grid(wired_controller):
    m = Morphon.forge(payload={"x": 1})
    frame = encode_frame(m)
    expected_low, expected_high = DTMF_CARRIERS[frame.channel]
    assert frame.low_hz == expected_low
    assert frame.high_hz == expected_high


def test_upper_word_8_bits(wired_controller):
    m = Morphon.forge(payload={"x": 1})
    frame = encode_frame(m)
    assert 0 <= frame.upper_word <= 255


def test_lower_word_8_bits(wired_controller):
    m = Morphon.forge(payload={"x": 1})
    frame = encode_frame(m)
    assert 0 <= frame.lower_word <= 255


def test_frame_carries_morphon_id(wired_controller):
    m = Morphon.forge(payload={"x": 1})
    frame = encode_frame(m)
    assert frame.morphon_id == m.id


def test_same_payload_yields_same_frame_content(wired_controller):
    """Two morphons with identical payloads share channel + words.
    (ids differ since each forge produces a fresh id.)"""
    m1 = Morphon.forge(payload={"same": "thing"})
    m2 = Morphon.forge(payload={"same": "thing"})
    f1 = encode_frame(m1)
    f2 = encode_frame(m2)
    assert f1.channel == f2.channel
    assert f1.low_hz == f2.low_hz
    assert f1.high_hz == f2.high_hz
    assert f1.upper_word == f2.upper_word
    assert f1.lower_word == f2.lower_word


def test_different_payloads_yield_different_frames(wired_controller):
    m1 = Morphon.forge(payload={"a": 1})
    m2 = Morphon.forge(payload={"b": 2})
    f1 = encode_frame(m1)
    f2 = encode_frame(m2)
    # At least one of (channel, upper, lower) should differ
    assert (f1.channel, f1.upper_word, f1.lower_word) != (
        f2.channel, f2.upper_word, f2.lower_word
    )


# ---------------------------------------------------------------------------
# Decoding round-trip
# ---------------------------------------------------------------------------

def test_decode_preserves_identity(wired_controller):
    m = Morphon.forge(payload={"k": "v"})
    frame = encode_frame(m)
    decoded = decode_frame(frame)
    assert decoded["morphon_id"] == m.id
    assert decoded["channel"] == frame.channel


def test_decode_e8_sign_bits_match_morphon(wired_controller):
    m = Morphon.forge(payload={"k": "v"})
    m.project_to_e8()
    frame = encode_frame(m)
    decoded = decode_frame(frame)
    for i, c in enumerate(m.e8_coordinates):
        expected_bit = 1 if c >= 0 else 0
        assert decoded["e8_sign_bits"][i] == expected_bit


def test_frame_to_dict_round_trip(wired_controller):
    m = Morphon.forge(payload={"k": "v"})
    f1 = encode_frame(m)
    d = f1.to_dict()
    f2 = ChirpFrame.from_dict(d)
    assert f1 == f2


# ---------------------------------------------------------------------------
# Frame validation
# ---------------------------------------------------------------------------

def test_frame_rejects_out_of_range_channel():
    with pytest.raises(ValueError, match="channel out of range"):
        ChirpFrame(channel=0, low_hz=697, high_hz=1209,
                   upper_word=0, lower_word=0, morphon_id="x")
    with pytest.raises(ValueError, match="channel out of range"):
        ChirpFrame(channel=10, low_hz=697, high_hz=1209,
                   upper_word=0, lower_word=0, morphon_id="x")


def test_frame_rejects_out_of_range_words():
    with pytest.raises(ValueError, match="upper_word"):
        ChirpFrame(channel=1, low_hz=697, high_hz=1209,
                   upper_word=300, lower_word=0, morphon_id="x")
    with pytest.raises(ValueError, match="lower_word"):
        ChirpFrame(channel=1, low_hz=697, high_hz=1209,
                   upper_word=0, lower_word=-1, morphon_id="x")


# ---------------------------------------------------------------------------
# Lazy provider use — pre-cached projections skip the ports
# ---------------------------------------------------------------------------

def test_pre_cached_morphon_skips_addressing_lookup():
    """If the morphon already has dr_channel set, chirp doesn't call
    the addressing port. (Proves the laziness pattern.)"""
    class _FailingAddressing:
        def channel_for(self, morphon):
            raise RuntimeError("addressing should not have been called")

    mc = MorphonController.get()
    mc.register("addressing", _FailingAddressing())
    mc.register("geometry", Geometry())

    m = Morphon.forge(payload={"k": "v"})
    m.dr_channel = 5  # pre-cached — chirp should use this
    frame = encode_frame(m)
    assert frame.channel == 5
    # The FailingAddressing was never called or we'd have raised.


# ---------------------------------------------------------------------------
# Bridge integration — Chirp on the transport port
# ---------------------------------------------------------------------------

def test_chirp_registers_on_transport_port(wired_controller):
    wired_controller.register("transport", Chirp())
    m = Morphon.forge(payload={"k": "v"})
    transport = wired_controller.get_provider("transport")
    frame = transport.encode(m)
    assert isinstance(frame, ChirpFrame)


# ---------------------------------------------------------------------------
# Cross-component constants
# ---------------------------------------------------------------------------

def test_channel_enum_imported_from_mdhg():
    """The static cross-import lives — chirp uses mdhg's Channel/Triad."""
    # The carriers module imports Channel and Triad at module-load time.
    # If the import broke we wouldn't have gotten this far.
    assert Channel.INITIATION.value == 1
    assert Triad.HIGH.value == "high"
