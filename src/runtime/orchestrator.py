"""RuntimeOrchestrator — High-level coordination of all agent subsystems."""

from __future__ import annotations
import json
import time
import logging
from typing import TYPE_CHECKING, Any

from dtt.orchestrator import IdeaPacket, DTTOrchestrator
from governance.engine import BoundaryEvent
from snapdna.factory import SNAPSpec, factory as snapdna_factory

if TYPE_CHECKING:
    from .persistent_agent import AgentProcess

logger = logging.getLogger("runtime.orchestrator")


class RuntimeOrchestrator:
    """Coordinates governance, ThinkTank, SNAPDNA, DTT, and AssemblyLine.

    Provides high-level methods for:
      - Processing ideas through the DTT pipeline
      - Creating expert agents from SNAPDNA specs
      - Composing tools under governance validation
      - Running thinktank agent operations
      - Validating operations against atomic boundaries
    """

    def __init__(self, agent: AgentProcess):
        self.agent = agent

    # ── Idea Pipeline ─────────────────────────────────────────

    def process_idea(self, problem: str, domain: str = "general",
                     context: dict | None = None) -> str:
        """Submit an idea/problem through the full DTT pipeline.

        Returns a packet ID that can be used to poll for results.
        """
        packet = IdeaPacket({
            "content": {
                "problem": problem,
                "domain": domain,
                "context": context or {},
            },
            "id": None,
        })
        packet_id = self.agent.dtt.submit(packet)

        self.agent.memory.store_task(
            task_type="idea_pipeline",
            input_data={"problem": problem, "domain": domain, "packet_id": packet_id},
            status="queued",
        )

        self.agent.governance.record_boundary_event(BoundaryEvent(
            event_id=f"idea_{packet_id}",
            timestamp=time.time(),
            entropy_delta=0.0,
            receipt_data={"packet_id": packet_id, "problem": problem[:200]},
            boundary_type="idea_submission",
        ))
        return packet_id

    def get_pipeline_result(self, packet_id: str) -> dict | None:
        return self.agent.dtt.get_result(packet_id)

    def pipeline_status(self) -> dict:
        return self.agent.dtt.status()

    # ── Expert Agent Creation ─────────────────────────────────

    def create_expert_agent(self, name: str, domain: str, purpose: str,
                            inputs: dict | None = None,
                            outputs: dict | None = None,
                            archetype: str = "strategist") -> dict:
        """Create a new expert agent via SNAPDNA blueprint + ThinkTank registration."""
        spec = snapdna_factory.new_spec(
            name=name,
            domain=domain,
            purpose=purpose,
            inputs=inputs or {},
            outputs=outputs or {},
        )

        agent_config = self.agent.thinktank.create_agent(
            agent_id=name,
            archetype=archetype,
        )

        summary = {
            "spec": {
                "name": spec.name,
                "domain": spec.domain,
                "purpose": spec.purpose,
                "governance": spec.governance,
            },
            "thinktank_agent": agent_config,
            "archetype": archetype,
        }

        self.agent.memory.store_task(
            task_type="create_expert",
            input_data={"name": name, "domain": domain},
            output_data=summary,
            status="done",
        )

        return summary

    def list_experts(self) -> list[dict]:
        agents = []
        for agent_id, config in self.agent.thinktank.agents.items():
            agents.append({
                "agent_id": agent_id,
                "archetype": config.get("archetype"),
                "state": config.get("state"),
                "capabilities": config.get("capabilities", []),
                "metrics": config.get("performance_metrics", {}),
            })
        return agents

    # ── Agent Operations ──────────────────────────────────────

    def execute_agent_operation(self, agent_id: str, operation: str,
                                parameters: dict | None = None) -> dict:
        """Execute a ThinkTank agent operation under governance."""
        result = self.agent.thinktank.execute_operation(
            agent_id, operation, parameters or {}
        )

        self.agent.governance.validate_operation(
            f"agent_op_{agent_id}_{operation}",
            {f"agent_{agent_id}_state": result.get("operation_signature", 0)},
        )

        self.agent.memory.store_task(
            task_type="agent_operation",
            input_data={"agent_id": agent_id, "operation": operation,
                        "parameters": parameters},
            output_data=result,
            status="done",
        )
        return result

    # ── Boundary Validation ───────────────────────────────────

    def define_boundary(self, boundary_id: str, spec: dict) -> None:
        self.agent.assembly.define_boundary(boundary_id, spec)

    def validate_operation(self, boundary_id: str, operation: str,
                           operation_data: dict) -> dict:
        return self.agent.assembly.validate(boundary_id, operation, operation_data)

    # ── Knowledge ─────────────────────────────────────────────

    def query_framework(self, question: str) -> dict:
        return self.agent.snapdna_agent.query_framework(question)

    def add_knowledge(self, content: str, metadata: dict | None = None) -> str:
        return self.agent.memory.add_document(content, metadata)

    def query_knowledge(self, query: str, top_k: int = 5) -> list[dict]:
        return self.agent.memory.query_knowledge(query, top_k=top_k)

    # ── DNA Encoding ──────────────────────────────────────────

    def encode_data(self, data: Any, context: str = "") -> str:
        return self.agent.snapdna_agent.encode_with_guidance(data, context)

    def decode_data(self, strand_id: str) -> Any:
        return self.agent.dna_encoder.decode(strand_id)

    # ── SNAPDNA Blueprint Factory ─────────────────────────────

    def list_blueprints(self) -> list[dict]:
        return snapdna_factory.list_experts()

    def emit_tool(self, name: str, tool_code: str | None = None,
                  service_url: str | None = None) -> str:
        spec = snapdna_factory.get_expert(name)
        if spec is None:
            return f"error: no blueprint '{name}' found"
        return snapdna_factory.emit_tool(spec, tool_code=tool_code,
                                          service_url=service_url)

    def emit_agent_definition(self, name: str,
                               instruction_set: str | None = None,
                               brain_data: dict | None = None) -> str:
        spec = snapdna_factory.get_expert(name)
        if spec is None:
            return f"error: no blueprint '{name}' found"
        return snapdna_factory.emit_agent(spec, instruction_set=instruction_set,
                                           brain_data=brain_data)
