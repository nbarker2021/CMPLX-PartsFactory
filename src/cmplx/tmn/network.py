from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import hashlib
import json
import logging

import numpy as np

from .manifold import ExpertModule, Manifold

logger = logging.getLogger(__name__)


class _SimpleSpectrum:
    """Fallback spectrum when no external decompose() is injected."""

    def __init__(self, weights: np.ndarray) -> None:
        # Simple SVD-based decomposition
        try:
            u, s, vh = np.linalg.svd(weights)
            self.total_strands = int(np.sum(s > 1e-6))
            self.dominant_period = float(s[0]) if len(s) > 0 else 0.0
        except Exception:
            self.total_strands = 0
            self.dominant_period = 0.0
        upper = np.sum(np.triu(weights, k=1) ** 2)
        lower = np.sum(np.tril(weights, k=-1) ** 2)
        self.chirality_balance = float(upper / (lower + 1e-8))


def _default_decompose(tmn: TriadicManifoldNetwork) -> _SimpleSpectrum:
    return _SimpleSpectrum(tmn.weights)


def _default_quantum_numbers(spectrum: _SimpleSpectrum) -> Dict[str, Any]:
    return {
        "strands": spectrum.total_strands,
        "period": spectrum.dominant_period,
    }


@dataclass
class TriadicState:
    """Current state of triadic constraints."""

    noether: np.ndarray = field(default_factory=lambda: np.zeros((3, 3)))
    shannon: np.ndarray = field(default_factory=lambda: np.zeros((3, 3)))
    landauer: np.ndarray = field(default_factory=lambda: np.zeros((3, 3)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "noether_trace": float(np.trace(self.noether)),
            "shannon_trace": float(np.trace(self.shannon)),
            "landauer_trace": float(np.trace(self.landauer)),
            "triadic_energy": float(self.energy()),
        }

    def energy(self) -> float:
        return (
            np.trace(self.noether)
            + np.trace(self.shannon)
            + np.trace(self.landauer)
        )


class TriadicManifoldNetwork:
    """Self-improving neural network using triadic constraints.

    Architecture:
    - 24D initial (Niemeier/Leech lattice)
    - Dynamic growth (increments of 8, E8 structure)
    - Critical period at epoch 300 (scale-3)
    - Expert modules post-hardening
    """

    def __init__(
        self,
        init_dims: int = 24,
        max_dims: int = 96,
        growth_increment: int = 8,
        prune_threshold: float = 0.03,
        critical_epoch: int = 300,
        *,
        decompose_fn=None,
        quantum_fn=None,
    ):
        self.init_dims = init_dims
        self.max_dims = max_dims
        self.dims = init_dims
        self.growth_increment = growth_increment
        self.prune_threshold = prune_threshold
        self.critical_epoch = critical_epoch
        self.generation = 0
        self.crystallization_threshold = 0.5
        self.crystallized = False
        self.glyph: Optional[Dict[str, Any]] = None

        self.manifold = Manifold(self.dims, block_size=4)
        self.triads = TriadicState()

        self.epoch = 0
        self.frozen = False
        self.experts: List[ExpertModule] = []
        self.mi_history: List[float] = []
        self.sparsity_history: List[float] = []

        self.hebbian_lr = 0.001
        self.mutual_information = 0.0

        self._decompose_fn = decompose_fn or _default_decompose
        self._quantum_fn = quantum_fn or _default_quantum_numbers

    @property
    def weights(self) -> np.ndarray:
        return self.manifold.weights

    @weights.setter
    def weights(self, value: np.ndarray) -> None:
        self.manifold.weights = value

    def encode_code(self, code: str) -> np.ndarray:
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        np.random.seed(int(code_hash[:16], 16) % (2**32))
        encoding = np.random.randn(self.dims)
        encoding = encoding / (np.linalg.norm(encoding) + 1e-8)
        return encoding

    def forward(self, x: np.ndarray) -> np.ndarray:
        if len(x) != self.dims:
            x = (
                np.pad(x, (0, self.dims - len(x)))
                if len(x) < self.dims
                else x[: self.dims]
            )
        x = np.clip(x, -10, 10)
        h = np.tanh(self.weights @ x)
        triad_gate = self._compute_triad_gate()
        return h * (1 + 0.1 * triad_gate)

    def recall(self, x: np.ndarray) -> np.ndarray:
        if len(x) != self.dims:
            x = (
                np.pad(x, (0, self.dims - len(x)))
                if len(x) < self.dims
                else x[: self.dims]
            )
        x = np.clip(x, -10, 10)
        h = np.tanh(self.weights.T @ x)
        triad_gate = self._compute_triad_gate()
        return h * (1 + 0.1 * triad_gate)

    def chirality_coherence(self, x: np.ndarray) -> float:
        gen = self.forward(x)
        rec = self.recall(x)
        dot = np.dot(gen, rec)
        norms = np.linalg.norm(gen) * np.linalg.norm(rec)
        return float(dot / (norms + 1e-8))

    def _compute_triad_gate(self) -> float:
        n_mod = np.trace(self.triads.noether) / (
            np.linalg.norm(self.triads.noether) + 1e-8
        )
        s_mod = np.trace(self.triads.shannon) / (
            np.linalg.norm(self.triads.shannon) + 1e-8
        )
        l_mod = np.trace(self.triads.landauer) / (
            np.linalg.norm(self.triads.landauer) + 1e-8
        )
        return (n_mod + s_mod + l_mod) / 3.0

    def learn(self, input_data: str, output_data: str) -> Dict[str, Any]:
        if self.frozen:
            return {"status": "frozen", "epoch": self.epoch}

        x = self.encode_code(input_data)
        y_target = self.encode_code(output_data)
        y_pred = self.forward(x)
        self._hebbian_update(x, y_pred)
        self._update_triads(x, y_pred)

        mi = (
            np.corrcoef(y_pred, y_target)[0, 1]
            if len(y_pred) == len(y_target)
            else 0
        )
        self.mutual_information = (
            0.9 * self.mutual_information + 0.1 * mi
        )
        self.mi_history.append(self.mutual_information)

        grew = self._check_growth()
        self.epoch += 1

        if self.epoch == self.critical_epoch:
            self._critical_period_pruning()

        return {
            "epoch": self.epoch,
            "mutual_information": float(self.mutual_information),
            "triadic_energy": float(self.triads.energy()),
            "sparsity": self._calculate_sparsity(),
            "grew": grew,
            "frozen": self.frozen,
        }

    def _hebbian_update(self, x: np.ndarray, y: np.ndarray) -> None:
        x_norm = x / (np.linalg.norm(x) + 1e-8)
        y_norm = y / (np.linalg.norm(y) + 1e-8)

        bs = self.manifold.block_size
        for bi in range(self.manifold.n_blocks):
            for bj in range(self.manifold.n_blocks):
                lr = self.manifold.get_block_lr(bi, bj)
                xi = x_norm[bi * bs : (bi + 1) * bs]
                yj = y_norm[bj * bs : (bj + 1) * bs]
                if len(xi) == bs and len(yj) == bs:
                    dW = lr * np.outer(yj, xi)
                    block = self.manifold.get_block(bi, bj)
                    self.manifold.set_block(bi, bj, block + dW)

        self.manifold.tick()

    def _update_triads(self, x: np.ndarray, y: np.ndarray) -> None:
        if len(x) >= 3 and len(y) >= 3:
            x_triad = np.clip(x[:3].reshape(-1), -10, 10)
            y_triad = np.clip(y[:3].reshape(-1), -10, 10)
            self.triads.noether += 0.01 * np.outer(x_triad, x_triad)
            self.triads.shannon += 0.01 * np.outer(y_triad, x_triad)
            self.triads.landauer += 0.01 * np.outer(y_triad, y_triad)

    def _check_growth(self) -> bool:
        if self.dims >= self.max_dims:
            return False
        if (
            self.mutual_information > 0.5
            and self.epoch % 100 == 0
        ):
            return self.grow()
        return False

    def grow(self) -> bool:
        if self.dims >= self.max_dims:
            return False
        new_dims = min(self.dims + self.growth_increment, self.max_dims)
        new_weights = np.random.randn(new_dims, new_dims) * np.sqrt(
            2.0 / new_dims
        )
        new_weights[: self.dims, : self.dims] = self.weights
        self.weights = new_weights
        self.dims = new_dims
        return True

    def _critical_period_pruning(self) -> None:
        weight_mags = np.abs(self.weights)
        w_max = np.max(weight_mags)
        if w_max < 1e-10:
            return
        threshold = self.prune_threshold * w_max
        pruned_mask = weight_mags < threshold
        self.weights[pruned_mask] = 0
        pruned_count = int(np.sum(pruned_mask))
        logger.debug(
            "Critical period pruning: %d/%d weights zeroed (threshold=%.4f)",
            pruned_count,
            self.weights.size,
            threshold,
        )
        self._create_experts()

    def _create_experts(self) -> None:
        domains = ["auditor", "healer", "expander", "optimizer", "validator"]
        for domain in domains:
            expert = ExpertModule(
                name=f"expert_{domain}",
                domain=domain,
                weights=self.weights.copy(),
                specialization_score=0.7,
            )
            self.experts.append(expert)

    def _calculate_sparsity(self) -> float:
        return float(np.mean(self.weights == 0))

    # -- Crystallization Cycle --

    def _check_crystallization(self) -> bool:
        if self.crystallized:
            return False
        if self.dims < self.max_dims:
            return False
        if self.triads.energy() > self.crystallization_threshold:
            return False
        if self.epoch < self.critical_epoch:
            return False
        return True

    def crystallize(self) -> Dict[str, Any]:
        spectrum = self._decompose_fn(self)
        qn = self._quantum_fn(spectrum)
        content_hash = hashlib.sha256(
            self.weights.tobytes()
        ).hexdigest()
        e8_address = self.weights[:8, :8].flatten()[:8].tolist()

        glyph = {
            "content_hash": content_hash,
            "e8_address": e8_address,
            "spinor_signature": qn,
            "generation": self.generation,
            "dims_at_crystal": self.dims,
            "epoch_at_crystal": self.epoch,
            "triadic_energy": float(self.triads.energy()),
            "n_experts": len(self.experts),
            "sparsity": self._calculate_sparsity(),
            "strand_count": spectrum.total_strands,
            "dominant_period": spectrum.dominant_period,
            "chirality_balance": spectrum.chirality_balance,
        }

        self.crystallized = True
        self.glyph = glyph
        return glyph

    def spawn_next_generation(
        self, glyph: Optional[Dict[str, Any]] = None
    ) -> TriadicManifoldNetwork:
        glyph = glyph or self.glyph
        if glyph is None:
            raise ValueError(
                "No glyph to spawn from — crystallize first"
            )

        child = TriadicManifoldNetwork(
            init_dims=self.init_dims,
            max_dims=self.max_dims,
            growth_increment=self.growth_increment,
            critical_epoch=self.critical_epoch,
            decompose_fn=self._decompose_fn,
            quantum_fn=self._quantum_fn,
        )
        child.generation = glyph["generation"] + 1

        seed = np.array(glyph["e8_address"][:8])
        seed = seed / (np.linalg.norm(seed) + 1e-8)
        child.weights[:8, :8] = np.outer(seed, seed) * np.sqrt(2.0 / 8)
        return child

    def analyze_code(
        self, code: str, context: str = ""
    ) -> Dict[str, Any]:
        encoding = self.encode_code(code)
        processed = self.forward(encoding)
        norm = np.linalg.norm(processed)
        sparsity = np.mean(np.abs(processed) < 0.1)
        triad_scores = {
            "conservation": float(np.trace(self.triads.noether)),
            "information": float(np.trace(self.triads.shannon)),
            "energy": float(np.trace(self.triads.landauer)),
        }
        return {
            "encoding_norm": float(norm),
            "sparsity": float(sparsity),
            "triadic_scores": triad_scores,
            "manifold_position": processed[:8].tolist(),
            "context": context,
        }

    def get_expert(self, domain: str) -> Optional[ExpertModule]:
        for expert in self.experts:
            if expert.domain == domain:
                return expert
        return None

    def state_dict(self) -> Dict[str, Any]:
        return {
            "dims": self.dims,
            "epoch": self.epoch,
            "frozen": self.frozen,
            "weights_shape": list(self.weights.shape),
            "triads": self.triads.to_dict(),
            "mutual_information": float(self.mutual_information),
            "experts": [
                {
                    "name": e.name,
                    "domain": e.domain,
                    "specialization": e.specialization_score,
                }
                for e in self.experts
            ],
        }

    # -- Persistence --

    def save(self, path: str) -> str:
        import os

        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        state = {
            "dims": self.dims,
            "max_dims": self.max_dims,
            "growth_increment": self.growth_increment,
            "prune_threshold": self.prune_threshold,
            "critical_epoch": self.critical_epoch,
            "epoch": self.epoch,
            "frozen": self.frozen,
            "hebbian_lr": self.hebbian_lr,
            "mutual_information": float(self.mutual_information),
            "mi_history": [
                float(x) for x in self.mi_history[-1000:]
            ],
            "weights": self.weights.tolist(),
            "triads_noether": self.triads.noether.tolist(),
            "triads_shannon": self.triads.shannon.tolist(),
            "triads_landauer": self.triads.landauer.tolist(),
            "experts": [
                {
                    "name": e.name,
                    "domain": e.domain,
                    "specialization": e.specialization_score,
                    "weights_shape": list(e.weights.shape),
                }
                for e in self.experts
            ],
        }
        with open(path, "w") as f:
            json.dump(state, f)
        return path

    @classmethod
    def load(cls, path: str) -> TriadicManifoldNetwork:
        with open(path) as f:
            state = json.load(f)
        tmn = cls(
            init_dims=state["dims"],
            max_dims=state.get("max_dims", 96),
            growth_increment=state.get("growth_increment", 8),
            prune_threshold=state.get("prune_threshold", 0.03),
            critical_epoch=state.get("critical_epoch", 300),
        )
        tmn.epoch = state["epoch"]
        tmn.frozen = state["frozen"]
        tmn.hebbian_lr = state.get("hebbian_lr", 0.001)
        tmn.mutual_information = state.get("mutual_information", 0.0)
        tmn.mi_history = state.get("mi_history", [])
        tmn.weights = np.array(state["weights"])
        tmn.dims = tmn.weights.shape[0]
        if "triads_noether" in state:
            tmn.triads.noether = np.array(state["triads_noether"])
            tmn.triads.shannon = np.array(state["triads_shannon"])
            tmn.triads.landauer = np.array(state["triads_landauer"])
        return tmn

    def learn_from_action(
        self, action_type: str, content: str, result: str = ""
    ) -> Dict[str, Any]:
        input_str = f"{action_type}:{content[:500]}"
        output_str = result[:500] if result else content[:500]
        return self.learn(input_str, output_str)

    def query(self, content: str) -> np.ndarray:
        encoding = self.encode_code(content)
        return self.forward(encoding)
