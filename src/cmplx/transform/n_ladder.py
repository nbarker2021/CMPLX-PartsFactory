"""
NLadderLayerConfig — eight typed transformer policies (N=1..8 doctrine).

N=1 is tokenizer/context; stack layers map to N=2..8 interaction floors.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .config import AttentionConfig, FFNConfig, LayerConfig


@dataclass(frozen=True)
class NLadderLayerConfig:
    n_level: int
    symmetry_tag: str
    attention_mode: str
    ffn_max_steps: int
    gate_strictness: str  # govern | strict | observe

    def to_layer_config(self) -> LayerConfig:
        attn = AttentionConfig(mode=self.attention_mode)
        if self.gate_strictness == "strict":
            attn.gate_mode = "govern"
            attn.stop_threshold = 1e-5
        elif self.gate_strictness == "observe":
            attn.gate_mode = "signal"
        ffn = FFNConfig(max_steps=self.ffn_max_steps)
        nsl_mode = "govern"
        if self.gate_strictness == "observe":
            nsl_mode = "signal"
        return LayerConfig(
            attention=attn,
            ffn=ffn,
            nsl_mode=nsl_mode,
        )


# Doctrine table: N → policy (layers 0..7 → N=2..8; N=1 in tokenizer)
_DEFAULT_LADDER: tuple[NLadderLayerConfig, ...] = (
    NLadderLayerConfig(2, "G2_horizontal", "pulse", 120, "govern"),
    NLadderLayerConfig(3, "SU3_triad", "traverse", 140, "govern"),
    NLadderLayerConfig(4, "F4_quad", "pulse", 160, "govern"),
    NLadderLayerConfig(5, "T5_octad", "traverse", 180, "govern"),
    NLadderLayerConfig(6, "Spin6_E6", "scan", 200, "govern"),
    NLadderLayerConfig(7, "E7_tighten", "pulse", 220, "strict"),
    NLadderLayerConfig(8, "E8_closure", "scan", 240, "strict"),
    NLadderLayerConfig(8, "E8_observer", "traverse", 200, "observe"),
)


def default_n_ladder_stack() -> tuple[NLadderLayerConfig, ...]:
    return _DEFAULT_LADDER


def layer_configs_from_n_ladder(
    configs: Sequence[NLadderLayerConfig] | None = None,
) -> list[LayerConfig]:
    stack = list(configs or default_n_ladder_stack())
    return [c.to_layer_config() for c in stack]


__all__ = [
    "NLadderLayerConfig",
    "default_n_ladder_stack",
    "layer_configs_from_n_ladder",
]
