"""
cmplx.symbolic.tarpit — the Morphonic Ribbon Ecology.

The symbolic-computation substrate. Programs over `}<>+[]01` reduce
to grain operations on a tape; grains bond into Dust → Triad; every
step emits an OutputWall or ErrorWall. Failed walls can be mirrored
to reopen blocked continua.

See INTERFACE.md + BRIDGE.md alongside this package.
"""
from __future__ import annotations

from .bond import BondEngine, Dust, Triad
from .ecology import (
    ComputationPhase,
    ComputationResult,
    TarpitEcology,
)
from .grain import (
    DimensionalExtent,
    Grain,
    GrainField,
    GrainType,
    Ribbon,
)
from .jot import CombinatorGrain, JotGrainEncoder, SKCombinator
from .aggregation import AggregatedRun, ExecutionSession, TarpitAggregator
from .canonical_forms import CANONICAL_ALIASES, CANONICAL_FORMS, normalize_form_name
from .glyphic import GLYPH_LEXICON, annotate_grain_tags, glyphs_to_etp_program
from .provider import TarPitSymbolicProvider
from ._functions import RelativityEnvelope, run_etp_with_ledger
from .walls import (
    ErrorClass,
    ErrorWall,
    MirroredState,
    MirrorOperator,
    OutputWall,
    WallEmitter,
    WallType,
)

__all__ = [
    "DimensionalExtent", "Grain", "GrainField", "GrainType", "Ribbon",
    "BondEngine", "Dust", "Triad",
    "ErrorClass", "ErrorWall", "MirroredState", "MirrorOperator",
    "OutputWall", "WallEmitter", "WallType",
    "CombinatorGrain", "JotGrainEncoder", "SKCombinator",
    "ComputationPhase", "ComputationResult", "TarpitEcology",
    "TarPitSymbolicProvider",
    "TarpitAggregator", "ExecutionSession", "AggregatedRun",
    "CANONICAL_FORMS", "CANONICAL_ALIASES", "normalize_form_name",
    "GLYPH_LEXICON", "glyphs_to_etp_program", "annotate_grain_tags",
    "RelativityEnvelope", "run_etp_with_ledger",
]
