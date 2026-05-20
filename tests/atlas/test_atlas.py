"""
Slots 26-27 tests — AtlasProvider (Mandelbrot deployment boundary + Julia c).

Verifies:
  1. Protocol compliance + registration on the `atlas` port.
  2. is_in_mandelbrot math (canonical in/out points).
  3. derive_c determinism + window placement.
  4. julia_c caches on morphon.fractal_coordinate.
  5. admit_to_deployment accepts in-set, rejects out-of-set + capacity.
  6. eviction round-trip.
  7. boundary_recompute evicts now-out-of-set morphons.
  8. admit_and_store integrates atlas as B-class trigger.
  9. Bootstrap registers atlas.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import (
    AtlasProvider as AtlasProviderProtocol,
    Morphon,
    MorphonController,
)
from cmplx.atlas import (
    AtlasProvider,
    derive_c,
    escape_time,
    is_in_mandelbrot,
)


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ─────────────────────────────────────────────────────────────────
# 1. Protocol + registration
# ─────────────────────────────────────────────────────────────────

def test_provider_satisfies_atlas_protocol():
    p = AtlasProvider()
    assert isinstance(p, AtlasProviderProtocol)


def test_atlas_is_in_known_ports():
    from cmplx.morphon import KNOWN_PORTS
    assert "atlas" in KNOWN_PORTS


def test_provider_registers_on_atlas_port():
    p = AtlasProvider()
    MorphonController.get().register("atlas", p)
    assert MorphonController.get().has("atlas")


# ─────────────────────────────────────────────────────────────────
# 2. Mandelbrot math
# ─────────────────────────────────────────────────────────────────

def test_origin_is_in_set():
    """c = 0 → orbit stays at 0 → in set."""
    assert is_in_mandelbrot(0+0j) is True


def test_minus_one_is_in_set():
    """c = -1 → orbit cycles 0, -1, 0, -1, ... → in set."""
    assert is_in_mandelbrot(-1+0j) is True


def test_large_positive_real_is_outside():
    """c = 2+0j: orbit 0 → 2 → 6 → ... escapes immediately."""
    assert is_in_mandelbrot(2+0j) is False


def test_far_imaginary_is_outside():
    assert is_in_mandelbrot(0+2j) is False


def test_escape_time_is_zero_or_low_for_outside_points():
    """Points far from the set escape within 1-2 iterations."""
    assert escape_time(10+10j, max_iter=100) < 5


def test_escape_time_caps_at_max_iter_for_inside_points():
    assert escape_time(0+0j, max_iter=100) == 100
    assert escape_time(-0.5+0j, max_iter=100) == 100


# ─────────────────────────────────────────────────────────────────
# 3. Julia c-assignment
# ─────────────────────────────────────────────────────────────────

def test_derive_c_is_deterministic():
    m = Morphon.forge(payload={"k": "v"})
    c1 = derive_c(m)
    c2 = derive_c(m)
    assert c1 == c2


def test_derive_c_differs_for_distinct_payloads():
    m1 = Morphon.forge(payload={"k": "v1"})
    m2 = Morphon.forge(payload={"k": "v2"})
    assert derive_c(m1) != derive_c(m2)


def test_derive_c_lands_in_interest_window():
    """c values should fall in [-2, 0.5] × [-1.25, 1.25]."""
    m = Morphon.forge(payload={"k": "v"})
    c = derive_c(m)
    assert -2.0 <= c.real <= 0.5
    assert -1.25 <= c.imag <= 1.25


# ─────────────────────────────────────────────────────────────────
# 4. julia_c caches on morphon.fractal_coordinate
# ─────────────────────────────────────────────────────────────────

def test_julia_c_caches_on_morphon():
    p = AtlasProvider()
    m = Morphon.forge(payload={"k": "v"})
    assert m.fractal_coordinate is None
    c = p.julia_c(m)
    assert m.fractal_coordinate == c


def test_julia_c_returns_existing_fractal_coordinate():
    """If morphon already has fractal_coordinate, julia_c returns it unchanged."""
    p = AtlasProvider()
    m = Morphon.forge(payload={"k": "v"})
    preset = complex(-0.5, 0.3)
    m.fractal_coordinate = preset
    assert p.julia_c(m) == preset


# ─────────────────────────────────────────────────────────────────
# 5. admit_to_deployment
# ─────────────────────────────────────────────────────────────────

def test_admit_accepts_in_set_morphon():
    """A morphon whose derived c lands in the set is admitted."""
    p = AtlasProvider()
    m = Morphon.forge(payload={"k": "v"})
    # Force an in-set c by pre-setting fractal_coordinate to 0+0j.
    m.fractal_coordinate = 0+0j
    ok, reason = p.admit_to_deployment(m)
    assert ok is True
    assert reason == ""
    assert p.deployment_stats()["deployed_count"] == 1


def test_admit_rejects_out_of_set_morphon():
    p = AtlasProvider()
    m = Morphon.forge(payload={"k": "v"})
    m.fractal_coordinate = 10+10j  # far outside
    ok, reason = p.admit_to_deployment(m)
    assert ok is False
    assert "outside" in reason


def test_admit_rejects_when_capacity_exhausted():
    """Pre-fill capacity to 1, then try to admit a second morphon."""
    p = AtlasProvider(capacity=1)
    m1 = Morphon.forge(payload={"k": "v1"})
    m1.fractal_coordinate = 0+0j
    m2 = Morphon.forge(payload={"k": "v2"})
    m2.fractal_coordinate = -0.5+0j
    ok1, _ = p.admit_to_deployment(m1)
    ok2, reason2 = p.admit_to_deployment(m2)
    assert ok1 is True
    assert ok2 is False
    assert "capacity" in reason2


def test_admit_is_idempotent_for_same_morphon():
    p = AtlasProvider()
    m = Morphon.forge(payload={"k": "v"})
    m.fractal_coordinate = 0+0j
    p.admit_to_deployment(m)
    ok, reason = p.admit_to_deployment(m)
    assert ok is True
    assert reason == "already-deployed"
    assert p.deployment_stats()["deployed_count"] == 1


# ─────────────────────────────────────────────────────────────────
# 6. Eviction
# ─────────────────────────────────────────────────────────────────

def test_evict_removes_morphon():
    p = AtlasProvider()
    m = Morphon.forge(payload={"k": "v"})
    m.fractal_coordinate = 0+0j
    p.admit_to_deployment(m)
    assert p.evict(m.id) is True
    assert p.deployment_stats()["deployed_count"] == 0


def test_evict_unknown_returns_false():
    p = AtlasProvider()
    assert p.evict("not_a_real_id") is False


# ─────────────────────────────────────────────────────────────────
# 7. boundary_recompute
# ─────────────────────────────────────────────────────────────────

def test_boundary_recompute_evicts_now_out_of_set():
    """Mutate a deployed morphon's c after admission, then recompute."""
    p = AtlasProvider()
    m = Morphon.forge(payload={"k": "v"})
    m.fractal_coordinate = 0+0j
    p.admit_to_deployment(m)
    # Externally mutate the deployed c by re-writing the dict entry.
    # (Direct mutation of internals is for testing the recompute path.)
    p._deployed[m.id] = 100+100j  # noqa — testing internal state
    report = p.boundary_recompute()
    assert m.id in report["evicted_ids"]
    assert report["deployed_count"] == 0


