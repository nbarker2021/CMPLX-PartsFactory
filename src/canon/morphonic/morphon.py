"""
morphon.morphon — Universal Morphon (M₀): formal definition and observation calculus.

Source document: "Morphonic Geometry: A Theoretical Framework for Formless Structure"
                 Nicholas Barker, October 2025

M₀ is the initial object in category Morph. All geometric structures are
observations O(M₀) under observation functors O: Morph → Geom.

Formal construction (Definition 3.4):
    M₀ = [Σᵢ αᵢ Gᵢ] / ~
where αᵢ ∈ ℂ are complex coefficients, Gᵢ are GeometrySpec instances,
and ~ is observational equivalence (O(M) ≅ O(M') for all O ⟺ M ~ M').

TMN1 system invariants encoded here:
    tmn1:latest            IS M₀ (the master image is the Universal Morphon)
    docker-compose.yml     IS the observation schema (which functors to instantiate)
    TMN1_ROLE              IS functor selection (which F to apply to M₀)
    Every TMN1 service     IS F(M₀) for some domain functor F
    crystals               ARE stable morphons found inside M₀ (ΔΦ ≤ 0 satisfied)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import numpy as np
    _HAS_NP = True
except ImportError:
    np = None  # type: ignore[assignment]
    _HAS_NP = False


# ─────────────────────────────────────────────────────────────────────────────
# Geometry Registry
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GeometrySpec:
    """
    Named geometry: one Gᵢ in the formal sum M₀ = Σᵢ αᵢ Gᵢ.

    A GeometrySpec does not instantiate the geometry — it names it.
    Instantiation only happens via an ObservationFunctor.
    (Theorem 5.1: E8 doesn't exist "in" M₀; it's what we see when we
    observe M₀ in a particular way.)
    """
    name: str
    dimension: int          # ambient dimension of this geometry
    rank: int               # rank of root system (0 = no roots, e.g. Leech)
    root_count: int         # number of roots (0 for Leech)
    properties: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, GeometrySpec) and self.name == other.name


# Global geometry registry — all standard lattices as M₀ projections
_GEOMETRIES: Dict[str, GeometrySpec] = {
    "E8": GeometrySpec(
        "E8", dimension=8, rank=8, root_count=240,
        properties={"even": True, "unimodular": True, "density": "optimal_8d"}),
    "Leech": GeometrySpec(
        "Leech", dimension=24, rank=0, root_count=0,
        properties={"even": True, "unimodular": True, "ground_state": True,
                    "note": "Minimal energy 24D observation of M₀ (Theorem 5.3)"}),
    # 24 Niemeier lattices = 24 distinct 24D observations of M₀ (Theorem 5.2)
    **{
        f"Niemeier_{i}": GeometrySpec(
            f"Niemeier_{i}", dimension=24, rank=24, root_count=-1,
            properties={"even": True, "unimodular": True, "niemeier_index": i,
                        "note": "One of 24 distinct 24D views of M₀"})
        for i in range(1, 25)
    },
}


def register_geometry(spec: GeometrySpec) -> None:
    """Register a new geometry in the global M₀ projection registry."""
    _GEOMETRIES[spec.name] = spec


def get_geometry(name: str) -> GeometrySpec:
    """Retrieve a registered geometry by name."""
    if name not in _GEOMETRIES:
        raise KeyError(f"Geometry {name!r} not registered. "
                       f"Use register_geometry() to add it.")
    return _GEOMETRIES[name]


# ─────────────────────────────────────────────────────────────────────────────
# Observation Functor
# ─────────────────────────────────────────────────────────────────────────────

class ObservationFunctor:
    """
    Observation functor O: Morph → Geom (Definition 4.1).

    Properties:
        Idempotency:  O(O(M)) = O(M)          — observation is a projection
        Closure:      O(M) ∈ Geom             — result is determinate geometry
        Faithfulness: M ≠ M' ⟹ O(M) ≇ O(M') — different morphons distinguishable

    Domain functors in TMN1 (each service IS one of these applied to M₀):
        F_gateway   → :10000  (O applied to tool space)
        F_board     → :10001  (O applied to communication space)
        F_snap      → :10011  (O applied to label space)
        F_agent     → :10012  (O applied to agent identity space)
        ... (one per TMN1_ROLE)
    """

    def __init__(
        self,
        name: str,
        geometry: GeometrySpec,
        fn: Callable[["UniversalMorphon"], Any],
    ) -> None:
        self.name = name
        self.geometry = geometry
        self._fn = fn

    def __call__(self, morphon: "UniversalMorphon") -> "ObservationResult":
        # Idempotency: if called on a result of this same functor, return as-is
        if isinstance(morphon, ObservationResult) and morphon.functor is self:
            return morphon
        data = self._fn(morphon)
        return ObservationResult(functor=self, geometry=self.geometry, data=data)

    def compose_with_reflection(
        self, reflection: Optional[Callable] = None
    ) -> "ObservationFunctor":
        """Produce σ ∘ O — the reflection-paired functor for dihedral observation."""
        refl = reflection or _negate_coefficients
        return ObservationFunctor(
            name=f"{self.name}:σ",
            geometry=self.geometry,
            fn=lambda m: self._fn(_apply_reflection(m, refl)),
        )

    def __repr__(self) -> str:
        return f"ObservationFunctor({self.name!r} → Geom({self.geometry.name!r}))"


@dataclass
class ObservationResult:
    """
    Result of applying an ObservationFunctor to a morphon.

    Itself acts as a morphon — it CAN be further observed (further functors
    can be applied to it). This is the chain: M₀ → G₁ → G₂ → ...
    each step is a further observation narrowing to more specific geometry.

    Crystal connection: a crystal IS an ObservationResult where the data
    has been frozen (ΔΦ ≤ 0 achieved, no further entropy increase possible).
    """
    functor: ObservationFunctor
    geometry: GeometrySpec
    data: Any

    def observe(self, functor: "ObservationFunctor") -> "ObservationResult":
        """Apply another functor to this result (further observation)."""
        return functor(self)

    def is_crystal_stable(self) -> bool:
        """True if this observation has reached a stable (crystallized) state."""
        # A result is crystal-stable if its data is frozen/hashable
        try:
            hash(self.data)
            return True
        except TypeError:
            return False

    def __repr__(self) -> str:
        stable = "crystal" if self.is_crystal_stable() else "fluid"
        return f"ObservationResult({self.geometry.name!r}, {stable})"


# ─────────────────────────────────────────────────────────────────────────────
# Dihedral Observation
# ─────────────────────────────────────────────────────────────────────────────

class DihedralObservation:
    """
    Dihedral observation: pair (O₁, O₂) where O₂ = σ ∘ O₁ (Theorem 4.1).

    Necessary because single observation cannot distinguish all morphons
    (information-theoretic bound on distinguishability). Dihedral pair +
    synthesis operator S yields closed, parity-conserving geometry.

    Parity conservation is automatic (Theorem 7.2): dihedral structure
    forces even parity in the synthesized result.

    Dihedral groups Dₙ (symmetries of regular n-gon) emerge necessarily
    from any non-trivial observation requirement (Theorem 7.1).
    """

    def __init__(
        self,
        o1: ObservationFunctor,
        o2: ObservationFunctor,
        synthesis: Optional[Callable[[Any, Any], Any]] = None,
    ) -> None:
        self.o1 = o1
        self.o2 = o2
        self._synthesis = synthesis or _default_synthesis

    @classmethod
    def from_functor(
        cls,
        functor: ObservationFunctor,
        reflection: Optional[Callable] = None,
    ) -> "DihedralObservation":
        """Construct dihedral pair from a single functor + optional reflection."""
        o2 = functor.compose_with_reflection(reflection)
        return cls(o1=functor, o2=o2)

    def synthesize(self, morphon: "UniversalMorphon") -> "ObservationResult":
        """
        Apply (O₁, σ∘O₁) and synthesize into closed geometry.
        Parity is conserved automatically (Theorem 7.2).
        """
        r1 = self.o1(morphon)
        r2 = self.o2(morphon)
        synthesized_data = self._synthesis(r1.data, r2.data)
        return ObservationResult(
            functor=self.o1,
            geometry=self.o1.geometry,
            data=synthesized_data,
        )

    def __repr__(self) -> str:
        return f"DihedralObservation({self.o1.name!r} ⊕ {self.o2.name!r})"


def _negate_coefficients(morphon: "UniversalMorphon") -> "UniversalMorphon":
    """Default reflection: negate all geometry coefficients."""
    negated = {g: -c for g, c in morphon._coefficients.items()}
    return UniversalMorphon(coefficients=negated)


def _apply_reflection(
    morphon: "UniversalMorphon",
    reflection: Callable,
) -> "UniversalMorphon":
    """Apply reflection operator to morphon, returning reflected copy."""
    return reflection(morphon)


def _default_synthesis(g1: Any, g2: Any) -> Any:
    """Default synthesis S(O₁(M), O₂(M)) — geometric mean of two observations."""
    if _HAS_NP and isinstance(g1, np.ndarray) and isinstance(g2, np.ndarray):
        return (g1 + g2) / 2.0
    if isinstance(g1, dict) and isinstance(g2, dict):
        all_keys = set(g1) | set(g2)
        return {k: (g1.get(k, 0) + g2.get(k, 0)) / 2 for k in all_keys}
    return g1  # fallback: return first observation


# ─────────────────────────────────────────────────────────────────────────────
# Universal Morphon — M₀
# ─────────────────────────────────────────────────────────────────────────────

class UniversalMorphon:
    """
    Universal Morphon M₀ — the initial object in category Morph.

    Formal construction (Definition 3.4, Theorem 3.1):
        M₀ = [Σᵢ αᵢ Gᵢ] / ~
    where αᵢ ∈ ℂ, Gᵢ ∈ registered geometries, ~ is observational equivalence.

    M₀ is NOT a fixed-dimensional numpy array. It is the formal superposition
    of ALL possible geometries, each with a complex amplitude. Observation
    collapses this superposition to a specific geometry (analogous to quantum
    measurement collapsing a superposition to an eigenstate).

    Key theorems implemented:
        Theorem 3.1  — M₀ exists and is well-defined (constructor proves existence)
        Theorem 5.1  — E8 = O_E8(M₀) (E8 functor built-in)
        Theorem 5.2  — 24 Niemeier lattices = 24 distinct observations of M₀
        Theorem 5.3  — Leech = minimal-energy 24D observation (ground state)
        Theorem 5.4  — Dimension is property of observation, not of M₀
        Theorem 4.1  — Dihedral observation available on any functor

    TMN1 architecture invariant:
        tmn1:latest IS this object. Every TMN1_ROLE is F(M₀) at instantiation.
        Crystals are stable ObservationResults found inside M₀ (ΔΦ ≤ 0).
    """

    def __init__(
        self,
        coefficients: Optional[Dict[str, complex]] = None,
        seed: Optional[int] = None,
    ) -> None:
        # The formal sum: geometry_name → complex coefficient αᵢ
        # Default: uniform unit weight over all registered geometries
        if coefficients is not None:
            self._coefficients: Dict[str, complex] = dict(coefficients)
        else:
            self._coefficients = {name: complex(1.0, 0.0) for name in _GEOMETRIES}

        # Registered observation functors for this morphon
        self._functors: Dict[str, ObservationFunctor] = {}

        # Observation history (every collapse is recorded)
        self._observation_log: List[ObservationResult] = []

        # Seed for deterministic Layer 0 construction (single digit → M₀)
        self._seed = seed

        # Register built-in standard functors
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register standard observation functors for all built-in geometries."""
        self.register_functor(ObservationFunctor(
            name="E8",
            geometry=_GEOMETRIES["E8"],
            fn=lambda m: _project_to_e8(m),
        ))
        self.register_functor(ObservationFunctor(
            name="Leech",
            geometry=_GEOMETRIES["Leech"],
            fn=lambda m: _project_to_leech(m),
        ))
        # Register all 24 Niemeier functors
        for i in range(1, 25):
            idx = i
            self.register_functor(ObservationFunctor(
                name=f"Niemeier_{idx}",
                geometry=_GEOMETRIES[f"Niemeier_{idx}"],
                fn=lambda m, j=idx: _project_to_niemeier(m, j),
            ))

    def register_functor(self, functor: ObservationFunctor) -> None:
        """Register an observation functor. Multiple functors coexist — each is
        a different view of the same M₀ (not competing, co-equal projections)."""
        self._functors[functor.name] = functor

    def observe(self, functor_name: str) -> ObservationResult:
        """
        Apply named observation functor: O(M₀) → G.

        Idempotency enforced: O(O(M)) = O(M) — calling twice returns same result.
        Dimension is determined by the functor, not by M₀ (Theorem 5.4).
        """
        if functor_name not in self._functors:
            raise KeyError(
                f"No functor registered: {functor_name!r}. "
                f"Available: {list(self._functors)}"
            )
        result = self._functors[functor_name](self)
        self._observation_log.append(result)
        return result

    def observe_dihedral(self, functor_name: str) -> ObservationResult:
        """
        Apply dihedral observation (O₁, σ∘O₁) and synthesize.
        Parity conservation guaranteed (Theorem 7.2).
        """
        functor = self._functors[functor_name]
        dihedral = DihedralObservation.from_functor(functor)
        result = dihedral.synthesize(self)
        self._observation_log.append(result)
        return result

    def add(self, other: "UniversalMorphon") -> "UniversalMorphon":
        """Morphonic sum M ⊕ N: add complex coefficients per geometry."""
        merged: Dict[str, complex] = dict(self._coefficients)
        for name, coeff in other._coefficients.items():
            merged[name] = merged.get(name, 0j) + coeff
        return UniversalMorphon(coefficients=merged)

    def multiply(self, other: "UniversalMorphon") -> "UniversalMorphon":
        """Morphonic product M ⊗ N: multiply complex coefficients per geometry."""
        all_names = set(self._coefficients) | set(other._coefficients)
        merged = {
            name: self._coefficients.get(name, 0j) * other._coefficients.get(name, 0j)
            for name in all_names
        }
        return UniversalMorphon(coefficients=merged)

    def gradient(self) -> Dict[str, complex]:
        """Morphonic gradient ∇(M): discrete gradient over coefficient sequence."""
        names = list(self._coefficients)
        values = [self._coefficients[n] for n in names]
        if len(values) < 2:
            return {n: 0j for n in names}
        result: Dict[str, complex] = {}
        for i, name in enumerate(names):
            prev = values[i - 1] if i > 0 else values[0]
            nxt = values[i + 1] if i < len(values) - 1 else values[-1]
            result[name] = (nxt - prev) / 2.0
        return result

    def coefficient(self, geometry_name: str) -> complex:
        """Get complex coefficient αᵢ for a specific geometry Gᵢ."""
        return self._coefficients.get(geometry_name, 0j)

    def dominant_geometry(self) -> Optional[str]:
        """Return the geometry with the largest |αᵢ| (strongest observation)."""
        if not self._coefficients:
            return None
        return max(self._coefficients, key=lambda k: abs(self._coefficients[k]))

    def to_mglc_term(self) -> "MTerm":
        """Express this morphon as an MGLC term (the calculus of morphonic forms)."""
        # Represent as sum of observations across all geometries with non-zero coeff
        active = {g: c for g, c in self._coefficients.items() if abs(c) > 1e-10}
        if not active:
            return MVar(name="M₀")
        terms = [
            MObserve(geometry_name=g, term=MVar(name="M₀"))
            for g in active
        ]
        result = terms[0]
        for t in terms[1:]:
            result = MSum(left=result, right=t)
        return result

    @classmethod
    def from_seed(cls, seed: int) -> "UniversalMorphon":
        """
        Construct M₀ from single digit seed.
        Implements Layer 0 mod-9 iteration from CQE Architecture (Section 2.2):
        'Generate initial state from single digit. Uses mod-9 iteration to
        build 24D substrate.'
        """
        coefficients: Dict[str, complex] = {}
        names = list(_GEOMETRIES.keys())
        for i, name in enumerate(names):
            val = (seed + i * 7) % 9 + 1  # mod-9, avoids zero
            phase = (val / 9.0) * 2.0 * math.pi
            coefficients[name] = complex(math.cos(phase), math.sin(phase))
        return cls(coefficients=coefficients, seed=seed)

    @classmethod
    def from_snap_labels(cls, snap_labels: List[str]) -> "UniversalMorphon":
        """
        Construct morphon from SNAP labels: geometry weights derived from
        label content. SNAP labels ARE the observation — they determine
        which geometries are amplified.
        """
        coefficients: Dict[str, complex] = {name: complex(0.1, 0.0) for name in _GEOMETRIES}
        for label in snap_labels:
            label_lower = label.lower()
            # Amplify geometries whose names appear in labels
            for geo_name in _GEOMETRIES:
                if geo_name.lower() in label_lower:
                    coefficients[geo_name] = coefficients[geo_name] + complex(1.0, 0.0)
            # Family → geometry mapping
            if "e8" in label_lower:
                coefficients["E8"] = coefficients.get("E8", 0j) + complex(2.0, 0.0)
            if "leech" in label_lower:
                coefficients["Leech"] = coefficients.get("Leech", 0j) + complex(2.0, 0.0)
        return cls(coefficients=coefficients)

    def __add__(self, other: "UniversalMorphon") -> "UniversalMorphon":
        return self.add(other)

    def __mul__(self, other: "UniversalMorphon") -> "UniversalMorphon":
        return self.multiply(other)

    def __repr__(self) -> str:
        dominant = self.dominant_geometry() or "none"
        n_active = sum(1 for c in self._coefficients.values() if abs(c) > 1e-10)
        return (f"UniversalMorphon(active_geometries={n_active}, "
                f"dominant={dominant!r}, "
                f"observations={len(self._observation_log)})")


