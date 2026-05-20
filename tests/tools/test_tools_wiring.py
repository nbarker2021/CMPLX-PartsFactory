"""Verify Manus + primitives toolkit wiring works as advertised."""
from __future__ import annotations

import numpy as np
import pytest

from cmplx.engine.manifold import ManifoldPipeline
from cmplx.morphon.controller import MorphonController
from cmplx.primitives import Base4Codec, e8_snap
from cmplx.tools import ManusToolsProvider, register_default_toolkit
from cmplx.tools.manus.e8_lattice import E8Lattice


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_e8_lattice_shim_240_roots():
    lat = E8Lattice()
    roots = lat.get_roots()
    assert len(roots) == 240
    assert len(roots[0].coords) == 8


def test_manus_provider_adapt_all_manifest_tools():
    prov = ManusToolsProvider()
    for t in prov.list_tools():
        tid = t["tool_id"]
        rails = prov.adapt(tid, {"features": list(range(24))})
        assert rails["alpha"].shape == (8,)


def test_protein_fold_instrument_runs():
    prov = ManusToolsProvider()
    out, receipt = prov.run_instrument(
        "protein_fold_morphon",
        "analyze_sequence",
        [(-60.0, -45.0), (-70.0, -30.0)],
    )
    assert receipt.success
    assert out is not None


def test_manifold_pipeline_conservation_gate():
    pipe = ManifoldPipeline()
    item = pipe.process(
        "T01_protein_fold_morphon",
        {"dihedral_angles": [1.0] * 8},
        phi_before=np.ones(8) * 0.5,
        phi_after=np.ones(8) * 10.0,
    )
    assert item.admitted is False


def test_manifold_pipeline_eversion_tempering():
    pipe = ManifoldPipeline()
    item = pipe.process(
        "T01_protein_fold_morphon",
        {"dihedral_angles": [(-60.0, -45.0), (-70.0, -30.0)]},
        eversion=True,
    )
    assert "eversion" in item.metadata
    assert item.metadata["eversion"]["genus"]
    assert item.rails["alpha"].shape == (8,)


def test_register_on_engine_mesh():
    from cmplx.engine.cqe import CQEProvider

    mc = MorphonController.get()
    mc.register("engine", CQEProvider())
    manus = register_default_toolkit()
    assert mc.get_provider("engine").manus is manus
    assert manus.health()["tools_in_manifest"] == 30


def test_primitives_base4_roundtrip():
    data = b"cmplx-test"
    z4 = Base4Codec.bytes_to_z4(data)
    back = Base4Codec.z4_to_bytes(z4)
    assert back == data


def test_primitives_e8_snap():
    v = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    snapped, dist = e8_snap(v)
    assert snapped.shape == (8,)
    assert dist >= 0.0
