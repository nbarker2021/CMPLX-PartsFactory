#!/usr/bin/env python3
"""Deprecated wrapper — use ``lattice-forge-lattice-space`` after ``pip install lattice-forge``."""
from lattice_forge.backwalk.runner import main_lattice_space

if __name__ == "__main__":
    raise SystemExit(main_lattice_space())
