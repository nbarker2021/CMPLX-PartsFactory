#!/usr/bin/env python3
"""Deprecated wrapper — use ``lattice-forge-weyl-bond`` after ``pip install lattice-forge``."""
from lattice_forge.backwalk.runner import main_weyl_orchestrate

if __name__ == "__main__":
    raise SystemExit(main_weyl_orchestrate())
