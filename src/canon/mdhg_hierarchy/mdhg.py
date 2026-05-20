from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

import hashlib


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def stable_sha256(obj: Any) -> str:
    return hashlib.sha256(stable_json(obj)).hexdigest()


DEFAULT_FACTORS_CORRIDOR = [2, 3, 5, 7, 11, 13]
DEFAULT_FACTORS_LATTICE = [8, 12, 16, 24, 32, 64, 128, 240]


@dataclass(frozen=True)
class HashAlgo:
    name: str
    digest_size: Optional[int] = None  # only used for blake2 variants

    def digest(self, payload: bytes) -> str:
        if self.name == "blake2b":
            h = hashlib.blake2b(payload, digest_size=self.digest_size or 32)
            return h.hexdigest()
        if self.name == "blake2s":
            h = hashlib.blake2s(payload, digest_size=self.digest_size or 32)
            return h.hexdigest()
        if self.name == "sha256":
            return hashlib.sha256(payload).hexdigest()
        if self.name == "sha1":
            return hashlib.sha1(payload).hexdigest()
        raise ValueError(f"unsupported hash algo: {self.name}")


def _mdhg_root(universe_dir: Path) -> Path:
    p = universe_dir / "ops" / "mdhg" / "planets"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _index_path(universe_dir: Path) -> Path:
    p = _mdhg_root(universe_dir) / "index.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def planet_dir(universe_dir: Path, planet_id: str) -> Path:
    return _mdhg_root(universe_dir) / planet_id


def load_geometric_keys(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _score_factor_choice(prod: int, f: int, target: int) -> float:
    # score in log-space; smaller is better
    return abs(math.log(prod * f) - math.log(max(2, target)))


def choose_dimensions(
    target_buckets: int,
    allowed_factors: List[int],
    *,
    max_dims: int = 8,
) -> List[int]:
    """
    Choose a factor sequence whose product >= target_buckets and is as close as possible,
    constrained to allowed factors. Greedy log-space fit.
    """
    target_buckets = max(2, int(target_buckets))
    allowed = sorted(set(int(x) for x in allowed_factors if int(x) >= 2))
    dims: List[int] = []
    prod = 1

    while prod < target_buckets and len(dims) < max_dims:
        best = None
        best_score = 1e9
        for f in allowed:
            sc = _score_factor_choice(prod, f, target_buckets)
            if sc < best_score:
                best_score = sc
                best = f
        if best is None:
            best = 2
        dims.append(int(best))
        prod *= int(best)
        if prod >= target_buckets and prod <= int(target_buckets * 1.15):
            break

    while prod < target_buckets and len(dims) < max_dims:
        f = allowed[0] if allowed else 2
        dims.append(int(f))
        prod *= int(f)

    return dims or [8]


def plan_profile(
    purpose: str,
    expected_items: Optional[int],
    expected_bytes: Optional[int],
    mutability: str,
    geo_keys: Dict[str, Any],
) -> Dict[str, Any]:
    """
    MDHG 'planet printer': build a per-task hash-house (routing dims + hash stack).
    Deterministic for the same request (stable replay).
    """
    purpose_l = (purpose or "").lower()

    # derive factor palette from geometric keys (if available)
    factors: List[int] = []
    consts = geo_keys.get("constants")
    if isinstance(consts, list):
        freq: Dict[int, int] = {}
        for c in consts:
            try:
                if c.get("type") == "int":
                    v = int(c.get("value"))
                    if 2 <= v <= 256:
                        freq[v] = freq.get(v, 0) + 1
            except Exception:
                continue
        top = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:12]
        factors = [v for v, _ in top]

    if not factors:
        factors = DEFAULT_FACTORS_LATTICE[:]

    if any(k in purpose_l for k in ["receipt", "ticket", "ledger", "audit"]):
        allowed_factors = sorted(set(DEFAULT_FACTORS_CORRIDOR + factors))
        bucket_load = 128
    else:
        allowed_factors = sorted(set(DEFAULT_FACTORS_LATTICE + factors))
        bucket_load = 256

    if expected_items is not None and expected_items > 0:
        target_buckets = max(8, int(round(expected_items / bucket_load)))
    elif expected_bytes is not None and expected_bytes > 0:
        est_items = max(1, int(round(expected_bytes / 4096)))
        target_buckets = max(8, int(round(est_items / bucket_load)))
    else:
        target_buckets = 32

    dims = choose_dimensions(target_buckets, allowed_factors, max_dims=8)
    prod = 1
    for d in dims:
        prod *= int(d)

    hash_stack = [
        {"name": "blake2b", "digest_size": 32},
        {"name": "sha256", "digest_size": None},
    ]
    if "legacy" in purpose_l:
        hash_stack.append({"name": "sha1", "digest_size": None})

    geo_digest = stable_sha256({"summary": geo_keys.get("analysis", {}), "n": len(geo_keys.get("constants", []) or [])}) if geo_keys else "nogeo"
    salt = stable_sha256({"purpose": purpose, "dims": dims, "mutability": mutability, "geo": geo_digest})[:16]

    return {
        "purpose": purpose,
        "mutability": mutability,
        "bucket_load": bucket_load,
        "target_buckets": int(target_buckets),
        "routing": {
            "dims": dims,
            "product": int(prod),
            "allowed_factors": allowed_factors,
            "salt": salt,
            "format": "base36",
        },
        "hash_stack": hash_stack,
        "geo_digest": geo_digest,
        "version": "mdhg/0.1",
    }


