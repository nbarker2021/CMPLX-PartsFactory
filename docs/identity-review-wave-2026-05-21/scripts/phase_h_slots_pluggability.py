#!/usr/bin/env python3
"""Phase H + slots vs CMPLX-PartsFactory pluggability analysis."""
from __future__ import annotations

import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(r"D:/PartsFactory")
REPO = ROOT / "CMPLX-PartsFactory"
OUT_MD = ROOT / "identity_review/reports/slots-pluggability-analysis-2026-05-21.md"
OUT_JSON = ROOT / "identity_review/reports/slots-pluggability-aggregate-2026-05-21.json"

REPO_KERNEL = "http://localhost:8786"

# MorphonController KNOWN_PORTS (mirror of controller.py)
KNOWN_PORTS = sorted(
    {
        "addressing",
        "geometry",
        "memory",
        "constraints",
        "engine",
        "transport",
        "symbolic",
        "routing",
        "hash_lanes",
        "crystal",
        "snap",
        "cache",
        "conservation",
        "diagnostic",
        "receipt",
        "embed",
        "atlas",
    }
)

# ATTRACTOR_FRAME slot hints (manufactured + in-progress from session work)
SLOT_REGISTRY: list[dict[str, Any]] = [
    {"slot": "slot-01-receipt-chain", "port": "receipt", "package": "cmplx.receipt", "manufactured": True},
    {"slot": "slot-04-speedlight-worldline", "port": "cache", "package": "cmplx.speedlight", "manufactured": True},
    {"slot": "slot-10-11-morphon", "port": "(substrate)", "package": "cmplx.morphon", "manufactured": True},
    {"slot": "slot-17-snap", "port": "snap", "package": "cmplx.snap", "manufactured": True},
    {"slot": "slot-18-tarpit", "port": "symbolic", "package": "cmplx.symbolic.tarpit", "manufactured": True},
    {"slot": "slot-addressing-mdhg", "port": "addressing", "package": "cmplx.addressing.mdhg", "manufactured": "partial"},
    {"slot": "slot-memory-mmdb", "port": "memory", "package": "cmplx.memory.mmdb", "manufactured": "partial"},
    {"slot": "slot-geometry-e8", "port": "geometry", "package": "cmplx.geometry", "manufactured": "partial"},
    {"slot": "slot-constraints-aletheia", "port": "constraints", "package": "cmplx.constraints", "manufactured": "partial"},
    {"slot": "slot-engine-cqe", "port": "engine", "package": "cmplx.engine.cqe", "manufactured": "partial"},
    {"slot": "slot-transport", "port": "transport", "package": "cmplx.transport", "manufactured": "partial"},
    {"slot": "slot-crystal", "port": "crystal", "package": "cmplx.crystal", "manufactured": "partial"},
    {"slot": "slot-routing-agrm", "port": "routing", "package": "cmplx.routing", "manufactured": True},
    {"slot": "slot-16-hash-lanes", "port": "hash_lanes", "package": "cmplx.hash_lanes", "manufactured": True},
    {"slot": "slot-transform", "port": "—", "package": "cmplx.transform", "manufactured": "partial"},
]


def _curl_json(path: str, timeout: float = 35.0) -> tuple[Any, str]:
    try:
        with urllib.request.urlopen(f"{REPO_KERNEL}{path}", timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), "ok"
    except Exception as e:
        return None, str(e)


