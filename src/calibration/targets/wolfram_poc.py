"""
WolframPocCalibration — first reality-calibration target (G5 gate, batch 1).

Compares the cmplx substrate's E8 implementation against the reference
implementation in
``CMPLX-1T/Wolfram study/cmplx_wolfram_poc.py``. Also captures the POC's
own internal-consistency claims (Rule 30 entropy, geometric-vs-CA entropy
match) as recorded values — the POC IS the reference for those.

This first target focuses on STRUCTURAL claims (E8 root set match,
norm-squared invariants). Behavioral claims (collision dynamics, phase-
transition discontinuity) are deferred to subsequent targets.
"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from typing import Any

from ..harness import CalibrationClaim, CalibrationTarget


# ─────────────────────────────────────────────────────────────────────
# Lazy POC import
# ─────────────────────────────────────────────────────────────────────

def _load_poc_module() -> Any:
    """Import the prior repo's POC as a module despite its non-package path."""
    here = Path(__file__).resolve()
    repo_root = here.parents[3]  # src/calibration/targets/wolfram_poc.py
    poc_path = repo_root / "CMPLX-1T" / "Wolfram study" / "cmplx_wolfram_poc.py"
    if not poc_path.exists():
        raise FileNotFoundError(
            f"prior POC not found at {poc_path}; this calibration target "
            f"requires the CMPLX-1T parts catalog to be present"
        )
    spec = importlib.util.spec_from_file_location("wolfram_poc_reference", poc_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not import POC at {poc_path}")
    module = importlib.util.module_from_spec(spec)
    # POC imports matplotlib at top — stub it so the import doesn't fail in
    # headless environments. matplotlib functions aren't called during the
    # claims we measure (only by visualization, which we don't invoke).
    _stub_matplotlib_if_missing()
    spec.loader.exec_module(module)
    return module


def _stub_matplotlib_if_missing() -> None:
    """Inject minimal matplotlib stubs so the POC imports without display deps."""
    if "matplotlib" in sys.modules:
        return
    try:
        import matplotlib  # noqa
        import matplotlib.pyplot  # noqa
        import matplotlib.patches  # noqa
        import matplotlib.gridspec  # noqa
        return  # real matplotlib present; let the POC use it
    except ImportError:
        pass
    import types
    matplotlib = types.ModuleType("matplotlib")
    pyplot = types.ModuleType("matplotlib.pyplot")
    patches = types.ModuleType("matplotlib.patches")
    gridspec = types.ModuleType("matplotlib.gridspec")
    pyplot.figure = lambda *a, **k: None
    pyplot.show = lambda *a, **k: None
    gridspec.GridSpec = lambda *a, **k: None
    sys.modules["matplotlib"] = matplotlib
    sys.modules["matplotlib.pyplot"] = pyplot
    sys.modules["matplotlib.patches"] = patches
    sys.modules["matplotlib.gridspec"] = gridspec


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def _roots_as_set(roots) -> set[tuple[float, ...]]:
    """Normalize a list of root vectors to a comparable set of tuples.

    Both POC and substrate represent roots in compatible numeric forms;
    rounding to 8 decimals filters out IEEE-754 noise without losing
    structure.
    """
    out = set()
    for r in roots:
        if hasattr(r, "coords"):  # POC's E8Vector
            t = r.coords
        else:
            t = tuple(r)
        out.add(tuple(round(float(x), 8) for x in t))
    return out


def _norm_squared(v) -> float:
    if hasattr(v, "norm_sq"):
        return float(v.norm_sq())
    return float(sum(float(x) ** 2 for x in v))


# ─────────────────────────────────────────────────────────────────────
# Calibration target
# ─────────────────────────────────────────────────────────────────────

class WolframPocCalibration(CalibrationTarget):
    """First reality-calibration target — Wolfram POC structural claims.

    Substrate paths exercised: ``cmplx.geometry.e8.embed.e8_roots``.

    Claims (7):
      1. POC E8 root count == 240
      2. Substrate E8 root count == 240
      3. Substrate root set matches POC root set (modulo permutation + rounding)
      4. Every substrate root has ‖v‖² == 2
      5. Every POC root has ‖v‖² == 2
      6. POC Rule 30 mean grid entropy in [0.7, 1.0]
      7. POC GeometricRule30 entropy within 0.2 of POC Rule 30 entropy
    """

    target_name = "wolfram_poc"

    def __init__(self) -> None:
        self._poc = None
        self._poc_e8 = None
        self._substrate_roots: list = []
        self._poc_roots: list = []
        self._rule30_entropy: float = -1.0
        self._geo_entropy: float = -1.0

    def setup(self) -> None:
        self._poc = _load_poc_module()
        self._poc_e8 = self._poc.E8Lattice()
        self._poc_roots = list(self._poc_e8.root_vecs)

        from cmplx.geometry.e8.embed import e8_roots
        self._substrate_roots = list(e8_roots())

        # Pre-compute the POC's Rule 30 + GeometricRule30 entropies.
        # These are deterministic given the POC's initial conditions.
        rule30 = self._poc.Rule30(width=201, height=100)
        rule30.evolve()
        self._rule30_entropy = float(rule30.entropy())

        geo = self._poc.GeometricRule30(self._poc_e8, cycle_order=8)
        geo.generate_forms(n_forms=200)
        self._geo_entropy = float(geo.compute_entropy())

    def claims(self) -> list[CalibrationClaim]:
        return [
            CalibrationClaim(
                name="poc_e8_root_count",
                expected=240,
                tolerance=0,
                observed_fn=lambda: len(self._poc_roots),
                notes="POC's E8Lattice claims 240 roots; this verifies the POC.",
            ),
            CalibrationClaim(
                name="substrate_e8_root_count",
                expected=240,
                tolerance=0,
                observed_fn=lambda: len(self._substrate_roots),
                notes="cmplx.geometry.e8.embed.e8_roots should produce 240 roots.",
            ),
            CalibrationClaim(
                name="substrate_root_set_matches_poc",
                expected=True,
                tolerance=0,
                observed_fn=lambda: (
                    _roots_as_set(self._substrate_roots) == _roots_as_set(self._poc_roots)
                ),
                notes=(
                    "If our 240 roots equal the POC's 240 roots (as sets, "
                    "modulo permutation + 8-decimal rounding), our E8 "
                    "substrate is structurally faithful to the prior repo."
                ),
            ),
            CalibrationClaim(
                name="substrate_norms_squared_all_two",
                expected=True,
                tolerance=0,
                observed_fn=lambda: all(
                    abs(_norm_squared(r) - 2.0) < 1e-6
                    for r in self._substrate_roots
                ),
                notes="Every E8 root has ‖v‖² == 2 (canonical E8 normalization).",
            ),
            CalibrationClaim(
                name="poc_norms_squared_all_two",
                expected=True,
                tolerance=0,
                observed_fn=lambda: all(
                    abs(_norm_squared(r) - 2.0) < 1e-6
                    for r in self._poc_roots
                ),
                notes="POC's E8 roots also normalize to ‖v‖² == 2.",
            ),
            CalibrationClaim(
                name="rule30_mean_entropy_in_known_range",
                expected=0.85,
                tolerance=0.20,
                observed_fn=lambda: self._rule30_entropy,
                notes=(
                    "Rule 30 mean grid entropy is empirically ≈ 0.85 ± 0.2 "
                    "depending on grid initialization. POC uses single 1 at "
                    "row 0 center, 201-wide × 100 rows."
                ),
            ),
            CalibrationClaim(
                name="geometric_entropy_matches_rule30",
                expected=self._geo_entropy_expected_placeholder,
                tolerance=0.20,
                observed_fn=lambda: self._rule30_entropy,
                notes=(
                    "POC asserts |geo_entropy - rule30_entropy| < 0.2 (main() "
                    "line ~794). Both values come from POC's own pipeline; "
                    "this claim checks the assertion holds across runs."
                ),
            ),
        ]

    @property
    def _geo_entropy_expected_placeholder(self) -> float:
        """Lazily-resolved expected for the geometric-entropy claim.

        Resolved in setup(); this property is read when claims() runs,
        which is after setup() — so _geo_entropy is populated.
        """
        return self._geo_entropy
