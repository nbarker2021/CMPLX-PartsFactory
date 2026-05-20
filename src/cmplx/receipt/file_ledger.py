"""
Minimal SpeedLight-compatible receipt + ledger utilities.

Design goals:
- Append-only ledger (jsonl)
- Deterministic artifact hashing
- Single call surface for controllers: write_receipt(...)
"""
from __future__ import annotations

import json, os, hashlib, time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .signing import sign_receipt_hash, verify_receipt_signature

# Schema pin: bumped when receipt format changes.
receipt_schema_version = 1

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, obj: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def canonical_json(obj: Any) -> str:
    """Canonical JSON used for receipt hashing.

    - UTF-8
    - sorted keys
    - no insignificant whitespace
    - no ASCII escaping
    """
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def merkle_root_hex(leaves_hex: List[str]) -> str:
    """Compute a simple Merkle root over hex digests (sha256), returning hex digest.

    Leaves are sorted to make the root order-independent for an artifact set.
    """
    leaves = [bytes.fromhex(h) for h in sorted([h for h in leaves_hex if h])]
    if not leaves:
        return sha256_bytes(b"")
    level = [hashlib.sha256(x).digest() for x in leaves]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            nxt.append(hashlib.sha256(left + right).digest())
        level = nxt
    return level[0].hex()


def _read_last_receipt_hash(ledger_path: Path) -> Optional[str]:
    if not ledger_path.exists():
        return None
    last: Optional[str] = None
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            last = obj.get("receipt_hash") or last
        except Exception:
            continue
    return last

def now_utc_iso() -> str:
    """
    Returns a UTC timestamp.
    If CQE_DETERMINISTIC_TIME=1, returns a fixed sentinel timestamp for determinism tests.
    """
    if os.environ.get("CQE_DETERMINISTIC_TIME","") == "1":
        return "1970-01-01T00:00:00Z"
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def write_receipt(
    workspace: Path,
    run_id: str,
    step_id: str,
    controller: str,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    artifacts: List[Dict[str, Any]],
    status: str = "ok",
    overlays: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
    city_family: Optional[str] = None,
    **_ignored_kwargs: Any,
) -> Dict[str, Any]:
    """
    Writes receipt JSON and appends to ledger.jsonl.
    Artifacts should be dicts: {"path": "...", "kind": "..."}.
    Hashes are computed if artifact paths exist.
    """
    run_dir = workspace / "runs" / run_id
    receipts_dir = run_dir / "receipts"
    artifacts_dir = run_dir / "artifacts"
    ensure_dir(receipts_dir)
    ensure_dir(artifacts_dir)

    # Compute hashes for artifacts
    hashed = []
    for a in artifacts:
        ap = a.get("path")
        canon_sha = a.get("sha256")
        rec = dict(a)
        if ap:
            p = Path(ap)
            if canon_sha:
                rec.setdefault("hashes", {})["sha256"] = canon_sha

            if not p.is_absolute():
                candidate1 = (workspace / "runs" / run_id / "artifacts" / ap)
                candidate2 = (workspace / "runs" / run_id / ap)
                candidate3 = (workspace / ap)
                if candidate1.exists():
                    p = candidate1.resolve()
                elif candidate2.exists():
                    p = candidate2.resolve()
                else:
                    p = candidate3.resolve()
            if p.exists() and p.is_file():
                rec.setdefault("hashes", {})["sha256"] = sha256_file(p)
                rec["bytes"] = p.stat().st_size
        hashed.append(rec)

    # Optional effect constraints (artifact path allowlist)
    # If controller spec declares effects.artifact_prefixes, enforce that every
    # artifact path is under one of those prefixes.
    try:
        spec_p = workspace / "schemas" / "controller_spec_min.json"
        if spec_p.exists():
            spec = json.loads(spec_p.read_text(encoding="utf-8"))
            entry = (spec.get("controllers") or {}).get(str(controller)) or {}
            eff = entry.get("effects") or {}
            allowed_prefixes = eff.get("artifact_prefixes") or []
            if allowed_prefixes:
                allowed_prefixes = [str(x).rstrip("/") for x in allowed_prefixes if str(x).strip()]
                for a in hashed:
                    ap = a.get("path")
                    if not isinstance(ap, str) or not ap:
                        continue
                    apn = ap.lstrip("/")
                    ok = any(apn == pref or apn.startswith(pref + "/") for pref in allowed_prefixes)
                    if not ok:
                        raise RuntimeError(
                            f"Controller '{controller}' attempted to receipt artifact '{ap}'. "
                            f"Not in allowed prefixes: {allowed_prefixes}"
                        )
    except Exception as e:
        # If effects are declared, failure is hard. If not declared or spec missing, ignore.
        # We detect the declared case by checking if the error message indicates a strict violation.
        if "attempted to receipt artifact" in str(e):
            raise

    ledger_path = run_dir / "ledger.jsonl"
    prev_hash = _read_last_receipt_hash(ledger_path)

    receipt = {
        "run_id": run_id,
        "step_id": step_id,
        "controller": controller,
        "timestamp_utc": now_utc_iso(),
        "status": status,
        "inputs": inputs,
        "outputs": outputs,
        "artifacts": hashed,
        "overlays": overlays or {},
        "extra": extra or {},
    }

    # Artifact set commitment (order-independent)
    artifact_hashes = []
    for a in hashed:
        h = (a.get("hashes") or {}).get("sha256")
        if h:
            artifact_hashes.append(h)
    receipt["artifacts_merkle_root"] = merkle_root_hex(artifact_hashes)

    # Back-link chain
    receipt["prev_receipt_hash"] = prev_hash

    # Schema pinning (for forward compatibility and audit)
    receipt["schema_pins"] = {"receipt_schema_version": int(receipt_schema_version)}
    if city_family:
        try:
            con = connect_city_db(workspace, city_family)
            try:
                ensure_city_schema(con, city_family)
                receipt["schema_pins"]["city_family"] = str(city_family)
                receipt["schema_pins"]["city_schema_version"] = int(current_version(con))
            finally:
                con.close()
        except Exception as _e:
            # Do not fail receipt emission; record the failure for audit.
            receipt["schema_pins"]["city_family"] = str(city_family)
            receipt["schema_pins"]["city_schema_version"] = None
            receipt["schema_pins"]["city_schema_error"] = str(_e)

    # Stable id: sha256 of normalized fields (human-friendly stable reference)
    receipt_id = sha256_bytes(canonical_json(
        {k: receipt.get(k) for k in ["run_id","step_id","controller","status","inputs","outputs","overlays","extra"]}
    ).encode("utf-8"))
    receipt["receipt_id"] = receipt_id

    # Tamper-evident hash over canonical receipt content.
    # Exclude: receipt_hash itself and signature fields (signature signs the receipt_hash).
    _hashable = {k: v for k, v in receipt.items() if k not in {"receipt_hash", "signature_b64", "signing_key_id"}}
    receipt_hash = sha256_bytes(canonical_json(_hashable).encode("utf-8"))
    receipt["receipt_hash"] = receipt_hash

    # Authenticity: sign the receipt hash
    signing_key_id, signature_b64 = sign_receipt_hash(workspace, receipt_hash)
    receipt["signing_key_id"] = signing_key_id
    receipt["signature_b64"] = signature_b64

    receipt_path = receipts_dir / f"{step_id}__{controller}.json"
    write_json(receipt_path, receipt)

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(receipt, ensure_ascii=False) + "\n")

    return receipt

