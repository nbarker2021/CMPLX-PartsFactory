"""Smoke tests for Manus + files(1) integration."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_manifest_v3_has_30_tools():
    from cmplx.tools import load_manifest_v3

    m = load_manifest_v3()
    assert len(m.get("tools", [])) == 30


def test_registry_adapts_protein_fold():
    from cmplx.tools.manus.registry import CMPLXToolRegistry

    reg = CMPLXToolRegistry()
    rails = reg.adapt("T01_protein_fold_morphon", {"dihedral_angles": [1] * 8})
    assert set(rails.keys()) == {"alpha", "beta", "gamma"}
    assert rails["alpha"].shape == (8,)


def test_primitives_e8_roots():
    from cmplx.primitives import e8_roots

    roots = e8_roots()
    assert roots.shape == (240, 8)


def test_instruments_dir_populated():
    inst = Path(__file__).resolve().parents[2] / "src/cmplx/tools/manus/instruments"
    py_files = list(inst.glob("*.py"))
    assert len(py_files) >= 25
