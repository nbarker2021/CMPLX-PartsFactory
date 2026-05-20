"""Smoke test for the PyTorch wrapper. Skipped when torch is missing."""
from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from cmplx.transform import TransformerConfig
from cmplx.transform.torch import GeometricTransformerModule


def test_torch_module_constructs_and_runs():
    module = GeometricTransformerModule(TransformerConfig(num_layers=1))
    result = module.forward("torch-smoke-ribbon")
    assert isinstance(result, dict)
    assert "cache_key" in result and result["cache_key"].startswith("transform::")
    assert isinstance(module.last_hidden, torch.Tensor)
    assert module.last_hidden.shape == (
        module.config.seq_length,
        module.config.hidden_dim,
    )


def test_torch_module_set_attention_policy_updates_layer():
    module = GeometricTransformerModule(TransformerConfig(num_layers=1))
    module.set_attention_policy(0, max_stages=2, stop_threshold=-1.0)
    assert module.config.layers[0].attention.max_stages == 2
    assert module.backend.layers[0].attention.config.max_stages == 2


def test_torch_module_last_output_populated():
    module = GeometricTransformerModule(TransformerConfig(num_layers=1))
    assert module.last_output() is None
    module.forward("torch-smoke-output")
    out = module.last_output()
    assert out is not None
    assert out.cache_key.startswith("transform::")
