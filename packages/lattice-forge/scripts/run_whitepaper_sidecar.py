#!/usr/bin/env python3
"""Ingest proofs + registry + handoffs → whitepaper_manifest.yaml v1."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_registry(path: pathlib.Path) -> list[dict[str, Any]]:
    rows = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def build_manifest(root: pathlib.Path) -> dict[str, Any]:
    proofs = _load_json(root / "proofs_report.json")
    expected = _load_json(root / "expected_outputs.json")
    registry = _load_registry(root / "claims" / "registry.jsonl")
    handoffs_dir = root / "docs" / "agents" / "handoffs"

    ring1_proven = [
        r["claim_id"]
        for r in registry
        if r.get("ring") == 1 and str(r.get("honesty_label", "")).upper() == "PROVEN"
    ]
    regime_claims = [r["claim_id"] for r in registry if str(r.get("claim_id", "")).startswith("regime.")]
    decomp_claims = [
        r["claim_id"]
        for r in registry
        if r.get("claim_id") == "DECOMP-PAPER"
        or str(r.get("claim_id", "")).startswith("decomposition.")
    ]
    honest_claims = [
        "rule30.prize.depth_only_shortcut",
        "rule30.prize.nonperiodicity_density",
        "P1",
        "P2",
        "P3",
    ]

    manifest: dict[str, Any] = {
        "version": 1,
        "generated_from": {
            "proofs_report": str(root / "proofs_report.json"),
            "expected_outputs": str(root / "expected_outputs.json"),
            "registry": str(root / "claims" / "registry.jsonl"),
            "handoffs": [p.name for p in handoffs_dir.glob("R30-*-to-D.md")] if handoffs_dir.is_dir() else [],
        },
        "paired_whitepapers": [
            {
                "id": "WP-CORE-01",
                "type": "core",
                "subpackage": "prize-core",
                "claims": ring1_proven,
                "honesty": "proven",
                "falsification": "lattice-forge falsify --tier-a",
                "count": len(ring1_proven),
            },
            {
                "id": "WP-HONEST-03",
                "type": "companion",
                "subpackage": "prize-core",
                "claims": honest_claims,
                "honesty": "conj_and_open_gaps",
                "falsification": "docs/prize/FALSIFICATION.md",
                "count": len(honest_claims),
                "not_in_ring1": False,
            },
            {
                "id": "WP-REGIMES-01",
                "type": "companion",
                "subpackage": "regimes",
                "claims": regime_claims,
                "honesty": "bounded_exec",
                "falsification": "scripts/run_regimes_proofs.py --quick",
                "count": len(regime_claims),
                "not_in_ring1": True,
            },
            {
                "id": "WP-DECOMP-01",
                "type": "companion",
                "subpackage": "decomposition",
                "claims": decomp_claims,
                "honesty": "separate_paper",
                "falsification": "lattice-forge decomposition verify",
                "count": len(decomp_claims),
                "not_in_ring1": True,
            },
        ],
        "deferred_whitepapers": [
            {
                "id": "WP-OLOID-01",
                "trigger": "quad_oloid + full kinematic roll proof key in run_all_proofs",
            },
            {
                "id": "WP-MOONSHINE",
                "trigger": "voa_lookup.py harness key + CONJ closure",
            },
            {
                "id": "WP-TOWER-01",
                "trigger": "≥5 transport lemma rows reach PROVEN (pass_with_open_gaps does not count)",
            },
        ],
        "sidecar_decision": {
            "total_companions_beyond_core": 3,
            "cap": "1 core + ≤4 companions",
            "proofs_overall_status": proofs.get("overall_status", expected.get("expected_overall_status")),
        },
    }
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help="Default: docs/prize/whitepaper_manifest.yaml under root",
    )
    args = parser.parse_args()
    out = args.output or (args.root / "docs" / "prize" / "whitepaper_manifest.yaml")
    manifest = build_manifest(args.root)
    out.parent.mkdir(parents=True, exist_ok=True)
    if yaml is not None:
        text = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True)
    else:
        text = json.dumps(manifest, indent=2)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
