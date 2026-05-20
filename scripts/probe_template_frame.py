"""
Probe how the substrate handles non-palindromic, arbitrary text
fragments — the actual practical question the user asked about.

The substrate is built on concentric palindromic rings (s[0]=s[7],
s[1]=s[6], s[2]=s[5]). The earlier `template-stats` sweep showed 100%
forced cells under that construction — but that's mathematically
guaranteed by the enumeration. The interesting question is:

   Given a fragment of real text (which is generally NOT palindromic),
   does the substrate provide any usable constraint information?

We test three things:

  1. Partial-shell queries: fix positions {0,1,6,7} from real text
     and ask for completions of positions {2,3,4,5}. This is the
     'outer shell template' — known from the substrate, with the
     inner positions free.

  2. Slot-coverage transitivity: if positions 0,1,2,5,6,7 are each
     individually solved, then ANY combination of values at those
     positions is reachable by transitivity. Verify by sampling
     random target patterns at those 6 positions and counting hits.

  3. Letter-anywhere queries: for a single letter 'L', count how many
     entries in the substrate contain 'L' at any position. Tests the
     user's claim: 'if you have any full a-z in any slot, you have
     every combination with any of those letters'.
"""
from __future__ import annotations

import json
import random
import sqlite3
import sys
from collections import Counter
from pathlib import Path


DB_PATH = Path("data/token_index.sqlite")
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
SAMPLES = 200


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        sys.exit(f"DB not found: {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def test_partial_shell(con: sqlite3.Connection) -> dict:
    """Pick random (pos0, pos1, pos6, pos7) tuples and ask: does the
    substrate have ANY entry matching this outer shell? If yes, how
    many distinct (pos2,pos3,pos4,pos5) completions does it admit?"""
    rng = random.Random(0)
    hits = 0
    admit_sizes: list[int] = []

    sql = (
        "SELECT substr(concat, 3, 4) AS inner "
        "FROM token_bonds WHERE "
        "substr(concat, 1, 1) = ? AND substr(concat, 2, 1) = ? "
        "AND substr(concat, 7, 1) = ? AND substr(concat, 8, 1) = ? "
        "AND case_mode = 'lower' AND language = 'any'"
    )
    for _ in range(SAMPLES):
        p0 = rng.choice(ALPHABET)
        p1 = rng.choice(ALPHABET)
        p6 = rng.choice(ALPHABET)
        p7 = rng.choice(ALPHABET)
        rows = con.execute(sql, (p0, p1, p6, p7)).fetchall()
        if rows:
            hits += 1
            admit_sizes.append(len(set(r[0] for r in rows)))
        else:
            admit_sizes.append(0)
    nonzero = [n for n in admit_sizes if n > 0]
    return {
        "samples": SAMPLES,
        "hit_count": hits,
        "hit_rate_pct": round(100.0 * hits / SAMPLES, 1),
        "avg_admit_size_when_hit": round(
            sum(nonzero) / max(len(nonzero), 1), 2
        ),
        "median_admit_size_when_hit": (
            sorted(nonzero)[len(nonzero) // 2] if nonzero else 0
        ),
        "max_admit_size": max(admit_sizes) if admit_sizes else 0,
    }


def test_partial_palindromic_shell(con: sqlite3.Connection) -> dict:
    """Same as above but constrain the query to palindromic shells
    (pos0=pos7, pos1=pos6), which IS the substrate's enumeration. The
    hit rate here is the structural ceiling — anything below this for
    non-palindromic queries is the cost of arbitrary text."""
    rng = random.Random(1)
    hits = 0
    admit_sizes: list[int] = []

    sql = (
        "SELECT substr(concat, 3, 4) AS inner "
        "FROM token_bonds WHERE "
        "substr(concat, 1, 1) = ? AND substr(concat, 2, 1) = ? "
        "AND substr(concat, 7, 1) = ? AND substr(concat, 8, 1) = ? "
        "AND case_mode = 'lower' AND language = 'any'"
    )
    for _ in range(SAMPLES):
        p0 = rng.choice(ALPHABET)
        p1 = rng.choice(ALPHABET)
        rows = con.execute(sql, (p0, p1, p1, p0)).fetchall()
        if rows:
            hits += 1
            admit_sizes.append(len(set(r[0] for r in rows)))
        else:
            admit_sizes.append(0)
    nonzero = [n for n in admit_sizes if n > 0]
    return {
        "samples": SAMPLES,
        "hit_count": hits,
        "hit_rate_pct": round(100.0 * hits / SAMPLES, 1),
        "avg_admit_size_when_hit": round(
            sum(nonzero) / max(len(nonzero), 1), 2
        ),
        "median_admit_size_when_hit": (
            sorted(nonzero)[len(nonzero) // 2] if nonzero else 0
        ),
    }


def test_letter_anywhere(con: sqlite3.Connection) -> dict:
    """For each letter, count how many lower-case any-language L3
    entries contain that letter at any position."""
    out: dict[str, int] = {}
    for letter in ALPHABET:
        cur = con.execute(
            "SELECT COUNT(*) FROM token_bonds "
            "WHERE bond_level = 3 AND case_mode = 'lower' AND language = 'any' "
            "AND concat LIKE ?",
            (f"%{letter}%",),
        )
        out[letter] = int(cur.fetchone()[0])
    return out


def test_real_text_fragments(con: sqlite3.Connection) -> dict:
    """Pull 4-char windows from realistic English bigram-rich words
    and probe whether their outer shell appears in the substrate."""
    samples = [
        "thethe", "andthe", "theand", "thathing", "ingthe",
        "ention", "ationof", "fromthe", "withthe", "ofthose",
        "people", "saidthe", "wherein", "between", "becoming",
        "however", "another", "process", "control", "without",
    ]
    hits = 0
    detail = []
    for s in samples:
        if len(s) < 4:
            continue
        # Use first 2 chars + last 2 chars as the outer shell prefix.
        p0, p1, p6, p7 = s[0], s[1], s[-2], s[-1]
        rows = con.execute(
            "SELECT substr(concat, 3, 4) FROM token_bonds WHERE "
            "substr(concat, 1, 1) = ? AND substr(concat, 2, 1) = ? "
            "AND substr(concat, 7, 1) = ? AND substr(concat, 8, 1) = ? "
            "AND case_mode = 'lower' AND language = 'english'",
            (p0, p1, p6, p7),
        ).fetchall()
        n = len(set(r[0] for r in rows))
        if n > 0:
            hits += 1
        detail.append({"fragment": s, "outer_shell": f"{p0}{p1}__{p6}{p7}", "admit_size": n})
    return {
        "total": len(samples),
        "hits": hits,
        "hit_rate_pct": round(100.0 * hits / len(samples), 1),
        "samples": detail,
    }


def main() -> None:
    con = connect()
    report = {
        "non_palindromic_shell": test_partial_shell(con),
        "palindromic_shell": test_partial_palindromic_shell(con),
        "letter_anywhere_counts": test_letter_anywhere(con),
        "real_text_fragments": test_real_text_fragments(con),
    }
    json.dump(report, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
