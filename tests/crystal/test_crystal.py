"""
Tests for cmplx.crystal — fabric + data crystals + tool crystals +
registry.
"""
from __future__ import annotations

import pytest

from cmplx.crystal import (
    ATOM_LEVELS,
    BlockType,
    CompositionRule,
    Crystal,
    CrystalRegistry,
    DEFAULT_FABRIC,
    E8Node,
    MEANING_LEVELS,
    PLANET_NAMES,
    ToolAtom,
    ToolCrystal,
    assign_address,
    digital_root,
    e8_seed_from_name,
    golay_encode,
    project_to_leech,
)
from cmplx.morphon import MorphonController


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# Fabric
# ---------------------------------------------------------------------------

def test_default_fabric_has_10_levels():
    assert len(DEFAULT_FABRIC) == 10
    assert DEFAULT_FABRIC[0].name == "universe"
    assert DEFAULT_FABRIC[-1].name == "atoms"


def test_atom_levels_has_6_levels():
    assert len(ATOM_LEVELS) == 6
    names = [l.name for l in ATOM_LEVELS]
    assert names == ["planet", "city", "building", "floor", "room", "atom"]


def test_meaning_levels_and_planet_names():
    assert len(MEANING_LEVELS) == 5
    assert MEANING_LEVELS[0] == "surface"
    assert MEANING_LEVELS[-1] == "transcendent"
    assert len(PLANET_NAMES) == 9
    assert PLANET_NAMES[0] == "alpha"


# ---------------------------------------------------------------------------
# digital_root + assign_address
# ---------------------------------------------------------------------------

def test_digital_root_in_range():
    for vec in [[0.1], [1.0, 2.0, 3.0], [0.0, 0.0, 0.0], [99.9]]:
        dr = digital_root(vec)
        assert 1 <= dr <= 9


def test_digital_root_zero_maps_to_nine():
    assert digital_root([0.0, 0.0, 0.0]) == 9


def test_assign_address_yields_all_levels():
    addr = assign_address(content="hello", e8_coords=[0.1] * 8,
                          entry_type="atom", labels=["test"])
    for lv in ATOM_LEVELS:
        assert lv.name in addr
    assert "full" in addr
    assert "digital_root" in addr
    assert addr["full"].count(".") == 5  # 6 levels → 5 dots


def test_assign_address_planet_picks_from_planet_names():
    addr = assign_address(content="x", e8_coords=[1.0] * 8, entry_type="atom")
    assert addr["planet"] in PLANET_NAMES


# ---------------------------------------------------------------------------
# Golay + Leech projection
# ---------------------------------------------------------------------------

def test_golay_encode_yields_24_bits():
    encoded = golay_encode(0b101010101010)
    assert 0 <= encoded < (1 << 24)


def test_golay_encode_rejects_too_large():
    with pytest.raises(ValueError):
        golay_encode(1 << 12)


