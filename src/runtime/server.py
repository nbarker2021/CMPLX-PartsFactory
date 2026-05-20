"""RuntimeHTTPServer — FastAPI HTTP server wrapping AgentProcess for standalone mode.

Provides REST API for:
  - Health check
  - Task submission and polling
  - State management (snapshots)
  - Orchestrator operations
  - Knowledge management
  - Service discovery
"""

from __future__ import annotations
import json
import logging
import os
import threading
import time
import uuid
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .persistent_agent import AgentProcess

logger = logging.getLogger("runtime.server")

# ── Request/Response Models ────────────────────────────────────


class TaskSubmit(BaseModel):
    type: str
    data: Any = {}
    metadata: dict | None = None


class TaskResponse(BaseModel):
    task_id: str
    status: str


class SnapshotRequest(BaseModel):
    label: str | None = None


class EncodeRequest(BaseModel):
    data: Any
    context: str = ""


class DecodeRequest(BaseModel):
    strand_id: str


class QueryRequest(BaseModel):
    question: str


class OperateRequest(BaseModel):
    agent_id: str = "default"
    operation: str
    parameters: dict = {}


class ValidateRequest(BaseModel):
    boundary_id: str
    operation: str
    operation_data: dict = {}


class PipelineRequest(BaseModel):
    problem: str
    domain: str = "general"
    context: dict | None = None


class KnowledgeAddRequest(BaseModel):
    content: str
    metadata: dict | None = None


class KnowledgeQueryRequest(BaseModel):
    query: str
    top_k: int = 5


class CreateExpertRequest(BaseModel):
    name: str
    domain: str = "general"
    purpose: str = ""
    archetype: str = "strategist"
    inputs: dict = {}
    outputs: dict = {}


class ConfigRequest(BaseModel):
    key: str
    value: Any

# ── Server ─────────────────────────────────────────────────────


