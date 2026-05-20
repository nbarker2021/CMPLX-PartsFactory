"""
MorphonicTokenizer — Slot 48 embed layer.

Composes three deterministic stages:

  1. `DeterministicTokenizer` (from the eversion network) for stable
     integer token ids derived from a SHA-256 chain over the input.
  2. `GeoTokenizer` (SpeedLight service) for an E8-quantised embedding
     and prototype-based equivalence learning (optional).
  3. `Morphon.forge` + `NLAECNFChain.full_chain` for the canonical
     SNAP key, E8 coordinates, digital root, and lane.

The result is a `TokenizedRibbon` carrying both the token-id sequence
and the initial `(seq_length, hidden_dim)` HiddenState tensor that
seeds the transformer stack.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

import numpy as np

from cmplx.morphon import Morphon
from cmplx.primitives.core import NLAECNFChain
from cmplx.engine.eversion.network import DeterministicTokenizer

from .bridge import (
    has_provider,
    get_atlas_provider,
    get_constraints_provider,
    get_geometry_provider,
    get_symbolic_provider,
)
from .config import TokenizerConfig
from .types import TokenizedRibbon

logger = logging.getLogger(__name__)

# Optional GeoTokenizer — pull lazily so a missing services tree does
# not block the substrate.
try:
    from cmplx.services.speedlight_engine_service import (
        GeoTokenizer as _ServiceGeoTokenizer,
    )
    _HAS_GEO_TOKENIZER = True
except Exception:  # pragma: no cover - services tree optional
    _ServiceGeoTokenizer = None  # type: ignore[assignment]
    _HAS_GEO_TOKENIZER = False


def _content_to_canonical_str(content: Any) -> str:
    """Stable JSON canonicalisation; bytes become hex."""
    if isinstance(content, bytes):
        return content.hex()
    if isinstance(content, str):
        return content
    return json.dumps(content, sort_keys=True, separators=(",", ":"), default=str)


def _tile_embedding(embedding: np.ndarray, seq_length: int, hidden_dim: int) -> np.ndarray:
    """Tile / pad a 1-D embedding into a (seq_length, hidden_dim) tensor.

    Each row gets a deterministic positional shift so the rows are not
    all identical — the shift comes from row index modulo embedding
    length, giving a content-stable seed for every position.
    """
    flat = np.asarray(embedding, dtype=np.float64).reshape(-1)
    if flat.size == 0:
        return np.zeros((seq_length, hidden_dim), dtype=np.float64)
    out = np.zeros((seq_length, hidden_dim), dtype=np.float64)
    for row in range(seq_length):
        shift = row % flat.size
        rolled = np.roll(flat, shift)
        if rolled.size >= hidden_dim:
            out[row] = rolled[:hidden_dim]
        else:
            reps = (hidden_dim + rolled.size - 1) // rolled.size
            out[row] = np.tile(rolled, reps)[:hidden_dim]
    return out


class MorphonicTokenizer:
    """Settings-driven embed layer for the Morphonic Transformer."""

    def __init__(
        self,
        config: Optional[TokenizerConfig] = None,
        *,
        hidden_dim: int = 24,
        seq_length: Optional[int] = None,
    ) -> None:
        self.config = config or TokenizerConfig()
        self.hidden_dim = int(hidden_dim)
        self.seq_length = int(seq_length if seq_length is not None else self.config.seq_length)
        self._deterministic = DeterministicTokenizer(
            vocab_size=self.config.vocab_size,
            seq_length=self.seq_length,
        )
        self._geo: Optional[Any] = None
        if self.config.use_geo and _HAS_GEO_TOKENIZER:
            self._geo = _ServiceGeoTokenizer(
                similarity_threshold=self.config.similarity_threshold
            )

    # ── Public API ──────────────────────────────────────────────────────

    def tokenize(
        self,
        content: Any,
        *,
        context_morphon: Optional[Morphon] = None,
    ) -> TokenizedRibbon:
        """Run the full embed stack and return a TokenizedRibbon."""
        canonical_str = _content_to_canonical_str(content)
        content_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()[:16]

        token_ids = self._deterministic.tokenize(content)
        canonical_info = NLAECNFChain.full_chain(content)
        e8_coords = tuple(float(x) for x in canonical_info["e8_coords"])

        geo_state: dict = {}
        if self._geo is not None:
            try:
                geo_state = dict(self._geo.encode(canonical_str))
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("GeoTokenizer.encode failed: %s", exc)
                geo_state = {}

        payload = {
            "content_hash": content_hash,
            "snap_key": canonical_info["snap_key"],
            "lane": canonical_info["lane"],
            "digital_root": canonical_info["digital_root"],
        }
        morphon = Morphon.forge(
            payload=payload,
            parent=context_morphon.id if context_morphon is not None else None,
        )
        # Cache the geometry projections we already computed.
        morphon.e8_coordinates = e8_coords
        morphon.dr_channel = int(canonical_info["digital_root"])

        # Optional admission gates — never fatal in the embed layer.
        if has_provider("constraints"):
            try:
                admitted, reason = get_constraints_provider().admit(morphon)
                if not admitted:
                    logger.debug(
                        "constraints.admit refused morphon %s: %s", morphon.id, reason
                    )
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("constraints.admit raised: %s", exc)

        if has_provider("atlas"):
            try:
                get_atlas_provider().admit_to_deployment(morphon)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("atlas.admit_to_deployment raised: %s", exc)

        if has_provider("geometry"):
            try:
                geom = get_geometry_provider()
                e8 = geom.e8_coordinates(morphon)
                if e8 is not None:
                    morphon.e8_coordinates = tuple(float(x) for x in e8)
                leech = geom.leech_point(morphon)
                if leech is not None:
                    morphon.leech_point = str(leech)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("geometry provider failed: %s", exc)

        etp_program: Optional[str] = None
        if self.config.encode_etp or self.config.ribbon_mode in {"etp", "mixed"}:
            if has_provider("symbolic"):
                try:
                    etp_program = get_symbolic_provider().encode_to_etp(morphon)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.debug("symbolic.encode_to_etp raised: %s", exc)

        tensor = self._build_tensor(
            token_ids=token_ids,
            e8_coords=e8_coords,
            geo_state=geo_state,
        )

        return TokenizedRibbon(
            raw_content=content,
            token_ids=token_ids,
            content_hash=content_hash,
            tensor=tensor,
            morphon=morphon,
            geo_state=geo_state,
            canonical_info=canonical_info,
            etp_program=etp_program,
        )

    # ── Internals ────────────────────────────────────────────────────────

    def _build_tensor(
        self,
        *,
        token_ids: np.ndarray,
        e8_coords: tuple[float, ...],
        geo_state: dict,
    ) -> np.ndarray:
        """Build the initial (seq_length, hidden_dim) seed tensor.

        Strategy: tile the E8 coordinates (always 8-D) across the
        hidden_dim, then add a normalised token-id positional shift per
        row. When a GeoTokenizer embedding is available, it is mixed
        in additively so the seed reflects both the canonical E8
        projection and the geometric prototype.
        """
        seed = np.array(e8_coords, dtype=np.float64)
        tensor = _tile_embedding(seed, self.seq_length, self.hidden_dim)

        # Add a token-id positional channel: small magnitude so it does
        # not dominate the canonical seed.
        if token_ids.size > 0:
            denom = float(max(self.config.vocab_size, 1))
            for row in range(self.seq_length):
                token = float(token_ids[row % token_ids.size])
                tensor[row, row % self.hidden_dim] += (token / denom) * 1e-2

        # Mix in GeoTokenizer embedding when present.
        geo_emb = geo_state.get("embedding") if isinstance(geo_state, dict) else None
        if geo_emb:
            geo_vec = np.array(geo_emb, dtype=np.float64)
            geo_tiled = _tile_embedding(geo_vec, self.seq_length, self.hidden_dim)
            tensor = tensor + 0.5 * geo_tiled

        return tensor


__all__ = ["MorphonicTokenizer"]
