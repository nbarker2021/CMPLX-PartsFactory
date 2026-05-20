#!/usr/bin/env python3
"""
CMPLX-PartsFactory — Smoke Tests

Basic tests to verify discovery, composition, catalog, and personal node
functionality.
"""

import sys
import os
import tempfile
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from composition import CompositionHarness, CompositionTemplate, FAMILY_CAPABILITIES
from discovery import PostgresDiscovery, SQLiteDiscovery, FileSystemDiscovery, DiscoveredTool
from catalog.catalog_db import CatalogDB
from personal_node.node import PersonalNode
from tools.stubs import TOOL_STUBS, register_stubs


def test_composition_harness():
    print("Testing CompositionHarness...")
    harness = CompositionHarness(catalog_path=tempfile.mkdtemp())
    register_stubs(harness)

    assert len(harness._tools) >= 8, f"Expected >=8 stubs, got {len(harness._tools)}"

    result = harness.test_pair("e8_embed", "bond_chemistry", test_input="test")
    assert result.success, f"Composition failed: {result.error}"
    print(f"  ✓ Composition test passed ({result.execution_time_ms:.1f}ms)")

    templates = CompositionTemplate.list_templates()
    assert len(templates) >= 5, f"Expected >=5 templates, got {len(templates)}"
    print(f"  ✓ Templates: {templates}")


def test_catalog_db():
    print("Testing CatalogDB...")
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name

    db = CatalogDB(db_path)
    db.connect()

    db.insert_tool({
        "tool_id": "test_tool",
        "name": "Test Tool",
        "source": "test",
        "source_type": "test",
        "families": ["brain"],
        "capabilities": ["test"],
    })

    tool = db.get_tool("test_tool")
    assert tool is not None, "Tool not found after insert"
    assert tool["name"] == "Test Tool"
    print(f"  ✓ Catalog insert/retrieve passed")

    manifest = db.get_manifest()
    assert manifest["tool_count"] == 1
    print(f"  ✓ Catalog manifest: {manifest}")

    db.close()
    os.unlink(db_path)


def test_personal_node():
    print("Testing PersonalNode...")
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name

    node = PersonalNode(db_path)
    node.connect()

    node.set_preference("test_key", {"value": 42})
    pref = node.get_preference("test_key")
    assert pref == {"value": 42}, f"Preference mismatch: {pref}"
    print(f"  ✓ Preference storage passed")

    node.start_session("sess_001", channel_id="ch_001")
    node.touch_session("sess_001", context_summary="test context")
    print(f"  ✓ Session tracking passed")

    node.close()
    os.unlink(db_path)


def test_discovery_structures():
    print("Testing discovery data structures...")
    tool = DiscoveredTool(
        tool_id="dt_001",
        name="Discovery Test",
        source="test",
        source_type="test",
    )
    d = tool.to_dict()
    assert d["tool_id"] == "dt_001"
    print(f"  ✓ DiscoveredTool dataclass passed")


def main():
    print("=== CMPLX-PartsFactory Smoke Tests ===\n")
    try:
        test_composition_harness()
        test_catalog_db()
        test_personal_node()
        test_discovery_structures()
        print("\n✅ All tests passed.")
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
