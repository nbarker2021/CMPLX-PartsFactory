"""
MorphonState — lifecycle states for a Morphon.

Adapted from the historical composed canonical at
`history/cmplx_pending/morphon/MorphonState.py` (4 variants merged).
The composed variant mixed Enum-style members with dataclass-style
attributes; this module keeps only the Enum (its consistent form
across variants) and exposes a small state-machine helper.
"""
from __future__ import annotations

from enum import Enum, auto
from typing import FrozenSet


class MorphonState(Enum):
    """
    Lifecycle states a Morphon traverses, from forge to terminal.

    Canonical flow:
        CREATED → VALIDATING → POLICY_CHECK → ROUTING → QUEUED
               → EXECUTING → CONSOLIDATING → COMPLETED
                                          → FAILED
                                          → CANCELLED

    Side-states (the executing branch may pause):
        EXECUTING → AWAITING_TOOL → EXECUTING
        EXECUTING → AWAITING_DATA → EXECUTING
    """

    CREATED = auto()
    VALIDATING = auto()
    POLICY_CHECK = auto()
    ROUTING = auto()
    QUEUED = auto()
    EXECUTING = auto()
    AWAITING_TOOL = auto()
    AWAITING_DATA = auto()
    CONSOLIDATING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


# Legal transitions: from_state -> set of allowed next states.
# Terminal states (COMPLETED, FAILED, CANCELLED) have empty sets;
# attempting to transition from a terminal state raises.
_TRANSITIONS: dict[MorphonState, FrozenSet[MorphonState]] = {
    MorphonState.CREATED:       frozenset({MorphonState.VALIDATING, MorphonState.CANCELLED}),
    MorphonState.VALIDATING:    frozenset({MorphonState.POLICY_CHECK, MorphonState.FAILED, MorphonState.CANCELLED}),
    MorphonState.POLICY_CHECK:  frozenset({MorphonState.ROUTING, MorphonState.FAILED, MorphonState.CANCELLED}),
    MorphonState.ROUTING:       frozenset({MorphonState.QUEUED, MorphonState.FAILED, MorphonState.CANCELLED}),
    MorphonState.QUEUED:        frozenset({MorphonState.EXECUTING, MorphonState.CANCELLED}),
    MorphonState.EXECUTING:     frozenset({
        MorphonState.AWAITING_TOOL, MorphonState.AWAITING_DATA,
        MorphonState.CONSOLIDATING, MorphonState.FAILED, MorphonState.CANCELLED,
    }),
    MorphonState.AWAITING_TOOL: frozenset({MorphonState.EXECUTING, MorphonState.FAILED, MorphonState.CANCELLED}),
    MorphonState.AWAITING_DATA: frozenset({MorphonState.EXECUTING, MorphonState.FAILED, MorphonState.CANCELLED}),
    MorphonState.CONSOLIDATING: frozenset({MorphonState.COMPLETED, MorphonState.FAILED}),
    MorphonState.COMPLETED:     frozenset(),
    MorphonState.FAILED:        frozenset(),
    MorphonState.CANCELLED:     frozenset(),
}


def can_transition(from_state: MorphonState, to_state: MorphonState) -> bool:
    """Return True if the transition is legal under the state machine."""
    return to_state in _TRANSITIONS.get(from_state, frozenset())


def assert_transition(from_state: MorphonState, to_state: MorphonState) -> None:
    """Raise ValueError if the transition is illegal."""
    if not can_transition(from_state, to_state):
        raise ValueError(
            f"illegal MorphonState transition: {from_state.name} -> {to_state.name}"
        )


def is_terminal(state: MorphonState) -> bool:
    """Return True if no further transitions are legal from `state`."""
    return not _TRANSITIONS.get(state, frozenset())
