from __future__ import annotations

from typing import Any, Dict, List, Optional
import time

from .state import AgentRecord, HubSession, HubState


def create_session(
    state: HubState,
    *,
    name: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> HubSession:
    """Create a new session and add it to state."""
    session = HubSession(name=name or "agent-session", metadata=metadata or {})
    state.sessions[session.session_id] = session
    return session


def get_session(state: HubState, session_id: str) -> Optional[HubSession]:
    return state.sessions.get(session_id)


def list_sessions(state: HubState) -> List[HubSession]:
    return list(state.sessions.values())


def register_agent(
    state: HubState,
    session_id: str,
    agent_id: str,
    role: str,
    goal: str,
    parent_agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Register an agent in a session."""
    session = state.sessions.get(session_id)
    if not session:
        return {"error": f"Unknown session_id: {session_id}"}
    if parent_agent_id and parent_agent_id not in session.agents:
        return {"error": f"Unknown parent_agent_id: {parent_agent_id}"}
    session.agents[agent_id] = AgentRecord(
        agent_id=agent_id,
        role=role,
        goal=goal,
        parent_agent_id=parent_agent_id,
    )
    session.last_active_at = time.time()
    return {
        "session_id": session_id,
        "agent_id": agent_id,
        "parent_agent_id": parent_agent_id,
        "role": role,
        "goal": goal,
    }


def update_agent_state(
    state: HubState,
    session_id: str,
    agent_id: str,
    agent_state: str,
    iterations: int = 0,
) -> Dict[str, Any]:
    """Update the runtime-reported state of an agent."""
    session = state.sessions.get(session_id)
    if not session:
        return {"error": f"Unknown session_id: {session_id}"}
    agent = session.agents.get(agent_id)
    if not agent:
        return {"error": f"Agent {agent_id} not found in session {session_id}"}
    agent.state = agent_state
    agent.iterations = iterations
    session.last_active_at = time.time()
    return {
        "session_id": session_id,
        "agent_id": agent_id,
        "state": agent_state,
        "iterations": iterations,
    }


def session_status(state: HubState, session_id: str) -> Dict[str, Any]:
    """Return the full status of a session including its agents."""
    session = state.sessions.get(session_id)
    if not session:
        return {"error": f"Unknown session_id: {session_id}"}
    return {
        "session": session.to_dict(),
        "agents": [
            {
                "agent_id": a.agent_id,
                "role": a.role,
                "goal": a.goal,
                "parent_agent_id": a.parent_agent_id,
                "state": a.state,
                "iterations": a.iterations,
            }
            for a in session.agents.values()
        ],
    }
