"""
OperationMode — controls which CQE subsystems are active per call.

Adapted from `cqe_modules/cqe_system.py:CQEOperationMode`. Each mode
flips a different set of pipeline stages on/off, so consumers can
trade depth for speed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OperationMode(str, Enum):
    BASIC = "BASIC"
    ENHANCED = "ENHANCED"
    SACRED_GEOMETRY = "SACRED_GEOMETRY"
    MANDELBROT_FRACTAL = "MANDELBROT_FRACTAL"
    ULTIMATE_UNIFIED = "ULTIMATE_UNIFIED"


@dataclass(frozen=True)
class ModeProfile:
    """Which stages run for a given OperationMode."""
    name: str
    e8_embed: bool = True
    fractal_mandelbrot: bool = False
    toroidal_shell: bool = False
    phi_computation: bool = True
    semantics: bool = False
    governance: bool = True
    validation: bool = True
    morsr_exploration: bool = False
    receipt_chain: bool = True
    cqe_atom_population: bool = True


# Canonical profiles, one per OperationMode.
PROFILES: dict[OperationMode, ModeProfile] = {
    OperationMode.BASIC: ModeProfile(
        name="BASIC",
        e8_embed=True, phi_computation=True,
        governance=True, validation=True,
        # All others off
        fractal_mandelbrot=False, toroidal_shell=False, semantics=False,
        morsr_exploration=False, cqe_atom_population=False,
    ),
    OperationMode.ENHANCED: ModeProfile(
        name="ENHANCED",
        e8_embed=True, phi_computation=True, semantics=True,
        governance=True, validation=True,
        cqe_atom_population=True,
        fractal_mandelbrot=False, toroidal_shell=False,
        morsr_exploration=False,
    ),
    OperationMode.SACRED_GEOMETRY: ModeProfile(
        name="SACRED_GEOMETRY",
        e8_embed=True, phi_computation=True, semantics=True,
        toroidal_shell=True,
        governance=True, validation=True,
        cqe_atom_population=True,
        fractal_mandelbrot=False, morsr_exploration=False,
    ),
    OperationMode.MANDELBROT_FRACTAL: ModeProfile(
        name="MANDELBROT_FRACTAL",
        e8_embed=True, phi_computation=True, semantics=True,
        fractal_mandelbrot=True,
        governance=True, validation=True,
        cqe_atom_population=True,
        toroidal_shell=False, morsr_exploration=False,
    ),
    OperationMode.ULTIMATE_UNIFIED: ModeProfile(
        name="ULTIMATE_UNIFIED",
        e8_embed=True, phi_computation=True, semantics=True,
        fractal_mandelbrot=True, toroidal_shell=True,
        morsr_exploration=True,
        governance=True, validation=True,
        cqe_atom_population=True, receipt_chain=True,
    ),
}


def profile_for(mode: OperationMode) -> ModeProfile:
    return PROFILES[mode]


def active_stages(mode: OperationMode) -> list[str]:
    """Return the list of stage names that are enabled for `mode`."""
    p = profile_for(mode)
    active: list[str] = []
    for field in (
        "e8_embed", "fractal_mandelbrot", "toroidal_shell",
        "phi_computation", "semantics", "governance", "validation",
        "morsr_exploration", "receipt_chain", "cqe_atom_population",
    ):
        if getattr(p, field, False):
            active.append(field)
    return active
