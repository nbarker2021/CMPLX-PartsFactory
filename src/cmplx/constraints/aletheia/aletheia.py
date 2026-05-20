"""
Aletheia — the conservation-law admission layer.

See INTERFACE.md and BRIDGE.md alongside this package. This is the
first build of the admission flow; Golay correction (the historical
Aletheia3 extension) is reference material at `_history_reference/`
and can be added when callers need it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterable, Optional, Sequence

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


LawResult = tuple[bool, str]


class RejectionError(PermissionError):
    """Raised by `Aletheia.admit_strict()` when a morphon is rejected."""

    def __init__(self, law_name: str, reason: str) -> None:
        self.law_name = law_name
        self.reason = reason
        super().__init__(f"{law_name}: {reason}")


# ---------------------------------------------------------------------------
# Law base
# ---------------------------------------------------------------------------

class ConservationLaw(ABC):
    """Abstract base for a conservation law.

    Subclass and implement `evaluate(morphon)` returning
    `(admitted: bool, reason: str)`. The reason is for human/audit
    consumption; keep it short.
    """

    #: Stable name. Overridden by subclasses or set per-instance.
    name: str = "unnamed_law"

    @abstractmethod
    def evaluate(self, morphon: "Morphon") -> LawResult:
        ...

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"


# ---------------------------------------------------------------------------
# Aletheia provider
# ---------------------------------------------------------------------------

class Aletheia:
    """Holds an ordered chain of conservation laws and admits morphons
    against them.

    >>> aletheia = Aletheia()  # default law set
    >>> ok, why = aletheia.admit(morphon)
    """

    def __init__(self, laws: Optional[Iterable[ConservationLaw]] = None) -> None:
        if laws is None:
            from .laws import default_law_set  # avoid import cycle if any
            self._laws: list[ConservationLaw] = list(default_law_set())
        else:
            self._laws = list(laws)

    # -- registration ----------------------------------------------------

    def register_law(self, law: ConservationLaw) -> None:
        """Append a law to the end of the chain."""
        if not isinstance(law, ConservationLaw):
            raise TypeError(f"expected ConservationLaw, got {type(law).__name__}")
        self._laws.append(law)

    def register_laws(self, laws: Sequence[ConservationLaw]) -> None:
        for law in laws:
            self.register_law(law)

    def clear(self) -> None:
        """Remove all laws. Useful for tests."""
        self._laws.clear()

    @property
    def laws(self) -> tuple[ConservationLaw, ...]:
        return tuple(self._laws)

    # -- ConstraintsProvider protocol ------------------------------------

    def admit(self, morphon: "Morphon") -> LawResult:
        """Walk the laws in order. Return (True, "") if every law admits;
        otherwise (False, reason) from the first refusing law.
        """
        for law in self._laws:
            try:
                ok, reason = law.evaluate(morphon)
            except Exception as exc:
                return False, f"{law.name} raised {type(exc).__name__}: {exc}"
            if not ok:
                return False, f"{law.name}: {reason}"
        return True, ""

    # -- Strict variant for callers that prefer exceptions ---------------

    def admit_strict(self, morphon: "Morphon") -> None:
        for law in self._laws:
            ok, reason = law.evaluate(morphon)
            if not ok:
                raise RejectionError(law.name, reason)

    def __repr__(self) -> str:
        names = [law.name for law in self._laws]
        return f"<Aletheia laws={names}>"
