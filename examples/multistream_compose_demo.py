#!/usr/bin/env python
"""Multistream compose demo — EN hub + mock-native sidecar on same doc."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from cmplx.primitives.core import NLAECNFChain
from cmplx.transform.compose_pipeline import compose_pipeline
from cmplx.transform.config import TransformerConfig
from cmplx.transform.lib_encoder import NativeLibEncoder, translate_hub_from_env
from cmplx.transform.meaning_store import AddressMeaningStore
from cmplx.transform.shell import MorphonShell
from cmplx.transform.shell_config import ShellConfig
from cmplx.transform.token_index.store import TokenIndexStore
from cmplx.transform.translation_store import TranslationLinkStore
from cmplx.transform.transformer import GeometricTransformer


def main() -> int:
    doc = "Morphonic unified substrate demo for multistream compose."
    hub = translate_hub_from_env()
    en_text = hub.translate(doc)
    native_enc = NativeLibEncoder()
    tkey = "demo-doc-001"

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "token_index.sqlite"
        store = TokenIndexStore(db)
        meaning = AddressMeaningStore.from_connection(store._conn, str(db))
        links = TranslationLinkStore.from_connection(store._conn, str(db))
        shell = MorphonShell(ShellConfig(), store, meaning)

        anchor = en_text[:8].ljust(8, "a")
        canonical = NLAECNFChain.full_chain(anchor)
        snap = str(canonical["snap_key"])
        from cmplx.transform.token_index.warmstart import IndexEntryPayload

        store.upsert(
            IndexEntryPayload(
                concat=anchor,
                morphon_id="demo-en",
                snap_key=snap,
                e8_coords=tuple(float(c) for c in canonical["e8_coords"]),
                digital_root=int(canonical["digital_root"]),
                lane=str(canonical["lane"]),
                cache_key=f"token_index::concat::{anchor}",
                level=1,
                case_mode="lower",
                language="any",
            ),
            bond_level=1,
            case_mode="lower",
            language="any",
            stream="en",
        )
        links.upsert(
            translation_key=tkey,
            stream="en",
            concat=anchor,
            snap_key=snap,
        )

        for seg in native_enc.encode(doc, translation_key=tkey):
            nat_canon = NLAECNFChain.full_chain(seg.concat)
            links.upsert(
                translation_key=tkey,
                stream="native",
                concat=seg.concat,
                snap_key=str(nat_canon["snap_key"]),
            )

        model = GeometricTransformer(
            TransformerConfig(num_layers=2, register_ports_on_init=False)
        )
        result = compose_pipeline(
            shell,
            partial=anchor[:4],
            transformer=model,
            run_forward=True,
        )
        print(json.dumps(result.as_dict(), indent=2, default=str))
        store.close()
        meaning.close()
        links.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