def test_project_to_leech_yields_24_floats():
    leech = project_to_leech([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    assert len(leech) == 24


def test_e8_seed_from_name_deterministic():
    a = e8_seed_from_name("alpha")
    b = e8_seed_from_name("alpha")
    c = e8_seed_from_name("beta")
    assert a == b
    assert a != c
    assert len(a) == 8


# ---------------------------------------------------------------------------
# Crystal + E8Node dataclasses
# ---------------------------------------------------------------------------

def test_crystal_autogenerates_id_and_receipt():
    c = Crystal(name="test")
    assert c.crystal_id
    assert c.receipt_chain
    assert c.snap_address.startswith("crystal://")
    assert c.created_at > 0


def test_crystal_extend_receipt_changes_chain():
    c = Crystal(name="test")
    r1 = c.receipt_chain
    r2 = c.extend_receipt("node:1")
    assert r1 != r2
    assert c.receipt_chain == r2


def test_e8node_autogenerates_id_and_mass_from_labels():
    n = E8Node(crystal_id="abc", content="x", snap_labels=["a", "b", "c"])
    assert n.node_id.startswith("node-")
    assert n.mass > 0  # 3 labels × COUPLING


# ---------------------------------------------------------------------------
# ToolAtom + ToolCrystal
# ---------------------------------------------------------------------------

def test_tool_crystal_autogenerates_blocks():
    tc = ToolCrystal(name="echo", description="Returns its input.")
    assert tc.input_atom is not None
    assert tc.input_atom.block_type == BlockType.INPUT
    assert tc.boundary_atom is not None
    assert tc.boundary_atom.laws == ["delta_phi_le_0", "receipt_required"]
    assert tc.output_atom is not None
    assert tc.transform_atom is None  # not configured yet
    assert tc.resonance  # auto-computed


def test_tool_crystal_configure_sets_transform():
    tc = ToolCrystal(name="add", description="Adds two ints.")
    handler = lambda x, y: x + y
    tc.configure(handler=handler, param_schema={"x": "int", "y": "int"},
                 output_desc="int", snap_labels=["arithmetic"])
    assert tc.transform_atom is not None
    assert tc.transform_atom.block_type == BlockType.TRANSFORM
    assert tc.transform_atom.handler is handler
    assert tc.transform_atom.snap_labels == ["arithmetic"]
    assert tc.input_atom.param_schema == {"x": "int", "y": "int"}


def test_tool_crystal_add_bond_returns_self():
    tc1 = ToolCrystal(name="a")
    tc2 = tc1.add_bond("b", CompositionRule.SEQUENTIAL)
    assert tc1 is tc2  # fluent
    assert tc1.bonds == [("b", CompositionRule.SEQUENTIAL)]


def test_tool_crystal_resonance_is_deterministic():
    tc1 = ToolCrystal(name="tool", description="same", category="x")
    tc2 = ToolCrystal(name="tool", description="same", category="x")
    assert tc1.resonance == tc2.resonance


def test_tool_crystal_to_mcp_schema():
    tc = ToolCrystal(name="echo", description="d")
    tc.configure(handler=lambda x: x, param_schema={"in": "str"})
    schema = tc.to_mcp_schema()
    assert schema["name"] == "echo"
    assert schema["inputSchema"] == {"in": "str"}


# ---------------------------------------------------------------------------
# CrystalRegistry
# ---------------------------------------------------------------------------

def test_registry_create_and_get():
    reg = CrystalRegistry()
    c = reg.create(name="knowledge_base")
    assert reg.get(c.crystal_id) is c
    assert reg.list()[0] is c


def test_registry_add_node_binds_everything():
    reg = CrystalRegistry()
    c = reg.create(name="kb")
    node = reg.add_node(c.crystal_id, content="fact A",
                        labels=["important", "verified"])
    # Bind-everything assertion: the node has all three identity fields
    assert node.snap_labels == ["important", "verified"]
    assert node.mdhg_address  # not empty
    assert "full" in node.mdhg_address
    assert len(node.e8_coords) == 8


def test_registry_add_node_extends_receipt_chain():
    reg = CrystalRegistry()
    c = reg.create(name="kb")
    r_before = c.receipt_chain
    reg.add_node(c.crystal_id, content="fact")
    r_after = c.receipt_chain
    assert r_before != r_after
    assert c.node_count == 1


def test_registry_add_node_unknown_crystal_raises():
    reg = CrystalRegistry()
    with pytest.raises(LookupError):
        reg.add_node("nope", content="x")


def test_registry_commit_and_activate_change_state():
    reg = CrystalRegistry()
    c = reg.create(name="kb")
    assert c.state == "growing"
    reg.commit(c.crystal_id)
    assert c.state == "committed"
    reg.activate(c.crystal_id)
    assert c.state == "active"


def test_registry_list_filters_by_state():
    reg = CrystalRegistry()
    a = reg.create(name="a")
    b = reg.create(name="b")
    reg.commit(b.crystal_id)
    growing = reg.list(state="growing")
    committed = reg.list(state="committed")
    assert a in growing and b not in growing
    assert b in committed and a not in committed


def test_registry_register_tool_and_get():
    reg = CrystalRegistry()
    tc = ToolCrystal(name="echo")
    reg.register_tool(tc)
    assert reg.get_tool("echo") is tc
    assert reg.list_tools() == [tc]


def test_registry_register_tool_rejects_duplicate():
    reg = CrystalRegistry()
    reg.register_tool(ToolCrystal(name="t"))
    with pytest.raises(RuntimeError, match="already registered"):
        reg.register_tool(ToolCrystal(name="t"))


def test_registry_vibrate_returns_resonant_nodes():
    reg = CrystalRegistry()
    c = reg.create(name="kb")
    n1 = reg.add_node(c.crystal_id, content="a", e8_coords=[0.5] + [0.0] * 7)
    n2 = reg.add_node(c.crystal_id, content="b", e8_coords=[0.9] + [0.0] * 7)
    hits = reg.vibrate(c.crystal_id, frequency=0.5, tolerance=0.1)
    assert n1 in hits
    assert n2 not in hits


def test_registry_health_reports():
    reg = CrystalRegistry()
    reg.create(name="a")
    reg.create(name="b")
    reg.register_tool(ToolCrystal(name="t"))
    h = reg.health
    assert h["crystals"] == 2
    assert h["tools"] == 1


# ---------------------------------------------------------------------------
# MorphonController bridge integration
# ---------------------------------------------------------------------------

def test_crystal_registers_on_crystal_port():
    mc = MorphonController.get()
    reg = CrystalRegistry()
    mc.register("crystal", reg)
    assert mc.get_provider("crystal") is reg
