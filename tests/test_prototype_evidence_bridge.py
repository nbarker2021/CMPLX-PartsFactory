from pathlib import Path


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_prototype_evidence_bridge_summarizes_docs_bridges_and_csvs(server, tmp_path):
    root = tmp_path / "Unification Prototypes"
    _write(root / "CLAIMS_VS_CODE.md", "# Claims\n")
    _write(root / "STACKS.md", "# Stacks\n")
    _write(root / "_scripts" / "inventory.csv", "path,sha\none.py,abc\n")
    _write(root / "_scripts" / "bridge_files.csv", "pair,path\ncmplx_tmn,a.py\ncmplx_tmn,b.py\n")
    _write(root / "bridges" / "cmplx_tmn" / "a.py", "def a(): pass\n")
    _write(root / "bridges" / "cmplx_tmn" / "b.py", "def b(): pass\n")
    _write(root / "tools" / "cmplx" / "docs" / "capability.md", "# Capability\n")
    _write(root / "tools" / "cmplx" / "api.py", "# generated wrapper\n")

    bridge = server.PrototypeEvidenceBridge([root])
    overview = bridge.overview()

    assert overview["status"] == "ready"
    assert any(doc["path"] == "CLAIMS_VS_CODE.md" and doc["exists"] for doc in overview["root_docs"])
    assert any(csv["path"] == "_scripts/bridge_files.csv" and csv["rows"] == 2 for csv in overview["csvs"])
    assert overview["bridges"]["file_count"] == 2
    assert overview["docs_harvest"]["doc_count"] == 1
    assert overview["superseded_wrappers"]["status"] == "superseded-by-module-adapter"
    assert any(need["area"] == "knowledge_claims_lane" for need in overview["api_layer_needs"])


def test_prototype_evidence_search_returns_claim_and_doc_matches(server, tmp_path):
    root = tmp_path / "Unification Prototypes"
    _write(root / "_scripts" / "phase5_claims_detail.csv", "tool,doc,token,status,backed_in\ncmplx,tools/cmplx/docs/capability.md,AdapterKernel,backed_own,cmplx.adapter\n")
    _write(root / "tools" / "cmplx" / "docs" / "capability.md", "# Capability\nAdapterKernel routes prototype claims into knowledge.\n")
    _write(root / "STACKS.md", "# Stacks\nAdapterKernel appears in historical compose notes.\n")
    bridge = server.PrototypeEvidenceBridge([root])

    result = bridge.search("AdapterKernel", limit=10)

    matches = result["data"]["matches"]
    assert result["query"] == "AdapterKernel"
    assert any(match["kind"] == "prototype_claim_token" for match in matches)
    assert any(match["kind"] == "prototype_doc_claim" for match in matches)
    assert any(match["kind"] == "prototype_root_doc" for match in matches)
    assert any(match["confidence"] == 1.0 for match in matches)


def test_prototype_evidence_read_blocks_path_escape(server, tmp_path):
    root = tmp_path / "Unification Prototypes"
    _write(root / "STACKS.md", "# Stacks\n")
    bridge = server.PrototypeEvidenceBridge([root])

    content = bridge.read(server.PrototypeEvidenceReadRequest(path="STACKS.md"))
    assert content["path"] == "STACKS.md"
    assert "Stacks" in content["content"]

    try:
        bridge.read(server.PrototypeEvidenceReadRequest(path="../outside.md"))
    except server.HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("expected prototype evidence path escape to be blocked")


def test_prototype_evidence_routes_are_registered(server):
    paths = {route.path for route in server.app.routes}

    assert "/api/prototype-evidence" in paths
    assert "/api/prototype-evidence/docs" in paths
    assert "/api/prototype-evidence/bridges" in paths
    assert "/api/prototype-evidence/search" in paths
    assert "/api/prototype-evidence/read" in paths
    assert "/api/global/knowledge/prototype-claims" in paths


def test_global_query_includes_prototype_claims_when_knowledge_is_selected(server, tmp_path):
    root = tmp_path / "Unification Prototypes"
    _write(root / "_scripts" / "phase5_claims_detail.csv", "tool,doc,token,status,backed_in\ncmplx,tools/cmplx/docs/capability.md,AdapterKernel,backed_own,cmplx.adapter\n")
    controller = server.global_systems
    original = controller.prototype_evidence
    controller.prototype_evidence = server.PrototypeEvidenceBridge([root])
    try:
        result = controller.global_query(server.GlobalQueryRequest(q="AdapterKernel", systems=["knowledge"], limit=10))
    finally:
        controller.prototype_evidence = original

    assert any(item["source"] == "claude-unification-prototypes" for item in result["results"])
    assert any("prototype" in str(item["kind"]) for item in result["results"])