class RuntimeHTTPServer:
    """HTTP server wrapping an AgentProcess in a FastAPI application.

    Can run standalone or be embedded in another FastAPI app.
    """

    def __init__(self, agent: AgentProcess | None = None,
                 config: dict | None = None):
        self.config = config or {}
        self.agent = agent or AgentProcess(self.config)
        self.host = self.config.get("host", "0.0.0.0")
        self.port = int(self.config.get("port", os.environ.get("RUNTIME_PORT", "8877")))
        self.app = FastAPI(
            title="CMPLX-PartsFactory Agent Runtime",
            version="1.0.0",
            description="Persistent agent runtime with governance, memory, and orchestration.",
        )
        self._register_routes()

    def _register_routes(self) -> None:
        app = self.app
        agent = self.agent

        # ── Health ──

        @app.get("/health")
        def get_health():
            return agent.health.check()

        @app.get("/health/summary")
        def get_health_summary():
            return agent.health.summary()

        # ── Status ──

        @app.get("/status")
        def get_status():
            return agent.status()

        # ── Task Management ──

        @app.post("/task", response_model=TaskResponse)
        def submit_task(body: TaskSubmit):
            task_id = agent.submit_task(body.type, body.data, body.metadata)
            return TaskResponse(task_id=task_id, status="queued")

        @app.get("/task/{task_id}")
        def get_task(task_id: str):
            result = agent.get_task_result(task_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Task not found")
            return result

        @app.get("/tasks")
        def list_tasks(task_type: str | None = None,
                       status: str | None = None,
                       limit: int = 50):
            return agent.memory.list_tasks(task_type=task_type,
                                            status=status, limit=limit)

        # ── Agent Control ──

        @app.post("/start")
        def start_agent():
            agent.start()
            return {"status": "started", "agent_id": agent.agent_id}

        @app.post("/stop")
        def stop_agent():
            agent.stop()
            return {"status": "stopped"}

        # ── Snapshots ──

        @app.post("/snapshot")
        def create_snapshot(body: SnapshotRequest = SnapshotRequest()):
            snapshot_id = agent.snapshots.save_snapshot(body.label)
            return {"snapshot_id": snapshot_id}

        @app.get("/snapshots")
        def list_snapshots():
            return agent.snapshots.list_snapshots()

        @app.post("/snapshot/{snapshot_id}/restore")
        def restore_snapshot(snapshot_id: str):
            ok = agent.restore_state(snapshot_id)
            if not ok:
                raise HTTPException(status_code=404, detail="Snapshot not found")
            return {"status": "restored", "snapshot_id": snapshot_id}

        @app.delete("/snapshot/{snapshot_id}")
        def delete_snapshot(snapshot_id: str):
            ok = agent.snapshots.delete_snapshot(snapshot_id)
            if not ok:
                raise HTTPException(status_code=404, detail="Snapshot not found")
            return {"status": "deleted"}

        @app.get("/snapshots/search")
        def search_snapshots(q: str, top_k: int = 5):
            results = agent.snapshots.recall_by_text(q, top_k=top_k)
            return {"query": q, "results": results}

        # ── DNA Encoding ──

        @app.post("/encode")
        def encode(body: EncodeRequest):
            strand_id = agent.snapdna_agent.encode_with_guidance(body.data, body.context)
            return {"strand_id": strand_id}

        @app.post("/decode")
        def decode(body: DecodeRequest):
            decoded = agent.dna_encoder.decode(body.strand_id)
            return {"decoded": decoded}

        # ── Framework Query ──

        @app.post("/query")
        def query_framework(body: QueryRequest):
            return agent.snapdna_agent.query_framework(body.question)

        # ── Orchestration ──

        @app.post("/pipeline")
        def submit_pipeline(body: PipelineRequest):
            packet_id = agent.orchestrator.process_idea(
                body.problem, body.domain, body.context
            )
            return {"packet_id": packet_id}

        @app.get("/pipeline/{packet_id}")
        def get_pipeline(packet_id: str):
            result = agent.orchestrator.get_pipeline_result(packet_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Pipeline result not found")
            return result

        @app.get("/pipeline/status")
        def pipeline_status():
            return agent.orchestrator.pipeline_status()

        # ── Agent Operations ──

        @app.post("/operate")
        def operate(body: OperateRequest):
            return agent.orchestrator.execute_agent_operation(
                body.agent_id, body.operation, body.parameters
            )

        @app.post("/validate")
        def validate(body: ValidateRequest):
            return agent.assembly.validate(
                body.boundary_id, body.operation, body.operation_data
            )

        @app.get("/agents")
        def list_agents():
            return agent.orchestrator.list_experts()

        @app.post("/agents/create")
        def create_agent(body: CreateExpertRequest):
            return agent.orchestrator.create_expert_agent(
                name=body.name, domain=body.domain,
                purpose=body.purpose, archetype=body.archetype,
                inputs=body.inputs, outputs=body.outputs,
            )

        # ── Knowledge ──

        @app.post("/knowledge")
        def add_knowledge(body: KnowledgeAddRequest):
            doc_id = agent.memory.add_document(body.content, body.metadata)
            return {"doc_id": doc_id}

        @app.post("/knowledge/query")
        def query_knowledge(body: KnowledgeQueryRequest):
            return agent.memory.query_knowledge(body.query, body.top_k)

        # ── Memory State ──

        @app.get("/memory/state")
        def get_memory_state():
            return agent.memory.get_all_state()

        @app.post("/memory/state")
        def set_memory_state(body: ConfigRequest):
            agent.memory.set_state(body.key, body.value)
            return {"status": "set", "key": body.key}

        # ── Services ──

        @app.get("/services")
        def list_services():
            return agent.services.list_services()

        @app.post("/services/health")
        def check_services():
            return agent.services.check_health()

        # ── Sessions ──

        @app.post("/sessions")
        def create_session(agent_id: str = "default"):
            sid = agent.memory.create_session(agent_id=agent_id)
            return {"session_id": sid}

        @app.get("/sessions")
        def list_sessions(agent_id: str | None = None, limit: int = 50):
            return agent.memory.list_sessions(agent_id=agent_id, limit=limit)

        @app.get("/sessions/{session_id}")
        def get_session(session_id: str):
            sess = agent.memory.get_session(session_id)
            if sess is None:
                raise HTTPException(status_code=404, detail="Session not found")
            return sess

        @app.post("/sessions/{session_id}/messages")
        def add_message(session_id: str, role: str, content: str):
            mid = agent.memory.add_message(session_id, role, content)
            return {"message_id": mid}

        @app.get("/sessions/{session_id}/messages")
        def get_messages(session_id: str, limit: int = 100):
            return agent.memory.get_messages(session_id, limit=limit)

        # ── Expert Blueprints ──

        @app.get("/blueprints")
        def list_blueprints():
            return agent.snapdna_factory.list_experts()

        @app.post("/blueprints/{name}/emit/tool")
        def emit_tool(name: str, service_url: str | None = None):
            result = agent.orchestrator.emit_tool(name, service_url=service_url)
            return {"path": result}

        @app.post("/blueprints/{name}/emit/agent")
        def emit_agent(name: str):
            result = agent.orchestrator.emit_agent_definition(name)
            return {"path": result}

    # ── Run ───────────────────────────────────────────────────

    def run(self, host: str | None = None, port: int | None = None,
            log_level: str = "info") -> None:
        self.agent.start()
        uvicorn.run(
            self.app,
            host=host or self.host,
            port=port or self.port,
            log_level=log_level,
        )


def run_server():
    """Entry point for standalone server execution."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    port = int(os.environ.get("RUNTIME_PORT", "8877"))
    server = RuntimeHTTPServer(config={"port": port})
    logger.info("Starting RuntimeHTTPServer on port %d", port)
    server.run()


if __name__ == "__main__":
    run_server()
