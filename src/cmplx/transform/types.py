"""
Value types passed between the transformer's layers.

Kept as plain dataclasses so callers can serialise them, log them, or
attach them to receipts without depending on any framework-specific
tensor type.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from cmplx.morphon import Morphon


# ────────────────────────────────────────────────────────────────────────────
# Tokenizer output
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class TokenizedRibbon:
    """Output of MorphonicTokenizer.tokenize().

    `tensor` is the initial HiddenState tensor (seq_length, hidden_dim).
    `morphon` is the freshly forged + canonicalised Morphon.
    """

    raw_content: Any
    token_ids: np.ndarray
    content_hash: str
    tensor: np.ndarray
    morphon: Morphon
    geo_state: dict = field(default_factory=dict)
    canonical_info: dict = field(default_factory=dict)
    etp_program: Optional[str] = None


# ────────────────────────────────────────────────────────────────────────────
# Hidden state and per-layer trace
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class HiddenState:
    """The mutable state threaded through the transformer stack.

    `tensor` is a (seq_length, hidden_dim) numpy array. `morphon` is the
    evolving Morphon whose payload and coefficients reflect the work
    each layer has done.
    """

    tensor: np.ndarray
    morphon: Morphon
    brain_observations: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class AttentionOutput:
    """Summary of one attention block."""

    mode: str
    final_overlay_id: str = ""
    cumulative_delta_phi: float = 0.0
    handshake_count: int = 0
    accept_count: int = 0
    stage_count: int = 0
    status: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class FFNOutput:
    """Summary of one FFN block."""

    mode: str
    program_length: int = 0
    steps: int = 0
    halted: bool = False
    output_walls: int = 0
    error_walls: int = 0
    toolkit_passes: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


class ShellViolation(Exception):
    """Raised when shell-bound forward rejects ribbon_out."""

    def __init__(self, token: str, reason: str = "") -> None:
        self.token = token
        self.reason = reason
        super().__init__(reason or f"shell rejected: {token!r}")


@dataclass
class LayerTrace:
    """Per-layer audit record."""

    layer_idx: int
    attention: AttentionOutput
    ffn: FFNOutput
    nsl_pre_attn_accepted: bool = True
    nsl_post_ffn_accepted: bool = True
    delta_phi_attention: float = 0.0
    delta_phi_ffn: float = 0.0
    speedlight_hit: bool = False
    speedlight_cache_key: str = ""
    shell_violation: bool = False
    shell_reason: str = ""


@dataclass
class TransformerOutput:
    """Final return value from GeometricTransformer.forward()."""

    ribbon_out: Any
    final_morphon: Morphon
    cache_key: str
    receipts: list = field(default_factory=list)
    layer_traces: list[LayerTrace] = field(default_factory=list)
    speedlight_hit: bool = False
    summary: dict = field(default_factory=dict)


__all__ = [
    "TokenizedRibbon",
    "HiddenState",
    "AttentionOutput",
    "FFNOutput",
    "ShellViolation",
    "LayerTrace",
    "TransformerOutput",
]
