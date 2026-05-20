"""Smoke imports for L0 batch escrow lands."""
from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "cmplx.receipt.file_ledger",
        "cmplx.receipt.hmac_ledger",
        "cmplx.receipt.ledger_manager",
        "cmplx.nsl.phi_metric",
        "cmplx.nsl.agrm_legality",
        "cmplx.constraints.aletheia.report_bridge",
        "cmplx.constraints.aletheia.dimensional_enforcement",
        "cmplx.speedlight.atlas_o8",
        "cmplx.speedlight.lattice_cache",
        "cmplx._adapters.conservation_http",
    ],
)
def test_escrow_module_imports(module: str) -> None:
    __import__(module)


def test_phi_metric_compute() -> None:
    from cmplx.nsl.phi_metric import PhiMetric

    m = PhiMetric()
    c = m.compute({"vector": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]})
    assert c.geom >= 0


def test_report_bridge_missing() -> None:
    from cmplx.constraints.aletheia.report_bridge import ingest_aletheia_report

    out = ingest_aletheia_report("/nonexistent/path.json")
    assert out["status"] == "missing_report"
