#!/usr/bin/env python3
"""
CMPLX-PartsFactory — TMN Brain Architecture

8-expert neural architecture aligned to E8 simple roots, with Hebbian gating,
3 conservation triads (Noether/Shannon/Landauer), and PG-backed persistence.

Ported from CMPLX-TMN2 personal_node.py (retooling.personal_node lineage).

Architecture:
  ExpertNode — 1 of 8 L0 experts, direction 0-7 (Cartan index), 24 dim weights
  GatingNetwork — routes inputs to experts via E8-inspired gate weights
  TMNBrain — 8 L0 experts x 24 dims (grows to max 96), 3 triads, epoch 300 freeze
  Expert domains aligned to E8 simple roots:
    geometry, computation, semantics, physics, economics, governance, integration, universal
"""

import hashlib
import json
import logging
import math
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [personal-node] %(message)s")
logger = logging.getLogger("personal-node")

COUPLING = float(os.environ.get("COUPLING", "0.030076"))
PG_URL = os.environ.get(
    "PG_URL",
    "postgresql://...:@host.docker.internal:5432/unification_hub"  # configure via PG_URL env var,
)
PHI = (1 + math.sqrt(5)) / 2
EPOCH_FREEZE = 300


# ═══════════════════════════════════════════════════════════════════════
# Expert Node — one L0 expert in the brain
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ExpertNode:
    """One of 8 L0 experts, aligned to an E8 simple root direction."""
    expert_id: str = ""
    direction: int = 0  # 0-7 (Cartan index)
    domain: str = ""
    weights: List[float] = field(default_factory=lambda: [0.0] * 24)
    activation_count: int = 0
    confidence: float = 0.0
    last_activated: float = 0.0

    def __post_init__(self):
        if not self.expert_id:
            self.expert_id = f"expert-{self.direction}"

    def activate(self, input_vector: List[float]) -> float:
        """Compute expert activation from input. Returns confidence [0,1]."""
        if len(input_vector) < len(self.weights):
            input_vector = input_vector + [0.0] * (len(self.weights) - len(input_vector))
        dot = sum(w * x for w, x in zip(self.weights, input_vector[:len(self.weights)]))
        norm_w = math.sqrt(sum(w * w for w in self.weights)) or 1e-12
        norm_x = math.sqrt(sum(x * x for x in input_vector[:len(self.weights)])) or 1e-12
        self.confidence = max(0.0, min(1.0, (dot / (norm_w * norm_x) + 1) / 2))
        self.activation_count += 1
        self.last_activated = time.time()
        return self.confidence

    def learn(self, input_vector: List[float], reward: float):
        """Hebbian update: strengthen connections that fire together."""
        lr = COUPLING * abs(reward)
        for i in range(min(len(self.weights), len(input_vector))):
            self.weights[i] += lr * input_vector[i] * reward

    def to_dict(self) -> Dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════════
# Gating Network — routes inputs to experts
# ═══════════════════════════════════════════════════════════════════════

class GatingNetwork:
    """Hebbian gating: routes inputs to the best expert by E8 proximity."""

    def __init__(self, num_experts: int = 8, dims: int = 24):
        self.num_experts = num_experts
        self.dims = dims
        self.gate_weights = [[0.0] * dims for _ in range(num_experts)]
        for i in range(min(num_experts, 8)):
            if i < 6:
                self.gate_weights[i][i] = 1.0
                self.gate_weights[i][i + 1] = -1.0
            elif i == 6:
                self.gate_weights[i][5] = 1.0
                self.gate_weights[i][6] = 1.0
            elif i == 7:
                for j in range(7):
                    self.gate_weights[i][j] = -0.5
                self.gate_weights[i][7] = 0.5

    def route(self, input_vector: List[float]) -> List[Tuple[int, float]]:
        """Route input to experts. Returns [(expert_idx, gate_score)]."""
        x = input_vector[:self.dims]
        while len(x) < self.dims:
            x.append(0.0)
        scores = []
        for i in range(self.num_experts):
            dot = sum(g * v for g, v in zip(self.gate_weights[i], x))
            scores.append((i, dot))
        scores.sort(key=lambda s: -s[1])
        return scores

    def update(self, expert_idx: int, input_vector: List[float], reward: float):
        """Update gate weights for the used expert."""
        x = input_vector[:self.dims]
        while len(x) < self.dims:
            x.append(0.0)
        lr = COUPLING * abs(reward)
        for j in range(self.dims):
            self.gate_weights[expert_idx][j] += lr * x[j] * reward


# ═══════════════════════════════════════════════════════════════════════
# TMN Brain — the agent's mind
# ═══════════════════════════════════════════════════════════════════════

