"""Tests for cmplx.transform.GeometricTransformerLayer."""
from __future__ import annotations

import numpy as np

from cmplx.transform import (
    AttentionConfig,
    FFNConfig,
    GeometricTransformerLayer,
    HiddenState,
    LayerConfig,
    MorphonicTokenizer,
    TokenizerConfig,
)
from cmplx.transform.bridge import ensure_bootstrapped


def _build_state(seed: str = "layer-test") -> HiddenState:
    ensure_bootstrapped()
    tok = MorphonicTokenizer(TokenizerConfig(seq_length=8), hidden_dim=24, seq_length=8)
    out = tok.tokenize(seed)
    return HiddenState(tensor=out.tensor, morphon=out.morphon)


def test_layer_forward_preserves_tensor_shape():
    state = _build_state()
    layer = GeometricTransformerLayer(LayerConfig())
    new_state, trace = layer.forward(state, layer_idx=0)
    assert new_state.tensor.shape == state.tensor.shape
    assert trace.layer_idx == 0


def test_layer_trace_records_attention_and_ffn():
    state = _build_state()
    layer = GeometricTransformerLayer(
        LayerConfig(
            attention=AttentionConfig(stop_threshold=-1.0, max_stages=2),
            ffn=FFNConfig(max_steps=64, program_length=16),
        )
    )
    _, trace = layer.forward(state, layer_idx=2)
    assert trace.attention.mode == "pulse"
    assert trace.attention.stage_count == 2
    assert trace.ffn.steps > 0


def test_layer_speedlight_cache_hit_on_repeat():
    state = _build_state(seed="cache-hit-test")
    layer = GeometricTransformerLayer(LayerConfig())
    _, first = layer.forward(state, layer_idx=0, cache_namespace="ns")
    state2 = HiddenState(tensor=state.tensor.copy(), morphon=state.morphon)
    _, second = layer.forward(state2, layer_idx=0, cache_namespace="ns")
    assert first.speedlight_cache_key == second.speedlight_cache_key
    assert second.speedlight_hit is True


def test_layer_nsl_gate_marks_rejection():
    state = _build_state()
    layer = GeometricTransformerLayer(LayerConfig(nsl_mode="govern", nsl_budget=0.0))
    new_state, trace = layer.forward(state, layer_idx=0)
    assert isinstance(trace.nsl_pre_attn_accepted, bool)
    assert isinstance(trace.nsl_post_ffn_accepted, bool)
