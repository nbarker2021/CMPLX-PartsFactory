"""Gate369 Service — Epoch gating, tier locks, rate limiting, quality gating.

Port of TMN2 gate.py core logic. Integrates with GeometricGovernance for
invariant validation and boundary event recording.

Gate types: conservation (dphi>0), epoch (tick boundary), tier (capability locked),
            rate (too many ops/sec), quality (below threshold).
"""
from __future__ import annotations
import hashlib
import time
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("services.gate")

GATE_INTERVAL = 300
CAPACITY_THRESHOLD = 0.75
GROWTH_INCREMENT = 8
MAX_DIMS = 96
ALPHA = {"nascent": 0.30, "apprentice": 0.40, "journeyman": 0.50, "master": 0.60, "architect": 0.70}
RATE_LIMIT_PER_SEC = 50
QUALITY_THRESHOLD = 0.3

TIER_LOCKS: Dict[str, str] = {
    "spawn_child": "apprentice",
    "merge_brain": "journeyman",
    "federated_contribute": "journeyman",
    "create_coin": "master",
    "modify_daemon": "architect",
    "epoch_gate": "nascent",
    "board_post": "nascent",
    "bond_create": "apprentice",
}
TIER_ORDER = ["nascent", "apprentice", "journeyman", "master", "architect"]

GATE_RULES = [
    {"type": "conservation", "description": "ΔΦ must be ≤ 0 (conservation law)", "severity": "hard"},
    {"type": "epoch", "description": "Agent tick_count % 300 triggers epoch advancement", "severity": "soft"},
    {"type": "tier", "description": "Operation requires minimum tier level", "severity": "hard"},
    {"type": "rate", "description": f"Max {RATE_LIMIT_PER_SEC} operations/second per agent", "severity": "soft"},
    {"type": "quality", "description": f"Quality score must be ≥ {QUALITY_THRESHOLD}", "severity": "soft"},
]


class GateCheckResult:
    def __init__(self, gated: bool, reason: str, gate_type: str, check_id: str = "",
                 epoch_due: bool = False, saturated: bool = False,
                 should_advance: bool = False, current_dims: int = 24,
                 new_dims: int = 24, growth: int = 0, alpha: float = 0.30,
                 tier: str = "nascent", actions: list[str] | None = None):
        self.gated = gated
        self.reason = reason
        self.gate_type = gate_type
        self.check_id = check_id
        self.epoch_due = epoch_due
        self.saturated = saturated
        self.should_advance = should_advance
        self.current_dims = current_dims
        self.new_dims = new_dims
        self.growth = growth
        self.alpha = alpha
        self.tier = tier
        self.actions = actions or []

    def to_dict(self) -> dict:
        return {
            "gated": self.gated, "reason": self.reason, "gate_type": self.gate_type,
            "check_id": self.check_id, "epoch_due": self.epoch_due,
            "saturated": self.saturated, "should_advance": self.should_advance,
            "current_dims": self.current_dims, "new_dims": self.new_dims,
            "growth": self.growth, "alpha": self.alpha, "tier": self.tier,
            "actions": self.actions,
        }


