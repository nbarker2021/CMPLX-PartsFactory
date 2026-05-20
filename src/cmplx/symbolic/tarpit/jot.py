"""
Jot binary combinator encoding.

Jot (Chris Barker, 2001) is a binary lambda-calculus:
  - bit `0` applies (S K) — in TarPit semantics: bond with neighbor
  - bit `1` nests   — in TarPit semantics: extend extent vector

Adapted from `evolving_tarpit/jot_grain_encoding.py`.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from . import _math as _m
from .bond import BondEngine
from .grain import DimensionalExtent, Grain, GrainField, GrainType


class SKCombinator(Enum):
    """The three primitive combinators."""
    S = "S"      # (Sx)yz = (xz)(yz)
    K = "K"      # Kxy = x
    I = "I"      # Ix = x


@dataclass
class CombinatorGrain:
    """A grain tagged with a combinator role."""
    grain: Grain
    combinator: SKCombinator = SKCombinator.I
    arity_remaining: int = 0


class JotGrainEncoder:
    """Translate a Jot bitstring into grain operations on a field.

    `_execute_apply` (bit `0`): bond current grain with its neighbor.
    `_execute_nest` (bit `1`): extend the extent vector at the current
    grain (a lambda nesting). Both return the (possibly modified)
    field.
    """

    def __init__(self, bond_engine: Optional[BondEngine] = None) -> None:
        self.bond_engine = bond_engine or BondEngine()
        self.combinator_history: list[SKCombinator] = []

    def interpret_bits(self, bits: str, field: GrainField,
                       step_base: int = 0) -> GrainField:
        """Execute each bit in `bits` against `field`."""
        for i, bit in enumerate(bits):
            if bit == "0":
                field = self._execute_apply(field, step_base + i)
            elif bit == "1":
                field = self._execute_nest(field, step_base + i)
            else:
                continue
        return field

    def _execute_apply(self, field: GrainField, step: int) -> GrainField:
        """Jot `0`: apply (S K) — bond the current grain with its right
        neighbor, producing a Dust (and possibly a Triad)."""
        cur = field.get_current_grain()
        right = field.get_primary_grain(field.pointer + 1)
        if cur is None:
            cur = field.create_grain(field.pointer, 0)
        if right is None:
            right = field.create_grain(field.pointer + 1, 0)
        dust = self.bond_engine.attempt_bond(cur, right)
        if dust is not None:
            field.composites.append(dust)
            triad = self.bond_engine.promote_to_triad(dust)
            if triad is not None:
                field.composites.append(triad)
        self.combinator_history.append(SKCombinator.S)
        return field

    def _execute_nest(self, field: GrainField, step: int) -> GrainField:
        """Jot `1`: nest lambda — extend the extent vector at the
        current grain. We add a small unit-vector perturbation, then
        re-emit the grain at the same position (history-preserving)."""
        cur = field.get_current_grain()
        if cur is None:
            cur = field.create_grain(field.pointer, 0)
        direction = _m.random_unit_vec(field.dimension, field._rng)
        extended = _m.add(cur.extent.vector, _m.scale(direction, 0.1))
        new_extent = cur.extent.with_vector(extended)
        nested = Grain(
            grain_type=GrainType.COMBINATOR,
            value=cur.value,
            extent=new_extent,
            position=cur.position,
            parent_ids=[cur.id],
            certificates={**cur.certificates, "nested_from": cur.id},
            tags=list(cur.tags) + ["nested"],
        )
        field.set_grain(cur.position, nested)
        self.combinator_history.append(SKCombinator.K)
        return field
