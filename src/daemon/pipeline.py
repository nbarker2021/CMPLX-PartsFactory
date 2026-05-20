"""PipelineManager — Manages the DTT pipeline queue on CRT tick schedule.

Processes IdeaPackets through the ExpertisePipeline on tick events.
Coordinates with:
  - DTTOrchestrator (dtt.orchestrator)
  - ExpertisePipeline (expertise.pipeline)
  - CRT buffers for pipeline submissions
"""

import json
import logging
import queue
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("daemon.pipeline")


class PipelineManager:
    """Manages pipeline queue processing on CRT tick schedule.

    Batches IdeaPackets and dispatches them through the ExpertisePipeline
    on pipeline_process ticks. Integrates with DTT orchestrator and
    governance audit trail.
    """

    def __init__(self, expertise_pipeline=None, dtt_orchestrator=None,
                 governance=None, buffer_fn: Callable = None):
        self.expertise_pipeline = expertise_pipeline
        self.dtt_orchestrator = dtt_orchestrator
        self.governance = governance
        self._buffer = buffer_fn
        self._queue: queue.Queue = queue.Queue()
        self._results: Dict[str, Dict] = {}
        self._processed_count = 0
        self._error_count = 0
        self._history: List[Dict] = []

    def submit(self, problem: str, context: Dict[str, Any] = None,
               domain_hint: str = None) -> str:
        """Submit a problem to the pipeline queue. Returns a packet ID."""
        packet_id = f"pkt_{uuid.uuid4().hex[:12]}"
        item = {
            "packet_id": packet_id,
            "problem": problem,
            "context": context or {},
            "domain_hint": domain_hint,
            "submitted_at": time.time(),
            "status": "queued",
        }
        self._queue.put(item)
        self._results[packet_id] = item

        if self._buffer:
            self._buffer("pipeline_submissions", {
                "packet_id": packet_id,
                "problem": problem[:200],
            })

        return packet_id

    def tick(self) -> Dict:
        """Process one batch of queued items. Called on pipeline_process ticks."""
        batch = self._drain_queue(max_items=5)
        if not batch:
            return {"processed": 0, "queued": self._queue.qsize()}

        results_list = []
        for item in batch:
            try:
                result = self._process_one(item)
                results_list.append(result)
            except Exception as e:
                self._error_count += 1
                logger.error("pipeline process error %s: %s",
                             item["packet_id"], str(e)[:120])
                item["status"] = "error"
                item["error"] = str(e)[:200]
                results_list.append(item)

        self._processed_count += len(results_list)
        self._history.extend(results_list)
        if len(self._history) > 200:
            self._history = self._history[-200:]

        return {
            "processed": len(results_list),
            "errors": sum(1 for r in results_list if r.get("status") == "error"),
            "queued": self._queue.qsize(),
            "total_processed": self._processed_count,
        }

    def _drain_queue(self, max_items: int) -> List[Dict]:
        items = []
        while len(items) < max_items:
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return items

    def _process_one(self, item: Dict) -> Dict:
        problem = item["problem"]
        context = item["context"]
        domain_hint = item.get("domain_hint")

        start = time.time()

        if self.expertise_pipeline:
            pipeline_result = self.expertise_pipeline.run(
                problem=problem,
                context=context,
                domain_hint=domain_hint,
                derived_expert_name=f"Auto_{item['packet_id']}",
            )
            item["pipeline_result"] = pipeline_result
        elif self.dtt_orchestrator:
            packet_id = self.dtt_orchestrator.submit(
                problem, domain=domain_hint or "general", context=context
            )
            item["dtt_packet_id"] = packet_id
        else:
            item["simulated"] = True

        item["status"] = "completed"
        item["completed_at"] = time.time()
        item["elapsed_seconds"] = time.time() - start
        item["result_id"] = f"res_{uuid.uuid4().hex[:12]}"

        self._results[item["packet_id"]] = item

        if self.governance:
            self._audit(item)

        return item

    def _audit(self, item: Dict):
        try:
            from governance.engine import BoundaryEvent
            event = BoundaryEvent(
                event_id=f"pipeline_{item['packet_id']}",
                timestamp=time.time(),
                entropy_delta=0.3,
                receipt_data={
                    "packet_id": item["packet_id"],
                    "status": item["status"],
                    "elapsed": item.get("elapsed_seconds", 0),
                },
                boundary_type="pipeline_process",
            )
            self.governance.record_boundary_event(event)
        except Exception as e:
            logger.warning("pipeline audit failed: %s", str(e)[:80])

    def get_result(self, packet_id: str) -> Optional[Dict]:
        return self._results.get(packet_id)

    def get_status(self) -> Dict:
        return {
            "queue_size": self._queue.qsize(),
            "total_processed": self._processed_count,
            "total_errors": self._error_count,
            "last_batch": self._history[-5:] if self._history else [],
        }

    def get_history(self, limit: int = 20) -> List[Dict]:
        return self._history[-limit:]
