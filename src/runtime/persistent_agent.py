"""AgentProcess — Persistent long-lived agent with memory, governance, and orchestration.

Can run as a background thread or standalone process. Integrates all
CMPLX-PartsFactory subsystems into a single coherent runtime.
"""

from __future__ import annotations
import logging
import os
import queue
import threading
import time
from typing import Any, Callable

from governance.engine import GeometricGovernance, BoundaryEvent
from governance.dna import DNAEncoder
from governance.snapdna import SNAPDNA
from governance.thinktank import ThinkTank
from governance.assembly import AssemblyLine
from governance.save_state import SNAPDNASaveState
from dtt.orchestrator import DTTOrchestrator
from personal_node.node import PersonalNode
from services.registry import ServiceRegistry, registry as default_registry
from snapdna.factory import factory as snapdna_factory

from .memory import AgentMemory
from .health import HealthChecker
from .snapshots import StateManager
from .orchestrator import RuntimeOrchestrator

logger = logging.getLogger("runtime.agent")


class AgentProcess:
    """Long-lived agent process with integrated subsystems.

    Features:
      - Background thread main loop with task queue
      - SQLite-backed memory (sessions, messages, knowledge, state)
      - Geometric governance with invariant validation
      - DNA encoding/decoding with governance receipts
      - ThinkTank agent management
      - AssemblyLine boundary validation
      - DTT pipeline orchestration
      - SNAPDNA expert blueprint integration
      - Service registry for Docker microservices
      - PersonalNode for operator preferences
      - State save/restore via DNA-encoded snapshots
      - Health check endpoint
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}

        # ── Governance Layer ──
        self.governance = GeometricGovernance()

        # ── DNA Layer ──
        self.dna_encoder = DNAEncoder(self.governance)

        # ── SNAPDNA Agent ──
        self.snapdna_agent = SNAPDNA(self.governance, self.dna_encoder)

        # ── ThinkTank ──
        self.thinktank = ThinkTank(self.governance)

        # ── AssemblyLine ──
        self.assembly = AssemblyLine(self.governance)

        # ── Save State ──
        self._save_state_manager = SNAPDNASaveState(self.dna_encoder)

        # ── Memory ──
        self.memory = AgentMemory(
            self.config.get("memory_db",
                            os.environ.get("AGENT_MEMORY_DB"))
        )
        self.memory.connect()

        # ── Personal Node ──
        self.node = PersonalNode(
            self.config.get("node_db",
                            os.environ.get("AGENT_NODE_DB"))
        )
        self.node.connect()

        # ── Service Registry ──
        self.services: ServiceRegistry = (
            self.config.get("service_registry") or default_registry
        )

        # ── SNAPDNA Factory ──
        self.snapdna_factory = snapdna_factory

        # ── DTT Orchestrator ──
        self.dtt = DTTOrchestrator(
            max_workers=self.config.get("dtt_max_workers", 4),
            expert_fn=self.config.get("dtt_expert_fn"),
        )

        # ── Runtime Components ──
        self.health = HealthChecker(self)
        self.snapshots = StateManager(self)
        self.orchestrator = RuntimeOrchestrator(self)

        # ── Threading ──
        self._task_queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: threading.Thread | None = None

        # ── Event Callbacks ──
        self._on_task: Callable | None = self.config.get("on_task")
        self._on_error: Callable | None = self.config.get("on_error")

        # ── Agent Identity ──
        self.agent_id = self.config.get("agent_id", "cmplx-agent")
        self.version = "1.0.0"

        # Register initial governance invariants
        self._register_core_invariants()

        # Wave 0.2: register cmplx port providers (receipt, conservation,
        # constraints, geometry, snap, memory, addressing, symbolic, transport,
        # diagnostic, engine, cache). Wraps in try/except so a misconfigured
        # cmplx tree never breaks agent boot — failures are logged but the
        # agent continues with whatever ports succeeded.
        try:
            from .cmplx_bootstrap import register_all
            self._cmplx_port_status = register_all(
                mesh=self.config.get("mesh"),  # optional mesh handle
                mmdb_path=self.config.get("cmplx_mmdb_path", ":memory:"),
            )
            logger.info("cmplx ports registered: %s", self._cmplx_port_status)
        except Exception as exc:
            logger.warning("cmplx port registration failed: %s", exc)
            self._cmplx_port_status = {"_error": str(exc)}

        logger.info("AgentProcess initialized: %s v%s", self.agent_id, self.version)

    def _register_core_invariants(self) -> None:
        from governance.engine import QuadraticInvariant
        self.governance.register_invariant(
            "agent_runtime_integrity",
            QuadraticInvariant(1.0, tolerance=0.1,
                               metadata={"type": "core", "description": "Agent runtime integrity check"}),
        )

    # ── Lifecycle ─────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            logger.warning("Agent already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                        name=f"agent-{self.agent_id}")
        self._thread.start()
        logger.info("Agent process started")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        self.save_state()
        self.memory.close()
        self.node.close()
        logger.info("Agent process stopped")

    @property
    def is_running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    # ── Task Submission ───────────────────────────────────────

    def submit_task(self, task_type: str, data: Any,
                    metadata: dict | None = None) -> str:
        task = {
            "type": task_type,
            "data": data,
            "metadata": metadata or {},
            "timestamp": time.time(),
            "task_id": None,
        }
        # Store in memory first to get a task_id
        stored_id = self.memory.store_task(task_type, data, status="queued")
        task["task_id"] = stored_id
        self._task_queue.put(task)

        self.governance.record_boundary_event(BoundaryEvent(
            event_id=f"task_{stored_id}",
            timestamp=time.time(),
            entropy_delta=0.0,
            receipt_data={"task_type": task_type, "task_id": stored_id},
            boundary_type="task_submission",
        ))
        return stored_id

    def get_task_result(self, task_id: str) -> dict | None:
        return self.memory.get_task(task_id)

    # ── Main Loop ─────────────────────────────────────────────

    def _run_loop(self) -> None:
        while self._running:
            try:
                task = self._task_queue.get(timeout=1.0)
                self._process_task(task)
            except queue.Empty:
                self._housekeeping()
            except Exception as e:
                logger.error("Task processing error: %s", e, exc_info=True)
                if self._on_error:
                    self._on_error(e)

    def _process_task(self, task: dict) -> None:
        task_type = task.get("type", "")
        data = task.get("data", {})
        task_id = task.get("task_id", "unknown")

        logger.debug("Processing task: %s [%s]", task_id, task_type)
        self.memory.update_task(task_id, status="running")

        try:
            result = self._dispatch(task_type, data)
            self.memory.update_task(task_id, output_data=result, status="done")

            if self._on_task:
                self._on_task(task_type, result)

            self.governance.record_boundary_event(BoundaryEvent(
                event_id=f"task_done_{task_id}",
                timestamp=time.time(),
                entropy_delta=0.0,
                receipt_data={"task_type": task_type, "task_id": task_id,
                              "status": "done"},
                boundary_type="task_completion",
            ))
        except Exception as e:
            logger.error("Task failed: %s — %s", task_id, e)
            self.memory.update_task(task_id, status="failed", error=str(e))

    def _dispatch(self, task_type: str, data: Any) -> Any:
        """Route task to the appropriate handler."""
        handlers = {
            "probe": self._handle_probe,
            "encode": self._handle_encode,
            "decode": self._handle_decode,
            "query": self._handle_query,
            "operate": self._handle_operate,
            "validate": self._handle_validate,
            "snapshot": self._handle_snapshot,
            "pipeline": self._handle_pipeline,
            "knowledge_add": self._handle_knowledge_add,
            "knowledge_query": self._handle_knowledge_query,
            "create_expert": self._handle_create_expert,
        }
        handler = handlers.get(task_type)
        if handler is None:
            return {"error": f"Unknown task type: {task_type}"}
        return handler(data)

    def _handle_probe(self, data: Any) -> Any:
        query = data if isinstance(data, str) else data.get("query", "")
        domain = data.get("domain", "general") if isinstance(data, dict) else "general"
        return self.snapdna_agent.query_framework(query)

    def _handle_encode(self, data: Any) -> Any:
        context = data.get("context", "") if isinstance(data, dict) else ""
        payload = data.get("data", data) if isinstance(data, dict) else data
        strand_id = self.snapdna_agent.encode_with_guidance(payload, context)
        return {"strand_id": strand_id}

    def _handle_decode(self, data: Any) -> Any:
        strand_id = data if isinstance(data, str) else data.get("strand_id", "")
        decoded = self.dna_encoder.decode(strand_id)
        return {"decoded": decoded}

    def _handle_query(self, data: Any) -> Any:
        question = data if isinstance(data, str) else data.get("question", "")
        return self.snapdna_agent.query_framework(question)

    def _handle_operate(self, data: dict) -> Any:
        agent_id = data.get("agent_id", "default")
        operation = data.get("operation", "")
        params = data.get("parameters", {})
        return self.thinktank.execute_operation(agent_id, operation, params)

    def _handle_validate(self, data: dict) -> Any:
        boundary_id = data.get("boundary_id", "")
        operation = data.get("operation", "")
        op_data = data.get("operation_data", {})
        return self.assembly.validate(boundary_id, operation, op_data)

    def _handle_snapshot(self, data: Any) -> Any:
        label = data if isinstance(data, str) else data.get("label")
        snapshot_id = self.snapshots.save_snapshot(label)
        return {"snapshot_id": snapshot_id}

    def _handle_pipeline(self, data: Any) -> Any:
        problem = data if isinstance(data, str) else data.get("problem", "")
        domain = data.get("domain", "general") if isinstance(data, dict) else "general"
        context = data.get("context") if isinstance(data, dict) else None
        packet_id = self.orchestrator.process_idea(problem, domain, context)
        return {"packet_id": packet_id}

    def _handle_knowledge_add(self, data: Any) -> Any:
        content = data if isinstance(data, str) else data.get("content", "")
        metadata = data.get("metadata") if isinstance(data, dict) else None
        doc_id = self.memory.add_document(content, metadata)
        return {"doc_id": doc_id}

    def _handle_knowledge_query(self, data: Any) -> Any:
        query = data if isinstance(data, str) else data.get("query", "")
        top_k = data.get("top_k", 5) if isinstance(data, dict) else 5
        return self.memory.query_knowledge(query, top_k=top_k)

    def _handle_create_expert(self, data: dict) -> Any:
        name = data.get("name", "")
        domain = data.get("domain", "general")
        purpose = data.get("purpose", "")
        archetype = data.get("archetype", "strategist")
        return self.orchestrator.create_expert_agent(
            name, domain, purpose, archetype=archetype
        )

    # ── Housekeeping ──────────────────────────────────────────

    _last_housekeeping: float = 0.0

    def _housekeeping(self) -> None:
        now = time.time()
        if now - self._last_housekeeping < 60.0:
            return
        self._last_housekeeping = now

        # Validate runtime invariant
        self.governance.validate_operation(
            "runtime_housekeeping",
            {"agent_runtime_integrity": 1.0},
        )

        # Periodically save state
        if int(now) % 300 < 2:
            try:
                self.save_state()
            except Exception as e:
                logger.warning("Auto-save failed: %s", e)

    # ── State Save / Restore ──────────────────────────────────

    def save_state(self, label: str | None = None) -> str | None:
        try:
            return self.snapshots.save_snapshot(label or "auto")
        except Exception as e:
            logger.error("State save failed: %s", e)
            return None

    def restore_state(self, snapshot_id: str) -> bool:
        try:
            state = self.snapshots.load_snapshot(snapshot_id)
            if state is None:
                return False
            logger.info("State restored from snapshot: %s", snapshot_id)
            return True
        except Exception as e:
            logger.error("State restore failed: %s", e)
            return False

    # ── Info / Status ─────────────────────────────────────────

    def status(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "version": self.version,
            "running": self.is_running,
            "queue_size": self._task_queue.qsize(),
            "memory": self.memory.stats(),
            "governance": {
                "invariants": len(self.governance.invariants),
                "boundary_events": len(self.governance.boundary_events),
                "audit_entries": len(self.governance.audit_trail),
            },
            "thinktank_agents": len(self.thinktank.agents),
            "assembly_boundaries": len(self.assembly.boundaries),
            "dtt_pipeline": self.dtt.status(),
        }