EXPERT_DOMAINS = [
    "geometry",      # E8 root α₁
    "computation",   # E8 root α₂
    "semantics",     # E8 root α₃
    "physics",       # E8 root α₄
    "economics",     # E8 root α₅
    "governance",    # E8 root α₆
    "integration",   # E8 root α₇ (e₆+e₇)
    "universal",     # E8 root α₈ (half-integer)
]


@dataclass
class TMNBrain:
    """The agent's reasoning layer.

    8 L0 experts × 24 dims at start → max 96 dims.
    3 triads (Noether/Shannon/Landauer) = 3 E8 copies in Leech.
    Epoch 300: training freezes, inference only.
    """
    brain_id: str = ""
    agent_id: str = ""
    dims: int = 24
    max_dims: int = 96
    epoch: int = 0
    frozen: bool = False
    experts: List[ExpertNode] = field(default_factory=list)
    gate: Optional[GatingNetwork] = None
    triad_noether: List[float] = field(default_factory=lambda: [0.0] * 8)
    triad_shannon: List[float] = field(default_factory=lambda: [0.0] * 8)
    triad_landauer: List[float] = field(default_factory=lambda: [0.0] * 8)
    mi_history: List[float] = field(default_factory=list)
    hebbian_lr: float = COUPLING
    journal: List[Dict] = field(default_factory=list)
    glyphs: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.brain_id:
            self.brain_id = f"brain-{uuid.uuid4().hex[:8]}"
        if not self.experts:
            self.experts = [ExpertNode(direction=i, domain=EXPERT_DOMAINS[i])
                            for i in range(8)]
        if not self.gate:
            self.gate = GatingNetwork(num_experts=8, dims=self.dims)

    def think(self, input_vector: List[float]) -> Dict:
        """Process input through the brain. Returns expert activations + decision."""
        routing = self.gate.route(input_vector)
        activations = []
        for expert_idx, gate_score in routing[:3]:
            expert = self.experts[expert_idx]
            confidence = expert.activate(input_vector)
            activations.append({
                "expert": expert.domain, "direction": expert_idx,
                "gate_score": round(gate_score, 4),
                "confidence": round(confidence, 4),
            })
        x8 = input_vector[:8]
        while len(x8) < 8:
            x8.append(0.0)
        noether_score = sum(t * x for t, x in zip(self.triad_noether, x8))
        shannon_score = sum(t * x for t, x in zip(self.triad_shannon, x8))
        landauer_score = sum(t * x for t, x in zip(self.triad_landauer, x8))
        return {
            "brain_id": self.brain_id,
            "activations": activations,
            "triads": {
                "noether": round(noether_score, 6),
                "shannon": round(shannon_score, 6),
                "landauer": round(landauer_score, 6),
            },
            "dims": self.dims,
            "epoch": self.epoch,
            "frozen": self.frozen,
        }

    def learn(self, input_vector: List[float], reward: float, context: str = ""):
        """Update brain from experience. No-op if frozen."""
        if self.frozen:
            return
        routing = self.gate.route(input_vector)
        best_idx = routing[0][0]
        self.experts[best_idx].learn(input_vector, reward)
        self.gate.update(best_idx, input_vector, reward)

        x8 = input_vector[:8]
        while len(x8) < 8:
            x8.append(0.0)
        lr = self.hebbian_lr * abs(reward)
        for i in range(8):
            self.triad_noether[i] += lr * x8[i] * (1 if reward < 0 else -1)
            self.triad_shannon[i] += lr * x8[i] * abs(reward)
            self.triad_landauer[i] -= lr * x8[i] * COUPLING

        self.mi_history.append(abs(reward))
        if len(self.mi_history) > 300:
            self.mi_history = self.mi_history[-300:]

        self.journal.append({
            "ts": time.time(), "expert": self.experts[best_idx].domain,
            "reward": reward, "context": context[:100],
        })
        if len(self.journal) > 500:
            self.journal = self.journal[-500:]

    def check_epoch_gate(self) -> bool:
        """Check if brain should freeze at epoch 300."""
        if self.epoch >= EPOCH_FREEZE and not self.frozen:
            self.frozen = True
            logger.info("Brain %s frozen at epoch %d", self.brain_id, self.epoch)
            return True
        return False

    def grow_dims(self, new_dims: int):
        """Grow brain dimensions (expert spawning)."""
        if self.frozen or new_dims <= self.dims or new_dims > self.max_dims:
            return
        old = self.dims
        self.dims = new_dims
        for expert in self.experts:
            expert.weights.extend([0.0] * (new_dims - len(expert.weights)))
        self.gate = GatingNetwork(num_experts=len(self.experts), dims=new_dims)
        logger.info("Brain %s grew: %dD → %dD", self.brain_id, old, new_dims)

    def compress(self, ratio: float = 0.3) -> Dict:
        """SVD-style compression of brain weights."""
        threshold = ratio * max(abs(w) for e in self.experts for w in e.weights) if self.experts else 0
        zeroed = 0
        total = 0
        for expert in self.experts:
            for i in range(len(expert.weights)):
                total += 1
                if abs(expert.weights[i]) < threshold:
                    expert.weights[i] = 0.0
                    zeroed += 1
        return {"zeroed": zeroed, "total": total, "compression": zeroed / max(total, 1)}

    def to_image(self) -> Dict:
        """Export brain as deployable image (the brain file format)."""
        return {
            "brain_id": self.brain_id, "agent_id": self.agent_id,
            "dims": self.dims, "epoch": self.epoch, "frozen": self.frozen,
            "experts": [e.to_dict() for e in self.experts],
            "triad_noether": self.triad_noether,
            "triad_shannon": self.triad_shannon,
            "triad_landauer": self.triad_landauer,
            "mi_history": self.mi_history[-50:],
            "hebbian_lr": self.hebbian_lr,
            "glyphs": self.glyphs[:100],
            "journal_size": len(self.journal),
        }


