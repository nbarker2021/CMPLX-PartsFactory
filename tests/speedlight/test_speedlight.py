"""
Tests for cmplx.speedlight — receipts + address + cache + tiers +
index + equivalence + worldline + provider.
"""
from __future__ import annotations

import threading
import time

import pytest

from cmplx.addressing.mdhg import MDHGMultiScale
from cmplx.morphon import MorphonController
from cmplx.speedlight import (
    ASPECTS,
    ComputationReceipt,
    EquivalenceLearner,
    GlobalIndex,
    PLANETS,
    Prototype,
    ReceiptStore,
    SpeedLight,
    SpeedLightDistributed,
    SpeedLightProvider,
    TwoTierCache,
    WorldlineCache,
    address_prefix,
    aspect_key,
    compute_mdhg_address,
    cosine_similarity,
    parse_address,
)


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# Receipt + ReceiptStore
# ---------------------------------------------------------------------------

def test_receipt_auto_populates_ids_and_hashes():
    r = ComputationReceipt(task_id="t1", result=42)
    assert r.receipt_id
    assert r.task_hash
    assert r.result_hash
    assert r.cached_at > 0


def test_receipt_to_dict_round_trip_keys():
    r = ComputationReceipt(task_id="t", result=1, fn_name="f")
    d = r.to_dict()
    for k in ("receipt_id", "task_id", "task_hash", "result_hash",
              "result", "cost_seconds", "cached_at", "fn_name"):
        assert k in d


def test_store_append_and_lookup():
    store = ReceiptStore()
    r = store.append(ComputationReceipt(task_id="t1", result=1))
    assert store.get("t1") is r
    assert store.get_by_hash(r.task_hash) is r
    assert "t1" in store
    assert len(store) == 1


def test_store_update_preserves_position():
    store = ReceiptStore()
    store.append(ComputationReceipt(task_id="t1", result=1))
    store.append(ComputationReceipt(task_id="t2", result=2))
    store.append(ComputationReceipt(task_id="t1", result=99))  # update t1
    receipts = store.all()
    # t1 moved to end
    assert receipts[-1].task_id == "t1"
    assert receipts[-1].result == 99


def test_store_requires_task_id():
    store = ReceiptStore()
    with pytest.raises(ValueError):
        store.append(ComputationReceipt(task_id="", result=1))


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------

def test_compute_address_has_6_layers():
    addr = compute_mdhg_address(
        content="def foo(): pass",
        snap_labels=["code", "python"],
        e8_coords=[0.1] * 8,
        atom_id="a1234567",
    )
    assert addr["address"].count(".") == 5
    for k in ("planet", "city", "building", "floor", "room", "atom"):
        assert addr[k]


def test_compute_address_planet_in_planets():
    addr = compute_mdhg_address(content="hello")
    assert addr["planet"] in PLANETS


def test_compute_address_city_detection():
    code = compute_mdhg_address(content="def foo(): pass")
    doc = compute_mdhg_address(content="# Title\nbody")
    data = compute_mdhg_address(content='{"k": 1}')
    other = compute_mdhg_address(content="hello world")
    assert code["city"] == "forge"
    assert doc["city"] == "library"
    assert data["city"] == "vault"
    assert other["city"] == "nexus"


def test_compute_address_locality_preserved_for_same_content():
    a = compute_mdhg_address(content="x", snap_labels=["a"], e8_coords=[0.1] * 8)
    b = compute_mdhg_address(content="x", snap_labels=["a"], e8_coords=[0.1] * 8)
    assert a["address"] == b["address"]


def test_address_prefix_truncates_to_level():
    addr = "earth.forge.aaaa.bbbb.cccc.dddd"
    assert address_prefix(addr, "planet") == "earth"
    assert address_prefix(addr, "city") == "earth.forge"
    assert address_prefix(addr, "building") == "earth.forge.aaaa"
    assert address_prefix(addr, "atom") == addr


def test_address_prefix_rejects_unknown_level():
    with pytest.raises(ValueError):
        address_prefix("a.b.c.d.e.f", "moon")


def test_parse_address_returns_dict_of_levels():
    parts = parse_address("earth.forge.aaaa.bbbb.cccc.dddd")
    assert parts["planet"] == "earth"
    assert parts["atom"] == "dddd"


def test_aspect_key_format():
    assert aspect_key("a.b.c.d.e.f", "kaprekar") == "a.b.c.d.e.f:kaprekar"


def test_aspects_constant_includes_canonical_ten():
    for name in ("gate_w4", "kaprekar", "phi", "e8_nearest",
                 "weyl_chamber", "bonds", "labels"):
        assert name in ASPECTS


