"""
Optional HuggingFace on-demand lane — wake only when configured.

Default lane is ``off`` (``CMPLX_HF_LANE=off``). No torch/transformers import
until ``on_demand`` and ``wake()`` is invoked.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional

_LANE_ENV = "CMPLX_HF_LANE"
_VALID_LANES = frozenset({"off", "on_demand", "train"})


def hf_lane_from_env() -> str:
    """Read ``CMPLX_HF_LANE``; default ``off``."""
    raw = os.environ.get(_LANE_ENV, "off").strip().lower()
    if raw not in _VALID_LANES:
        return "off"
    return raw


def hf_lane_enabled() -> bool:
    """On-demand wake lane (not the bounded train window)."""
    return hf_lane_from_env() == "on_demand"


def hf_lane_train() -> bool:
    """Explicit train lane (see ``train_window.train_window_from_env``)."""
    return hf_lane_from_env() == "train"


@dataclass
class HFWakeContext:
    """Minimal context for a layer-bound HF fallback."""

    layer_idx: int = 0
    reason: str = ""
    tensor_signature: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HFWakeResult:
    """Outcome of a single on-demand wake (stub or real model)."""

    woke: bool
    model_id: str = ""
    note: str = ""


class HFOnDemandLane:
    """
    Lazy HF lane: loads external model machinery only after ``wake()``.

    Production substrate remains authoritative; this lane is a bounded
    fallback hook, not a parallel stack.
    """

    def __init__(self, *, model_name: str = "cmplx/hf-on-demand-stub") -> None:
        self.model_name = model_name
        self._wake_count = 0
        self._model: Any = None

    @property
    def wake_count(self) -> int:
        return self._wake_count

    def wake(self, context: Optional[HFWakeContext] = None) -> HFWakeResult:
        """Load (or stub) the HF model once per process for on_demand lane."""
        if not hf_lane_enabled():
            return HFWakeResult(woke=False, note="lane_off")

        self._wake_count += 1
        if self._model is None:
            self._model = {"stub": True, "model_name": self.model_name}
        _ = context  # reserved for layer_idx / NSL reject reason
        return HFWakeResult(woke=True, model_id=self.model_name, note="stub_wake")

    def reset(self) -> None:
        """Test helper: clear loaded model and wake counter."""
        self._model = None
        self._wake_count = 0


def try_layer_hf_fallback(
    *,
    layer_idx: int,
    nsl_accepted: bool,
    use_hf_fallback: bool,
    lane: Optional[HFOnDemandLane] = None,
) -> Optional[HFWakeResult]:
    """
    Layer hook: invoke on-demand lane when config requests fallback and NSL rejected.

    Returns ``None`` when lane is off or gate conditions are not met.
    """
    if not use_hf_fallback or nsl_accepted or not hf_lane_enabled():
        return None
    active = lane or HFOnDemandLane()
    return active.wake(
        HFWakeContext(layer_idx=layer_idx, reason="nsl_reject_ffn")
    )


__all__ = [
    "HFOnDemandLane",
    "HFWakeContext",
    "HFWakeResult",
    "hf_lane_enabled",
    "hf_lane_from_env",
    "hf_lane_train",
    "try_layer_hf_fallback",
]
