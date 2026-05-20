"""Write a concise report for the repo-kernel unified workflow layer."""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_URL = "http://localhost:8786"
WORKFLOWS = ["memory", "mcp_tools", "agent_orchestration", "knowledge", "training", "geometry", "code_execution", "pipeline", "external_ai_portal"]


def get_json(path: str, timeout: int = 180) -> dict[str, Any]:
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(path: str, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    generated_at = datetime.now(timezone.utc).isoformat()
    topology = get_json("/api/runtime/topology")
    workflows = get_json("/api/unified/workflows")
    route_plans = {
        workflow: post_json(f"/api/unified/workflows/{workflow}/route-plan", {"goal": f"{workflow} workflow unification"})
        for workflow in WORKFLOWS
    }
    payload = {
        "generated_at": generated_at,
        "topology": topology,
        "workflows": workflows,
        "route_plans": route_plans,
    }

    json_path = Path("reports/repo_kernel_unified_workflows_2026-05-13.json")
    md_path = Path("docs/REPO_KERNEL_UNIFIED_WORKFLOWS_2026-05-13.md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Repo Kernel Unified Workflows",
        "",
        f"Generated: {generated_at}",
        "",
        "## Runtime Topology",
        "",
        "| Module | Runtime URLs | Compose Services | README Ports | Port Ranges |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for module in topology.get("modules", []):
        ranges = ", ".join(f"{r['start']}-{r['end']}" for r in module.get("readme_port_ranges", []))
        lines.append(
            f"| `{module['module']}` | {len(module.get('runtime_urls', []))} | "
            f"{len(module.get('compose_services', []))} | {len(module.get('readme_ports', []))} | {ranges or '-'} |"
        )

    lines.extend(["", "## Workflow Coverage", "", "| Workflow | Modules | Routes | MCP Tools | Runtime Targets |", "| --- | ---: | ---: | ---: | ---: |"])
    for workflow in workflows.get("workflows", []):
        routes = sum(item.get("routes", 0) for item in workflow.get("modules", []))
        tools = sum(item.get("mcp_tools", 0) for item in workflow.get("modules", []))
        targets = sum(item.get("runtime_targets", 0) for item in workflow.get("modules", []))
        lines.append(f"| `{workflow['workflow']}` | {workflow['module_count']} | {routes} | {tools} | {targets} |")

    lines.extend(["", "## First API Layer Recommendation", ""])
    lines.append("Start with `memory`, then `mcp_tools`, then `agent_orchestration`.")
    lines.append("")
    lines.append("The unified API should health-check documented runtime ports first, then fall back to static adapter surfaces when a repo service is not running.")
    lines.append("")
    lines.append("Do not call mutating endpoints automatically; require an explicit approved workflow before writes.")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
