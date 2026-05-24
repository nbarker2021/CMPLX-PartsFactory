#!/usr/bin/env python3
"""Cross-check O(1) registry against SymPy (theory extra only; not runtime hot path)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from lattice_forge.algebra.o1_registry import (  # noqa: E402
    E8_ROOT_COUNT,
    E8_WEYL_ORDER,
    WEYL_ORDER,
    root_count_ade,
    weyl_order,
)
from lattice_forge.ledger.roots import root_system_E8  # noqa: E402


def _sympy_checks() -> tuple[list[str], bool]:
    """Return (errors, sympy_ran)."""
    errors: list[str] = []
    try:
        from sympy.liealgebras.cartan_type import CartanType
        from sympy.liealgebras.weyl_group import WeylGroup
    except ImportError:
        return [], False

    for label, expected in WEYL_ORDER.items():
        series = label[0]
        rank = int(label[1:]) if len(label) > 1 else 1
        if series == "G":
            ct = CartanType("G2")
        elif series == "F":
            ct = CartanType("F4")
        elif series == "E":
            ct = CartanType(["E", rank])
        else:
            ct = CartanType([series, rank])
        got = WeylGroup(ct).order()
        if int(got) != expected:
            errors.append(f"Weyl order {label}: registry={expected} sympy={got}")
    return errors, True


def _local_checks() -> list[str]:
    errors: list[str] = []
    e8 = root_system_E8()
    if len(e8.roots) != E8_ROOT_COUNT:
        errors.append(f"E8 root count: registry={E8_ROOT_COUNT} built={len(e8.roots)}")
    if weyl_order("E8") != E8_WEYL_ORDER:
        errors.append("weyl_order(E8) mismatch")
    if root_count_ade("E", 8) != E8_ROOT_COUNT:
        errors.append("root_count_ade E8 mismatch")
    return errors


def main() -> int:
    sympy_errors, sympy_ran = _sympy_checks()
    errors = _local_checks() + sympy_errors
    if errors:
        for e in errors:
            print("FAIL:", e)
        return 1
    suffix = " + SymPy" if sympy_ran else " (SymPy skipped; install [theory])"
    print("PASS: O(1) registry matches built roots" + suffix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
