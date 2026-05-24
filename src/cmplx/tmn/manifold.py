from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import logging

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ChannelState:
    """State of one parity channel in the manifold."""

    channel_id: int = 0
    policy_type: int = 1  # 1-8 matching PolicyChannel enum
    block_indices: List[Tuple[int, int]] = field(default_factory=list)
    local_lr: float = 0.001
    local_prune_threshold: float = 0.03
    energy: float = 0.0
    sparsity: float = 0.0
    stability: float = 1.0
    update_count: int = 0
    repair_count: int = 0
    energy_history: List[float] = field(default_factory=list)
    max_history: int = 50


@dataclass
class ExpertModule:
    """Specialized expert module (post-critical period)."""

    name: str
    domain: str  # 'auditor', 'healer', 'expander', etc.
    weights: np.ndarray
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    specialization_score: float = 0.0


class Manifold:
    """Block-structured weight manifold with embedded micro-controllers.

    The 24D Leech lattice is built from 4D blocks. Each block has a
    MicroController that self-heals, self-learns, and self-monitors.
    """

    def __init__(self, dims: int = 24, block_size: int = 4):
        self.dims = dims
        self.block_size = block_size
        self.n_blocks = dims // block_size
        self.weights = np.random.randn(dims, dims) * np.sqrt(2.0 / dims)
        self._tick_count = 0

        all_blocks = [
            (i, j) for i in range(self.n_blocks) for j in range(self.n_blocks)
        ]
        right_blocks = [(i, j) for i, j in all_blocks if j >= i]
        left_blocks = [(i, j) for i, j in all_blocks if i >= j]
        self.channels: List[MicroController] = []

        for ch in range(4):
            stripe = [
                right_blocks[k]
                for k in range(len(right_blocks))
                if k % 4 == ch
            ]
            ctrl = MicroController(
                channel_id=ch,
                block_indices=stripe,
                policy_type=ch + 1,
                is_parity=False,
                block_size=block_size,
            )
            ctrl.state.local_lr = 0.0015
            self.channels.append(ctrl)

        for ch in range(4):
            stripe = [
                left_blocks[k]
                for k in range(len(left_blocks))
                if k % 4 == ch
            ]
            ctrl = MicroController(
                channel_id=4 + ch,
                block_indices=stripe,
                policy_type=ch + 5,
                is_parity=False,
                block_size=block_size,
            )
            ctrl.state.local_lr = 0.0005
            self.channels.append(ctrl)

        self.channels.append(
            MicroController(
                channel_id=8,
                block_indices=[],
                policy_type=1,
                is_parity=True,
                block_size=block_size,
            )
        )
        self.channels.append(
            MicroController(
                channel_id=9,
                block_indices=[],
                policy_type=2,
                is_parity=True,
                block_size=block_size,
            )
        )

        self._rotation = {
            0: [0, 1, 2, 3],  # right-chiral: generative
            1: [4, 5, 6, 7],  # left-chiral: recall
            2: [8, 9],  # parity: coherence check
        }

    @property
    def blocks(self) -> List[List[np.ndarray]]:
        bs = self.block_size
        result = []
        for i in range(self.n_blocks):
            row = []
            for j in range(self.n_blocks):
                row.append(
                    self.weights[i * bs : (i + 1) * bs, j * bs : (j + 1) * bs]
                )
            result.append(row)
        return result

    def get_block(self, i: int, j: int) -> np.ndarray:
        bs = self.block_size
        return self.weights[i * bs : (i + 1) * bs, j * bs : (j + 1) * bs].copy()

    def set_block(self, i: int, j: int, block: np.ndarray) -> None:
        bs = self.block_size
        self.weights[i * bs : (i + 1) * bs, j * bs : (j + 1) * bs] = block

    def merge_from(
        self,
        other: Manifold,
        block_indices: Optional[List[Tuple[int, int]]] = None,
        alpha: float = 0.5,
    ) -> None:
        if block_indices is None:
            block_indices = [
                (i, j)
                for i in range(self.n_blocks)
                for j in range(self.n_blocks)
            ]
        for i, j in block_indices:
            my_block = self.get_block(i, j)
            their_block = other.get_block(i, j)
            blended = (1 - alpha) * my_block + alpha * their_block
            self.set_block(i, j, blended)

    def split(self, block_indices: List[Tuple[int, int]]) -> Manifold:
        child = Manifold(self.dims, self.block_size)
        child.weights = np.zeros_like(self.weights)
        for i, j in block_indices:
            child.set_block(i, j, self.get_block(i, j))
        return child

    def block_norms(self) -> np.ndarray:
        norms = np.zeros((self.n_blocks, self.n_blocks))
        for i in range(self.n_blocks):
            for j in range(self.n_blocks):
                norms[i, j] = np.linalg.norm(self.get_block(i, j))
        return norms

    def tick(self) -> None:
        self._tick_count += 1
        phase = self._tick_count % 3
        active_ids = self._rotation[phase]

        for ch_id in active_ids:
            ch = self.channels[ch_id]
            if ch.is_parity:
                data_channels = [c for c in self.channels if not c.is_parity]
                unstable = ch.parity_check(data_channels)
                if unstable:
                    for uch_id in unstable:
                        uch = self.channels[uch_id]
                        blocks = {
                            idx: self.get_block(*idx)
                            for idx in uch.state.block_indices
                        }
                        healed = uch.heal(blocks, self._safe_get_block)
                        for idx, hblock in healed.items():
                            self.set_block(*idx, hblock)
            else:
                blocks = {
                    idx: self.get_block(*idx) for idx in ch.state.block_indices
                }
                ch.observe(blocks)
                healed = ch.heal(blocks, self._safe_get_block)
                for idx, hblock in healed.items():
                    self.set_block(*idx, hblock)
                ch.tune_lr()

    def _safe_get_block(self, i: int, j: int) -> Optional[np.ndarray]:
        if 0 <= i < self.n_blocks and 0 <= j < self.n_blocks:
            return self.get_block(i, j)
        return None

    def health_report(self) -> Dict[str, Any]:
        data_reports = [
            ch.health_report() for ch in self.channels if not ch.is_parity
        ]
        parity_reports = [
            ch.health_report() for ch in self.channels if ch.is_parity
        ]
        avg_stability = (
            np.mean([r["stability"] for r in data_reports])
            if data_reports
            else 1.0
        )
        total_repairs = sum(r["repairs"] for r in data_reports)
        min_stability = min(
            (r["stability"] for r in data_reports), default=1.0
        )
        weakest = (
            min(data_reports, key=lambda r: r["stability"])
            if data_reports
            else {}
        )
        return {
            "n_channels": len(self.channels),
            "data_channels": len(data_reports),
            "parity_channels": len(parity_reports),
            "tick": self._tick_count,
            "phase": self._tick_count % 3,
            "avg_stability": round(float(avg_stability), 4),
            "min_stability": round(float(min_stability), 4),
            "total_repairs": total_repairs,
            "weakest_channel": weakest,
        }

    def get_block_lr(self, i: int, j: int) -> float:
        for ch in self.channels:
            if not ch.is_parity and (i, j) in ch.state.block_indices:
                return ch.state.local_lr
        return 0.001

    def resolution(self, level: int = 1) -> np.ndarray:
        if level <= 1:
            return self.weights
        elif level == 2:
            return self.block_norms()
        else:
            return np.array([[np.linalg.norm(self.weights)]])

    def grow(self, new_dims: int) -> Manifold:
        grown = Manifold(new_dims, self.block_size)
        grown.weights = np.random.randn(new_dims, new_dims) * np.sqrt(
            2.0 / new_dims
        )
        min_d = min(self.dims, new_dims)
        grown.weights[:min_d, :min_d] = self.weights[:min_d, :min_d]
        return grown


