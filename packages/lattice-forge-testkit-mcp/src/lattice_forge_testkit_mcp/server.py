"""FastAPI + MCP SSE for lattice-forge non-proven test toolkit."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

MCP_NAME = os.environ.get("FASTMCP_INSTANCE", "lattice-forge-testkit")
ROOT = Path(os.environ.get("PROOF_LAB_ROOT", Path.cwd()))
PKG = ROOT / "packages" / "lattice-forge"

mcp = FastMCP(
    MCP_NAME,
    instructions=(
        "Toolkit for NON-PROVEN lattice-forge items: CONJ claims, Tier B falsify, pytest subsets. "
        "Do not treat tool output as proof promotion; use Proof Lab / lattice-forge for formal PROVEN runs."
    ),
)

app = FastAPI(title="Lattice Forge Testkit MCP", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("TESTKIT_CORS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _run(cmd: list[str], *, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
    )
    return json.dumps(
        {"exit_code": proc.returncode, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-4000:]},
        indent=2,
    )


@mcp.tool()
def list_nonproven_claims() -> str:
    """List claims whose honesty_label is not in the proven library surface (e.g. CONJ)."""
    from lattice_forge_testkit_mcp.registry_io import filter_nonproven, load_claims

    rows = filter_nonproven(load_claims())
    return json.dumps(rows, indent=2)


@mcp.tool()
def list_proven_claim_ids() -> str:
    """List claim_ids on the proven library surface (for cross-check only)."""
    from lattice_forge_testkit_mcp.registry_io import PROVEN_LABELS, load_claims

    rows = [c for c in load_claims() if c.get("honesty_label") in PROVEN_LABELS]
    return json.dumps([c.get("claim_id") for c in rows], indent=2)


@mcp.tool()
def run_falsify_tier_b(quick: bool = True, max_depth: int = 128) -> str:
    """Run lattice-forge falsify --tier-b (non-blocking exploration report)."""
    cmd = ["lattice-forge", "falsify", "--tier-b", "--max-depth", str(max_depth)]
    if quick:
        cmd.append("--quick")
    return _run(cmd)


@mcp.tool()
def run_pytest_subset(markers: str = "", paths: str = "packages/lattice-forge/tests") -> str:
    """Run pytest on a path list (space-separated under repo root). Optional -k expression via markers."""
    parts = [p for p in paths.split() if p]
    cmd = ["python", "-m", "pytest", *parts, "-q", "--tb=short"]
    if markers.strip():
        cmd.extend(["-k", markers.strip()])
    return _run(cmd)


@mcp.tool()
def read_proof_artifact(name: str = "proofs_report.json") -> str:
    """Read a package proof artifact (does not run proofs). Allowed: proofs_report.json, expected_outputs.json."""
    allowed = {"proofs_report.json", "expected_outputs.json", "expected_outputs_umbrella.json"}
    if name not in allowed:
        return json.dumps({"error": f"name must be one of {sorted(allowed)}"})
    path = PKG / name
    if not path.is_file():
        return json.dumps({"error": f"missing {path}"})
    return path.read_text(encoding="utf-8")


@mcp.tool()
def run_empirical_platform(claim_id: str, mode: str = "quick") -> str:
    """Run exhaustive empirical platform for one claim (depth ladder per honesty label)."""
    from lattice_forge.empirical.runner import run_claim_platform

    row = run_claim_platform(claim_id, exhaustion_mode=mode)
    return json.dumps(row, indent=2)


@mcp.tool()
def run_empirical_matrix(mode: str = "quick") -> str:
    """Run all platforms in empirical/platforms.manifest.jsonl."""
    from lattice_forge.empirical.runner import run_empirical_matrix

    report = run_empirical_matrix(exhaustion_mode=mode)
    return json.dumps(report, indent=2)


@mcp.tool()
def materialize_empirical_platforms() -> str:
    """Rebuild platforms.manifest.jsonl from claims registry."""
    return _run(
        ["python", str(ROOT / "packages" / "lattice-forge" / "scripts" / "materialize_empirical_platforms.py")],
    )


@mcp.tool()
def run_regimes_proofs_quick() -> str:
    """Run regimes proof script --quick (ring-2; may include pass_with_open_gaps companions)."""
    out = PKG / "proofs_report_regimes.json"
    return _run(
        ["python", str(PKG / "scripts" / "run_regimes_proofs.py"), "--quick", "--output", str(out)],
        cwd=PKG,
    )


@app.get("/health")
async def health():
    return {"status": "ok", "mcp": MCP_NAME, "root": str(ROOT)}


app.mount("/mcp", mcp.sse_app())


def main():
    import uvicorn

    port = int(os.environ.get("TESTKIT_MCP_PORT", "8872"))
    uvicorn.run("lattice_forge_testkit_mcp.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
