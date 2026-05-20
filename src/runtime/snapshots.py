"""StateManager — Full runtime state save/restore via SNAPDNASaveState snapshots."""

from __future__ import annotations
import json
import time
import logging
from typing import TYPE_CHECKING, Any, List

from governance.save_state import SNAPDNASaveState
from governance.dna import DNAStrand

if TYPE_CHECKING:
    from .persistent_agent import AgentProcess
    import numpy as np

logger = logging.getLogger("runtime.snapshots")


class StateManager:
    """Save and restore full agent runtime state as DNA-encoded snapshots.

    Each snapshot captures:
      - Governance state (invariants, boundary events, audit trail)
      - ThinkTank agents and operations
      - AssemblyLine boundaries and validations
      - SNAPDNA session history
      - AgentMemory key-value state
      - Service registry status
    """

    def __init__(self, agent: AgentProcess):
        self.agent = agent
        self.snap = SNAPDNASaveState(agent.dna_encoder)

    def save_snapshot(self, label: str | None = None) -> str:
        """Capture full runtime state as a snapshot. Returns snapshot ID."""
        state = {
            "timestamp": time.time(),
            "label": label or f"snapshot_{int(time.time())}",
            "governance": {
                "invariants": {
                    name: {
                        "value": inv.value,
                        "tolerance": inv.tolerance,
                        "metadata": inv.metadata,
                    }
                    for name, inv in self.agent.governance.invariants.items()
                },
                "boundary_events": [
                    {
                        "event_id": e.event_id,
                        "timestamp": e.timestamp,
                        "entropy_delta": e.entropy_delta,
                        "receipt_data": e.receipt_data,
                        "boundary_type": e.boundary_type,
                    }
                    for e in self.agent.governance.boundary_events
                ],
                "audit_trail": self.agent.governance.audit_trail[-100:],
            },
            "thinktank": {
                "agents": self.agent.thinktank.agents,
                "operations": self.agent.thinktank.operation_log[-100:],
            },
            "assembly": {
                "boundaries": self.agent.assembly.boundaries,
                "validations": self.agent.assembly.validation_queue[-100:],
            },
            "snapdna": {
                "session_history": self.agent.snapdna_agent.session_history[-100:],
            },
            "memory_state": self.agent.memory.get_all_state(),
            "services": self.agent.services.list_services(),
        }

        ctx = {"label": label, "type": "runtime_snapshot"}
        snapshot_id = self.snap.snap_data(state, context_metadata=ctx)
        logger.info("Snapshot saved: %s", snapshot_id)
        return snapshot_id

    def load_snapshot(self, snapshot_id: str) -> dict | None:
        """Restore runtime state from a snapshot."""
        state = self.snap.restore_save_state(snapshot_id)
        if state is None:
            logger.warning("Snapshot not found: %s", snapshot_id)
            return None
        logger.info("Snapshot loaded: %s", snapshot_id)
        return state

    def list_snapshots(self) -> list[dict]:
        """List all available snapshots with metadata."""
        results: list[dict] = []
        for ss_id, ss_data in self.snap.save_states.items():
            results.append({
                "snapshot_id": ss_id,
                "created_at": ss_data.get("created_at"),
                "original_type": ss_data.get("original_type"),
                "context": ss_data.get("context_metadata"),
            })
        results.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return results

    def delete_snapshot(self, snapshot_id: str) -> bool:
        if snapshot_id in self.snap.save_states:
            del self.snap.save_states[snapshot_id]
            logger.info("Snapshot deleted: %s", snapshot_id)
            return True
        return False

    def recall_by_text(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Recall snapshots by text similarity using geometric embeddings."""
        query_emb = self.agent.memory._generate_embedding(query)
        return self.snap.recall_by_geometry(query_emb, top_k=top_k)
