"""
F-4 facade tests — TarPitSymbolicProvider against SymbolicProvider Protocol.

Verifies:
  1. Provider satisfies the SymbolicProvider runtime-checkable Protocol.
  2. encode_to_etp produces deterministic, syntactically valid programs.
  3. encode_to_etp differs for distinct morphons (id, payload, parent).
  4. run_program returns the expected dict shape.
  5. derive returns a SymbolicReport with all fields populated.
  6. decode_from_etp produces a derived morphon from a ledger.
  7. Round-trip semantics: encode → run → decode produces deterministic
     morphons across repeated calls.
  8. Registration on the `symbolic` port works.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import (
    Morphon,
    MorphonController,
    SymbolicProvider,
    SymbolicReport,
)
from cmplx.symbolic.tarpit import TarPitSymbolicProvider


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# 1. Protocol compliance
# ---------------------------------------------------------------------------

def test_provider_satisfies_symbolic_protocol():
    provider = TarPitSymbolicProvider()
    assert isinstance(provider, SymbolicProvider)


def test_provider_registers_on_symbolic_port():
    provider = TarPitSymbolicProvider()
    MorphonController.get().register("symbolic", provider)
    assert MorphonController.get().has("symbolic")
    assert MorphonController.get().get_provider("symbolic") is provider


# ---------------------------------------------------------------------------
# 2-3. encode_to_etp determinism + uniqueness
# ---------------------------------------------------------------------------

def test_encode_to_etp_is_deterministic():
    provider = TarPitSymbolicProvider()
    m = Morphon.forge(payload={"k": "v"})
    p1 = provider.encode_to_etp(m)
    p2 = provider.encode_to_etp(m)
    assert p1 == p2


def test_encode_to_etp_uses_loopless_alphabet():
    """Encoded programs use only `}<>+01` — no brackets, no other chars."""
    provider = TarPitSymbolicProvider()
    m = Morphon.forge(payload={"k": "v"})
    program = provider.encode_to_etp(m)
    assert all(c in "}<>+01" for c in program)
    assert "[" not in program
    assert "]" not in program


def test_encode_to_etp_program_length_matches_config():
    provider = TarPitSymbolicProvider(program_length=16)
    m = Morphon.forge(payload={"k": "v"})
    assert len(provider.encode_to_etp(m)) == 16


def test_encode_to_etp_differs_for_distinct_payloads():
    provider = TarPitSymbolicProvider()
    m1 = Morphon.forge(payload={"k": "v1"})
    m2 = Morphon.forge(payload={"k": "v2"})
    assert provider.encode_to_etp(m1) != provider.encode_to_etp(m2)


def test_encode_to_etp_differs_for_distinct_ids_same_payload():
    """Two morphons with the same payload but different IDs encode differently."""
    provider = TarPitSymbolicProvider()
    m1 = Morphon.forge(payload={"k": "v"})
    m2 = Morphon.forge(payload={"k": "v"})
    assert m1.id != m2.id
    assert provider.encode_to_etp(m1) != provider.encode_to_etp(m2)


# ---------------------------------------------------------------------------
# 4. run_program
# ---------------------------------------------------------------------------

def test_run_program_returns_summary_and_ledger():
    provider = TarPitSymbolicProvider()
    result = provider.run_program("}0}1>")
    assert "summary" in result
    assert "ledger" in result
    assert isinstance(result["ledger"], list)
    assert len(result["ledger"]) > 0


def test_run_program_summary_has_expected_keys():
    provider = TarPitSymbolicProvider()
    result = provider.run_program("}0}1>")
    summary = result["summary"]
    for key in ("dimension", "halted", "steps_executed", "wall_serial"):
        assert key in summary


def test_run_program_ledger_row_has_expected_keys():
    provider = TarPitSymbolicProvider()
    result = provider.run_program("}0}1>")
    row = result["ledger"][0]
    for key in ("step", "ip_before", "instr", "wall10", "torus8", "digital_root"):
        assert key in row


# ---------------------------------------------------------------------------
# 5. derive — dual-report shape
# ---------------------------------------------------------------------------

def test_derive_returns_symbolic_report():
    provider = TarPitSymbolicProvider(default_max_steps=50, program_length=8)
    m = Morphon.forge(payload={"k": "v"})
    report = provider.derive(m)
    assert isinstance(report, SymbolicReport)


def test_derive_report_has_trace_and_ecology():
    provider = TarPitSymbolicProvider(default_max_steps=50, program_length=8)
    m = Morphon.forge(payload={"k": "v"})
    report = provider.derive(m)
    assert isinstance(report.trace, list)
    assert len(report.trace) > 0
    assert report.ecology is not None
    # Ecology has its own surface (TarpitEcology). Check one obvious method.
    assert hasattr(report.ecology, "step_count")


def test_derive_report_has_walls_and_summary():
    provider = TarPitSymbolicProvider(default_max_steps=50, program_length=8)
    m = Morphon.forge(payload={"k": "v"})
    report = provider.derive(m)
    assert isinstance(report.output_walls, list)
    assert isinstance(report.error_walls, list)
    assert isinstance(report.summary, dict)
    assert "halted" in report.summary


def test_derive_receipts_empty_when_receipt_port_unregistered():
    """No receipt provider → empty receipts list, not an error."""
    provider = TarPitSymbolicProvider(default_max_steps=50, program_length=8)
    m = Morphon.forge(payload={"k": "v"})
    report = provider.derive(m)
    assert report.receipts == []


# ---------------------------------------------------------------------------
# 6. decode_from_etp
# ---------------------------------------------------------------------------

def test_decode_from_etp_empty_ledger_returns_marker_morphon():
    provider = TarPitSymbolicProvider()
    m = provider.decode_from_etp([])
    assert isinstance(m, Morphon)
    assert m.payload == {"etp_decode": "empty_ledger"}


def test_decode_from_etp_captures_final_state():
    provider = TarPitSymbolicProvider(default_max_steps=50)
    result = provider.run_program("}0}1>")
    decoded = provider.decode_from_etp(result["ledger"])
    assert isinstance(decoded, Morphon)
    assert decoded.payload.get("etp_decode") is True
    # The final row's wall10 should appear in the decoded payload
    assert decoded.payload["wall10"] == result["ledger"][-1]["wall10"]
    # torus8 too
    assert decoded.payload["torus8"] == list(result["ledger"][-1]["torus8"])


# ---------------------------------------------------------------------------
# 7. Round-trip determinism
# ---------------------------------------------------------------------------

def test_round_trip_determinism():
    """encode → run → decode produces the same derived morphon twice."""
    provider = TarPitSymbolicProvider(default_max_steps=50, program_length=8)
    m = Morphon.forge(payload={"k": "v"})

    program1 = provider.encode_to_etp(m)
    result1 = provider.run_program(program1)
    derived1 = provider.decode_from_etp(result1["ledger"])

    program2 = provider.encode_to_etp(m)
    result2 = provider.run_program(program2)
    derived2 = provider.decode_from_etp(result2["ledger"])

    assert program1 == program2
    assert derived1.payload["wall10"] == derived2.payload["wall10"]
    assert derived1.payload["torus8"] == derived2.payload["torus8"]
    assert derived1.payload["digital_root"] == derived2.payload["digital_root"]


def test_health_endpoint_returns_metadata():
    provider = TarPitSymbolicProvider()
    h = provider.health
    assert h["ok"] is True
    assert h["service"] == "tarpit_symbolic_provider"
    assert h["alphabet"] == "}<>+01"


def test_repr_includes_config():
    provider = TarPitSymbolicProvider(default_dimension=8, program_length=16)
    r = repr(provider)
    assert "dim=8" in r
    assert "prog_len=16" in r
