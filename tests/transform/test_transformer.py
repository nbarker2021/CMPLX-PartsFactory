"""Tests for cmplx.transform.GeometricTransformer (full stack)."""
from __future__ import annotations

import numpy as np
import pytest

from cmplx.transform import (
    AttentionConfig,
    GeometricTransformer,
    LayerConfig,
    TransformerConfig,
)


def test_default_construction():
    model = GeometricTransformer()
    assert len(model.layers) == 4
    assert model.config.hidden_dim == 24  # 8 * 3 domains


def test_invalid_config_raises():
    with pytest.raises(ValueError):
        TransformerConfig(num_layers=0)
    with pytest.raises(ValueError):
        TransformerConfig(num_layers=2, layers=[LayerConfig()])  # length mismatch


def test_forward_returns_full_output():
    model = GeometricTransformer(TransformerConfig(num_layers=2))
    out = model.forward("ribbon-content")
    assert out.ribbon_out is not None
    assert out.final_morphon.id
    assert out.cache_key.startswith("transform::")
    assert len(out.layer_traces) == 2
    assert out.speedlight_hit is False


def test_forward_is_idempotent_via_speedlight():
    model = GeometricTransformer(TransformerConfig(num_layers=2))
    a = model.forward("idempotency-ribbon")
    b = model.forward("idempotency-ribbon")
    assert a.cache_key == b.cache_key
    assert b.speedlight_hit is True


def test_different_inputs_yield_different_cache_keys():
    model = GeometricTransformer(TransformerConfig(num_layers=1))
    a = model.forward("alpha")
    b = model.forward("beta")
    assert a.cache_key != b.cache_key


def test_config_digest_in_cache_key_changes_when_attention_changes():
    base = GeometricTransformer(TransformerConfig(num_layers=1))
    alt = GeometricTransformer(
        TransformerConfig(
            num_layers=1,
            layers=[LayerConfig(attention=AttentionConfig(max_stages=2))],
        )
    )
    a = base.forward("settings-cache-test")
    b = alt.forward("settings-cache-test")
    assert a.cache_key != b.cache_key


def test_output_mode_etp_returns_string():
    model = GeometricTransformer(TransformerConfig(num_layers=1, output_mode="etp"))
    out = model.forward("etp-ribbon")
    assert isinstance(out.ribbon_out, str)
    assert all(ch in "}<>+01" for ch in out.ribbon_out)


def test_output_mode_raw_returns_input():
    model = GeometricTransformer(TransformerConfig(num_layers=1, output_mode="raw"))
    out = model.forward("raw-ribbon-passthrough")
    assert out.ribbon_out == "raw-ribbon-passthrough"


def test_hooks_invoked_when_set():
    seen: list[int] = []

    def pre(state, idx, layer_cfg):
        seen.append(idx)

    model = GeometricTransformer(
        TransformerConfig(num_layers=2, hook_pre_layer=pre)
    )
    model.forward("hooks-ribbon")
    assert seen == [0, 1]
