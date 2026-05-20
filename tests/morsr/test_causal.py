"""
Slot 25 tests — CausalDAG diagnostic over the receipt chain.

Verifies:
  1. Builds nodes from a receipt provider's recent() output.
  2. ancestors() walks parent_hash chain.
  3. descendants() does BFS over children.
  4. attribution() scores upstream contributions with type-weighted decay.
  5. predict_delta() returns the deferred-stub shape.
  6. Refresh rebuilds after the underlying chain grows.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from cmplx.morphon import MorphonController
from cmplx.morsr import CausalDAG, CausalNode


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ─────────────────────────────────────────────────────────────────────
# Fake receipt provider
# ─────────────────────────────────────────────────────────────────────

@dataclass
class _Receipt:
    receipt_hash: str
    receipt_id: str = ""
    receipt_type: str = "process"
    operation: str = ""
    atom_id: str = ""
    agent_id: str = ""
    parent_hash: str = ""
    payload: dict = None


class _FakeReceiptProvider:
    def __init__(self, receipts: list[_Receipt]):
        self._receipts = receipts

    def recent(self, limit: int = 100):
        return list(self._receipts[:limit])


# ─────────────────────────────────────────────────────────────────────
# 1. Basic node construction
# ─────────────────────────────────────────────────────────────────────

def test_dag_builds_nodes_from_receipts():
    receipts = [
        _Receipt(receipt_hash="h1", receipt_type="birth", operation="forge"),
        _Receipt(receipt_hash="h2", receipt_type="process", operation="step", parent_hash="h1"),
        _Receipt(receipt_hash="h3", receipt_type="gate", operation="admit", parent_hash="h2"),
    ]
    dag = CausalDAG(_FakeReceiptProvider(receipts))
    nodes = dag.nodes()
    assert len(nodes) == 3
    hashes = {n.receipt_hash for n in nodes}
    assert hashes == {"h1", "h2", "h3"}


def test_node_lookup_by_hash():
    receipts = [_Receipt(receipt_hash="x", receipt_type="birth")]
    dag = CausalDAG(_FakeReceiptProvider(receipts))
    assert dag.node("x") is not None
    assert dag.node("nonexistent") is None


def test_node_captures_payload_keys():
    receipts = [
        _Receipt(
            receipt_hash="h1",
            receipt_type="process",
            payload={"alpha": 1, "beta": 2, "gamma": 3},
        )
    ]
    dag = CausalDAG(_FakeReceiptProvider(receipts))
    n = dag.node("h1")
    assert n.payload_keys == ("alpha", "beta", "gamma")


# ─────────────────────────────────────────────────────────────────────
# 2. Ancestors walk
# ─────────────────────────────────────────────────────────────────────

def test_ancestors_walks_parent_chain():
    receipts = [
        _Receipt(receipt_hash="h1", receipt_type="birth"),
        _Receipt(receipt_hash="h2", receipt_type="process", parent_hash="h1"),
        _Receipt(receipt_hash="h3", receipt_type="process", parent_hash="h2"),
        _Receipt(receipt_hash="h4", receipt_type="gate", parent_hash="h3"),
    ]
    dag = CausalDAG(_FakeReceiptProvider(receipts))
    ancestors = dag.ancestors("h4", depth=10)
    # Nearest first: h3, h2, h1
    assert [a.receipt_hash for a in ancestors] == ["h3", "h2", "h1"]


def test_ancestors_respects_depth_limit():
    receipts = [_Receipt(receipt_hash=f"h{i}", parent_hash=f"h{i-1}" if i > 1 else "") for i in range(1, 6)]
    dag = CausalDAG(_FakeReceiptProvider(receipts))
    ancestors = dag.ancestors("h5", depth=2)
    assert len(ancestors) == 2
    assert [a.receipt_hash for a in ancestors] == ["h4", "h3"]


def test_ancestors_of_root_is_empty():
    receipts = [_Receipt(receipt_hash="root", parent_hash="")]
    dag = CausalDAG(_FakeReceiptProvider(receipts))
    assert dag.ancestors("root") == []


# ─────────────────────────────────────────────────────────────────────
# 3. Descendants BFS
# ─────────────────────────────────────────────────────────────────────

def test_descendants_bfs_two_children():
    receipts = [
        _Receipt(receipt_hash="parent", receipt_type="birth"),
        _Receipt(receipt_hash="left", parent_hash="parent"),
        _Receipt(receipt_hash="right", parent_hash="parent"),
        _Receipt(receipt_hash="left_child", parent_hash="left"),
    ]
    dag = CausalDAG(_FakeReceiptProvider(receipts))
    descendants = dag.descendants("parent", depth=10)
    hashes = {d.receipt_hash for d in descendants}
    assert hashes == {"left", "right", "left_child"}


def test_descendants_respects_depth_limit():
    receipts = [
        _Receipt(receipt_hash="root", parent_hash=""),
        _Receipt(receipt_hash="a", parent_hash="root"),
        _Receipt(receipt_hash="b", parent_hash="a"),
        _Receipt(receipt_hash="c", parent_hash="b"),
    ]
    dag = CausalDAG(_FakeReceiptProvider(receipts))
    d1 = dag.descendants("root", depth=1)
    assert {d.receipt_hash for d in d1} == {"a"}
    d2 = dag.descendants("root", depth=2)
    assert {d.receipt_hash for d in d2} == {"a", "b"}


# ─────────────────────────────────────────────────────────────────────
# 4. Attribution scoring
# ─────────────────────────────────────────────────────────────────────

def test_attribution_scores_decay_with_distance():
    receipts = [
        _Receipt(receipt_hash="far_gate", receipt_type="gate"),
        _Receipt(receipt_hash="proc_a", receipt_type="process", parent_hash="far_gate"),
        _Receipt(receipt_hash="proc_b", receipt_type="process", parent_hash="proc_a"),
        _Receipt(receipt_hash="outcome", receipt_type="process", parent_hash="proc_b"),
    ]
    dag = CausalDAG(_FakeReceiptProvider(receipts))
    report = dag.attribution("outcome", depth=10)
    assert report.upstream_count == 3
    # Even though the GATE has the highest base weight (1.0), it's 3 steps
    # away and gets decayed (default decay 0.7^2 = 0.49 → 0.49 vs proc_a's
    # 0.4 base undecayed = 0.4). So the gate should still beat proc_a.
    assert report.top_attribution.node.receipt_hash == "far_gate"
    # All scores sorted descending
    scores = [a.score for a in report.attributions]
    assert scores == sorted(scores, reverse=True)


def test_attribution_respects_custom_weights():
    receipts = [
        _Receipt(receipt_hash="h1", receipt_type="custom_high"),
        _Receipt(receipt_hash="h2", receipt_type="process", parent_hash="h1"),
        _Receipt(receipt_hash="outcome", receipt_type="process", parent_hash="h2"),
    ]
    dag = CausalDAG(
        _FakeReceiptProvider(receipts),
        type_weights={"custom_high": 2.0},  # override default
    )
    report = dag.attribution("outcome")
    # h1 (custom_high, weight 2.0, distance 2 → score = 2.0 * 0.7 = 1.4)
    # h2 (process, weight 0.4, distance 1 → score = 0.4)
    top = report.top_attribution
    assert top.node.receipt_hash == "h1"
    assert top.score > 1.0


def test_attribution_empty_when_outcome_has_no_ancestors():
    receipts = [_Receipt(receipt_hash="root", parent_hash="")]
    dag = CausalDAG(_FakeReceiptProvider(receipts))
    report = dag.attribution("root")
    assert report.upstream_count == 0
    assert report.top_attribution is None


# ─────────────────────────────────────────────────────────────────────
# 5. predict_delta stub
# ─────────────────────────────────────────────────────────────────────

def test_predict_delta_returns_deferred_stub():
    dag = CausalDAG(_FakeReceiptProvider([]))
    result = dag.predict_delta({"intervene_on": "h1", "new_op": "skip"})
    assert result["status"] == "deferred"
    assert "scenario" in result
    assert result["scenario"]["intervene_on"] == "h1"


# ─────────────────────────────────────────────────────────────────────
# 6. Refresh
# ─────────────────────────────────────────────────────────────────────

def test_refresh_rebuilds_after_chain_grows():
    receipts = [_Receipt(receipt_hash="h1", receipt_type="birth")]
    provider = _FakeReceiptProvider(receipts)
    dag = CausalDAG(provider)
    assert len(dag.nodes()) == 1

    # Grow the underlying chain.
    receipts.append(_Receipt(receipt_hash="h2", receipt_type="process", parent_hash="h1"))
    # Without refresh, the cached DAG still has 1 node.
    assert len(dag.nodes()) == 1

    dag.refresh()
    assert len(dag.nodes()) == 2
    assert dag.node("h2") is not None


# ─────────────────────────────────────────────────────────────────────
# 7. End-to-end with the real ReceiptProvider
# ─────────────────────────────────────────────────────────────────────

def test_end_to_end_with_real_receipt_provider():
    """CausalDAG works against the actual cmplx.receipt.ReceiptProvider."""
    from cmplx.receipt.provider import ReceiptProvider
    provider = ReceiptProvider()
    # Mint a small chain.
    r1 = provider.mint(receipt_type="birth", atom_id="atom_1", operation="forge")
    r2 = provider.mint(receipt_type="process", atom_id="atom_1", operation="step")
    r3 = provider.mint(receipt_type="gate", atom_id="atom_1", operation="admit")

    dag = CausalDAG(provider)
    nodes = dag.nodes()
    assert len(nodes) >= 3
    # Each minted receipt's hash should be a node.
    hashes = {n.receipt_hash for n in nodes}
    assert r1.receipt_hash in hashes
    assert r2.receipt_hash in hashes
    assert r3.receipt_hash in hashes
