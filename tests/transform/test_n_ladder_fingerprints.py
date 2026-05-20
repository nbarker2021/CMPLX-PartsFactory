"""N-ladder layer fingerprints — eight distinct typed policies."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from cmplx.transform.config import LayerConfig
from cmplx.transform.n_ladder import default_n_ladder_stack, layer_configs_from_n_ladder


def _layer_fingerprint(layer: LayerConfig) -> str:
    payload = {
        "attention": asdict(layer.attention),
        "ffn": asdict(layer.ffn),
        "nsl_mode": layer.nsl_mode,
        "nsl_budget": layer.nsl_budget,
        "use_speedlight_residual": layer.use_speedlight_residual,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]


def test_n_ladder_eight_distinct_layer_fingerprints():
    layers = layer_configs_from_n_ladder()
    assert len(layers) == 8
    fingerprints = {_layer_fingerprint(layer) for layer in layers}
    assert len(fingerprints) == 8


def test_n_ladder_stack_tags_map_to_distinct_ffn_steps():
    stack = default_n_ladder_stack()
    assert len(stack) == 8
    ffn_steps = {entry.ffn_max_steps for entry in stack}
    assert len(ffn_steps) >= 6
    attention_modes = {entry.attention_mode for entry in stack}
    assert len(attention_modes) >= 2
