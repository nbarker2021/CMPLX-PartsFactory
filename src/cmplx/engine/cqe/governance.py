"""
CQEGovernance — policy-level governance for CQE operations.

Coexists with `cmplx.constraints.aletheia` (per user direction): both
are valid governance entry points. Aletheia is the per-law admission
gate; CQEGovernance is the policy-level enforcement layer with
named tiers.

Adapted from `cqe_modules/cqe_governance.py`. The 6 canonical
governance levels (permissive..ultimate) each name a subset of
constraints + enforcement rules. CQEGovernance evaluates an operation
against the active policy and returns a decision.

The full historical engine had 14 builtin constraints across 8
types; this version ships a smaller, runnable starter set that
delegates the real validation work to NSL (for ΔΦ) and Aletheia
(for per-law laws). New constraint types register at runtime.
"""
from __future__ import annotations

import time
import uuid
from collections import Counter, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from cmplx.nsl import GateMode, NSLProvider, NSLSectors


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GovernanceLevel(str, Enum):
    PERMISSIVE = "permissive"           # Minimal constraints
    STANDARD = "standard"               # Normal CQE
    STRICT = "strict"                   # Enhanced
    TQF_LAWFUL = "tqf_lawful"           # TQF orbit-4
    UVIBS_COMPLIANT = "uvibs_compliant" # 80D Monster constraints
    ULTIMATE = "ultimate"               # All constraints


class ConstraintType(str, Enum):
    QUAD = "quad"
    E8 = "e8"
    PARITY = "parity"
    GOVERNANCE = "governance"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    LOGICAL = "logical"
    SEMANTIC = "semantic"
    NSL = "nsl"  # New: delegates to NSL conservation


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CQEConstraint:
    """A constraint in CQE governance.

    `validator(item, ctx) -> bool` returns True iff the item passes.
    `repair(item, ctx) -> item` is optional; called when violations
    are observed AND auto_repair is enabled.
    """
    constraint_id: str
    constraint_type: ConstraintType
    name: str
    description: str = ""
    validator: Optional[Callable[[Any, dict], bool]] = None
    repair: Optional[Callable[[Any, dict], Any]] = None
    severity: Severity = Severity.ERROR
    active: bool = True

    def evaluate(self, item: Any, ctx: dict) -> bool:
        if not self.active or self.validator is None:
            return True
        try:
            return bool(self.validator(item, ctx))
        except Exception:
            return False  # Buggy validators count as violations


@dataclass
class CQEPolicy:
    """A named set of constraints + enforcement rules."""
    policy_id: str
    name: str
    level: GovernanceLevel
    description: str = ""
    constraint_ids: list[str] = field(default_factory=list)
    auto_repair: bool = True
    strict_enforcement: bool = True
    violation_threshold: int = 10
    active: bool = True


@dataclass(frozen=True)
class ViolationRecord:
    """An immutable record of one constraint violation."""
    violation_id: str
    constraint_id: str
    constraint_name: str
    constraint_type: str
    severity: str
    item_repr: str
    timestamp: float
    resolved: bool = False
    resolution: str = ""


# ---------------------------------------------------------------------------
# Built-in constraints (starter set)
# ---------------------------------------------------------------------------

def _valid_quad_range(item: Any, ctx: dict) -> bool:
    quad = getattr(item, "quad_encoding", None) or ctx.get("quad_encoding")
    if quad is None:
        return True  # Doesn't apply if quad not present
    return all(1 <= q <= 4 for q in quad)


def _valid_e8_bounds(item: Any, ctx: dict) -> bool:
    coords = getattr(item, "e8_coordinates", None) or ctx.get("e8_coordinates")
    if coords is None:
        return True
    import math
    n = math.sqrt(sum(x * x for x in coords))
    return 0.0 <= n <= 5.0


def _valid_parity_consistency(item: Any, ctx: dict) -> bool:
    quad = getattr(item, "quad_encoding", None) or ctx.get("quad_encoding")
    parity = getattr(item, "parity_channels", None) or ctx.get("parity_channels")
    if quad is None or parity is None:
        return True
    from .atom import parity_from_quad
    return tuple(parity) == parity_from_quad(quad)


def _valid_nsl_conserved(item: Any, ctx: dict) -> bool:
    """Delegates to NSL: cumulative ΔΦ must remain ≤ 0."""
    sectors = ctx.get("sectors")
    if sectors is None:
        return True
    if not isinstance(sectors, NSLSectors):
        return True
    return sectors.is_conserved()