def build_receipt_index(workspace: Path, run_id: str) -> Dict[str, Any]:
    run_dir = workspace / "runs" / run_id
    ledger_path = run_dir / "ledger.jsonl"
    idx = {"run_id": run_id, "receipts": []}
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            idx["receipts"].append({
                "receipt_id": r.get("receipt_id"),
                "receipt_hash": r.get("receipt_hash"),
                "prev_receipt_hash": r.get("prev_receipt_hash"),
                "step_id": r.get("step_id"),
                "controller": r.get("controller"),
                "status": r.get("status"),
                "timestamp_utc": r.get("timestamp_utc"),
            })
    # Chain head/tail summary
    if idx["receipts"]:
        idx["chain_head_receipt_hash"] = idx["receipts"][0].get("receipt_hash")
        idx["chain_tail_receipt_hash"] = idx["receipts"][-1].get("receipt_hash")
    out = run_dir / "receipt_index.json"
    write_json(out, idx)
    return idx

def verify_ledger(workspace: Path, run_id: str, *, write_report: bool = True, out_rel: str = "ledger_verify.json") -> Dict[str, Any]:
    """
    Minimal verification:
    - artifact hashes match current content (if artifact still exists)
    """
    run_dir = workspace / "runs" / run_id
    ledger_path = run_dir / "ledger.jsonl"
    report = {"run_id": run_id, "ok": True, "checks": [], "chain": [], "provenance": {}}
    if not ledger_path.exists():
        report["ok"] = False
        report["error"] = "ledger.jsonl missing"
        return report
    expected_prev: Optional[str] = None
    # Retention/lifecycle policy (tombstones, sealed blobs).
    retention_policy = _load_retention_policy(workspace)
    for i, line in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip(): 
            continue
        r = json.loads(line)

        # Verify receipt hash and prev hash chaining
        prev = r.get("prev_receipt_hash")
        rh = r.get("receipt_hash")
        # Receipt hash commits all fields except: receipt_hash and signature fields.
        _hashable = {k: v for k, v in r.items() if k not in {"receipt_hash", "signature_b64", "signing_key_id"}}
        recomputed = sha256_bytes(canonical_json(_hashable).encode("utf-8"))
        ok_hash = (rh == recomputed)
        ok_prev = (prev == expected_prev)

        # Verify authenticity signature
        key_id = r.get("signing_key_id")
        sig = r.get("signature_b64")
        ok_sig = bool(key_id and sig and rh and verify_receipt_signature(workspace, key_id, rh, sig, signed_at_utc=r.get("timestamp_utc")))
        if not ok_sig:
            report["ok"] = False
        if not ok_hash or not ok_prev:
            report["ok"] = False
        report["chain"].append({
            "line": i,
            "ok_hash": ok_hash,
            "ok_prev": ok_prev,
            "ok_sig": ok_sig,
            "expected_prev": expected_prev,
            "prev_receipt_hash": prev,
            "receipt_hash": rh,
            "recomputed_receipt_hash": recomputed,
            "signing_key_id": key_id,
            "receipt_id": r.get("receipt_id"),
            "controller": r.get("controller"),
            "step_id": r.get("step_id"),
        })
        expected_prev = rh

        # Verify artifacts
        for a in r.get("artifacts", []):
            ap = a.get("path")
            h = (a.get("hashes") or {}).get("sha256")
            if not ap or not h:
                continue
            p = Path(ap)
            if not p.is_absolute():
                candidate1 = (workspace / "runs" / run_id / "artifacts" / ap)
                candidate2 = (workspace / "runs" / run_id / ap)
                candidate3 = (workspace / ap)
                if candidate1.exists():
                    p = candidate1.resolve()
                elif candidate2.exists():
                    p = candidate2.resolve()
                else:
                    p = candidate3.resolve()
            if not p.exists():
                # If the digest has been tombstoned, treat it according to retention policy.
                tomb = _lifecycle_tombstone_info(workspace, h)
                if tomb is not None:
                    if retention_policy.get("allow_tombstoned_artifacts", False):
                        report["checks"].append({
                            "line": i,
                            "artifact": ap,
                            "ok": True,
                            "reason": "tombstoned",
                            "expected": h,
                            "tombstone": tomb,
                        })
                        continue
                    report["ok"] = False
                    report["checks"].append({"line": i, "artifact": ap, "ok": False, "reason": "tombstoned_not_allowed", "expected": h, "tombstone": tomb})
                    continue
                # Lifecycle support: allow artifacts to be archived to a content-addressed store.
                from .artifact_store import resolve_artifact_bytes
                # Try canonical run-relative locations first; fall back to archive by digest.
                rel_candidates = []
                if not Path(ap).is_absolute():
                    rel_candidates = [
                        (workspace / "runs" / run_id / "artifacts" / ap).relative_to(workspace).as_posix(),
                        (workspace / "runs" / run_id / ap).relative_to(workspace).as_posix(),
                        ap,
                    ]
                else:
                    # Absolute path: attempt to map to workspace-relative for archive lookup.
                    try:
                        rel_candidates = [Path(ap).resolve().relative_to(workspace.resolve()).as_posix()]
                    except Exception:
                        rel_candidates = []
                data = None
                used_rel = None
                for relc in rel_candidates:
                    data = resolve_artifact_bytes(workspace, relc, h)
                    if data is not None:
                        used_rel = relc
                        break
                if data is None:
                    report["ok"] = False
                    report["checks"].append({"line": i, "artifact": ap, "ok": False, "reason": "missing"})
                    continue
                import hashlib
                actual = hashlib.sha256(data).hexdigest()
                ok = (actual == h)
                if not ok:
                    report["ok"] = False
                seal = _lifecycle_seal_info(workspace, h)
                report["checks"].append({"line": i, "artifact": ap, "ok": ok, "expected": h, "actual": actual, "resolved_via": "archive_or_mapped", "rel_used": used_rel, "seal": seal})
                continue

            actual = sha256_file(p)
            ok = (actual == h)
            if not ok:
                report["ok"] = False
            report["checks"].append({"line": i, "artifact": ap, "ok": ok, "expected": h, "actual": actual})

    # Artifact provenance enforcement: every file under runs/<id>/artifacts must be referenced
    # by at least one receipt, unless explicitly allowlisted.
    prov = verify_artifact_provenance(workspace, run_id)
    report["provenance"] = prov
    if not prov.get("ok", False):
        report["ok"] = False
    if write_report:
        out = run_dir / out_rel
        write_json(out, report)
    return report


