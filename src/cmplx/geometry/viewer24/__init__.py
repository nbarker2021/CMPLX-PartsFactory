"""Viewer24 — 24-screen dihedral CA + inverse residue viewer (slot-09)."""
from __future__ import annotations

from .dihedral_ca import DihedralCA, wavelength_to_rgb, rgb_to_hex
from .inverse_residue import ResidueAnalyzer
from .niemeier_specs import NIEMEIER_SPECS

__all__ = [
    "DihedralCA",
    "ResidueAnalyzer",
    "NIEMEIER_SPECS",
    "wavelength_to_rgb",
    "rgb_to_hex",
]