def _valid_timestamp(item: Any, ctx: dict) -> bool:
    ts = ctx.get("timestamp", time.time())
    return (time.time() - 86400) <= ts <= (time.time() + 3600)


_BUILTIN_CONSTRAINTS: tuple[dict, ...] = (
    {"type": ConstraintType.QUAD, "name": "valid_quad_range",
     "description": "Quad values in [1, 4]", "validator": _valid_quad_range},
    {"type": ConstraintType.E8, "name": "valid_e8_bounds",
     "description": "E8 norm in [0, 5]", "validator": _valid_e8_bounds},
    {"type": ConstraintType.PARITY, "name": "parity_consistency",
     "description": "Parity channels match quad encoding",
     "validator": _valid_parity_consistency},
    {"type": ConstraintType.NSL, "name": "nsl_conserved",
     "description": "Cumulative ΔΦ ≤ 0",
     "validator": _valid_nsl_conserved},
    {"type": ConstraintType.TEMPORAL, "name": "timestamp_validity",
     "description": "Timestamp within 24h past .. 1h future",
     "validator": _valid_timestamp,
     "severity": Severity.WARNING},
)


# ---------------------------------------------------------------------------
# CQEGovernance — the policy-level engine
# ---------------------------------------------------------------------------

class CQEGovernance:
    """Policy-level governance for CQE operations.

    Holds named constraints and policies; the active policy selects
    which constraints fire on each `validate(item, ctx)` call.

    `nsl` is required because the NSL constraint delegates the actual
    ΔΦ check to the conservation provider; if not supplied, a private
    NSLProvider is constructed.
    """

    name: str = "cqe_governance"

    def __init__(self, nsl: Optional[NSLProvider] = None) -> None:
        self.nsl = nsl or NSLProvider()
        self.constraints: dict[str, CQEConstraint] = {}
        self.policies: dict[str, CQEPolicy] = {}
        self.violations: deque[ViolationRecord] = deque(maxlen=1000)
        self.active_policy_id: Optional[str] = None
        self._register_builtin_constraints()
        self._register_builtin_policies()
        self.set_active_policy("standard")

    # ── Constraint / policy registration ─────────────────────────────

    def register_constraint(
        self,
        constraint_type: ConstraintType,
        name: str,
        validator: Callable[[Any, dict], bool],
        description: str = "",
        repair: Optional[Callable[[Any, dict], Any]] = None,
        severity: Severity = Severity.ERROR,
    ) -> str:
        constraint_id = f"{constraint_type.value}:{name}"
        if constraint_id in self.constraints:
            raise RuntimeError(f"constraint {constraint_id!r} already registered")
        self.constraints[constraint_id] = CQEConstraint(
            constraint_id=constraint_id,
            constraint_type=constraint_type,
            name=name,
            description=description,
            validator=validator,
            repair=repair,
            severity=severity,
        )
        return constraint_id

    def register_policy(
        self,
        name: str,
        level: GovernanceLevel,
        constraint_ids: list[str],
        description: str = "",
        auto_repair: bool = True,
        strict_enforcement: bool = True,
        violation_threshold: int = 10,
    ) -> str:
        policy_id = f"{level.value}:{name}"
        self.policies[policy_id] = CQEPolicy(
            policy_id=policy_id,
            name=name,
            level=level,
            description=description,
            constraint_ids=list(constraint_ids),
            auto_repair=auto_repair,
            strict_enforcement=strict_enforcement,
            violation_threshold=violation_threshold,
        )
        return policy_id

    def _register_builtin_constraints(self) -> None:
        for spec in _BUILTIN_CONSTRAINTS:
            self.register_constraint(
                constraint_type=spec["type"],
                name=spec["name"],
                validator=spec["validator"],
                description=spec.get("description", ""),
                severity=spec.get("severity", Severity.ERROR),
            )

    def _register_builtin_policies(self) -> None:
        # Index built-ins by name → full id
        cid = {c.name: c.constraint_id for c in self.constraints.values()}

        self.register_policy(
            name="permissive",
            level=GovernanceLevel.PERMISSIVE,
            constraint_ids=[cid["valid_quad_range"]],
            description="Minimal constraints",
            violation_threshold=100,
            strict_enforcement=False,
        )
        self.register_policy(
            name="standard",
            level=GovernanceLevel.STANDARD,
            constraint_ids=[
                cid["valid_quad_range"],
                cid["valid_e8_bounds"],
                cid["parity_consistency"],
                cid["nsl_conserved"],
            ],
            description="Standard CQE governance",
            violation_threshold=50,
        )
        self.register_policy(
            name="strict",
            level=GovernanceLevel.STRICT,
            constraint_ids=list(cid.values()),
            description="Enhanced validation (all built-ins)",
            violation_threshold=20,
        )
        self.register_policy(
            name="ultimate",
            level=GovernanceLevel.ULTIMATE,
            constraint_ids=list(cid.values()),
            description="All constraints active, zero tolerance",
            violation_threshold=1,
        )
        # TQF_LAWFUL and UVIBS_COMPLIANT use the same built-in set
        # in this starter; the historical engine had specialized
        # constraints for each — future follow-up.
        self.register_policy(
            name="tqf_lawful",
            level=GovernanceLevel.TQF_LAWFUL,
            constraint_ids=[
                cid["valid_quad_range"],
                cid["parity_consistency"],
                cid["nsl_conserved"],
            ],
            description="TQF Orbit-4 (starter; full TQF constraints TBD)",
            violation_threshold=10,
        )
        self.register_policy(
            name="uvibs_compliant",
            level=GovernanceLevel.UVIBS_COMPLIANT,
            constraint_ids=[
                cid["valid_quad_range"],
                cid["valid_e8_bounds"],
                cid["parity_consistency"],
                cid["nsl_conserved"],
            ],
            description="UVIBS Monster (starter; full 80D constraints TBD)",
            violation_threshold=5,
        )

    def set_active_policy(self, name: str) -> bool:
        for policy in self.policies.values():
            if policy.name == name:
                self.active_policy_id = policy.policy_id
                return True
        return False

    def active_policy(self) -> Optional[CQEPolicy]:
        if self.active_policy_id is None:
            return None
        return self.policies.get(self.active_policy_id)

    # ── Validation + repair ──────────────────────────────────────────

    def validate(self, item: Any, ctx: Optional[dict] = None) -> dict:
        """Apply the active policy to `item`. Returns:
            {valid, violations, constraint_count, policy}
        """
        ctx = dict(ctx or {})
        policy = self.active_policy()
        if policy is None or not policy.active:
            return {"valid": True, "violations": [], "constraint_count": 0,
                    "policy": None}

        violations: list[ViolationRecord] = []
        for cid in policy.constraint_ids:
            c = self.constraints.get(cid)
            if c is None or not c.active:
                continue
            if not c.evaluate(item, ctx):
                v = ViolationRecord(
                    violation_id=uuid.uuid4().hex[:12],
                    constraint_id=c.constraint_id,
                    constraint_name=c.name,
                    constraint_type=c.constraint_type.value,
                    severity=c.severity.value,
                    item_repr=str(item)[:120],
                    timestamp=time.time(),
                )
                violations.append(v)
                self.violations.append(v)

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "constraint_count": len(policy.constraint_ids),
            "policy": policy.name,
        }

    def repair(self, item: Any, ctx: Optional[dict] = None) -> tuple[Any, list]:
        """Run repair functions for any violated constraints with auto_repair.

        Returns `(item, list_of_applied_repair_names)`.
        """
        ctx = dict(ctx or {})
        policy = self.active_policy()
        if policy is None or not policy.auto_repair:
            return item, []

        applied: list[str] = []
        for cid in policy.constraint_ids:
            c = self.constraints.get(cid)
            if c is None or c.repair is None:
                continue
            if not c.evaluate(item, ctx):
                try:
                    item = c.repair(item, ctx)
                    applied.append(c.name)
                except Exception:
                    pass
        return item, applied

    # ── Stats ────────────────────────────────────────────────────────

    @property
    def health(self) -> dict:
        policy = self.active_policy()
        sev_counts: Counter[str] = Counter()
        type_counts: Counter[str] = Counter()
        for v in self.violations:
            sev_counts[v.severity] += 1
            type_counts[v.constraint_type] += 1
        return {
            "ok": True,
            "service": "cqe_governance",
            "active_policy": policy.name if policy else None,
            "constraint_count": len(self.constraints),
            "policy_count": len(self.policies),
            "violation_count": len(self.violations),
            "violations_by_severity": dict(sev_counts),
            "violations_by_type": dict(type_counts),
        }

    def __repr__(self) -> str:
        return (
            f"<CQEGovernance policy={self.active_policy().name if self.active_policy() else 'none'} "
            f"constraints={len(self.constraints)}>"
        )
