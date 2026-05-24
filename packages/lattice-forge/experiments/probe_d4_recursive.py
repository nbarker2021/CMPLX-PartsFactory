"""
probe_d4_recursive.py — Recursive D_4 / second-sheet probe (LEVEL 0–2).

Continues the interrupted background probe on axis-3 sheet sub-sequences.

LEVEL 0: D_4 antipodal decomposition (4-symbol labels + binary sheets).
LEVEL 1: Per-axis sheet sub-sequences — marginal H(1), conditional H(2|1), LZ ratio.
LEVEL 2: Reapply Rule 30 (and XOR/OR variants) to each axis sheet stream;
         measure whether a "second sheet" carries further structure.

Does NOT claim log-time prize solved; records what compresses vs what does not.
"""
from __future__ import annotations

import json
import math
import os
import sys
import zlib
from collections import Counter
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.chart_codec_d4 import (
    encode_d4,
    rule30_chart_trajectory,
    axis_sheet_subsequence,
)


def shannon_bits(counts: dict[Any, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum(
        (c / total) * math.log2(c / total) for c in counts.values() if c > 0
    )


def ngram_entropy(seq: list, n: int) -> float:
    if len(seq) < n:
        return 0.0
    grams = Counter(tuple(seq[i : i + n]) for i in range(len(seq) - n + 1))
    return shannon_bits(dict(grams))


def conditional_entropy(seq: list, order: int) -> float:
    if order < 1:
        return 0.0
    if order == 1:
        return ngram_entropy(seq, 1)
    return ngram_entropy(seq, order) - ngram_entropy(seq, order - 1)


def lz_ratio(seq: list[int]) -> dict[str, Any]:
    raw = bytes(seq)
    if not raw:
        return {"raw_bytes": 0, "compressed_bytes": 0, "lz_ratio": 0.0}
    compressed = zlib.compress(raw, level=9)
    return {
        "raw_bytes": len(raw),
        "compressed_bytes": len(compressed),
        "lz_ratio": len(compressed) / len(raw),
    }


def rule30_step_binary(bits: list[int]) -> list[int]:
    """One Rule 30 step on a 1D binary row (implicit-zero boundaries)."""
    w = len(bits)
    out = [0] * w
    prev_l = 0
    for i in range(w):
        c = bits[i]
        r = bits[i + 1] if i + 1 < w else 0
        out[i] = prev_l ^ (c | r)
        prev_l = c
    return out


def binary_pass(row: list[int], op: str = "rule30") -> list[int]:
    """One local update on the full row (same length)."""
    if op == "rule30":
        return rule30_step_binary(row)
    if op == "xor_neighbor":
        new = [0] * len(row)
        for i in range(len(row)):
            l = row[i - 1] if i > 0 else 0
            r = row[i + 1] if i + 1 < len(row) else 0
            new[i] = l ^ r
        return new
    if op == "or_neighbor":
        new = [0] * len(row)
        for i in range(len(row)):
            l = row[i - 1] if i > 0 else 0
            r = row[i + 1] if i + 1 < len(row) else 0
            new[i] = l | r
        return new
    raise ValueError(f"unknown op: {op}")


def evolve_binary(seq: list[int], steps: int, op: str = "rule30") -> list[int]:
    """Apply `steps` full-row passes; output length equals input length."""
    row = list(seq)
    for _ in range(max(steps, 0)):
        row = binary_pass(row, op=op)
    return row


def label_transition_matrix(labels: list[int]) -> dict[str, Any]:
    counts: dict[tuple[int, int], int] = Counter()
    for i in range(len(labels) - 1):
        counts[(labels[i], labels[i + 1])] += 1
    matrix = [[0 for _ in range(4)] for _ in range(4)]
    for (a, b), c in counts.items():
        matrix[a][b] = c
    row_totals = [sum(row) for row in matrix]
    row_probs = [
        [matrix[i][j] / row_totals[i] if row_totals[i] else 0.0 for j in range(4)]
        for i in range(4)
    ]
    return {
        "counts": {f"{a}->{b}": c for (a, b), c in sorted(counts.items())},
        "matrix": matrix,
        "row_probs": row_probs,
        "h_label_given_prev": conditional_entropy(labels, 2),
    }


def analyze_stream(seq: list[int], signal: str, level: int) -> dict[str, Any]:
    if not seq:
        return {
            "level": level,
            "signal": signal,
            "length": 0,
            "H1": 0.0,
            "H2_given_1": 0.0,
            "lz_ratio": 0.0,
        }
    h1 = ngram_entropy(seq, 1)
    h2 = conditional_entropy(seq, 2)
    lz = lz_ratio(seq)
    return {
        "level": level,
        "signal": signal,
        "length": len(seq),
        "H1": round(h1, 6),
        "H2_given_1": round(h2, 6),
        "lz_ratio": round(lz["lz_ratio"], 6),
        "marginal_counts": dict(Counter(seq)),
    }


def probe_level2(seq: list[int], prefix: str) -> list[dict[str, Any]]:
    """Reapply Rule 30 / XOR / OR as full-row passes on the sheet sub-sequence."""
    if len(seq) < 32:
        return []
    results: list[dict[str, Any]] = []
    for op in ("rule30", "xor_neighbor", "or_neighbor"):
        for steps in (1, 2, 4):
            evolved = evolve_binary(seq, steps=steps, op=op)
            sig = f"{prefix}_{op}_pass{steps}"
            results.append(analyze_stream(evolved, sig, level=2))
    return results


def main(max_depth: int = 16384) -> dict[str, Any]:
    print("=" * 72)
    print("PROBE: D_4 recursive / second-sheet (LEVEL 0–2)")
    print(f"max_depth={max_depth}")
    print("=" * 72)

    traj = rule30_chart_trajectory(max_depth)
    enc = encode_d4(traj)
    labels = enc["labels"]
    sheets = enc["sheets"]

    rows: list[dict[str, Any]] = []

    # LEVEL 0 — full streams
    rows.append(analyze_stream(labels, "labels_all", level=0))
    rows.append(analyze_stream(sheets, "sheets_all", level=0))
    rows.append(label_transition_matrix(labels) | {"signal": "label_transitions", "level": 0})

    print("\n[LEVEL 0] full chart decomposition")
    for r in rows[:2]:
        print(
            f"  {r['signal']:16} len={r['length']:>6}  "
            f"H1={r['H1']:.4f}  H2|1={r['H2_given_1']:.4f}  LZ={r['lz_ratio']:.4f}"
        )

    # LEVEL 1 — per-axis sheet sub-sequences
    print("\n[LEVEL 1] per-axis sheet sub-sequences")
    level1: list[dict[str, Any]] = []
    for axis in range(4):
        sub = axis_sheet_subsequence(enc, axis)
        sig = f"axis{axis}_sheet"
        row = analyze_stream(sub, sig, level=1)
        level1.append(row)
        rows.append(row)
        print(
            f"  {sig:16} len={row['length']:>6}  "
            f"H1={row['H1']:.4f}  H2|1={row['H2_given_1']:.4f}  LZ={row['lz_ratio']:.4f}"
        )

    # LEVEL_0 label stream restricted to axis-3 visit depths (for comparison)
    axis3_mask = [a == 3 for a in labels]
    label_at_axis3 = [labels[i] for i, m in enumerate(axis3_mask) if m]
    rows.append(analyze_stream(label_at_axis3, "label_at_axis3_depths", level=1))

    # LEVEL 2 — reapply on axis sheets (focus axis 3 = T_BIJECTIVE doublet)
    print("\n[LEVEL 2] reapply Rule 30 / XOR / OR on axis sheet streams")
    level2: list[dict[str, Any]] = []
    for axis in range(4):
        sub = axis_sheet_subsequence(enc, axis)
        for r in probe_level2(sub, f"axis{axis}_sheet"):
            level2.append(r)
            rows.append(r)
            if axis == 3:
                print(
                    f"  {r['signal']:28} len={r['length']:>4}  "
                    f"H1={r['H1']:.4f}  H2|1={r['H2_given_1']:.4f}  LZ={r['lz_ratio']:.4f}"
                )

    # LEVEL 2b — iterative scalar reapply: stack Rule30 passes on axis-3 sheet
    print("\n[LEVEL 2b] iterative Rule30 passes on axis-3 sheet (quadratic stack)")
    a3 = axis_sheet_subsequence(enc, 3)
    iterative: list[dict[str, Any]] = []
    stacked = list(a3)
    for depth in range(1, 4):
        stacked = evolve_binary(stacked, steps=1, op="rule30")
        sig = f"axis3_iter_rule30_pass{depth}"
        r = analyze_stream(stacked, sig, level=2)
        iterative.append(r)
        rows.append(r)
        print(
            f"  {sig:28} len={r['length']:>4}  "
            f"H1={r['H1']:.4f}  H2|1={r['H2_given_1']:.4f}  LZ={r['lz_ratio']:.4f}"
        )

    summary_table = [
        {
            "level": r.get("level"),
            "signal": r.get("signal"),
            "H1": r.get("H1"),
            "H2_given_1": r.get("H2_given_1"),
            "lz_ratio": r.get("lz_ratio"),
            "length": r.get("length"),
        }
        for r in rows
        if "H1" in r
    ]

    result = {
        "max_depth": max_depth,
        "trajectory_length": len(traj),
        "summary_table": summary_table,
        "level0": rows[:3],
        "level1_axis_sheets": level1,
        "level2_reapply": level2,
        "level2b_iterative_axis3": iterative,
        "interpretation": {
            "axis3_sheet_level1": next(r for r in level1 if r["signal"] == "axis3_sheet"),
            "best_level2_axis3": min(
                (r for r in level2 if r["signal"].startswith("axis3")),
                key=lambda x: x["lz_ratio"],
                default={},
            ),
            "prize_depth_only_shortcut": "CONJ",
            "note": (
                "Axis-3 sheet shows measurable memory (H2|1 < H1) at LEVEL 1; "
                "LEVEL 2 reapply does not collapse entropy below ~1 bit/symbol. "
                "Label stream remains ~2 bits/symbol. No log-time addressing "
                "from D_4 decomposition alone."
            ),
        },
    }

    out = os.path.join(os.path.dirname(__file__), "results_probe_d4_recursive.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nSaved to {out}")
    return result


if __name__ == "__main__":
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 16384
    main(depth)
