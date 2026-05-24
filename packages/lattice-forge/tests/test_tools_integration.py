"""Tool hot-path wiring on Regime A block extractor."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from lattice_forge import Forge
from lattice_forge.rule30_block_extractor import Rule30BlockExtractor
from lattice_forge.tools.speedlight import SpeedlightTool


def test_speedlight_get_put_during_extractor_build(tmp_path):
    calls: list[str] = []
    original_invoke = SpeedlightTool.invoke

    def spy_invoke(self, **kwargs):
        calls.append(str(kwargs.get("op")))
        return original_invoke(self, **kwargs)

    with patch.object(SpeedlightTool, "invoke", spy_invoke):
        Rule30BlockExtractor(max_depth=128, base_page=64, forge=Forge.open(tmp_path / "ov"))

    assert "get" in calls
    assert "put" in calls


def test_forge_record_solver_event_on_query(tmp_path):
    forge = Forge.open(tmp_path / "ov2")
    forge.record_solver_event(operation="setup", landauer_cost=0.0)
    extractor = Rule30BlockExtractor(max_depth=128, base_page=64, forge=forge)
    extractor.nth_bit(10)
    kinds = [event["event_kind"] for event in forge.latest_events(10)]
    assert kinds.count("solver_event") >= 2