def test_boundary_recompute_keeps_in_set_morphons():
    p = AtlasProvider()
    m = Morphon.forge(payload={"k": "v"})
    m.fractal_coordinate = 0+0j
    p.admit_to_deployment(m)
    report = p.boundary_recompute()
    assert report["evicted_count"] == 0
    assert report["deployed_count"] == 1


# ─────────────────────────────────────────────────────────────────
# 8. Integration with admit_and_store
# ─────────────────────────────────────────────────────────────────

class _FakeConstraints:
    def admit(self, morphon):
        return True, ""


class _FakeAddressing:
    def channel_for(self, morphon):
        return 3


class _FakeMemory:
    def __init__(self):
        self.stored = {}

    def store(self, morphon):
        self.stored[morphon.id] = morphon

    def fetch(self, morphon_id):
        return self.stored.get(morphon_id)


def test_admit_and_store_uses_atlas_when_registered():
    """When atlas is registered, admit_and_store includes it in the sequence."""
    ctrl = MorphonController.get()
    ctrl.register("constraints", _FakeConstraints())
    ctrl.register("addressing", _FakeAddressing())
    ctrl.register("memory", _FakeMemory())
    atlas = AtlasProvider()
    ctrl.register("atlas", atlas)

    m = Morphon.forge(payload={"k": "v"})
    m.fractal_coordinate = 0+0j  # ensure in-set
    result = ctrl.admit_and_store(m)
    assert any(r.operation == "admit_and_store" for r in result.receipts)
    # Atlas saw the morphon
    assert atlas.deployment_stats()["deployed_count"] == 1


def test_admit_and_store_rejects_when_atlas_rejects():
    ctrl = MorphonController.get()
    ctrl.register("constraints", _FakeConstraints())
    ctrl.register("addressing", _FakeAddressing())
    ctrl.register("memory", _FakeMemory())
    ctrl.register("atlas", AtlasProvider())

    m = Morphon.forge(payload={"k": "v"})
    m.fractal_coordinate = 100+100j  # out of set
    with pytest.raises(PermissionError, match="rejected by atlas"):
        ctrl.admit_and_store(m)


def test_admit_and_store_skips_atlas_when_unregistered():
    """Existing behavior unchanged when atlas isn't registered."""
    ctrl = MorphonController.get()
    ctrl.register("constraints", _FakeConstraints())
    ctrl.register("addressing", _FakeAddressing())
    ctrl.register("memory", _FakeMemory())
    # No atlas registration.
    m = Morphon.forge(payload={"k": "v"})
    result = ctrl.admit_and_store(m)
    assert result.dr_channel == 3


# ─────────────────────────────────────────────────────────────────
# 9. Bootstrap registers atlas
# ─────────────────────────────────────────────────────────────────

def test_bootstrap_registers_atlas_port():
    from runtime.cmplx_bootstrap import register_all
    status = register_all()
    assert "atlas" in status
    assert status["atlas"] == "registered (in-process)"
    assert MorphonController.get().has("atlas")


def test_bootstrap_registered_atlas_satisfies_protocol():
    from runtime.cmplx_bootstrap import register_all
    register_all()
    p = MorphonController.get().get_provider("atlas")
    assert isinstance(p, AtlasProviderProtocol)


# ─────────────────────────────────────────────────────────────────
# 10. Health + repr
# ─────────────────────────────────────────────────────────────────

def test_health_reports_deployment():
    p = AtlasProvider()
    h = p.health
    assert h["ok"] is True
    assert h["service"] == "atlas_provider"
    assert "deployment" in h
    assert h["deployment"]["capacity"] == 196_560


def test_repr_includes_capacity():
    p = AtlasProvider()
    assert "/196560" in repr(p)
