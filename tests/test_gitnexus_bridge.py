import sqlite3


def _make_gitnexus_db(path):
    conn = sqlite3.connect(path)
    conn.execute(
        """
        create table gitnexus_reports (
            report_id text primary key,
            name text,
            source_path text,
            source_id text,
            system text,
            language text,
            file_size text,
            implement_status text,
            confidence text,
            capability_summary text
        )
        """
    )
    conn.executemany(
        """
        insert into gitnexus_reports (
            report_id, name, source_path, source_id, system, language, file_size,
            implement_status, confidence, capability_summary
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("r1", "memory_api", "systems/memory/api.py", "s1", "cmplx-tmn1", "python", "4 KB", "evidence", "claim", "Memory route evidence"),
            ("r2", "memory_api", "cqe/memory.c", "s2", "cqe", "c", "8 KB", "evidence", "claim", "CQE memory implementation evidence"),
            ("r3", "geometry_kernel", "geo/kernel.py", "s3", "aletheia", "python", "3 KB", "evidence", "claim", "Geometry capability evidence"),
        ],
    )
    conn.commit()
    conn.close()


def test_gitnexus_bridge_summarizes_local_aggregate(server, tmp_path):
    db = tmp_path / "gitnexus.sqlite"
    _make_gitnexus_db(db)
    bridge = server.GitNexusBridge(api_base="http://gitnexus.example", aggregate_db=db, meta_path=tmp_path / "missing.json")

    summary = bridge.aggregate_summary()

    assert summary["status"] == "ready"
    assert summary["total_reports"] == 3
    assert summary["by_system"][0]["value"] in {"aletheia", "cmplx-tmn1", "cqe"}
    assert summary["shared_names"][0]["name"] == "memory_api"
    assert summary["shared_names"][0]["system_count"] == 2


def test_gitnexus_bridge_searches_historical_reports(server, tmp_path):
    db = tmp_path / "gitnexus.sqlite"
    _make_gitnexus_db(db)
    bridge = server.GitNexusBridge(api_base="http://gitnexus.example", aggregate_db=db, meta_path=tmp_path / "missing.json")

    result = bridge.aggregate_search(q="memory", limit=10)

    assert result["result_count"] == 2
    assert {item["system"] for item in result["results"]} == {"cmplx-tmn1", "cqe"}
    assert result["policy"].startswith("read-only")


def test_gitnexus_bridge_builds_unification_hints(server, tmp_path):
    db = tmp_path / "gitnexus.sqlite"
    _make_gitnexus_db(db)
    bridge = server.GitNexusBridge(api_base="http://gitnexus.example", aggregate_db=db, meta_path=tmp_path / "missing.json")
    bridge.repos = lambda limit=200: {
        "repos": [
            {"name": "rk-cmplxuni", "path": "/repos/CMPLXUNI", "indexedAt": "now", "stats": {"nodes": 100, "processes": 2, "communities": 3, "files": 10}},
            {"name": "cmplx-partsfactory-root", "path": "/root", "indexedAt": "now", "stats": {"nodes": 50, "processes": 1, "communities": 1, "files": 5}},
        ]
    }

    hints = bridge.unification_hints(limit=5)

    assert hints["status"] == "ready"
    assert hints["top_repo_hints"][0]["repo"] == "rk-cmplxuni"
    assert hints["shared_historical_names"][0]["name"] == "memory_api"
    assert hints["recommended_work"][0]["lane"] == "large_surface_adapter_review"


def test_adapter_registry_joins_gitnexus_hints_to_modules(server):
    class FakeGitNexus:
        def unification_hints(self, limit=25):
            return {
                "status": "ready",
                "top_repo_hints": [
                    {
                        "repo": "rk-cmplxdevkit",
                        "role": "clean_repo_checkout",
                        "path": "/repos/CMPLXDevKit",
                        "stats": {"files": 4979, "nodes": 220727, "edges": 320531, "communities": 3478, "processes": 299},
                        "priority_score": 264477,
                    },
                    {
                        "repo": "rk-cmplxuni",
                        "role": "clean_repo_checkout",
                        "path": "/repos/CMPLXUNI",
                        "stats": {"files": 2869, "nodes": 143285, "edges": 213079, "communities": 2295, "processes": 300, "routes": 135, "tools": 14},
                        "priority_score": 175235,
                    },
                ],
                "shared_historical_names": [{"name": "main", "system_count": 3}],
                "recommended_work": [],
            }

    worklist = server.adapter_registry.unification_worklist(gitnexus=FakeGitNexus(), limit=10)
    modules = {item["module"]: item for item in worklist["top_modules"]}

    assert worklist["summary"]["hint_status"] == "ready"
    assert modules["CMPLXDevKit"]["gitnexus_alias"] == "rk-cmplxdevkit"
    assert modules["CMPLXDevKit"]["next_action"]["lane"] == "slice_filter_before_adapter"
    assert modules["CMPLXUNI"]["next_action"]["lane"] == "adapter_ready_candidate"
    assert worklist["recommended_work"][1]["lane"] == "slice_filtering"


def test_adapter_registry_suggests_bounded_slices_for_devkit(server):
    result = server.adapter_registry.slice_candidates("CMPLXDevKit", gitnexus=None, limit=20)
    candidates = {item["path"]: item for item in result["candidates"]}

    assert result["module"] == "CMPLXDevKit"
    assert "src/octa64" in candidates
    assert candidates["src/octa64"]["classification"]["lane"] == "code_execution_runtime_slice"
    assert "src/cqe_organized" in candidates
    assert candidates["src/cqe_organized"]["classification"]["lane"] == "quarantine_external_or_vendor"


def test_adapter_registry_builds_slice_candidate_matrix(server):
    matrix = server.adapter_registry.slice_candidate_matrix(gitnexus=None, modules=["CMPLXDevKit"], limit_per_module=8)
    systems = {item["system"]: item for item in matrix["systems"]}

    assert matrix["matrix"] == "slice-candidate-matrix"
    assert "code-execution" in systems
    assert "validation" in systems
    assert matrix["recommended_next_intakes"]
    assert matrix["recommended_next_intakes"][0]["intake_plan"].startswith("/api/adapters/")


def test_adapter_registry_builds_slice_intake_plan(server):
    plan = server.adapter_registry.slice_intake_plan("CMPLXDevKit", "src/octa64", gitnexus=None)

    assert plan["plan"] == "slice-intake-plan"
    assert plan["target_system"] == "code-execution"
    assert plan["canonical_base"] == "/api/global/code-execution"
    assert any(route["path"].startswith("/api/global/code-execution/slices/") for route in plan["proposed_routes"])
    assert plan["controller_changes"][0]["step"] == "catalog"


def test_adapter_registry_exposes_canonical_slices(server):
    registry = server.adapter_registry.canonical_slice_registry(gitnexus=None, system="code-execution", modules=["CMPLXDevKit"])

    assert registry["registry"] == "canonical-slice-registry"
    assert registry["slice_count"] >= 1
    first = registry["slices"][0]
    assert first["system"] == "code-execution"
    assert first["canonical_routes"]["summary"].startswith("/api/global/code-execution/slices/")

    detail = server.adapter_registry.canonical_slice("code-execution", first["route_id"], gitnexus=None)
    assert detail["slice"]["route_id"] == first["route_id"]
    tree = server.adapter_registry.canonical_slice_tree("code-execution", first["route_id"], gitnexus=None, max_depth=1, limit=20)
    assert tree["slice"]["module"] == "CMPLXDevKit"
    plan = server.adapter_registry.canonical_slice_call_plan(
        "code-execution",
        first["route_id"],
        server.GlobalSystemCallPlanRequest(operation="tool", name="run_graph", dry_run=True),
        gitnexus=None,
    )
    assert "not executed" in plan["execution"]


def test_octa64_named_capability_is_read_only(server):
    summary = server.adapter_registry.octa64_capability(gitnexus=None)

    assert summary["capability"] == "octa64"
    assert summary["source"]["module"] == "CMPLXDevKit"
    assert summary["source"]["path"] == "src/octa64"
    assert summary["activation_state"]["execution"] == "disabled"
    assert "PARITY_CHECK" in summary["vm_opcodes"]
    assert summary["known_issues"][0]["area"] == "entrypoint_import"

    file_result = server.adapter_registry.octa64_read_file("pack.py")
    assert file_result["data"]["path"] == "src/octa64/pack.py"
    assert "class Pack" in file_result["data"]["content"]

    plan = server.adapter_registry.octa64_call_plan(
        server.GlobalSystemCallPlanRequest(operation="tool", name="run_graph", dry_run=True)
    )
    assert plan["known_operation"] is True
    assert "not executed" in plan["execution"]
    assert plan["policy"]["execute"] == "blocked"

    try:
        server.adapter_registry.octa64_read_file("../README.md")
    except server.HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("expected octa64 file allowlist to block traversal")


def test_mcp_os_validation_named_capability_is_read_only(server):
    summary = server.adapter_registry.mcp_os_validation_capability(gitnexus=None)

    assert summary["capability"] == "mcp-os-validation"
    assert summary["system"] == "validation"
    assert summary["source"]["module"] == "CMPLXDevKit"
    assert summary["source"]["path"] == "CMPLXLOCALMCP/mcp_os/validation"
    assert summary["activation_state"]["execution"] == "disabled"
    assert any(suite["suite"] == "mcp_tools" for suite in summary["suite_catalog"])
    assert {issue["area"] for issue in summary["known_issues"]} >= {"missing_symbol", "cli_branch", "benchmarks"}

    file_result = server.adapter_registry.mcp_os_validation_read_file("system_validator.py")
    assert file_result["data"]["path"] == "CMPLXLOCALMCP/mcp_os/validation/system_validator.py"
    assert "class ValidationSuite" in file_result["data"]["content"]

    plan = server.adapter_registry.mcp_os_validation_call_plan(
        server.GlobalSystemCallPlanRequest(operation="tool", name="validate_mcp_tools", dry_run=True)
    )
    assert plan["known_operation"] is True
    assert "not executed" in plan["execution"]
    assert plan["policy"]["execute"] == "blocked"

    try:
        server.adapter_registry.mcp_os_validation_read_file("../runner.py")
    except server.HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("expected validation file allowlist to block traversal")


def test_cqe_modular_named_capability_is_read_only(server):
    summary = server.adapter_registry.cqe_modular_capability(gitnexus=None)

    assert summary["capability"] == "cqe-modular"
    assert summary["system"] == "synthesis"
    assert summary["source"]["module"] == "CMPLXDevKit"
    assert summary["source"]["path"] == "src/cqe_modular_atomic"
    assert summary["activation_state"]["execution"] == "disabled"
    assert any(module["name"] == "BraidComposer" for module in summary["module_catalog"])
    assert {issue["area"] for issue in summary["known_issues"]} >= {"import_path", "determinism"}

    file_result = server.adapter_registry.cqe_modular_read_file("cqe_sdk.py")
    assert file_result["data"]["path"] == "src/cqe_modular_atomic/cqe_sdk.py"
    assert "class Pack" in file_result["data"]["content"]

    plan = server.adapter_registry.cqe_modular_call_plan(
        server.GlobalSystemCallPlanRequest(operation="tool", name="run_once", arguments={"prompt": "hello"}, dry_run=True)
    )
    assert plan["known_operation"] is True
    assert "not executed" in plan["execution"]
    assert plan["policy"]["execute"] == "blocked"

    try:
        server.adapter_registry.cqe_modular_read_file("../cqe_sdk.py")
    except server.HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("expected cqe-modular file allowlist to block traversal")


def test_devkit_ingest_named_capability_is_read_only(server):
    summary = server.adapter_registry.devkit_ingest_capability(gitnexus=None)

    assert summary["capability"] == "devkit-ingest"
    assert summary["system"] == "knowledge"
    assert summary["source"]["module"] == "CMPLXDevKit"
    assert summary["source"]["path"] == "devkit"
    assert summary["activation_state"]["execution"] == "disabled"
    assert any(tool["name"] == "ocr_image_to_text" for tool in summary["tool_catalog"])
    assert {issue["area"] for issue in summary["known_issues"]} >= {"write_path", "optional_dependencies", "historical_paths"}

    file_result = server.adapter_registry.devkit_ingest_read_file("ingest/embed_and_index.py")
    assert file_result["data"]["path"] == "devkit/ingest/embed_and_index.py"
    assert "def embed_texts_stub" in file_result["data"]["content"]

    plan = server.adapter_registry.devkit_ingest_call_plan(
        server.GlobalSystemCallPlanRequest(operation="tool", name="ocr_image_to_text", arguments={"image_path": "scan.png"}, dry_run=True)
    )
    assert plan["known_operation"] is True
    assert "not executed" in plan["execution"]
    assert plan["policy"]["write"] == "blocked"

    try:
        server.adapter_registry.devkit_ingest_read_file("../ingest/ocr_pipeline.py")
    except server.HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("expected devkit-ingest file allowlist to block traversal")


def test_mcp_local_os_named_capability_is_read_only(server):
    summary = server.adapter_registry.mcp_local_os_capability(gitnexus=None)

    assert summary["capability"] == "mcp-local-os"
    assert summary["system"] == "mcp"
    assert summary["source"]["module"] == "CMPLXDevKit"
    assert summary["source"]["path"] == "CMPLXLOCALMCP/mcp_os"
    assert summary["activation_state"]["execution"] == "disabled"
    assert any(layer["layer"] == "layer2_geometric" for layer in summary["mcp_tool_layers"])
    assert {issue["area"] for issue in summary["known_issues"]} >= {"missing_dependency", "missing_import", "runtime_side_effects"}

    file_result = server.adapter_registry.mcp_local_os_read_file("server/server.py")
    assert file_result["data"]["path"] == "CMPLXLOCALMCP/mcp_os/server/server.py"
    assert "class CMPLXMCPServer" in file_result["data"]["content"]

    plan = server.adapter_registry.mcp_local_os_call_plan(
        server.GlobalSystemCallPlanRequest(operation="tool", name="list_tools", dry_run=True)
    )
    assert plan["known_operation"] is True
    assert "not executed" in plan["execution"]
    assert plan["policy"]["execute"] == "blocked"

    try:
        server.adapter_registry.mcp_local_os_read_file("../README.md")
    except server.HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("expected mcp-local-os file allowlist to block traversal")


def test_global_query_normalizes_gitnexus_reports(server, tmp_path):
    db = tmp_path / "gitnexus.sqlite"
    _make_gitnexus_db(db)
    bridge = server.GitNexusBridge(api_base="http://gitnexus.example", aggregate_db=db, meta_path=tmp_path / "missing.json")
    payload = bridge.aggregate_search(q="memory", limit=2)

    normalized = server.global_systems._normalize_global_query_result(
        "gitnexus_reports",
        payload,
        server.GlobalQueryRequest(q="memory", limit=2),
    )

    assert len(normalized["results"]) == 2
    assert normalized["results"][0]["source"] == "gitnexus-aggregate-db"
    assert normalized["results"][0]["kind"] == "historical_report"


def test_gitnexus_bridge_blocks_write_cypher(server):
    bridge = server.GitNexusBridge(api_base="http://gitnexus.example")

    try:
        bridge._validate_read_cypher("MATCH (n) DETACH DELETE n")
    except server.HTTPException as exc:
        assert exc.status_code == 403
        assert "read-only" in exc.detail
    else:
        raise AssertionError("expected write Cypher to be blocked")


def test_gitnexus_routes_are_registered(server):
    paths = {route.path for route in server.app.routes}

    assert "/api/gitnexus/status" in paths
    assert "/api/gitnexus/repos" in paths
    assert "/api/gitnexus/repos/{repo}" in paths
    assert "/api/gitnexus/graph-summary" in paths
    assert "/api/gitnexus/unification-hints" in paths
    assert "/api/gitnexus/repo-unification-worklist" in paths
    assert "/api/gitnexus/slice-candidates" in paths
    assert "/api/gitnexus/slice-candidate-matrix" in paths
    assert "/api/gitnexus/slice-intake-plan" in paths
    assert "/api/repo-unification-worklist" in paths
    assert "/api/slice-candidate-matrix" in paths
    assert "/api/global/{system}/slices" in paths
    assert "/api/global/{system}/slices/{slice_id}" in paths
    assert "/api/global/{system}/slices/{slice_id}/tree" in paths
    assert "/api/global/{system}/slices/{slice_id}/call-plan" in paths
    assert "/api/global/code-execution/octa64" in paths
    assert "/api/global/code-execution/octa64/tree" in paths
    assert "/api/global/code-execution/octa64/files/{path:path}" in paths
    assert "/api/global/code-execution/octa64/call-plan" in paths
    assert "/api/global/validation/mcp-os" in paths
    assert "/api/global/validation/mcp-os/tree" in paths
    assert "/api/global/validation/mcp-os/files/{path:path}" in paths
    assert "/api/global/validation/mcp-os/call-plan" in paths
    assert "/api/global/synthesis/cqe-modular" in paths
    assert "/api/global/synthesis/cqe-modular/tree" in paths
    assert "/api/global/synthesis/cqe-modular/files/{path:path}" in paths
    assert "/api/global/synthesis/cqe-modular/call-plan" in paths
    assert "/api/global/knowledge/devkit-ingest" in paths
    assert "/api/global/knowledge/devkit-ingest/tree" in paths
    assert "/api/global/knowledge/devkit-ingest/files/{path:path}" in paths
    assert "/api/global/knowledge/devkit-ingest/call-plan" in paths
    assert "/api/global/mcp/local-os" in paths
    assert "/api/global/mcp/local-os/tree" in paths
    assert "/api/global/mcp/local-os/files/{path:path}" in paths
    assert "/api/global/mcp/local-os/call-plan" in paths
    assert "/api/adapters/{name}/slice-candidates" in paths
    assert "/api/adapters/{name}/slice-intake-plan" in paths
    assert "/api/gitnexus/grep" in paths
    assert "/api/gitnexus/aggregate" in paths
    assert "/api/gitnexus/aggregate/search" in paths


def test_operations_contract_allows_safe_gitnexus_info_but_blocks_mutation(server):
    contract = server.global_systems.operations_routing_contract(check_health=False)
    gitnexus = next(upstream for upstream in contract["upstreams"] if upstream["name"] == "gitnexus-rebuild-server")

    assert "/api/info" in gitnexus["read_paths"]
    assert "/api/repos" in gitnexus["read_paths"]
    assert not server.global_systems._operations_path_allowed("gitnexus-rebuild-server", "/api/analyze")
