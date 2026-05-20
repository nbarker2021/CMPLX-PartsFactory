"""HealthChecker — Comprehensive health probe for all runtime subsystems."""

from __future__ import annotations
import time
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .persistent_agent import AgentProcess

logger = logging.getLogger("runtime.health")


class HealthChecker:
    """Probes every subsystem and returns structured health report."""

    def __init__(self, agent: AgentProcess):
        self.agent = agent

    def check(self) -> dict:
        subsystems = {}

        subsystems["agent"] = {
            "running": self.agent._running,
            "alive": self.agent._thread is not None and self.agent._thread.is_alive(),
            "queue_size": self.agent._task_queue.qsize(),
        }

        subsystems["memory"] = self._check_memory()
        subsystems["governance"] = self._check_governance()
        subsystems["thinktank"] = self._check_thinktank()
        subsystems["assembly"] = self._check_assembly()
        subsystems["snapdna"] = self._check_snapdna()
        subsystems["services"] = self._check_services()
        subsystems["node"] = self._check_node()

        return {
            "status": "ok" if all(
                s.get("status") == "ok" for s in subsystems.values()
            ) else "degraded",
            "timestamp": time.time(),
            "subsystems": subsystems,
        }

    def summary(self) -> dict:
        full = self.check()
        flat = {"status": full["status"], "timestamp": full["timestamp"]}
        for name, sub in full["subsystems"].items():
            flat[name] = sub.get("status", "unknown")
        return flat

    def _check_memory(self) -> dict:
        try:
            stats = self.agent.memory.stats()
            return {"status": "ok", "db": self.agent.memory.db_path, **stats}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_governance(self) -> dict:
        try:
            g = self.agent.governance
            return {
                "status": "ok",
                "invariants": len(g.invariants),
                "boundary_events": len(g.boundary_events),
                "audit_entries": len(g.audit_trail),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_thinktank(self) -> dict:
        try:
            tt = self.agent.thinktank
            return {
                "status": "ok",
                "agents": len(tt.agents),
                "operations": len(tt.operation_log),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_assembly(self) -> dict:
        try:
            al = self.agent.assembly
            return {
                "status": "ok",
                "boundaries": len(al.boundaries),
                "validations": len(al.validation_queue),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_snapdna(self) -> dict:
        try:
            return {
                "status": "ok",
                "knowledge_docs": len(
                    self.agent.snapdna_agent.knowledge_base.documents
                ),
                "session_queries": len(self.agent.snapdna_agent.session_history),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_services(self) -> dict:
        try:
            services = self.agent.services.list_services()
            return {
                "status": "ok",
                "count": len(services),
                "services": services,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_node(self) -> dict:
        try:
            return {"status": "ok", "db": self.agent.node.db_path}
        except Exception as e:
            return {"status": "error", "error": str(e)}
