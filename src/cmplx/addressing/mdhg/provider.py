"""
MDHGAddressingProvider — the `addressing` port provider.

Wraps the stateless ``MDHG`` channel hasher and the multi-scale helpers
``quantize_24`` / ``slot_id_from_q24`` into a single object satisfying
the extended ``AddressingProvider`` Protocol.

Sub-frame slot F-2. See docs/sub_frames/port_provider_facades.md.

ETP delegation: ``encode_to_etp`` / ``decode_from_etp`` route through the
``symbolic`` port's TarPitSymbolicProvider when registered (it is the
canonical ETP source). When symbolic is not registered, the facade falls
back to a deterministic local encoding so the port remains useful in
standalone tests.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from cmplx.morphon import Morphon

from .hash import MDHG
from .multiscale import quantize_24, slot_id_from_q24, DEFAULT_BINS, QUANT_DIMS


# Loopless ETP alphabet (matches TarPitSymbolicProvider). Used only by the
# fallback encoder when no symbolic provider is registered.
_FALLBACK_ETP_ALPHABET = "}<>+01"


def _payload_to_24vec(payload: Any) -> list[float]:
    """Map a morphon payload to a 24-D float vector in roughly [-1, 1].

    SHA256 → 32 bytes; take the first 24 and map each byte b to
    (b - 128) / 128.0. Deterministic per stable JSON serialization.
    """
    serialized = json.dumps(payload, sort_keys=True, default=str)
    digest = hashlib.sha256(serialized.encode("utf-8")).digest()
    return [(b - 128) / 128.0 for b in digest[:QUANT_DIMS]]


class MDHGAddressingProvider:
    """The `addressing` port — channel-1-9 + multi-scale slot addressing.

    Conforms to ``cmplx.morphon.AddressingProvider`` Protocol. Registration:

        MorphonController.get().register("addressing", MDHGAddressingProvider())
    """

    name: str = "mdhg_addressing_provider"

    def __init__(self, *, bins: int = DEFAULT_BINS) -> None:
        self._mdhg = MDHG()
        self._bins = bins

    # ── Core: channel_for ────────────────────────────────────────────

    def channel_for(self, morphon: Morphon) -> int:
        """Return the digital-root channel (1-9) for this morphon."""
        return self._mdhg.channel_for(morphon)

    # ── Multi-scale extensions ──────────────────────────────────────

    def quantize24(self, morphon: Morphon) -> tuple[int, ...]:
        """Return the 24-tuple quantization for this morphon's payload."""
        vec = _payload_to_24vec(morphon.payload)
        return quantize_24(vec, self._bins)

    def slot_id(self, q24: tuple[int, ...]) -> str:
        """Return the stable 16-hex-char slot ID for a 24-tuple."""
        return slot_id_from_q24(q24)

    # ── ETP integration ─────────────────────────────────────────────

    def encode_to_etp(self, morphon: Morphon) -> str:
        """Encode the morphon as an ETP program.

        Delegates to the registered ``symbolic`` provider when present.
        Falls back to a local SHA256 → loopless-alphabet encoding when
        no symbolic provider is registered (e.g., during isolated tests).
        """
        symbolic = self._maybe_get_symbolic()
        if symbolic is not None:
            return symbolic.encode_to_etp(morphon)
        return self._fallback_encode_to_etp(morphon)

    def decode_from_etp(self, ledger: list[dict]) -> Morphon:
        """Reconstruct a morphon from an ETP ledger.

        Delegates to the registered ``symbolic`` provider when present.
        Falls back to materializing the ledger's final row as a morphon
        payload when no symbolic provider is registered.
        """
        symbolic = self._maybe_get_symbolic()
        if symbolic is not None:
            return symbolic.decode_from_etp(ledger)
        return self._fallback_decode_from_etp(ledger)

    # ── Convenience surface ────────────────────────────────────────

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": self.name,
            "bins": self._bins,
            "quant_dims": QUANT_DIMS,
        }

    def __repr__(self) -> str:
        return f"<MDHGAddressingProvider bins={self._bins}>"

    # ── Internals ──────────────────────────────────────────────────

    def _maybe_get_symbolic(self) -> Any:
        """Return the registered symbolic provider, or None."""
        try:
            from cmplx.morphon import MorphonController
            return MorphonController.get().get_provider("symbolic")
        except (LookupError, ImportError):
            return None

    def _fallback_encode_to_etp(self, morphon: Morphon) -> str:
        """Local encoding used when no symbolic provider is registered.

        Matches TarPitSymbolicProvider's encoding scheme byte-for-byte so
        callers see the same program either way: SHA256 of (id, payload,
        parent) → each byte mod 6 → loopless alphabet.
        """
        serialized = json.dumps(
            {
                "id": morphon.id,
                "payload": morphon.payload,
                "parent": morphon.parent,
            },
            sort_keys=True,
            default=str,
        ).encode("utf-8")
        digest = hashlib.sha256(serialized).digest()
        return "".join(
            _FALLBACK_ETP_ALPHABET[b % len(_FALLBACK_ETP_ALPHABET)] for b in digest
        )

    def _fallback_decode_from_etp(self, ledger: list[dict]) -> Morphon:
        """Local decoding used when no symbolic provider is registered.

        Materializes the ledger's final row as a derived morphon payload,
        matching TarPitSymbolicProvider.decode_from_etp's shape.
        """
        if not ledger:
            return Morphon.forge(payload={"etp_decode": "empty_ledger"})
        final = ledger[-1]
        return Morphon.forge(payload={
            "etp_decode": True,
            "torus8": list(final.get("torus8", [])),
            "torus8_mirror": list(final.get("torus8_mirror", [])),
            "wall10": final.get("wall10", "0.000"),
            "digital_root": final.get("digital_root", 0),
            "halted": final.get("halted_now", False),
            "n_grains": final.get("n_grains", 0),
            "dusts": final.get("dusts", 0),
            "triads": final.get("triads", 0),
            "steps": final.get("step", 0),
        })
