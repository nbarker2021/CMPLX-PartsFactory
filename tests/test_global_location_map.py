def test_global_location_map_lists_all_systems_with_paths_and_ports(server):
    location_map = server.global_systems.location_map()

    assert location_map["count"] == 18
    systems = {item["system"]: item for item in location_map["systems"]}
    assert "memory" in systems
    assert "external-ai-portal" in systems
    assert "formalization" in systems
    assert "ai-runtime" in systems
    assert "operations" in systems
    assert "eventing" in systems
    assert "community" in systems
    assert "economy" in systems
    assert "validation" in systems
    assert "synthesis" in systems
    assert "simulation" in systems
    assert systems["memory"]["hosted_locations"]["canonical_base"] == "/api/global/memory"
    assert systems["memory"]["hosted_locations"]["generic_base"] == "/api/global-systems/memory"
    assert any(port["port"] == 11120 for port in systems["memory"]["port_map"]["canonical_ports"])
    assert all(
        module["local_root"].startswith("repo_kernel/repos/")
        for module in systems["memory"]["path_map"]["module_roots"]
    )


def test_single_system_location_map_is_relocation_safe(server):
    location_map = server.global_systems.location_map("pipeline")
    system = location_map["systems"][0]

    assert location_map["count"] == 1
    assert system["system"] == "pipeline"
    assert system["status"] == "mapped_not_moved"
    assert system["hosted_locations"]["canonical_base"] == "/api/global/pipeline"
    assert any(port["port"] == 11060 for port in system["port_map"]["canonical_ownership"])
    assert "requires" not in " ".join(system["move_plan"]).lower()


def test_generic_global_alias_routes_are_registered(server):
    paths = {route.path for route in server.app.routes}

    assert "/api/global/{system}" in paths
    assert "/api/global/{system}/location" in paths
    assert "/api/global/{system}/tools" in paths
    assert "/api/global/{system}/call-plan" in paths
    assert "/api/global-coverage" in paths
    assert "/api/global-port-plan" in paths
    assert "/api/global-runtime-slices" in paths
    assert "/api/global-tool-workbook" in paths
    assert "/api/global-state" in paths
    assert "/api/global/query" in paths


def test_global_coverage_identifies_assigned_and_unassigned_surfaces(server):
    coverage = server.global_systems.coverage(
        modules=["CMPLXMCP", "CMPLXUNI", "CMPLX-TMN-main"],
        limit_unassigned=20,
    )

    assert coverage["module_count"] == 3
    assert coverage["summary"]["routes"] >= 1
    assert coverage["summary"]["assigned"] >= 1
    assert coverage["summary"]["unassigned"] >= 1
    assert coverage["implementation_needs"]
    assert any(item["local_source"].startswith("repo_kernel/repos/") for item in coverage["unassigned_samples"])


def test_global_formalization_lane_covers_proof_and_planner_surfaces(server):
    description = server.global_systems.describe(
        "formalization",
        modules=["CMPLXUNI", "CMPLXMCP", "CMPLX-Formalization"],
    )

    assert description["canonical_base"] == "/api/global/formalization"
    assert description["route_count"] >= 10
    assert any(route["canonical_path"].startswith("/api/global/formalization/routes/") for route in description["routes"])
    assert all(module["local_root"].startswith("repo_kernel/repos/") for module in description["modules"])


def test_global_gap_lanes_cover_ai_ops_and_eventing_clusters(server):
    ai_runtime = server.global_systems.describe("ai-runtime", modules=["CMPLXUNI", "CMPLX-TMN-main"])
    operations = server.global_systems.describe("operations", modules=["CMPLXUNI", "CMPLX-TMN-main"])
    eventing = server.global_systems.describe("eventing", modules=["CMPLXUNI", "CMPLX-TMN-main"])

    assert ai_runtime["route_count"] >= 1
    assert operations["route_count"] >= 1
    assert eventing["route_count"] >= 1
    assert any(port["port"] == 11150 for port in operations["canonical_ports"])
    assert any(port["port"] == 11191 for port in eventing["canonical_ports"])


def test_global_domain_lanes_cover_tmn_service_clusters(server):
    community = server.global_systems.describe("community", modules=["CMPLXUNI", "CMPLX-TMN-main"])
    economy = server.global_systems.describe("economy", modules=["CMPLX-TMN-main"])
    validation = server.global_systems.describe("validation", modules=["CMPLX-TMN-main"])
    synthesis = server.global_systems.describe("synthesis", modules=["CMPLX-TMN-main"])
    simulation = server.global_systems.describe("simulation", modules=["CMPLXUNI", "CMPLX-TMN-main"])

    assert community["route_count"] >= 1
    assert economy["route_count"] >= 1
    assert validation["route_count"] >= 1
    assert synthesis["route_count"] >= 1
    assert simulation["route_count"] >= 1
    assert any(port["port"] == 11001 for port in community["canonical_ports"])
    assert any(port["port"] == 11090 for port in economy["canonical_ports"])
    assert any(port["port"] == 11196 for port in validation["canonical_ports"])
    assert any(port["port"] == 11202 for port in synthesis["canonical_ports"])
    assert any(port["port"] == 11081 for port in simulation["canonical_ports"])


