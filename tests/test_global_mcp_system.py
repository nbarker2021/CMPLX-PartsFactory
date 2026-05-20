def test_global_mcp_system_maps_tools_ports_skills_and_local_paths(server):
    description = server.global_systems.describe("mcp", modules=["CMPLXMCP"])

    assert description["canonical_base"] == "/api/global/mcp"
    assert description["tool_count"] >= 30
    assert description["skill_count"] >= 1
    assert any(port["host_port"] == 8900 for port in description["ports"])
    assert all(module["local_root"].startswith("repo_kernel/repos/") for module in description["modules"])
    assert any(tool["canonical_path"].startswith("/api/global/mcp/tools/") for tool in description["tools"])


def test_global_mcp_call_plan_is_dry_run(server):
    plan = server.global_systems.call_plan(
        "mcp",
        server.GlobalSystemCallPlanRequest(operation="tool", name="l2_e8_project", dry_run=True),
    )

    assert plan["system"] == "mcp"
    assert plan["operation"] == "tool"
    assert plan["candidates"]
    assert "not executed" in plan["execution"]
