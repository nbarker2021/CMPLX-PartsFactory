"""
cmplx.engine.cqe — Cartan-Quadratic Equivalence executor.

CQE is the pre-CMPLX identity tag of every system in this build. The
`engine.cqe` package is the orchestrator that ties them together:

  - `CQERunner.process_text(text)` — 8-stage unified-runtime pipeline
  - `CQERunner.solve_problem(problem, domain_type)` — 5-phase modular
    orchestrator (domain adapt → channels → MORSR → analyze →
    recommend)

The pipeline composes existing ports (snap / crystal / mdhg / morsr /
nsl / receipt / cache) plus the CQE-native primitives (mandelbrot,
toroidal, domain adapter, objective function, governance policy
layer, banding).

See INTERFACE.md + BRIDGE.md alongside this package.
"""
from __future__ import annotations

from .atom import (
    CQEAtom,
    digital_root_of_quad,
    parity_from_quad,
    quad_from_payload,
    quad_from_text,
)
from .banding import (
    THRESHOLD_BREAKTHROUGH,
    THRESHOLD_PEER_READY,
    ValidationBand,
    band_enum_for,
    band_for,
    compute_v_total,
)
from .cqe import CQEConfig, CQERunner, CQESystem, ProblemSolution, TextResult
from .domain import DomainAdapter, E8_DIM
from .governance import (
    CQEConstraint,
    CQEGovernance,
    CQEPolicy,
    ConstraintType,
    GovernanceLevel,
    Severity,
    ViolationRecord,
)
from .mandelbrot import (
    ESCAPE_RADIUS,
    MAX_ITER_DEFAULT,
    analyze_string,
    classify_behavior,
    hash_to_complex,
    is_bounded_path,
    is_in_set,
    mandelbrot_iterate,
)
from .modes import (
    PROFILES,
    ModeProfile,
    OperationMode,
    active_stages,
    profile_for,
)
from .objective import (
    DEFAULT_WEIGHTS,
    CQEObjectiveFunction,
    ObjectiveScores,
)
from .provider import CQEProvider
from .toroidal import (
    ROTATION_PATTERNS,
    generate_toroidal_shell,
    pattern_balance,
    pattern_distribution,
    sacred_frequency,
    torus_point,
)

__all__ = [
    # atom
    "CQEAtom", "digital_root_of_quad", "parity_from_quad",
    "quad_from_payload", "quad_from_text",
    # banding
    "THRESHOLD_BREAKTHROUGH", "THRESHOLD_PEER_READY",
    "ValidationBand", "band_enum_for", "band_for", "compute_v_total",
    # cqe orchestrator
    "CQEConfig", "CQERunner", "CQESystem", "ProblemSolution", "TextResult",
    # domain
    "DomainAdapter", "E8_DIM",
    # governance
    "CQEConstraint", "CQEGovernance", "CQEPolicy", "ConstraintType",
    "GovernanceLevel", "Severity", "ViolationRecord",
    # mandelbrot
    "ESCAPE_RADIUS", "MAX_ITER_DEFAULT", "analyze_string",
    "classify_behavior", "hash_to_complex", "is_bounded_path",
    "is_in_set", "mandelbrot_iterate",
    # modes
    "PROFILES", "ModeProfile", "OperationMode", "active_stages", "profile_for",
    # objective
    "DEFAULT_WEIGHTS", "CQEObjectiveFunction", "ObjectiveScores",
    # provider
    "CQEProvider",
    # toroidal
    "ROTATION_PATTERNS", "generate_toroidal_shell", "pattern_balance",
    "pattern_distribution", "sacred_frequency", "torus_point",
]
