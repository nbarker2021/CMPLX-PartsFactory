"""
MorphonicAttention — Slot 48 attention.

The attention slot is filled by MORSR's diagnostic engine, not by
softmax QKV. For each block, we:

  1. Build an `Overlay` from the HiddenState (centroid = first-row
     8-D slice, optional 240-bit activation mask derived from the
     row's sign pattern).
  2. Configure the engine's `MORSRPolicy` from `AttentionConfig`.
  3. Call `pulse` / `traverse` / `scan` on the diagnostic port.
  4. Translate the result back into a new HiddenState tensor (the
     accepted overlay's position replaces the centroid row) and a
     summary `AttentionOutput`.

Changing `mode`, `shell_factors`, `max_stages`, `gate_mode`, etc.
changes the resulting trace observably — meeting plan criterion 4.
"""
from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any, Iterable, Optional

import numpy as np

from cmplx.morsr import (
    MORSRPolicy,
    Overlay,
    ShellMode,
    StopMetric,
    TraversalStrategy,
)
from cmplx.nsl import GateMode

from .bridge import get_diagnostic_provider
from .config import AttentionConfig
from .types import AttentionOutput, HiddenState

logger = logging.getLogger(__name__)


def _activation_mask_from_row(row: np.ndarray, mask_len: int = 240) -> tuple[int, ...]:
    """Derive a 240-bit activation mask from a tensor row.

    Each row entry's sign votes for a chunk of the mask so the mask
    reflects the row's structure without requiring a dedicated
    embedding. Stable for stable rows.
    """
    if row.size == 0:
        return tuple(0 for _ in range(mask_len))
    signs = (row > 0.0).astype(np.int64)
    repeats = max(1, mask_len // max(row.size, 1))
    expanded = np.repeat(signs, repeats)
    if expanded.size < mask_len:
        pad = np.zeros(mask_len - expanded.size, dtype=np.int64)
        expanded = np.concatenate([expanded, pad])
    return tuple(int(x) & 1 for x in expanded[:mask_len])


def _policy_from_config(cfg: AttentionConfig) -> MORSRPolicy:
    """Translate the public-facing config into the engine's policy type."""
    return MORSRPolicy(
        eps_phi=cfg.eps_phi,
        plateau_cap=cfg.plateau_cap,
        shell_mode=ShellMode(cfg.shell_mode),
        shell_base=cfg.shell_base,
        shell_factors=tuple(int(x) for x in cfg.shell_factors),
        stop_metric=StopMetric(cfg.stop_metric),
        stop_threshold=cfg.stop_threshold,
        ema_alpha=cfg.ema_alpha,
        max_stages=cfg.max_stages,
        gate_mode=GateMode(cfg.gate_mode),
        stage_budget=cfg.stage_budget,
    )


class MorphonicAttention:
    """Settings-driven attention block backed by the MORSR diagnostic port."""

    def __init__(self, config: Optional[AttentionConfig] = None) -> None:
        self.config = config or AttentionConfig()

    # ── Public API ──────────────────────────────────────────────────────

    def _effective_scan_radius(self, state: HiddenState) -> float:
        radius = float(self.config.scan_radius)
        metrics = state.metadata.get("token_metrics") if state.metadata else None
        if isinstance(metrics, dict):
            mass = float(metrics.get("token_mass", metrics.get("mass_e8", 0)) or 0)
            if mass > 0:
                radius *= 1.0 + 0.05 * min(mass, 20.0)
        return radius

    def forward(self, state: HiddenState) -> tuple[HiddenState, AttentionOutput]:
        provider = get_diagnostic_provider()
        seed = self._build_overlay(state.tensor)
        if self.config.mode == "pulse":
            output, new_position = self._run_pulse(provider, seed)
        elif self.config.mode == "traverse":
            output, new_position = self._run_traverse(provider, seed)
        elif self.config.mode == "scan":
            output, new_position = self._run_scan(provider, seed, state)
        else:
            raise ValueError(f"unknown attention mode: {self.config.mode!r}")

        new_tensor = self._apply_position(state.tensor, new_position)
        new_state = HiddenState(
            tensor=new_tensor,
            morphon=state.morphon,
            brain_observations=dict(state.brain_observations),
            metadata=dict(state.metadata),
        )
        return new_state, output

    # ── Mode runners ────────────────────────────────────────────────────

    def _run_pulse(
        self,
        provider: Any,
        seed: Overlay,
    ) -> tuple[AttentionOutput, tuple[float, ...]]:
        prior_policy = deepcopy(provider.engine.policy)
        try:
            provider.engine.policy = _policy_from_config(self.config)
            region = provider.pulse(seed)
        finally:
            provider.engine.policy = prior_policy

        final = region.overlay_store.get(region.final_overlay_id)
        position = final.position if final is not None else seed.position

        summary = region.summary()
        return (
            AttentionOutput(
                mode="pulse",
                final_overlay_id=region.final_overlay_id,
                cumulative_delta_phi=float(summary.get("cumulative_delta_phi", 0.0)),
                handshake_count=int(summary.get("total_attempts", 0)),
                accept_count=int(summary.get("total_accepts", 0)),
                stage_count=int(summary.get("stage_count", 0)),
                status=str(region.status),
                extra={"overlays_accepted": int(summary.get("overlays_accepted", 0))},
            ),
            position,
        )

    def _run_traverse(
        self,
        provider: Any,
        seed: Overlay,
    ) -> tuple[AttentionOutput, tuple[float, ...]]:
        strategy = TraversalStrategy(self.config.traverse_strategy)
        result = provider.traverse(seed, strategy=strategy)
        summary = result.summary()
        return (
            AttentionOutput(
                mode="traverse",
                final_overlay_id="",
                cumulative_delta_phi=float(-summary.get("best_score", 0.0)),
                handshake_count=int(summary.get("nodes_visited", 0)),
                accept_count=int(summary.get("nodes_visited", 0)),
                stage_count=int(summary.get("nodes_visited", 0)),
                status=str(summary.get("strategy", strategy.value)),
                extra={"best_node_index": int(result.best_node_index)},
            ),
            tuple(float(x) for x in result.best_vector),
        )

    def _run_scan(
        self,
        provider: Any,
        seed: Overlay,
        state: HiddenState,
    ) -> tuple[AttentionOutput, tuple[float, ...]]:
        # SonarScan.ping expects a source coordinate tuple, not an Overlay.
        result = provider.scan(seed.position, radius=self._effective_scan_radius(state))
        return (
            AttentionOutput(
                mode="scan",
                final_overlay_id="",
                cumulative_delta_phi=0.0,
                handshake_count=int(result.directions_total),
                accept_count=int(result.hit_count),
                stage_count=1,
                status=str(result.shell),
                extra={
                    "depth_score": float(result.depth_score),
                    "shadow_actions": len(result.shadow_actions),
                },
            ),
            seed.position,
        )

    # ── Internals ───────────────────────────────────────────────────────

    def _build_overlay(self, tensor: np.ndarray) -> Overlay:
        first_row = tensor[0] if tensor.ndim == 2 and tensor.shape[0] > 0 else tensor.reshape(-1)
        position_full = np.asarray(first_row, dtype=np.float64)
        # MORSR Overlay defaults to 8-D position; pad/truncate.
        if position_full.size >= 8:
            position = tuple(float(x) for x in position_full[:8])
        else:
            padded = np.zeros(8, dtype=np.float64)
            padded[: position_full.size] = position_full
            position = tuple(float(x) for x in padded)
        activations = _activation_mask_from_row(position_full)
        return Overlay(position=position, activations=activations)

    @staticmethod
    def _apply_position(
        tensor: np.ndarray,
        position: Iterable[float],
    ) -> np.ndarray:
        new_tensor = tensor.copy()
        if new_tensor.ndim != 2 or new_tensor.shape[0] == 0:
            return new_tensor
        pos_arr = np.asarray(list(position), dtype=np.float64)
        width = new_tensor.shape[1]
        if pos_arr.size >= width:
            new_tensor[0] = pos_arr[:width]
        else:
            new_tensor[0, : pos_arr.size] = pos_arr
        return new_tensor


__all__ = ["MorphonicAttention"]
