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


_ETP_BRIDGE_OPS = "}<>+01"


class BondType(Enum):
    RESONANCE = "resonance"
    DUST = "dust"
    BRIDGE = "bridge"
    FAILED = "failed"


@dataclass
class Mediator:
    """Bonding mediator between two atoms (torus midpoint interpolation)."""

    wall_serial: str
    torus_digits: List[int]
    digital_root: int
    source: str = "interpolation"

    @classmethod
    def from_atoms(cls, a: Atom, b: Atom) -> "Mediator":
        t1 = a.signature.torus_final
        t2 = b.signature.torus_final
        n = min(len(t1), len(t2))
        mid_torus: List[int] = []
        for i in range(n):
            diff = (t2[i] - t1[i]) % 8
            if diff > 4:
                mid = (t1[i] - (8 - diff) // 2) % 8
            else:
                mid = (t1[i] + diff // 2) % 8
            mid_torus.append(mid)

        dr = (a.signature.digital_root + b.signature.digital_root) % 9
        if dr == 0 and (a.signature.digital_root + b.signature.digital_root) > 0:
            dr = 9

        a_res = a.signature.residual_digits
        b_res = b.signature.residual_digits
        n_res = max(len(a_res), len(b_res))
        med_digits: List[int] = []
        for i in range(min(n_res, 8)):
            d1 = a_res[i] if i < len(a_res) else 0
            d2 = b_res[i] if i < len(b_res) else 0
            med_digits.append((d1 + d2) // 2)
        while len(med_digits) < 8:
            med_digits.append(0)

        closures = (a.signature.closure_count + b.signature.closure_count) // 2
        serial = f"{closures}.{''.join(str(d) for d in med_digits)}"

        return cls(
            wall_serial=serial,
            torus_digits=mid_torus,
            digital_root=dr,
            source="interpolation",
        )


@dataclass
class Composite:
    """Bonded atom pair + mediator — promotable to next-level Atom."""

    pole_a: Atom
    pole_b: Atom
    mediator: Mediator
    bond_type: BondType
    compatibility: float
    composite_id: str = ""

    def __post_init__(self) -> None:
        if not self.composite_id:
            raw = self.pole_a.atom_id + "|" + self.pole_b.atom_id
            self.composite_id = hashlib.sha256(raw.encode()).hexdigest()[:12]

    def _bridge_token(self) -> str:
        t = self.mediator.torus_digits
        tokens = []
        for i in range(min(2, len(t))):
            tokens.append(_ETP_BRIDGE_OPS[t[i] % len(_ETP_BRIDGE_OPS)])
        return "".join(tokens) if tokens else ">"

    def promote(self) -> Atom:
        composite_program = (
            self.pole_a.derivation_key.program
            + self._bridge_token()
            + self.pole_b.derivation_key.program
        )
        new_level = max(self.pole_a.level, self.pole_b.level) + 1
        a_env = self.pole_a.derivation_key.envelope_max_delta
        b_env = self.pole_b.derivation_key.envelope_max_delta
        env_delta: Optional[float] = None
        if a_env is not None and b_env is not None:
            env_delta = min(a_env, b_env)
        elif a_env is not None:
            env_delta = a_env
        elif b_env is not None:
            env_delta = b_env

        atom = Atom.from_program(
            composite_program,
            dimension=self.pole_a.derivation_key.dimension,
            max_steps=self.pole_a.derivation_key.max_steps,
            mirror_policy=self.pole_a.derivation_key.mirror_policy,
            envelope_max_delta=env_delta,
        )
        atom.level = new_level
        atom.derivation_key.level = new_level
        atom._lineage = [self.pole_a.atom_id, self.pole_b.atom_id]
        return atom

    def to_dict(self) -> Dict[str, Any]:
        return {
            "composite_id": self.composite_id,
            "bond_type": self.bond_type.value,
            "compatibility": round(self.compatibility, 4),
            "poles": [self.pole_a.atom_id, self.pole_b.atom_id],
            "mediator_dr": self.mediator.digital_root,
        }


@dataclass
class BondResult:
    """Outcome of an atom bond attempt."""

    bonded: bool
    bond_type: BondType
    compatibility: float = 0.0
    composite: Optional[Composite] = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "bonded": self.bonded,
            "bond_type": self.bond_type.value,
            "compatibility": round(self.compatibility, 4),
            "reason": self.reason,
        }
        if self.composite is not None:
            out["composite"] = self.composite.to_dict()
        return out


def bond_atoms(
    a: Atom,
    b: Atom,
    threshold: float = BOND_THRESHOLD_DUST,
) -> BondResult:
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
        return BondResult(
            bonded=False,
            bond_type=BondType.FAILED,
            compatibility=compat,
            reason=f"compatibility {compat:.3f} < threshold {threshold:.3f}",
        )

    mediator = Mediator.from_atoms(a, b)
    composite = Composite(
        pole_a=a,
        pole_b=b,
        mediator=mediator,
        bond_type=bond_type,
        compatibility=compat,
    )
    return BondResult(
        bonded=True,
        bond_type=bond_type,
        compatibility=compat,
        composite=composite,
    )


@dataclass
class AtomField:
    """Multi-atom chemistry — bond, composite, promote."""

    atoms: Dict[str, Atom] = field(default_factory=dict)
    composites: List[Composite] = field(default_factory=list)
    promoted: Dict[str, Atom] = field(default_factory=dict)
    failed_bonds: List[BondResult] = field(default_factory=list)
    bond_threshold: float = BOND_THRESHOLD_DUST
    max_level: int = 3

    def add_atom(self, atom: Atom) -> None:
        self.atoms[atom.atom_id] = atom

    def add_program(self, program: str, **kwargs: Any) -> Atom:
        atom = Atom.from_program(program, **kwargs)
        self.add_atom(atom)
        return atom

    def add_programs(self, programs: List[str], **kwargs: Any) -> List[Atom]:
        return [self.add_program(p, **kwargs) for p in programs]

    def screen_bonds(self) -> List[Dict[str, Any]]:
        ids = list(self.atoms.keys())
        results: List[Dict[str, Any]] = []
        for i, aid in enumerate(ids):
            for bid in ids[i + 1 :]:
                a, b = self.atoms[aid], self.atoms[bid]
                br = bond_atoms(a, b, threshold=self.bond_threshold)
                results.append({"a": aid, "b": bid, **br.to_dict()})
        return results

    def run_chemistry(self, promote: bool = True) -> Dict[str, Any]:
        atom_list = list(self.atoms.values())
        n = len(atom_list)
        bonds_attempted = 0
        bonds_succeeded = 0

        for i in range(n):
            for j in range(i + 1, n):
                a, b = atom_list[i], atom_list[j]
                bonds_attempted += 1
                result = bond_atoms(a, b, threshold=self.bond_threshold)
                if result.bonded and result.composite is not None:
                    bonds_succeeded += 1
                    self.composites.append(result.composite)
                    if promote:
                        promoted_atom = result.composite.promote()
                        self.promoted[promoted_atom.atom_id] = promoted_atom
                else:
                    self.failed_bonds.append(result)

        return {
            "n_atoms": n,
            "bonds_attempted": bonds_attempted,
            "bonds_succeeded": bonds_succeeded,
            "bonds_failed": bonds_attempted - bonds_succeeded,
            "composites": len(self.composites),
            "promoted_atoms": len(self.promoted),
        }

    def run_multilevel(self, max_level: int = 2) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        r0 = self.run_chemistry(promote=True)
        r0["level"] = 0
        results.append(r0)

        for level in range(1, min(max_level, self.max_level) + 1):
            if not self.promoted:
                break
            level_field = AtomField(
                bond_threshold=self.bond_threshold, max_level=self.max_level
            )
            for atom in self.promoted.values():
                level_field.add_atom(atom)
            rN = level_field.run_chemistry(promote=(level < max_level))
            rN["level"] = level
            results.append(rN)
            self.promoted = level_field.promoted
            self.composites.extend(level_field.composites)

        return {
            "levels": results,
            "total_composites": len(self.composites),
            "final_promoted": len(self.promoted),
        }

    def compatibility_matrix(self) -> Dict[str, Any]:
        atom_list = list(self.atoms.values())
        n = len(atom_list)
        ids = [a.atom_id for a in atom_list]
        matrix: List[List[float]] = []
        off_diag: List[float] = []
        for i in range(n):
            row: List[float] = []
            for j in range(n):
                if i == j:
                    row.append(1.0)
                else:
                    v = atom_list[i].wall_compatibility(atom_list[j])
                    row.append(v)
                    if j > i:
                        off_diag.append(v)
            matrix.append(row)
        return {
            "ids": ids,
            "matrix": matrix,
            "mean_compatibility": sum(off_diag) / len(off_diag) if off_diag else 0.0,
            "max_off_diagonal": max(off_diag) if off_diag else 0.0,
            "min_off_diagonal": min(off_diag) if off_diag else 0.0,
        }

    def summary(self) -> Dict[str, Any]:
        all_atoms = list(self.atoms.values()) + list(self.promoted.values())
        masses = [a.signature.mass for a in all_atoms]
        lattices = [a.signature.lattice for a in all_atoms]
        bond_types = [c.bond_type.value for c in self.composites]
        return {
            "base_atoms": len(self.atoms),
            "promoted_atoms": len(self.promoted),
            "composites": len(self.composites),
            "failed_bonds": len(self.failed_bonds),
            "mass_distribution": {
                "mean": sum(masses) / len(masses) if masses else 0.0,
                "max": max(masses) if masses else 0.0,
                "closed": sum(1 for a in all_atoms if a.signature.is_closed),
            },
            "lattice_distribution": _count_values(lattices),
            "bond_types": _count_values(bond_types),
        }


def _count_values(items: List[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


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