def verify_artifact_provenance(workspace: Path, run_id: str, allowlist_rel_prefixes: Optional[List[str]] = None) -> Dict[str, Any]:
    """Verify that artifacts are controller-produced (i.e., referenced by receipts).

    Rule:
      Every file in runs/<run_id>/artifacts/** must be referenced by a receipt artifact path.

    Rationale:
      Prevents bypass where files are written beside the controller pipeline.

    allowlist_rel_prefixes:
      Optional list of prefixes (relative to artifacts/) that are permitted to exist unreferenced.
      Default is conservative (no additional allowlist).
    """
    run_dir = workspace / "runs" / run_id
    artifacts_dir = run_dir / "artifacts"
    ledger_path = run_dir / "ledger.jsonl"
    allowlist_rel_prefixes = allowlist_rel_prefixes or []

    referenced: set[str] = set()
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            for a in r.get("artifacts", []):
                ap = a.get("path")
                if not ap:
                    continue
                # Normalize to artifacts-relative if possible
                # We store receipts with relative paths (preferred), but tolerate absolute.
                p = Path(ap)
                if p.is_absolute():
                    try:
                        rel = p.resolve().relative_to(artifacts_dir.resolve())
                        referenced.add(rel.as_posix())
                    except Exception:
                        # If absolute but not under artifacts_dir, we ignore for provenance scope.
                        pass
                else:
                    referenced.add(p.as_posix())

    untracked: List[Dict[str, Any]] = []
    if artifacts_dir.exists():
        for p in artifacts_dir.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(artifacts_dir).as_posix()
            if rel in referenced:
                continue
            if any(rel.startswith(pref.rstrip("/") + "/") or rel == pref.rstrip("/") for pref in allowlist_rel_prefixes):
                continue
            untracked.append({"path": rel, "sha256": sha256_file(p), "bytes": p.stat().st_size})

    ok = (len(untracked) == 0)
    return {
        "ok": ok,
        "referenced_count": len(referenced),
        "untracked_count": len(untracked),
        "untracked": untracked,
        "allowlist_rel_prefixes": allowlist_rel_prefixes,
    }


