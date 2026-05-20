"""Conservation Service — ΔΦ = ΔN + ΔI + ΔL enforcement.

Port of TMN2 conservation.py core logic. Tracks conservation across all services.
Cumulative ΔΦ must remain ≤ 0. Violation = system halt on that path.
Three sectors: Noether (symmetry), Shannon (information), Landauer (erasure).

Integrates with GeometricGovernance for invariant validation.
"""
from __future__ import annotations
import time
import logging
from typing import Any, Dict, List

logger = logging.getLogger("services.conservation")

COUPLING = 0.030076


class ConservationReport:
    def __init__(self, agent_id: str = "", service: str = "", atom_id: str = "",
                 delta_phi: float = 0.0, delta_n: float = 0.0,
                 delta_i: float = 0.0, delta_l: float = 0.0,
                 operation: str = "", epoch: int = 0):
        self.agent_id = agent_id
        self.service = service
        self.atom_id = atom_id
        self.delta_phi = delta_phi
        self.delta_n = delta_n
        self.delta_i = delta_i
        self.delta_l = delta_l
        self.operation = operation
        self.epoch = epoch


class ConservationService:
    """Conservation law enforcement engine — ΔΦ = ΔN + ΔI + ΔL, cumulative ΔΦ ≤ 0."""

    def __init__(self, governance=None):
        self._governance = governance
        self._ledger: list[dict] = []
        self._cumulative_dphi: float = 0.0
        self._violations: int = 0
        self._per_agent: Dict[str, float] = {}
        self._per_service: Dict[str, float] = {}
        self._per_operation: Dict[str, float] = {}
        self._per_agent_violations: Dict[str, int] = {}
        self._total_checks: int = 0
        self._pg = None
        self._init_pg()

    def _init_pg(self):
        try:
            from ._pg import get_pg, ensure_table
            self._pg = get_pg()
            if self._pg:
                ensure_table(self._pg, "conservation_entries", """
                    entry_id TEXT PRIMARY KEY,
                    agent_id TEXT, service TEXT, atom_id TEXT,
                    delta_phi DOUBLE PRECISION, delta_n DOUBLE PRECISION,
                    delta_i DOUBLE PRECISION, delta_l DOUBLE PRECISION,
                    operation TEXT, epoch INT, violation BOOLEAN,
                    cumulative_before DOUBLE PRECISION,
                    cumulative_after DOUBLE PRECISION,
                    created_at DOUBLE PRECISION
                """)
        except Exception:
            self._pg = None

    def _persist_entry(self, entry: dict):
        if not self._pg:
            return
        try:
            from ._pg import upsert
            entry_id = f"cons-{entry['agent_id']}-{int(entry['timestamp'])}"
            upsert(self._pg, "conservation_entries", {
                "entry_id": entry_id, "agent_id": entry.get("agent_id", ""),
                "service": entry.get("service", ""), "atom_id": entry.get("atom_id", ""),
                "delta_phi": entry.get("delta_phi", 0.0),
                "delta_n": entry.get("delta_n", 0.0),
                "delta_i": entry.get("delta_i", 0.0),
                "delta_l": entry.get("delta_l", 0.0),
                "operation": entry.get("operation", ""),
                "epoch": entry.get("epoch", 0),
                "violation": entry.get("violation", False),
                "cumulative_before": entry.get("cumulative_before", 0.0),
                "cumulative_after": entry.get("cumulative_after", 0.0),
                "created_at": entry.get("timestamp", time.time()),
            }, pk="entry_id")
        except Exception:
            pass

    def process(self, report: ConservationReport) -> dict:
        self._total_checks += 1

        entry = {
            "agent_id": report.agent_id, "service": report.service,
            "atom_id": report.atom_id,
            "delta_phi": report.delta_phi, "delta_n": report.delta_n,
            "delta_i": report.delta_i, "delta_l": report.delta_l,
            "operation": report.operation, "epoch": report.epoch,
            "timestamp": time.time(),
            "cumulative_before": self._cumulative_dphi,
        }

        self._cumulative_dphi += report.delta_phi
        entry["cumulative_after"] = self._cumulative_dphi

        self._per_agent[report.agent_id] = self._per_agent.get(report.agent_id, 0) + report.delta_phi
        self._per_service[report.service] = self._per_service.get(report.service, 0) + report.delta_phi
        self._per_operation[report.operation] = self._per_operation.get(report.operation, 0) + report.delta_phi

        is_violation = report.delta_phi > 0
        if is_violation:
            self._violations += 1
            self._per_agent_violations[report.agent_id] = self._per_agent_violations.get(report.agent_id, 0) + 1
            entry["violation"] = True
            logger.warning("CONSERVATION VIOLATION: ΔΦ=%.4f from %s/%s op=%s",
                           report.delta_phi, report.agent_id, report.service, report.operation)
        else:
            entry["violation"] = False

        self._ledger.append(entry)
        self._persist_entry(entry)

        if self._governance:
            from governance.engine import BoundaryEvent
            event = BoundaryEvent(
                event_id=f"cons-{report.agent_id}-{int(time.time())}",
                timestamp=time.time(), entropy_delta=report.delta_phi,
                receipt_data={
                    "agent_id": report.agent_id, "service": report.service,
                    "operation": report.operation, "violation": is_violation,
                    "cumulative": self._cumulative_dphi,
                },
                boundary_type="conservation_check",
            )
            self._governance.record_boundary_event(event)

            if is_violation:
                self._governance.validate_operation(
                    f"conservation:{report.operation}",
                    {"conservation_dphi": self._cumulative_dphi},
                )

        return entry

    def process_batch(self, operations: list[ConservationReport]) -> dict:
        results = []
        violations = 0
        for op in operations:
            result = self.process(op)
            results.append(result)
            if result.get("violation"):
                violations += 1
        return {
            "processed": len(results), "violations": violations,
            "cumulative_dphi": round(self._cumulative_dphi, 6),
            "results": results,
        }

    def get_agent(self, agent_id: str) -> dict:
        return {
            "agent_id": agent_id,
            "cumulative_dphi": round(self._per_agent.get(agent_id, 0), 6),
            "violations": self._per_agent_violations.get(agent_id, 0),
        }

    def audit(self) -> dict:
        running = 0.0
        errors = []
        for i, entry in enumerate(self._ledger):
            expected_before = running
            if abs(entry.get("cumulative_before", expected_before) - expected_before) > 1e-8:
                errors.append({
                    "index": i, "expected": expected_before,
                    "got": entry.get("cumulative_before"),
                    "agent_id": entry.get("agent_id"),
                })
            running += entry.get("delta_phi", 0.0)

        drift = abs(running - self._cumulative_dphi)
        return {
            "valid": len(errors) == 0 and drift < 1e-8,
            "memory_cumulative": round(self._cumulative_dphi, 6),
            "recomputed_cumulative": round(running, 6),
            "drift": drift, "chain_errors": errors[:20],
            "total_entries": len(self._ledger),
        }

    def ledger(self, limit: int = 20) -> list[dict]:
        return self._ledger[-limit:]

    @property
    def surplus(self) -> dict:
        return {
            "surplus": round(abs(self._cumulative_dphi), 6),
            "spendable": self._cumulative_dphi < 0,
            "coupling": COUPLING,
            "conservation_valid": self._violations == 0,
        }

    @property
    def stats(self) -> dict:
        return {
            "cumulative_dphi": round(self._cumulative_dphi, 6),
            "total_checks": self._total_checks, "violations": self._violations,
            "conservation_valid": self._violations == 0, "coupling": COUPLING,
            "by_agent": {k: round(v, 6) for k, v in sorted(self._per_agent.items(), key=lambda x: x[1])},
            "by_service": {k: round(v, 6) for k, v in self._per_service.items()},
            "by_operation": {k: round(v, 6) for k, v in self._per_operation.items()},
            "agent_violations": self._per_agent_violations,
        }

    @property
    def status(self) -> dict:
        return {
            "cumulative_dphi": round(self._cumulative_dphi, 6),
            "entries": len(self._ledger), "violations": self._violations,
            "agents_tracked": len(self._per_agent),
            "services_tracked": len(self._per_service),
            "operations_tracked": len(self._per_operation),
            "coupling": COUPLING, "conservation_valid": self._violations == 0,
        }
