"""
DomainAdapter — problem-description → E8 vector.

Adapted from `cqe_modules/CQE_Runner_Main_Orchestrator.py` (Phase 1
domain adaptation). Different problem types embed into the E8 vector
differently:

  - **P** (polynomial complexity) — small norm, regular structure
  - **NP** (nondeterministic) — larger norm, scattered structure
  - **optimization** (variables + constraints + objective_type) —
    encoded by problem dimensions
  - **creative** (scene/narrative complexity) — encoded by depth +
    character count
  - **text** (raw string) — SHA256 → unit-sphere fallback

Pure stdlib: 8-D vectors as tuples of floats; deterministic per input.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any


E8_DIM: int = 8


def _sha256_to_8d(payload: bytes) -> tuple[float, ...]:
    """SHA256 prefix → 8 floats in [-1, 1] (deterministic embedding)."""
    h = hashlib.sha256(payload).digest()
    vec = []
    for i in range(E8_DIM):
        byte = h[i]
        vec.append((byte / 127.5) - 1.0)
    return tuple(vec)


def _scale(v: tuple[float, ...], k: float) -> tuple[float, ...]:
    return tuple(x * k for x in v)


def _norm(v: tuple[float, ...]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _normalize(v: tuple[float, ...], target: float = 1.0) -> tuple[float, ...]:
    n = _norm(v)
    if n == 0:
        return v
    return tuple(x / n * target for x in v)


class DomainAdapter:
    """Maps problem descriptions to 8-D E8 vectors.

    Each method is deterministic for the same input. The vectors are
    NOT snapped to actual E8 roots — that's `cmplx.geometry.alena`'s
    job. This adapter produces a position that the downstream pipeline
    (parity extraction, MORSR, etc.) can work from.
    """

    name: str = "domain_adapter"

    # ── Problem-type embeddings ───────────────────────────────────────

    def embed_p_problem(
        self,
        size: int = 100,
        complexity_hint: int = 1,
    ) -> tuple[float, ...]:
        """P-class problem: small norm, regular structure.

        `size` and `complexity_hint` modulate a base sinusoidal pattern.
        Result has norm ≈ 0.5 (small).
        """
        base = []
        for i in range(E8_DIM):
            phase = 2 * math.pi * i / E8_DIM
            val = math.sin(phase * complexity_hint) * math.log1p(size) / 10.0
            base.append(val)
        return _normalize(tuple(base), target=0.5)

    def embed_np_problem(
        self,
        size: int = 100,
        nondeterminism: float = 0.8,
    ) -> tuple[float, ...]:
        """NP-class problem: larger norm, scattered.

        `nondeterminism` ∈ [0, 1] controls how much the components
        diverge from a sinusoid. Norm scales with size.
        """
        base = []
        for i in range(E8_DIM):
            phase = 2 * math.pi * i / E8_DIM
            sinusoidal = math.sin(phase) * math.log1p(size) / 5.0
            # Hash-derived perturbation
            h = hashlib.sha256(f"np:{size}:{i}".encode()).digest()
            perturbation = ((h[0] / 127.5) - 1.0) * nondeterminism
            base.append(sinusoidal + perturbation)
        return _normalize(tuple(base), target=1.5)

    def embed_optimization_problem(
        self,
        variables: int = 10,
        constraints: int = 5,
        objective_type: str = "linear",
    ) -> tuple[float, ...]:
        """Optimization: dimensions encode variables/constraints; objective
        type chooses the activation function shape."""
        v_norm = math.log1p(variables) / 5.0
        c_norm = math.log1p(constraints) / 5.0
        obj_scale = {
            "linear": 1.0,
            "quadratic": 1.5,
            "convex": 1.2,
            "nonconvex": 2.0,
        }.get(objective_type, 1.0)

        base = []
        for i in range(E8_DIM):
            if i < 4:
                base.append(v_norm * math.cos(i * math.pi / 4))
            else:
                base.append(c_norm * math.sin((i - 4) * math.pi / 4))
        return _scale(tuple(base), obj_scale)

    def embed_scene_problem(
        self,
        scene_complexity: int = 50,
        narrative_depth: int = 25,
        character_count: int = 5,
    ) -> tuple[float, ...]:
        """Creative-domain: scene + narrative + character dimensions."""
        sc = math.log1p(scene_complexity) / 5.0
        nd = math.log1p(narrative_depth) / 5.0
        cc = math.log1p(character_count) / 3.0
        return tuple([
            sc, sc * 0.7,
            nd, nd * 0.7,
            cc, cc * 0.7,
            sc * nd,
            cc * nd,
        ])

    def embed_text(self, text: str) -> tuple[float, ...]:
        """Pure text: SHA256-hashed to unit sphere then scaled to E8 range."""
        v = _sha256_to_8d(text.encode("utf-8"))
        return _normalize(v, target=math.sqrt(2))  # E8 root norm

    def hash_to_features(self, payload: str) -> tuple[float, ...]:
        """Generic JSON-payload → 8-D fallback."""
        return _sha256_to_8d(payload.encode("utf-8"))

    # ── Dispatcher ────────────────────────────────────────────────────

    def adapt(
        self,
        problem_description: dict[str, Any],
        domain_type: str = "computational",
    ) -> tuple[float, ...]:
        """Choose the right embedding for the (description, type) pair.

        - `computational` + `P` / `NP` → P/NP embedding
        - `optimization` → optimization embedding
        - `creative` → scene embedding
        - `text` → text embedding (description must have `text` key)
        - anything else → JSON-payload hash fallback
        """
        if domain_type == "computational":
            cclass = problem_description.get("complexity_class")
            if cclass == "P":
                return self.embed_p_problem(
                    problem_description.get("size", 100),
                    problem_description.get("complexity_hint", 1),
                )
            if cclass == "NP":
                return self.embed_np_problem(
                    problem_description.get("size", 100),
                    problem_description.get("nondeterminism", 0.8),
                )

        if domain_type == "optimization":
            return self.embed_optimization_problem(
                problem_description.get("variables", 10),
                problem_description.get("constraints", 5),
                problem_description.get("objective_type", "linear"),
            )

        if domain_type == "creative":
            return self.embed_scene_problem(
                problem_description.get("scene_complexity", 50),
                problem_description.get("narrative_depth", 25),
                problem_description.get("character_count", 5),
            )

        if domain_type == "text":
            text = problem_description.get("text", "")
            return self.embed_text(text)

        # Fallback: hash the whole description
        return self.hash_to_features(
            json.dumps(problem_description, sort_keys=True, default=str)
        )

    def __repr__(self) -> str:
        return "<DomainAdapter>"
