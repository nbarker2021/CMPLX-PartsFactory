"""Tests for transform.octad."""
from __future__ import annotations

from cmplx.transform.octad import OctadSheet, octad_phase_at


def test_octad_from_json_seven_trees():
    sheet = OctadSheet.from_json()
    assert len(sheet.tree_ids) == 7
    assert sheet.palindrome_id


def test_octad_slot_id():
    sheet = OctadSheet.from_json()
    assert sheet.slot_id(0) == sheet.palindrome_id
    assert sheet.slot_id(1) == sheet.tree_ids[0]


def test_octad_phase_at():
    assert octad_phase_at(8) == 0
    assert octad_phase_at(3) == 3