class MicroController:
    """Self-healing channel controller — one per parity channel.

    8 data channels + 2 parity channels = 10 total (8b/10b encoding).
    Each channel manages a stripe of blocks in the manifold.
    """

    def __init__(
        self,
        channel_id: int,
        block_indices: List[Tuple[int, int]],
        policy_type: int = 1,
        is_parity: bool = False,
        block_size: int = 4,
    ):
        self.state = ChannelState(
            channel_id=channel_id,
            policy_type=policy_type,
            block_indices=block_indices,
        )
        self.is_parity = is_parity
        self.block_size = block_size
        self._snapshots: Dict[Tuple[int, int], np.ndarray] = {}
        self._max_norm = 5.0
        self._min_norm = 0.01
        self._max_drift = 0.5

    def observe(self, blocks: Dict[Tuple[int, int], np.ndarray]) -> None:
        total_energy = 0.0
        total_sparsity = 0.0
        min_stability = 1.0
        n = len(blocks)

        for (i, j), block in blocks.items():
            energy = float(np.linalg.norm(block))
            sparsity = float(np.mean(np.abs(block) < 1e-6))
            total_energy += energy
            total_sparsity += sparsity

            prev = self._snapshots.get((i, j))
            if prev is not None:
                drift = float(np.linalg.norm(block - prev))
                stab = max(0, 1.0 - drift / self._max_drift)
                min_stability = min(min_stability, stab)
            self._snapshots[(i, j)] = block.copy()

        self.state.energy = total_energy / max(n, 1)
        self.state.sparsity = total_sparsity / max(n, 1)
        self.state.stability = min_stability
        self.state.energy_history.append(self.state.energy)
        if len(self.state.energy_history) > self.state.max_history:
            self.state.energy_history.pop(0)

    def heal(
        self,
        blocks: Dict[Tuple[int, int], np.ndarray],
        all_blocks_getter,
    ) -> Dict[Tuple[int, int], np.ndarray]:
        healed: Dict[Tuple[int, int], np.ndarray] = {}
        for (i, j), block in blocks.items():
            fixed = block.copy()
            repaired = False

            bad = ~np.isfinite(fixed)
            if np.any(bad):
                neighbors = []
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    try:
                        nb = all_blocks_getter(i + di, j + dj)
                        if nb is not None:
                            neighbors.append(nb)
                    except (IndexError, KeyError):
                        pass
                if neighbors:
                    fixed[bad] = np.mean(neighbors, axis=0)[bad]
                else:
                    fixed[bad] = 0.0
                repaired = True

            norm = np.linalg.norm(fixed)
            if norm > self._max_norm:
                fixed *= self._max_norm / norm
                repaired = True

            prev = self._snapshots.get((i, j))
            if self.state.stability < 0.3 and prev is not None:
                fixed = 0.7 * fixed + 0.3 * prev
                repaired = True

            if repaired:
                self.state.repair_count += 1
            healed[(i, j)] = fixed

        self.state.update_count += 1
        return healed

    def tune_lr(self) -> float:
        if len(self.state.energy_history) < 5:
            return self.state.local_lr
        recent = self.state.energy_history[-5:]
        trend = recent[-1] - recent[0]
        if trend > 0.5:
            self.state.local_lr *= 0.9
        elif trend < -0.1 and self.state.stability > 0.7:
            self.state.local_lr *= 1.05
        self.state.local_lr = max(1e-6, min(0.01, self.state.local_lr))
        return self.state.local_lr

    def parity_check(
        self, data_channels: List[MicroController]
    ) -> List[int]:
        unstable = []
        for ch in data_channels:
            if ch.state.stability < 0.5:
                unstable.append(ch.state.channel_id)
        return unstable

    def health_report(self) -> Dict[str, Any]:
        return {
            "channel": self.state.channel_id,
            "policy": self.state.policy_type,
            "is_parity": self.is_parity,
            "blocks": len(self.state.block_indices),
            "energy": round(self.state.energy, 4),
            "sparsity": round(self.state.sparsity, 4),
            "stability": round(self.state.stability, 4),
            "local_lr": round(self.state.local_lr, 6),
            "updates": self.state.update_count,
            "repairs": self.state.repair_count,
        }
