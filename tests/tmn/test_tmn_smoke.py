"""Smoke tests for cmplx.tmn — construction, forward, recall, learn, grow, save/load."""
from __future__ import annotations

import json
import os
import tempfile

import numpy as np
import pytest

from cmplx.tmn import (
    ChannelState,
    ExpertModule,
    Manifold,
    MicroController,
    TMNProvider,
    TriadicManifoldNetwork,
    TriadicState,
)


class TestConstruction:
    def test_provider_constructs(self):
        p = TMNProvider()
        h = p.health()
        assert h["dims"] == 24
        assert h["epoch"] == 0
        assert h["frozen"] is False

    def test_network_constructs_with_defaults(self):
        net = TriadicManifoldNetwork()
        assert net.dims == 24
        assert net.max_dims == 96
        assert net.weights.shape == (24, 24)

    def test_network_constructs_with_custom_dims(self):
        net = TriadicManifoldNetwork(init_dims=8, max_dims=32)
        assert net.dims == 8
        assert net.weights.shape == (8, 8)


class TestForwardRecall:
    def test_forward_shape(self):
        net = TriadicManifoldNetwork(init_dims=8)
        x = np.random.randn(8)
        out = net.forward(x)
        assert out.shape == (8,)

    def test_recall_shape(self):
        net = TriadicManifoldNetwork(init_dims=8)
        x = np.random.randn(8)
        out = net.recall(x)
        assert out.shape == (8,)

    def test_forward_pads_short_input(self):
        net = TriadicManifoldNetwork(init_dims=8)
        x = np.random.randn(3)
        out = net.forward(x)
        assert out.shape == (8,)

    def test_forward_trims_long_input(self):
        net = TriadicManifoldNetwork(init_dims=8)
        x = np.random.randn(20)
        out = net.forward(x)
        assert out.shape == (8,)

    def test_chirality_coherence_range(self):
        net = TriadicManifoldNetwork(init_dims=8)
        x = np.random.randn(8)
        c = net.chirality_coherence(x)
        assert -1.0 <= c <= 1.0


class TestLearn:
    def test_learn_increments_epoch(self):
        net = TriadicManifoldNetwork(init_dims=8)
        r = net.learn("hello", "world")
        assert r["epoch"] == 1
        assert "mutual_information" in r

    def test_learn_updates_weights(self):
        net = TriadicManifoldNetwork(init_dims=8)
        w_before = net.weights.copy()
        net.learn("input", "output")
        assert not np.allclose(net.weights, w_before)

    def test_frozen_network_does_not_learn(self):
        net = TriadicManifoldNetwork(init_dims=8)
        net.frozen = True
        r = net.learn("a", "b")
        assert r["status"] == "frozen"


class TestGrow:
    def test_grow_increases_dims(self):
        net = TriadicManifoldNetwork(init_dims=8, max_dims=24, growth_increment=8)
        net.mutual_information = 0.6
        net.epoch = 100
        grew = net.grow()
        assert grew is True
        assert net.dims == 16

    def test_grow_respects_max_dims(self):
        net = TriadicManifoldNetwork(init_dims=8, max_dims=8)
        grew = net.grow()
        assert grew is False


class TestCrystallize:
    def test_crystallize_produces_glyph(self):
        net = TriadicManifoldNetwork(init_dims=8, max_dims=8)
        net.epoch = 400
        # Force low triadic energy
        net.triads.noether = np.zeros((3, 3))
        net.triads.shannon = np.zeros((3, 3))
        net.triads.landauer = np.zeros((3, 3))
        glyph = net.crystallize()
        assert "content_hash" in glyph
        assert "e8_address" in glyph
        assert net.crystallized is True

    def test_spawn_next_generation(self):
        net = TriadicManifoldNetwork(init_dims=8, max_dims=8)
        net.epoch = 400
        net.triads.noether = np.zeros((3, 3))
        net.triads.shannon = np.zeros((3, 3))
        net.triads.landauer = np.zeros((3, 3))
        glyph = net.crystallize()
        child = net.spawn_next_generation()
        assert child.generation == 1
        assert child.dims == 8
        assert not np.allclose(child.weights, 0)

    def test_spawn_without_glyph_raises(self):
        net = TriadicManifoldNetwork(init_dims=8)
        with pytest.raises(ValueError):
            net.spawn_next_generation()


class TestPersistence:
    def test_save_and_load_roundtrip(self):
        net = TriadicManifoldNetwork(init_dims=8)
        net.learn("a", "b")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "tmn.json")
            net.save(path)
            loaded = TriadicManifoldNetwork.load(path)
            assert loaded.dims == net.dims
            assert loaded.epoch == net.epoch
            np.testing.assert_allclose(loaded.weights, net.weights)

    def test_provider_save_load(self):
        p = TMNProvider(init_dims=8)
        p.network.learn("x", "y")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "tmn.json")
            p.save(path)
            loaded = TMNProvider.load(path)
            assert loaded.health()["epoch"] == p.health()["epoch"]


class TestCodeAnalysis:
    def test_analyze_code_returns_metrics(self):
        net = TriadicManifoldNetwork(init_dims=8)
        r = net.analyze_code("def foo(): pass")
        assert "encoding_norm" in r
        assert "triadic_scores" in r

    def test_query_returns_array(self):
        net = TriadicManifoldNetwork(init_dims=8)
        out = net.query("hello world")
        assert isinstance(out, np.ndarray)
        assert out.shape == (8,)


class TestManifold:
    def test_manifold_health_report(self):
        m = Manifold(dims=8, block_size=4)
        hr = m.health_report()
        assert hr["n_channels"] == 10
        assert "avg_stability" in hr

    def test_manifold_tick(self):
        m = Manifold(dims=8, block_size=4)
        m.tick()
        assert m._tick_count == 1

    def test_block_norms(self):
        m = Manifold(dims=8, block_size=4)
        norms = m.block_norms()
        assert norms.shape == (2, 2)

    def test_merge_and_split(self):
        m1 = Manifold(dims=8, block_size=4)
        m2 = Manifold(dims=8, block_size=4)
        m1.merge_from(m2, block_indices=[(0, 0)], alpha=0.5)
        child = m1.split([(0, 0)])
        assert child.weights.shape == (8, 8)


class TestMicroController:
    def test_microcontroller_observe(self):
        mc = MicroController(0, [(0, 0)], block_size=4)
        block = np.random.randn(4, 4)
        mc.observe({(0, 0): block})
        assert mc.state.update_count == 0  # observe doesn't count
        assert mc.state.energy > 0

    def test_microcontroller_heal(self):
        mc = MicroController(0, [(0, 0)], block_size=4)
        block = np.random.randn(4, 4)
        healed = mc.heal({(0, 0): block}, lambda i, j: None)
        assert (0, 0) in healed

    def test_parity_check(self):
        mc_data = MicroController(0, [(0, 0)], block_size=4)
        mc_data.state.stability = 0.2
        mc_parity = MicroController(8, [], is_parity=True, block_size=4)
        unstable = mc_parity.parity_check([mc_data])
        assert 0 in unstable
