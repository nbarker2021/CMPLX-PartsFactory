"""
cmplx.transform — Slot 48: the Morphonic Transformer.

Substrate-first geometric transformer that fills the classic
`tokenize → embed → L × block → head → output` shape with existing
CMPLX ports (MORSR for attention, TarPit for FFN, NSL for gates,
SpeedLight for residuals).

See INTERFACE.md and BRIDGE.md alongside this package for the
contract, and `config.py` for the full settings surface.
"""
from __future__ import annotations

from .config import (
    AttentionConfig,
    FFNConfig,
    LayerConfig,
    TokenizerConfig,
    TransformerConfig,
)
from .types import (
    AttentionOutput,
    FFNOutput,
    HiddenState,
    LayerTrace,
    TokenizedRibbon,
    TransformerOutput,
)
from .tokenizer import MorphonicTokenizer
from .attention import MorphonicAttention
from .ffn import MorphonicFFN
from .layer import GeometricTransformerLayer
from .transformer import GeometricTransformer

from .crystal_pack import CrystalPackager, LoadedCrystal
from .meaning_store import AddressMeaningStore, MeaningRow
from .rule_lib import RuleLibraryLoader, RuleLibraryBundle
from .shell import AdmitResult, MorphonShell
from .shell_config import ShellConfig
from .ingest import CorpusIngester, IngestStats
from .index_supervisor import IndexSupervisor
from .metrics import MorphSignature, TokenMetrics, compute_morph_signature, probe_case_pair
from .octad import OctadSheet

__all__ = [
    # config
    "AttentionConfig",
    "FFNConfig",
    "LayerConfig",
    "TokenizerConfig",
    "TransformerConfig",
    # types
    "AttentionOutput",
    "FFNOutput",
    "HiddenState",
    "LayerTrace",
    "TokenizedRibbon",
    "TransformerOutput",
    # components
    "MorphonicTokenizer",
    "MorphonicAttention",
    "MorphonicFFN",
    "GeometricTransformerLayer",
    "GeometricTransformer",
    # morphonic substrate MVP
    "ShellConfig",
    "AdmitResult",
    "MorphonShell",
    "AddressMeaningStore",
    "MeaningRow",
    "CorpusIngester",
    "IngestStats",
    "IndexSupervisor",
    "MorphSignature",
    "TokenMetrics",
    "compute_morph_signature",
    "probe_case_pair",
    "OctadSheet",
    "RuleLibraryLoader",
    "RuleLibraryBundle",
    "CrystalPackager",
    "LoadedCrystal",
]
