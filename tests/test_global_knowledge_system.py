def test_global_knowledge_maps_tools_routes_ports_skills_and_local_paths(server):
    description = server.global_systems.describe(
        "knowledge",
        modules=["CMPLXUNI", "CMPLXMCP", "CMPLX-TMN-main"],
    )

    assert description["canonical_base"] == "/api/global/knowledge"
    assert description["tool_count"] >= 5
    assert description["route_count"] >= 10
    assert description["skill_count"] >= 1
    assert any(port["port"] == 11050 for port in description["canonical_ports"])
    assert any(port["port"] == 11112 for port in description["canonical_ports"])
    assert all(module["local_root"].startswith("repo_kernel/repos/") for module in description["modules"])
    assert any(tool["canonical_path"].startswith("/api/global/knowledge/tools/") for tool in description["tools"])


def test_global_knowledge_plan_is_dry_run(server):
    plan = server.global_systems.call_plan(
        "knowledge",
        server.GlobalSystemCallPlanRequest(
            operation="plan",
            name="search code context for adapters",
            arguments={"role": "code_context", "query": "adapter"},
            dry_run=True,
        ),
    )

    assert plan["system"] == "knowledge"
    assert plan["operation"] == "plan"
    assert plan["plan"]["workflow"] == "knowledge"
    assert plan["plan"]["runtime_candidates"]
    assert "not executed" in plan["plan"]["execution"]


def test_global_knowledge_routing_contract_exposes_needs_and_disabled_evidence(server):
    contract = server.global_systems.knowledge_routing_contract(check_health=False)

    assert contract["system"] == "knowledge"
    assert contract["control_endpoint"] == "/api/global/knowledge"
    assert any(route == "GET /api/global/knowledge/upstreams" for route in contract["public_routes"])
    assert any(upstream["name"] == "research-api" for upstream in contract["upstreams"])
    assert any(upstream["name"] == "db-aggregator-api" for upstream in contract["upstreams"])
    assert any(upstream["name"] == "research-api-jupyter" for upstream in contract["disabled_upstreams"])
    assert any(need["area"] == "native_knowledge_search" for need in contract["api_layer_needs"])
    db = next(upstream for upstream in contract["upstreams"] if upstream["name"] == "db-aggregator-api")
    assert "/search" in db["read_paths"]
    assert "blocked" in db["write_policy"]


def test_global_knowledge_proxy_blocks_write_paths(server):
    try:
        server.global_systems.knowledge_read_proxy("db-aggregator-api", "discover", query={})
    except server.HTTPException as exc:
        assert exc.status_code == 403
        assert "not approved" in exc.detail
    else:
        raise AssertionError("expected write-like knowledge path to be blocked")


def test_global_knowledge_disabled_upstream_is_not_routable(server):
    try:
        server.global_systems.knowledge_read_proxy("research-api-jupyter", "", query={})
    except server.HTTPException as exc:
        assert exc.status_code == 409
        assert "disabled" in exc.detail
    else:
        raise AssertionError("expected disabled upstream to be blocked")


def test_global_knowledge_route_endpoints_are_registered(server):
    paths = {route.path for route in server.app.routes}

    assert "/api/global/knowledge/upstreams" in paths
    assert "/api/global/knowledge/health" in paths
    assert "/api/global/knowledge/search" in paths
    assert "/api/global/knowledge/read/{service}" in paths
    assert "/api/global/knowledge/read/{service}/{path:path}" in paths
