def test_clean_system_image_plan_names_real_bootstrap_problems(server):
    plan = server.global_systems.clean_system_image_plan()

    assert plan["plan"] == "clean-system-image"
    assert plan["current_controller"]["service"] == "repo-kernel"
    assert "mcp" in plan["current_controller"]["routed_systems"]
    assert "code-execution" in plan["current_controller"]["routed_systems"]
    assert any(item["problem"] == "controller_monolith" for item in plan["problems_to_resolve"])
    assert any(item["problem"] == "skill_conflict_and_duplication" for item in plan["problems_to_resolve"])
    assert any("repo_kernel_app/controllers/" in item for item in plan["target_architecture"]["package_layout"])
    assert any(lane["lane"] == "capability_canon" for lane in plan["promotion_lanes"])
    assert "stable global API" in plan["new_system_image_definition"]["must_include"]
    assert "direct execution of generated wrappers" in plan["new_system_image_definition"]["must_not_include"]


def test_clean_system_image_plan_route_is_registered(server):
    paths = {route.path for route in server.app.routes}

    assert "/api/clean-system-image-plan" in paths


def test_capability_registry_stages_unification_without_refactor(server):
    registry = server.global_systems.capability_registry()

    assert registry["registry"] == "global-capability-registry"
    assert registry["summary"]["capability_count"] >= 11
    assert registry["summary"]["system_count"] >= 11
    assert any(item["system"] == "mcp" for item in registry["systems"])
    assert any(item["id"] == "mcp.repo-kernel-adapter" for item in registry["capabilities"])
    assert any(item["service"] == "manny-manifold-api" for item in registry["shared_services"])
    assert any(lane["lane"] == "merge_shared_services" for lane in registry["promotion_lanes"])
    assert registry["policy"]["not_a_refactor_yet"].startswith("this registry stages")


def test_capability_registry_route_is_registered(server):
    paths = {route.path for route in server.app.routes}

    assert "/api/capability-registry" in paths