# --- Lifecycle helpers (retention / seals / tombstones) ---

def _load_retention_policy(workspace: Path) -> Dict[str, Any]:
    """Load retention/lifecycle policy from runtime/config.

    Policy is optional; defaults are conservative.
    """
    p = workspace / "config" / "retention_policy.json"
    if not p.exists():
        return {
            "allow_tombstoned_artifacts": False,
            "allow_export_sealed": False,
        }
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {
            "allow_tombstoned_artifacts": False,
            "allow_export_sealed": False,
            "error": "failed_to_parse_retention_policy",
        }


def _lifecycle_tombstone_info(workspace: Path, sha256_hex: str) -> Optional[Dict[str, Any]]:
    try:
        from .city_db import connect_city_db, ensure_city_schema

        conn = connect_city_db(workspace, "lifecycle")
        ensure_city_schema(conn, "lifecycle")
        row = conn.execute(
            "SELECT sha256, tombstoned_at_utc, reason, notes FROM artifact_tombstones WHERE sha256=?",
            (sha256_hex.lower(),),
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {"sha256": row[0], "tombstoned_at_utc": row[1], "reason": row[2], "notes": row[3]}
    except Exception:
        return None


def _lifecycle_seal_info(workspace: Path, sha256_hex: str) -> Optional[Dict[str, Any]]:
    try:
        from .city_db import connect_city_db, ensure_city_schema

        conn = connect_city_db(workspace, "lifecycle")
        ensure_city_schema(conn, "lifecycle")
        row = conn.execute(
            "SELECT sha256, access_level, sealed_at_utc, notes FROM artifact_seals WHERE sha256=?",
            (sha256_hex.lower(),),
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {"sha256": row[0], "access_level": row[1], "sealed_at_utc": row[2], "notes": row[3]}
    except Exception:
        return None


# Compatibility helper for controllers that pass ControllerContext directly.
def write_receipt_ctx(ctx, controller: str, inputs=None, outputs=None, artifacts=None, status: str="ok", overlays=None, extra=None, **_ignored_kwargs):
    """Write receipt using a ControllerContext.

    This keeps older controllers simple and reduces boilerplate.
    """
    return write_receipt(
        workspace=ctx.workspace,
        run_id=ctx.run_id,
        step_id=ctx.step_id,
        controller=controller,
        inputs=inputs or {},
        outputs=outputs or {},
        artifacts=artifacts or [],
        status=status,
        overlays=overlays,
        extra=extra,
    )
