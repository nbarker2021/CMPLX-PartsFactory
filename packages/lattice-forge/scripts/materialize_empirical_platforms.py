#!/usr/bin/env python3
"""Build empirical/platforms.manifest.jsonl from claims/registry.jsonl + umbrella proof keys."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lattice_forge.empirical.exhaust import ladder_for_mode
from lattice_forge.empirical.manifest import EmpiricalPlatform, write_platform_manifest

CLAIMS = ROOT / "claims" / "registry.jsonl"

UMBRELLA_PROOF_KEYS = [
    ("TRANSPORT_FIELD_ADDRESS", "verify_rule30_mandelbrot_field_address", "pass_with_open_gaps", 1),
    ("TRANSPORT_EXIT_TRAJECTORY", "verify_rule30_exit_trajectory", "pass_with_open_gaps", 1),
    ("QUAD_OLOID", "verify_quad_oloid", "pass_with_open_gaps", 2),
    ("VOA_LOOKUP", "verify_voa_lookup_harness", "CONJ", 1),
    ("WITNESS-INDEX", "Forge.witnessed_lookup+regime_encode", "PROVEN", 1),
]


def _ladder(label: str) -> list[int]:
    if label == "CONJ":
        return ladder_for_mode("exhaustive")
    if label in {"PROVEN", "TRANSPORTED"}:
        return ladder_for_mode("exhaustive")
    return ladder_for_mode("standard")


def main() -> int:
    platforms: list[EmpiricalPlatform] = []
    seen: set[str] = set()

    for line in CLAIMS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        c = json.loads(line)
        cid = c["claim_id"]
        seen.add(cid)
        platforms.append(
            EmpiricalPlatform(
                claim_id=cid,
                platform_id=cid,
                verifier_id=c.get("verifier_id", ""),
                honesty_label=c.get("honesty_label", ""),
                exhaustion_mode="exhaustive" if c.get("honesty_label") == "CONJ" else "standard",
                depth_ladder=_ladder(c.get("honesty_label", "")),
                falsify_break=c.get("falsify_break"),
                proof_key=c.get("proof_key"),
                ring=int(c.get("ring", 1)),
                kind=c.get("kind", "theorem"),
                statement_ref=c.get("statement_ref", ""),
                notes="from claims/registry.jsonl",
            )
        )

    for proof_key, verifier_id, label, ring in UMBRELLA_PROOF_KEYS:
        cid = proof_key if proof_key not in seen else f"umbrella.{proof_key}"
        platforms.append(
            EmpiricalPlatform(
                claim_id=cid,
                platform_id=cid,
                verifier_id=verifier_id,
                honesty_label=label,
                exhaustion_mode="exhaustive" if label == "CONJ" else "standard",
                depth_ladder=_ladder(label),
                proof_key=proof_key,
                ring=ring,
                kind="umbrella_harness",
                notes="umbrella harness row (run_all_proofs)",
            )
        )

    out = write_platform_manifest(platforms)
    print(f"Wrote {len(platforms)} platforms -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
