def test_live_slices_expose_upstream_contracts(server):
    expected = {
        "ai-runtime": {"research-api", "manny-manifold-api"},
        "validation": {"speedlight-api", "db-aggregator-api"},
        "synthesis": {"manny-manifold-api", "unique-systems-api"},
        "external-ai-portal": {"ngrok-cmplx"},
    }

    for system, services in expected.items():
        contract = server.global_systems.live_slice_routing_contract(system)

        assert contract["system"] == system
        assert contract["control_endpoint"] == f"/api/global/{system}"
        assert contract["status"] == "ready_for_control_route"
        assert any(route == f"GET /api/global/{system}/upstreams" for route in contract["public_routes"])
        assert services.issubset({upstream["name"] for upstream in contract["upstreams"]})
        assert all(upstream["read_paths"] for upstream in contract["upstreams"])
        assert all("blocked" in upstream["write_policy"] for upstream in contract["upstreams"])


def test_external_ai_portal_keeps_auth_gated_opencode_disabled(server):
    contract = server.global_systems.live_slice_routing_contract("external-ai-portal")

    assert any(upstream["name"] == "ngrok-cmplx" for upstream in contract["upstreams"])
    assert any(upstream["name"] == "opencode-session" for upstream in contract["disabled_upstreams"])
    assert any(need["area"] == "portal_auth_contract" for need in contract["api_layer_needs"])

    try:
        server.global_systems.live_slice_read_proxy("external-ai-portal", "opencode-session", "health")
    except server.HTTPException as exc:
        assert exc.status_code == 409
        assert "disabled" in exc.detail
    else:
        raise AssertionError("expected opencode-session to be disabled until auth contract exists")


def test_live_slice_read_paths_are_allowlisted(server):
    try:
        server.global_systems.live_slice_read_proxy("validation", "speedlight-api", "admin/delete")
    except server.HTTPException as exc:
        assert exc.status_code == 403
        assert "not approved" in exc.detail
    else:
        raise AssertionError("expected mutating-looking validation path to be blocked")


def test_live_slice_routes_are_registered(server):
    paths = {route.path for route in server.app.routes}

    assert "/api/global/{system}/upstreams" in paths
    assert "/api/global/{system}/health" in paths
    assert "/api/global/{system}/read/{service}" in paths
    assert "/api/global/{system}/read/{service}/{path:path}" in paths


def test_static_adapter_slices_cover_mcp_agent_and_code_execution(server):
    for system in ("mcp", "agent-orchestration", "code-execution"):
        contract = server.global_systems.static_adapter_routing_contract(system)

        assert contract["system"] == system
        assert contract["status"] == "ready_for_static_control_route"
        assert contract["upstreams"][0]["name"] == "repo-kernel-adapter"
        assert "/activation-candidates" in contract["upstreams"][0]["read_paths"]
        assert any(need["area"] == f"{system}_live_runtime_selection" for need in contract["api_layer_needs"])


def test_static_adapter_read_blocks_execution_paths(server):
    summary = server.global_systems.live_slice_read_proxy("mcp", "repo-kernel-adapter", "summary")

    assert summary["system"] == "mcp"
    assert summary["ok"] is True
    assert summary["data"]["status"] == "ready_for_static_control_route"

    try:
        server.global_systems.live_slice_read_proxy("code-execution", "repo-kernel-adapter", "execute")
    except server.HTTPException as exc:
        assert exc.status_code == 403
        assert "not approved" in exc.detail
    else:
        raise AssertionError("expected static adapter execution path to be blocked")
