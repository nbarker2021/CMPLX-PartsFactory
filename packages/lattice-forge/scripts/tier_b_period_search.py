"""Optional Tier B period search (non-blocking; CONJ obligations unchanged)."""

from __future__ import annotations

import argparse
import json

from lattice_forge.block_tower import rule30_center_column


def search_periods(max_period: int = 128, sample_depth: int = 512) -> dict:
    bits = rule30_center_column(sample_depth)
    hits = []
    for p in range(2, max_period + 1):
        if all(bits[i] == bits[i + p] for i in range(min(len(bits) - p, 64))):
            hits.append(p)
    return {
        "tier": "B",
        "script": "tier_b_period_search",
        "max_period": max_period,
        "sample_depth": sample_depth,
        "period_hits_in_prefix": hits,
        "obligation_id": "rule30.prize.nonperiodicity_density",
        "honesty": "CONJ",
        "blocking": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-period", type=int, default=128)
    parser.add_argument("--sample-depth", type=int, default=512)
    args = parser.parse_args()
    report = search_periods(max_period=args.max_period, sample_depth=args.sample_depth)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
