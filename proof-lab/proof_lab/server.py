"""HTTP API for formal proof runs against the mounted clone."""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from proof_lab.runner import ARTIFACTS, ROOT, run_formal_bundle

app = FastAPI(
    title="CMPLX Proof Lab",
    description="Formal validation runner for lattice-forge proven surface.",
    version="2026.05.23",
)


@app.get("/health")
async def health():
    meta_path = ARTIFACTS / "meta" / "last_clone.json"
    meta = {}
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return {"status": "ok", "root": str(ROOT), "clone": meta}


@app.post("/api/formal/run")
async def run_formal():
    result = run_formal_bundle()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle = ARTIFACTS / "bundles" / ts
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "run_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    pkg = ROOT / "packages" / "lattice-forge"
    for name in ("proofs_report.json", "expected_outputs.json"):
        src = pkg / name
        if src.is_file():
            shutil.copy2(src, bundle / name)
    claims = pkg / "claims" / "registry.jsonl"
    if claims.is_file():
        shutil.copy2(claims, bundle / "claims_registry.jsonl")
    latest = ARTIFACTS / "latest"
    if latest.exists():
        if latest.is_symlink():
            latest.unlink()
        elif latest.is_dir():
            shutil.rmtree(latest)
    try:
        latest.symlink_to(bundle, target_is_directory=True)
    except OSError:
        shutil.copytree(bundle, latest, dirs_exist_ok=True)
    return JSONResponse({"bundle": str(bundle), **result})


@app.post("/api/empirical/run")
async def run_empirical(mode: str = "quick"):
    from lattice_forge.empirical.runner import run_empirical_matrix

    out = ARTIFACTS / "empirical_matrix_report.json"
    report = run_empirical_matrix(exhaustion_mode=mode, output=out)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle = ARTIFACTS / "bundles" / ts
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "empirical_matrix_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return JSONResponse({"artifact": str(out), **report})


@app.get("/api/formal/latest")
async def latest_bundle():
    latest = ARTIFACTS / "latest"
    if not latest.exists():
        return JSONResponse({"error": "no bundle yet"}, status_code=404)
    run_file = latest / "run_result.json"
    if not run_file.is_file():
        return JSONResponse({"path": str(latest), "run_result": None})
    return JSONResponse(json.loads(run_file.read_text(encoding="utf-8")))


def main():
    import uvicorn

    port = int(os.environ.get("PROOF_LAB_PORT", "8871"))
    uvicorn.run("proof_lab.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