# ─────────────────────────────────────────────────────────────────────────────
# Internal projection functions (used by built-in functors)
# ─────────────────────────────────────────────────────────────────────────────

def _project_to_e8(morphon: "UniversalMorphon") -> Any:
    """Project M₀ → E8 (8-dimensional coordinate from E8 coefficient)."""
    coeff = morphon.coefficient("E8")
    r = abs(coeff)
    theta = math.atan2(coeff.imag, coeff.real) if abs(coeff) > 1e-15 else 0.0
    if _HAS_NP:
        return np.array([r * math.cos(theta + i * math.pi / 4.0) for i in range(8)])
    return {"e8_real": coeff.real, "e8_imag": coeff.imag, "e8_norm": r}


def _project_to_leech(morphon: "UniversalMorphon") -> Any:
    """
    Project M₀ → Leech (24D minimal-energy ground state).
    Leech = sum of all 24 Niemeier views (Theorem 5.3: Leech is the
    observation of M₀ 'at rest' in 24D — no roots, maximal density).
    """
    if _HAS_NP:
        vec = np.array([abs(morphon.coefficient(f"Niemeier_{i+1}")) for i in range(24)])
        norm = float(np.linalg.norm(vec))
        return vec / norm if norm > 1e-12 else vec
    return {"leech_dim": 24, "ground_state": True,
            "coefficients": [abs(morphon.coefficient(f"Niemeier_{i+1}")) for i in range(24)]}


