"""
Thin PyTorch wrapper around the numpy GeometricTransformer.

The substrate stays numpy-only; this module exists so callers can use
the transformer from a PyTorch pipeline without rewriting the host
code. No tensor weights are trainable here — the wrapper publishes the
last `HiddenState` tensor as a non-trainable buffer and exposes the
config so external optimisation surfaces (e.g. policy search) can
treat it like any other `nn.Module`.

Import is guarded so the rest of the package keeps working when torch
is unavailable.
"""
from __future__ import annotations

from typing import Any, Optional

try:
    import torch
    from torch import nn

    _HAS_TORCH = True
except Exception as exc:  # pragma: no cover - import-time only
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    _HAS_TORCH = False
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

from ..config import AttentionConfig, TransformerConfig
from ..transformer import GeometricTransformer
from ..types import TransformerOutput


def _require_torch() -> None:
    if not _HAS_TORCH:
        raise ImportError(
            "GeometricTransformerModule requires PyTorch. "
            "Install via `pip install -e .[torch]`. "
            f"Original error: {_IMPORT_ERROR!r}"
        )


class GeometricTransformerModule(nn.Module if _HAS_TORCH else object):  # type: ignore[misc]
    """nn.Module wrapper around the numpy `GeometricTransformer` backend."""

    def __init__(self, config: Optional[TransformerConfig] = None) -> None:
        _require_torch()
        super().__init__()  # type: ignore[misc]
        self.config = config or TransformerConfig()
        self.backend = GeometricTransformer(self.config)
        hidden_dim = int(self.config.hidden_dim or 24)
        seq_length = int(self.config.seq_length or self.config.tokenizer.seq_length)
        # Non-trainable buffer for the last hidden state tensor.
        self.register_buffer(
            "last_hidden",
            torch.zeros((seq_length, hidden_dim), dtype=torch.float32),
        )
        self._last_output: Optional[TransformerOutput] = None

    # ── Public API ──────────────────────────────────────────────────────

    def forward(self, ribbon: Any) -> dict:
        """Run the numpy backend and update the buffer.

        Accepts whatever the underlying tokenizer accepts (str, bytes,
        dict, …). Returns a small dict so the caller does not have to
        handle a non-tensor `TransformerOutput`. The raw output is
        available via `last_output()`.
        """
        out = self.backend.forward(ribbon)
        tensor = self.backend.tokenizer.tokenize(ribbon).tensor
        torch_tensor = torch.tensor(tensor, dtype=torch.float32)
        if torch_tensor.shape == self.last_hidden.shape:
            self.last_hidden.copy_(torch_tensor)
        self._last_output = out
        return {
            "ribbon_out": out.ribbon_out,
            "cache_key": out.cache_key,
            "morphon_id": out.final_morphon.id,
            "speedlight_hit": out.speedlight_hit,
            "num_layer_traces": len(out.layer_traces),
        }

    def last_output(self) -> Optional[TransformerOutput]:
        """Return the underlying TransformerOutput from the most recent forward."""
        return self._last_output

    # ── Settings passthrough ────────────────────────────────────────────

    def set_attention_policy(self, layer_idx: int, **kwargs: Any) -> None:
        """Update attention settings for a single layer.

        Useful for policy-search loops that want to perturb attention
        knobs without rebuilding the model.
        """
        layers = self.config.layers or []
        if not 0 <= layer_idx < len(layers):
            raise IndexError(f"layer_idx {layer_idx} out of range")
        current = layers[layer_idx].attention
        new = AttentionConfig(
            **{**current.__dict__, **kwargs}
        )
        layers[layer_idx].attention = new
        # Rebuild the underlying layer's attention block in place.
        self.backend.layers[layer_idx].attention.config = new

    def get_config(self) -> TransformerConfig:
        return self.config


__all__ = ["GeometricTransformerModule"]
