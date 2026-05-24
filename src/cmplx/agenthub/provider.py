from __future__ import annotations

from typing import Any, Awaitable, Dict, List, Optional
import asyncio

from .state import HubState, HubSession
from .operations import (
    create_session,
    get_session,
    list_sessions,
    register_agent,
    session_status,
    update_agent_state,
)


class AgentHubProvider:
    """Port-facing provider for agent session lifecycle.

    The *memory_pipeline* and *runtime* dependencies are optional.
    When absent, memory and task methods return descriptive error dicts
    rather than raising, so the hub can still be used for registration
    and status tracking.
    """

    def __init__(
        self,
        *,
        memory_pipeline: Optional[Any] = None,
        runtime: Optional[Any] = None,
    ) -> None:
        self.state = HubState()
        self.memory_pipeline = memory_pipeline
        self.runtime = runtime

    # ------------------------------------------------------------------
    # Sync lifecycle
    # ------------------------------------------------------------------

    def create_session(
        self,
        *,
        name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        session = create_session(self.state, name=name, metadata=metadata)
        return session.to_dict()

    def list_sessions(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in list_sessions(self.state)]

    def get_session(self, session_id: str) -> Optional[HubSession]:
        return get_session(self.state, session_id)

    def register_agent(
        self,
        *,
        session_id: str,
        agent_id: str,
        role: str,
        goal: str,
        parent_agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return register_agent(
            self.state,
            session_id,
            agent_id,
            role,
            goal,
            parent_agent_id,
        )

    def session_status(self, session_id: str) -> Dict[str, Any]:
        return session_status(self.state, session_id)

    def health(self) -> Dict[str, Any]:
        total_agents = sum(len(s.agents) for s in self.state.sessions.values())
        return {
            "sessions": len(self.state.sessions),
            "agents": total_agents,
        }

    # ------------------------------------------------------------------
    # Async memory & task execution (require injected dependencies)
    # ------------------------------------------------------------------

    async def append_memory(
        self,
        *,
        session_id: str,
        content: str,
        role: str = "user",
        level: str = "ca",
        metadata: Optional[Dict[str, Any]] = None,
        terms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        session = get_session(self.state, session_id)
        if not session:
            return {"error": f"Unknown session_id: {session_id}"}
        if self.memory_pipeline is None:
            return {"error": "memory_pipeline not configured"}

        event_number = session.memory_events + 1
        source_path = (
            f"memory://session/{session_id}/{event_number:06d}_{role}"
        )
        merged_metadata: Dict[str, Any] = {
            "session_id": session_id,
            "role": role,
        }
        if metadata:
            merged_metadata.update(metadata)

        result = await self.memory_pipeline.ingest(
            {
                "level": level,
                "corpus_label": f"session:{session_id}",
                "source_path": source_path,
                "content": content,
                "metadata": merged_metadata,
                "terms": terms,
            }
        )

        session.memory_events += 1
        return {
            "session_id": session_id,
            "event_number": event_number,
            "level": level,
            "source_path": source_path,
            "result": result,
        }

    async def recall(
        self,
        *,
        session_id: str,
        query: str,
        top_k: int = 5,
        level: Optional[str] = None,
        snap_required: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        session = get_session(self.state, session_id)
        if not session:
            return {"error": f"Unknown session_id: {session_id}"}
        if self.memory_pipeline is None:
            return {"error": "memory_pipeline not configured"}

        result = await self.memory_pipeline.query(
            {
                "term": query,
                "top_k": top_k,
                "level": level,
                "snap_required": snap_required or [],
            }
        )

        prefix = f"memory://session/{session_id}/"
        scoped = []
        for item in result.get("results", []):
            mdhg_payload = item.get("mdhg", {}) if isinstance(item, dict) else {}
            source_path = mdhg_payload.get("source_path", "")
            if source_path.startswith(prefix):
                scoped.append(item)

        return {
            "session_id": session_id,
            "query": query,
            "count": len(scoped),
            "results": scoped[:top_k],
            "level": level or "all",
        }

    async def run_agent_task(
        self,
        *,
        session_id: str,
        agent_id: str,
        task_description: str,
        inputs: Optional[Dict[str, Any]] = None,
        remember: bool = True,
        level: str = "ca",
    ) -> Dict[str, Any]:
        session = get_session(self.state, session_id)
        if not session:
            return {"error": f"Unknown session_id: {session_id}"}
        if agent_id not in session.agents:
            return {
                "error": f"Agent {agent_id} is not registered in session {session_id}"
            }
        if self.runtime is None:
            return {"error": "runtime not configured"}

        if remember:
            await self.append_memory(
                session_id=session_id,
                content=task_description,
                role="user",
                level=level,
                metadata={"agent_id": agent_id, "kind": "task"},
            )

        result = await self.runtime.run_task(
            agent_id, task_description, inputs=inputs
        )

        # Update agent state from runtime if available
        if hasattr(self.runtime, "get"):
            runtime_state = self.runtime.get(agent_id)
            if runtime_state is not None:
                state_val = getattr(runtime_state, "state", None)
                iterations = getattr(runtime_state, "iterations", 0)
                if state_val is not None:
                    update_agent_state(
                        self.state,
                        session_id,
                        agent_id,
                        state_val.value if hasattr(state_val, "value") else str(state_val),
                        iterations,
                    )

        if remember and result.get("output"):
            await self.append_memory(
                session_id=session_id,
                content=result.get("output", ""),
                role="assistant",
                level=level,
                metadata={"agent_id": agent_id, "kind": "response"},
            )

        return {
            "session_id": session_id,
            "agent_id": agent_id,
            "task_result": result,
        }
