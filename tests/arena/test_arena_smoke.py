"""Smoke tests for cmplx.arena — module registry, signup, party, scoring."""
from __future__ import annotations

import pytest

from cmplx.arena import ArenaProvider, TRAINING_SYSTEMS


class TestConstruction:
    def test_provider_constructs_in_memory(self):
        p = ArenaProvider()
        assert p.health()["modules"] == 17

    def test_training_systems_has_17(self):
        assert len(TRAINING_SYSTEMS) == 17


class TestModuleRegistry:
    def test_list_modules(self):
        p = ArenaProvider()
        mods = p.list_modules()
        assert len(mods) == 17
        ids = {m["module_id"] for m in mods}
        assert "delve" in ids
        assert "worldforge" in ids

    def test_get_module(self):
        p = ArenaProvider()
        m = p.get_module("delve")
        assert m is not None
        assert m["name"] == "DELVE"
        assert m["min_party"] == 3
        assert p.get_module("nonexistent") is None


class TestSignup:
    def test_signup_queues_agent(self):
        p = ArenaProvider()
        r = p.signup("alice", "delve")
        assert r["status"] == "queued"
        assert r["waiting"] == 1
        assert r["ready"] is False

    def test_signup_ready_when_min_met(self):
        p = ArenaProvider()
        p.signup("a", "delve")
        p.signup("b", "delve")
        r = p.signup("c", "delve")
        assert r["waiting"] == 3
        assert r["ready"] is True


class TestPartyFormation:
    def test_form_party_not_ready(self):
        p = ArenaProvider()
        p.signup("alice", "delve")
        party = p.form_party("delve")
        assert party is None

    def test_form_party_success(self):
        p = ArenaProvider()
        for i in range(3):
            p.signup(f"agent_{i}", "delve")
        party = p.form_party("delve")
        assert party is not None
        assert party["module_id"] == "delve"
        assert len(party["party"]) == 3
        assert party["status"] == "active"
        assert p.health()["active_sessions"] == 1

    def test_form_party_capped_at_max(self):
        p = ArenaProvider()
        for i in range(10):
            p.signup(f"agent_{i}", "delve")  # max_party = 6
        party = p.form_party("delve")
        assert len(party["party"]) == 6

    def test_form_party_unknown_module(self):
        p = ArenaProvider()
        assert p.form_party("nope") is None


class TestSessionCompletion:
    def test_complete_session(self):
        p = ArenaProvider()
        for i in range(3):
            p.signup(f"a{i}", "delve")
        party = p.form_party("delve")
        sid = party["session_id"]
        r = p.complete_session(
            sid,
            results={
                "production_delta": 5.0,
                "agent_scores": {"a0": 10, "a1": 8, "a2": 6},
            },
        )
        assert r["status"] == "completed"
        assert r["party_size"] == 3

    def test_complete_session_updates_leaderboard(self):
        p = ArenaProvider()
        for i in range(3):
            p.signup(f"a{i}", "delve")
        party = p.form_party("delve")
        p.complete_session(
            party["session_id"],
            results={"agent_scores": {"a0": 10, "a1": 5, "a2": 2}},
        )
        board = p.get_leaderboard("delve")
        assert len(board) == 3
        assert board[0]["agent_id"] == "a0"
        assert board[0]["score"] == 10

    def test_complete_unknown_session(self):
        p = ArenaProvider()
        r = p.complete_session("nope", results={})
        assert "error" in r


class TestEconomyStats:
    def test_economy_stats_after_party(self):
        p = ArenaProvider()
        for i in range(3):
            p.signup(f"a{i}", "delve")
        p.form_party("delve")
        stats = p.economy_stats()
        assert stats["total_fees_collected"] == 24.0  # 3 * 8.0 (delve base_cost)
        assert stats["total_rewards_paid"] == 0

    def test_health(self):
        p = ArenaProvider()
        h = p.health()
        assert h["modules"] == 17
        assert h["sessions"] == 0
        assert h["active_sessions"] == 0
