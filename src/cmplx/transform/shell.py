"""
MorphonShell — constraint engine for shell-valid token emit.

Every emitted token must pass bond shape, language filter, and optional
NSL gate checks before admission. Long ribbons are sliced via TarPit
walls + MirrorOperator (max 3 reflections) with midpoint fallback.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from cmplx.morphon import Morphon
from cmplx.primitives.core import NLAECNFChain
from cmplx.symbolic.tarpit import (
    DimensionalExtent,
    ErrorClass,
    Grain,
    MirrorOperator,
    WallEmitter,
)

from .bridge import get_conservation_provider, has_provider
from .shell_config import ShellConfig
from .token_index.bonds import QUAD_LEN, QuadBond
from .token_index.language import LanguageFilter, any_filter, get_filter
from .token_index.store import TokenIndexStore
from .token_index.template_frame import TemplateFrame

logger = logging.getLogger(__name__)

MAX_MIRROR_REFLECTIONS = 3


@dataclass
class AdmitResult:
    admitted: bool
    token: str
    reason: str = ""
    snap_key: str = ""
    lane: str = ""
    digital_root: int = 0
    segments: list[str] = field(default_factory=list)


class MorphonShell:
    """Single entry point for shell-valid token operations."""

    def __init__(
        self,
        config: ShellConfig,
        store: TokenIndexStore,
        meaning: Optional[object] = None,
        language_filters: Optional[dict[str, LanguageFilter]] = None,
    ) -> None:
        self.config = config
        self.store = store
        self.meaning = meaning
        self._filters = language_filters or {"any": any_filter()}

    # ── Ribbon slicing ────────────────────────────────────────────────

    def slice_ribbon(self, text: str) -> list[str]:
        """Split text into segments of at most ``max_arity`` characters.

        Long tokens trigger TarPit capacity walls; up to three mirror
        reflections attempt an alternate split before midpoint fallback.
        """
        segments: list[str] = []
        for raw in text.split():
            word = raw.strip()
            if not word:
                continue
            segments.extend(self._slice_word(word))
        return segments

    def _slice_word(self, word: str) -> list[str]:
        max_len = self.config.max_arity
        if len(word) <= max_len:
            return [word]

        emitter = WallEmitter()
        mirror = MirrorOperator()
        out: list[str] = []
        chunk = word
        reflections = 0

        while len(chunk) > max_len:
            grain = Grain(
                value=len(chunk),
                extent=DimensionalExtent(
                    vector=tuple(float(min(len(chunk), 9)) for _ in range(8))
                ),
            )
            err = emitter.emit_error(
                error_class=ErrorClass.CAPACITY_EXCEEDED,
                reproducer_grains=[grain],
                violated_invariants=[f"max_arity<={max_len}"],
                context={"token": chunk, "length": len(chunk)},
            )
            if reflections < MAX_MIRROR_REFLECTIONS and err.mirror_candidate:
                state = mirror.apply_mirror(err, [grain])
                if state is not None and state.is_valid_bridge():
                    chunk = chunk[::-1]
                    reflections += 1
                    continue

            mid = max(1, len(chunk) // 2)
            left, chunk = chunk[:mid], chunk[mid:]
            if len(left) <= max_len:
                out.append(left)
            else:
                out.extend(self._slice_word(left))
            reflections = 0

        if chunk:
            out.append(chunk)
        return out

    # ── Admission ─────────────────────────────────────────────────────

    def admit(self, token: str, *, lang: str = "any") -> AdmitResult:
        """Check bond shape, language filter, substrate row, optional NSL."""
        sep = self.config.bond_separator
        segments = self.slice_ribbon(token) if sep not in token else [token]

        if sep in token:
            parts = token.split(sep)
            if len(parts) != 2 or any(len(p) != QUAD_LEN * 2 for p in parts):
                return AdmitResult(
                    False, token, reason="invalid_bond_shape", segments=segments
                )
            concat = parts[0] + parts[1]
        elif len(token) == QUAD_LEN * 2:
            concat = token
        else:
            return AdmitResult(
                False, token, reason="invalid_length", segments=segments
            )

        bond = QuadBond(
            quad_left=concat[:QUAD_LEN],
            quad_right=concat[QUAD_LEN:],
            level=1,
        )
        lang_filter = self._filters.get(lang) or get_filter(lang)
        if lang != "any" and not lang_filter.accept(bond):
            return AdmitResult(
                False, token, reason="language_rejected", segments=segments
            )

        rows = self.store.by_concat(concat, language=None if lang == "any" else lang)
        if not rows:
            rows = self.store.by_concat(concat)

        if rows:
            row = rows[0]
            return AdmitResult(
                True,
                token,
                snap_key=str(row["snap_key"]),
                lane=str(row["lane"]),
                digital_root=int(row["digital_root"]),
                segments=segments,
            )

        if not self._nsl_allows_forge(concat):
            return AdmitResult(
                False, token, reason="nsl_rejected", segments=segments
            )

        try:
            canonical = NLAECNFChain.full_chain(concat)
            Morphon.forge(
                payload={"concat": concat, "snap_key": canonical["snap_key"]}
            )
        except Exception as exc:
            logger.debug("forge failed for %s: %s", concat, exc)
            return AdmitResult(
                False, token, reason="forge_failed", segments=segments
            )

        return AdmitResult(
            True,
            token,
            reason="forged",
            snap_key=str(canonical["snap_key"]),
            lane=str(canonical["lane"]),
            digital_root=int(canonical["digital_root"]),
            segments=segments,
        )

    def _nsl_allows_forge(self, concat: str) -> bool:
        if not has_provider("conservation"):
            return True
        try:
            nsl = get_conservation_provider()
            sectors = nsl.compute_sectors({"concat": concat, "operation": "shell.admit"})
            decision = nsl.gate(sectors, mode=self.config.gate_mode, budget=0.0)
            return bool(getattr(decision, "accepted", True))
        except Exception as exc:
            logger.debug("nsl gate skipped: %s", exc)
            return True

    # ── Completion ────────────────────────────────────────────────────

    def complete(self, partial: str, *, max_candidates: int = 64) -> list[str]:
        """Return substrate-admitted completions for a partial window."""
        partial = partial.lower()
        with TemplateFrame(self.store.db_path) as frame:
            if len(partial) == QUAD_LEN:
                adm = frame.admit_set_by_left(
                    partial, language=self._lang_for_frame()
                )
                return sorted(adm.distinct_completions)[:max_candidates]

            if len(partial) < QUAD_LEN * 2:
                pattern = partial + "?" * (QUAD_LEN * 2 - len(partial))
            elif len(partial) == QUAD_LEN * 2:
                pattern = partial
            else:
                pattern = partial[: QUAD_LEN * 2]

            if len(pattern) != QUAD_LEN * 2:
                return []

            adm = frame.admit_set_by_partial(
                pattern, language=self._lang_for_frame()
            )
            if adm.distinct_completions:
                return sorted(adm.distinct_completions)[:max_candidates]
            return sorted(adm.matching_concats)[:max_candidates]

    def _lang_for_frame(self) -> Optional[str]:
        lang = self.config.language
        return None if lang == "any" else lang


__all__ = ["AdmitResult", "MorphonShell", "MAX_MIRROR_REFLECTIONS"]
