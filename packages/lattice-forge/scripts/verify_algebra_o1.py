#!/usr/bin/env python3
"""Deprecated wrapper — use ``lattice-forge-verify-algebra`` after ``pip install lattice-forge``."""
from lattice_forge.algebra.verify_o1 import main

if __name__ == "__main__":
    raise SystemExit(main())
