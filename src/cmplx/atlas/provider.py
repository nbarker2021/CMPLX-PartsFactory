"""
AtlasProvider — the `atlas` port provider.

Stateful: maintains a registry of currently-deployed Morphons + their
Julia c-values. Supports admission (c must be in the Mandelbrot
boundary AND headroom must exist), eviction, deployment stats, and
periodic boundary recomputation (when wired to a daemon channel).

Parent frame Slots 26 (atlas-mandelbrot) + 27 (julia-c-assignment).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

from cmplx.morphon import Morphon

from .julia import derive_c
from .mandelbrot import is_in_mandelbrot


# Leech lattice kissing number — the natural deployment capacity per the
# formalization (CMPLX2 §11.1.2 "Voronoi cell organization"). Each Morphon
# in the deployment occupies one position in the 196,560-vertex shell.
_LEECH_KISSING_NUMBER = 196_560


class AtlasProvider:
    """The `atlas` port — Mandelbrot deployment boundary + Julia c-assignment.

    Conforms to ``cmplx.morphon.AtlasProvider`` Protocol. Registration:

        MorphonController.get().register("atlas", AtlasProvider())

    Once registered, ``admit_and_store`` automatically calls
    ``admit_to_deployment`` after constraints admission. Morphons whose
    c-value is outside the Mandelbrot boundary, or whose admission would
    exceed the deployment capacity, are rejected with ``PermissionError``.

    State is in-memory (a dict of morphon_id → complex). Persistence
    across process restarts requires snapshotting + restoration; that's
    a Wave-2 concern.
    """

    name: str = "atlas_provider"

    def __init__(
        self,
        *,
        max_iter: int = 100,
        capacity: int = _LEECH_KISSING_NUMBER,
    ) -> None:
        """
        Args:
            max_iter: Mandelbrot escape-time iteration cap. Higher = more
                accurate boundary but slower admission. Default 100.
            capacity: maximum deployed morphons. Default is the Leech
                kissing number (196,560).
        """
        self._max_iter = max_iter
        self._capacity = capacity
        self._deployed: dict[str, complex] = {}

    # ── Core Protocol methods ─────────────────────────────────────

    def julia_c(self, morphon: Morphon) -> complex:
        """Return this morphon's Julia c-value.

        If the morphon already has a ``fractal_coordinate`` set (e.g., the
        CQE atom flow populated it), that takes precedence — the existing
        value is the morphon's identity geometry. Otherwise compute c
        deterministically from identity components and cache it on the
        morphon's ``fractal_coordinate`` field.
        """
        existing = getattr(morphon, "fractal_coordinate", None)
        if existing is not None:
            return existing
        c = derive_c(morphon)
        # Cache on the morphon. Note: Morphon is typed as a dataclass with
        # CQE fields; this assignment matches the existing CQEAtom pattern.
        try:
            morphon.fractal_coordinate = c
        except AttributeError:
            # If the morphon class doesn't support attribute assignment
            # (frozen variants), silently skip — c is still returned.
            pass
        return c

    def in_boundary(self, c: complex, *, max_iter: Optional[int] = None) -> bool:
        """True iff c is in the Mandelbrot set (within iteration budget)."""
        return is_in_mandelbrot(c, max_iter if max_iter is not None else self._max_iter)

    def admit_to_deployment(self, morphon: Morphon) -> tuple[bool, str]:
        """Boundary-aware admission check.

        Returns ``(True, "")`` on success; ``(False, reason)`` on rejection.
        Two rejection paths:

          1. c is outside the Mandelbrot boundary → ``"c=<value> is outside..."``
          2. deployment at capacity → ``"deployment at capacity (...)"``

        On admission, the morphon is added to the deployed set. Idempotent:
        re-admitting an already-deployed morphon (same id) returns
        ``(True, "already-deployed")`` without growing the deployed set.
        """
        c = self.julia_c(morphon)

        if morphon.id in self._deployed:
            return True, "already-deployed"

        if not self.in_boundary(c):
            return (
                False,
                f"c={c.real:.4f}{c.imag:+.4f}j is outside the Mandelbrot boundary",
            )

        if len(self._deployed) >= self._capacity:
            return (
                False,
                f"deployment at capacity ({self._capacity})",
            )

        self._deployed[morphon.id] = c
        return True, ""

    def evict(self, morphon_id: str) -> bool:
        """Remove a morphon from the deployed set. Returns True if it was present."""
        return self._deployed.pop(morphon_id, None) is not None

    def deployment_stats(self) -> dict:
        """Snapshot of current deployment state."""
        return {
            "deployed_count": len(self._deployed),
            "capacity": self._capacity,
            "headroom": self._capacity - len(self._deployed),
            "max_iter": self._max_iter,
        }

    def boundary_recompute(self) -> dict:
        """Periodic re-check of all deployed morphons' c-values.

        Designed for class-C (daemon-periodic) triggering. Iterates the
        deployed set, evicts any morphons whose c is no longer in the
        Mandelbrot boundary (could happen if ``max_iter`` was lowered or
        if a morphon's c was externally mutated). Returns stats.

        Per ``docs/sub_frames/port_trigger_map.md`` §3, this binds to the
        ``brain_sync`` daemon channel by convention (period 7 ticks).
        """
        evicted_ids: list[str] = []
        for morphon_id, c in list(self._deployed.items()):
            if not self.in_boundary(c):
                self._deployed.pop(morphon_id, None)
                evicted_ids.append(morphon_id)
        return {
            "evicted_count": len(evicted_ids),
            "evicted_ids": evicted_ids,
            "deployed_count": len(self._deployed),
            "tick_source": "atlas.boundary_recompute",
        }

    # ── ETP integration ─────────────────────────────────────────

    def encode_to_etp(self, morphon: Morphon) -> str:
        """Encode morphon as ETP program. Delegates to symbolic when registered."""
        symbolic = self._maybe_get_symbolic()
        if symbolic is not None:
            return symbolic.encode_to_etp(morphon)
        return self._fallback_encode_to_etp(morphon)

    def decode_from_etp(self, ledger: list[dict]) -> Morphon:
        """Reconstruct a morphon from an ETP ledger."""
        symbolic = self._maybe_get_symbolic()
        if symbolic is not None:
            return symbolic.decode_from_etp(ledger)
        return self._fallback_decode_from_etp(ledger)

    # ── Convenience surface ────────────────────────────────────

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": self.name,
            "deployment": self.deployment_stats(),
        }

    def __repr__(self) -> str:
        return (
            f"<AtlasProvider deployed={len(self._deployed)}/{self._capacity} "
            f"max_iter={self._max_iter}>"
        )

    # ── Internals ──────────────────────────────────────────────

    def _maybe_get_symbolic(self) -> Any:
        try:
            from cmplx.morphon import MorphonController
            return MorphonController.get().get_provider("symbolic")
        except (LookupError, ImportError):
            return None

    def _fallback_encode_to_etp(self, morphon: Morphon) -> str:
        alphabet = "}<>+01"
        serialized = json.dumps(
            {"id": morphon.id, "payload": morphon.payload, "parent": morphon.parent},
            sort_keys=True,
            default=str,
        ).encode("utf-8")
        digest = hashlib.sha256(serialized).digest()
        return "".join(alphabet[b % len(alphabet)] for b in digest)

    def _fallback_decode_from_etp(self, ledger: list[dict]) -> Morphon:
        if not ledger:
            return Morphon.forge(payload={"etp_decode": "empty_ledger"})
        final = ledger[-1]
        return Morphon.forge(payload={
            "etp_decode": True,
            "torus8": list(final.get("torus8", [])),
            "wall10": final.get("wall10", "0.000"),
            "digital_root": final.get("digital_root", 0),
            "halted": final.get("halted_now", False),
            "n_grains": final.get("n_grains", 0),
            "steps": final.get("step", 0),
        })