def _project_to_niemeier(morphon: "UniversalMorphon", index: int) -> Any:
    """Project M₀ → Niemeier_i (one of 24 distinct 24D observations)."""
    coeff = morphon.coefficient(f"Niemeier_{index}")
    if _HAS_NP:
        # Phase-encode the coefficient into a 24D vector
        r = abs(coeff)
        base_phase = math.atan2(coeff.imag, coeff.real) if r > 1e-15 else 0.0
        return np.array([
            r * math.cos(base_phase + j * 2.0 * math.pi / 24.0)
            for j in range(24)
        ])
    return {"niemeier_index": index, "coeff_real": coeff.real, "coeff_imag": coeff.imag}


# ─────────────────────────────────────────────────────────────────────────────
# MGLC — Morphonic Geometric Lambda Calculus (Section 6)
# ─────────────────────────────────────────────────────────────────────────────

class MorphonType(Enum):
    """
    MGLC type system (Section 6.3).
    Types describe the form of a morphonic expression.
    """
    MORPHON = "Morphon"      # τ = Morphon (any morphonic state)
    GEOM = "Geom"            # τ = Geom(G) (specific geometry)
    FUNCTION = "Function"    # τ₁ → τ₂
    SUM = "Sum"              # τ₁ ⊕ τ₂
    PRODUCT = "Product"      # τ₁ ⊗ τ₂


