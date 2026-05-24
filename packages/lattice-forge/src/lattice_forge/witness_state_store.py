"""In-memory witnessed-state table (per Forge instance)."""

from __future__ import annotations

from typing import Any


class WitnessStateStore:
    """O(1) lookup for regime-encode payloads keyed by canonical state keys."""

    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}

    def put(self, state_key: str, payload: dict[str, Any]) -> None:
        self._entries[state_key] = dict(payload)

    def get(self, state_key: str) -> dict[str, Any] | None:
        return self._entries.get(state_key)

    def has(self, state_key: str) -> bool:
        return state_key in self._entries
