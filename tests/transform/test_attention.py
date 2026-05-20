"""Tests for cmplx.transform.MorphonicAttention."""
from __future__ import annotations

import numpy as np
import pytest

from cmplx.morphon import Morphon
from cmplx.transform import (
    AttentionConfig,
    HiddenState,
    MorphonicAttention,
    MorphonicTokenizer,
    TokenizerConfig,
)
from cmplx.transform.bridge import ensure_bootstrapped


@pytest.fixture
def seed_state():
    ensure_bootstrapped()
    tok = MorphonicTokenizer(TokenizerConfig(seq_length=8), hidden_dim=24, seq_length=8)
    out = tok.tokenize("attention-seed")
    return HiddenState(tensor=out.tensor, morphon=out.morphon)


def test_attention_pulse_returns_summary(seed_state):
    attn = MorphonicAttention(AttentionConfig(mode="pulse", stop_threshold=-1.0, max_stages=2))
    new_state, output = attn.forward(seed_state)
    assert new_state.tensor.shape == seed_state.tensor.shape
    assert output.mode == "pulse"
    assert output.stage_count == 2
    assert output.handshake_count > 0


def test_attention_max_stages_changes_trace_length(seed_state):
    one = MorphonicAttention(AttentionConfig(mode="pulse", stop_threshold=-1.0, max_stages=1))
    three = MorphonicAttention(AttentionConfig(mode="pulse", stop_threshold=-1.0, max_stages=3))
    _, out_one = one.forward(seed_state)
    _, out_three = three.forward(seed_state)
    assert out_one.stage_count < out_three.stage_count


def test_attention_traverse_mode(seed_state):
    attn = MorphonicAttention(AttentionConfig(mode="traverse"))
    new_state, output = attn.forward(seed_state)
    assert output.mode == "traverse"
    assert output.handshake_count == 240  # 240 E8 roots


def test_attention_scan_mode(seed_state):
    attn = MorphonicAttention(AttentionConfig(mode="scan", scan_radius=5.0))
    new_state, output = attn.forward(seed_state)
    assert output.mode == "scan"
    assert output.handshake_count == 240


def test_attention_unknown_mode_raises(seed_state):
    attn = MorphonicAttention(AttentionConfig(mode="not-a-mode"))
    with pytest.raises(ValueError):
        attn.forward(seed_state)
