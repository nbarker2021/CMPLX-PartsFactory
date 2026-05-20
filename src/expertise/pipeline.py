"""ExpertisePipeline — Complete expert factory pipeline.

Integrates all components:
  1. Expert Creation (analyze problem → create experts)
  2. Socratic Composition (critique → refine → converge)
  3. Derived Synthesis (converged results → new derived expert)
  4. Expert Registry (searchable catalog of all experts)
  5. Expert Recall (self-insert into future tasks)
  6. Expert Memory (persistent per-expert storage)

Connects to running Docker services via ServiceRegistry and persists
to the PartsFactory catalog.
"""

from __future__ import annotations
import json
import time
import uuid
import logging
from typing import Dict, List, Any, Optional, Callable

from governance import GeometricGovernance, DNAEncoder, BoundaryEvent
from snapdna.factory import SNAPDNA
from catalog.catalog_db import CatalogDB
from services.registry import ServiceRegistry

from .expert_memory import ExpertMemory
from .expert_registry import ExpertRegistry
from .expert_creator import ExpertCreator
from .socratic_composer import SocraticComposer
from .derived_synthesizer import DerivedSynthesizer
from .expert_recall import ExpertRecall

logger = logging.getLogger("expertise.pipeline")


class ExpertisePipeline:
    """Full expert factory pipeline.

    Integrates creation, composition, synthesis, registry, recall, and memory
    into a single operational pipeline.
    """

    def __init__(self, governance: GeometricGovernance = None,
                 registry: ExpertRegistry = None,
                 catalog_db: CatalogDB = None,
                 service_registry: ServiceRegistry = None,
                 snapdna: SNAPDNA = None):
        self.governance = governance or GeometricGovernance()
        self.registry = registry or ExpertRegistry()
        self.catalog_db = catalog_db
        self.service_registry = service_registry
        self.snapdna = snapdna or SNAPDNA()
        self.dna_encoder = DNAEncoder(self.governance)

        self.registry.connect()

        self.creator = ExpertCreator(self.governance, self.registry, self.catalog_db)
        self.composer = SocraticComposer(
            self.governance, self.registry,
            service_fn=self._service_dispatch if service_registry else None,
        )
        self.synthesizer = DerivedSynthesizer(
            self.governance, self.registry, self.snapdna, self.catalog_db
        )
        self.recall = ExpertRecall(self.registry)

        self.pipeline_log: List[Dict[str, Any]] = []
        self._service_cache: Dict[str, Any] = {}

    def run(self, problem: str, context: Dict[str, Any] = None,
            domain_hint: str = None,
            derived_expert_name: str = None,
            max_rounds: int = 7) -> Dict[str, Any]:
        """Run the complete expert factory pipeline for a problem.

        Steps:
          1. Self-insert existing relevant experts
          2. Create missing domain experts
          3. Run socratic composition
          4. Synthesize derived expert
          5. Register everything
        """
        pipeline_id = f"pipe_{uuid.uuid4().hex[:12]}"
        ctx = context or {}
        start = time.time()

        self.governance.record_boundary_event(
            BoundaryEvent(
                event_id=f"pipeline_start_{pipeline_id}",
                timestamp=start,
                entropy_delta=0.5,
                receipt_data={"pipeline_id": pipeline_id, "problem": problem[:200]},
                boundary_type="pipeline_start",
            )
        )

        recall_result = self.recall.self_insert(problem, domain=domain_hint)
        existing_expert_ids = [
            e["expert_id"] for e in recall_result.get("self_inserted_experts", [])
        ]

        creation_result = self.creator.create_experts_for_problem(problem)
        new_expert_ids = list(creation_result["expert_ids"])

        all_expert_ids = list(dict.fromkeys(existing_expert_ids + new_expert_ids))

        if not all_expert_ids:
            return {"error": "No experts could be created or recalled", "pipeline_id": pipeline_id}

        composer_result = self.composer.compose(
            all_expert_ids, problem, ctx
        )

        name = derived_expert_name or f"{creation_result['analysis']['primary_domain'].title()}DerivedExpert"
        derived = self.synthesizer.synthesize(
            name=name,
            source_expert_ids=all_expert_ids,
            socratic_result=composer_result,
            problem=problem,
            metadata={
                "pipeline_id": pipeline_id,
                "domain_hint": domain_hint,
                "recall_used": len(existing_expert_ids) > 0,
            },
        )

        elapsed = time.time() - start
        result = {
            "pipeline_id": pipeline_id,
            "problem": problem,
            "elapsed_seconds": elapsed,
            "recall": {
                "self_inserted": len(existing_expert_ids),
                "experts": recall_result.get("self_inserted_experts", []),
            },
            "creation": {
                "experts_created": len(new_expert_ids),
                "expert_ids": new_expert_ids,
                "experts": creation_result.get("experts", {}),
            },
            "composition": {
                "rounds": composer_result["rounds"],
                "convergence_score": composer_result["convergence_score"],
                "convergence_history": composer_result["convergence_history"],
                "all_expert_ids": all_expert_ids,
            },
            "derived_expert": derived,
        }

        self.pipeline_log.append(result)

        self.governance.record_boundary_event(
            BoundaryEvent(
                event_id=f"pipeline_end_{pipeline_id}",
                timestamp=time.time(),
                entropy_delta=0.1,
                receipt_data={
                    "pipeline_id": pipeline_id,
                    "elapsed": elapsed,
                    "recall_count": len(existing_expert_ids),
                    "created_count": len(new_expert_ids),
                    "composition_rounds": composer_result["rounds"],
                    "convergence": composer_result["convergence_score"],
                    "derived_expert_id": derived.get("expert_id"),
                },
                boundary_type="pipeline_end",
            )
        )

        logger.info("Pipeline %s complete: %d experts, %d rounds, convergence=%.4f",
                     pipeline_id, len(all_expert_ids),
                     composer_result["rounds"], composer_result["convergence_score"])

        return result

    def _service_dispatch(self, expert_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to Docker service if available."""
        if not self.service_registry:
            return {"status": "no_registry", "expert_id": expert_id}

        problem = params.get("problem", "")
        problem_lower = problem.lower()

        if any(w in problem_lower for w in ["store", "save", "crystal"]):
            if self.service_registry.mmdb:
                try:
                    return self.service_registry.mmdb.store(
                        content=problem,
                        snap_labels=[expert_id],
                        domain=expert_id,
                    )
                except Exception as e:
                    return {"error": str(e), "status": "service_error"}

        if any(w in problem_lower for w in ["brain", "reason", "think", "probe"]):
            if self.service_registry.manny:
                try:
                    return self.service_registry.manny.probe(
                        query=problem, domain=expert_id
                    )
                except Exception as e:
                    return {"error": str(e), "status": "service_error"}

        if any(w in problem_lower for w in ["stratify", "label", "classify"]):
            if self.service_registry.snap:
                try:
                    return self.service_registry.snap.stratify(
                        concept=problem, depth=3
                    )
                except Exception as e:
                    return {"error": str(e), "status": "service_error"}

        return {
            "status": "simulated",
            "expert_id": expert_id,
            "message": "No matching service found, returning simulated response",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status."""
        manifest = self.registry.get_manifest()
        return {
            "total_pipelines": len(self.pipeline_log),
            "last_pipeline": self.pipeline_log[-1] if self.pipeline_log else None,
            "registry": manifest,
            "governance_events": len(self.governance.audit_trail),
            "governance_boundary_events": len(self.governance.boundary_events),
        }

    def get_audit_trail(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent governance audit trail entries."""
        return self.governance.audit_trail[-limit:]
