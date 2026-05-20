"""
LibEncoder — YAML-driven encoders for multistream sidecar ingest.

Streams: native | math | notation (plus default ``en`` via CorpusIngester).

TranslateHub extension point
----------------------------
Production default is ``NoOpHub`` (passthrough). Configure via env::

    CMPLX_TRANSLATE_HUB=noop          # default
    CMPLX_TRANSLATE_HUB=passthrough   # alias for noop

Future MT backends (e.g. DeepL) implement ``TranslateHub.translate`` and register
in ``translate_hub_from_env()`` — do not wire API keys in library code.
"""
from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Protocol

from .token_index.notation import SurfaceMode, load_notation_lib, normalize_surface

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

_DEFAULT_NATIVE_LIB = (
    Path(__file__).resolve().parents[3] / "data" / "rule_libs" / "native" / "starter.yaml"
)


class EncoderConfig(Protocol):
    stream: str


@dataclass
class EncodedSegment:
    concat: str
    translation_key: str
    stream: str
    label: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


class LibEncoder(ABC):
    """Encode raw text into 8-char bond windows for a sidecar stream."""

    stream: str = "native"

    @abstractmethod
    def encode(self, text: str, *, translation_key: str) -> list[EncodedSegment]:
        ...


def _load_native_config(path: str | Path | None = None) -> dict[str, Any]:
    if yaml is None:
        return {}
    p = Path(path) if path else _DEFAULT_NATIVE_LIB
    if not p.is_file():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


@dataclass
class NativeLibEncoder(LibEncoder):
    """Segment on word tokens; pad/truncate to 8-char bonds.

    Token pattern and boundaries are YAML-driven (``data/rule_libs/native/``).
    """

    stream: str = "native"
    min_token_len: int = 4
    token_pattern: str = r"[A-Za-z0-9\u00C0-\u024F]+"
    use_word_boundaries: bool = True

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> "NativeLibEncoder":
        cfg = _load_native_config(path)
        return cls(
            stream=str(cfg.get("stream", "native")),
            min_token_len=int(cfg.get("min_token_len", 4)),
            token_pattern=str(cfg.get("token_pattern", r"[A-Za-z0-9\u00C0-\u024F]+")),
            use_word_boundaries=bool(cfg.get("use_word_boundaries", True)),
        )

    def _token_regex(self) -> re.Pattern[str]:
        pat = self.token_pattern
        if self.use_word_boundaries and not pat.startswith(r"\b"):
            pat = rf"\b(?:{pat})\b"
        return re.compile(pat)

    def encode(self, text: str, *, translation_key: str) -> list[EncodedSegment]:
        tokens = self._token_regex().findall(text)
        out: list[EncodedSegment] = []
        for tok in tokens:
            if len(tok) < self.min_token_len:
                continue
            concat = tok[:8].ljust(8, "a")
            out.append(
                EncodedSegment(
                    concat=concat,
                    translation_key=translation_key,
                    stream=self.stream,
                    label=tok,
                )
            )
        return out


@dataclass
class NotationLibEncoder(LibEncoder):
    stream: str = "notation"
    lib: dict = field(default_factory=load_notation_lib)

    def encode(self, text: str, *, translation_key: str) -> list[EncodedSegment]:
        norm = normalize_surface(text, mode=SurfaceMode.UNICODE_EQUIV, lib=self.lib)
        chunks = [norm[i : i + 8] for i in range(0, max(len(norm), 1), 8)]
        out: list[EncodedSegment] = []
        for i, chunk in enumerate(chunks):
            concat = chunk[:8].ljust(8, "a")
            out.append(
                EncodedSegment(
                    concat=concat,
                    translation_key=translation_key,
                    stream=self.stream,
                    label=chunk.strip() or f"chunk:{i}",
                )
            )
        return out


_SYMBOL_RUN = re.compile(
    r"[+\-*/=^_{}\\()[\]αβγδεζηθικλμνξοπρστυφχψω"
    r"∀∃∈∉⊂⊃∪∩≤≥≠≈∞∫∑∏√∂∇]+",
    re.UNICODE,
)


