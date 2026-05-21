"""
CorpusIngester — walk user docs, slice, canonicalize, upsert substrate + meaning.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence

from cmplx.morphon import Morphon

from .morphon_ingest import forge_ingest_morphon
from cmplx.primitives.core import NLAECNFChain
from cmplx.runtime_paths import runtime_path
from cmplx.snap.labeler import SNAPLabeler

from .bridge import get_receipt_provider, has_provider
from .meaning_store import AddressMeaningStore
from .rule_lib import RuleLibraryLoader, apply_language_filters
from .shell import MorphonShell
from .shell_config import ShellConfig
from .token_index.bonds import QuadBond
from .token_index.case import CaseMode
from .lib_encoder import (
    EncodedSegment,
    LibEncoder,
    NoOpHub,
    TranslateHub,
    encoder_for_stream,
    translate_hub_from_env,
)
from .metrics import compute_token_metrics
from .token_index.store import TokenIndexStore
from .e6_lift import lift_concat
from .token_geometry import GeometryRow, TokenGeometryStore
from .translation_store import TranslationLinkStore
from .token_index.warmstart import (
    IndexEntryPayload,
    WarmStartLookup,
    WarmStartOutcome,
    key_exact,
    publish_entry,
)
from .bridge import ensure_bootstrapped, get_cache_provider, has_provider as _has

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 512
TEXT_EXTENSIONS = {".md", ".txt", ".py"}


@dataclass
class IngestStats:
    files_seen: int = 0
    chunks_seen: int = 0
    new_bonds: int = 0
    bond_skips: int = 0
    new_meanings: int = 0
    new_labels: int = 0
    cache_hits: int = 0
    bond_morphons: int = 0
    elapsed_seconds: float = 0.0

    def as_dict(self) -> dict:
        return {
            "files_seen": self.files_seen,
            "chunks_seen": self.chunks_seen,
            "new_bonds": self.new_bonds,
            "bond_skips": self.bond_skips,
            "new_meanings": self.new_meanings,
            "new_labels": self.new_labels,
            "cache_hits": self.cache_hits,
            "bond_morphons": self.bond_morphons,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
        }


@dataclass
class CorpusIngester:
    chunk_size: int = DEFAULT_CHUNK_SIZE
    shell_config: ShellConfig = field(default_factory=ShellConfig)
    register_ports: bool = True
    max_files: Optional[int] = None
    stream: str = "en"

    def ingest_path(
        self,
        root: Path,
        *,
        lib_paths: Sequence[str | Path] = (),
        db: str | Path | None = None,
        labeler: Optional[SNAPLabeler] = None,
        lib: Optional[str | Path] = None,
        translate_hub: Optional[TranslateHub] = None,
    ) -> IngestStats:
        start = time.time()
        stats = IngestStats()
        root = Path(root)

        if self.register_ports:
            ensure_bootstrapped()

        loader = RuleLibraryLoader()
        bundle = loader.merge(*lib_paths) if lib_paths else loader.merge(loader.root)
        apply_language_filters(bundle)
        shell_cfg = bundle.shell_config or self.shell_config

        db_path = Path(db) if db is not None else runtime_path("data", "token_index.sqlite")
        store = TokenIndexStore(db_path)
        meaning = AddressMeaningStore.from_connection(store._conn, str(db_path))
        links = TranslationLinkStore.from_connection(store._conn, str(db_path))
        geometry = TokenGeometryStore.from_connection(store._conn, str(db_path))
        shell = MorphonShell(shell_cfg, store, meaning, bundle.language_filters)
        snap = labeler or SNAPLabeler()
        cache = get_cache_provider() if _has("cache") else None
        lookup = WarmStartLookup(cache)
        hub = translate_hub or translate_hub_from_env()
        stream_encoder: Optional[LibEncoder] = None
        if self.stream != "en":
            stream_encoder = encoder_for_stream(self.stream, lib)

        before_bonds = store.count()
        before_meanings = meaning.count()

        for path in self._iter_files(root, max_files=self.max_files):
            stats.files_seen += 1
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                logger.warning("skip unreadable %s: %s", path, exc)
                continue
            for chunk_id, chunk in enumerate(self._chunk_text(text)):
                stats.chunks_seen += 1
                if self.stream == "en" and hub:
                    chunk = hub.translate(chunk)
                tkey = f"{path.stem}:chunk:{chunk_id}"
                if self.stream == "en":
                    self._ingest_chunk(
                        chunk,
                        source_doc=str(path),
                        source_span=f"chunk:{chunk_id}",
                        shell=shell,
                        store=store,
                        meaning=meaning,
                        snap=snap,
                        lookup=lookup,
                        stats=stats,
                        translation_key=tkey,
                        links=links,
                        geometry=geometry,
                    )
                if stream_encoder is not None:
                    self._ingest_encoded_segments(
                        stream_encoder.encode(chunk, translation_key=tkey),
                        store=store,
                        links=links,
                        lookup=lookup,
                        stats=stats,
                        geometry=geometry,
                        translation_key=tkey,
                    )

        stats.new_bonds = store.count() - before_bonds
        stats.new_meanings = meaning.count() - before_meanings
        stats.elapsed_seconds = time.time() - start
        store.close()
        links.close()
        geometry.close()
        if meaning._owns_conn:
            meaning.close()
        return stats

    def _upsert_geometry(
        self,
        geometry: TokenGeometryStore,
        concat: str,
        stream: str,
        translation_key: str,
    ) -> None:
        witness = lift_concat(concat, translation_key=translation_key, stream=stream)
        geometry.upsert(
            GeometryRow(
                concat=concat,
                stream=stream,
                snap_key=witness.snap_key,
                e6_coords=witness.e6_coords,
                e8_coords=witness.e8_coords,
                translation_key=translation_key or None,
            )
        )

    def _ingest_encoded_segments(
        self,
        segments: list[EncodedSegment],
        *,
        store: TokenIndexStore,
        links: TranslationLinkStore,
        lookup: WarmStartLookup,
        stats: IngestStats,
        geometry: TokenGeometryStore,
        translation_key: str = "",
    ) -> None:
        cache = get_cache_provider() if _has("cache") else None
        prev_morphon: Optional[Morphon] = None
        for seg in segments:
            bond = QuadBond(quad_left=seg.concat[:4], quad_right=seg.concat[4:], level=1)
            hit = lookup.probe(bond, CaseMode.LOWER)
            canonical = NLAECNFChain.full_chain(seg.concat)
            snap_key = str(canonical["snap_key"])
            links.upsert(
                translation_key=seg.translation_key,
                stream=seg.stream,
                concat=seg.concat,
                snap_key=snap_key,
            )
            self._upsert_geometry(geometry, seg.concat, seg.stream, seg.translation_key)
            if hit.outcome is WarmStartOutcome.EXACT:
                stats.cache_hits += 1
                continue
            if store.by_concat(seg.concat, stream=seg.stream):
                continue
            morphon, bond_m = forge_ingest_morphon(
                {
                    "concat": seg.concat,
                    "snap_key": snap_key,
                    "token_metrics": compute_token_metrics(seg.concat).as_dict(),
                    "translation_key": translation_key,
                    "stream": seg.stream,
                },
                prev=prev_morphon,
                store=self.register_ports,
                bond_with_prev=self.register_ports and prev_morphon is not None,
                snap_labeler=None,
            )
            morphon.e8_coordinates = tuple(float(c) for c in canonical["e8_coords"])
            if bond_m is not None:
                stats.bond_morphons += 1
            prev_morphon = morphon
            payload = IndexEntryPayload(
                concat=seg.concat,
                morphon_id=morphon.id,
                snap_key=snap_key,
                e8_coords=tuple(float(c) for c in canonical["e8_coords"]),
                digital_root=int(canonical["digital_root"]),
                lane=str(canonical["lane"]),
                cache_key=key_exact(seg.concat),
                level=1,
                case_mode=CaseMode.LOWER.value,
                language="any",
                warmstart_outcome=hit.outcome.value,
            )
            store.upsert(
                payload,
                bond_level=1,
                case_mode=CaseMode.LOWER.value,
                language="any",
                stream=seg.stream,
            )
            if self.register_ports and cache is not None:
                publish_entry(cache, payload, CaseMode.LOWER)
            stats.new_bonds += 1

    def _ingest_chunk(
        self,
        chunk: str,
        *,
        source_doc: str,
        source_span: str,
        shell: MorphonShell,
        store: TokenIndexStore,
        meaning: AddressMeaningStore,
        snap: SNAPLabeler,
        lookup: WarmStartLookup,
        stats: IngestStats,
        translation_key: str = "",
        links: Optional[TranslationLinkStore] = None,
        geometry: Optional[TokenGeometryStore] = None,
    ) -> None:
        segments = shell.slice_ribbon(chunk)
        label_result = snap.label(chunk, key=source_doc, context={"text": chunk})
        labels = sorted(label_result.all_labels)
        if not labels:
            labels = [self._heading_label(chunk) or Path(source_doc).stem]
            stats.new_labels += 1

        cache = get_cache_provider() if _has("cache") else None
        chunk_anchor = re.sub(r"\s+", "", chunk)[:8].ljust(8, "a")
        chunk_canonical = NLAECNFChain.full_chain(chunk_anchor)
        prev_morphon: Optional[Morphon] = None

        for seg in segments:
            if len(seg) < 4:
                continue
            concat = seg if len(seg) == 8 else seg[:8].ljust(8, "a")
            if len(concat) != 8:
                continue

            bond = QuadBond(quad_left=concat[:4], quad_right=concat[4:], level=1)
            hit = lookup.probe(bond, CaseMode.LOWER)

            canonical = NLAECNFChain.full_chain(concat)
            snap_key = str(canonical["snap_key"])

            if links is not None and translation_key:
                links.upsert(
                    translation_key=translation_key,
                    stream=self.stream,
                    concat=concat,
                    snap_key=snap_key,
                    source_doc=source_doc,
                    source_span=source_span,
                )
            if geometry is not None:
                self._upsert_geometry(geometry, concat, self.stream, translation_key)

            if hit.outcome is WarmStartOutcome.EXACT:
                stats.cache_hits += 1
                stats.bond_skips += 1
            elif not store.by_concat(concat, stream=self.stream):
                token_metrics = compute_token_metrics(concat)
                morphon, bond_m = forge_ingest_morphon(
                    {
                        "concat": concat,
                        "snap_key": snap_key,
                        "token_metrics": token_metrics.as_dict(),
                        "source_doc": source_doc,
                        "source_span": source_span,
                    },
                    prev=prev_morphon,
                    store=self.register_ports,
                    bond_with_prev=self.register_ports and prev_morphon is not None,
                    snap_labeler=snap if self.register_ports else None,
                    label_text=chunk,
                )
                morphon.e8_coordinates = tuple(float(c) for c in canonical["e8_coords"])
                morphon.dr_channel = int(canonical["digital_root"])
                if bond_m is not None:
                    stats.bond_morphons += 1
                prev_morphon = morphon
                payload = IndexEntryPayload(
                    concat=concat,
                    morphon_id=morphon.id,
                    snap_key=snap_key,
                    e8_coords=tuple(float(c) for c in canonical["e8_coords"]),
                    digital_root=int(canonical["digital_root"]),
                    lane=str(canonical["lane"]),
                    cache_key=key_exact(concat),
                    level=1,
                    case_mode=CaseMode.LOWER.value,
                    language="any",
                    warmstart_outcome=WarmStartOutcome.COLD.value,
                )
                store.upsert(
                    payload,
                    bond_level=1,
                    case_mode=CaseMode.LOWER.value,
                    language="any",
                    stream=self.stream,
                )
                if self.register_ports and cache is not None:
                    publish_entry(cache, payload, CaseMode.LOWER)
                if self.register_ports:
                    store.publish(payload, CaseMode.LOWER.value, morphon)
                stats.new_bonds += 1
            else:
                stats.bond_skips += 1

        if not label_result.all_labels and labels:
            snap.register_dynamic_label(str(chunk_canonical["snap_key"]), labels[0])

        receipt_hash = None
        if self.register_ports and has_provider("receipt"):
            try:
                rcpt = get_receipt_provider().mint(
                    receipt_type="PROCESS",
                    atom_id="corpus_ingest",
                    operation="transform.ingest",
                    payload={"source_doc": source_doc, "chunk": source_span},
                )
                receipt_hash = getattr(rcpt, "hash", None) or str(rcpt)
            except Exception:
                pass

        for label in labels[:8]:
            meaning.upsert(
                snap_key=str(chunk_canonical["snap_key"]),
                lane=str(chunk_canonical["lane"]),
                digital_root=int(chunk_canonical["digital_root"]),
                label=label,
                label_source="ingest" if label in label_result.all_labels else "inferred",
                source_doc=source_doc,
                source_span=source_span,
                receipt_hash=receipt_hash,
            )
            stats.new_meanings += 1

    @staticmethod
    def _iter_files(root: Path, max_files: Optional[int] = None) -> Iterable[Path]:
        """Yield text files under *root* without materializing a full tree walk."""
        if root.is_file():
            if root.suffix.lower() in TEXT_EXTENSIONS:
                yield root
            return
        seen = 0
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            yield path
            seen += 1
            if max_files is not None and seen >= max_files:
                return

    def _chunk_text(self, text: str) -> list[str]:
        text = re.sub(r"\s+", " ", text.strip())
        if not text:
            return []
        size = self.chunk_size
        return [text[i : i + size] for i in range(0, len(text), size)]

    @staticmethod
    def _heading_label(chunk: str) -> Optional[str]:
        for line in chunk.splitlines()[:5]:
            line = line.strip()
            if line.startswith("#"):
                return re.sub(r"^#+\s*", "", line).strip()[:64]
        m = re.search(r"^([A-Z][A-Za-z0-9 _-]{2,48})", chunk)
        return m.group(1).strip() if m else None


@dataclass
class MultistreamIngestPolicy:
    """EN-first multistream policy: shared ``translation_key`` per chunk."""

    streams: tuple[str, ...] = ("en", "native")
    en_first: bool = True


def ingest_multistream(
    root: Path,
    *,
    db: str | Path | None = None,
    lib_paths: Sequence[str | Path] = (),
    policy: Optional[MultistreamIngestPolicy] = None,
    max_files: Optional[int] = None,
    register_ports: bool = False,
    translate_hub: Optional[TranslateHub] = None,
) -> dict[str, IngestStats]:
    """Ingest sidecar streams with EN-first link policy.

    Each stream pass uses the same ``{stem}:chunk:{id}`` translation keys so
    ``TranslationLinkStore`` rows align across ``en`` and ``native`` (etc.).
    """
    policy = policy or MultistreamIngestPolicy()
    db_path = Path(db) if db is not None else runtime_path("data", "token_index.sqlite")
    order = list(policy.streams)
    if policy.en_first and "en" in order:
        order = ["en"] + [s for s in order if s != "en"]
    stats_by_stream: dict[str, IngestStats] = {}
    for stream in order:
        ingester = CorpusIngester(
            stream=stream,
            max_files=max_files,
            register_ports=register_ports,
        )
        stats_by_stream[stream] = ingester.ingest_path(
            Path(root),
            lib_paths=lib_paths,
            db=db_path,
            translate_hub=translate_hub if stream == "en" else NoOpHub(),
        )
    return stats_by_stream


__all__ = [
    "CorpusIngester",
    "IngestStats",
    "DEFAULT_CHUNK_SIZE",
    "MultistreamIngestPolicy",
    "ingest_multistream",
]
