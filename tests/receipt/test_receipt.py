"""
Tests for cmplx.receipt — Merkle-chained operation provenance.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import MorphonController
from cmplx.receipt import (
    CANONICAL_TYPES,
    DagEdge,
    DagEdgeStore,
    GENESIS_HASH,
    Receipt,
    ReceiptChain,
    ReceiptProvider,
    ReceiptType,
    compute_receipt_hash,
    is_canonical_type,
    load_geolight,
    load_toklight,
    merge_timelines,
    read_jsonl,
)


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# Types + constants
# ---------------------------------------------------------------------------

def test_genesis_hash_is_64_zeros():
    assert GENESIS_HASH == "0" * 64


def test_canonical_types_count():
    assert len(CANONICAL_TYPES) == 10
    for name in ("MINT", "BOND", "PROCESS", "GATE", "CROSSING"):
        assert name in CANONICAL_TYPES


def test_is_canonical_type():
    assert is_canonical_type("MINT")
    assert not is_canonical_type("mint")
    assert not is_canonical_type("UNKNOWN")


def test_compute_receipt_hash_deterministic():
    h1 = compute_receipt_hash(GENESIS_HASH, "op", "atom", 1000.0)
    h2 = compute_receipt_hash(GENESIS_HASH, "op", "atom", 1000.0)
    assert h1 == h2
    assert len(h1) == 64


def test_compute_receipt_hash_diverges_on_input_change():
    h1 = compute_receipt_hash(GENESIS_HASH, "op", "atom", 1000.0)
    h2 = compute_receipt_hash(GENESIS_HASH, "op", "atom", 1000.1)
    assert h1 != h2


# ---------------------------------------------------------------------------
# Receipt dataclass
# ---------------------------------------------------------------------------

def test_receipt_auto_populates_id_hash_timestamp():
    r = Receipt(operation="test", atom_id="a1")
    assert r.receipt_id
    assert r.receipt_hash
    assert r.created_at > 0
    assert r.operator == ""  # agent_id was empty so operator stays empty


def test_receipt_operator_defaults_to_agent_id():
    r = Receipt(agent_id="alice", operation="x")
    assert r.operator == "alice"


def test_receipt_source_tag_auto_built():
    r = Receipt(agent_id="alice", epoch=5)
    assert "alice@epoch5::receipt::" in r.source_tag


def test_receipt_verify_hash_round_trip():
    r = Receipt(operation="op", atom_id="a1")
    assert r.verify_hash()


def test_receipt_verify_hash_fails_on_tamper():
    r = Receipt(operation="op", atom_id="a1")
    # Tamper with operation but keep stored hash → mismatch
    r.operation = "TAMPERED"
    assert not r.verify_hash()


def test_receipt_to_from_dict_round_trip():
    r1 = Receipt(
        agent_id="alice", atom_id="a1", operation="x",
        delta_phi=-0.5, snap_labels=["tag1", "tag2"], epoch=3,
    )
    r2 = Receipt.from_dict(r1.to_dict())
    assert r1.receipt_id == r2.receipt_id
    assert r1.receipt_hash == r2.receipt_hash
    assert r1.snap_labels == r2.snap_labels


# ---------------------------------------------------------------------------
# ReceiptChain — minting + linkage
# ---------------------------------------------------------------------------

def test_chain_starts_empty():
    c = ReceiptChain()
    assert c.length == 0
    assert c.head == GENESIS_HASH


def test_chain_mint_links_to_head():
    c = ReceiptChain()
    r1 = c.mint(operation="op1", atom_id="a1")
    r2 = c.mint(operation="op2", atom_id="a1")
    assert r1.prev_hash == GENESIS_HASH
    assert r2.prev_hash == r1.receipt_hash
    assert c.head == r2.receipt_hash


def test_chain_mint_advances_chain_index():
    c = ReceiptChain()
    r1 = c.mint(operation="op1")
    r2 = c.mint(operation="op2")
    r3 = c.mint(operation="op3")
    assert r1.chain_index == 0
    assert r2.chain_index == 1
    assert r3.chain_index == 2


def test_chain_explicit_parent_overrides_head():
    c = ReceiptChain()
    r1 = c.mint(operation="op1")
    # Mint r2 explicitly chained to r1 (which equals head anyway)
    r2 = c.mint(operation="op2", parent_hash=r1.receipt_hash)
    assert r2.prev_hash == r1.receipt_hash


def test_chain_rejects_duplicate_id():
    c = ReceiptChain()
    r = c.mint(operation="op1")
    # Force a duplicate id by appending directly with same id
    dup = Receipt(receipt_id=r.receipt_id, operation="op2")
    with pytest.raises(RuntimeError, match="already in chain"):
        c.append_receipt(dup)


# ---------------------------------------------------------------------------
# Multi-index lookup
# ---------------------------------------------------------------------------

def test_chain_by_id():
    c = ReceiptChain()
    r = c.mint(operation="op", agent_id="alice")
    assert c.by_id(r.receipt_id) is r


def test_chain_by_hash():
    c = ReceiptChain()
    r = c.mint(operation="op", agent_id="alice")
    assert c.by_hash(r.receipt_hash) is r


def test_chain_by_agent():
    c = ReceiptChain()
    c.mint(operation="op1", agent_id="alice")
    c.mint(operation="op2", agent_id="bob")
    c.mint(operation="op3", agent_id="alice")
    alices = c.by_agent("alice")
    assert len(alices) == 2
    assert all(r.agent_id == "alice" for r in alices)


def test_chain_by_agent_limit():
    c = ReceiptChain()
    for i in range(5):
        c.mint(operation=f"op{i}", agent_id="alice")
    latest = c.by_agent("alice", limit=2)
    assert len(latest) == 2


def test_chain_by_type():
    c = ReceiptChain()
    c.mint(receipt_type=ReceiptType.MINT.value, operation="m1")
    c.mint(receipt_type=ReceiptType.BOND.value, operation="b1")
    c.mint(receipt_type=ReceiptType.MINT.value, operation="m2")
    mints = c.by_type(ReceiptType.MINT.value)
    assert len(mints) == 2


def test_chain_by_atom():
    c = ReceiptChain()
    c.mint(operation="op1", atom_id="atom-A")
    c.mint(operation="op2", atom_id="atom-B")
    c.mint(operation="op3", atom_id="atom-A")
    a = c.by_atom("atom-A")
    assert len(a) == 2


def test_chain_for_atom_chronological():
    c = ReceiptChain()
    r1 = c.mint(operation="op1", atom_id="a1")
    c.mint(operation="other")
    r2 = c.mint(operation="op2", atom_id="a1")
    chain = c.chain_for_atom("a1")
    assert chain == [r1, r2]


# ---------------------------------------------------------------------------
# Walking + verification
# ---------------------------------------------------------------------------

def test_walk_chain_from_head():
    c = ReceiptChain()
    r1 = c.mint(operation="op1")
    r2 = c.mint(operation="op2")
    r3 = c.mint(operation="op3")
    walked = c.walk_chain()
    assert [r.receipt_id for r in walked] == [r3.receipt_id, r2.receipt_id, r1.receipt_id]


def test_walk_chain_max_depth_limits_walk():
    c = ReceiptChain()
    for i in range(10):
        c.mint(operation=f"op{i}")
    walked = c.walk_chain(max_depth=3)
    assert len(walked) == 3


def test_walk_chain_empty_returns_empty():
    c = ReceiptChain()
    assert c.walk_chain() == []


def test_verify_full_chain_valid():
    c = ReceiptChain()
    for i in range(5):
        c.mint(operation=f"op{i}", atom_id=f"a{i}")
    result = c.verify()
    assert result["valid"]
    assert result["length"] == 5
    assert result["breaks"] == []


def test_verify_from_specific_hash():
    c = ReceiptChain()
    r1 = c.mint(operation="op1")
    r2 = c.mint(operation="op2")
    c.mint(operation="op3")
    result = c.verify(receipt_hash=r2.receipt_hash, max_depth=10)
    assert result["chain_depth"] == 2
    assert result["reaches_genesis"]


def test_verify_chain_detects_hash_tampering():
    c = ReceiptChain()
    r1 = c.mint(operation="op1")
    c.mint(operation="op2")
    # Tamper with r1's stored operation field; hash won't re-derive
    r1.operation = "TAMPERED_OP"
    result = c.verify()
    assert not result["valid"]
    assert len(result["breaks"]) > 0


# ---------------------------------------------------------------------------
# Recent + stats + clear
# ---------------------------------------------------------------------------

def test_chain_recent():
    c = ReceiptChain()
    for i in range(10):
        c.mint(operation=f"op{i}")
    recent = c.recent(limit=3)
    assert len(recent) == 3
    # recent returns the LAST 3 in chronological order
    assert recent[-1].operation == "op9"


def test_chain_stats_keys():
    c = ReceiptChain()
    c.mint(receipt_type=ReceiptType.MINT.value, agent_id="alice", atom_id="a1")
    c.mint(receipt_type=ReceiptType.BOND.value, agent_id="bob", atom_id="a1")
    stats = c.stats()
    assert stats["length"] == 2
    assert stats["agents"] == 2
    assert stats["atoms_tracked"] == 1
    assert stats["by_type"]["MINT"] == 1
    assert stats["by_type"]["BOND"] == 1


def test_chain_clear_resets():
    c = ReceiptChain()
    c.mint(operation="op")
    c.clear()
    assert c.length == 0
    assert c.head == GENESIS_HASH


# ---------------------------------------------------------------------------
# DagEdge + DagEdgeStore
# ---------------------------------------------------------------------------

def test_dag_edge_key():
    e = DagEdge(source_id="A", target_id="B", edge_type="bond")
    assert e.key == ("A", "B", "bond")


def test_dag_store_add_and_lookup():
    s = DagEdgeStore()
    s.add(DagEdge(source_id="A", target_id="B"))
    assert s.has("A", "B", "depends")
    assert s.get("A", "B", "depends") is not None


def test_dag_store_upsert_updates_weight():
    s = DagEdgeStore()
    s.add(DagEdge(source_id="A", target_id="B", weight=1.0))
    s.add(DagEdge(source_id="A", target_id="B", weight=5.0))
    assert s.get("A", "B").weight == 5.0
    assert len(s) == 1  # still one edge


def test_dag_store_outgoing_incoming():
    s = DagEdgeStore()
    s.add(DagEdge(source_id="A", target_id="B"))
    s.add(DagEdge(source_id="A", target_id="C"))
    s.add(DagEdge(source_id="C", target_id="A"))
    assert len(s.outgoing("A")) == 2
    assert len(s.incoming("A")) == 1


def test_dag_store_edges_of():
    s = DagEdgeStore()
    s.add(DagEdge(source_id="A", target_id="B"))
    s.add(DagEdge(source_id="C", target_id="A"))
    eo = s.edges_of("A")
    assert len(eo["outgoing"]) == 1
    assert len(eo["incoming"]) == 1


def test_dag_store_by_type():
    s = DagEdgeStore()
    s.add(DagEdge(source_id="A", target_id="B", edge_type="bond"))
    s.add(DagEdge(source_id="C", target_id="D", edge_type="depends"))
    s.add(DagEdge(source_id="E", target_id="F", edge_type="bond"))
    bonds = s.by_type("bond")
    assert len(bonds) == 2


# ---------------------------------------------------------------------------
# ReceiptProvider — composite (the `receipt` port)
# ---------------------------------------------------------------------------

def test_provider_mint_typed_helpers():
    p = ReceiptProvider()
    r_mint = p.mint_mint(atom_id="atom1", agent_id="alice")
    r_bond = p.mint_bond(source_atom="A", target_atom="B", agent_id="alice")
    r_gate = p.mint_gate(atom_id="atom1", accepted=True, agent_id="alice")
    r_cross = p.mint_crossing(atom_id="atom1", boundary="layer3", agent_id="alice")
    assert r_mint.receipt_type == "MINT"
    assert r_bond.receipt_type == "BOND"
    assert r_gate.receipt_type == "GATE"
    assert r_cross.receipt_type == "CROSSING"


def test_provider_chain_walk_and_verify():
    p = ReceiptProvider()
    p.mint(operation="op1")
    p.mint(operation="op2")
    walked = p.walk_chain()
    assert len(walked) == 2
    assert p.verify_chain()["valid"]


def test_provider_dag_helpers():
    p = ReceiptProvider()
    p.add_edge("A", "B", edge_type="bond", weight=0.5)
    eo = p.edges_of("A")
    assert len(eo["outgoing"]) == 1
    assert eo["outgoing"][0]["weight"] == 0.5


def test_provider_registers_on_receipt_port():
    mc = MorphonController.get()
    p = ReceiptProvider()
    mc.register("receipt", p)
    assert mc.get_provider("receipt") is p


def test_provider_health_keys():
    p = ReceiptProvider()
    p.mint(operation="op")
    p.add_edge("A", "B")
    h = p.health
    assert h["ok"] is True
    assert h["service"] == "receipt_provider"
    assert h["chain"]["length"] == 1
    assert h["dag"]["total_edges"] == 1


def test_provider_lookup_passthroughs():
    p = ReceiptProvider()
    r = p.mint(operation="op", agent_id="alice", atom_id="a1",
               receipt_type=ReceiptType.MINT.value)
    assert p.by_id(r.receipt_id) is r
    assert p.by_hash(r.receipt_hash) is r
    assert r in p.by_agent("alice")
    assert r in p.by_atom("a1")
    assert r in p.by_type("MINT")


def test_provider_chain_for_atom():
    p = ReceiptProvider()
    p.mint(operation="op1", atom_id="A")
    p.mint(operation="other", atom_id="B")
    p.mint(operation="op2", atom_id="A")
    chain = p.chain_for_atom("A")
    assert len(chain) == 2


def test_provider_recent():
    p = ReceiptProvider()
    for i in range(5):
        p.mint(operation=f"op{i}")
    assert len(p.recent(limit=3)) == 3


# ---------------------------------------------------------------------------
# Integration scenario: receipt as cross-system spine
# ---------------------------------------------------------------------------

def test_integration_atom_lifecycle_via_receipts():
    """Simulate an atom's lifecycle: BIRTH → BOND → GATE → CROSSING → DEATH."""
    p = ReceiptProvider()
    atom = "atom-001"
    p.mint(ReceiptType.BIRTH.value, atom_id=atom, operation="birth")
    p.mint_bond(source_atom=atom, target_atom="atom-002")
    p.mint_gate(atom_id=atom, accepted=True, delta_phi=-0.1)
    p.mint_crossing(atom_id=atom, boundary="layer3->layer4")
    p.mint(ReceiptType.DEATH.value, atom_id=atom, operation="death")

    chain = p.chain_for_atom(atom)
    # 5 receipts touched this atom
    assert len(chain) == 5
    # Walk back from head; should reach genesis
    walked = p.walk_chain()
    assert len(walked) == 5
    # Chain still verifies
    assert p.verify_chain()["valid"]


