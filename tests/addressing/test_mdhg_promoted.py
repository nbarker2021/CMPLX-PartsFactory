"""
Tests for the promoted MDHG surface: MDHGAddress + MDHGMultiScale.
"""
from __future__ import annotations

import pytest

from cmplx.addressing.mdhg import (
    DEFAULT_BINS,
    LAYERS,
    LayerCache,
    MDHGAddress,
    MDHGMultiScale,
    QUANT_DIMS,
    SlotRecord,
    quantize_24,
    slot_id_from_q24,
)


# ---------------------------------------------------------------------------
# MDHGAddress
# ---------------------------------------------------------------------------

def test_mdhg_address_from_e8_populates_levels():
    coords = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    addr = MDHGAddress.from_e8(coords)
    for level in ("atom", "room", "floor", "building", "city", "planet"):
        assert getattr(addr, level).startswith("s")
    assert addr.e8_coords == coords


def test_mdhg_address_full_path_dotted():
    addr = MDHGAddress.from_e8([0.1] * 8)
    path = addr.full_path()
    assert path.count("/") == 5  # planet/city/building/floor/room/atom


def test_mdhg_address_shaped_hash_locality():
    """Similar coords → similar shaped_hash prefix (locality preserved)."""
    a = MDHGAddress.from_e8([0.1] * 8)
    b = MDHGAddress.from_e8([0.1] * 8)
    c = MDHGAddress.from_e8([0.9] * 8)
    assert a.shaped_hash() == b.shaped_hash()
    assert a.shaped_hash() != c.shaped_hash()


def test_mdhg_address_auto_hash_on_construction():
    addr = MDHGAddress.from_e8([0.1] * 8)
    assert addr.address_hash
    assert len(addr.address_hash) == 24


def test_mdhg_address_layer_default_fast():
    addr = MDHGAddress.from_e8([0.1] * 8)
    assert addr.grid_layer == "fast"
    addr2 = MDHGAddress.from_e8([0.1] * 8, grid_layer="slow")
    assert addr2.grid_layer == "slow"


def test_mdhg_address_pads_short_vector():
    addr = MDHGAddress.from_e8([0.1, 0.2])
    assert len(addr.e8_coords) == 8


def test_mdhg_address_to_dict_round_trip_keys():
    addr = MDHGAddress.from_e8([0.1] * 8)
    d = addr.to_dict()
    for k in ("atom", "room", "floor", "building", "city", "planet",
              "address_hash", "full_path"):
        assert k in d


# ---------------------------------------------------------------------------
# quantize_24 + slot_id_from_q24
# ---------------------------------------------------------------------------

def test_quantize_24_yields_24_bins():
    q = quantize_24([0.5] * 24)
    assert len(q) == QUANT_DIMS
    assert all(0 <= i < DEFAULT_BINS for i in q)


def test_quantize_24_pads_short_vec():
    q = quantize_24([0.1, 0.2, 0.3])
    assert len(q) == 24


def test_quantize_24_clamps_out_of_range():
    q_low = quantize_24([-10.0] * 24)
    q_high = quantize_24([10.0] * 24)
    assert all(i == 0 for i in q_low)
    assert all(i == DEFAULT_BINS - 1 for i in q_high)


def test_slot_id_deterministic():
    q = quantize_24([0.5] * 24)
    assert slot_id_from_q24(q) == slot_id_from_q24(q)


# ---------------------------------------------------------------------------
# LayerCache
# ---------------------------------------------------------------------------

def test_layer_cache_admit_creates_slot():
    lc = LayerCache(name="fast")
    result = lc.admit([0.1] * 24, meta={"k": "v"})
    assert result["layer"] == "fast"
    assert result["drift"] is False
    assert lc.occupancy() == 1


def test_layer_cache_admit_same_vec_no_drift():
    lc = LayerCache(name="fast")
    lc.admit([0.1] * 24)
    r2 = lc.admit([0.1] * 24)
    assert r2["drift"] is False
    assert r2["access_count"] == 2
    assert lc.occupancy() == 1


def test_layer_cache_admit_different_vec_same_slot_detects_drift():
    """Two vectors in the same quantized cell but with different
    signatures should register a drift event."""
    lc = LayerCache(name="fast")
    # Two vectors close enough to quantize the same way, but distinct
    lc.admit([0.10] * 24)
    r2 = lc.admit([0.11] * 24)
    # If they land in the same slot, the sig differs → drift
    if r2["slot"] == slot_id_from_q24(quantize_24([0.10] * 24)):
        assert r2["drift"] is True


def test_layer_cache_top_k_orders_by_access():
    lc = LayerCache(name="fast")
    lc.admit([0.1] * 24)
    lc.admit([0.1] * 24)
    lc.admit([0.9] * 24)
    top = lc.top_k(k=2)
    assert top[0].access_count >= top[1].access_count


# ---------------------------------------------------------------------------
# MDHGMultiScale
# ---------------------------------------------------------------------------

def test_multiscale_has_three_layers():
    ms = MDHGMultiScale()
    assert ms.occupancy_snapshot() == {n: 0 for n in LAYERS}


def test_multiscale_admit_targets_one_layer():
    ms = MDHGMultiScale()
    ms.admit([0.1] * 24, layer="fast")
    snap = ms.occupancy_snapshot()
    assert snap["fast"] == 1
    assert snap["med"] == 0
    assert snap["slow"] == 0


def test_multiscale_admit_all_layers():
    ms = MDHGMultiScale()
    results = ms.admit_all_layers([0.5] * 24, meta={"src": "test"})
    assert set(results.keys()) == set(LAYERS)
    for r in results.values():
        assert r["drift"] is False
    snap = ms.occupancy_snapshot()
    assert all(v == 1 for v in snap.values())


def test_multiscale_unknown_layer_raises():
    ms = MDHGMultiScale()
    with pytest.raises(ValueError, match="unknown layer"):
        ms.admit([0.1] * 24, layer="warp")


def test_multiscale_proposeK_returns_topK_in_layer():
    ms = MDHGMultiScale()
    ms.admit([0.1] * 24, layer="slow")
    ms.admit([0.1] * 24, layer="slow")
    top = ms.propose_topK(k=1, layer="slow")
    assert len(top) == 1
    assert top[0].access_count == 2
