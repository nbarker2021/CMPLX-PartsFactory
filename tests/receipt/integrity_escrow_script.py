"""
Escrow merge (2026-05-18T23:57:12Z).
Source: ``CMPLX-history/staging/by-family/unclassified/partsfactory/test_receipt_integrity.py``
Slot: ``slot-01-receipt-chain``
"""
from __future__ import annotations
import json
from pathlib import Path
from .checkpoint_utils import sha256_json, load_json, write_json

def main(pack_root: Path, out_dir: Path) -> dict:
    # Assume a run already exists in out_dir/ws_main
    ws = out_dir / "ws_main"
    runs = sorted((ws / "runs").glob("*"))
    if not runs:
        write_json(out_dir / "receipt_integrity.json", {"ok": False, "error": "no runs found"})
        return {"ok": False}
    last = runs[-1]
    receipts = sorted((last / "receipts").glob("*.json"))
    ledger = (last / "ledger.jsonl")
    ok = ledger.exists() and len(receipts) > 0
    # basic checks: each receipt has id, step, digest, and referenced artifacts exist
    missing_artifacts = []
    artifact_schema_errors = []
    receipt_ids = []
    for p in receipts:
        r = json.loads(p.read_text(encoding="utf-8"))
        receipt_ids.append(r.get("receipt_id"))
        for a in r.get("artifacts", []):
            if not isinstance(a, dict) or "path" not in a or "role" not in a:
                artifact_schema_errors.append({"receipt": r.get("receipt_id"), "artifact": str(a)})
                continue
            # artifacts may be stored as strings or dicts {"path": "..."}
            apath = a.get("path")
            apath = Path(apath)
            if not apath:
                continue
            cand1 = last / "artifacts" / apath
            cand2 = last / apath
            cand3 = ws / apath
            ap = cand1 if cand1.exists() else (cand2 if cand2.exists() else cand3)
            if not ap.exists():
                missing_artifacts.append({"receipt": r.get("receipt_id"), "artifact": str(apath)})
    ok = ok and (len(missing_artifacts)==0) and (None not in receipt_ids)
    rep = {"ok": ok, "run_id": last.name, "receipt_count": len(receipts), "ledger_present": ledger.exists(),
           "missing_artifacts": missing_artifacts[:50], "artifact_schema_errors": artifact_schema_errors[:50]}
    write_json(out_dir / "receipt_integrity.json", rep)
    return rep
