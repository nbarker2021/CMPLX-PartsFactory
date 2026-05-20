"""Run repo-kernel capability probes and persist a promotion-cycle report."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MODULES = ["CMPLXUNI", "CMPLX-TMN-main", "CMPLXMCP"]


def post_json(url: str, payload: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{exc.code} from {url}: {body}") from exc


def get_json(url: str, timeout: int = 120) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{exc.code} from {url}: {body}") from exc


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plans = payload.get("promotion_plan", {}).get("plans", [])
    lines = [
        "# Repo Kernel Promotion Cycle",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Summary",
        "",
        "| Module | Status | Readiness | Capabilities |",
        "| --- | --- | ---: | --- |",
    ]
    for plan in plans:
        probe = plan.get("probe") or {}
        score = (probe.get("score") or {}).get("readiness", 0)
        capabilities = ", ".join(probe.get("capabilities") or [])
        lines.append(f"| `{plan['module']}` | {probe.get('status')} | {score} | {capabilities} |")

    surfaces = payload.get("surfaces", {})
    lines.extend(["", "## Surface Catalog", "", "| Module | FastAPI Routes | MCP Tools | Next.js Routes | Skipped |", "| --- | ---: | ---: | ---: | ---: |"])
    for module, surface in surfaces.items():
        summary = surface.get("summary") or {}
        lines.append(
            f"| `{module}` | {summary.get('route_count', 0)} | {summary.get('mcp_tool_count', 0)} | "
            f"{summary.get('nextjs_route_count', 0)} | {summary.get('skipped_count', 0)} |"
        )

    lines.extend(["", "## Actions", ""])
    for plan in plans:
        lines.append(f"### {plan['module']}")
        lines.append("")
        for action in plan.get("actions", []):
            lines.append(f"- `{action['phase']}`: {action['action']}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repo-kernel promotion probes")
    parser.add_argument("--base-url", default="http://localhost:8786")
    parser.add_argument("--module", action="append", dest="modules")
    parser.add_argument("--goal", default="first promotion cycle")
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    args = parser.parse_args()

    modules = args.modules or DEFAULT_MODULES
    payload = {"modules": modules, "goal": args.goal}
    probe = post_json(f"{args.base_url}/api/controller/probe", payload)
    promotion_plan = post_json(f"{args.base_url}/api/controller/promotion-plan", payload)
    surfaces = {
        module: get_json(f"{args.base_url}/api/adapters/{module}/surfaces?limit=1000")
        for module in modules
    }
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "modules": modules,
        "probe": probe,
        "promotion_plan": promotion_plan,
        "surfaces": surfaces,
    }

    json_path = Path(f"reports/repo_kernel_promotion_cycle_{args.date}.json")
    md_path = Path(f"docs/REPO_KERNEL_PROMOTION_CYCLE_{args.date}.md")
    write_json(json_path, output)
    write_markdown(md_path, output)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
