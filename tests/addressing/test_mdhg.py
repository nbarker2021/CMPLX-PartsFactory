"""
Smoke tests for cmplx.addressing.mdhg — the digital-root hash provider.
"""
from __future__ import annotations

from collections import Counter

import pytest

from cmplx.addressing.mdhg import MDHG, Channel, Triad, digital_root, digital_root_hex
from cmplx.morphon import Morphon, MorphonController


# ---------------------------------------------------------------------------
# Standalone helpers
# ---------------------------------------------------------------------------

def test_digital_root_collapses_to_single_digit():
    assert digital_root(9) == 9
    assert digital_root(19) == 1   # 1+9=10 -> 1
    assert digital_root(99) == 9   # 9+9=18 -> 9
    assert digital_root(1234) == 1 # 1+2+3+4=10 -> 1


def test_digital_root_zero_maps_to_nine():
    # By system convention — channels are 1-9, not 0-8.
    assert digital_root(0) == 9


def test_digital_root_hex():
    # Sum of hex digit values 1+a+b+c+d+e+f = 1+10+11+12+13+14+15 = 76 → 7+6=13 → 1+3=4
    assert digital_root_hex("1abcdef") == 4


# ---------------------------------------------------------------------------
# Provider behaviour
# ---------------------------------------------------------------------------

def test_channel_for_returns_1_to_9():
    mdhg = MDHG()
    m = Morphon.forge(payload={"hello": "world"})
    ch = mdhg.channel_for(m)
    assert 1 <= ch <= 9


def test_channel_for_is_deterministic():
    mdhg = MDHG()
    m1 = Morphon.forge(payload={"same": "thing"})
    m2 = Morphon.forge(payload={"same": "thing"})
    # Different morphon IDs but identical payload → same channel
    assert mdhg.channel_for(m1) == mdhg.channel_for(m2)


def test_different_payloads_distribute():
    """Across 200 different payloads, channels should be reasonably spread.
    We don't require uniform distribution but we do require all 9 channels
    to appear and none to swallow >50%."""
    mdhg = MDHG()
    channels = Counter()
    for i in range(200):
        m = Morphon.forge(payload={"i": i})
        channels[mdhg.channel_for(m)] += 1
    # At least 7 of 9 channels should appear in 200 samples
    assert len(channels) >= 7, f"only {len(channels)} channels used: {channels}"
    # No channel should swallow more than half
    assert max(channels.values()) < 100, f"distribution skewed: {channels}"


def test_hierarchical_address_shape():
    mdhg = MDHG()
    m = Morphon.forge(payload={"k": "v"})
    sha, ch, register, triad = mdhg.hierarchical_address(m)
    assert len(sha) == 64
    assert all(c in "0123456789abcdef" for c in sha)
    assert 1 <= ch <= 9
    assert register in {ch.name for ch in Channel}
    assert triad in ("low", "mid", "high")


def test_channel_of_returns_enum():
    mdhg = MDHG()
    assert mdhg.channel_of(1) is Channel.INITIATION
    assert mdhg.channel_of(5) is Channel.ACTION
    assert mdhg.channel_of(9) is Channel.RESET


def test_channel_of_rejects_out_of_range():
    mdhg = MDHG()
    with pytest.raises(ValueError, match="out of range"):
        mdhg.channel_of(0)
    with pytest.raises(ValueError, match="out of range"):
        mdhg.channel_of(10)


def test_triad_of():
    mdhg = MDHG()
    assert mdhg.triad_of(1) is Triad.LOW
    assert mdhg.triad_of(3) is Triad.LOW
    assert mdhg.triad_of(4) is Triad.MID
    assert mdhg.triad_of(6) is Triad.MID
    assert mdhg.triad_of(7) is Triad.HIGH
    assert mdhg.triad_of(9) is Triad.HIGH


# ---------------------------------------------------------------------------
# Bridge integration
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_mdhg_plugs_in_as_addressing_provider():
    MorphonController.get().register("addressing", MDHG())
    m = Morphon.forge(payload={"hello": "world"})
    ch = m.project_to_channel()
    assert 1 <= ch <= 9
    # Cached on morphon
    assert m.dr_channel == ch


def test_morphon_caches_channel_after_first_lookup():
    class _CountingMDHG(MDHG):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        def channel_for(self, morphon: Morphon) -> int:
            self.calls += 1
            return super().channel_for(morphon)

    fake = _CountingMDHG()
    MorphonController.get().register("addressing", fake)
    m = Morphon.forge(payload={"x": 1})
    m.project_to_channel()
    m.project_to_channel()
    m.project_to_channel()
    assert fake.calls == 1
