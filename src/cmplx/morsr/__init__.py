"""
cmplx.morsr — the recursive diagnostic-pulse engine.

MORSR (Middle Out Ripple SubRipple, renamed many times — the original
diagnostic core is the canonical anchor) takes a centroid, pulses to
anything that touches it (ripple), pulses again to anything that
touched that (subripple), evaluates what was hit and what interfered,
re-centers, and repeats until everything has been traced.

Three modes, all on the `diagnostic` port:

  - `pulse(seed)`     — the recursive ripple/subripple cycle
                         (NSL-gated, shell-bounded, ΔΦ-tracked)
  - `traverse(seed, strategy)` — 240-node complete-lattice walk
                                  (every E8 root scored exactly once)
  - `scan(coords, radius)`     — 240-direction sonar ping
                                  (which roots touch / which don't)

See INTERFACE.md + BRIDGE.md alongside this package.
"""
from __future__ import annotations

from .handshake import Handshake, HandshakeLog
from .operators import (
    OperatorFn,
    OperatorRegistry,
    op_midpoint,
    op_parity_mirror,
    op_rtheta,
    op_weyl_reflect,
)
from .overlay import DEFAULT_DIM, DEFAULT_MASK_LEN, Overlay
from .provider import MORSRProvider
from .pulse import (
    MORSREngine,
    MORSRPolicy,
    Region,
    StageMetrics,
    StopMetric,
)
from .shell import ShellMode, build_shell, in_shell
from .sonar import (
    E8_DIRECTIONS_DEFAULT,
    SHADOW_CATEGORIES,
    ShadowAction,
    SonarAtom,
    SonarScan,
    SonarScanResult,
    SonarShell,
)
from .traversal import (
    CompleteTraversal,
    NodeAnalysis,
    TraversalResult,
    TraversalStrategy,
)

from .causal import AttributionScore, CausalDAG, CausalNode, CausalReport
from .spectral import SpectralHealth, SpectralReport

__all__ = [
    # spectral health (Slot 24)
    "SpectralHealth", "SpectralReport",
    # causal DAG (Slot 25)
    "AttributionScore", "CausalDAG", "CausalNode", "CausalReport",
    # overlay
    "DEFAULT_DIM", "DEFAULT_MASK_LEN", "Overlay",
    # operators
    "OperatorFn", "OperatorRegistry",
    "op_rtheta", "op_weyl_reflect", "op_midpoint", "op_parity_mirror",
    # shell
    "ShellMode", "build_shell", "in_shell",
    # handshake
    "Handshake", "HandshakeLog",
    # pulse engine
    "MORSREngine", "MORSRPolicy", "Region", "StageMetrics", "StopMetric",
    # traversal
    "CompleteTraversal", "NodeAnalysis", "TraversalResult", "TraversalStrategy",
    # sonar
    "E8_DIRECTIONS_DEFAULT", "SHADOW_CATEGORIES",
    "ShadowAction", "SonarAtom", "SonarScan", "SonarScanResult", "SonarShell",
    # provider
    "MORSRProvider",
]