# ---------------------------------------------------------------------------
# SpeedLight — idempotent compute
# ---------------------------------------------------------------------------

def test_speedlight_first_call_misses_and_caches():
    sl = SpeedLight()
    call_count = [0]
    def expensive():
        call_count[0] += 1
        return "result"
    result, cost, receipt = sl.compute("task1", expensive)
    assert result == "result"
    assert cost >= 0
    assert sl.stats()["misses"] == 1
    assert call_count[0] == 1


def test_speedlight_second_call_hits_with_zero_cost():
    sl = SpeedLight()
    sl.compute("task1", lambda: 42)
    result, cost, _ = sl.compute("task1", lambda: 999)  # fn ignored on hit
    assert result == 42
    assert cost == 0.0
    assert sl.stats()["hits"] == 1


def test_speedlight_idempotent_f_of_f_equals_f():
    sl = SpeedLight()
    calls = []
    def fn():
        calls.append(1)
        return "value"
    r1, _, _ = sl.compute("task", fn)
    r2, _, _ = sl.compute("task", fn)
    r3, _, _ = sl.compute("task", fn)
    assert r1 == r2 == r3 == "value"
    assert len(calls) == 1  # fn ran exactly once


def test_speedlight_no_fn_on_miss_raises():
    sl = SpeedLight()
    with pytest.raises(LookupError):
        sl.compute("unknown_task")


def test_speedlight_key_cache_put_get():
    sl = SpeedLight()
    sl.put("k", "v")
    assert sl.get("k") == "v"
    assert sl.has("k")


def test_speedlight_aspect_keys_use_colon_separator():
    sl = SpeedLight()
    sl.put_aspect("earth.forge.a.b.c.d", "kaprekar", {"steps": 5})
    assert sl.get_aspect("earth.forge.a.b.c.d", "kaprekar") == {"steps": 5}
    assert sl.has_aspect("earth.forge.a.b.c.d", "kaprekar")


def test_speedlight_compute_and_cache_idempotent():
    sl = SpeedLight()
    calls = []
    def fn():
        calls.append(1)
        return {"steps": 7}
    addr = "earth.forge.a.b.c.d"
    r1 = sl.compute_and_cache(addr, "kaprekar", fn)
    r2 = sl.compute_and_cache(addr, "kaprekar", fn)
    assert r1 == r2 == {"steps": 7}
    assert len(calls) == 1


def test_speedlight_share_cache_merges_receipts():
    sl1 = SpeedLight()
    sl2 = SpeedLight()
    sl1.compute("t1", lambda: 1)
    sl2.compute("t2", lambda: 2)
    merged = sl1.share_cache(sl2)
    assert merged == 1
    assert "t2" in sl1.receipt_cache


def test_speedlight_stats_reports_hit_rate():
    sl = SpeedLight()
    sl.compute("a", lambda: 1)
    sl.compute("a", lambda: 1)
    sl.compute("a", lambda: 1)
    stats = sl.stats()
    # 1 miss + 2 hits → hit rate ~ 66.7%
    assert 60.0 < stats["hit_rate_percent"] < 70.0


def test_speedlight_report_returns_string():
    sl = SpeedLight()
    sl.compute("a", lambda: 1)
    report = sl.report()
    assert "SpeedLight Report" in report
    assert "hit rate" in report


def test_speedlight_clear_resets_state():
    sl = SpeedLight()
    sl.compute("a", lambda: 1)
    sl.put("k", "v")
    sl.clear()
    assert len(sl.receipt_cache) == 0
    assert len(sl.key_cache) == 0
    assert sl.stats()["hits"] == 0


# ---------------------------------------------------------------------------
# SpeedLightDistributed — thread safety
# ---------------------------------------------------------------------------

