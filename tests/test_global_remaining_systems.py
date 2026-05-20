import pytest


@pytest.mark.parametrize(
    ("system", "canonical_base", "canonical_port"),
    [
        ("geometry", "/api/global/geometry", 11182),
        ("training", "/api/global/training", 11092),
        ("code-execution", "/api/global/code-execution", 11072),
        ("pipeline", "/api/global/pipeline", 11060),
        ("external-ai-portal", "/api/global/external-ai-portal", 11000),
    ],
)
def test_remaining_global_systems_map_routes_ports_skills_and_local_paths(server, system, canonical_base, canonical_port):
    description = server.global_systems.describe(system)

    assert description["canonical_base"] == canonical_base
    assert description["module_count"] >= 1
    assert description["route_count"] >= 1
    assert description["skill_count"] >= 1
    assert any(port["port"] == canonical_port for port in description["canonical_ports"])
    assert all(module["local_root"].startswith("repo_kernel/repos/") for module in description["modules"])


@pytest.mark.parametrize(
    ("system", "tool_name"),
    [
        ("geometry", "crystal_query"),
        ("training", "l3_morsr_optimize"),
        ("code-execution", "l1_mglc_execute"),
    ],
)
def test_remaining_global_system_tool_plans_are_dry_run(server, system, tool_name):
    plan = server.global_systems.call_plan(
        system,
        server.GlobalSystemCallPlanRequest(operation="tool", name=tool_name, dry_run=True),
    )

    assert plan["system"] == system
    assert plan["operation"] == "tool"
    assert plan["candidates"]
    assert "not executed" in plan["execution"]


@pytest.mark.parametrize(
    ("system", "service_name"),
    [
        ("pipeline", "intake"),
        ("external-ai-portal", "gateway"),
    ],
)
def test_remaining_global_system_service_plans_are_approval_gated(server, system, service_name):
    plan = server.global_systems.call_plan(
        system,
        server.GlobalSystemCallPlanRequest(operation="service", name=service_name, dry_run=True),
    )

    assert plan["system"] == system
    assert plan["operation"] == "service"
    assert plan["candidates"]
    assert "requires explicit approval" in plan["execution"]


def test_global_geometry_routing_contract_exposes_read_only_upstreams(server):
    contract = server.global_systems.geometry_routing_contract(check_health=False)

    assert contract["system"] == "geometry"
    assert contract["control_endpoint"] == "/api/global/geometry"
    assert any(route == "GET /api/global/geometry/upstreams" for route in contract["public_routes"])
    assert any(upstream["name"] == "snap-unified" for upstream in contract["upstreams"])
    assert any(upstream["name"] == "unique-systems-api" for upstream in contract["upstreams"])
    snap = next(upstream for upstream in contract["upstreams"] if upstream["name"] == "snap-unified")
    assert "/snap_state" in snap["read_paths"]
    assert "blocked" in snap["write_policy"]


def test_global_geometry_proxy_blocks_mutating_paths(server):
    try:
        server.global_systems.geometry_read_proxy("tarpit-api", "process", query={})
    except server.HTTPException as exc:
        assert exc.status_code == 403
        assert "not approved" in exc.detail
    else:
        raise AssertionError("expected mutating geometry path to be blocked")


def test_global_geometry_route_endpoints_are_registered(server):
    paths = {route.path for route in server.app.routes}

    assert "/api/global/geometry/upstreams" in paths
    assert "/api/global/geometry/health" in paths
    assert "/api/global/geometry/read/{service}" in paths
    assert "/api/global/geometry/read/{service}/{path:path}" in paths


def test_global_operations_routing_contract_exposes_control_upstreams(server):
    contract = server.global_systems.operations_routing_contract(check_health=False)

    assert contract["system"] == "operations"
    assert contract["control_endpoint"] == "/api/global/operations"
    assert any(route == "GET /api/global/operations/upstreams" for route in contract["public_routes"])
    assert any(upstream["name"] == "repo-kernel" for upstream in contract["upstreams"])
    assert any(upstream["name"] == "gitnexus-rebuild-web" for upstream in contract["upstreams"])
    repo_kernel = next(upstream for upstream in contract["upstreams"] if upstream["name"] == "repo-kernel")
    assert "/api/health" in repo_kernel["read_paths"]
    assert "blocked" in repo_kernel["write_policy"]


def test_global_operations_self_read_uses_synthetic_health(server):
    result = server.global_systems.operations_read_proxy("repo-kernel", "api/health", query={})

    assert result["system"] == "operations"
    assert result["service"] == "repo-kernel"
    assert result["ok"] is True
    assert result["url"] == "self:/api/health"
    assert result["data"]["ok"] is True


def test_global_operations_proxy_blocks_unapproved_backend_paths(server):
    try:
        server.global_systems.operations_read_proxy("gitnexus-rebuild-server", "status", query={})
    except server.HTTPException as exc:
        assert exc.status_code == 403
        assert "not approved" in exc.detail
    else:
        raise AssertionError("expected unapproved operations path to be blocked")


def test_global_operations_route_endpoints_are_registered(server):
    paths = {route.path for route in server.app.routes}

    assert "/api/global/operations/upstreams" in paths
    assert "/api/global/operations/health" in paths
    assert "/api/global/operations/read/{service}" in paths
    assert "/api/global/operations/read/{service}/{path:path}" in paths
