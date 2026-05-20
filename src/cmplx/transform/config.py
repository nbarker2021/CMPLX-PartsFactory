"""
Configuration dataclasses for the Morphonic Transformer (Slot 48).

Every knob the substrate-first transformer exposes lives in one of the
four nested configs below. The defaults are the MVP recipe described
in the operational plan: 4 layers, MORSR pulse attention, TarPit FFN,
NSL-gated residuals, SpeedLight idempotency.

Settings are deliberately data-only so callers can serialise them,
diff them across runs, and swap nested configs per layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Sequence


# ────────────────────────────────────────────────────────────────────────────
# Tokenizer
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class TokenizerConfig:
    """Settings for the MorphonicTokenizer.

    The tokenizer composes three layers in order:
      1. DeterministicTokenizer (eversion network)
      2. GeoTokenizer (SpeedLight service) — optional, on by default
      3. Morphon.forge + Atlas / NLAECNF canonicalisation
    """

    vocab_size: int = 8192
    seq_length: int = 128
    use_geo: bool = True
    similarity_threshold: float = 0.95
    ribbon_mode: str = "raw"  # one of: raw | etp | mixed
    encode_etp: bool = False  # also produce an ETP program string


# ────────────────────────────────────────────────────────────────────────────
# Attention (MORSR-backed)
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class AttentionConfig:
    """Settings for the MorphonicAttention.

    Mirrors MORSRPolicy plus a top-level mode flag selecting between
    the three MORSR ports: pulse, traverse, scan.
    """

    mode: str = "pulse"  # one of: pulse | traverse | scan

    # MORSRPolicy fields
    eps_phi: float = 1e-6
    plateau_cap: int = 0
    shell_mode: str = "radial"  # ShellMode value
    shell_base: float = 0.25
    shell_factors: Sequence[int] = (1, 2, 3, 5, 8)
    stop_metric: str = "strict_gain"  # StopMetric value
    stop_threshold: float = 1e-4
    ema_alpha: float = 0.5
    max_stages: Optional[int] = None
    gate_mode: str = "govern"  # GateMode value
    stage_budget: float = 0.0

    # Traverse / scan
    traverse_strategy: str = "systematic"
    scan_radius: float = 5.0


# ────────────────────────────────────────────────────────────────────────────
# FFN (TarPit-backed)
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class FFNConfig:
    """Settings for the MorphonicFFN.

    The FFN slot runs the TarPit symbolic provider (`derive` or
    `run_program`) and may chain additional toolkit passes (SNAP,
    Crystal, MDHG place) when their ports are available.
    """

    dimension: int = 8
    max_steps: int = 200
    program_length: int = 32
    derive_mode: str = "derive"  # one of: derive | run_program
    toolkit_passes: list[str] = field(default_factory=list)


# ────────────────────────────────────────────────────────────────────────────
# Layer
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class LayerConfig:
    """Settings for one GeometricTransformerLayer."""

    attention: AttentionConfig = field(default_factory=AttentionConfig)
    ffn: FFNConfig = field(default_factory=FFNConfig)
    nsl_mode: str = "govern"  # gate mode applied to layer-wide ΔΦ
    nsl_budget: float = 0.0
    use_speedlight_residual: bool = True
    use_hf_fallback: bool = False  # optional on-demand HF lane after NSL reject


# ────────────────────────────────────────────────────────────────────────────
# Top-level transformer
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class TransformerConfig:
    """Settings for the whole GeometricTransformer stack."""

    num_layers: int = 4
    n_domains: int = 3  # default 24-D = 3 × 8-D rails
    hidden_dim: Optional[int] = None  # defaults to 8 * n_domains if None
    seq_length: Optional[int] = None  # defaults to tokenizer.seq_length

    tokenizer: TokenizerConfig = field(default_factory=TokenizerConfig)
    layers: Optional[list[LayerConfig]] = None  # filled in __post_init__

    output_mode: str = "json"  # one of: json | etp | raw
    mmdb_path: str = ":memory:"
    register_ports_on_init: bool = True
    full_manifold_pipeline: bool = False  # phase 2: delegate to EnhancedManifoldV3
    use_n_ladder: bool = False  # eight typed policies (N=2..8)
    shell_bind: bool = False  # post-head shell.admit on ribbon_out

    # TMN1-style hooks
    hook_pre_layer: Optional[Callable[[Any, int, "LayerConfig"], None]] = None
    hook_post_layer: Optional[Callable[[Any, int, "LayerConfig"], None]] = None

    def __post_init__(self) -> None:
        if self.num_layers < 1:
            raise ValueError(f"num_layers must be >= 1 (got {self.num_layers})")
        if self.n_domains < 1:
            raise ValueError(f"n_domains must be >= 1 (got {self.n_domains})")
        if self.hidden_dim is None:
            self.hidden_dim = 8 * self.n_domains
        if self.seq_length is None:
            self.seq_length = self.tokenizer.seq_length
        if self.use_n_ladder:
            from .n_ladder import layer_configs_from_n_ladder

            self.layers = layer_configs_from_n_ladder()
            self.num_layers = len(self.layers)
        elif self.layers is None:
            self.layers = [LayerConfig() for _ in range(self.num_layers)]
        if len(self.layers) != self.num_layers:
            raise ValueError(
                f"layers list length ({len(self.layers)}) "
                f"!= num_layers ({self.num_layers})"
            )


def ProductionTransformerConfig(**overrides: Any) -> TransformerConfig:
    """Production inference preset: N-ladder (N=2..8), shell bind, ports on init."""
    base: dict[str, Any] = {
        "use_n_ladder": True,
        "shell_bind": True,
        "register_ports_on_init": True,
    }
    base.update(overrides)
    return TransformerConfig(**base)


__all__ = [
    "TokenizerConfig",
    "AttentionConfig",
    "FFNConfig",
    "LayerConfig",
    "TransformerConfig",
    "ProductionTransformerConfig",
]