def _spine_packages() -> dict[str, dict[str, Any]]:
    base = REPO / "src/cmplx"
    out: dict[str, dict[str, Any]] = {}
    for d in sorted(base.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        provider = (d / "provider.py").exists()
        bridge = (d / "BRIDGE.md").exists()
        iface = (d / "INTERFACE.md").exists()
        receipt_br = any(d.rglob("_receipt_bridge.py"))
        py_count = len(list(d.rglob("*.py")))
        out[d.name] = {
            "has_provider": provider,
            "has_bridge": bridge,
            "has_interface": iface,
            "has_receipt_bridge": receipt_br,
            "py_files": py_count,
        }
    return out


def _catalog_parts() -> list[dict[str, Any]]:
    rows = []
    for p in sorted((REPO / "catalog/parts").glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        rows.append(
            {
                "part_id": d.get("part_id"),
                "slot": d.get("slot"),
                "package": d.get("package"),
                "landing_path": d.get("landing_path"),
                "depends_on": d.get("depends_on", []),
                "test_count": d.get("test_count"),
            }
        )
    return rows


def _gitnexus_snap() -> dict[str, Any]:
    gn = REPO / "data/gitnexus_index.sqlite"
    result: dict[str, Any] = {"db_exists": gn.exists(), "queries": {}}
    if not gn.exists():
        return result
    conn = sqlite3.connect(gn)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    result["tables"] = tables[:20]
    for table, col in [
        ("aggregate_search", "content"),
        ("nodes", "name"),
        ("by_system", "name"),
    ]:
        if table not in tables:
            continue
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        c = col if col in cols else next(iter(cols), "name")
        for term in ("SNAPEngine", "MorphonController", "snap", "receipt"):
            try:
                n = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE lower({c}) LIKE ?",
                    (f"%{term.lower()}%",),
                ).fetchone()[0]
                result["queries"][f"{table}.{term}"] = n
            except sqlite3.OperationalError:
                pass
    conn.close()
    return result


def _pluggability_score(pkg: str, spine: dict[str, dict]) -> str:
    key = pkg.replace("cmplx.", "").split(".")[0]
    info = spine.get(key)
    if not info:
        return "missing_spine_dir"
    if info["has_provider"] and info["has_receipt_bridge"]:
        return "instant_port_register"
    if info["has_provider"]:
        return "instant_with_bootstrap_factory"
    if info["py_files"] > 3 and info["has_bridge"]:
        return "near_ready_add_provider"
    if info["py_files"] > 0:
        return "library_only_wire_bootstrap"
    return "defer"


def main() -> int:
    phase_h: dict[str, Any] = {}
    health, err = _curl_json("/api/health")
    phase_h["repo_kernel_health"] = health
    phase_h["repo_kernel_error"] = err if health is None else None
    for path in (
        "/api/gitnexus/status",
        "/api/gitnexus/unification-hints",
        "/api/gitnexus/aggregate/search?q=SNAPEngine&limit=5",
        "/api/gitnexus/aggregate/search?q=MorphonController&limit=5",
    ):
        data, status = _curl_json(path, timeout=45.0)
        phase_h[path] = {"status": status, "sample": data}

    manifest_path = REPO / "catalog/bootstrap_manifest.json"
    bootstrap_manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )
    catalog = _catalog_parts()
    spine = _spine_packages()
    gitnexus = _gitnexus_snap()

    pluggable: list[dict[str, Any]] = []
    for row in SLOT_REGISTRY:
        pkg = row["package"]
        if pkg.startswith("cmplx."):
            plug = _pluggability_score(pkg, spine)
        else:
            plug = "substrate_core"
        row = {**row, "pluggability": plug}
        pluggable.append(row)

    # Compare folder = CMPLX-PartsFactory src/cmplx
    instant = [r for r in pluggable if r["pluggability"] == "instant_port_register"]
    near = [r for r in pluggable if "near_ready" in r["pluggability"] or "instant_with" in r["pluggability"]]

    aggregate = {
        "phase_h": phase_h,
        "bootstrap_manifest": bootstrap_manifest,
        "catalog_parts": catalog,
        "catalog_part_count": len(catalog),
        "spine_dir_count": len(spine),
        "known_ports": sorted(KNOWN_PORTS),
        "gitnexus_offline_sqlite": gitnexus,
        "slots": pluggable,
        "instant_pluggable_count": len(instant),
    }
    OUT_JSON.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")

    lines = [
        "# Slots vs CMPLX-PartsFactory — pluggability analysis",
        "",
        f"**Compared folder:** `{REPO}` (spine `src/cmplx/`, `catalog/parts/`)",
        "",
        "## Phase H — repo-kernel / GitNexus",
        "",
    ]
    if health:
        lines.append(f"- repo-kernel: **up** (`{REPO_KERNEL}/api/health`)")
    else:
        lines.append(f"- repo-kernel: **offline** ({phase_h.get('repo_kernel_error', 'unreachable')})")
        lines.append("- Fallback: `data/gitnexus_index.sqlite` queries below")
    lines.append("")
    lines.append("### GitNexus SNAP-related hits (SQLite fallback)")
    for k, v in sorted(gitnexus.get("queries", {}).items()):
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("## Manufactured catalog parts (explicit gate JSON)")
    lines.append("")
    lines.append("| part_id | slot | package | tests |")
    lines.append("|---------|------|---------|------:|")
    for c in catalog:
        lines.append(
            f"| {c.get('part_id','')} | {c.get('slot','')} | {c.get('package','')} | {c.get('test_count','—')} |"
        )
    lines.append("")
    boot_n = bootstrap_manifest.get("port_count", len(catalog))
    lines.append(
        f"**{len(catalog)}** catalog JSON parts; **{boot_n}** bootstrap-wired ports "
        f"(`catalog/bootstrap_manifest.json`). Remaining ATTRACTOR slots may be spine-only or escrow."
    )
    lines.append("")
    lines.append("## MorphonController ports vs spine directories")
    lines.append("")
    lines.append(f"**{len(KNOWN_PORTS)}** registered port names. Spine has **{len(spine)}** top-level packages under `src/cmplx/`.")
    lines.append("")
    lines.append("| Port | Spine dir | provider.py | receipt bridge | Pluggability |")
    lines.append("|------|-----------|-------------|----------------|--------------|")
    port_to_dir = {
        "receipt": "receipt",
        "cache": "speedlight",
        "snap": "snap",
        "symbolic": "symbolic",
        "addressing": "addressing",
        "memory": "memory",
        "geometry": "geometry",
        "constraints": "constraints",
        "engine": "engine",
        "transport": "transport",
        "crystal": "crystal",
        "routing": "routing",
        "hash_lanes": "hash_lanes",
        "conservation": "conservation",
        "diagnostic": "diagnostic",
        "embed": "embed",
        "atlas": "atlas",
    }
    for port in KNOWN_PORTS:
        d = port_to_dir.get(port, port)
        info = spine.get(d, {})
        if port == "symbolic":
            info = spine.get("symbolic", {})
        prov = "yes" if info.get("has_provider") else "—"
        rb = "yes" if info.get("has_receipt_bridge") else "—"
        if info.get("has_provider") and info.get("has_receipt_bridge"):
            plug = "**instant**"
        elif info.get("has_provider"):
            plug = "instant (bootstrap)"
        elif info.get("py_files", 0) > 5:
            plug = "near-ready"
        else:
            plug = "partial/missing"
        lines.append(f"| `{port}` | `{d}` | {prov} | {rb} | {plug} |")
    lines.append("")
    lines.append("## Slot registry (frame + session manufacturing)")
    lines.append("")
    for r in pluggable:
        lines.append(
            f"- **{r['slot']}** — `{r['package']}` port `{r['port']}` — manufactured={r['manufactured']} — **{r['pluggability']}**"
        )
    lines.append("")
    lines.append("## Instantly pluggable into the framework (today)")
    lines.append("")
    lines.append("Call once per process:")
    lines.append("")
    lines.append("```python")
    lines.append("from runtime.cmplx_bootstrap import register_all")
    lines.append("register_all()  # wires all MorphonController ports")
    lines.append("```")
    lines.append("")
    lines.append("| Ready now | Why |")
    lines.append("|-----------|-----|")
    lines.append("| `cmplx.receipt` | provider + `_receipt_bridge`; catalog part slot-01 |")
    lines.append("| `cmplx.speedlight` | provider + bridge; catalog slot-04 |")
    lines.append("| `cmplx.snap` | `SNAPEngine` + receipt bridge + HTTP :8823; catalog slot-17 |")
    lines.append("| `cmplx.morphon` | substrate + combinations + store/fetch; all ports route here |")
    lines.append("| `cmplx.symbolic.tarpit` | `TarPitSymbolicProvider` on `symbolic` port; slot-18 slice |")
    lines.append("| `cmplx.memory.mmdb` | `MMDBMemoryProvider` — bootstrap `memory` port |")
    lines.append("| `cmplx.addressing.mdhg` | MDHG provider — bootstrap `addressing` |")
    lines.append("| `cmplx.constraints` | Aletheia — bootstrap `constraints` |")
    lines.append("| `cmplx.geometry` | E8/Leech — bootstrap `geometry` |")
    lines.append("| `cmplx.engine.cqe` | CQE evolve — bootstrap `engine` |")
    lines.append("| `cmplx.transport` | chirp/etc — bootstrap `transport` |")
    lines.append("| `cmplx.embed` | 4-embed — bootstrap `embed` |")
    lines.append("| `cmplx.atlas` | Mandelbrot boundary — bootstrap `atlas` |")
    lines.append("| `cmplx.transform` | ingest + morphon_ingest; uses ports when `ensure_bootstrapped()` |")
    lines.append("")
    lines.append("## Near-ready (add catalog part + done gate)")
    lines.append("")
    lines.append("| Package | Gap |")
    lines.append("|---------|-----|")
    lines.append("| `cmplx.crystal` | provider exists; wire crystal←snap labels (escrow row closed in register) |")
    lines.append("| `cmplx.routing` | AGRM port — register in bootstrap, smoke tests |")
    lines.append("| `cmplx.conservation` | provider present; receipt bridge verify |")
    lines.append("| `cmplx.diagnostic` | MORSR/diagnostic — bootstrap registered |")
    lines.append("")
    lines.append("## Not instant — keep in escrow / external corpus")
    lines.append("")
    lines.append("- `CMPLX-history/cmplx_pending/snap/*` — 53/66 defer per triage (agent shards, homonyms)")
    lines.append("- `geometry/e8` SnapE8 — wrong slot")
    lines.append("- Manny `snap_runtime` — bridge only")
    lines.append("- Catalog entries missing for most ATTRACTOR slots — manufacturing gate not yet written")
    lines.append("")
    lines.append(f"Aggregate JSON: `{OUT_JSON.name}`")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
