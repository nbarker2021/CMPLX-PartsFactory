"""ExpertCreator — Expert creation pipeline.

Takes a problem, determines required expert domains, creates experts
with proper DNA archetypes, and assigns governance boundaries.
"""

from __future__ import annotations
import time
import uuid
import logging
from typing import Dict, List, Any, Optional

from governance import (
    GeometricGovernance, DNAStrand, DNAEncoder, ThinkTank,
    AssemblyLine, QuadraticInvariant, BoundaryEvent, CQELawViolationError
)
from governance.thinktank import ThinkTank as GovernanceThinkTank
from thinktank.agent import AgentArchetype, DEFAULT_ARCHETYPES
from catalog.catalog_db import CatalogDB

from .expert_memory import ExpertMemory
from .expert_registry import ExpertRegistry

logger = logging.getLogger("expertise.creator")

DOMAIN_ARCHETYPE_MAP: Dict[str, str] = {
    "storage": "validator",
    "governance": "validator",
    "cognitive": "strategist",
    "bond": "optimizer",
    "cache": "optimizer",
    "analysis": "strategist",
    "pipeline": "strategist",
    "monitoring": "monitor",
    "synthesis": "strategist",
    "verification": "validator",
    "search": "optimizer",
    "reasoning": "strategist",
    "memory": "validator",
    "coordination": "strategist",
}

DOMAIN_CAPABILITIES: Dict[str, List[str]] = {
    "storage": ["store", "retrieve", "persist", "index", "query"],
    "governance": ["validate", "audit", "enforce", "verify", "track"],
    "cognitive": ["reason", "analyze", "synthesize", "infer", "compose"],
    "bond": ["connect", "bond", "link", "assemble", "merge"],
    "cache": ["cache", "accelerate", "buffer", "optimize", "fast_lookup"],
    "analysis": ["analyze", "classify", "cluster", "extract", "summarize"],
    "pipeline": ["orchestrate", "dispatch", "coordinate", "schedule", "route"],
    "monitoring": ["monitor", "alert", "report", "track", "observe"],
    "synthesis": ["compose", "synthesize", "derive", "generate", "create"],
    "verification": ["verify", "check", "validate", "test", "prove"],
    "search": ["search", "explore", "discover", "navigate", "probe"],
    "reasoning": ["reason", "deduce", "infer", "argue", "conclude"],
    "memory": ["remember", "recall", "associate", "recognize", "store"],
    "coordination": ["coordinate", "delegate", "sync", "negotiate", "merge"],
}