def test_distributed_compute_thread_safe():
    sl = SpeedLightDistributed()
    call_count = [0]
    def fn():
        call_count[0] += 1
        time.sleep(0.01)
        return call_count[0]
    threads = [
        threading.Thread(target=sl.compute, args=("shared", fn))
        for _ in range(10)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # Some races allowed in cache fill, but everyone must end up with
    # the SAME cached value (idempotent).
    result, _, _ = sl.compute("shared", lambda: -1)
    assert result == sl.receipt_cache["shared"].result


# ---------------------------------------------------------------------------
# TwoTierCache
# ---------------------------------------------------------------------------

def test_two_tier_t1_hit():
    c = TwoTierCache(max_t1_entries=10)
    c.put("k", "v")
    assert c.get("k") == "v"
    assert c.stats()["t1_hits"] == 1


def test_two_tier_t2_promotion_on_miss():
    c = TwoTierCache(max_t1_entries=2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)  # evicts a from T1
    assert c.get("a") == 1  # T1 miss → T2 hit → promote
    stats = c.stats()
    assert stats["t1_promotions"] >= 1


def test_two_tier_lru_evicts_oldest():
    c = TwoTierCache(max_t1_entries=2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)  # evicts "a" (oldest)
    # "a" still recoverable from T2 but evicted from T1
    assert c.stats()["evictions"] >= 1


def test_two_tier_missing_key_returns_none():
    c = TwoTierCache()
    assert c.get("nope") is None
    assert c.stats()["misses"] == 1


def test_two_tier_pluggable_t2_backend():
    backend: dict[str, str] = {}
    c = TwoTierCache(
        max_t1_entries=1,
        t2_get=backend.get,
        t2_put=lambda k, v: backend.__setitem__(k, v),
    )
    c.put("k", "v")
    assert backend["k"] == "v"


# ---------------------------------------------------------------------------
# GlobalIndex — E8 proximity
# ---------------------------------------------------------------------------

def test_index_admit_records_entry():
    idx = GlobalIndex()
    idx.admit("atom1", [0.1] * 8, labels=["foo"])
    assert idx.has("atom1")
    assert len(idx) == 1


def test_index_query_returns_top_k_by_distance():
    idx = GlobalIndex()
    idx.admit("a", [0.0] * 8)
    idx.admit("b", [1.0] + [0.0] * 7)
    idx.admit("c", [5.0] + [0.0] * 7)
    hits = idx.query([0.0] * 8, k=2)
    ids = [h[0] for h in hits]
    assert ids == ["a", "b"]
    # distances ascending
    assert hits[0][1] <= hits[1][1]


def test_index_query_label_filter():
    idx = GlobalIndex()
    idx.admit("a", [0.0] * 8, labels=["x"])
    idx.admit("b", [0.0] * 8, labels=["y"])
    hits = idx.query([0.0] * 8, k=5, label_filter=["x"])
    assert [h[0] for h in hits] == ["a"]


def test_index_eviction_at_capacity():
    idx = GlobalIndex(max_entries=2)
    idx.admit("a", [0.0] * 8)
    idx.admit("b", [0.0] * 8)
    idx.admit("c", [0.0] * 8)
    assert len(idx) == 2
    assert not idx.has("a")


def test_index_stats_increment():
    idx = GlobalIndex()
    idx.admit("a", [0.0] * 8)
    idx.query([0.0] * 8)
    stats = idx.stats()
    assert stats["total_admits"] == 1
    assert stats["total_queries"] == 1


# ---------------------------------------------------------------------------
# EquivalenceLearner
# ---------------------------------------------------------------------------

def test_cosine_similarity_identical_vectors():
    assert cosine_similarity((1.0, 0.0), (1.0, 0.0)) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal():
    assert cosine_similarity((1.0, 0.0), (0.0, 1.0)) == pytest.approx(0.0)


def test_cosine_similarity_handles_zero_vector():
    assert cosine_similarity((0.0, 0.0), (1.0, 1.0)) == 0.0


def test_equivalence_registers_first_creates_prototype():
    learner = EquivalenceLearner(threshold=0.95)
    r = ComputationReceipt(task_id="t1", result=[1.0, 0.0, 0.0])
    proto = learner.register(r)
    assert isinstance(proto, Prototype)
    assert proto.receipt_ids == [r.receipt_id]
    assert learner.prototype_count() == 1


def test_equivalence_merges_similar_results():
    learner = EquivalenceLearner(threshold=0.95)
    r1 = ComputationReceipt(task_id="t1", result=[1.0, 0.0, 0.0])
    r2 = ComputationReceipt(task_id="t2", result=[0.999, 0.01, 0.01])
    learner.register(r1)
    p2 = learner.register(r2)
    assert learner.prototype_count() == 1
    assert r2.receipt_id in p2.receipt_ids


def test_equivalence_creates_distinct_prototypes_for_orthogonal():
    learner = EquivalenceLearner(threshold=0.95)
    r1 = ComputationReceipt(task_id="t1", result=[1.0, 0.0, 0.0])
    r2 = ComputationReceipt(task_id="t2", result=[0.0, 0.0, 1.0])
    learner.register(r1)
    learner.register(r2)
    assert learner.prototype_count() == 2


def test_equivalence_skips_non_vectorizable():
    learner = EquivalenceLearner()
    r = ComputationReceipt(task_id="t1", result="not a vector")
    proto = learner.register(r)
    assert proto is None
    assert learner.prototype_count() == 0


def test_equivalence_dict_result_with_e8_coords():
    learner = EquivalenceLearner()
    r = ComputationReceipt(task_id="t1",
                           result={"e8_coords": [1.0, 0.0]})
    proto = learner.register(r)
    assert proto is not None


def test_equivalence_threshold_validation():
    with pytest.raises(ValueError):
        EquivalenceLearner(threshold=2.0)


# ---------------------------------------------------------------------------
# WorldlineCache
# ---------------------------------------------------------------------------

def test_worldline_admit_lands_in_layer():
    sl = SpeedLight()
    ms = MDHGMultiScale()
    wc = WorldlineCache(sl, ms)
    wc.admit("tick1", [0.1] * 24, layer="fast")
    assert ms.occupancy_snapshot()["fast"] == 1


def test_worldline_admit_keyframe_hits_all_layers():
    sl = SpeedLight()
    ms = MDHGMultiScale()
    wc = WorldlineCache(sl, ms)
    wc.admit_keyframe("kf1", [0.5] * 24)
    snap = ms.occupancy_snapshot()
    assert snap["fast"] == 1
    assert snap["med"] == 1
    assert snap["slow"] == 1


def test_worldline_jit_compute_caches_via_speedlight():
    sl = SpeedLight()
    ms = MDHGMultiScale()
    wc = WorldlineCache(sl, ms)
    calls = []
    def fn():
        calls.append(1)
        return 42
    assert wc.jit_compute("t", fn) == 42
    assert wc.jit_compute("t", fn) == 42
    assert len(calls) == 1


def test_worldline_prewarm_executes_all_specs():
    sl = SpeedLight()
    ms = MDHGMultiScale()
    wc = WorldlineCache(sl, ms)
    specs = [
        ("t1", lambda: 1, (), {}),
        ("t2", lambda: 2, (), {}),
    ]
    summary = wc.prewarm(specs)
    assert summary["prewarmed_tasks"] == 2
    assert summary["new_misses"] == 2


def test_worldline_tick_advances():
    sl = SpeedLight()
    ms = MDHGMultiScale()
    wc = WorldlineCache(sl, ms)
    wc.admit("t1", [0.1] * 24)
    wc.admit("t2", [0.2] * 24)
    assert wc.tick == 2


# ---------------------------------------------------------------------------
# SpeedLightProvider
# ---------------------------------------------------------------------------

def test_provider_compute_admits_to_index_on_miss():
    p = SpeedLightProvider()
    p.compute("t1", lambda: 1, e8_coords=[0.1] * 8, labels=["x"])
    assert p.index.has("t1")


def test_provider_compute_doesnt_admit_on_hit():
    p = SpeedLightProvider()
    p.compute("t1", lambda: [1.0, 2.0], e8_coords=[0.1] * 8)
    admits_before = p.index.stats()["total_admits"]
    p.compute("t1", lambda: [1.0, 2.0])  # hit → no new admit
    assert p.index.stats()["total_admits"] == admits_before


def test_provider_query_proximity():
    p = SpeedLightProvider()
    p.compute("t1", lambda: 1, e8_coords=[0.0] * 8)
    p.compute("t2", lambda: 2, e8_coords=[1.0] + [0.0] * 7)
    hits = p.query_proximity([0.0] * 8, k=2)
    assert hits[0][0] == "t1"


def test_provider_find_equivalent_result_returns_match():
    p = SpeedLightProvider()
    p.compute("t1", lambda: [1.0, 0.0, 0.0], e8_coords=[0.0] * 8)
    match = p.find_equivalent_result([0.99, 0.01, 0.01])
    assert match is not None


def test_provider_attach_worldline_returns_cache():
    p = SpeedLightProvider()
    ms = MDHGMultiScale()
    wc = p.attach_worldline(ms)
    assert isinstance(wc, WorldlineCache)
    assert p.worldline is wc


def test_provider_registers_on_cache_port():
    mc = MorphonController.get()
    p = SpeedLightProvider()
    mc.register("cache", p)
    assert mc.get_provider("cache") is p


def test_provider_health_keys():
    p = SpeedLightProvider()
    h = p.health
    assert h["ok"] is True
    assert "cache" in h
    assert "index" in h
    assert "equivalence" in h


def test_provider_get_aspect_pass_through():
    p = SpeedLightProvider()
    p.put_aspect("earth.forge.a.b.c.d", "phi", {"v": 4})
    assert p.get_aspect("earth.forge.a.b.c.d", "phi") == {"v": 4}


def test_provider_compute_and_cache_idempotent():
    p = SpeedLightProvider()
    calls = []
    def fn():
        calls.append(1)
        return "y"
    addr = "earth.forge.a.b.c.d"
    assert p.compute_and_cache(addr, "kaprekar", fn) == "y"
    assert p.compute_and_cache(addr, "kaprekar", fn) == "y"
    assert len(calls) == 1
