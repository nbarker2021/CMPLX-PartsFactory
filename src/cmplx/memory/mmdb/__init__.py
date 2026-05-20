"""
cmplx.memory.mmdb — Morphon Memory Database.

Provides the `memory` port on MorphonController. SQLite-backed,
stdlib-only. See INTERFACE.md and BRIDGE.md.
"""
from __future__ import annotations

from .provider import MMDBMemoryProvider
from .store import MMDB

__all__ = ["MMDB", "MMDBMemoryProvider"]
