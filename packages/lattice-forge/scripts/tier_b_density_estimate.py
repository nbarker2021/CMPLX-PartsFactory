"""Optional Tier B center-column density estimate (non-blocking)."""

from __future__ import annotations

import argparse
import json

from lattice_forge.block_tower import rule30_center_column


def estimate_density(max_depth: int = 4096) -> dict:
    bits = rule30_center_column(max_depth)
    ones = sum(bits)
    return {
        "tier": "B",
        "script": "tier_b_density_estimate",
        "max_depth": max_depth,
        "ones": ones,
        "density": ones / max_depth if max_depth else 0.0,
        "obligation_id": "rule30.prize.nonperiodicity_density",
        "honesty": "CONJ",
        "blocking": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-depth", type=int, default=4096)
    args = parser.parse_args()
    report = estimate_density(max_depth=args.max_depth)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