def test_integration_dag_topology_from_bonds():
    """When bonds are formed, DAG edges link bonded atoms."""
    p = ReceiptProvider()
    p.mint_bond(source_atom="A", target_atom="B")
    p.add_edge("A", "B", edge_type="bond", weight=1.0, snap_overlap=["tag1"])
    p.add_edge("B", "C", edge_type="bond", weight=0.5)
    # A points outward to B
    out_a = p.edges_of("A")["outgoing"]
    assert len(out_a) == 1
    assert out_a[0]["snap_overlap"] == ["tag1"]
    # B is reachable as both source and target
    edges_b = p.edges_of("B")
    assert len(edges_b["incoming"]) == 1
    assert len(edges_b["outgoing"]) == 1


# ---------------------------------------------------------------------------
# receipts_bridge (GeoLight / TokLight JSONL)
# ---------------------------------------------------------------------------


def test_read_jsonl_missing_path(tmp_path):
    assert read_jsonl(tmp_path / "missing.jsonl") == []


def test_merge_timelines_orders_by_ts_and_lane():
    geo = [{"ts": 2, "lane": "GeoLight"}, {"ts": 1, "lane": "GeoLight"}]
    tok = [{"ts": 1, "lane": "TokLight"}]
    merged = merge_timelines(geo, tok)
    assert [r["ts"] for r in merged] == [1, 1, 2]
    assert [r["lane"] for r in merged[:2]] == sorted(["TokLight", "GeoLight"])


def test_load_geolight_normalizes_lane(tmp_path):
    path = tmp_path / "geo.jsonl"
    path.write_text(
        '{"ts": 1, "scope": "g", "entry": "e", "prev": "p"}\n',
        encoding="utf-8",
    )
    rows = load_geolight(path)
    assert len(rows) == 1
    assert rows[0]["lane"] == "GeoLight"
    assert rows[0]["scope"] == "g"


def test_load_toklight_normalizes_lane(tmp_path):
    path = tmp_path / "tok.jsonl"
    path.write_text('{"ts": 3, "op": "tok"}\n', encoding="utf-8")
    rows = load_toklight(path)
    assert rows[0]["lane"] == "TokLight"
    assert rows[0]["op"] == "tok"
