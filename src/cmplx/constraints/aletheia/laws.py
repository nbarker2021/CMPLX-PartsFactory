"""
Built-in conservation laws.

Each law subclasses `ConservationLaw` and implements `evaluate()`.
The default law set covers basic well-formedness; richer laws are
registered by callers via `Aletheia.register_law()`.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Mapping

from .aletheia import ConservationLaw, LawResult

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


class PayloadIsMappingLaw(ConservationLaw):
    """Payload must be a Mapping (dict-shaped)."""

    name = "payload_is_mapping"

    def evaluate(self, morphon: "Morphon") -> LawResult:
        if not isinstance(morphon.payload, Mapping):
            return False, (
                f"payload must be a Mapping, got "
                f"{type(morphon.payload).__name__}"
            )
        return True, ""


class PayloadNotEmptyLaw(ConservationLaw):
    """Payload must have at least one key."""

    name = "payload_not_empty"

    def evaluate(self, morphon: "Morphon") -> LawResult:
        if not morphon.payload:
            return False, "payload is empty"
        return True, ""


class PayloadSizeLimitLaw(ConservationLaw):
    """Serialized payload must be under `max_bytes`. Default 1 MB.

    Catches accidental payloads that are unreasonably large (e.g.,
    a giant log dump that shouldn't be stored as a morphon).
    """

    name = "payload_size_limit"

    def __init__(self, max_bytes: int = 1_000_000) -> None:
        self.max_bytes = max_bytes

    def evaluate(self, morphon: "Morphon") -> LawResult:
        try:
            serialized = json.dumps(morphon.payload, default=str)
        except (TypeError, ValueError) as exc:
            return False, f"payload not JSON-serializable: {exc}"
        size = len(serialized.encode("utf-8"))
        if size > self.max_bytes:
            return False, (
                f"payload size {size} exceeds limit {self.max_bytes}"
            )
        return True, ""


class StateTransitionWellFormedLaw(ConservationLaw):
    """Refuses morphons that are already in a terminal state when asked
    to be admitted — admitting a COMPLETED/FAILED/CANCELLED morphon
    means nothing.
    """

    name = "state_admittable"

    def evaluate(self, morphon: "Morphon") -> LawResult:
        if morphon.is_terminal():
            return False, (
                f"morphon is in terminal state {morphon.state.name}; "
                f"cannot admit"
            )
        return True, ""


class NoForbiddenKeysLaw(ConservationLaw):
    """Reject morphons whose payload contains any of the named keys.

    Useful as a basic privacy guard (e.g., NoForbiddenKeysLaw('password',
    'api_key', 'ssn')). The historical Aletheia2 used Golay-coded
    forbidden-region detection; this is the simpler keyword form.
    """

    name = "no_forbidden_keys"

    def __init__(self, *forbidden_keys: str) -> None:
        self.forbidden = frozenset(forbidden_keys)
        if forbidden_keys:
            self.name = f"no_forbidden_keys[{','.join(sorted(forbidden_keys))}]"

    def evaluate(self, morphon: "Morphon") -> LawResult:
        if not isinstance(morphon.payload, Mapping):
            # Defer to PayloadIsMappingLaw; we just pass.
            return True, ""
        found = self.forbidden & set(morphon.payload)
        if found:
            return False, f"forbidden keys present: {sorted(found)}"
        return True, ""


def default_law_set() -> tuple[ConservationLaw, ...]:
    """Default chain — cheap structural checks, ordered for fast rejection."""
    return (
        PayloadIsMappingLaw(),
        PayloadNotEmptyLaw(),
        StateTransitionWellFormedLaw(),
        PayloadSizeLimitLaw(max_bytes=1_000_000),
    )
