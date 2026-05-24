from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time
import uuid


@dataclass
class AgentRecord:
    """A registered agent within a hub session."""

    agent_id: str
    role: str
    goal: str
    parent_agent_id: Optional[str] = None
    state: str = "idle"
    iterations: int = 0


@dataclass
class HubSession:
    """A session that groups agents and their shared memory."""

    session_id: str = field(
        default_factory=lambda: f"sess:{uuid.uuid4().hex[:12]}"
    )
    name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    memory_events: int = 0
    agents: Dict[str, AgentRecord] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        roots = [
            a.agent_id for a in self.agents.values() if not a.parent_agent_id
        ]
        subs = [
            a.agent_id for a in self.agents.values() if a.parent_agent_id
        ]
        return {
            "session_id": self.session_id,
            "name": self.name,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "last_active_at": self.last_active_at,
            "memory_events": self.memory_events,
            "agent_count": len(self.agents),
            "root_agents": roots,
            "subagents": subs,
        }


@dataclass
class HubState:
    """Top-level mutable state for the agent hub."""

    sessions: Dict[str, HubSession] = field(default_factory=dict)
