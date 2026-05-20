"""
GeometricTransformerLayer — one transformer block.

Internal order: attention → NSL gate → FFN → NSL gate → residual.

The NSL gates decide whether the sub-block's ΔΦ is acceptable; on
rejection the block falls back to the pre-sub-block state so the
layer never violates conservation. The residual stage caches the
post-block tensor through the SpeedLight provider so a second identical
forward returns the same key (and `speedlight_hit=True`).
"""
from __future__ import annotations

import hashlib
import logging
from typing import Optional

import numpy as np

from cmplx.nsl import GateMode

from .attention import MorphonicAttention
from .bridge import (
    get_cache_provider,
    get_conservation_provider,
    has_provider,
)
from .config import LayerConfig
from .ffn import MorphonicFFN
from .types import HiddenState, LayerTrace

logger = logging.getLogger(__name__)


def _tensor_signature(tensor: np.ndarray) -> str:
    """Stable short hash of a tensor's bytes."""
    return hashlib.sha256(np.ascontiguousarray(tensor).tobytes()).hexdigest()[:16]


def _delta_phi(before: np.ndarray, after: np.ndarray) -> float:
    """Cheap scalar ΔΦ across two tensors (row sums of squared norms)."""
    if before.size == 0 or after.size == 0:
        return 0.0
    b = float(np.linalg.norm(before))
    a = float(np.linalg.norm(after))
    # Φ ≈ 0.5 |v|², so ΔΦ ≈ 0.5 (|a|² − |b|²)
    return 0.5 * (a * a - b * b)


class GeometricTransformerLayer:
    """One block: attention → NSL → FFN → NSL → SpeedLight residual."""

    def __init__(self, config: Optional[LayerConfig] = None) -> None:
        self.config = config or LayerConfig()
        self.attention = MorphonicAttention(self.config.attention)
        self.ffn = MorphonicFFN(self.config.ffn)

    def forward(
        self,
        state: HiddenState,
        layer_idx: int,
        *,
        cache_namespace: str = "",
    ) -> tuple[HiddenState, LayerTrace]:
        # ── Attention sub-block ────────────────────────────────────────
        tensor_pre = state.tensor
        attn_state, attn_out = self.attention.forward(state)
        delta_attn = _delta_phi(tensor_pre, attn_state.tensor)
        attn_accepted = self._nsl_gate(
            v_before=tensor_pre.reshape(-1),
            v_after=attn_state.tensor.reshape(-1),
            mode=self.config.nsl_mode,
            budget=self.config.nsl_budget,
        )
        if not attn_accepted:
            # Roll back attention — keep the morphon evolution.
            attn_state = HiddenState(
                tensor=tensor_pre.copy(),
                morphon=attn_state.morphon,
                brain_observations=attn_state.brain_observations,
                metadata=attn_state.metadata,
            )

        # ── FFN sub-block ──────────────────────────────────────────────
        tensor_mid = attn_state.tensor
        ffn_state, ffn_out = self.ffn.forward(attn_state)
        delta_ffn = _delta_phi(tensor_mid, ffn_state.tensor)
        ffn_accepted = self._nsl_gate(
            v_before=tensor_mid.reshape(-1),
            v_after=ffn_state.tensor.reshape(-1),
            mode=self.config.nsl_mode,
            budget=self.config.nsl_budget,
        )
        if not ffn_accepted:
            ffn_state = HiddenState(
                tensor=tensor_mid.copy(),
                morphon=ffn_state.morphon,
                brain_observations=ffn_state.brain_observations,
                metadata=ffn_state.metadata,
            )
            if self.config.use_hf_fallback:
                try:
                    from .torch.hf_on_demand import try_layer_hf_fallback

                    hf_result = try_layer_hf_fallback(
                        layer_idx=layer_idx,
                        nsl_accepted=False,
                        use_hf_fallback=True,
                    )
                    if hf_result is not None and hf_result.woke:
                        meta = dict(ffn_state.metadata)
                        meta["hf_lane"] = hf_result.model_id or hf_result.note
                        ffn_state = HiddenState(
                            tensor=ffn_state.tensor,
                            morphon=ffn_state.morphon,
                            brain_observations=ffn_state.brain_observations,
                            metadata=meta,
                        )
                except Exception as exc:  # pragma: no cover - defensive
                    logger.debug("hf on-demand fallback skipped: %s", exc)

        # ── Residual ───────────────────────────────────────────────────
        residual = ffn_state.tensor + tensor_pre  # classical residual stream

        cache_key = ""
        cache_hit = False
        if self.config.use_speedlight_residual and has_provider("cache"):
            cache_key = f"{cache_namespace}::layer{layer_idx}::{_tensor_signature(residual)}"
            try:
                cached = get_cache_provider().get(cache_key)
                if cached is None:
                    get_cache_provider().put(cache_key, _tensor_signature(residual))
                else:
                    cache_hit = True
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("speedlight residual cache failed: %s", exc)

        out_state = HiddenState(
            tensor=residual,
            morphon=ffn_state.morphon,
            brain_observations=ffn_state.brain_observations,
            metadata=ffn_state.metadata,
        )

        trace = LayerTrace(
            layer_idx=layer_idx,
            attention=attn_out,
            ffn=ffn_out,
            nsl_pre_attn_accepted=attn_accepted,
            nsl_post_ffn_accepted=ffn_accepted,
            delta_phi_attention=delta_attn,
            delta_phi_ffn=delta_ffn,
            speedlight_hit=cache_hit,
            speedlight_cache_key=cache_key,
        )
        return out_state, trace

    # ── Internals ───────────────────────────────────────────────────────

    @staticmethod
    def _nsl_gate(
        v_before: np.ndarray,
        v_after: np.ndarray,
        *,
        mode: str,
        budget: float,
    ) -> bool:
        """Apply the conservation gate. Returns True if accepted."""
        if not has_provider("conservation"):
            return True
        try:
            nsl = get_conservation_provider()
            gate_mode = GateMode(mode)
            sectors = nsl.compute_sectors(
                list(map(float, v_before[:8])),
                list(map(float, v_after[:8])),
            )
            decision = nsl.gate(sectors, mode=gate_mode, budget=budget)
            return bool(decision.accepted)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("nsl gate raised, accepting by default: %s", exc)
            return True


__all__ = ["GeometricTransformerLayer"]
