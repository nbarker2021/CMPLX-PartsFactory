"""
Unified composed-E8 brain core.

This is the current CMPLX PartsFactory brain product surface, adapted from the
prior Manny unified brain assembly. It keeps the useful local behavior as a
library module: 8-D experts compose into 24-D lattice slices, four slices form
the 96-D manifold view, and learning preserves a serializable brain image.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from ._constants import (
    ALPHA_BY_TIER,
    CONTROL_EXPERTS,
    DEFAULT_DOMAINS,
    FREEZE_EPOCH,
    LATTICE_ROLES,
    PHI,
    TIER_THRESHOLDS,
    TMN_MAX_DIMS,
    TOP_K,
)


def label_signature(labels: Sequence[str]) -> str:
    """Return a stable short signature for a label set."""
    normalized = sorted(str(label) for label in labels)
    raw = json.dumps(normalized, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _as_vector(values: Sequence[float] | np.ndarray, dims: int = 8) -> np.ndarray:
    """Return a finite vector with exactly dims entries."""
    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size < dims:
        arr = np.pad(arr, (0, dims - arr.size))
    if arr.size > dims:
        arr = arr[:dims]
    return np.nan_to_num(arr, nan=0.0, posinf=1.0, neginf=-1.0)


def _chunks(values: Sequence[float] | np.ndarray, *, chunk_size: int) -> list[np.ndarray]:
    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size % chunk_size:
        arr = np.pad(arr, (0, chunk_size - (arr.size % chunk_size)))
    return [_as_vector(arr[i:i + chunk_size]) for i in range(0, arr.size, chunk_size)]


def vector_from_payload(payload: Mapping[str, Any] | str, dims: int = 8) -> np.ndarray:
    """Create a stable numeric vector from arbitrary payload evidence."""
    if isinstance(payload, str):
        raw = payload
    else:
        raw = json.dumps(payload, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    vals = []
    for i in range(dims):
        pair = digest[(i * 2) % len(digest): (i * 2 + 2) % len(digest)]
        if len(pair) < 2:
            pair += digest[: 2 - len(pair)]
        val = int.from_bytes(pair, "big") / 65535.0
        vals.append((val * 2.0) - 1.0)
    return np.asarray(vals, dtype=float)


def _e8_simple_roots() -> np.ndarray:
    """Return a deterministic 8-root basis used by historical brain builds."""
    roots = np.zeros((8, 8), dtype=float)
    for i in range(7):
        roots[i, i] = 1.0
        roots[i, i + 1] = -1.0
    roots[7, :] = 0.5
    return roots


E8_ROOTS = _e8_simple_roots()


@dataclass
class Expert:
    """A single 8-D expert node with local learning statistics."""

    expert_id: str
    domain: str
    e8_position: np.ndarray
    weights: np.ndarray
    expert_type: str = "domain"
    activation_count: int = 0
    use_count: int = 0
    avg_reward: float = 0.0
    confidence: float = 0.5
    parent_ids: tuple[str, ...] = ()
    co_activations: dict[str, int] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    model_path: str | None = None

    @classmethod
    def new(
        cls,
        expert_id: str,
        domain: str,
        e8_position: Sequence[float] | np.ndarray,
        *,
        expert_type: str = "domain",
        parent_ids: Iterable[str] = (),
    ) -> "Expert":
        position = _as_vector(e8_position)
        seed = int.from_bytes(
            hashlib.sha256(f"{expert_id}:{domain}".encode("utf-8")).digest()[:8],
            "big",
        )
        rng = np.random.default_rng(seed)
        weights = position + rng.normal(0.0, 0.05, size=8)
        return cls(
            expert_id=expert_id,
            domain=domain,
            e8_position=position,
            weights=_as_vector(weights),
            expert_type=expert_type,
            parent_ids=tuple(parent_ids),
        )

    def activate(self, input_vector: Sequence[float] | np.ndarray) -> float:
        vector = _as_vector(input_vector)
        denom = float(np.linalg.norm(vector) * np.linalg.norm(self.weights))
        similarity = 0.0 if denom == 0.0 else float(np.dot(vector, self.weights) / denom)
        distance = float(np.linalg.norm(vector - self.e8_position))
        proximity = 1.0 / (1.0 + distance)
        score = (0.7 * similarity + 0.3 * proximity) * self.confidence
        self.activation_count += 1
        return float(score)

    def learn(
        self,
        input_vector: Sequence[float] | np.ndarray,
        reward: float,
        alpha: float,
    ) -> None:
        vector = _as_vector(input_vector)
        bounded_reward = float(max(-1.0, min(1.0, reward)))
        self.weights = _as_vector((1.0 - alpha) * self.weights + alpha * bounded_reward * vector)
        self.use_count += 1
        self.avg_reward += (bounded_reward - self.avg_reward) / max(1, self.use_count)
        self.confidence = float(max(0.05, min(1.0, 0.5 + self.avg_reward / 2.0)))

    def co_activate_with(self, other_id: str) -> None:
        self.co_activations[other_id] = self.co_activations.get(other_id, 0) + 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "expert_id": self.expert_id,
            "domain": self.domain,
            "e8_position": self.e8_position.tolist(),
            "weights": self.weights.tolist(),
            "expert_type": self.expert_type,
            "activation_count": self.activation_count,
            "use_count": self.use_count,
            "avg_reward": self.avg_reward,
            "confidence": self.confidence,
            "parent_ids": list(self.parent_ids),
            "co_activations": dict(self.co_activations),
            "created_at": self.created_at,
            "model_path": self.model_path,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Expert":
        return cls(
            expert_id=str(data["expert_id"]),
            domain=str(data.get("domain") or "unknown"),
            e8_position=_as_vector(data.get("e8_position") or ()),
            weights=_as_vector(data.get("weights") or ()),
            expert_type=str(data.get("expert_type") or "domain"),
            activation_count=int(data.get("activation_count") or 0),
            use_count=int(data.get("use_count") or 0),
            avg_reward=float(data.get("avg_reward") or 0.0),
            confidence=float(data.get("confidence", 0.5)),
            parent_ids=tuple(data.get("parent_ids") or ()),
            co_activations=dict(data.get("co_activations") or {}),
            created_at=float(data.get("created_at") or time.time()),
            model_path=data.get("model_path"),
        )


@dataclass
class Triad:
    """Noether/Shannon/Landauer style triad over an 8-D vector."""

    name: str
    weights: np.ndarray

    @classmethod
    def new(cls, name: str) -> "Triad":
        return cls(name=name, weights=np.ones(8, dtype=float) / 8.0)

    def activate(self, input_vector: Sequence[float] | np.ndarray) -> float:
        vector = _as_vector(input_vector)
        return float(np.dot(vector, self.weights))

    def update(
        self,
        input_vector: Sequence[float] | np.ndarray,
        reward: float,
        alpha: float,
    ) -> None:
        vector = _as_vector(input_vector)
        self.weights = _as_vector((1.0 - alpha) * self.weights + alpha * reward * vector)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "weights": self.weights.tolist()}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Triad":
        return cls(name=str(data["name"]), weights=_as_vector(data.get("weights") or ()))


@dataclass
class GatingNetwork:
    """Top-k gate with a tiny Hebbian matrix."""

    n_experts: int
    gate_weights: np.ndarray = field(default_factory=lambda: np.zeros((0, 0), dtype=float))
    hebbian_lr: float = 0.03

    def __post_init__(self) -> None:
        if self.gate_weights.shape != (self.n_experts, self.n_experts):
            self.gate_weights = np.eye(self.n_experts, dtype=float)

    def gate(self, scores: Sequence[float], top_k: int = TOP_K) -> list[int]:
        if self.n_experts <= 0:
            return []
        vec = np.asarray(list(scores), dtype=float).reshape(-1)
        if vec.size < self.n_experts:
            vec = np.pad(vec, (0, self.n_experts - vec.size))
        if vec.size > self.n_experts:
            vec = vec[: self.n_experts]
        mixed = vec @ self.gate_weights
        k = max(1, min(top_k, self.n_experts))
        return [int(i) for i in np.argsort(mixed)[-k:][::-1]]

    def top_k(self, scores: Sequence[float], k: int = TOP_K) -> list[int]:
        return self.gate(scores, top_k=k)

    def hebbian_update(self, selected: Sequence[int], reward: float) -> None:
        bounded_reward = float(max(-1.0, min(1.0, reward)))
        for i in selected:
            for j in selected:
                if i != j and i < self.n_experts and j < self.n_experts:
                    self.gate_weights[i, j] += self.hebbian_lr * bounded_reward

    def resize(self, n_experts: int) -> None:
        old = self.gate_weights
        self.n_experts = n_experts
        new = np.eye(n_experts, dtype=float)
        limit = min(old.shape[0], n_experts)
        if limit:
            new[:limit, :limit] = old[:limit, :limit]
        self.gate_weights = new

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_experts": self.n_experts,
            "gate_weights": self.gate_weights.tolist(),
            "hebbian_lr": self.hebbian_lr,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GatingNetwork":
        return cls(
            n_experts=int(data.get("n_experts") or 0),
            gate_weights=np.asarray(data.get("gate_weights") or [], dtype=float),
            hebbian_lr=float(data.get("hebbian_lr", 0.03)),
        )


@dataclass
class LatticeSlice:
    """A 24-D lattice slice composed from exactly three E8 experts."""

    role: str
    experts: list[Expert]

    def __post_init__(self) -> None:
        padded = list(self.experts[:3])
        while len(padded) < 3:
            padded.append(
                Expert.new(
                    f"{self.role.lower()}_zero_{len(padded)}",
                    "zero",
                    np.zeros(8),
                )
            )
        self.experts = padded

    def compose(self) -> np.ndarray:
        return np.concatenate([expert.weights for expert in self.experts])

    def decompose_input(self, input_vector: Sequence[float] | np.ndarray) -> list[np.ndarray]:
        vector = np.asarray(input_vector, dtype=float).reshape(-1)
        if vector.size < 24:
            vector = np.pad(vector, (0, 24 - vector.size))
        return [_as_vector(vector[i * 8: (i + 1) * 8]) for i in range(3)]

    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role, "experts": [expert.expert_id for expert in self.experts]}


@dataclass
class BrainState:
    """Serializable brain image."""

    agent_id: str
    experts: list[dict[str, Any]]
    triads: list[dict[str, Any]]
    gate: dict[str, Any]
    epoch: int = 0
    tier: str = "nascent"
    frozen: bool = False
    contribution_points: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrainObservation:
    """Personal-node style memory row attached to a brain image."""

    datum_id: str
    label_sig: str
    mdhg_address: str = ""
    accepted: bool = True
    delta_phi: float = 0.0
    boundary_type: str = "default"
    deception_severity: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "datum_id": self.datum_id,
            "label_sig": self.label_sig,
            "mdhg_address": self.mdhg_address,
            "accepted": self.accepted,
            "delta_phi": self.delta_phi,
            "boundary_type": self.boundary_type,
            "deception_severity": self.deception_severity,
            "timestamp": self.timestamp,
        }


@dataclass
class BrainContribution:
    """Contribution row from the prior global brain service."""

    agent_id: str
    domain: str = ""
    snap_labels: list[str] = field(default_factory=list)
    mi_score: float = 0.0
    epoch: int = 0
    tier: str = "nascent"
    dims: int = 24
    contributed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "snap_labels": list(self.snap_labels),
            "mi_score": self.mi_score,
            "epoch": self.epoch,
            "tier": self.tier,
            "dims": self.dims,
            "contributed_at": self.contributed_at,
        }


class Brain:
    """Composed-E8 brain image with organic expert growth."""

    def __init__(
        self,
        agent_id: str,
        experts: Iterable[Expert] = (),
        triads: Iterable[Triad] = (),
        *,
        tier: str = "nascent",
        epoch: int = 0,
        frozen: bool = False,
        contribution_points: float = 0.0,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.experts = list(experts)
        self.triads = list(triads) or [
            Triad.new("Noether"),
            Triad.new("Shannon"),
            Triad.new("Landauer"),
        ]
        self.gate = GatingNetwork(len(self.experts))
        self.epoch = epoch
        self.tier = tier
        self.frozen = frozen
        self.contribution_points = float(contribution_points)
        self.metadata = dict(metadata or {})
        self.metadata.setdefault("observations", [])
        self.metadata.setdefault("contributions", [])

    def compose_lattices(self) -> list[LatticeSlice]:
        slices: list[LatticeSlice] = []
        if not self.experts:
            return slices
        for role_index, role in enumerate(LATTICE_ROLES):
            start = role_index * 3
            group = self.experts[start:start + 3]
            if not group:
                group = self.experts[-3:]
            slices.append(LatticeSlice(role=role, experts=list(group)))
        return slices

    def manifold(self) -> np.ndarray:
        slices = self.compose_lattices()
        if not slices:
            return np.zeros(TMN_MAX_DIMS, dtype=float)
        vector = np.concatenate([slice_.compose() for slice_ in slices])
        if vector.size < TMN_MAX_DIMS:
            vector = np.pad(vector, (0, TMN_MAX_DIMS - vector.size))
        return vector[:TMN_MAX_DIMS]

    def add_expert(self, expert: Expert) -> None:
        self.experts.append(expert)
        self.gate.resize(len(self.experts))

    def expertise(
        self,
        *,
        domain: str = "",
        min_confidence: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Return the expert topology as a routeable capability table."""
        rows = []
        for index, expert in enumerate(self.experts):
            if domain and expert.domain != domain:
                continue
            if expert.confidence < min_confidence:
                continue
            rows.append(
                {
                    "index": index,
                    "expert_id": expert.expert_id,
                    "domain": expert.domain,
                    "expert_type": expert.expert_type,
                    "confidence": expert.confidence,
                    "avg_reward": expert.avg_reward,
                    "use_count": expert.use_count,
                    "activation_count": expert.activation_count,
                    "parents": list(expert.parent_ids),
                }
            )
        return sorted(
            rows,
            key=lambda row: (row["confidence"], row["avg_reward"], row["use_count"]),
            reverse=True,
        )

    def try_spawn(self, domain: str, parents: Sequence[str] = ()) -> Expert:
        root = E8_ROOTS[len(self.experts) % len(E8_ROOTS)]
        position = root * (PHI ** (len(self.experts) % 5))
        expert = Expert.new(
            f"{self.agent_id}:{domain}:{len(self.experts)}",
            domain,
            position,
            parent_ids=parents,
        )
        self.add_expert(expert)
        return expert

    def think(
        self,
        input_vector: Sequence[float] | np.ndarray,
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        vector = _as_vector(input_vector)
        confidences = [expert.activate(vector) for expert in self.experts]
        norms = [float(np.linalg.norm(expert.weights)) for expert in self.experts]
        routed_scores = [confidence * (1.0 + norm) for confidence, norm in zip(confidences, norms)]
        selected = self.gate.top_k(routed_scores, k=top_k)
        triad_scores = {triad.name: triad.activate(vector) for triad in self.triads}
        return {
            "agent_id": self.agent_id,
            "selected": selected,
            "experts": [self.experts[i].expert_id for i in selected],
            "scores": [confidences[i] for i in selected],
            "triads": triad_scores,
            "tier": self.tier,
            "epoch": self.epoch,
            "frozen": self.frozen,
        }

    def learn(
        self,
        input_vector: Sequence[float] | np.ndarray,
        reward: float,
        *,
        context: str = "",
        domain: str | None = None,
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        result = self.think(input_vector, top_k=top_k)
        if self.frozen:
            result["learned"] = False
            result["reason"] = "frozen"
            return result
        vector = _as_vector(input_vector)
        alpha = self.alpha()
        selected = result["selected"]
        for i in selected:
            self.experts[i].learn(vector, reward, alpha)
        for left in selected:
            for right in selected:
                if left != right:
                    self.experts[left].co_activate_with(self.experts[right].expert_id)
        for triad in self.triads:
            triad.update(vector, reward, alpha / 2.0)
        self.gate.hebbian_update(selected, reward)
        self.epoch += 1
        if domain and len(self.experts) < 24 and reward > 0.75 and self.epoch % 7 == 0:
            self.try_spawn(domain=domain, parents=[self.experts[i].expert_id for i in selected])
        self.record_contribution(max(0.0, reward), context=context)
        self.try_advance_tier()
        self._maybe_freeze()
        result["learned"] = True
        result["alpha"] = alpha
        result["tier"] = self.tier
        result["epoch"] = self.epoch
        return result

    def think_lattice(
        self,
        lattice_vector: Sequence[float] | np.ndarray,
        *,
        role: str,
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        """Route a 24-D lattice slice through the 8-D expert population."""
        parts = _chunks(lattice_vector, chunk_size=8)[:3]
        return {
            "role": role,
            "parts": [
                {"part": index, **self.think(part, top_k=top_k)}
                for index, part in enumerate(parts)
            ],
        }

    def learn_lattice(
        self,
        lattice_vector: Sequence[float] | np.ndarray,
        *,
        role: str,
        reward: float,
        context: str = "",
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        """Train from one 24-D SELF/MEMORY/BODY/ATTENTION lattice."""
        parts = _chunks(lattice_vector, chunk_size=8)[:3]
        results = []
        for index, part in enumerate(parts):
            results.append(
                self.learn(
                    part,
                    reward,
                    context=f"{context}:{role}:{index}" if context else f"{role}:{index}",
                    domain=role.lower(),
                    top_k=top_k,
                )
            )
        return {"role": role, "parts": results, "epoch": self.epoch}

    def think_manifold(
        self,
        manifold_vector: Sequence[float] | np.ndarray,
        *,
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        """Route a 96-D four-lattice manifold through the brain."""
        vector = np.asarray(manifold_vector, dtype=float).reshape(-1)
        if vector.size < TMN_MAX_DIMS:
            vector = np.pad(vector, (0, TMN_MAX_DIMS - vector.size))
        role_results = {}
        for index, role in enumerate(LATTICE_ROLES):
            start = index * 24
            role_results[role] = self.think_lattice(
                vector[start:start + 24],
                role=role,
                top_k=top_k,
            )
        return {
            "agent_id": self.agent_id,
            "roles": role_results,
            "tier": self.tier,
            "epoch": self.epoch,
        }

    def learn_manifold(
        self,
        manifold_vector: Sequence[float] | np.ndarray,
        *,
        reward: float,
        context: str = "",
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        """Train from a 96-D SELF/MEMORY/BODY/ATTENTION manifold."""
        vector = np.asarray(manifold_vector, dtype=float).reshape(-1)
        if vector.size < TMN_MAX_DIMS:
            vector = np.pad(vector, (0, TMN_MAX_DIMS - vector.size))
        role_results = {}
        for index, role in enumerate(LATTICE_ROLES):
            start = index * 24
            role_results[role] = self.learn_lattice(
                vector[start:start + 24],
                role=role,
                reward=reward,
                context=context,
                top_k=top_k,
            )
        return {
            "agent_id": self.agent_id,
            "roles": role_results,
            "epoch": self.epoch,
            "learned": not self.frozen,
        }

    def _maybe_freeze(self) -> None:
        if self.epoch >= FREEZE_EPOCH and self.tier == "architect":
            self.frozen = True

    def is_frozen(self) -> bool:
        return self.frozen

    def freeze(self) -> None:
        self.frozen = True

    def try_advance_tier(self) -> str:
        current = self.tier
        for tier, threshold in TIER_THRESHOLDS.items():
            if self.contribution_points >= threshold:
                current = tier
        self.tier = current
        return current

    def alpha(self) -> float:
        return ALPHA_BY_TIER.get(self.tier, ALPHA_BY_TIER["nascent"])

    def record_contribution(self, points: float, *, context: str = "") -> None:
        self.contribution_points += float(points)
        if context:
            self.metadata.setdefault("contexts", []).append(
                {"epoch": self.epoch, "context": context, "points": points}
            )

    def contribute(
        self,
        *,
        domain: str = "",
        snap_labels: Sequence[str] = (),
        mi_score: float = 0.0,
    ) -> BrainContribution:
        """Record a domain/SNAP contribution for later routing and merging."""
        contribution = BrainContribution(
            agent_id=self.agent_id,
            domain=domain,
            snap_labels=list(snap_labels),
            mi_score=float(mi_score),
            epoch=self.epoch,
            tier=self.tier,
            dims=TMN_MAX_DIMS,
        )
        self.metadata.setdefault("contributions", []).append(contribution.to_dict())
        self.record_contribution(max(0.0, mi_score), context=f"contribution:{domain}")
        return contribution

    def record_observation(
        self,
        *,
        datum_id: str,
        labels: Sequence[str],
        mdhg_address: str = "",
        accepted: bool = True,
        delta_phi: float = 0.0,
        boundary_type: str = "default",
        deception_severity: float = 0.0,
    ) -> BrainObservation:
        """Record personal-node style label/address memory."""
        observation = BrainObservation(
            datum_id=datum_id,
            label_sig=label_signature(labels),
            mdhg_address=mdhg_address,
            accepted=accepted,
            delta_phi=float(delta_phi),
            boundary_type=boundary_type,
            deception_severity=float(deception_severity),
        )
        observations = self.metadata.setdefault("observations", [])
        observations.append(observation.to_dict())
        if len(observations) > 500:
            del observations[:-500]
        return observation

    def specialist_profile(self) -> dict[str, float]:
        """Summarize domain knowledge from contributions and experts."""
        profile: dict[str, float] = {}
        for expert in self.experts:
            profile[expert.domain] = max(
                profile.get(expert.domain, 0.0),
                float(expert.confidence),
            )
        for row in self.metadata.get("contributions", []):
            domain = str(row.get("domain") or "")
            if not domain:
                continue
            profile[domain] = max(profile.get(domain, 0.0), float(row.get("mi_score") or 0.0))
        return dict(sorted(profile.items(), key=lambda item: item[1], reverse=True))

    def capacity_score(
        self,
        *,
        mi_history: Sequence[float] | None = None,
        weight_density: float | None = None,
        step_count: int | None = None,
    ) -> dict[str, Any]:
        """Score saturation using the prior brain-service capacity formula."""
        if mi_history is None:
            mi_history = [
                float(row.get("mi_score") or 0.0)
                for row in self.metadata.get("contributions", [])
            ]
        mi_flat = 0.0
        if len(mi_history) >= 10:
            recent = list(mi_history)[-10:]
            xs = list(range(len(recent)))
            mean_x = sum(xs) / len(xs)
            mean_y = sum(recent) / len(recent)
            num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, recent))
            den = sum((x - mean_x) ** 2 for x in xs)
            slope = num / den if den > 0 else 0.0
            mi_flat = 1.0 - min(abs(slope) / 0.005, 1.0) if slope <= 0.005 else 0.0
        if weight_density is None:
            weights = [abs(float(w)) for expert in self.experts for w in expert.weights]
            nonzero = sum(1 for weight in weights if weight > 1e-12)
            weight_density = nonzero / max(len(weights), 1)
        if step_count is None:
            step_count = self.epoch
        density = min(float(weight_density), 1.0)
        step_proxy = min(float(step_count) / 8000.0, 1.0)
        score = max(0.0, min(1.0, 0.45 * mi_flat + 0.30 * density + 0.25 * step_proxy))
        return {
            "capacity_score": round(score, 4),
            "mi_flat": round(mi_flat, 4),
            "density": round(density, 4),
            "step_proxy": round(step_proxy, 4),
            "saturated": score >= 0.75,
            "recommendation": "reinit" if score >= 0.75 else "continue",
        }

    def capacity(self) -> dict[str, Any]:
        return {
            "experts": len(self.experts),
            "max_experts": 24,
            "epoch": self.epoch,
            "tier": self.tier,
            "frozen": self.frozen,
            "manifold_dims": int(self.manifold().size),
            "domains": sorted({expert.domain for expert in self.experts}),
            "specialist_profile": self.specialist_profile(),
            "capacity_score": self.capacity_score(),
        }

    def conservation_step(self) -> dict[str, float]:
        if not self.experts:
            return {"weight_norm": 0.0, "gate_norm": 0.0, "triad_norm": 0.0}
        return {
            "weight_norm": float(sum(np.linalg.norm(expert.weights) for expert in self.experts)),
            "gate_norm": float(np.linalg.norm(self.gate.gate_weights)),
            "triad_norm": float(sum(np.linalg.norm(triad.weights) for triad in self.triads)),
        }

    def compress(self, ratio: float = 0.3) -> dict[str, Any]:
        """Zero small weights and return a compactness receipt."""
        weights = [abs(float(w)) for expert in self.experts for w in expert.weights]
        threshold = (max(weights) * ratio) if weights else 0.0
        zeroed = 0
        total = 0
        for expert in self.experts:
            updated = expert.weights.copy()
            for index, weight in enumerate(updated):
                total += 1
                if abs(float(weight)) < threshold:
                    updated[index] = 0.0
                    zeroed += 1
            expert.weights = _as_vector(updated)
        receipt = {
            "zeroed": zeroed,
            "total": total,
            "compression": zeroed / max(total, 1),
            "threshold": threshold,
        }
        self.metadata.setdefault("compression", []).append(
            {"epoch": self.epoch, **receipt}
        )
        return receipt

    def fork(self, child_agent_id: str, *, domain_boost: str = "") -> "Brain":
        """Create a child brain image without sharing mutable arrays."""
        state = copy.deepcopy(self.to_image())
        state["agent_id"] = child_agent_id
        state.setdefault("metadata", {})
        state["metadata"]["forked_from"] = self.agent_id
        state["metadata"]["fork_epoch"] = self.epoch
        child = Brain.from_image(state)
        for expert in child.experts:
            expert.expert_id = expert.expert_id.replace(self.agent_id, child_agent_id, 1)
        if domain_boost:
            child.try_spawn(
                domain_boost,
                parents=[expert.expert_id for expert in child.experts[:3]],
            )
        return child

    def merge(self, other: "Brain", *, weight: float = 0.5) -> dict[str, Any]:
        """Blend another brain image into this one by domain and type."""
        blend = float(max(0.0, min(1.0, weight)))
        by_key = {(expert.domain, expert.expert_type): expert for expert in self.experts}
        merged = 0
        imported = 0
        for incoming in other.experts:
            key = (incoming.domain, incoming.expert_type)
            current = by_key.get(key)
            if current is None:
                clone = Expert.from_dict(incoming.to_dict())
                clone.expert_id = f"{self.agent_id}:{clone.domain}:{len(self.experts)}"
                clone.parent_ids = tuple({*clone.parent_ids, incoming.expert_id})
                self.add_expert(clone)
                by_key[key] = clone
                imported += 1
                continue
            current.weights = _as_vector(
                (1.0 - blend) * current.weights + blend * incoming.weights
            )
            current.e8_position = _as_vector(
                (1.0 - blend) * current.e8_position + blend * incoming.e8_position
            )
            current.confidence = (1.0 - blend) * current.confidence + blend * incoming.confidence
            current.avg_reward = (1.0 - blend) * current.avg_reward + blend * incoming.avg_reward
            current.use_count += incoming.use_count
            current.activation_count += incoming.activation_count
            merged += 1
        self.gate.resize(len(self.experts))
        self.metadata.setdefault("merged_from", []).append(
            {
                "agent_id": other.agent_id,
                "epoch": other.epoch,
                "weight": blend,
                "merged": merged,
                "imported": imported,
            }
        )
        return {"merged": merged, "imported": imported, "total": len(self.experts)}

    def to_state(self) -> BrainState:
        return BrainState(
            agent_id=self.agent_id,
            experts=[expert.to_dict() for expert in self.experts],
            triads=[triad.to_dict() for triad in self.triads],
            gate=self.gate.to_dict(),
            epoch=self.epoch,
            tier=self.tier,
            frozen=self.frozen,
            contribution_points=self.contribution_points,
            metadata=dict(self.metadata),
        )

    def to_image(self) -> dict[str, Any]:
        """Export the product-level brain image format."""
        state = self.to_state()
        return {
            "schema": "cmplx.cognition.brain.image.v1",
            "agent_id": state.agent_id,
            "experts": state.experts,
            "triads": state.triads,
            "gate": state.gate,
            "epoch": state.epoch,
            "tier": state.tier,
            "frozen": state.frozen,
            "contribution_points": state.contribution_points,
            "metadata": state.metadata,
            "capacity": self.capacity(),
            "conservation": self.conservation_step(),
        }

    @classmethod
    def from_state(cls, state: BrainState | Mapping[str, Any]) -> "Brain":
        if isinstance(state, Mapping):
            state = BrainState(
                agent_id=str(state["agent_id"]),
                experts=list(state.get("experts") or []),
                triads=list(state.get("triads") or []),
                gate=dict(state.get("gate") or {}),
                epoch=int(state.get("epoch") or 0),
                tier=str(state.get("tier") or "nascent"),
                frozen=bool(state.get("frozen") or False),
                contribution_points=float(state.get("contribution_points") or 0.0),
                metadata=dict(state.get("metadata") or {}),
            )
        brain = cls(
            agent_id=state.agent_id,
            experts=[Expert.from_dict(expert) for expert in state.experts],
            triads=[Triad.from_dict(triad) for triad in state.triads],
            tier=state.tier,
            epoch=state.epoch,
            frozen=state.frozen,
            contribution_points=state.contribution_points,
            metadata=state.metadata,
        )
        brain.gate = GatingNetwork.from_dict(state.gate)
        if brain.gate.n_experts != len(brain.experts):
            brain.gate.resize(len(brain.experts))
        return brain

    @classmethod
    def from_image(cls, image: Mapping[str, Any]) -> "Brain":
        """Load a brain from a product image or raw BrainState mapping."""
        state = {
            "agent_id": image["agent_id"],
            "experts": list(image.get("experts") or []),
            "triads": list(image.get("triads") or []),
            "gate": dict(image.get("gate") or {}),
            "epoch": int(image.get("epoch") or 0),
            "tier": str(image.get("tier") or "nascent"),
            "frozen": bool(image.get("frozen") or False),
            "contribution_points": float(image.get("contribution_points") or 0.0),
            "metadata": dict(image.get("metadata") or {}),
        }
        return cls.from_state(state)


def default_population_e8_positions() -> list[np.ndarray]:
    positions = [root.copy() for root in E8_ROOTS]
    positions.extend(
        [
            E8_ROOTS[0] + E8_ROOTS[1],
            E8_ROOTS[2] + E8_ROOTS[3],
            E8_ROOTS[4] + E8_ROOTS[5],
        ]
    )
    return positions


def make_default_brain(agent_id: str = "manny") -> Brain:
    positions = default_population_e8_positions()
    experts: list[Expert] = []
    for domain, position in zip(DEFAULT_DOMAINS, positions):
        experts.append(Expert.new(f"{agent_id}:{domain}", domain, position))
    for name, position in zip(CONTROL_EXPERTS, positions[len(experts):]):
        experts.append(Expert.new(f"{agent_id}:{name}", name, position, expert_type="control"))
    return Brain(agent_id=agent_id, experts=experts)


__all__ = [
    "Brain",
    "BrainContribution",
    "BrainObservation",
    "BrainState",
    "E8_ROOTS",
    "Expert",
    "GatingNetwork",
    "LatticeSlice",
    "Triad",
    "default_population_e8_positions",
    "label_signature",
    "make_default_brain",
    "vector_from_payload",
]
