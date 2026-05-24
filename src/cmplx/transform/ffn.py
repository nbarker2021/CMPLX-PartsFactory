"""
MorphonicFFN — Slot 48 FFN block.

Runs the TarPit symbolic provider on the layer's morphon and uses the
resulting torus8 / wall10 state to perturb the hidden tensor. Optional
toolkit passes (e.g. SNAP labelling, MDHG placement) chain after the
core derive when their ports are registered.

The block is purposefully thin: the heavy lifting belongs to the
symbolic port. This module just translates the hidden state into a
morphon payload, dispatches, and writes the result back.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

from cmplx.morphon import Morphon

from .bridge import (
    get_addressing_provider,
    get_snap_provider,
    get_symbolic_provider,
    has_provider,
)
from .config import FFNConfig
from .types import FFNOutput, HiddenState

logger = logging.getLogger(__name__)


def _torus_to_tensor(torus: list, hidden_dim: int) -> np.ndarray:
    """Tile an 8-D torus vector across `hidden_dim`."""
    if not torus:
        return np.zeros(hidden_dim, dtype=np.float64)
    arr = np.asarray(torus, dtype=np.float64)
    if arr.size >= hidden_dim:
        return arr[:hidden_dim]
    reps = (hidden_dim + arr.size - 1) // arr.size
    return np.tile(arr, reps)[:hidden_dim]


class MorphonicFFN:
    """Settings-driven FFN block backed by the TarPit symbolic port."""

    def __init__(self, config: Optional[FFNConfig] = None) -> None:
        self.config = config or FFNConfig()

    def forward(self, state: HiddenState) -> tuple[HiddenState, FFNOutput]:
        provider = get_symbolic_provider()
        # Honour configured TarPit dimensions / program length when the
        # provider supports them. Skip mutation for mesh proxies (they have
        # __slots__ and remote services own their own config).
        original_dim = getattr(provider, "default_dimension", None)
        original_steps = getattr(provider, "default_max_steps", None)
        original_prog = getattr(provider, "program_length", None)
        _has_dict = getattr(provider, "__dict__", None) is not None
        try:
            if original_dim is not None and _has_dict:
                provider.default_dimension = self.config.dimension
            if original_steps is not None and _has_dict:
                provider.default_max_steps = self.config.max_steps
            if original_prog is not None and _has_dict:
                provider.program_length = self.config.program_length
            report = provider.derive(state.morphon)
        finally:
            if original_dim is not None and _has_dict:
                provider.default_dimension = original_dim
            if original_steps is not None and _has_dict:
                provider.default_max_steps = original_steps
            if original_prog is not None and _has_dict:
                provider.program_length = original_prog

        ledger = report.trace if hasattr(report, "trace") else []
        final = ledger[-1] if ledger else {}
        torus = final.get("torus8") if isinstance(final, dict) else None
        steps = int(final.get("step", len(ledger))) if isinstance(final, dict) else len(ledger)
        halted = bool(final.get("halted_now", False)) if isinstance(final, dict) else False

        hidden_dim = state.tensor.shape[1] if state.tensor.ndim == 2 else state.tensor.size
        torus_vec = _torus_to_tensor(torus or [], hidden_dim)

        new_tensor = state.tensor.copy()
        if new_tensor.ndim == 2 and new_tensor.shape[0] > 0:
            new_tensor[-1] = torus_vec  # write torus8 fingerprint into last row
        elif new_tensor.ndim == 1:
            new_tensor = torus_vec.copy()

        # Decode the ledger back into a payload morphon and merge into our
        # morphon's payload so downstream layers see the derivation result.
        new_payload = dict(state.morphon.payload)
        try:
            derived_morphon = provider.decode_from_etp(ledger)
            new_payload.update({
                "tarpit_torus8": list(derived_morphon.payload.get("torus8", [])),
                "tarpit_wall10": derived_morphon.payload.get("wall10", "0.000"),
                "tarpit_digital_root": derived_morphon.payload.get("digital_root", 0),
                "tarpit_steps": steps,
                "tarpit_halted": halted,
            })
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("symbolic.decode_from_etp raised: %s", exc)

        new_morphon = Morphon.forge(
            payload=new_payload,
            parent=state.morphon.id,
        )
        new_morphon.e8_coordinates = state.morphon.e8_coordinates
        new_morphon.leech_point = state.morphon.leech_point
        new_morphon.dr_channel = state.morphon.dr_channel

        # Toolkit passes — best-effort, log if missing.
        applied_passes: list[str] = []
        for name in self.config.toolkit_passes:
            applied = self._apply_toolkit_pass(name, new_morphon)
            if applied:
                applied_passes.append(name)

        new_state = HiddenState(
            tensor=new_tensor,
            morphon=new_morphon,
            brain_observations=dict(state.brain_observations),
            metadata=dict(state.metadata),
        )

        return new_state, FFNOutput(
            mode=self.config.derive_mode,
            program_length=self.config.program_length,
            steps=steps,
            halted=halted,
            output_walls=len(report.output_walls) if hasattr(report, "output_walls") else 0,
            error_walls=len(report.error_walls) if hasattr(report, "error_walls") else 0,
            toolkit_passes=applied_passes,
        )

    # ── Internals ───────────────────────────────────────────────────────

    @staticmethod
    def _apply_toolkit_pass(name: str, morphon: Morphon) -> bool:
        if name == "run_snap" and has_provider("snap"):
            try:
                get_snap_provider()  # availability check is enough for MVP
                return True
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("snap pass failed: %s", exc)
        if name == "run_mdhg_place" and has_provider("addressing"):
            try:
                addressing = get_addressing_provider()
                channel = addressing.channel_for(morphon)
                morphon.dr_channel = int(channel)
                return True
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("mdhg_place pass failed: %s", exc)
        return False


__all__ = ["MorphonicFFN"]
