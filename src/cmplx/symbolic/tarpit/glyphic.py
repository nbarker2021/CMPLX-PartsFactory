"""
glyphic_tarpit — semantic glyph layer (stdlib, no numpy).

Merged from preview `glyph_tarpit/` into the slot-18 spine. Corpus alias
`glyph_tarpit` → canonical name **glyphic_tarpit**.
"""
from __future__ import annotations

import hashlib
from typing import Any

# Subset of Universal Glyph Dictionary (list e8 coords for stdlib use)
GLYPH_LEXICON: dict[str, dict[str, Any]] = {
    "∅": {"id": "empty", "dr": 0, "e8": [0.0] * 8},
    "🧠": {"id": "brain", "dr": 7, "e8": [1.0, 0, 0, 0, 0, 0, 0, 0]},
    "💡": {"id": "insight", "dr": 1, "e8": [0, 1.0, 0, 0, 0, 0, 0, 0]},
    "📥": {"id": "put", "dr": 1, "e8": [0, 0, 1.0, 0, 0, 0, 0, 0]},
    "📤": {"id": "get", "dr": 2, "e8": [0, 0, 0, 1.0, 0, 0, 0, 0]},
    "💎": {"id": "snap", "dr": 4, "e8": [1, 1, 1, 1, 0, 0, 0, 0]},
    "✓": {"id": "validate", "dr": 1, "e8": [1, 0, 0, 0, 1, 0, 0, 0]},
    "👥": {"id": "witness", "dr": 3, "e8": [0, 0, 0, 0, 0, 1.0, 0, 0]},
    "⚖️": {"id": "balance", "dr": 3, "e8": [0, 0, 0, 0, 0, 0, 1.0, 0]},
    "🧾": {"id": "receipt", "dr": 1, "e8": [0, 0, 0, 0, 0, 0, 0, 1.0]},
    "🌉": {"id": "bridge", "dr": 2, "e8": [0, 0, 0, 0, 1, 1, 0, 0]},
}

_ETP_ALPHABET = "}<>+01"


def _normalize_e8(coords: list[float]) -> list[float]:
    n = sum(x * x for x in coords) ** 0.5
    if n <= 0:
        return [0.0] * 8
    return [x / n for x in coords]


def glyph_meta(glyph: str) -> dict[str, Any]:
    """Metadata for a glyph symbol (lexicon or hashed unknown)."""
    if glyph in GLYPH_LEXICON:
        meta = GLYPH_LEXICON[glyph]
        return {
            "glyph": glyph,
            "glyph_id": meta["id"],
            "digital_root": meta["dr"],
            "e8": _normalize_e8(list(meta["e8"])),
            "source": "lexicon",
        }
    digest = hashlib.sha256(glyph.encode()).digest()
    coords = _normalize_e8([b / 255.0 for b in digest[:8]])
    dr = (sum(int(coords[i] * 9) for i in range(2)) % 9) or 9
    return {
        "glyph": glyph,
        "glyph_id": f"unknown_{glyph[:8]}",
        "digital_root": dr,
        "e8": coords,
        "source": "hash",
    }


def glyphs_to_etp_program(text: str, *, program_length: int = 32) -> str:
    """Encode glyph string as loopless ETP program (}<>+01)."""
    if not text:
        return "0"
    out: list[str] = []
    for ch in text:
        if ch in _ETP_ALPHABET:
            out.append(ch)
            continue
        h = hashlib.sha256(ch.encode()).digest()[0]
        out.append(_ETP_ALPHABET[h % len(_ETP_ALPHABET)])
    prog = "".join(out)
    if len(prog) < program_length:
        extra = hashlib.sha256(prog.encode()).digest()
        while len(prog) < program_length:
            prog += _ETP_ALPHABET[extra[len(prog) % len(extra)] % len(_ETP_ALPHABET)]
    return prog[:program_length]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def annotate_grain_tags(grain: Any, glyph: str) -> None:
    """Attach glyphic_tarpit labels to a spine ``Grain`` (tags + associations)."""
    meta = glyph_meta(glyph)
    tag = f"glyph:{meta['glyph_id']}"
    if tag not in grain.tags:
        grain.tags.append(tag)
    grain.associations["glyph_dr"] = float(meta["digital_root"])
    grain.associations["glyph_sim"] = meta.get("source", "")
