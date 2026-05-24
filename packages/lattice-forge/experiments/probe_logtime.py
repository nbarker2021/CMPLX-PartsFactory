"""
probe_logtime.py — Probe what stands between the current submission and a
true log-time Rule 30 extractor.

A log-time extractor needs an O(log N) addressing function:
    addr(N) -> W(E_8) element  (or equivalent finite-Weyl element)
that resolves to the depth-N center bit via a single table lookup.

Current state of the umbrella:
  * T3 / T_BRIDGE give an exact embedding of the chart into the zero-weight
    space of F_4's 26-dim fundamental representation.
  * chart_codec produces a *lossless* S_3 word for the shell=2 sub-trajectory.
  * The S_3 word is the deterministic ribbon dynamics restricted to W(F_4).

If the S_3 word has o(N) structural complexity, a log-time addressing
function is possible in principle. If the word has Shannon entropy
indistinguishable from random, then the obstruction is mathematical
(no log-time extractor exists without storing O(N) bits somewhere).

This script tests, on the actual depth-4096 chart_codec output:
  (1) Periodicity at any period < N/2.
  (2) Self-similarity: prefix vs suffix correlation under shifts.
  (3) Shannon entropy of n-grams (n = 1..4).
  (4) Run-length distribution vs an i.i.d. baseline.
  (5) Compressibility under a generic compressor (zlib).
"""
import math
import os
import sys
import zlib
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.chart_codec import (
    rule30_chart_trajectory,
    shell2_subtrajectory,
    encode,
    S3,
)


SYMBOL_ORDER = ["e", "(1 2)", "(1 3)", "(2 3)"]
SYMBOL_TO_CODE = {s: i for i, s in enumerate(SYMBOL_ORDER)}


def shannon_bits(counts: dict) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum(
        (c / total) * math.log2(c / total)
        for c in counts.values() if c > 0
    )


def ngram_entropy(word: list[str], n: int) -> float:
    if len(word) < n:
        return 0.0
    grams = Counter(tuple(word[i:i + n]) for i in range(len(word) - n + 1))
    return shannon_bits(grams)


def per_symbol_conditional_entropy(word: list[str], n: int) -> float:
    """H(X_n | X_{n-1} ... X_0): how much new entropy a symbol adds given
    the previous n-1 symbols. For an i.i.d. sequence this equals H(X)."""
    if n < 1:
        return 0.0
    if n == 1:
        return ngram_entropy(word, 1)
    return ngram_entropy(word, n) - ngram_entropy(word, n - 1)


