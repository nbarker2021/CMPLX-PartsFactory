"""CMPLX Canonicalization Engine — deduplicate history into one file per tool."""

from .scanner import ArtifactScanner, ArtifactRecord
from .database import LineageDB
from .cluster import ClusterEngine
from .emitter import CanonicalEmitter

__all__ = [
    "ArtifactScanner",
    "ArtifactRecord", 
    "LineageDB",
    "ClusterEngine",
    "CanonicalEmitter",
]
