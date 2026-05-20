def test_global_agent_orchestration_maps_tools_routes_ports_skills_and_local_paths(server):
    description = server.global_systems.describe(
        "agent-orchestration",
        modules=["CMPLXUNI", "CMPLXMCP", "CMPLX-TMN-main"],
    )

    assert description["canonical_base"] == "/api/global/agent-orchestration"
    assert description["tool_count"] >= 5
    assert description["route_count"] >= 10
    assert description["skill_count"] >= 1
    assert any(port["port"] == 11030 for port in description["canonical_ports"])
    assert any(port["port"] == 11197 for port in description["canonical_ports"])
    assert all(module["local_root"].startswith("repo_kernel/repos/") for module in description["modules"])
    assert any(tool["canonical_path"].startswith("/api/global/agent-orchestration/tools/") for tool in description["tools"])


def test_global_agent_orchestration_plan_is_dry_run(server):
    plan = server.global_systems.call_plan(
        "agent-orchestration",
        server.GlobalSystemCallPlanRequest(
            operation="plan",
            name="spawn a cooperative coding agent",
            arguments={"role": "spawn"},
            dry_run=True,
        ),
    )

    assert plan["system"] == "agent-orchestration"
    assert plan["operation"] == "plan"
    assert plan["plan"]["workflow"] == "agent_orchestration"
    assert plan["plan"]["runtime_candidates"]
    assert "not executed" in plan["plan"]["execution"]