@dataclass
class MathLibEncoder(LibEncoder):
    """LaTeX-ish and symbol-run tokenization (command table from YAML)."""

    stream: str = "math"
    commands: dict[str, str] = field(default_factory=dict)
    min_symbol_len: int = 2

    @classmethod
    def from_yaml(cls, path: str | Path) -> "MathLibEncoder":
        if yaml is None:
            raise ImportError("PyYAML required")
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls(
            commands={str(k): str(v) for k, v in (data.get("latex_commands") or {}).items()},
            min_symbol_len=int(data.get("min_symbol_len", 2)),
        )

    def encode(self, text: str, *, translation_key: str) -> list[EncodedSegment]:
        lib = load_notation_lib()
        lib["latex_commands"] = {**lib.get("latex_commands", {}), **self.commands}
        normalized = normalize_surface(text, mode=SurfaceMode.LATEX_COMMAND, lib=lib)
        normalized = normalize_surface(normalized, mode=SurfaceMode.OPERATOR, lib=lib)
        out: list[EncodedSegment] = []
        seen: set[str] = set()
        for m in _SYMBOL_RUN.finditer(normalized):
            sym = m.group(0)
            if len(sym) < self.min_symbol_len or sym in seen:
                continue
            seen.add(sym)
            concat = sym[:8].ljust(8, "a")
            out.append(
                EncodedSegment(
                    concat=concat,
                    translation_key=translation_key,
                    stream=self.stream,
                    label=sym,
                    meta={"span": [m.start(), m.end()]},
                )
            )
        if not out:
            enc = NotationLibEncoder(stream=self.stream, lib=lib)
            return enc.encode(normalized, translation_key=translation_key)
        return out


def encoder_for_stream(stream: str, lib_path: Optional[str | Path] = None) -> LibEncoder:
    stream = stream.strip().lower()
    if stream == "native":
        if lib_path and Path(lib_path).is_file():
            return NativeLibEncoder.from_yaml(lib_path)
        return NativeLibEncoder.from_yaml()
    if stream == "math":
        if lib_path and Path(lib_path).is_file():
            return MathLibEncoder.from_yaml(lib_path)
        return MathLibEncoder(commands=load_notation_lib().get("latex_commands", {}))
    if stream == "notation":
        notation_lib = load_notation_lib(lib_path) if lib_path else load_notation_lib()
        return NotationLibEncoder(lib=notation_lib)
    raise ValueError(f"unsupported stream for LibEncoder: {stream}")


class TranslateHub(ABC):
    """Optional EN hub — implement ``translate`` for external MT backends."""

    @abstractmethod
    def translate(self, text: str, *, target: str = "en") -> str:
        ...


class NoOpHub(TranslateHub):
    """Production default: passthrough (no MT)."""

    def translate(self, text: str, *, target: str = "en") -> str:
        return text


class PassthroughTranslateHub(NoOpHub):
    """Backward-compatible alias for NoOpHub."""


def translate_hub_from_env() -> TranslateHub:
    """Env-driven TranslateHub factory (``CMPLX_TRANSLATE_HUB``)."""
    kind = os.environ.get("CMPLX_TRANSLATE_HUB", "noop").strip().lower()
    if kind in ("noop", "none", "", "passthrough", "stub"):
        return NoOpHub()
    # Extension point — wire DeepL or other providers here after review.
    if kind == "deepl":
        raise NotImplementedError(
            "DeepLTranslateHub is not bundled; set CMPLX_TRANSLATE_HUB=noop "
            "or implement DeepLTranslateHub and register it in translate_hub_from_env()"
        )
    raise ValueError(f"unknown CMPLX_TRANSLATE_HUB={kind!r}")


__all__ = [
    "EncodedSegment",
    "LibEncoder",
    "NativeLibEncoder",
    "NotationLibEncoder",
    "MathLibEncoder",
    "encoder_for_stream",
    "TranslateHub",
    "NoOpHub",
    "PassthroughTranslateHub",
    "translate_hub_from_env",
]