class ExpertCreator:
    """Creates experts from problem descriptions.

    Pipeline:
      1. Analyze problem to determine required domains and archetypes
      2. Create expert configurations with DNA sequences
      3. Assign governance boundaries
      4. Initialize expert memory
      5. Register in the expert registry
    """

    def __init__(self, governance: GeometricGovernance,
                 registry: ExpertRegistry,
                 catalog_db: CatalogDB = None):
        self.governance = governance
        self.registry = registry
        self.catalog_db = catalog_db
        self.thinktank = GovernanceThinkTank(governance)
        self.dna_encoder = DNAEncoder(governance)
        self.assembly = AssemblyLine(governance)
        self._init_archetypes()

    def _init_archetypes(self) -> None:
        for name, arch in DEFAULT_ARCHETYPES.items():
            self.thinktank.register_archetype(name, {
                "behavior_pattern": arch.behavior_pattern,
                "priority": arch.priority,
                "dna_template": arch.dna_template,
                "capabilities": list(arch.capabilities),
            })

    def analyze_problem(self, problem: str) -> Dict[str, Any]:
        """Analyze a problem to determine required expert domains."""
        problem_lower = problem.lower()
        domains = []
        domain_scores = {}

        indicators = {
            "storage": ["store", "save", "persist", "crystal", "mmdb", "keep", "record"],
            "governance": ["govern", "rule", "policy", "audit", "validate", "compliance"],
            "cognitive": ["think", "reason", "analyze", "understand", "explain", "probe"],
            "bond": ["connect", "link", "bond", "merge", "join", "relate", "associate"],
            "cache": ["fast", "speed", "cache", "quick", "buffer", "accelerate"],
            "analysis": ["classify", "cluster", "label", "categorize", "analyze"],
            "pipeline": ["process", "pipeline", "workflow", "orchestrate", "dispatch"],
            "monitoring": ["monitor", "watch", "track", "observe", "alert", "report"],
            "synthesis": ["compose", "synthesize", "generate", "create", "build"],
            "verification": ["verify", "check", "test", "validate", "proof"],
            "search": ["search", "find", "discover", "explore", "locate"],
            "reasoning": ["deduce", "infer", "conclude", "logical", "argument"],
            "memory": ["remember", "recall", "memory", "history", "past"],
            "coordination": ["coordinate", "delegate", "team", "group", "multi"],
        }

        for domain, keywords in indicators.items():
            score = sum(1 for kw in keywords if kw in problem_lower)
            if score > 0:
                domain_scores[domain] = score
                domains.append(domain)

        if not domains:
            domains = ["analysis", "cognitive", "synthesis"]
            domain_scores = {"analysis": 1, "cognitive": 1, "synthesis": 1}

        domains.sort(key=lambda d: domain_scores[d], reverse=True)

        return {
            "domains": domains,
            "domain_scores": domain_scores,
            "primary_domain": domains[0],
        }

    def determine_required_experts(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine which experts to create based on problem analysis."""
        experts_needed = []
        for domain in analysis["domains"]:
            archetype = DOMAIN_ARCHETYPE_MAP.get(domain, "strategist")
            caps = DOMAIN_CAPABILITIES.get(domain, ["analyze", "compose", "report"])
            experts_needed.append({
                "domain": domain,
                "archetype": archetype,
                "capabilities": caps,
                "priority": analysis["domain_scores"].get(domain, 1),
            })
        return experts_needed

    def create_expert(self, name: str, domain: str, archetype: str,
                      purpose: str, capabilities: List[str],
                      problem: str = "",
                      dna_override: str = None) -> Dict[str, Any]:
        """Create a single expert with full configuration."""
        expert_id = f"expert_{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"

        agent_config = self.thinktank.create_agent(
            expert_id, archetype, custom_dna=dna_override
        )
        agent_config["capabilities"] = capabilities

        self.assembly.define_boundary(f"boundary_{expert_id}", {
            "validation_rules": ["non_negative_values", "required_fields"],
            "entropy_constraints": {"max_entropy_delta": 0.8},
        })

        dna_strand = DNAStrand()
        strand_id = dna_strand.encode_data({
            "expert_id": expert_id,
            "name": name,
            "domain": domain,
            "archetype": archetype,
            "capabilities": capabilities,
        })
        self.dna_encoder.encode(
            {"expert_id": expert_id, "domain": domain},
            f"dna_{expert_id}"
        )

        self.governance.register_invariant(
            f"expert_{expert_id}_integrity",
            QuadraticInvariant(hash(expert_id + archetype + domain) % 10000 / 10000.0)
        )

        self.governance.record_boundary_event(BoundaryEvent(
            event_id=f"create_{expert_id}",
            timestamp=time.time(),
            entropy_delta=0.1,
            receipt_data={
                "expert_id": expert_id,
                "name": name,
                "domain": domain,
                "archetype": archetype,
            },
            boundary_type="expert_creation",
        ))

        brain_template = {
            "knowledge_base": {
                "domain": domain,
                "purpose": purpose,
                "problem_context": problem[:500] if problem else "",
            },
            "experience_log": [],
            "provenance": {
                "created_by": "ExpertCreator",
                "dna_strand": strand_id,
                "archetype": archetype,
            },
        }

        instruction_set = {
            "identity": f"You are {name}, a {domain} expert.",
            "purpose": purpose,
            "capabilities": capabilities,
            "governance": f"Lane: {domain}, Archetype: {archetype}",
            "boundary": f"boundary_{expert_id}",
            "mandate": "Operate within defined governance boundaries. Log all operations. Report violations.",
        }

        agent_definition = {
            "agent_id": expert_id,
            "name": name,
            "type": "domain_expert",
            "domain": domain,
            "archetype": archetype,
            "purpose": purpose,
            "capabilities": capabilities,
            "dna_sequence": dna_override or agent_config["dna_sequence"],
            "governance_boundaries": [f"boundary_{expert_id}"],
            "inputs": {"problem": "str", "context": "dict"},
            "outputs": {"analysis": "dict", "recommendation": "dict"},
        }

        expert_data = {
            "expert_id": expert_id,
            "name": name,
            "domain": domain,
            "archetype": archetype,
            "dna_sequence": dna_override or agent_config["dna_sequence"],
            "purpose": purpose,
            "capabilities": capabilities,
            "governance_boundaries": [f"boundary_{expert_id}"],
            "brain_template": brain_template,
            "instruction_set": instruction_set,
            "agent_definition": agent_definition,
            "tags": [domain, archetype] + capabilities[:3],
            "created_at": time.time(),
        }

        self.registry.register_expert(expert_data)

        memory = ExpertMemory(expert_id)
        memory.connect()
        memory.store_entry(
            "creation",
            {
                "domain": domain,
                "archetype": archetype,
                "purpose": purpose,
                "capabilities": capabilities,
                "problem": problem[:500] if problem else "",
            },
            relevance_score=1.0,
            metadata={"event": "expert_creation", "governance": "geometric"},
        )
        memory.close()

        if self.catalog_db:
            self.catalog_db.insert_tool({
                "tool_id": expert_id,
                "name": name,
                "source": "ExpertisePipeline",
                "source_type": "derived_expert",
                "description": purpose,
                "capabilities": capabilities,
                "families": [domain, archetype],
            })

        logger.info("Created expert: %s (%s) — domain=%s archetype=%s",
                     expert_id, name, domain, archetype)
        return expert_data

    def create_experts_for_problem(self, problem: str) -> Dict[str, Any]:
        """Full pipeline: analyze problem → create all required experts."""
        analysis = self.analyze_problem(problem)
        required = self.determine_required_experts(analysis)

        created_experts = {}
        for req in required:
            domain = req["domain"]
            name = f"{domain.title()}Expert"
            purpose = f"Expert in {domain} analysis and processing"
            expert = self.create_expert(
                name=name,
                domain=domain,
                archetype=req["archetype"],
                purpose=purpose,
                capabilities=req["capabilities"],
                problem=problem,
            )
            created_experts[domain] = expert

        return {
            "analysis": analysis,
            "experts": created_experts,
            "expert_ids": [e["expert_id"] for e in created_experts.values()],
            "expert_names": {d: e["name"] for d, e in created_experts.items()},
        }
