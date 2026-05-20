"""
Slot 24 tests — SpectralHealth diagnostic.

Verifies:
  1. Empty graph → zero-filled report.
  2. Triangle (3-node clique) → connected, gap > 0.
  3. Disconnected graph → connected_components ≥ 2, spectral_gap = 0.
  4. Path graph (3 nodes) → spectral_gap < clique gap (Cheeger intuition).
  5. Single node → trivial report.
  6. Provider-backed walk reaches the right node set.
  7. Health flag tracks connected + gap threshold.
"""
from __future__ import annotations

import pytest

from cmplx.morsr import SpectralHealth, SpectralReport


# ---------------------------------------------------------------------------
# 1. Empty graph
# ---------------------------------------------------------------------------

def test_empty_edges_report_is_zero_filled():
    s = SpectralHealth(edges=[])
    r = s.report()
    assert r.node_count == 0
    assert r.edge_count == 0
    assert r.spectral_gap == 0.0
    assert r.connected_components == 0
    assert r.healthy is False


# ---------------------------------------------------------------------------
# 2. Triangle clique
# ---------------------------------------------------------------------------

def test_triangle_is_connected_with_positive_gap():
    s = SpectralHealth(edges=[("a", "b"), ("b", "c"), ("a", "c")])
    r = s.report()
    assert r.node_count == 3
    assert r.edge_count == 3
    assert r.connected_components == 1
    assert r.spectral_gap > 0.0
    # Triangle (K_3) has Laplacian eigenvalues {0, 3, 3}, so gap = 3.
    assert abs(r.spectral_gap - 3.0) < 1e-6
    assert r.max_degree == 2
    assert r.min_degree == 2
    assert r.healthy is True


# ---------------------------------------------------------------------------
# 3. Disconnected graph
# ---------------------------------------------------------------------------

def test_disconnected_graph_components_at_least_two():
    """Two disjoint edges form two components → spectral_gap = 0."""
    s = SpectralHealth(edges=[("a", "b"), ("c", "d")])
    r = s.report()
    assert r.node_count == 4
    assert r.edge_count == 2
    assert r.connected_components == 2
    assert r.spectral_gap == 0.0
    assert r.healthy is False


def test_three_isolated_components():
    s = SpectralHealth(edges=[
        ("a", "b"),
        ("c", "d"),
        ("e", "f"),
    ])
    r = s.report()
    assert r.connected_components == 3


# ---------------------------------------------------------------------------
# 4. Path graph gap < clique gap
# ---------------------------------------------------------------------------

def test_path_gap_less_than_triangle_gap():
    """P_3 has eigenvalues {0, 1, 3}, so its gap = 1 < triangle gap = 3."""
    path = SpectralHealth(edges=[("a", "b"), ("b", "c")])
    triangle = SpectralHealth(edges=[("a", "b"), ("b", "c"), ("a", "c")])
    assert path.report().spectral_gap < triangle.report().spectral_gap


# ---------------------------------------------------------------------------
# 5. Single-node graph
# ---------------------------------------------------------------------------

def test_isolated_node_via_provider():
    """Single node with no neighbors — one component, zero edges, zero gap."""
    class _OneNodeMem:
        def neighbors(self, node_id):
            return []
    s = SpectralHealth(memory_provider=_OneNodeMem(), seed_ids=["x"])
    r = s.report()
    assert r.node_count == 1
    assert r.edge_count == 0
    assert r.connected_components == 1
    assert r.spectral_gap == 0.0
    # Single node = trivially "connected" but no gap → not healthy
    assert r.healthy is False


# ---------------------------------------------------------------------------
# 6. Provider-backed walk
# ---------------------------------------------------------------------------

def test_provider_walk_reaches_all_reachable_nodes():
    """Provider walk should BFS from seed and find the full connected set."""
    graph = {
        "a": ["b"],
        "b": ["a", "c"],
        "c": ["b", "d"],
        "d": ["c"],
        # disconnected:
        "z": ["y"],
        "y": ["z"],
    }

    class _Provider:
        def neighbors(self, node_id):
            return list(graph.get(node_id, []))

    s = SpectralHealth(memory_provider=_Provider(), seed_ids=["a"])
    r = s.report()
    # Walk from "a" reaches a, b, c, d. Doesn't touch z, y.
    assert r.node_count == 4


def test_provider_walk_caps_at_max_nodes():
    """Walk stops at 1000 nodes by default to prevent runaway exploration."""
    # Build a 1500-node line graph; walk should stop at 1000.
    class _LineProvider:
        def neighbors(self, node_id):
            try:
                i = int(node_id)
            except ValueError:
                return []
            return [str(i + 1)] if i < 1500 else []

    s = SpectralHealth(memory_provider=_LineProvider(), seed_ids=["0"])
    r = s.report()
    assert r.node_count <= 1000


# ---------------------------------------------------------------------------
# 7. Health flag tracks connected + gap
# ---------------------------------------------------------------------------

def test_healthy_requires_connected_and_meaningful_gap():
    # K_3 with default threshold (0.01) — gap is 3, well above. Healthy.
    s_healthy = SpectralHealth(edges=[("a", "b"), ("b", "c"), ("a", "c")])
    assert s_healthy.report().healthy is True

    # Same K_3 but threshold = 5 (above its gap) — not healthy.
    s_strict = SpectralHealth(
        edges=[("a", "b"), ("b", "c"), ("a", "c")],
        healthy_gap_threshold=5.0,
    )
    assert s_strict.report().healthy is False


def test_eigenvalues_sample_is_sorted_ascending():
    s = SpectralHealth(edges=[("a", "b"), ("b", "c"), ("a", "c")])
    eigs = s.report().eigenvalues_sample
    assert eigs == sorted(eigs)
    # K_3 eigenvalues: {0, 3, 3}
    assert abs(eigs[0]) < 1e-6
    assert abs(eigs[1] - 3.0) < 1e-6


# ---------------------------------------------------------------------------
# 8. Construction validation
# ---------------------------------------------------------------------------

def test_construction_requires_edges_or_provider():
    with pytest.raises(ValueError, match="requires either"):
        SpectralHealth()  # no edges and no provider


def test_construction_with_only_provider_but_no_seed():
    class _DummyMem:
        def neighbors(self, x):
            return []
    with pytest.raises(ValueError, match="requires either"):
        SpectralHealth(memory_provider=_DummyMem())
