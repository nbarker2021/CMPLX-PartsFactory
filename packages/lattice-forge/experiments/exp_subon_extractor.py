"""
exp_subon_extractor.py — Block-addressed Rule 30 extractor verification
and benchmarking.

Demonstrates that:
  1. The block tower (Rule30Checkpoints) round-trips Rule 30 exactly.
  2. The block-addressed extractor's per-query latency is bounded by
     base_page and is effectively constant in n.
  3. The D4 algebraic substrate verifies (state count, root count,
     sub-block sizes).

The previous incarnation of this experiment tried to predict 64-bit
futures from a 3-bit (L,C,R) key and produced ~82% accuracy — that
approach is information-theoretically impossible because Rule 30's center
column is full-entropy. This rewritten experiment exercises the *honest*
Regime A reading: block-addressed I/O via hierarchical checkpoints.
"""
import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.block_tower import (
    Rule30Checkpoints,
    rule30_center_column,
    verify_block_tower,
)
from lattice_forge.block_d4 import verify_d4_block
from lattice_forge.rule30_block_extractor import (
    Rule30BlockExtractor,
    verify_extractor,
    benchmark_extractor,
)


def run_experiment():
    print("=" * 60)
    print("EXP: Block-Addressed Rule 30 Extractor (Regime A)")
    print("=" * 60)

    print("\n[1] D4 algebraic substrate (Regime B foundation)...")
    d4 = verify_d4_block()
    print(f"    status={d4['status']}  states={d4['state_count']}  "
          f"roots={d4['root_count']}  edges={d4['edge_count']}")

    print("\n[2] Block tower (checkpoint store)...")
    bt = verify_block_tower(max_depth=4096)
    print(f"    status={bt['status']}  build={bt['build_seconds']:.3f}s  "
          f"checkpoints={bt['info']['checkpoints_stored']}  "
          f"avg_query={bt['avg_query_seconds']*1000:.3f}ms")
    if bt["mismatches"]:
        for m in bt["mismatches"][:5]:
            print(f"    MISMATCH: {m}")

    print("\n[3] Block-addressed extractor correctness (depth 4096)...")
    ve = verify_extractor(max_depth=4096)
    print(f"    status={ve['status']}  "
          f"individual_mismatches={ve['individual_mismatch_count']}  "
          f"range_match_rate={ve['range_match_rate']:.4f}")

    print("\n[4] Per-query latency vs depth...")
    bm = benchmark_extractor([64, 256, 1024, 4096])
    for r in bm["results"]:
        print(f"    n={r['n']:>5}: {r['avg_query_s']*1000:.4f} ms/query")
    print(f"    ratio(max/min) = {bm['max_over_min_ratio']:.3f}  "
          f"(should be ~1 for constant-time queries)")

    print("\n[5] Range read (depth 1..4096)...")
    ex = Rule30BlockExtractor(max_depth=4096)
    t0 = time.perf_counter()
    rr = ex.bit_range(1, 4096)
    bf = rule30_center_column(4096)
    matches = sum(1 for a, b in zip(rr["bits"], bf) if a == b)
    elapsed = time.perf_counter() - t0
    print(f"    bits_read={rr['length']}  matches={matches}/{len(bf)}  "
          f"elapsed={elapsed*1000:.2f}ms")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    overall_pass = (
        d4["status"] == "pass"
        and bt["status"] == "pass"
        and ve["status"] == "pass"
        and matches == len(bf)
    )
    print(f"D4 substrate:           {d4['status']}")
    print(f"Block tower:            {bt['status']}")
    print(f"Extractor correctness:  {ve['status']}")
    print(f"Range read full pass:   {matches == len(bf)}")
    print(f"Constant-time query:    "
          f"{bm['max_over_min_ratio']:.3f}x ratio across 64x depth span")
    print(f"\nOverall: {'PASS' if overall_pass else 'FAIL'}")

    results = {
        "experiment": "exp_subon_extractor",
        "d4_block": d4,
        "block_tower": {k: bt[k] for k in bt if k != "mismatches"},
        "extractor_verify": {k: ve[k] for k in ve if k != "individual_mismatches"},
        "benchmark": bm,
        "range_read_4096_matches": matches,
        "overall_status": "pass" if overall_pass else "fail",
    }
    out_path = os.path.join(os.path.dirname(__file__), "results_subon_extractor.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")
    return results


if __name__ == "__main__":
    run_experiment()