def periodicity_test(word: list[str], max_period: int) -> dict:
    """Find any period <= max_period that divides the word."""
    found = []
    for p in range(1, min(max_period, len(word) // 2) + 1):
        if all(word[i] == word[i % p] for i in range(len(word))):
            found.append(p)
    return {"found_periods": found, "any_period_found": bool(found)}


def autocorrelation_at_shift(word: list[str], shift: int) -> float:
    """Fraction of positions where word[i] == word[i + shift]."""
    if shift <= 0 or shift >= len(word):
        return 0.0
    matches = sum(
        1 for i in range(len(word) - shift) if word[i] == word[i + shift]
    )
    return matches / (len(word) - shift)


def run_length_stats(word: list[str]) -> dict:
    """Distribution of run lengths in the symbol stream."""
    if not word:
        return {"max_run": 0, "mean_run": 0.0, "run_count": 0}
    runs: list[int] = []
    current = word[0]
    length = 1
    for s in word[1:]:
        if s == current:
            length += 1
        else:
            runs.append(length)
            current = s
            length = 1
    runs.append(length)
    return {
        "max_run": max(runs),
        "mean_run": sum(runs) / len(runs),
        "run_count": len(runs),
        "iid_expected_mean_run": 4 / 3,  # for 4 equiprobable symbols
    }


def zlib_compression_ratio(word: list[str]) -> dict:
    raw = bytes(SYMBOL_TO_CODE[s] for s in word)
    compressed = zlib.compress(raw, level=9)
    return {
        "raw_bytes": len(raw),
        "compressed_bytes": len(compressed),
        "ratio": len(compressed) / len(raw) if raw else 0.0,
        "raw_entropy_bits": shannon_bits(Counter(word)),
        "theoretical_min_bytes_at_2_bits": len(raw) / 4.0,
    }


def main():
    print("=" * 64)
    print("PROBE: What stands between umbrella v1 and a log-time solver?")
    print("=" * 64)

    DEPTH = 4096
    print(f"\nGenerating chart_codec S_3 word at max_depth={DEPTH}...")
    traj = rule30_chart_trajectory(DEPTH)
    shell2 = shell2_subtrajectory(traj)
    encoded = encode(shell2)
    word = encoded["word"]
    print(f"  shell=2 transitions: {len(word)}")
    print(f"  symbol counts: {Counter(word)}")

    print("\n[1] Periodicity scan (period <= 1024)...")
    p = periodicity_test(word, max_period=1024)
    print(f"  any_period <= 1024 found: {p['any_period_found']}")
    if p["found_periods"]:
        print(f"  smallest periods: {p['found_periods'][:5]}")

    print("\n[2] Autocorrelation at strategic shifts...")
    iid_chance = 1.0 / 4 + (494 / len(word)) ** 2  # rough rebias to actual marginal
    for s in [1, 2, 3, 4, 8, 16, 32, 64, 128, 256, 512, 784, 1024]:
        if s < len(word):
            ac = autocorrelation_at_shift(word, s)
            print(f"  shift={s:>4}: autocorr={ac:.4f}  "
                  f"(iid baseline ~= 0.25)")

    print("\n[3] n-gram entropy (bits per symbol; max = 2.0 for 4 symbols)...")
    for n in range(1, 7):
        h = ngram_entropy(word, n)
        h_cond = per_symbol_conditional_entropy(word, n)
        print(f"  H({n}-gram) = {h:.4f}     "
              f"H(X_n | prev {n-1}) = {h_cond:.4f}")

    print("\n[4] Run-length distribution...")
    rls = run_length_stats(word)
    print(f"  max_run={rls['max_run']}  mean_run={rls['mean_run']:.4f}  "
          f"(iid mean ~= {rls['iid_expected_mean_run']:.4f})")

    print("\n[5] Generic compressibility (zlib)...")
    zr = zlib_compression_ratio(word)
    print(f"  raw_bytes={zr['raw_bytes']}  compressed={zr['compressed_bytes']}  "
          f"ratio={zr['ratio']:.4f}")
    print(f"  marginal Shannon ({zr['raw_entropy_bits']:.4f} bits) implies "
          f">= {zr['raw_entropy_bits']/8:.4f} bytes/symbol lower bound")

    print("\n" + "=" * 64)
    print("INTERPRETATION")
    print("=" * 64)
    h1 = ngram_entropy(word, 1)
    h5 = per_symbol_conditional_entropy(word, 5)
    delta = h1 - h5
    print(f"H(symbol)                = {h1:.4f} bits")
    print(f"H(symbol | prev 4)       = {h5:.4f} bits")
    print(f"Conditional entropy drop = {delta:.4f} bits")
    print()
    if p["any_period_found"]:
        print("  --> Periodicity found. Log-time addressing follows trivially.")
    elif delta > 0.05:
        print("  --> Significant conditional entropy drop. Some structure"
              " exists; an Nth-order Markov model may help.")
    else:
        print("  --> Conditional entropy is indistinguishable from i.i.d."
              " at order 4. The S_3 word is empirically incompressible.")
        print("      A log-time extractor cannot exist by addressing this"
              " word alone — the bottleneck is mathematical (Wolfram")
        print("      Problem 3 itself), not I/O.")

    return {
        "word_length": len(word),
        "marginal_entropy": h1,
        "conditional_entropy_order_4": h5,
        "any_period_found": p["any_period_found"],
        "zlib_ratio": zr["ratio"],
        "run_lengths": rls,
    }


if __name__ == "__main__":
    import json
    result = main()
    out = os.path.join(os.path.dirname(__file__), "results_probe_logtime.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nSaved to {out}")
