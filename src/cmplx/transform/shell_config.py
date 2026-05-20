"""Shell configuration — shared by MorphonShell and rule libraries."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ShellConfig:
    max_arity: int = 8
    bond_separator: str = "|"
    gate_mode: str = "govern"
    language: str = "any"


__all__ = ["ShellConfig"]
