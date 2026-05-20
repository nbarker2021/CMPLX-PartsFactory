"""
Gate369Engine — the 3→6→9 selection protocol.

Adapted from `cmplx_pending/snap/Gate369Engine.py` (1 variant, 5
methods). Defines the supporting types inline (`Body`, `Predicate`,
`SNAPRecord`, `HexadInvariant`, `EnneadPackage`) since the canonical
forms scatter them across the snap folder.

The protocol:
  - **Gate 3 (triad)**: pick the 3 best `Body` objects by lens-scored
    reward.
  - **Gate 6 (hexad)**: across pairs of triads, find polarity
    invariants (sign-flipped members with comparable margin).
  - **Gate 9 (ennead)**: collapse to a 9-body containment package;
    compute `polarity_conflict` from variance of deltas; pass/fail
    via the selected lens.

`process()` runs the full sequence and returns a structured trace.
A high `containment_c` (> 0.7) signals the package "crystallized" —
this is the boundary at which the user's giraffe pipeline would mint
a `Crystal` with the ennead facets as nodes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .lenses import BaseLens, LensBank


# ---------------------------------------------------------------------------
# Supporting types
# ---------------------------------------------------------------------------

@dataclass
class Body:
    """A candidate the gates select among.

    Bodies are opaque to the engine — they're identified by `id` and
    carry arbitrary `payload`. Equality is by id.
    """
    id: str
    payload: Any = None

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Body) and self.id == other.id


@dataclass
class Predicate:
    """A scored claim about a body or set of bodies."""
    name: str
    meta: dict = field(default_factory=dict)  # carries expected_du
    cost: float = 1.0


@dataclass
class HexadInvariant:
    """A polarity invariant: a positive body paired with a negative one,
    with a numeric margin and a textual invariant string."""
    pos: Body
    neg: Body
    invariant: str = ""
    margin: float = 0.0


@dataclass
class SNAPRecord:
    """The result of one gate. Records carry their members + predicates
    + accumulated delta_u + polarity_conflict score."""
    kind: str = "triad"
    members: list[Body] = field(default_factory=list)
    predicates: list[Predicate] = field(default_factory=list)
    delta_u: float = 0.0
    polarity_conflict: float = 0.0


@dataclass
class EnneadPackage:
    """The crystallization-candidate output of Gate 9."""
    facets: list[Body] = field(default_factory=list)
    lens_name: str = "base"
    mirror_pass: bool = False
    containment_c: float = 0.0
    delta_u: float = 0.0
    reversibility: bool = False


# ---------------------------------------------------------------------------
# Gate369Engine
# ---------------------------------------------------------------------------

class Gate369Engine:
    """3-6-9 selection and evaluation."""

    name: str = "gate369"

    def __init__(self, lens_bank: Optional[LensBank] = None) -> None:
        self.lens_bank = lens_bank or LensBank()
        self._history: list[dict] = []

    # ── Gate 3 ────────────────────────────────────────────────────────

    def triad(
        self,
        bodies: list[Body],
        predicates: list[Predicate],
        state: Optional[dict] = None,
    ) -> SNAPRecord:
        state = state or {}
        lens = self.lens_bank.best_lens(state)
        du_sum = sum(p.meta.get("expected_du", 0.0) for p in predicates)
        scored = [(b, lens.score_reward({}, {"delta_u": du_sum})) for b in bodies]
        top3 = [b for b, _ in sorted(scored, key=lambda x: -x[1])[:3]]
        return SNAPRecord(
            kind="triad",
            members=top3,
            predicates=list(predicates),
            delta_u=sum(s for _, s in scored[:3]),
        )

    # ── Gate 6 ────────────────────────────────────────────────────────

    def hexad(self, records: list[SNAPRecord]) -> list[HexadInvariant]:
        invariants: list[HexadInvariant] = []
        for i in range(0, len(records) - 1, 2):
            a, b = records[i], records[i + 1]
            if a.members and b.members:
                invariants.append(HexadInvariant(
                    pos=a.members[0],
                    neg=b.members[0],
                    invariant=f"{a.kind}↔{b.kind}",
                    margin=abs(a.delta_u - b.delta_u),
                ))
        return invariants

    # ── Gate 9 ────────────────────────────────────────────────────────

    def ennead(
        self,
        records: list[SNAPRecord],
        lens_name: str = "base",
    ) -> EnneadPackage:
        all_bodies: list[Body] = []
        for r in records:
            for b in r.members:
                if b not in all_bodies:
                    all_bodies.append(b)
                if len(all_bodies) >= 9:
                    break
            if len(all_bodies) >= 9:
                break

        lens: BaseLens = self.lens_bank.get(lens_name) or self.lens_bank.get("base")
        delta_us = [r.delta_u for r in records] if records else [0.0]
        mean_du = sum(delta_us) / len(delta_us)
        variance = sum((d - mean_du) ** 2 for d in delta_us) / max(len(delta_us), 1)
        polarity_conflict = min(variance / max(abs(mean_du) + 1e-9, 1.0), 1.0)
        conflict_free = sum(1 for r in records if r.polarity_conflict == 0)
        containment_c = conflict_free / max(len(records), 1)

        state = {
            "mirror_pass": polarity_conflict <= 0.3,
            "polarity_conflict": polarity_conflict,
            "containment_c": containment_c,
        }
        verdict = lens.evaluate(state)
        return EnneadPackage(
            facets=all_bodies,
            lens_name=lens_name,
            mirror_pass=state["mirror_pass"],
            containment_c=containment_c,
            delta_u=sum(delta_us),
            reversibility=(verdict == "pass"),
        )

    # ── Full 3→6→9 ────────────────────────────────────────────────────

    def process(
        self,
        bodies: list[Body],
        predicates: list[Predicate],
        state: Optional[dict] = None,
    ) -> dict:
        state = state or {}
        triad = self.triad(bodies, predicates, state)
        self._history.append({"gate": 3, "members": len(triad.members)})

        remaining = [b for b in bodies if b not in triad.members]
        triads = [triad]
        if remaining:
            triads.append(self.triad(remaining, predicates, state))

        invariants = self.hexad(triads)
        self._history.append({"gate": 6, "invariants": len(invariants)})

        ennead = self.ennead(triads)
        crystallized = ennead.containment_c > 0.7
        self._history.append({
            "gate": 9,
            "facets": len(ennead.facets),
            "crystallized": crystallized,
        })

        return {
            "triad": {
                "members": [b.id for b in triad.members],
                "delta_u": triad.delta_u,
            },
            "hexad": [
                {"pos": i.pos.id, "neg": i.neg.id, "margin": i.margin}
                for i in invariants
            ],
            "ennead": {
                "facets": [b.id for b in ennead.facets],
                "containment_c": ennead.containment_c,
                "reversible": ennead.reversibility,
                "crystallized": crystallized,
                "lens": ennead.lens_name,
            },
        }

    @property
    def history(self) -> list[dict]:
        return list(self._history)
