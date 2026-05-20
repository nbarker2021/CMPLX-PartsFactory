"""Tests for token metrics and morphability."""
from __future__ import annotations

import pytest

from cmplx.transform.metrics import (
    compute_morph_signature,
    compute_token_metrics,
    morph_verdict,
    probe_case_pair,
)
from cmplx.transform.token_index.bonds import QuadBond
from cmplx.transform.token_index.case import CaseMode
from cmplx.transform.token_index.notation import (
    SurfaceMode,
    load_notation_lib,
    normalize_surface,
    surfaces_equivalent,
)
from cmplx.transform.token_index.warmstart import (
    IndexEntryPayload,
    WarmStartOutcome,
    case_base_eligible,
    geometry_snap_key,
)


def test_compute_token_metrics():
    m = compute_token_metrics("baaaaaab")
    assert m.arity == 8
    assert m.token_mass == 2
    assert m.mass_e8 > 0
    assert m.mass_tarpit > 0
    assert m.snap_key


def test_baaa_lead_right_intentional():
    bond = QuadBond(quad_left="baaa", quad_right="aaab", level=1)
    sig = probe_case_pair(bond, CaseMode.LEAD_RIGHT)
    assert sig.warmstart_outcome is WarmStartOutcome.CASE_BASE
    assert sig.delta_snap == 0
    assert sig.geometry_invariant is True
    assert sig.seam_role == "lead_right"
    assert sig.verdict == "intentional"


def test_geometry_snap_invariant_for_case_shift():
    base = "baaaaaab"
    variant = "baaaAaab"
    assert geometry_snap_key(base) == geometry_snap_key(variant)


def test_case_base_eligible_requires_geometry():
    payload = IndexEntryPayload(
        concat="baaaaaab",
        morphon_id="m1",
        snap_key=geometry_snap_key("baaaaaab"),
        e8_coords=(0.0,) * 8,
        digital_root=3,
        lane="A",
        cache_key="k",
        level=1,
        case_mode="lower",
        language="any",
    )
    bond = QuadBond(quad_left="baaa", quad_right="Aaab", level=1)
    assert case_base_eligible(payload, bond) is True


def test_notation_unicode_equiv():
    lib = load_notation_lib()
    assert surfaces_equivalent("-", "−", mode=SurfaceMode.UNICODE_EQUIV, lib=lib)
    assert normalize_surface("−", mode=SurfaceMode.UNICODE_EQUIV, lib=lib) == "-"


def test_morph_verdict_cold_on_different_geometry():
    sig = compute_morph_signature("baaaaaab", "caaaaaac", case_mode=CaseMode.LOWER)
    assert sig.verdict == "cold"
