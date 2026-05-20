"""End-to-end smoke for the Morphonic Transformer (Slot 48).

Run with `PYTHONPATH=src python examples/transform_smoke.py`.

Demonstrates:
  - Default construction (4 layers, 24-D hidden, MORSR pulse, TarPit FFN)
  - One forward pass against a string ribbon
  - SpeedLight whole-forward idempotency on the second call
  - Per-layer summary access
"""
from __future__ import annotations

import json
import logging

from cmplx.transform import (
    AttentionConfig,
    GeometricTransformer,
    LayerConfig,
    TransformerConfig,
)

logging.basicConfig(level=logging.WARNING)


def main() -> None:
    config = TransformerConfig(
        num_layers=2,
        layers=[
            LayerConfig(attention=AttentionConfig(mode="pulse", max_stages=2)),
            LayerConfig(attention=AttentionConfig(mode="traverse")),
        ],
    )
    model = GeometricTransformer(config)

    ribbon = "the morphonic transformer projects a ribbon into geometric space"
    first = model.forward(ribbon)
    second = model.forward(ribbon)

    print("=== forward summary ===")
    print(json.dumps(first.summary, indent=2, default=str))
    print()
    print(f"cache_key (first):  {first.cache_key}")
    print(f"cache_key (second): {second.cache_key}")
    print(f"speedlight_hit (first):  {first.speedlight_hit}")
    print(f"speedlight_hit (second): {second.speedlight_hit}")
    print()
    print("=== per-layer summary ===")
    for trace in first.layer_traces:
        attn = trace.attention
        ffn = trace.ffn
        print(
            f"layer {trace.layer_idx}: "
            f"attention(mode={attn.mode} status={attn.status} stages={attn.stage_count}) "
            f"ffn(steps={ffn.steps} halted={ffn.halted})"
        )


if __name__ == "__main__":
    main()
