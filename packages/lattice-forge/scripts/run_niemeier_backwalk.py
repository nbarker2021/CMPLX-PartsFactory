#!/usr/bin/env python3
"""Deprecated wrapper — use ``lattice-forge-backwalk`` after ``pip install lattice-forge``."""
from lattice_forge.backwalk.runner import main_backwalk

if __name__ == "__main__":
    raise SystemExit(main_backwalk())
