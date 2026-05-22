"""Lattice Forge public API.

Lattice Forge is an installable lattice/morphism admissibility engine. It ships
an immutable seed ledger and writes project-local interaction state to an
overlay database.
"""

from .forge import Forge
from .ledger import Ledger, build_seed_database
from .morphonics import morphonics_model_v0_2, verify_morphonics_model
from .overlay import OverlayStore
from .rule30 import (
    rule30_color_chirality_cipher,
    rule30_dihedral_block_hypervisor,
    rule30_discrete_lagrangian,
    rule30_hypervisor_extension_tape,
    rule30_lagrangian_depth_trace,
    rule30_mandelbrot_boundary_scalar,
    rule30_morphon_hardened,
    rule30_moving_frame,
    rule30_nth_bit_expression,
    rule30_physics_method_stack,
    rule30_proof_obligation_ledger,
    rule30_readout_ribbon_machine,
    rule30_reduced_alphabet_catalog,
    rule30_sheet_operator,
    rule30_symmetry_environment,
    rule30_whole_integer_n_scalar_coverage,
    rule30_vignette_algebra,
    verify_rule30_color_chirality_cipher,
    verify_rule30_dihedral_block_hypervisor,
    verify_rule30_discrete_lagrangian,
    verify_rule30_hypervisor_extension_tape,
    verify_rule30_lagrangian_depth_trace,
    verify_rule30_mandelbrot_boundary_scalar,
    verify_rule30_morphon,
    verify_rule30_moving_frame,
    verify_rule30_nth_bit_expression,
    verify_rule30_physics_method_stack,
    verify_rule30_proof_obligation_ledger,
    verify_rule30_readout_ribbon_machine,
    verify_rule30_reduced_alphabet_catalog,
    verify_rule30_sheet_operator,
    verify_rule30_symmetry_environment,
    verify_rule30_whole_integer_n_scalar_coverage,
    verify_rule30_vignette_algebra,
)
from .seed import SeedStore
from .terminal_tree import build_terminal_composition_tree

__all__ = [
    "Forge",
    "Ledger",
    "OverlayStore",
    "SeedStore",
    "build_seed_database",
    "build_terminal_composition_tree",
    "morphonics_model_v0_2",
    "verify_morphonics_model",
    "rule30_morphon_hardened",
    "verify_rule30_morphon",
    "rule30_vignette_algebra",
    "verify_rule30_vignette_algebra",
    "rule30_moving_frame",
    "verify_rule30_moving_frame",
    "rule30_color_chirality_cipher",
    "verify_rule30_color_chirality_cipher",
    "rule30_discrete_lagrangian",
    "verify_rule30_discrete_lagrangian",
    "rule30_lagrangian_depth_trace",
    "verify_rule30_lagrangian_depth_trace",
    "rule30_mandelbrot_boundary_scalar",
    "verify_rule30_mandelbrot_boundary_scalar",
    "rule30_reduced_alphabet_catalog",
    "verify_rule30_reduced_alphabet_catalog",
    "rule30_symmetry_environment",
    "verify_rule30_symmetry_environment",
    "rule30_physics_method_stack",
    "verify_rule30_physics_method_stack",
    "rule30_whole_integer_n_scalar_coverage",
    "verify_rule30_whole_integer_n_scalar_coverage",
    "rule30_readout_ribbon_machine",
    "verify_rule30_readout_ribbon_machine",
    "rule30_dihedral_block_hypervisor",
    "verify_rule30_dihedral_block_hypervisor",
    "rule30_hypervisor_extension_tape",
    "verify_rule30_hypervisor_extension_tape",
    "rule30_sheet_operator",
    "verify_rule30_sheet_operator",
    "rule30_nth_bit_expression",
    "verify_rule30_nth_bit_expression",
    "rule30_proof_obligation_ledger",
    "verify_rule30_proof_obligation_ledger",
]
__version__ = "0.1.0"
