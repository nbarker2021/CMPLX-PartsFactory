"""
Stop theorizing. Actually USE the walls + MirrorOperator + E8 simple
roots + NLAECNFChain canonicalization on real inputs and print what
happens.

Three concrete things:

  1. Build grains, fire an ErrorWall via WallEmitter, run MirrorOperator
     and observe what the MirroredState actually contains.
  2. Run chamber_reflection(grain, boundary_normal) using one of E8's
     simple roots as the boundary, and see how the grain moves.
  3. Canonicalize real-text tokens through NLAECNFChain.full_chain and
     check whether the produced snap_keys overlap with the substrate's
     existing 62.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np

from cmplx.geometry.e8.e8_roots import E8RootSystem
from cmplx.primitives.core import NLAECNFChain
from cmplx.symbolic.tarpit import (
    DimensionalExtent,
    ErrorClass,
    Grain,
    GrainType,
    MirrorOperator,
    WallEmitter,
)


# ---------------------------------------------------------------------------
# 1. Walls + Mirror with actual grains
# ---------------------------------------------------------------------------

def demo_walls_and_mirror() -> dict:
    """Build two grains whose extent vectors sit on different sides of
    a hyperplane. Pretend an invariant is violated. Fire an ErrorWall.
    Apply the MirrorOperator. Inspect the MirroredState."""
    g1 = Grain(
        grain_type=GrainType.BIT,
        value=1,
        extent=DimensionalExtent(
            vector=(0.5, -0.5, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0),
        ),
        position=0,
    )
    g2 = Grain(
        grain_type=GrainType.BIT,
        value=1,
        extent=DimensionalExtent(
            vector=(0.7, 0.7, -0.2, 0.0, 0.0, 0.0, 0.0, 0.0),
        ),
        position=1,
    )

    emitter = WallEmitter()
    wall = emitter.emit_error(
        error_class=ErrorClass.INVARIANT_VIOLATION,
        reproducer_grains=[g1, g2],
        violated_invariants=["L_max_exceeded", "phase_bound_breach"],
        context={"slice_attempt": "unif|icati|on", "char_index": 5},
        time=0,
    )

    mirror = MirrorOperator()
    state = mirror.apply_mirror(wall, [g1, g2], time=0)
    assert state is not None

    return {
        "wall": {
            "id": wall.id,
            "error_class": wall.error_class.value,
            "stack_signature": wall.stack_signature,
            "violated_invariants": wall.violated_invariants,
            "suggested_actions": wall.suggested_actions,
            "mirror_candidate": wall.mirror_candidate,
            "context": wall.context,
        },
        "mirrored_state": {
            "id": state.id,
            "mirror_type": state.mirror_type,
            "counter_grain_count": len(state.counter_grains),
            "counter_grain_extents": [
                list(g.extent.vector) for g in state.counter_grains
            ],
            "new_mediator_extent": (
                list(state.new_mediator.extent.vector) if state.new_mediator else None
            ),
            "new_mediator_certs": (
                state.new_mediator.certificates if state.new_mediator else None
            ),
            "stability_check": state.certificates.get("stability_check"),
            "is_valid_bridge": state.is_valid_bridge(),
        },
        "wall_emitter_stats": emitter.get_wall_statistics(),
    }


# ---------------------------------------------------------------------------
# 2. chamber_reflection across an E8 simple-root boundary
# ---------------------------------------------------------------------------

def demo_chamber_reflection() -> dict:
    """Take the same g1 and reflect it across each of E8's simple roots.
    Print before/after extent vectors so we can see the geometry move."""
    g = Grain(
        grain_type=GrainType.BIT,
        value=1,
        extent=DimensionalExtent(
            vector=(0.6, 0.3, 0.1, -0.2, 0.4, 0.0, 0.0, 0.0),
        ),
    )

    simple_roots = E8RootSystem().get_simple_roots()
    mirror = MirrorOperator()
    out: dict = {
        "original_extent": list(g.extent.vector),
        "reflections": [],
    }
    for i, alpha in enumerate(simple_roots):
        # Skip zero-length roots if any made it in.
        n = np.linalg.norm(alpha)
        if n == 0:
            continue
        reflected = mirror.chamber_reflection(g, tuple(float(x) for x in alpha))
        out["reflections"].append({
            "simple_root_index": i,
            "boundary_normal": [int(x) for x in alpha],
            "reflected_extent": [round(x, 4) for x in reflected.extent.vector],
            "delta_from_original": [
                round(b - a, 4)
                for a, b in zip(g.extent.vector, reflected.extent.vector)
            ],
            "certs": reflected.certificates,
        })
    return out


# ---------------------------------------------------------------------------
# 3. NLAECNFChain on real text tokens — do they hit existing snap_keys?
# ---------------------------------------------------------------------------

def demo_canonicalize_real_text(db_path: str = "data/token_index.sqlite") -> dict:
    """Take a handful of real workspace tokens, canonicalize each, and
    check whether the snap_key appears in the current substrate."""
    # Pad shorter tokens to 8 chars with base 'a' (the existing build
    # convention). Truncate longer ones for this probe — we will let
    # the bonded-tuple logic handle them once it's wired.
    raw_tokens = [
        "morphon",   # 7 chars
        "tarpit",    # 6 chars
        "snap",      # 4 chars
        "between",   # 7 chars
        "process",   # 7 chars
        "ribbon",    # 6 chars
        "transfor",  # 8 chars (truncated 'transformer')
        "identity",  # 8 chars
        "review",    # 6 chars
        "geometry",  # 8 chars
        "thethe",    # 6 chars (deliberately bigram-rich)
        "between",   # duplicate of above
        "wallread",  # made-up 8 char
    ]

    existing = set()
    if Path(db_path).exists():
        con = sqlite3.connect(db_path)
        existing = {
            row[0] for row in con.execute(
                "SELECT DISTINCT snap_key FROM token_bonds"
            )
        }
        con.close()

    chain_results = []
    new_keys: set[str] = set()
    seen_keys: set[str] = set()

    for tok in raw_tokens:
        padded = (tok + "a" * 8)[:8].lower()
        try:
            canonical = NLAECNFChain.full_chain(padded)
        except Exception as exc:
            chain_results.append({
                "token": tok,
                "padded": padded,
                "error": f"{type(exc).__name__}: {exc}",
            })
            continue
        snap = canonical.get("snap_key")
        is_existing = snap in existing
        if is_existing:
            seen_keys.add(snap)
        else:
            new_keys.add(snap)
        chain_results.append({
            "token": tok,
            "padded": padded,
            "snap_key": snap,
            "lane": canonical.get("lane"),
            "digital_root": canonical.get("digital_root"),
            "in_substrate": is_existing,
        })

    return {
        "existing_snap_key_count": len(existing),
        "results": chain_results,
        "summary": {
            "tokens_tested": len(raw_tokens),
            "snap_keys_in_substrate": len(seen_keys),
            "snap_keys_new": len(new_keys),
            "new_snap_keys": sorted(new_keys),
        },
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    out = {
        "walls_and_mirror": demo_walls_and_mirror(),
        "chamber_reflection": demo_chamber_reflection(),
        "canonicalize_real_text": demo_canonicalize_real_text(),
    }
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