def test_global_port_reassignment_plan_keeps_repo_kernel_as_control_layer(server):
    plan = server.global_systems.port_reassignment_plan(modules=["CMPLXUNI", "CMPLX-TMN-main"])

    assert plan["control_layer"]["service"] == "repo-kernel"
    assert plan["control_layer"]["public_port"] == 8786
    assert plan["system_count"] == len(server.global_systems.SYSTEMS)
    assert any(system["public_control_endpoint"] == "/api/global/memory" for system in plan["systems"])
    assert plan["phases"][0]["name"] == "freeze current evidence"
    assert "do not change host ports" in plan["policy"]["no_bulk_port_moves"]


def test_global_runtime_slice_plan_ranks_live_upstreams_before_port_moves(server):
    plan = server.global_systems.runtime_slice_plan(
        modules=["CMPLXUNI", "CMPLX-TMN-main"],
        check_health=False,
        limit=5,
    )

    assert plan["control_layer"]["service"] == "repo-kernel"
    assert plan["health_checked"] is False
    assert plan["recommendations"]
    assert any(item["system"] == "memory" for item in plan["recommendations"])
    assert all(item["control_endpoint"].startswith("/api/global/") for item in plan["recommendations"])
    assert any(step["action"] for step in plan["next_best_steps"])
    memory = next(item for item in plan["recommendations"] if item["system"] == "memory")
    assert memory["live_upstream_count"] >= 1
    assert memory["status"] == "candidate_needs_health_check"
    assert "defer host port edits" in memory["port_move_policy"]


def test_global_runtime_slice_plan_accepts_health_report_shape(server, monkeypatch):
    def fake_health_check_targets(targets, timeout_seconds=1.5, limit=80):
        return {
            "checks": [
                {
                    "module": target.get("module"),
                    "service": target.get("service"),
                    "ok": True,
                    "status": 200,
                }
                for target in targets[:limit]
            ],
            "truncated": False,
        }

    monkeypatch.setattr(server.global_systems.topology, "health_check_targets", fake_health_check_targets)

    plan = server.global_systems.runtime_slice_plan(
        modules=["CMPLXUNI", "CMPLX-TMN-main"],
        check_health=True,
        timeout_seconds=0.2,
        limit=5,
    )

    memory = next(item for item in plan["recommendations"] if item["system"] == "memory")
    assert memory["status"] == "ready_for_control_route"
    assert memory["healthy_upstream_count"] == memory["live_upstream_count"]
    assert memory["health"]["truncated"] is False


def test_global_tool_workbook_lists_live_tools_needs_and_usage_rules(server):
    workbook = server.global_systems.tool_workbook(check_health=False)

    assert workbook["workbook"] == "global-live-tool-workbook"
    assert workbook["control_layer"]["service"] == "repo-kernel"
    systems = {item["system"] for item in workbook["routed_systems"]}
    assert {"memory", "geometry", "operations", "knowledge"}.issubset(systems)
    assert any(tool["system"] == "memory" and tool["service"] == "pocket-memory-api" for tool in workbook["available_live_tools"])
    assert any(tool["system"] == "knowledge" and tool["service"] == "db-aggregator-api" for tool in workbook["available_live_tools"])
    assert any(tool.get("capability") == "devkit-ingest" for tool in workbook["named_capabilities"])
    assert any(tool.get("capability") == "mcp-local-os" for tool in workbook["named_capabilities"])
    assert any(tool.get("capability") == "octa64" for tool in workbook["named_capabilities"])
    assert any(tool.get("capability") == "mcp-os-validation" for tool in workbook["named_capabilities"])
    assert any(tool.get("capability") == "cqe-modular" for tool in workbook["named_capabilities"])
    assert any(need["area"] == "global_query_fanout" for need in workbook["api_layer_needs"])
    assert any(item["path"].startswith("/api/global/query") for item in workbook["quick_use"])
    assert any(item["path"] == "/api/global/knowledge/devkit-ingest" for item in workbook["quick_use"])
    assert any(item["path"] == "/api/global/mcp/local-os" for item in workbook["quick_use"])
    assert any(item["path"] == "/api/global/code-execution/octa64" for item in workbook["quick_use"])
    assert any("403" in rule for rule in workbook["use_rules"])