def _base36(n: int) -> str:
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    out = []
    x = n
    while x > 0:
        x, r = divmod(x, 36)
        out.append(chars[r])
    return "".join(reversed(out))


def _route_from_digest(digest_hex: str, dims: List[int]) -> List[str]:
    x = int(digest_hex[:16], 16)  # 64-bit slice for routing
    parts: List[str] = []
    for d in dims:
        idx = x % int(d)
        x //= int(d)
        parts.append(_base36(idx).rjust(2, "0"))
    return parts


def _hash_algos(profile: Dict[str, Any]) -> List[HashAlgo]:
    out: List[HashAlgo] = []
    for a in profile.get("hash_stack", []):
        name = str(a.get("name"))
        ds = a.get("digest_size")
        out.append(HashAlgo(name=name, digest_size=int(ds) if ds is not None else None))
    return out


def _planet_paths(pdir: Path) -> Dict[str, Path]:
    return {
        "root": pdir,
        "meta": pdir / "meta.json",
        "manifest": pdir / "manifest.jsonl",
        "events": pdir / "events.jsonl",
        "shards": pdir / "shards",
        "tombstones": pdir / "tombstones.jsonl",
    }


def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def spawn_planet(
    universe_dir: Path,
    *,
    purpose: str,
    expected_items: Optional[int] = None,
    expected_bytes: Optional[int] = None,
    mutability: str = "append_only",
    geo_keys_path: Optional[Path] = None,
    planet_id: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    geo = load_geometric_keys(geo_keys_path)
    profile = plan_profile(purpose, expected_items, expected_bytes, mutability, geo)

    pid = planet_id or f"planet:{uuid4().hex}"
    pdir = planet_dir(universe_dir, pid)
    paths = _planet_paths(pdir)
    paths["shards"].mkdir(parents=True, exist_ok=True)

    meta = {
        "planet_id": pid,
        "created_at": now_utc(),
        "profile": profile,
        "tags": tags or {},
        "stats": {"objects": 0, "bytes": 0},
    }
    paths["meta"].write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    _append_jsonl(_index_path(universe_dir), {"type": "spawn", "at": now_utc(), "planet_id": pid, "purpose": purpose, "profile": profile})
    _append_jsonl(paths["events"], {"type": "spawn", "at": now_utc(), "planet_id": pid, "profile": profile})
    return {"ok": True, "planet_id": pid, "planet_dir": str(pdir), "profile": profile}


def _load_meta(pdir: Path) -> Dict[str, Any]:
    return json.loads((pdir / "meta.json").read_text(encoding="utf-8"))


def _save_meta(pdir: Path, meta: Dict[str, Any]) -> None:
    (pdir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def _record_object(paths: Dict[str, Path], record: Dict[str, Any]) -> None:
    _append_jsonl(paths["manifest"], record)


def put(
    universe_dir: Path,
    planet_id: str,
    *,
    key: str,
    payload: bytes,
    content_type: str = "application/octet-stream",
    tags: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    pdir = planet_dir(universe_dir, planet_id)
    if not pdir.exists():
        return {"ok": False, "error": "planet_not_found", "planet_id": planet_id}

    meta = _load_meta(pdir)
    profile = meta.get("profile", {})
    salt = (profile.get("routing", {}) or {}).get("salt", "nosalt")
    dims = (profile.get("routing", {}) or {}).get("dims", [8])
    algos = _hash_algos(profile)

    content_seed = (salt + "|" + key).encode("utf-8") + b"\x00" + payload
    digests = {a.name: a.digest(content_seed) for a in algos}
    primary = digests.get(algos[0].name) if algos else hashlib.sha256(content_seed).hexdigest()
    route = _route_from_digest(primary, [int(d) for d in dims])

    shard_dir = (pdir / "shards")
    for r in route:
        shard_dir = shard_dir / r
    shard_dir = shard_dir / primary[:2]
    shard_dir.mkdir(parents=True, exist_ok=True)

    obj_id = f"obj:{uuid4().hex}"
    obj_path = shard_dir / f"{obj_id}.bin"
    obj_path.write_bytes(payload)

    rec = {
        "type": "put",
        "at": now_utc(),
        "planet_id": planet_id,
        "obj_id": obj_id,
        "key": key,
        "size": int(len(payload)),
        "content_type": content_type,
        "digests": digests,
        "route": route,
        "path": str(obj_path.relative_to(pdir)),
        "tags": tags or {},
    }
    paths = _planet_paths(pdir)
    _record_object(paths, rec)
    _append_jsonl(paths["events"], {"type": "put", "at": rec["at"], "obj_id": obj_id, "key": key, "size": rec["size"], "digests": digests})

    try:
        meta.setdefault("stats", {})
        meta["stats"]["objects"] = int(meta["stats"].get("objects", 0)) + 1
        meta["stats"]["bytes"] = int(meta["stats"].get("bytes", 0)) + int(len(payload))
        _save_meta(pdir, meta)
    except Exception:
        pass

    return {"ok": True, "planet_id": planet_id, "obj_id": obj_id, "digests": digests, "path": rec["path"], "route": route}


def _iter_manifest(paths: Dict[str, Path]) -> Iterable[Dict[str, Any]]:
    p = paths["manifest"]
    if not p.exists():
        return []
    def gen():
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
    return gen()


def get_latest_by_key(universe_dir: Path, planet_id: str, *, key: str) -> Dict[str, Any]:
    pdir = planet_dir(universe_dir, planet_id)
    if not pdir.exists():
        return {"ok": False, "error": "planet_not_found", "planet_id": planet_id}
    paths = _planet_paths(pdir)

    latest = None
    for rec in _iter_manifest(paths):
        if rec.get("type") == "put" and rec.get("key") == key:
            latest = rec
    if latest is None:
        return {"ok": False, "error": "not_found", "key": key, "planet_id": planet_id}

    rel = latest.get("path")
    abs_path = pdir / rel
    if not abs_path.exists():
        return {"ok": False, "error": "missing_blob", "key": key, "path": rel}

    return {
        "ok": True,
        "planet_id": planet_id,
        "key": key,
        "obj_id": latest.get("obj_id"),
        "path": rel,
        "size": latest.get("size"),
        "content_type": latest.get("content_type"),
        "digests": latest.get("digests"),
        "payload": abs_path.read_bytes(),
    }


def status(universe_dir: Path, planet_id: str) -> Dict[str, Any]:
    pdir = planet_dir(universe_dir, planet_id)
    if not pdir.exists():
        return {"ok": False, "error": "planet_not_found", "planet_id": planet_id}
    meta = _load_meta(pdir)
    return {"ok": True, "planet_id": planet_id, "planet_dir": str(pdir), "meta": meta}


def list_planets(universe_dir: Path, limit: int = 200) -> List[Dict[str, Any]]:
    idx = _index_path(universe_dir)
    if not idx.exists():
        return []
    out: List[Dict[str, Any]] = []
    with idx.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out[-limit:]


def grow_routing(universe_dir: Path, planet_id: str, *, add_factor: Optional[int] = None) -> Dict[str, Any]:
    pdir = planet_dir(universe_dir, planet_id)
    if not pdir.exists():
        return {"ok": False, "error": "planet_not_found", "planet_id": planet_id}
    meta = _load_meta(pdir)
    prof = meta.get("profile", {})
    routing = prof.get("routing", {}) or {}
    dims = [int(d) for d in (routing.get("dims") or [8])]

    allowed = [int(x) for x in (routing.get("allowed_factors") or DEFAULT_FACTORS_LATTICE)]
    factor = int(add_factor) if add_factor is not None else (allowed[0] if allowed else 2)
    if factor < 2:
        factor = 2
    dims.append(factor)

    prod = 1
    for d in dims:
        prod *= int(d)

    routing["dims"] = dims
    routing["product"] = int(prod)
    prof["routing"] = routing
    meta["profile"] = prof
    _save_meta(pdir, meta)
    paths = _planet_paths(pdir)
    _append_jsonl(paths["events"], {"type": "grow", "at": now_utc(), "add_factor": factor, "dims": dims, "product": prod})
    return {"ok": True, "planet_id": planet_id, "dims": dims, "product": prod}


def export_filtered(
    universe_dir: Path,
    planet_id: str,
    *,
    key_prefix: Optional[str] = None,
    key_regex: Optional[str] = None,
    max_items: int = 10000,
    out_zip: Optional[Path] = None,
) -> Dict[str, Any]:
    pdir = planet_dir(universe_dir, planet_id)
    if not pdir.exists():
        return {"ok": False, "error": "planet_not_found", "planet_id": planet_id}
    paths = _planet_paths(pdir)

    rx = re.compile(key_regex) if key_regex else None
    matches: List[Dict[str, Any]] = []
    for rec in _iter_manifest(paths):
        if rec.get("type") != "put":
            continue
        k = str(rec.get("key", ""))
        if key_prefix and not k.startswith(key_prefix):
            continue
        if rx and not rx.search(k):
            continue
        matches.append(rec)
        if len(matches) >= max_items:
            break

    out_zip = out_zip or (pdir / f"export_{uuid4().hex}.zip")
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    import zipfile
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta.json", json.dumps(_load_meta(pdir), indent=2, ensure_ascii=False))
        z.writestr("selection.json", json.dumps({"planet_id": planet_id, "count": len(matches), "key_prefix": key_prefix, "key_regex": key_regex}, indent=2))
        z.writestr("manifest_selected.jsonl", "\n".join(json.dumps(m, ensure_ascii=False) for m in matches) + "\n")
        for rec in matches:
            rel = rec.get("path")
            if not rel:
                continue
            abs_path = pdir / rel
            if abs_path.exists():
                z.write(abs_path, arcname=f"blobs/{rel}")

    _append_jsonl(paths["events"], {"type": "export", "at": now_utc(), "count": len(matches), "out_zip": str(out_zip)})
    return {"ok": True, "planet_id": planet_id, "count": len(matches), "out_zip": str(out_zip)}


def ingest_export(
    universe_dir: Path,
    *,
    export_zip: Path,
    purpose: str = "ingest",
    mutability: str = "append_only",
    geo_keys_path: Optional[Path] = None,
) -> Dict[str, Any]:
    if not export_zip.exists():
        return {"ok": False, "error": "zip_not_found", "path": str(export_zip)}

    spawn = spawn_planet(
        universe_dir,
        purpose=purpose,
        mutability=mutability,
        geo_keys_path=geo_keys_path,
        tags={"ingested_from": str(export_zip)},
    )
    pid = spawn["planet_id"]
    pdir = planet_dir(universe_dir, pid)

    import zipfile
    ingested = 0
    with zipfile.ZipFile(export_zip, "r") as z:
        sel = z.read("manifest_selected.jsonl").decode("utf-8", errors="ignore").splitlines()
        names = set(z.namelist())
        for line in sel:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            key = str(rec.get("key", ""))
            rel = rec.get("path", "")
            blob_name = f"blobs/{rel}"
            if blob_name in names:
                payload = z.read(blob_name)
                put(universe_dir, pid, key=key, payload=payload, content_type=str(rec.get("content_type", "application/octet-stream")), tags={"ingested": True})
                ingested += 1

    _append_jsonl(_planet_paths(pdir)["events"], {"type": "ingest", "at": now_utc(), "from_zip": str(export_zip), "count": ingested})
    return {"ok": True, "planet_id": pid, "ingested": ingested}
