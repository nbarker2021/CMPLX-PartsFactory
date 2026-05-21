"""
cmplx.snap — semantic decomposition + polarity-aware evaluation.

See INTERFACE.md + BRIDGE.md alongside this package.
"""
from __future__ import annotations

from .gate369 import (
    Body,
    EnneadPackage,
    Gate369Engine,
    HexadInvariant,
    Predicate,
    SNAPRecord,
)
from .label import LabelRule, SNAPLabel, SNAPRole
from .labeler import SNAPLabeler
from .ledger import SNAPLedger, SNAPTransaction
from .lenses import BaseLens, LegalityLens, LensBank, NoveltyLens, SymmetryLens
from .morphon_context import enrich_label_from_morphon, label_context_from_morphon
from .provider import SNAPEngine

__all__ = [
    # labels
    "LabelRule",
    "SNAPLabel",
    "SNAPRole",
    "SNAPLabeler",
    # lenses
    "BaseLens",
    "LegalityLens",
    "NoveltyLens",
    "SymmetryLens",
    "LensBank",
    # gate 369
    "Body",
    "Predicate",
    "HexadInvariant",
    "EnneadPackage",
    "SNAPRecord",
    "Gate369Engine",
    # ledger
    "SNAPLedger",
    "SNAPTransaction",
    # provider
    "SNAPEngine",
    "label_context_from_morphon",
    "enrich_label_from_morphon",
]