def test_global_compact_state_summarizes_without_full_coverage_scan(server):
    state = server.global_systems.compact_state(check_health=False)

    assert state["state"] == "global-control-compact"
    assert state["control_layer"]["service"] == "repo-kernel"
    assert state["summary"]["routed_system_count"] >= 8
    assert any(item["system"] == "memory" for item in state["routed_systems"])
    assert any(item["system"] == "ai-runtime" for item in state["routed_systems"])
    assert "ai-runtime" not in state["next_routing_candidates"]
    assert state["fast_paths"]["query"] == "/api/global/query?q=<term>"


def test_global_query_dry_run_lists_fanout_calls(server):
    result = server.global_systems.global_query(
        server.GlobalQueryRequest(q="receipt", systems=["memory", "knowledge"], dry_run=True)
    )

    assert result["dry_run"] is True
    assert result["systems"] == ["memory", "knowledge"]
    assert any(item["system"] == "memory" for item in result["planned_calls"])
    assert "not executed" in result["execution"]


def test_global_query_fanout_normalizes_results(server, monkeypatch):
    def fake_memory_search(q, service="pocket-memory-api", limit=20):
        return {
            "system": "memory",
            "service": service,
            "data": {
                "matches": [
                    {
                        "table": "ability_map",
                        "column": "capability_name",
                        "row": {
                            "id": 1,
                            "capability_name": "receipt_tracking",
                            "implementation": "receipt tracking summary",
                            "file_refs": "[\"repo/path.py\"]",
                            "confidence": 0.9,
                        },
                    },
                    {
                        "table": "ability_map",
                        "column": "implementation",
                        "row": {
                            "id": 1,
                            "capability_name": "receipt_tracking",
                            "implementation": "receipt tracking summary with more detail",
                            "file_refs": "[\"repo/path.py\"]",
                            "confidence": 0.7,
                        },
                    }
                ]
            },
        }

    def fake_knowledge_search(q, service="db-aggregator-api", limit=20):
        return {
            "system": "knowledge",
            "service": service,
            "data": {
                "sources": [
                    {
                        "artifact_kind": "doc_text",
                        "relative_path": "code-reports/adapter/report.md",
                        "size_bytes": 100,
                    }
                ]
            },
        }

    def fake_geometry_read(service, path="", query=None):
        if service == "tarpit-api":
            return {"system": "geometry", "service": service, "data": {"atoms": 2, "top_labels": {"receipt": 2}, "sources": {}}}
        return {"system": "geometry", "service": service, "data": {"systems": 3, "sources_present": 3, "by_kind": {"adapter": 1}}}

    def fake_operations_read(service, path="", query=None):
        return {"system": "operations", "service": service, "data": {"ok": True, "kernel": "cmplx-repo-kernel", "module_count": 12}}

    monkeypatch.setattr(server.global_systems, "memory_search", fake_memory_search)
    monkeypatch.setattr(server.global_systems, "knowledge_search", fake_knowledge_search)
    monkeypatch.setattr(server.global_systems, "geometry_read_proxy", fake_geometry_read)
    monkeypatch.setattr(server.global_systems, "operations_read_proxy", fake_operations_read)

    result = server.global_systems.global_query(server.GlobalQueryRequest(q="receipt", limit=10))

    assert result["dry_run"] is False
    assert result["schema_version"] == 2
    assert result["result_count"] >= 2
    memory_results = [item for item in result["results"] if item["system"] == "memory" and item["title"] == "receipt_tracking"]
    assert len(memory_results) == 1
    assert memory_results[0]["id"]
    assert memory_results[0]["score"] > 0
    assert memory_results[0]["summary"] == "receipt tracking summary with more detail"
    assert memory_results[0]["local_refs"] == ["repo/path.py"]
    assert "raw" in memory_results[0]
    assert any(item["system"] == "knowledge" for item in result["results"])
    assert any(item["system"] == "operations" for item in result["context"])


def test_global_query_ranks_title_hits_before_context(server):
    records = [
        server.global_systems._canonical_query_record(
            system="geometry",
            source="tarpit-api",
            kind="context",
            title="40 tarpit atoms",
            matched_field="context",
            summary="general geometry context",
            confidence=None,
            local_refs=[],
            payload={},
        ),
        server.global_systems._canonical_query_record(
            system="knowledge",
            source="db-aggregator-api",
            kind="doc_text",
            title="adapter report",
            matched_field="source",
            summary="adapter reference",
            confidence=None,
            local_refs=["reports/adapter.md"],
            payload={},
        ),
    ]

    ranked = server.global_systems._rank_global_query_records(records, "adapter")

    assert ranked[0]["system"] == "knowledge"
    assert ranked[0]["score"] > ranked[1]["score"]