# ═══════════════════════════════════════════════════════════════════════
# PG + State Management
# ═══════════════════════════════════════════════════════════════════════

_pg_conn = None


def _get_pg():
    global _pg_conn
    if not PG_URL:
        return None
    try:
        if _pg_conn is None or _pg_conn.closed:
            _pg_conn = psycopg2.connect(PG_URL)
            _pg_conn.autocommit = True
        return _pg_conn
    except Exception:
        return None


_brains: Dict[str, TMNBrain] = {}


def init_tables():
    """Ensure tmn_brains table exists in Postgres."""
    conn = _get_pg()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS tmn_brains (
            brain_id TEXT PRIMARY KEY, agent_id TEXT, dims INT DEFAULT 24,
            epoch INT DEFAULT 0, frozen BOOLEAN DEFAULT FALSE,
            image JSONB DEFAULT '{}', created_at DOUBLE PRECISION,
            updated_at DOUBLE PRECISION)""")
    except Exception:
        pass


def save_brain(brain: TMNBrain):
    """Persist a brain snapshot to Postgres."""
    conn = _get_pg()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""INSERT INTO tmn_brains (brain_id, agent_id, dims, epoch, frozen, image, created_at, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (brain_id) DO UPDATE SET
            dims=EXCLUDED.dims, epoch=EXCLUDED.epoch, frozen=EXCLUDED.frozen,
            image=EXCLUDED.image, updated_at=EXCLUDED.updated_at""",
            (brain.brain_id, brain.agent_id, brain.dims, brain.epoch, brain.frozen,
             json.dumps(brain.to_image()),
             brain.journal[0]["ts"] if brain.journal else time.time(),
             time.time()))
    except Exception as e:
        logger.warning("PG save brain: %s", e)


def load_brain(brain_id: str) -> Optional[TMNBrain]:
    """Load a brain from Postgres by ID. Returns None if not found."""
    conn = _get_pg()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT image FROM tmn_brains WHERE brain_id = %s", (brain_id,))
        row = cur.fetchone()
        if not row:
            return None
        data = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        brain = TMNBrain(brain_id=brain_id)
        brain.agent_id = data.get("agent_id", "")
        brain.dims = data.get("dims", 24)
        brain.epoch = data.get("epoch", 0)
        brain.frozen = data.get("frozen", False)
        brain.gate = GatingNetwork(num_experts=8, dims=brain.dims)
        brain.triad_noether = data.get("triad_noether", [0.0] * 8)
        brain.triad_shannon = data.get("triad_shannon", [0.0] * 8)
        brain.triad_landauer = data.get("triad_landauer", [0.0] * 8)
        brain.hebbian_lr = data.get("hebbian_lr", COUPLING)
        brain.glyphs = data.get("glyphs", [])
        experts_data = data.get("experts", [])
        if experts_data:
            brain.experts = []
            for ed in experts_data:
                expert = ExpertNode(
                    expert_id=ed.get("expert_id", ""),
                    direction=ed.get("direction", 0),
                    domain=ed.get("domain", ""),
                    weights=ed.get("weights", [0.0] * brain.dims),
                    activation_count=ed.get("activation_count", 0),
                    confidence=ed.get("confidence", 0.0),
                    last_activated=ed.get("last_activated", 0.0),
                )
                brain.experts.append(expert)
        return brain
    except Exception as e:
        logger.warning("PG load brain: %s", e)
        return None
