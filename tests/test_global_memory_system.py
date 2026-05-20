def test_global_memory_system_maps_tools_routes_ports_skills_and_local_paths(server):
    description = server.global_systems.describe(
        "memory",
        modules=["CMPLXUNI", "CMPLX", "CMPLXMCP", "CMPLX-TMN-main"],
    )

    assert description["canonical_base"] == "/api/global/memory"
    assert description["tool_count"] >= 10
    assert description["route_count"] >= 10
    assert description["skill_count"] >= 1
    assert any(port["port"] == 11120 for port in description["canonical_ports"])
    assert any(port["port"] == 11195 for port in description["canonical_ports"])
    assert all(module["local_root"].startswith("repo_kernel/repos/") for module in description["modules"])
    assert any(tool["canonical_path"].startswith("/api/global/memory/tools/") for tool in description["tools"])


def test_global_memory_query_plan_is_dry_run(server):
    plan = server.global_systems.call_plan(
        "memory",
        server.GlobalSystemCallPlanRequest(
            operation="query",
            name="query",
            arguments={"family": "e8"},
            dry_run=True,
        ),
    )

    assert plan["system"] == "memory"
    assert plan["operation"] == "query"
    assert plan["plan"]["operation"] == "query"
    assert plan["plan"]["tool_candidates"]
    assert "not executed" in plan["plan"]["execution"]


def test_global_memory_tool_plan_aggregates_same_name_candidates(server):
    plan = server.global_systems.call_plan(
        "memory",
        server.GlobalSystemCallPlanRequest(operation="tool", name="query_atoms", dry_run=True),
    )

    assert plan["system"] == "memory"
    assert plan["operation"] == "tool"
    assert plan["candidates"]
    assert len({candidate["module"] for candidate in plan["candidates"]}) >= 1
    assert "not executed" in plan["execution"]


def test_global_memory_routing_contract_exposes_read_only_upstreams(server):
    contract = server.global_systems.memory_routing_contract(check_health=False)

    assert contract["system"] == "memory"
    assert contract["control_endpoint"] == "/api/global/memory"
    assert any(route == "GET /api/global/memory/upstreams" for route in contract["public_routes"])
    assert any(upstream["name"] == "pocket-memory-api" for upstream in contract["upstreams"])
    assert any(upstream["name"] == "mmdb-unified" for upstream in contract["upstreams"])
    pocket = next(upstream for upstream in contract["upstreams"] if upstream["name"] == "pocket-memory-api")
    assert "/search" in pocket["read_paths"]
    assert "blocked" in pocket["write_policy"]


def test_global_memory_proxy_blocks_unapproved_write_paths(server):
    try:
        server.global_systems.memory_read_proxy("pocket-memory-api", "persist", query={})
    except server.HTTPException as exc:
        assert exc.status_code == 403
        assert "not approved" in exc.detail
    else:
        raise AssertionError("expected unapproved write path to be blocked")


def test_global_memory_route_endpoints_are_registered(server):
    paths = {route.path for route in server.app.routes}

    assert "/api/global/memory/upstreams" in paths
    assert "/api/global/memory/health" in paths
    assert "/api/global/memory/search" in paths
    assert "/api/global/memory/read/{service}" in paths
    assert "/api/global/memory/read/{service}/{path:path}" in paths
