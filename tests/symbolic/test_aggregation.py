"""Aggregation across evolving_tarpit, glyphic_tarpit, unified_tarpit."""
from __future__ import annotations

import pytest

from cmplx.symbolic.tarpit import (
    CANONICAL_FORMS,
    TarpitAggregator,
    TarPitSymbolicProvider,
    glyphs_to_etp_program,
    GLYPH_LEXICON,
)
from cmplx.symbolic.tarpit._functions import RelativityEnvelope


def test_canonical_forms_tuple():
    assert "evolving_tarpit" in CANONICAL_FORMS
    assert "glyphic_tarpit" in CANONICAL_FORMS
    assert "unified_tarpit" in CANONICAL_FORMS


def test_glyphic_lexicon_and_program_encode():
    assert "🧠" in GLYPH_LEXICON
    prog = glyphs_to_etp_program("🧠💡", program_length=8)
    assert len(prog) == 8
    assert all(c in "}<>+01" for c in prog)


def test_unified_run_with_ledger():
    agg = TarpitAggregator(max_steps=32)
    out = agg.run_unified("}01", envelope=RelativityEnvelope(enabled=False))
    assert "ledger" in out
    assert len(out["ledger"]) >= 1


def test_aggregator_glyph_mode_session():
    prov = TarPitSymbolicProvider(program_length=16, default_max_steps=40)
    result = prov.execute_aggregated("🧾✓", mode="glyph")
    assert result["session"]["canonical_form"] == "glyphic_tarpit"
    assert result["result"]["ledger_rows"] >= 0


def test_evolve_lineage():
    agg = TarpitAggregator(max_steps=30)
    lineage = agg.evolve_lineage("}01", iterations=2, mutation_rate=0.5)
    assert len(lineage) == 2
    assert lineage[0].steps_executed >= 0


def test_provider_evolve_program():
    prov = TarPitSymbolicProvider(default_max_steps=25)
    rows = prov.evolve_program("}0", iterations=2)
    assert len(rows) == 2