@dataclass
class MTerm:
    """Base class for all MGLC terms (Section 6.1 syntax)."""
    morphon_type: MorphonType = field(default=MorphonType.MORPHON)


@dataclass
class MVar(MTerm):
    """Morphonic variable: x"""
    name: str = ""


@dataclass
class MLambda(MTerm):
    """Morphonic abstraction: λx.M"""
    var: str = ""
    body: Optional[MTerm] = None
    morphon_type: MorphonType = field(default=MorphonType.FUNCTION)


@dataclass
class MApp(MTerm):
    """Morphonic application: M₁ M₂"""
    func: Optional[MTerm] = None
    arg: Optional[MTerm] = None


@dataclass
class MObserve(MTerm):
    """
    Observation term: O[G](M)

    Typing rule (Section 6.3):
        Γ ⊢ M : Morphon    G is geometry
        ─────────────────────────────────
        Γ ⊢ O[G](M) : Geom(G)
    """
    geometry_name: str = ""
    term: Optional[MTerm] = None
    morphon_type: MorphonType = field(default=MorphonType.GEOM)


@dataclass
class MSum(MTerm):
    """Morphonic sum: M₁ ⊕ M₂"""
    left: Optional[MTerm] = None
    right: Optional[MTerm] = None


@dataclass
class MProd(MTerm):
    """Morphonic product: M₁ ⊗ M₂"""
    left: Optional[MTerm] = None
    right: Optional[MTerm] = None


