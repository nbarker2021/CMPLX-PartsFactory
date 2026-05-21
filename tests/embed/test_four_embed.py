"""
Slot 19 tests — FourEmbedProvider against EmbedProvider Protocol.

Verifies:
  1. Protocol compliance + registration on `embed` port.
  2. Implicit decomposition (payload-as-state, default channels empty).
  3. Explicit decomposition (payload with constraint/state/evidence/operator keys).
  4. Residual handling when payload mixes reserved + extra keys.
  5. Receipt-derived evidence augmentation (default-on).
  6. include_receipt_evidence=False suppresses receipt evidence.
  7. ETP delegation + fallback parity.
  8. Bootstrap registers the embed port.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import (
    EmbedProvider,
    FourEmbedView,
    Morphon,
    MorphonController,
)
from cmplx.embed import FourEmbedProvider
from cmplx.symbolic.tarpit import TarPitSymbolicProvider


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# 1. Protocol compliance
# ---------------------------------------------------------------------------

def test_provider_satisfies_embed_protocol():
    provider = FourEmbedProvider()
    assert isinstance(provider, EmbedProvider)


def test_provider_registers_on_embed_port():
    provider = FourEmbedProvider()
    MorphonController.get().register("embed", provider)
    assert MorphonController.get().has("embed")


def test_embed_is_in_known_ports():
    from cmplx.morphon import KNOWN_PORTS
    assert "embed" in KNOWN_PORTS


# ---------------------------------------------------------------------------
# 2. Implicit decomposition (payload-as-state)
# ---------------------------------------------------------------------------

def test_implicit_decomposition_payload_becomes_state():
    provider = FourEmbedProvider()
    m = Morphon.forge(payload={"some": "data", "value": 42})
    view = provider.decompose(m)
    assert isinstance(view, FourEmbedView)
    assert view.state == {"some": "data", "value": 42}
    assert view.constraint is None
    assert view.operator is None
    assert view.morphon_id == m.id


def test_implicit_decomposition_non_dict_payload():
    provider = FourEmbedProvider(include_receipt_evidence=False)
    m = Morphon.forge(payload={"text": "hello"})
    # Replace payload with a non-dict directly (skip forge re-creation)
    object.__setattr__(m, "payload", "raw_string")
    view = provider.decompose(m)
    assert view.state == "raw_string"
    assert view.constraint is None


# ---------------------------------------------------------------------------
# 3. Explicit decomposition (reserved keys)
# ---------------------------------------------------------------------------

def test_explicit_decomposition_all_four_channels():
    provider = FourEmbedProvider()
    m = Morphon.forge(payload={
        "constraint": {"max_value": 100},
        "state": {"current": 42},
        "evidence": [{"source": "sensor_1", "reading": 42}],
        "operator": ["increment", "decrement"],
    })
    view = provider.decompose(m)
    assert view.constraint == {"max_value": 100}
    assert view.state == {"current": 42}
    assert view.evidence == [{"source": "sensor_1", "reading": 42}]
    assert view.operator == ["increment", "decrement"]


def test_explicit_decomposition_partial_channels():
    """Only some reserved keys present — others default to None."""
    provider = FourEmbedProvider(include_receipt_evidence=False)
    m = Morphon.forge(payload={
        "state": {"x": 1},
        "operator": ["transform"],
    })
    view = provider.decompose(m)
    assert view.state == {"x": 1}
    assert view.operator == ["transform"]
    assert view.constraint is None
    assert view.evidence is None


# ---------------------------------------------------------------------------
# 4. Residual handling
# ---------------------------------------------------------------------------

def test_residual_keys_merge_into_state_when_state_is_dict():
    provider = FourEmbedProvider(include_receipt_evidence=False)
    m = Morphon.forge(payload={
        "state": {"x": 1},
        "extra_key": "extra_value",
        "another": 99,
    })
    view = provider.decompose(m)
    assert view.state == {
        "x": 1,
        "_residual": {"extra_key": "extra_value", "another": 99},
    }


def test_residual_becomes_state_when_state_missing():
    """Payload has reserved keys (e.g., constraint) but no state — residual
    fills the state channel."""
    provider = FourEmbedProvider(include_receipt_evidence=False)
    m = Morphon.forge(payload={
        "constraint": {"max": 100},
        "value": 42,
        "label": "test",
    })
    view = provider.decompose(m)
    assert view.constraint == {"max": 100}
    assert view.state == {"value": 42, "label": "test"}


# ---------------------------------------------------------------------------
# 5. Receipt-derived evidence
# ---------------------------------------------------------------------------

def test_receipt_evidence_is_populated_by_default():
    provider = FourEmbedProvider()  # default include_receipt_evidence=True
    m = Morphon.forge(payload={"k": "v"})
    view = provider.decompose(m)
    # The forge call leaves one receipt.
    assert view.evidence is not None
    assert isinstance(view.evidence, list)
    assert len(view.evidence) >= 1
    assert view.evidence[0]["operation"] == "forge"


def test_receipt_evidence_suppressed_when_flag_disabled():
    provider = FourEmbedProvider(include_receipt_evidence=False)
    m = Morphon.forge(payload={"k": "v"})
    view = provider.decompose(m)
    assert view.evidence is None


def test_explicit_evidence_takes_precedence_over_receipts():
    """When the payload supplies evidence, receipts don't override it."""
    provider = FourEmbedProvider()
    m = Morphon.forge(payload={
        "state": {"x": 1},
        "evidence": [{"source": "explicit"}],
    })
    view = provider.decompose(m)
    assert view.evidence == [{"source": "explicit"}]


