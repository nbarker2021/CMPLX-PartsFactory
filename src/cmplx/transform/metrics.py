"""
Token metrics and morphability signatures.

Scalars for arity, token_mass, dual mass witnesses, and surface
morphism comparison (CaseMode + SurfaceMode).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from cmplx.primitives.core import COUPLING, NLAECNFChain

from .token_index.case import CaseMode, apply_case
from .token_index.bonds import QuadBond
from .token_index.warmstart import WarmStartLookup, WarmStartOutcome, geometry_snap_key


def surface_snap_key(concat: str) -> str:
    """SNAP key on surface concat (case-sensitive)."""
    return str(NLAECNFChain.full_chain(concat)["snap_key"])


def _kissing_proxy(digital_root: int, token_mass: int) -> int:
    """E8 kissing-neighbor count proxy from DR channel + token_mass."""
    base = {3: 72, 6: 96, 9: 72}.get(digital_root, 48)
    return min(240, base + token_mass * 2)


@dataclass(frozen=True)
class TokenMetrics:
    arity: int
    token_mass: int
    mass_e8: int
    mass_tarpit: float
    digital_root: int = 0
    lane: str = ""
    snap_key: str = ""

    def as_dict(self) -> dict:
        return {
            "arity": self.arity,
            "token_mass": self.token_mass,
            "mass_e8": self.mass_e8,
            "mass_tarpit": self.mass_tarpit,
            "digital_root": self.digital_root,
            "lane": self.lane,
            "snap_key": self.snap_key,
        }


@dataclass
class MorphSignature:
    base_concat: str
    variant_concat: str
    delta_snap: int
    delta_lane: bool
    delta_dr: int
    delta_token_mass: int
    delta_mass_e8: int
    delta_mass_tarpit: float
    warmstart_outcome: WarmStartOutcome
    seam_role: Optional[str] = None
    geometry_invariant: bool = False
    extra: dict = field(default_factory=dict)

    @property
    def verdict(self) -> str:
        return morph_verdict(self)

    def as_dict(self) -> dict:
        return {
            "base_concat": self.base_concat,
            "variant_concat": self.variant_concat,
            "delta_snap": self.delta_snap,
            "delta_lane": self.delta_lane,
            "delta_dr": self.delta_dr,
            "delta_token_mass": self.delta_token_mass,
            "delta_mass_e8": self.delta_mass_e8,
            "delta_mass_tarpit": self.delta_mass_tarpit,
            "warmstart_outcome": self.warmstart_outcome.value,
            "seam_role": self.seam_role,
            "geometry_invariant": self.geometry_invariant,
            "verdict": self.verdict,
            "extra": self.extra,
        }


def compute_token_metrics(concat: str) -> TokenMetrics:
    canonical = NLAECNFChain.full_chain(concat)
    dr = int(canonical["digital_root"])
    token_mass = len(set(concat.lower()))
    mass_e8 = _kissing_proxy(dr, token_mass)
    mass_tarpit = round(token_mass * COUPLING, 6)
    return TokenMetrics(
        arity=len(concat),
        token_mass=token_mass,
        mass_e8=mass_e8,
        mass_tarpit=mass_tarpit,
        digital_root=dr,
        lane=str(canonical["lane"]),
        snap_key=str(canonical["snap_key"]),
    )


def compute_morph_signature(
    base_concat: str,
    variant_concat: str,
    *,
    case_mode: Optional[CaseMode] = None,
    cache_provider: Optional[object] = None,
    require_geometry_invariant: bool = True,
) -> MorphSignature:
    base_m = compute_token_metrics(base_concat)
    var_m = compute_token_metrics(variant_concat)
    geom_base = geometry_snap_key(base_concat)
    geom_var = geometry_snap_key(variant_concat)
    geometry_invariant = geom_base == geom_var

    bond = QuadBond(
        quad_left=variant_concat[:4],
        quad_right=variant_concat[4:],
        level=1,
    )
    mode = case_mode or CaseMode.LOWER
    if base_concat == variant_concat:
        outcome = WarmStartOutcome.EXACT
    elif base_concat.lower() == variant_concat.lower() and mode is not CaseMode.LOWER:
        if cache_provider is not None:
            hit = WarmStartLookup(cache_provider).probe(bond, mode)
            outcome = hit.outcome
        elif geometry_invariant:
            outcome = WarmStartOutcome.CASE_BASE
        else:
            outcome = WarmStartOutcome.COLD
    else:
        outcome = WarmStartOutcome.COLD
        if cache_provider is not None:
            hit = WarmStartLookup(cache_provider).probe(bond, mode)
            outcome = hit.outcome

    seam_role = mode.value if mode in (
        CaseMode.LEAD_RIGHT,
        CaseMode.LEAD_BOTH,
        CaseMode.CAMEL_INNER,
    ) else None

    return MorphSignature(
        base_concat=base_concat,
        variant_concat=variant_concat,
        delta_snap=0 if geometry_invariant else 1,
        delta_lane=base_m.lane != var_m.lane,
        delta_dr=var_m.digital_root - base_m.digital_root,
        delta_token_mass=var_m.token_mass - base_m.token_mass,
        delta_mass_e8=var_m.mass_e8 - base_m.mass_e8,
        delta_mass_tarpit=round(var_m.mass_tarpit - base_m.mass_tarpit, 6),
        warmstart_outcome=outcome,
        seam_role=seam_role,
        geometry_invariant=geometry_invariant,
        extra={
            "surface_snap_base": base_m.snap_key,
            "surface_snap_variant": var_m.snap_key,
            "geometry_snap": geom_base,
        },
    )


def morph_verdict(sig: MorphSignature) -> str:
    if sig.warmstart_outcome is WarmStartOutcome.CASE_BASE and sig.geometry_invariant:
        if sig.seam_role:
            return "intentional"
        return "intentional"
    if sig.geometry_invariant and sig.warmstart_outcome is WarmStartOutcome.COLD:
        return "typo"
    if sig.warmstart_outcome is WarmStartOutcome.EXACT:
        return "exact"
    return "cold"


def probe_case_pair(
    base_bond: QuadBond,
    case_mode: CaseMode,
    *,
    cache_provider: Optional[object] = None,
) -> MorphSignature:
    """Compare LOWER base to a case-shifted variant."""
    lower = apply_case(base_bond, CaseMode.LOWER)
    variant = apply_case(base_bond, case_mode)
    return compute_morph_signature(
        lower.concat,
        variant.concat,
        case_mode=case_mode,
        cache_provider=cache_provider,
    )


__all__ = [
    "TokenMetrics",
    "MorphSignature",
    "compute_token_metrics",
    "compute_morph_signature",
    "morph_verdict",
    "probe_case_pair",
    "geometry_snap_key",
    "surface_snap_key",
]