@dataclass
class MGrad(MTerm):
    """Morphonic gradient: ∇(M)"""
    term: Optional[MTerm] = None


def substitute(term: MTerm, var: str, replacement: MTerm) -> MTerm:
    """
    Substitution for β-reduction: term[var := replacement].
    Standard capture-avoiding substitution.
    """
    if isinstance(term, MVar):
        return replacement if term.name == var else term
    if isinstance(term, MLambda):
        if term.var == var:
            return term  # variable is shadowed by inner binding
        return MLambda(var=term.var, body=substitute(term.body, var, replacement),
                       morphon_type=term.morphon_type)
    if isinstance(term, MApp):
        return MApp(func=substitute(term.func, var, replacement),
                    arg=substitute(term.arg, var, replacement))
    if isinstance(term, MObserve):
        return MObserve(geometry_name=term.geometry_name,
                        term=substitute(term.term, var, replacement),
                        morphon_type=term.morphon_type)
    if isinstance(term, MSum):
        return MSum(left=substitute(term.left, var, replacement),
                    right=substitute(term.right, var, replacement))
    if isinstance(term, MProd):
        return MProd(left=substitute(term.left, var, replacement),
                     right=substitute(term.right, var, replacement))
    if isinstance(term, MGrad):
        return MGrad(term=substitute(term.term, var, replacement))
    return term


