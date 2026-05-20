"""DerivedSynthesizer — Synthesizes composition results into new derived experts.

When socratic composition converges, synthesizes the results into a NEW
derived expert with:
  - Named identity
  - Brain template from composition knowledge
  - Instruction set from combined capabilities
  - Agent definition
  - Registered in the PartsFactory catalog
"""

from __future__ import annotations
import time
import uuid
import json
import logging
from typing import Dict, List, Any, Optional

from governance import (
    GeometricGovernance, DNAStrand, DNAEncoder, BoundaryEvent,
    QuadraticInvariant
)
from snapdna.factory import SNAPDNA, SNAPSpec
from catalog.catalog_db import CatalogDB

from .expert_memory import ExpertMemory
from .expert_registry import ExpertRegistry

logger = logging.getLogger("expertise.synthesizer")


class DerivedSynthesizer:
    """Synthesizes composition results into new derived experts.

    Takes converged socratic outputs and creates a permanent expert
    artifact with all required definitions.
    """

    def __init__(self, governance: GeometricGovernance,
                 registry: ExpertRegistry,
                 snapdna: SNAPDNA = None,
                 catalog_db: CatalogDB = None):
        self.governance = governance
        self.registry = registry
        self.snapdna = snapdna or SNAPDNA()
        self.catalog_db = catalog_db
        self.dna_encoder = DNAEncoder(governance)

    def synthesize(self, name: str, source_expert_ids: List[str],
                   socratic_result: Dict[str, Any],
                   problem: str = "",
                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Synthesize a derived expert from converged socratic outputs."""
        derived_id = f"derived_{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"

        source_experts = []
        for eid in source_expert_ids:
            expert = self.registry.get_expert(eid)
            if expert:
                source_experts.append(expert)

        combined_capabilities = list(set(
            cap for exp in source_experts
            for cap in exp.get("capabilities", [])
        ))

        final_outputs = socratic_result.get("final_outputs", {})
        convergence_score = socratic_result.get("convergence_score", 0.0)

        domain = self._derive_domain(source_experts, final_outputs)
        archetype = "strategist"

        brain_template = {
            "knowledge_base": {
                "domain": domain,
                "purpose": f"Derived expert from composition of {len(source_experts)} source experts",
                "source_experts": [e.get("name", e.get("expert_id")) for e in source_experts],
                "composition_result": self._summarize_outputs(final_outputs),
                "convergence_score": convergence_score,
                "problem": problem[:1000] if problem else "",
            },
            "experience_log": [],
            "provenance": {
                "created_by": "DerivedSynthesizer",
                "source_expert_ids": source_expert_ids,
                "socratic_rounds": socratic_result.get("rounds", 0),
                "convergence_history": socratic_result.get("convergence_history", []),
            },
        }

        instruction_set = {
            "identity": f"You are {name}, a derived {domain} expert.",
            "purpose": f"Synthesized from composition of {len(source_experts)} domain experts",
            "source_experts": [e.get("name", e.get("expert_id")) for e in source_experts],
            "combined_capabilities": combined_capabilities,
            "convergence_score": convergence_score,
            "mandate": "Apply synthesized knowledge from parent experts. "
                       "Preserve all capabilities. Operate within governance boundaries.",
            "lineage": [
                {
                    "ancestor": e.get("name", e.get("expert_id")),
                    "domain": e.get("domain", "unknown"),
                    "archetype": e.get("archetype", "unknown"),
                }
                for e in source_experts
            ],
        }

        agent_definition = {
            "agent_id": derived_id,
            "name": name,
            "type": "derived_expert",
            "domain": domain,
            "archetype": archetype,
            "purpose": f"Derived expert from {len(source_experts)} sources",
            "capabilities": combined_capabilities,
            "source_experts": source_expert_ids,
            "convergence_score": convergence_score,
            "governance_boundaries": list(set(
                b for exp in source_experts
                for b in (exp.get("governance_boundaries") or [])
            )),
            "inputs": {"problem": "str", "context": "dict"},
            "outputs": {"synthesis": "dict", "recommendation": "dict"},
        }

        dna_strand = DNAStrand()
        dna_strand.encode_data({
            "derived_id": derived_id,
            "name": name,
            "domain": domain,
            "sources": source_expert_ids,
            "convergence_score": convergence_score,
        })
        self.dna_encoder.encode(
            {"derived_id": derived_id, "domain": domain},
            f"dna_{derived_id}"
        )

        self.governance.register_invariant(
            f"derived_{derived_id}_integrity",
            QuadraticInvariant(hash(derived_id + name + domain) % 10000 / 10000.0)
        )

        self.governance.record_boundary_event(BoundaryEvent(
            event_id=f"synthesize_{derived_id}",
            timestamp=time.time(),
            entropy_delta=0.3,
            receipt_data={
                "derived_id": derived_id,
                "name": name,
                "domain": domain,
                "sources": source_expert_ids,
                "convergence_score": convergence_score,
            },
            boundary_type="derived_synthesis",
        ))

        expert_data = {
            "expert_id": derived_id,
            "name": name,
            "domain": domain,
            "archetype": archetype,
            "dna_sequence": dna_strand.sequence or "CGATCGAT",
            "purpose": f"Derived expert from {len(source_experts)} sources via socratic composition",
            "capabilities": combined_capabilities,
            "governance_boundaries": agent_definition["governance_boundaries"],
            "brain_template": brain_template,
            "instruction_set": instruction_set,
            "agent_definition": agent_definition,
            "tags": [domain, archetype, "derived"] + combined_capabilities[:3],
            "created_at": time.time(),
        }

        self.registry.register_expert(expert_data)
        for ancestor_id in source_expert_ids:
            self.registry.record_lineage(
                derived_id, ancestor_id,
                relationship="derived_from",
                contribution_weight=1.0 / len(source_expert_ids),
            )

        comp_id = None
        for i, src in enumerate(source_expert_ids):
            for j, other in enumerate(source_expert_ids):
                if i < j:
                    comp_id = self.registry.record_composition(
                        src, other,
                        result_expert_id=derived_id,
                        convergence_score=convergence_score,
                        rounds=socratic_result.get("rounds", 0),
                    )

        memory = ExpertMemory(derived_id)
        memory.connect()
        memory.store_entry(
            "synthesis",
            {
                "source_experts": source_expert_ids,
                "convergence_score": convergence_score,
                "rounds": socratic_result.get("rounds", 0),
                "domain": domain,
                "capabilities": combined_capabilities,
            },
            relevance_score=1.0,
            metadata={"event": "derived_synthesis", "sources": source_expert_ids},
        )
        memory.close()

        snap_spec = self.snapdna.new_spec(
            name=name,
            domain=domain,
            purpose=expert_data["purpose"],
            inputs=agent_definition["inputs"],
            outputs=agent_definition["outputs"],
            governance={"lane": domain, "dr": 0},
        )
        self.snapdna.emit_agent(
            snap_spec,
            instruction_set=json.dumps(instruction_set, indent=2),
            brain_data=brain_template,
        )

        if self.catalog_db:
            self.catalog_db.insert_tool({
                "tool_id": derived_id,
                "name": name,
                "source": "DerivedSynthesizer",
                "source_type": "derived_expert",
                "description": expert_data["purpose"],
                "capabilities": combined_capabilities,
                "families": [domain, "derived", archetype],
                "compositions_tested": source_expert_ids,
            })

        metadata_recorded = metadata or {}
        logger.info("Synthesized derived expert: %s (%s) — domain=%s convergence=%.4f",
                     derived_id, name, domain, convergence_score)

        return expert_data

    def _derive_domain(self, source_experts: List[Dict[str, Any]],
                        outputs: Dict[str, Any]) -> str:
        domains = [e.get("domain", "general") for e in source_experts]
        if not domains:
            return "general"
        from collections import Counter
        domain_counts = Counter(domains)
        return domain_counts.most_common(1)[0][0]

    def _summarize_outputs(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        summary = {}
        for expert_id, output in outputs.items():
            summary[expert_id] = {
                "status": output.get("status", "unknown"),
                "domain": output.get("domain", "unknown"),
                "has_refinements": output.get("refinements_applied") is not None,
            }
        return summary
