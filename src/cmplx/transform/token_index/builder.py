"""
TokenIndexBuilder — the iterative builder.

Construction order is part of the spec, not an implementation detail.
The substrate-first claim is that every new entry inherits structure
from prior entries via the SpeedLight cache. To make that true, the
builder walks the combinatorial space in *dependency order*:

    for level in (1, 2, 3):                           # level k depends on k-1
      for case_mode in (LOWER, then derived modes):   # derived depends on LOWER
        for language in ("any", then language filters):  # filtered depends on any
          for bond in enumerate(level, alphabet):
              probe cache → defined / vague / cold
              forge morphon (with parent from probe if vague)
              upsert SQLite row + publish to memory/cache/receipt

The probe is the **only** thing standing between a new entry and a
full forge. When the substrate is healthy, levels 2 and 3 are mostly
predecessor hits and case-base hits; cold forges are bounded by
`|alphabet|` per level. On re-run, every probe is an EXACT hit and
nothing is recomputed.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from cmplx.morphon import Morphon
from cmplx.primitives.core import NLAECNFChain
from cmplx.runtime_paths import runtime_path

from ..bridge import (
    ensure_bootstrapped,
    get_cache_provider,
    has_provider,
)
from ..config import TransformerConfig
from .bonds import (
    DEFAULT_ALPHABET,
    DEFAULT_BASE_CHAR,
    QuadBond,
    enumerate_bonds,
)
from .case import CaseMode, DEFAULT_CASE_MODES, apply_case
from .language import LanguageFilter, any_filter, english_filter
from .store import TokenIndexStore
from .warmstart import (
    IndexEntryPayload,
    NAMESPACE,
    WarmStartHit,
    WarmStartLookup,
    WarmStartOutcome,
    WarmStartStats,
    key_exact,
)

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# Build config
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class TokenIndexBuildConfig:
    levels: tuple[int, ...] = (1, 2, 3)
    alphabet: Sequence[str] = DEFAULT_ALPHABET
    base_char: str = DEFAULT_BASE_CHAR
    case_modes: Sequence[CaseMode] = field(default_factory=lambda: list(DEFAULT_CASE_MODES))
    languages: Sequence[LanguageFilter] = field(
        default_factory=lambda: [any_filter(), english_filter()]
    )
    db_path: str = field(
        default_factory=lambda: str(runtime_path("data", "token_index.sqlite"))
    )
    stream: str = "en"
    lib_paths: tuple[str, ...] = ()
    transformer_config: Optional[TransformerConfig] = None
    register_ports: bool = True
    progress_every: int = 1000
    max_entries: Optional[int] = None  # safety cap for smoke runs


@dataclass
class BuildResult:
    total_seen: int = 0
    total_stored: int = 0
    elapsed_seconds: float = 0.0
    warmstart_stats: WarmStartStats = field(default_factory=WarmStartStats)
    per_level: dict[int, WarmStartStats] = field(default_factory=dict)
    per_case: dict[str, WarmStartStats] = field(default_factory=dict)
    per_language: dict[str, WarmStartStats] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "total_seen": self.total_seen,
            "total_stored": self.total_stored,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "warmstart": self.warmstart_stats.as_dict(),
            "per_level": {k: v.as_dict() for k, v in self.per_level.items()},
            "per_case": {k: v.as_dict() for k, v in self.per_case.items()},
            "per_language": {k: v.as_dict() for k, v in self.per_language.items()},
        }


# ────────────────────────────────────────────────────────────────────────────
# Builder
# ────────────────────────────────────────────────────────────────────────────

class TokenIndexBuilder:
    """Substrate-first token index builder.

    Usage:
        builder = TokenIndexBuilder(TokenIndexBuildConfig(levels=(1,2,3)))
        result = builder.build()
        print(result.as_dict())
    """

    def __init__(self, config: Optional[TokenIndexBuildConfig] = None) -> None:
        self.config = config or TokenIndexBuildConfig()
        if self.config.lib_paths:
            from ..rule_lib import filters_from_paths

            merged = filters_from_paths(*self.config.lib_paths)
            names = {lang.name for lang in self.config.languages}
            extra = [f for n, f in merged.items() if n not in names]
            if extra:
                self.config.languages = list(self.config.languages) + extra
        if self.config.register_ports:
            ensure_bootstrapped()
        # The transformer is constructed once so the bootstrap is paid
        # only here; for each entry we only touch the tokenizer and
        # canonicalization path (not the full layer stack — those are
        # for runtime inference, not index construction).
        from ..transformer import GeometricTransformer

        self.transformer = GeometricTransformer(
            self.config.transformer_config or TransformerConfig(num_layers=1)
        )
        cache = get_cache_provider() if has_provider("cache") else None
        self.lookup = WarmStartLookup(cache)
        self.store = TokenIndexStore(self.config.db_path)

    # ── Entry point ─────────────────────────────────────────────────────

    def build(self) -> BuildResult:
        cfg = self.config
        result = BuildResult()
        start = time.time()
        run_id = self.store.start_run(
            levels=cfg.levels,
            alphabet=cfg.alphabet,
            languages=[lang.name for lang in cfg.languages],
            case_modes=[c.value for c in cfg.case_modes],
        )

        # Ensure LOWER is processed first so case-base hits work.
        ordered_cases = self._order_case_modes(cfg.case_modes)
        ordered_languages = self._order_languages(cfg.languages)

        for level in cfg.levels:
            level_stats = result.per_level.setdefault(level, WarmStartStats())
            for case_mode in ordered_cases:
                case_stats = result.per_case.setdefault(case_mode.value, WarmStartStats())
                for lang_filter in ordered_languages:
                    lang_stats = result.per_language.setdefault(
                        lang_filter.name, WarmStartStats()
                    )
                    self._process_slice(
                        level=level,
                        case_mode=case_mode,
                        lang_filter=lang_filter,
                        result=result,
                        bucket_stats=(level_stats, case_stats, lang_stats),
                    )
                    if (
                        cfg.max_entries is not None
                        and result.total_stored >= cfg.max_entries
                    ):
                        break
                if (
                    cfg.max_entries is not None
                    and result.total_stored >= cfg.max_entries
                ):
                    break
            if cfg.max_entries is not None and result.total_stored >= cfg.max_entries:
                break

        result.elapsed_seconds = time.time() - start
        self.store.finish_run(
            total_seen=result.total_seen,
            total_stored=result.total_stored,
            stats=result.as_dict(),
        )
        self.store.mint_summary_receipt(
            total_stored=result.total_stored,
            levels=cfg.levels,
            languages=[lang.name for lang in cfg.languages],
            stats=result.warmstart_stats.as_dict(),
        )
        logger.info(
            "token index build complete: %d stored, %d seen, %.2fs",
            result.total_stored,
            result.total_seen,
            result.elapsed_seconds,
        )
        return result

    # ── Slice processing ────────────────────────────────────────────────

    def _process_slice(
        self,
        *,
        level: int,
        case_mode: CaseMode,
        lang_filter: LanguageFilter,
        result: BuildResult,
        bucket_stats: tuple[WarmStartStats, WarmStartStats, WarmStartStats],
    ) -> None:
        cfg = self.config
        level_stats, case_stats, lang_stats = bucket_stats

        for base_bond in enumerate_bonds(
            level,
            alphabet=cfg.alphabet,
            base_char=cfg.base_char,
            include_base=False,
        ):
            cased_bond = apply_case(base_bond, case_mode)
            if not lang_filter.accept(cased_bond):
                continue
            result.total_seen += 1

            hit = self.lookup.probe(cased_bond, case_mode)
            payload, morphon, outcome = self._materialize(
                cased_bond, case_mode, lang_filter, hit
            )

            result.warmstart_stats.record(outcome)
            level_stats.record(outcome)
            case_stats.record(outcome)
            lang_stats.record(outcome)

            self.store.upsert(
                payload,
                bond_level=level,
                case_mode=case_mode.value,
                language=lang_filter.name,
                stream=cfg.stream,
            )
            self.store.publish(payload, case_mode.value, morphon)
            result.total_stored += 1

            if (
                cfg.progress_every
                and result.total_stored % cfg.progress_every == 0
            ):
                logger.info(
                    "  built %d (L%d %s lang=%s) | exact=%d vague=%d cold=%d",
                    result.total_stored,
                    level,
                    case_mode.value,
                    lang_filter.name,
                    result.warmstart_stats.exact,
                    result.warmstart_stats.vague,
                    result.warmstart_stats.cold,
                )
            if cfg.max_entries is not None and result.total_stored >= cfg.max_entries:
                return

    # ── Materialization ─────────────────────────────────────────────────

    def _materialize(
        self,
        bond: QuadBond,
        case_mode: CaseMode,
        lang_filter: LanguageFilter,
        hit: WarmStartHit,
    ) -> tuple[IndexEntryPayload, Morphon, WarmStartOutcome]:
        """Build (or reuse) the morphonic record for one entry.

        Three branches:
          - EXACT: reuse the cached payload verbatim. No forge.
          - vague (CASE_BASE / PREDECESSOR / NEIGHBOR): inherit canonical
            info; forge a fresh morphon with parent=hit.payload.morphon_id.
          - COLD: full canonicalize + forge.
        """
        concat = bond.concat
        cache_key = key_exact(concat)

        if hit.outcome is WarmStartOutcome.EXACT and hit.payload is not None:
            # Defined: rebuild the morphon record from the cached
            # payload so downstream `publish` still has a Morphon
            # object to hand to memory.store(...).
            morphon = Morphon.forge(
                payload={
                    "concat": concat,
                    "snap_key": hit.payload.snap_key,
                    "case_mode": case_mode.value,
                    "language": lang_filter.name,
                    "reused_from": hit.payload.morphon_id,
                },
                parent=hit.payload.morphon_id,
            )
            morphon.e8_coordinates = tuple(hit.payload.e8_coords)
            morphon.dr_channel = hit.payload.digital_root
            payload = IndexEntryPayload(
                concat=concat,
                morphon_id=morphon.id,
                snap_key=hit.payload.snap_key,
                e8_coords=tuple(hit.payload.e8_coords),
                digital_root=hit.payload.digital_root,
                lane=hit.payload.lane,
                cache_key=cache_key,
                level=bond.level,
                case_mode=case_mode.value,
                language=lang_filter.name,
                parent_morphon_id=hit.payload.morphon_id,
                warmstart_outcome=WarmStartOutcome.EXACT.value,
            )
            return payload, morphon, WarmStartOutcome.EXACT

        if hit.outcome.is_vague and hit.payload is not None:
            # Vague: inherit canonical info from the prior, mint a new
            # morphon as a child of it. The case-shift / inner-ring
            # add does not change the snap_key in this MVP (the snap
            # is computed on the lowercase ring structure, which is
            # invariant under case shifts; for predecessor hits the
            # snap_key is a close-enough warm start until we recompute
            # at refinement time).
            morphon = Morphon.forge(
                payload={
                    "concat": concat,
                    "snap_key": hit.payload.snap_key,
                    "case_mode": case_mode.value,
                    "language": lang_filter.name,
                    "warmstart_from": hit.payload.concat,
                    "warmstart_outcome": hit.outcome.value,
                },
                parent=hit.payload.morphon_id,
            )
            morphon.e8_coordinates = tuple(hit.payload.e8_coords)
            morphon.dr_channel = hit.payload.digital_root
            payload = IndexEntryPayload(
                concat=concat,
                morphon_id=morphon.id,
                snap_key=hit.payload.snap_key,
                e8_coords=tuple(hit.payload.e8_coords),
                digital_root=hit.payload.digital_root,
                lane=hit.payload.lane,
                cache_key=cache_key,
                level=bond.level,
                case_mode=case_mode.value,
                language=lang_filter.name,
                parent_morphon_id=hit.payload.morphon_id,
                warmstart_outcome=hit.outcome.value,
            )
            return payload, morphon, hit.outcome

        # COLD: full canonicalize.
        canonical = NLAECNFChain.full_chain(concat)
        e8_coords = tuple(float(c) for c in canonical["e8_coords"])
        morphon = Morphon.forge(
            payload={
                "concat": concat,
                "snap_key": canonical["snap_key"],
                "case_mode": case_mode.value,
                "language": lang_filter.name,
                "warmstart_outcome": WarmStartOutcome.COLD.value,
            }
        )
        morphon.e8_coordinates = e8_coords
        morphon.dr_channel = int(canonical["digital_root"])

        # After canonicalizing, check whether a NEIGHBOR existed — this
        # retroactively "warms" the entry for downstream lookups via
        # the neighbor bucket even though we had to pay the forge cost.
        neighbor_hit = self.lookup.probe_neighbor(
            int(canonical["digital_root"]),
            str(canonical["lane"]),
        )
        outcome = WarmStartOutcome.COLD
        parent_id = None
        if neighbor_hit.outcome is WarmStartOutcome.NEIGHBOR and neighbor_hit.payload is not None:
            outcome = WarmStartOutcome.NEIGHBOR
            parent_id = neighbor_hit.payload.morphon_id

        payload = IndexEntryPayload(
            concat=concat,
            morphon_id=morphon.id,
            snap_key=canonical["snap_key"],
            e8_coords=e8_coords,
            digital_root=int(canonical["digital_root"]),
            lane=str(canonical["lane"]),
            cache_key=cache_key,
            level=bond.level,
            case_mode=case_mode.value,
            language=lang_filter.name,
            parent_morphon_id=parent_id,
            warmstart_outcome=outcome.value,
        )
        return payload, morphon, outcome

    # ── Ordering helpers ────────────────────────────────────────────────

    @staticmethod
    def _order_case_modes(modes: Sequence[CaseMode]) -> list[CaseMode]:
        """LOWER first so derived case modes can hit it as case_base."""
        ordered = [CaseMode.LOWER] if CaseMode.LOWER in modes else []
        ordered.extend(m for m in modes if m is not CaseMode.LOWER)
        return ordered

    @staticmethod
    def _order_languages(filters: Sequence[LanguageFilter]) -> list[LanguageFilter]:
        """`any` first so language-filtered entries hit the unfiltered."""
        ordered = [f for f in filters if f.name == "any"]
        ordered.extend(f for f in filters if f.name != "any")
        return ordered


__all__ = [
    "TokenIndexBuildConfig",
    "BuildResult",
    "TokenIndexBuilder",
]