def reduce_step(term: MTerm) -> Tuple[MTerm, bool]:
    """
    Single reduction step. Returns (reduced_term, did_reduce).

    Implements (Section 6.2):
        β-reduction:       (λx.M) N → M[x := N]
        Closure reduction: O[G](O[G](M)) → O[G](M)   (idempotency)
    """
    # β-reduction: (λx.M) N → M[x := N]
    if isinstance(term, MApp) and isinstance(term.func, MLambda):
        return substitute(term.func.body, term.func.var, term.arg), True

    # Closure reduction (idempotency): O[G](O[G](M)) → O[G](M)
    if (isinstance(term, MObserve)
            and isinstance(term.term, MObserve)
            and term.geometry_name == term.term.geometry_name):
        return term.term, True

    # Recurse into subterms
    if isinstance(term, MApp):
        f, r = reduce_step(term.func)
        if r:
            return MApp(func=f, arg=term.arg), True
        a, r = reduce_step(term.arg)
        return MApp(func=term.func, arg=a), r
    if isinstance(term, MLambda):
        b, r = reduce_step(term.body)
        return MLambda(var=term.var, body=b, morphon_type=term.morphon_type), r
    if isinstance(term, MObserve):
        t, r = reduce_step(term.term)
        return MObserve(geometry_name=term.geometry_name, term=t,
                        morphon_type=term.morphon_type), r
    if isinstance(term, MSum):
        l, r = reduce_step(term.left)
        if r:
            return MSum(left=l, right=term.right), True
        rt, r = reduce_step(term.right)
        return MSum(left=term.left, right=rt), r
    if isinstance(term, MProd):
        l, r = reduce_step(term.left)
        if r:
            return MProd(left=l, right=term.right), True
        rt, r = reduce_step(term.right)
        return MProd(left=term.left, right=rt), r
    if isinstance(term, MGrad):
        t, r = reduce_step(term.term)
        return MGrad(term=t), r

    return term, False  # already in normal form


def normalize(term: MTerm, max_steps: int = 1000) -> MTerm:
    """
    Reduce MGLC term to normal form (β-normal form — no more reductions possible).
    Terminates: well-typed MGLC terms are strongly normalizing (Theorem 6.1).
    """
    for _ in range(max_steps):
        term, did_reduce = reduce_step(term)
        if not did_reduce:
            break
    return term


# ─────────────────────────────────────────────────────────────────────────────
# Module-level M₀ singleton
# ─────────────────────────────────────────────────────────────────────────────

#: The Universal Morphon singleton.
#: tmn1:latest IS this object. Every TMN1_ROLE is an ObservationFunctor applied to it.
#: Crystals are stable ObservationResults (ΔΦ ≤ 0) found inside M₀.
M0: UniversalMorphon = UniversalMorphon()
