#!/usr/bin/env python3
"""Deprecated: use validate_superpermutations.py (--require 5)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO / "scripts" / "validate_superpermutations.py"


def main() -> int:
    return subprocess.call(
        [sys.executable, str(_SCRIPT), "--require", "5"],
        cwd=str(_REPO),
    )


if __name__ == "__main__":
    raise SystemExit(main())
