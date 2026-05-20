"""Canonical TarPit lineage names (witness + homonym register)."""
from __future__ import annotations

CANONICAL_FORMS: tuple[str, ...] = (
    "evolving_tarpit",
    "glyphic_tarpit",
    "unified_tarpit",
)

# Corpus paths often use legacy folder name; treat as glyphic_tarpit.
CANONICAL_ALIASES: dict[str, str] = {
    "glyph_tarpit": "glyphic_tarpit",
    "unified_tarpit.py": "unified_tarpit",
    "evolving_tarpit.zip": "evolving_tarpit",
}


def normalize_form_name(path_fragment: str) -> str | None:
    """Map a path fragment to a canonical form id, if recognized."""
    low = path_fragment.lower().replace("\\", "/")
    for canonical in CANONICAL_FORMS:
        if canonical in low:
            return canonical
    for alias, canonical in CANONICAL_ALIASES.items():
        if alias in low:
            return canonical
    return None
