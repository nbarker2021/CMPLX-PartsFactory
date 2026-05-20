#!/usr/bin/env python
"""Load a crystal bundle (schema 2.1.0) and run meaning query + production forward."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cmplx.transform import GeometricTransformer
from cmplx.transform.config import ProductionTransformerConfig, TransformerConfig
from cmplx.transform.crystal_pack import CrystalPackager, SCHEMA_VERSION


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Load crystal bundle v2.1.0 and demo shell + forward."
    )
    parser.add_argument(
        "--bundle",
        default="crystals/identity_review.crystal",
        help="Path to .crystal bundle directory (manifest schema 2.1.0)",
    )
    parser.add_argument("--label", default="morphonic", help="Meaning query label")
    parser.add_argument("--ribbon", default="th", help="Partial ribbon for forward/complete")
    parser.add_argument(
        "--production",
        action="store_true",
        help="Use ProductionTransformerConfig (N-ladder, shell bind, 7+ layers).",
    )
    args = parser.parse_args()

    bundle = Path(args.bundle)
    if not bundle.is_dir():
        print(f"bundle not found: {bundle}", file=sys.stderr)
        return 1

    info = CrystalPackager.info(bundle)
    manifest = info.get("manifest") if isinstance(info.get("manifest"), dict) else info
    schema = (manifest or {}).get("schema_version", "")
    if schema and schema != SCHEMA_VERSION:
        print(
            f"warning: bundle schema {schema!r} != expected {SCHEMA_VERSION!r}",
            file=sys.stderr,
        )

    loaded = CrystalPackager().load(bundle)
    rows = loaded.meaning.by_label(args.label, limit=5)
    print("=== meaning query ===")
    print(json.dumps([r.as_dict() for r in rows], indent=2, default=str))

    completions = loaded.shell.complete(args.ribbon, max_candidates=8)
    print("=== shell complete ===")
    print(json.dumps({"partial": args.ribbon, "candidates": completions}, indent=2))

    ribbon = args.ribbon
    if completions:
        ribbon = completions[0][:8] if len(completions[0]) >= 8 else args.ribbon.ljust(8, "a")

    if args.production:
        config = ProductionTransformerConfig(register_ports_on_init=False)
    else:
        config = TransformerConfig(num_layers=1, register_ports_on_init=False)

    model = GeometricTransformer(config, shell=loaded.shell)
    out = model.forward(ribbon)
    print("=== forward summary ===")
    print(
        json.dumps(
            {
                "production": args.production,
                "schema_version": schema or SCHEMA_VERSION,
                "ribbon": ribbon,
                "ribbon_out": out.ribbon_out,
                "cache_key": out.cache_key,
                "num_layer_traces": len(out.layer_traces),
            },
            indent=2,
            default=str,
        )
    )

    loaded.store.close()
    loaded.meaning.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