class GateService:
    """Core Gate369 logic — conservation, tier, rate, quality, epoch gating."""

    def __init__(self, governance=None):
        self._governance = governance
        self._rate_tracker: Dict[str, list[float]] = {}
        self._gate_history: list[dict] = []
        self._stats: dict = {"checked": 0, "passed": 0, "blocked": 0, "by_type": {}}
        self._pg = None
        self._init_pg()

    def _init_pg(self):
        try:
            from ._pg import get_pg, ensure_table
            self._pg = get_pg()
            if self._pg:
                ensure_table(self._pg, "gate_checks", """
                    check_id TEXT PRIMARY KEY,
                    agent_id TEXT, operation TEXT, gate_type TEXT,
                    gated BOOLEAN, tier TEXT, delta_phi REAL,
                    epoch INT, quality_score REAL, capacity_score REAL,
                    dims INT, created_at DOUBLE PRECISION
                """)
        except Exception:
            self._pg = None

    def _persist_check(self, agent_id: str, operation: str, gate_type: str,
                       gated: bool, tier: str, delta_phi: float,
                       epoch: int, quality_score: float, capacity_score: float,
                       dims: int, check_id: str):
        if not self._pg:
            return
        try:
            from ._pg import upsert
            upsert(self._pg, "gate_checks", {
                "check_id": check_id, "agent_id": agent_id,
                "operation": operation, "gate_type": gate_type,
                "gated": gated, "tier": tier, "delta_phi": delta_phi,
                "epoch": epoch, "quality_score": quality_score,
                "capacity_score": capacity_score, "dims": dims,
                "created_at": time.time(),
            }, pk="check_id")
        except Exception:
            pass

    def _check_conservation(self, delta_phi: float) -> dict | None:
        if delta_phi > 0:
            return {"gated": True, "reason": f"ΔΦ={delta_phi:.6f} > 0 violates conservation", "gate_type": "conservation"}
        return None

    def _check_tier(self, operation: str, agent_tier: str) -> dict | None:
        required = TIER_LOCKS.get(operation)
        if required is None:
            return None
        agent_rank = TIER_ORDER.index(agent_tier) if agent_tier in TIER_ORDER else 0
        required_rank = TIER_ORDER.index(required) if required in TIER_ORDER else 0
        if agent_rank < required_rank:
            return {"gated": True, "reason": f"Operation '{operation}' requires tier '{required}', agent is '{agent_tier}'", "gate_type": "tier"}
        return None

    def _check_rate(self, agent_id: str) -> dict | None:
        now = time.time()
        timestamps = self._rate_tracker.get(agent_id, [])
        timestamps = [t for t in timestamps if now - t < 1.0]
        self._rate_tracker[agent_id] = timestamps
        if len(timestamps) >= RATE_LIMIT_PER_SEC:
            return {"gated": True, "reason": f"Rate limit exceeded: {len(timestamps)}/{RATE_LIMIT_PER_SEC} ops/sec", "gate_type": "rate"}
        timestamps.append(now)
        return None

    def _check_quality(self, quality_score: float) -> dict | None:
        if quality_score < QUALITY_THRESHOLD:
            return {"gated": True, "reason": f"Quality score {quality_score:.3f} below threshold {QUALITY_THRESHOLD}", "gate_type": "quality"}
        return None

    def _update_stats(self, gate_type: str, blocked: bool):
        self._stats["checked"] += 1
        if blocked:
            self._stats["blocked"] += 1
        else:
            self._stats["passed"] += 1
        self._stats["by_type"][gate_type] = self._stats["by_type"].get(gate_type, 0) + 1

    def check(self, agent_id: str = "", operation: str = "",
              delta_phi: float = 0.0, tier: str = "nascent",
              epoch: int = 0, quality_score: float = 1.0,
              capacity_score: float = 0.0, dims: int = 24) -> GateCheckResult:
        check_id = hashlib.sha256(f"{agent_id}:{operation}:{time.time()}".encode()).hexdigest()[:24]

        for checker, args in [
            (self._check_conservation, (delta_phi,)),
            (self._check_tier, (operation, tier)),
            (self._check_rate, (agent_id,)),
            (self._check_quality, (quality_score,)),
        ]:
            result = checker(*args)
            if result:
                self._update_stats(result["gate_type"], True)
                logger.info("GATE BLOCKED: %s op=%s type=%s", agent_id, operation, result["gate_type"])
                self._persist_check(agent_id, operation, result["gate_type"], True, tier, delta_phi, epoch, quality_score, capacity_score, dims, check_id)
                return GateCheckResult(
                    gated=True, reason=result["reason"], gate_type=result["gate_type"],
                    check_id=check_id, tier=tier, alpha=ALPHA.get(tier, 0.30),
                )

        self._update_stats("none", False)

        epoch_due = epoch > 0 and epoch % GATE_INTERVAL == 0
        saturated = capacity_score >= CAPACITY_THRESHOLD
        should_advance = epoch_due and saturated
        new_dims = min(dims + GROWTH_INCREMENT, MAX_DIMS) if should_advance else dims
        alpha = ALPHA.get(tier, 0.30)

        actions = ["compress", "contribute", "gather", "merge", "retrain", "grow", "restore"] if should_advance else []
        self._persist_check(agent_id, operation, "none", False, tier, delta_phi, epoch, quality_score, capacity_score, dims, check_id)
        response = GateCheckResult(
            gated=False, reason="all checks passed", gate_type="none",
            check_id=check_id, epoch_due=epoch_due, saturated=saturated,
            should_advance=should_advance, current_dims=dims, new_dims=new_dims,
            growth=new_dims - dims, alpha=alpha, tier=tier, actions=actions,
        )

        if should_advance:
            self._gate_history.append(response.to_dict())

        if self._governance:
            from governance.engine import BoundaryEvent
            event = BoundaryEvent(
                event_id=check_id, timestamp=time.time(), entropy_delta=delta_phi,
                receipt_data={"operation": operation, "agent_id": agent_id, "gate_type": "none"},
                boundary_type="gate_check",
            )
            self._governance.record_boundary_event(event)

        return response

    def epoch_check(self, agent_id: str, tick_count: int = 0,
                    capacity_score: float = 0.0, dims: int = 24,
                    tier: str = "nascent") -> dict:
        due = tick_count > 0 and tick_count % GATE_INTERVAL == 0
        saturated = capacity_score >= CAPACITY_THRESHOLD
        should_advance = due and saturated
        new_dims = min(dims + GROWTH_INCREMENT, MAX_DIMS) if should_advance else dims
        alpha = ALPHA.get(tier, 0.30)

        result = {
            "agent_id": agent_id, "tick_count": tick_count,
            "due": due, "saturated": saturated, "should_advance": should_advance,
            "current_dims": dims, "new_dims": new_dims, "growth": new_dims - dims,
            "alpha": alpha, "tier": tier, "gate_interval": GATE_INTERVAL,
            "next_gate_at": ((tick_count // GATE_INTERVAL) + 1) * GATE_INTERVAL,
            "actions": ["compress", "contribute", "gather", "merge", "retrain", "grow", "restore"] if should_advance else [],
        }
        if should_advance:
            self._gate_history.append(result)
        return result

    @property
    def rules(self) -> dict:
        return {
            "gate_rules": GATE_RULES, "tier_locks": TIER_LOCKS,
            "tier_order": TIER_ORDER, "gate_interval": GATE_INTERVAL,
            "capacity_threshold": CAPACITY_THRESHOLD, "rate_limit": RATE_LIMIT_PER_SEC,
            "quality_threshold": QUALITY_THRESHOLD, "growth_increment": GROWTH_INCREMENT,
            "max_dims": MAX_DIMS,
        }

    @property
    def stats(self) -> dict:
        return {
            "memory": self._stats,
            "gate_history_length": len(self._gate_history),
            "active_rate_trackers": len(self._rate_tracker),
        }

    @property
    def history(self) -> list[dict]:
        return self._gate_history