# ---------------------------------------------------------------------------
# 6. ETP delegation + fallback parity
# ---------------------------------------------------------------------------

def test_encode_to_etp_fallback_when_symbolic_unregistered():
    provider = FourEmbedProvider()
    m = Morphon.forge(payload={"k": "v"})
    program = provider.encode_to_etp(m)
    assert all(c in "}<>+01" for c in program)


def test_encode_to_etp_delegates_when_symbolic_registered():
    symbolic = TarPitSymbolicProvider()
    embed = FourEmbedProvider()
    MorphonController.get().register("symbolic", symbolic)
    m = Morphon.forge(payload={"k": "v"})
    assert embed.encode_to_etp(m) == symbolic.encode_to_etp(m)


def test_fallback_etp_parity_with_symbolic():
    """The local fallback matches the canonical symbolic provider byte-for-byte."""
    symbolic = TarPitSymbolicProvider(program_length=32)
    embed = FourEmbedProvider()
    m = Morphon.forge(payload={"k": "v"})
    assert embed.encode_to_etp(m) == symbolic.encode_to_etp(m)


def test_decode_from_etp_empty_returns_marker():
    provider = FourEmbedProvider()
    m = provider.decode_from_etp([])
    assert m.payload["etp_decode"] == "empty_ledger"
    assert m.payload.get("identity_kind") == "morphon"


# ---------------------------------------------------------------------------
# 7. Bootstrap integration
# ---------------------------------------------------------------------------

def test_bootstrap_registers_embed_port():
    from runtime.cmplx_bootstrap import register_all
    status = register_all()
    assert "embed" in status
    assert status["embed"] == "registered (in-process)"
    assert MorphonController.get().has("embed")


def test_bootstrap_registered_embed_satisfies_protocol():
    from runtime.cmplx_bootstrap import register_all
    register_all()
    p = MorphonController.get().get_provider("embed")
    assert isinstance(p, EmbedProvider)


# ---------------------------------------------------------------------------
# 8. Health + repr
# ---------------------------------------------------------------------------

def test_health_endpoint():
    provider = FourEmbedProvider()
    h = provider.health
    assert h["ok"] is True
    assert h["service"] == "four_embed_provider"
    assert h["include_receipt_evidence"] is True


def test_repr_includes_flag():
    provider = FourEmbedProvider(include_receipt_evidence=False)
    assert "receipt_evidence=False" in repr(provider)
