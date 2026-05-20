"""
CrystalPackager — pack / load morphonic workstate bundles.
"""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

from cmplx.crystal.registry import CrystalRegistry
from cmplx.crystal.types import Crystal

from .meaning_store import AddressMeaningStore
from .rule_lib import RuleLibraryLoader
from .shell import MorphonShell
from .shell_config import ShellConfig
from .token_index.store import TokenIndexStore
from .token_index.template_frame import template_report
from .substrate_manifest import enrich_crystal_manifest
from .translation_store import TranslationLinkStore

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "2.1.0"


@dataclass
class LoadedCrystal:
    bundle_path: str
    manifest: dict[str, Any]
    crystal: Crystal
    registry: CrystalRegistry
    store: TokenIndexStore
    meaning: AddressMeaningStore
    shell: MorphonShell
    digest: str = ""


class CrystalPackager:
    """Pack index + meaning + rule libs into a ``.crystal/`` directory."""

    def pack(
        self,
        crystal_name: str,
        *,
        db: str | Path,
        libs: str | Path = "data/rule_libs",
        out: str | Path,
    ) -> Crystal:
        out_path = Path(out)
        if out_path.suffix != ".crystal" and not str(out_path).endswith(".crystal"):
            out_path = Path(str(out_path) + ("" if str(out_path).endswith("/") else ""))
        out_path.mkdir(parents=True, exist_ok=True)

        db_path = Path(db)
        libs_path = Path(libs)

        shutil.copy2(db_path, out_path / "token_index.sqlite")

        rule_dest = out_path / "rule_libs"
        if libs_path.is_dir():
            if rule_dest.exists():
                shutil.rmtree(rule_dest)
            shutil.copytree(libs_path, rule_dest)

        tmpl_stats = template_report(db_path)
        with open(out_path / "template_stats.json", "w", encoding="utf-8") as fh:
            json.dump(tmpl_stats, fh, indent=2, default=str)

        self._copy_optional_ledger(out_path)

        registry = CrystalRegistry()
        crystal = registry.create(name=crystal_name, crystal_type="workstate")

        meaning = AddressMeaningStore(db_path)
        try:
            import sqlite3

            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute("SELECT label, snap_key, source_doc FROM address_meaning").fetchall()
            except sqlite3.OperationalError:
                rows = []
            conn.close()
            for row in rows:
                content = json.dumps(
                    {
                        "label": row["label"],
                        "snap_key": row["snap_key"],
                        "source_doc": row["source_doc"],
                    },
                    sort_keys=True,
                )
                registry.add_node(
                    crystal.crystal_id,
                    content=content,
                    content_type="meaning",
                    labels=[row["label"]],
                )
        finally:
            meaning.close()

        store = TokenIndexStore(db_path)
        translation = TranslationLinkStore.from_connection(store._conn, str(db_path))
        stream_counts: dict[str, int] = {}
        link_count = 0
        morph_sig_count = 0
        try:
            stream_counts = dict(store.stats().get("by_stream", {}))
            link_count = translation.count()
            links_path = out_path / "translation_links.jsonl"
            with links_path.open("w", encoding="utf-8") as fh:
                for row in translation.all_rows():
                    fh.write(json.dumps(row.as_dict(), sort_keys=True, default=str))
                    fh.write("\n")
            morph_path = out_path / "morph_signatures.jsonl"
            try:
                from .morph_signature_store import MorphSignatureStore

                morph_store = MorphSignatureStore.from_connection(store._conn, str(db_path))
                try:
                    if morph_path.is_file():
                        morph_path.unlink()
                    morph_sig_count = morph_store.export_jsonl(morph_path)
                finally:
                    morph_store.close()
            except Exception as exc:
                logger.debug("optional morph_signatures export skipped: %s", exc)
        finally:
            store.close()

        sections = ["primary", "sidecar_native", "geometry_e6"]
        if morph_sig_count:
            sections.append("morph_signatures")

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "crystal_id": crystal.crystal_id,
            "crystal_name": crystal_name,
            "e8_root": crystal.e8_root,
            "created_at": time.time(),
            "node_count": crystal.node_count,
            "db_source": str(db_path),
            "streams": [
                {"stream": name, "bond_count": count}
                for name, count in sorted(stream_counts.items())
            ],
            "translation_link_count": link_count,
            "morph_signature_count": morph_sig_count,
            "sections": sections,
            "migration_from": "2.0.0",
            "migration_notes": "2.1.0 adds optional morph_signatures.jsonl and stream manifest fields.",
        }
        manifest = enrich_crystal_manifest(manifest)
        with open(out_path / "manifest.json", "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)

        digest = self._write_digest(out_path)
        with open(out_path / "substrate_digest.sha256", "w", encoding="utf-8") as fh:
            fh.write(digest + "\n")

        crystal.state = "committed"
        registry.commit(crystal.crystal_id)
        return crystal

    def load(self, bundle: str | Path) -> LoadedCrystal:
        bundle_path = Path(bundle)
        manifest_path = bundle_path / "manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"missing manifest: {manifest_path}")

        expected = (bundle_path / "substrate_digest.sha256").read_text(encoding="utf-8").strip()
        actual = self._compute_digest(bundle_path)
        if expected and expected != actual:
            raise ValueError(f"substrate digest mismatch: expected {expected}, got {actual}")

        with manifest_path.open(encoding="utf-8") as fh:
            manifest = json.load(fh)

        db_file = bundle_path / "token_index.sqlite"
        store = TokenIndexStore(db_file)
        meaning = AddressMeaningStore(db_file)

        loader = RuleLibraryLoader(bundle_path / "rule_libs")
        bundle_libs = loader.merge(bundle_path / "rule_libs")
        shell_cfg = bundle_libs.shell_config or ShellConfig()
        shell = MorphonShell(shell_cfg, store, meaning, bundle_libs.language_filters)

        registry = CrystalRegistry()
        crystal = registry.create(
            name=str(manifest.get("crystal_name", "loaded")),
            crystal_type="workstate",
            e8_seed=manifest.get("e8_root"),
        )
        crystal.state = "active"
        load_id = crystal.crystal_id

        for row in meaning.all_rows():
            if not row.label:
                continue
            registry.add_node(
                load_id,
                content=json.dumps(row.as_dict(), sort_keys=True),
                content_type="meaning",
                labels=[row.label],
            )

        return LoadedCrystal(
            bundle_path=str(bundle_path),
            manifest=manifest,
            crystal=crystal,
            registry=registry,
            store=store,
            meaning=meaning,
            shell=shell,
            digest=actual,
        )

    @staticmethod
    def info(bundle: str | Path) -> dict[str, Any]:
        bundle_path = Path(bundle)
        manifest = json.loads((bundle_path / "manifest.json").read_text(encoding="utf-8"))
        digest = (bundle_path / "substrate_digest.sha256").read_text(encoding="utf-8").strip()
        tmpl = {}
        tmpl_path = bundle_path / "template_stats.json"
        if tmpl_path.is_file():
            tmpl = json.loads(tmpl_path.read_text(encoding="utf-8"))
        db_path = bundle_path / "token_index.sqlite"
        stats = {}
        if db_path.is_file():
            store = TokenIndexStore(db_path)
            meaning = AddressMeaningStore(db_path)
            translation = TranslationLinkStore.from_connection(store._conn, str(db_path))
            try:
                store_stats = store.stats()
                stats = {
                    "token_bonds": store.count(),
                    "address_meaning": meaning.count(),
                    "translation_links": translation.count(),
                    "by_stream": store_stats.get("by_stream", {}),
                }
            finally:
                store.close()
                meaning.close()
        streams_manifest = manifest.get("streams", [])
        return {
            "manifest": manifest,
            "digest": digest,
            "template_stats": tmpl,
            "db_stats": stats,
            "streams": streams_manifest or [
                {"stream": k, "bond_count": v}
                for k, v in sorted(stats.get("by_stream", {}).items())
            ],
        }

    @staticmethod
    def _copy_optional_ledger(out_path: Path) -> None:
        for name in ("snap_ledger.jsonl", "receipt_chain.jsonl"):
            src_candidates = [
                Path("data") / name,
                Path("data/receipts") / name,
            ]
            for src in src_candidates:
                if src.is_file():
                    shutil.copy2(src, out_path / name)
                    break

    @staticmethod
    def _write_digest(out_path: Path) -> str:
        digest = CrystalPackager._compute_digest(out_path)
        return digest

    @staticmethod
    def _compute_digest(out_path: Path) -> str:
        h = hashlib.sha256()
        for path in sorted(out_path.rglob("*")):
            if path.is_file() and path.name != "substrate_digest.sha256":
                h.update(path.relative_to(out_path).as_posix().encode())
                h.update(path.read_bytes())
        return h.hexdigest()


__all__ = ["CrystalPackager", "LoadedCrystal", "SCHEMA_VERSION"]
