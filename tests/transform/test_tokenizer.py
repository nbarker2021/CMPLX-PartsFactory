"""Tests for cmplx.transform.MorphonicTokenizer."""
from __future__ import annotations

import numpy as np
import pytest

from cmplx.transform import MorphonicTokenizer, TokenizerConfig


def test_tokenizer_returns_deterministic_token_ids():
    tok = MorphonicTokenizer(TokenizerConfig(seq_length=32), hidden_dim=24, seq_length=32)
    first = tok.tokenize("alpha")
    second = tok.tokenize("alpha")
    np.testing.assert_array_equal(first.token_ids, second.token_ids)
    assert first.content_hash == second.content_hash


def test_tokenizer_tensor_shape_matches_config():
    tok = MorphonicTokenizer(TokenizerConfig(seq_length=16), hidden_dim=24, seq_length=16)
    out = tok.tokenize({"a": 1})
    assert out.tensor.shape == (16, 24)


def test_tokenizer_morphon_carries_canonical_projections():
    tok = MorphonicTokenizer(TokenizerConfig(seq_length=8), hidden_dim=24, seq_length=8)
    out = tok.tokenize("beta")
    assert out.morphon.e8_coordinates is not None
    assert len(out.morphon.e8_coordinates) == 8
    assert out.morphon.dr_channel is not None


def test_tokenizer_different_inputs_differ():
    tok = MorphonicTokenizer(TokenizerConfig(seq_length=8), hidden_dim=24, seq_length=8)
    a = tok.tokenize("alpha")
    b = tok.tokenize("beta")
    assert a.content_hash != b.content_hash
    assert not np.array_equal(a.token_ids, b.token_ids)


def test_tokenizer_etp_mode_produces_program():
    tok = MorphonicTokenizer(
        TokenizerConfig(seq_length=8, encode_etp=True), hidden_dim=24, seq_length=8
    )
    # Requires the symbolic port to be registered; bootstrap on demand.
    from cmplx.transform.bridge import ensure_bootstrapped

    ensure_bootstrapped()
    out = tok.tokenize("ribbon-with-etp")
    assert out.etp_program is not None
    assert all(ch in "}<>+01" for ch in out.etp_program)
