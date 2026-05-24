"""Smoke tests for cmplx.agenthub — can we construct, session, register, status?"""
from __future__ import annotations

import pytest

from cmplx.agenthub import AgentHubProvider, AgentRecord, HubSession, HubState
from cmplx.agenthub.operations import (
    create_session,
    get_session,
    list_sessions,
    register_agent,
    session_status,
    update_agent_state,
)


class TestConstruction:
    def test_provider_constructs_with_defaults(self):
        p = AgentHubProvider()
        assert p.health()["sessions"] == 0
        assert p.health()["agents"] == 0

    def test_provider_constructs_with_optional_deps(self):
        class FakePipeline:
            pass

        class FakeRuntime:
            pass

        p = AgentHubProvider(memory_pipeline=FakePipeline(), runtime=FakeRuntime())
        assert p.health()["sessions"] == 0


class TestSessionLifecycle:
    def test_create_session(self):
        p = AgentHubProvider()
        s = p.create_session(name="demo", metadata={"env": "test"})
        assert s["name"] == "demo"
        assert s["metadata"]["env"] == "test"
        assert s["agent_count"] == 0
        assert p.health()["sessions"] == 1

    def test_list_sessions(self):
        p = AgentHubProvider()
        p.create_session(name="a")
        p.create_session(name="b")
        assert len(p.list_sessions()) == 2

    def test_get_session(self):
        p = AgentHubProvider()
        s = p.create_session(name="x")
        sess = p.get_session(s["session_id"])
        assert sess is not None
        assert sess.name == "x"
        assert p.get_session("nope") is None


class TestAgentRegistration:
    def test_register_agent(self):
        p = AgentHubProvider()
        s = p.create_session(name="arena")
        r = p.register_agent(
            session_id=s["session_id"],
            agent_id="alice",
            role="planner",
            goal="plan routes",
        )
        assert r["agent_id"] == "alice"
        assert r["role"] == "planner"
        assert p.health()["agents"] == 1

    def test_register_subagent(self):
        p = AgentHubProvider()
        s = p.create_session(name="family")
        sid = s["session_id"]
        p.register_agent(session_id=sid, agent_id="parent", role="lead", goal="lead")
        r = p.register_agent(
            session_id=sid,
            agent_id="child",
            role="worker",
            goal="work",
            parent_agent_id="parent",
        )
        assert r["parent_agent_id"] == "parent"

    def test_register_agent_unknown_session(self):
        p = AgentHubProvider()
        r = p.register_agent(
            session_id="bad", agent_id="x", role="r", goal="g"
        )
        assert "error" in r

    def test_register_agent_unknown_parent(self):
        p = AgentHubProvider()
        s = p.create_session(name="orphan")
        r = p.register_agent(
            session_id=s["session_id"],
            agent_id="child",
            role="r",
            goal="g",
            parent_agent_id="nobody",
        )
        assert "error" in r


class TestSessionStatus:
    def test_session_status(self):
        p = AgentHubProvider()
        s = p.create_session(name="status-test")
        sid = s["session_id"]
        p.register_agent(session_id=sid, agent_id="a1", role="r1", goal="g1")
        p.register_agent(session_id=sid, agent_id="a2", role="r2", goal="g2")
        st = p.session_status(sid)
        assert st["session"]["agent_count"] == 2
        assert len(st["agents"]) == 2

    def test_session_status_unknown(self):
        p = AgentHubProvider()
        st = p.session_status("nope")
        assert "error" in st


class TestAsyncWithoutDeps:
    """Async methods must gracefully report missing dependencies."""

    @pytest.mark.anyio
    async def test_append_memory_no_pipeline(self):
        p = AgentHubProvider()
        s = p.create_session(name="mem")
        r = await p.append_memory(session_id=s["session_id"], content="hi")
        assert r["error"] == "memory_pipeline not configured"

    @pytest.mark.anyio
    async def test_recall_no_pipeline(self):
        p = AgentHubProvider()
        s = p.create_session(name="mem")
        r = await p.recall(session_id=s["session_id"], query="hi")
        assert r["error"] == "memory_pipeline not configured"

    @pytest.mark.anyio
    async def test_run_agent_task_no_runtime(self):
        p = AgentHubProvider()
        s = p.create_session(name="task")
        sid = s["session_id"]
        p.register_agent(session_id=sid, agent_id="alice", role="r", goal="g")
        r = await p.run_agent_task(
            session_id=sid, agent_id="alice", task_description="do it"
        )
        assert r["error"] == "runtime not configured"


class TestAsyncWithMocks:
    """Async methods work when dependencies are injected."""

    @pytest.mark.anyio
    async def test_append_memory_with_pipeline(self):
        class FakePipeline:
            async def ingest(self, payload):
                return {"stored": True, "id": "123"}

        p = AgentHubProvider(memory_pipeline=FakePipeline())
        s = p.create_session(name="mem")
        r = await p.append_memory(session_id=s["session_id"], content="hi")
        assert r["event_number"] == 1
        assert r["result"]["stored"] is True

    @pytest.mark.anyio
    async def test_recall_with_pipeline(self):
        class FakePipeline:
            async def query(self, payload):
                return {
                    "results": [
                        {"mdhg": {"source_path": f"memory://session/{payload['term']}/000001_user"}}
                    ]
                }

        p = AgentHubProvider(memory_pipeline=FakePipeline())
        s = p.create_session(name="mem")
        sid = s["session_id"]
        r = await p.recall(session_id=sid, query=sid)
        assert r["count"] == 1

    @pytest.mark.anyio
    async def test_run_agent_task_with_runtime(self):
        class FakeState:
            state = type("S", (), {"value": "done"})()
            iterations = 3

        class FakeRuntime:
            async def run_task(self, agent_id, task, inputs=None):
                return {"output": "ok"}

            def get(self, agent_id):
                return FakeState()

        p = AgentHubProvider(runtime=FakeRuntime())
        s = p.create_session(name="task")
        sid = s["session_id"]
        p.register_agent(session_id=sid, agent_id="alice", role="r", goal="g")
        r = await p.run_agent_task(
            session_id=sid, agent_id="alice", task_description="do it"
        )
        assert r["task_result"]["output"] == "ok"


class TestOperationsPure:
    def test_create_session_in_state(self):
        state = HubState()
        s = create_session(state, name="pure")
        assert s.name == "pure"
        assert s.session_id in state.sessions

    def test_update_agent_state(self):
        state = HubState()
        s = create_session(state, name="u")
        register_agent(state, s.session_id, "a1", "r", "g")
        r = update_agent_state(state, s.session_id, "a1", "running", 5)
        assert r["state"] == "running"
        assert r["iterations"] == 5
