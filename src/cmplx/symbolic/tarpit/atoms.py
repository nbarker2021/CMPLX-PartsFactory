"""
unified_tarpit atom layer — DerivationKey, InvariantSignature, Atom.

Promoted from CMPLXUNI ``e6_atom_layer`` (corpus ``unified_tarpit.py``).
Compresses full ETP ledger runs into ~200-byte atoms with lossless re-derive.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ._functions import RelativityEnvelope, run_etp_with_ledger

BOND_THRESHOLD_RESONANCE = 0.85
BOND_THRESHOLD_DUST = 0.55
BOND_THRESHOLD_BRIDGE = 0.35


@dataclass
class DerivationKey:
    """Genome — minimum information to regenerate a full execution trace."""

    program: str
    dimension: int = 8
    max_steps: int = 10_000
    gauge_seed: Optional[int] = None
    mirror_policy: str = "pole"
    force_mirror_on_error: bool = False
    envelope_max_delta: Optional[float] = None
    level: int = 0

    def deterministic_hash(self) -> str:
        raw = json.dumps(
            {
                "program": self.program,
                "dimension": self.dimension,
                "max_steps": self.max_steps,
                "gauge_seed": self.gauge_seed,
                "mirror_policy": self.mirror_policy,
                "force_mirror_on_error": self.force_mirror_on_error,
                "envelope_max_delta": self.envelope_max_delta,
                "level": self.level,
            },
            sort_keys=True,
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class InvariantSignature:
    """Measured invariants — what other atoms observe at interaction time."""

    wall_serial: str = "0.00000000"
    wall_score: float = 0.0
    torus_final: List[int] = field(default_factory=lambda: [0] * 8)
    torus_mirror_final: List[int] = field(default_factory=lambda: [0] * 8)
    digital_root: int = 0
    effective_dim: int = 0
    halted: bool = False
    error_count: int = 0
    bonds_formed: int = 0
    lattice: str = "Isolated"
    entropy_final: float = 0.0
    gram_spectrum: List[float] = field(default_factory=list)

    @property
    def closure_count(self) -> int:
        try:
            return int(self.wall_serial.split(".")[0])
        except (ValueError, IndexError):
            return 0

    @property
    def residual_digits(self) -> List[int]:
        try:
            tail = self.wall_serial.split(".")[1]
            return [int(c) for c in tail if c.isdigit()]
        except (ValueError, IndexError):
            return []

    @property
    def residual_mass(self) -> float:
        digits = self.residual_digits
        return sum(d * (10 ** -(i + 1)) for i, d in enumerate(digits))

    @property
    def is_closed(self) -> bool:
        return self.halted and self.error_count == 0 and self.closure_count > 0

    @property
    def mass(self) -> float:
        if not self.halted:
            return 0.0
        if self.closure_count == 0:
            return 0.1
        return min(1.0, (1.0 - self.residual_mass) * min(1.0, self.closure_count / 3.0))


@dataclass
class Atom:
    """Wrapped execution — derivation key + invariant signature."""

    derivation_key: DerivationKey
    signature: InvariantSignature
    atom_id: str = ""
    level: int = 0
    _lineage: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.atom_id:
            self.atom_id = self._compute_id()

    def _compute_id(self) -> str:
        raw = self.derivation_key.deterministic_hash() + "|" + self.signature.wall_serial
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    @classmethod
    def from_program(
        cls,
        program: str,
        *,
        dimension: int = 8,
        max_steps: int = 200,
        mirror_policy: str = "pole",
        force_mirror_on_error: bool = False,
        envelope_max_delta: Optional[float] = None,
    ) -> "Atom":
        env = None
        if envelope_max_delta is not None:
            env = RelativityEnvelope(
                enabled=True, max_delta_component=envelope_max_delta
            )
        out = run_etp_with_ledger(
            program,
            dimension=dimension,
            max_steps=max_steps,
            mirror_policy=mirror_policy,
            force_mirror_on_error=force_mirror_on_error,
            envelope=env,
        )
        key = DerivationKey(
            program=program,
            dimension=dimension,
            max_steps=max_steps,
            mirror_policy=mirror_policy,
            force_mirror_on_error=force_mirror_on_error,
            envelope_max_delta=envelope_max_delta,
            level=0,
        )
        return wrap_run(out, key)

    def re_derive(self) -> Dict[str, Any]:
        env = None
        if self.derivation_key.envelope_max_delta is not None:
            env = RelativityEnvelope(
                enabled=True,
                max_delta_component=self.derivation_key.envelope_max_delta,
            )
        return run_etp_with_ledger(
            self.derivation_key.program,
            dimension=self.derivation_key.dimension,
            max_steps=self.derivation_key.max_steps,
            mirror_policy=self.derivation_key.mirror_policy,
            force_mirror_on_error=self.derivation_key.force_mirror_on_error,
            envelope=env,
        )

    def torus_distance(self, other: "Atom") -> float:
        t1 = self.signature.torus_final
        t2 = other.signature.torus_final
        if len(t1) != len(t2):
            return float("inf")
        total = 0.0
        for a, b in zip(t1, t2):
            diff = abs(a - b)
            diff = min(diff, 8 - diff)
            total += diff ** 2
        return math.sqrt(total)

    def wall_compatibility(self, other: "Atom") -> float:
        if self.atom_id == other.atom_id:
            return 1.0
        score = 0.0
        max_score = 0.0

        max_score += 1.0
        dr_diff = abs(self.signature.digital_root - other.signature.digital_root)
        if dr_diff == 0:
            score += 1.0
        elif dr_diff <= 2 or dr_diff >= 7:
            score += 0.5

        max_score += 1.0

        def _residual_torus_match(res: List[int], torus: List[int]) -> float:
            if not res or not torus:
                return 0.0
            n = min(len(res), len(torus))
            return sum(1 for i in range(n) if res[i] % 8 == torus[i]) / n

        fwd = _residual_torus_match(
            self.signature.residual_digits, other.signature.torus_final
        )
        bwd = _residual_torus_match(
            other.signature.residual_digits, self.signature.torus_final
        )
        score += (fwd + bwd) / 2.0

        max_score += 1.0
        if self.signature.lattice == other.signature.lattice:
            score += 1.0
        elif "Grid" in self.signature.lattice and "Grid" in other.signature.lattice:
            score += 0.5
        elif "Chain" in self.signature.lattice or "Chain" in other.signature.lattice:
            score += 0.3

        max_score += 1.0
        if self.signature.is_closed and other.signature.is_closed:
            score += 1.0
        elif self.signature.halted and other.signature.halted:
            score += 0.5

        max_score += 1.0
        dim_diff = abs(self.signature.effective_dim - other.signature.effective_dim)
        if dim_diff == 0:
            score += 1.0
        elif dim_diff == 1:
            score += 0.5

        return score / max_score if max_score > 0 else 0.0

    def compact_repr(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "level": self.level,
            "wall_serial": self.signature.wall_serial,
            "mass": round(self.signature.mass, 4),
            "torus": self.signature.torus_final,
            "dr": self.signature.digital_root,
            "dim": self.signature.effective_dim,
            "lattice": self.signature.lattice,
            "closed": self.signature.is_closed,
            "program_len": len(self.derivation_key.program),
            "lineage": list(self._lineage),
        }


class BondType(Enum):
    RESONANCE = "resonance"
    DUST = "dust"
    BRIDGE = "bridge"
    FAILED = "failed"


@dataclass
class AtomBondResult:
    bonded: bool
    bond_type: BondType
    compatibility: float
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bonded": self.bonded,
            "bond_type": self.bond_type.value,
            "compatibility": round(self.compatibility, 4),
            "reason": self.reason,
        }


def bond_atoms(
    a: Atom,
    b: Atom,
    threshold: float = BOND_THRESHOLD_DUST,
) -> AtomBondResult:
    compat = a.wall_compatibility(b)
    if compat >= BOND_THRESHOLD_RESONANCE:
        bond_type = BondType.RESONANCE
    elif compat >= BOND_THRESHOLD_DUST:
        bond_type = BondType.DUST
    elif compat >= BOND_THRESHOLD_BRIDGE:
        bond_type = BondType.BRIDGE
    else:
        bond_type = BondType.FAILED

    if compat < threshold:
        return AtomBondResult(
            bonded=False,
            bond_type=BondType.FAILED,
            compatibility=compat,
            reason=f"compatibility {compat:.3f} < threshold {threshold:.3f}",
        )
    return AtomBondResult(
        bonded=True,
        bond_type=bond_type,
        compatibility=compat,
    )


@dataclass
class AtomField:
    """Workspace for multi-atom chemistry (probe + pairwise bond screening)."""

    atoms: Dict[str, Atom] = field(default_factory=dict)
    bond_threshold: float = BOND_THRESHOLD_DUST

    def add_atom(self, atom: Atom) -> None:
        self.atoms[atom.atom_id] = atom

    def add_program(self, program: str, **kwargs: Any) -> Atom:
        atom = Atom.from_program(program, **kwargs)
        self.add_atom(atom)
        return atom

    def screen_bonds(self) -> List[Dict[str, Any]]:
        """Pairwise bond screen over all atoms in the field."""
        ids = list(self.atoms.keys())
        results: List[Dict[str, Any]] = []
        for i, aid in enumerate(ids):
            for bid in ids[i + 1 :]:
                a, b = self.atoms[aid], self.atoms[bid]
                br = bond_atoms(a, b, threshold=self.bond_threshold)
                results.append(
                    {
                        "a": aid,
                        "b": bid,
                        **br.to_dict(),
                    }
                )
        return results


def wrap_run(run_output: Dict[str, Any], key: DerivationKey) -> Atom:
    """Crystallize ``run_etp_with_ledger`` output into an Atom."""
    summary = run_output.get("summary", {})
    ledger = run_output.get("ledger", [])
    final_row = ledger[-1] if ledger else {}

    sig = InvariantSignature(
        wall_serial=str(summary.get("wall_serial", "0.00000000")),
        wall_score=float(summary.get("wall_score", 0.0)),
        torus_final=list(final_row.get("torus8", [0] * 8)),
        torus_mirror_final=list(final_row.get("torus8_mirror", [0] * 8)),
        digital_root=int(summary.get("final_digital_root", 0)),
        effective_dim=int(final_row.get("effective_dim", 0)),
        halted=bool(summary.get("halted_now", summary.get("halted", False))),
        error_count=int(summary.get("n_error_walls", 0)),
        bonds_formed=int(summary.get("bonds_formed", 0)),
        lattice=str(summary.get("lattice", "Isolated")),
        entropy_final=float(final_row.get("entropy", 0.0)),
        gram_spectrum=list(final_row.get("gram5", [])),
    )
    return Atom(derivation_key=key, signature=sig, level=key.level)
