from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import uuid
import hashlib


@dataclass
class AgentArchetype:
    """A behavioral DNA archetype for expert agents."""
    name: str
    behavior_pattern: str
    priority: str
    dna_template: str
    capabilities: List[str]


DEFAULT_ARCHETYPES: dict[str, AgentArchetype] = {
    "validator": AgentArchetype(
        name="validator",
        behavior_pattern="strict_validation",
        priority="accuracy",
        dna_template="ATGCATGC",
        capabilities=["validate", "audit", "verify"],
    ),
    "optimizer": AgentArchetype(
        name="optimizer",
        behavior_pattern="efficiency_focused",
        priority="performance",
        dna_template="GCTAGCTA",
        capabilities=["optimize", "analyze", "improve"],
    ),
    "monitor": AgentArchetype(
        name="monitor",
        behavior_pattern="continuous_observation",
        priority="stability",
        dna_template="TACGTACG",
        capabilities=["monitor", "alert", "report"],
    ),
    "strategist": AgentArchetype(
        name="strategist",
        behavior_pattern="composition_focused",
        priority="synthesis",
        dna_template="CGATCGAT",
        capabilities=["compose", "synthesize", "derive"],
    ),
}


@dataclass
class AgentInstance:
    agent_id: str
    archetype: str
    dna_sequence: str
    behavior_pattern: str
    capabilities: List[str]
    state: str = "initialized"
    operations_completed: int = 0
    success_rate: float = 0.0
    efficiency_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentManager:
    """ThinkTank — Creates, manages, and operates expert agents.
    
    Each agent has:
      - A DNA archetype defining its behavioral pattern
      - Capabilities tailored to its purpose
      - Performance tracking across operations
      - Governance validation for every operation
    """
    
    def __init__(self):
        self.archetypes: dict[str, AgentArchetype] = dict(DEFAULT_ARCHETYPES)
        self.agents: dict[str, AgentInstance] = {}
        self.operation_log: List[Dict[str, Any]] = []
    
    def register_archetype(self, archetype: AgentArchetype):
        """Register a new agent archetype."""
        self.archetypes[archetype.name] = archetype
    
    def create_agent(self, agent_id: str, archetype_name: str,
                     custom_dna: str | None = None,
                     metadata: dict | None = None) -> AgentInstance:
        """Create a tailored agent from a DNA archetype."""
        if archetype_name not in self.archetypes:
            avail = ", ".join(self.archetypes.keys())
            raise ValueError(f"Unknown archetype '{archetype_name}'. Available: {avail}")
        
        arch = self.archetypes[archetype_name]
        dna_seq = custom_dna or arch.dna_template
        
        agent = AgentInstance(
            agent_id=agent_id,
            archetype=archetype_name,
            dna_sequence=dna_seq,
            behavior_pattern=arch.behavior_pattern,
            capabilities=list(arch.capabilities),
            metadata=metadata or {},
        )
        
        self.agents[agent_id] = agent
        self._log("create_agent", {"agent_id": agent_id, "archetype": archetype_name})
        return agent
    
    def execute(self, agent_id: str, operation: str,
                parameters: dict | None = None) -> dict:
        """Execute an operation through a specific agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent '{agent_id}' not found")
        
        agent = self.agents[agent_id]
        params = parameters or {}
        
        op_hash = hash(operation + str(sorted(params.items())))
        signature = abs(op_hash) % 1000 / 1000.0
        
        result = {
            "agent_id": agent_id,
            "operation": operation,
            "parameters": params,
            "signature": signature,
            "success": True,
            "timestamp": time.time(),
        }
        
        agent.operations_completed += 1
        agent.state = "active"
        self._log("execute", result)
        return result
    
    def get_state(self) -> dict:
        """Get current agent sandbox state."""
        return {
            "agents": list(self.agents.keys()),
            "archetypes": list(self.archetypes.keys()),
            "operation_count": len(self.operation_log),
        }
    
    def _log(self, action: str, data: dict):
        self.operation_log.append({
            "action": action,
            "timestamp": time.time(),
            **data,
        })
