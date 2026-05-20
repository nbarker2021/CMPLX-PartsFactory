"""Viewer24 slot-09 package smoke tests."""
from __future__ import annotations

from cmplx.geometry.viewer24 import DihedralCA, NIEMEIER_SPECS, ResidueAnalyzer


def test_dihedral_ca_step():
    ca = DihedralCA(tiles_x=2, tiles_y=2, n=8, seed=1)
    ca.seed_from_specs(["E8"] * 4)
    ca.step(kappa=0.08, dual=True)
    assert ca.step_id == 1
    tile = ca.tile_pixels_em(0, alpha=128)
    assert tile["w"] == 8 and len(tile["rgba"]) == 8 * 8 * 4


def test_residue_analyzer_baseline():
    ca = DihedralCA(tiles_x=2, tiles_y=2, n=4, seed=2)
    ca.seed_from_specs(NIEMEIER_SPECS[:4])
    inv = ResidueAnalyzer(ca)
    inv.capture_baseline()
    assert inv.baseline_hex is not None
    assert len(inv.baseline_hex) == ca.W * ca.H
