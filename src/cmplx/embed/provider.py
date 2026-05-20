"""
FourEmbedProvider — the `embed` port provider.

Decomposes morphons into the four typed channels (Constraint / State /
Evidence / Operator) of the 4-Embed Model. See INTERFACE.md alongside.

Parent frame slot 19. Provider satisfies the ``EmbedProvider`` Protocol.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from cmplx.morphon import FourEmbedView, Morphon


# Reserved payload keys that, when present, drive the explicit-decomposition
# path. A morphon payload using any of these keys gets its channels read
# directly. The remaining keys are merged into the state channel as
# residual data.
_EXPLICIT_KEYS = ("constraint", "state", "evidence", "operator")


class FourEmbedProvider:
    """The `embed` port — 4-Embed Model decomposition.

    Conforms to ``cmplx.morphon.EmbedProvider`` Protocol. Registration:

        MorphonController.get().register("embed", FourEmbedProvider())

    Decomposition rules:
      - **Explicit shape**: payloads whose dict has any of
        ``constraint``/``state``/``evidence``/``operator`` keys are read
        directly into the corresponding channels. Any other keys merge
        into the state channel.
      - **Implicit shape**: payloads without any of those keys are treated
        wholesale as the state channel; constraint / operator default to
        empty (``None``); evidence is populated from the morphon's receipt
        chain so consumers get free provenance.
      - **Non-dict payloads**: the payload becomes the state channel,
        other channels default to empty.

    The decomposition is non-destructive — the original morphon is
    unchanged; the returned ``FourEmbedView`` is a typed view, not a
    rewrite.
    """

    name: str = "four_embed_provider"

    def __init__(self, *, include_receipt_evidence: bool = True) -> None:
        """
        Args:
            include_receipt_evidence: When True (default), the evidence
                channel is populated with a summary of the morphon's
                receipt chain when no explicit ``evidence`` key exists in
                the payload. Set False for callers that want strictly
                payload-derived channels.
        """
        self.include_receipt_evidence = include_receipt_evidence

    # ── Core Protocol method ───────────────────────────────────────

    def decompose(self, morphon: Morphon) -> FourEmbedView:
        """Return the 4-channel typed view of this morphon.

        Implementation routes between the explicit and implicit shapes
        based on payload structure. Always returns a ``FourEmbedView``;
        never raises (a malformed payload yields the implicit shape).
        """
        payload = morphon.payload

        if isinstance(payload, dict) and any(k in payload for k in _EXPLICIT_KEYS):
            return self._decompose_explicit(morphon, payload)
        return self._decompose_implicit(morphon, payload)

    # ── ETP integration ───────────────────────────────────────────

    def encode_to_etp(self, morphon: Morphon) -> str:
        """Encode the morphon as an ETP program.

        Delegates to the registered ``symbolic`` provider when present.
        Falls back to a local SHA-256 → loopless-alphabet encoding that
        matches every other facade's fallback byte-for-byte.
        """
        symbolic = self._maybe_get_symbolic()
        if symbolic is not None:
            return symbolic.encode_to_etp(morphon)
        return self._fallback_encode_to_etp(morphon)

    def decode_from_etp(self, ledger: list[dict]) -> Morphon:
        """Reconstruct a morphon from an ETP ledger.

        Delegates to the registered ``symbolic`` provider when present;
        falls back to materializing the ledger's final row.
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
            "include_receipt_evidence": self.include_receipt_evidence,
        }

    def __repr__(self) -> str:
        return f"<FourEmbedProvider receipt_evidence={self.include_receipt_evidence}>"

    # ── Internals ──────────────────────────────────────────────────

    def _decompose_explicit(self, morphon: Morphon, payload: dict) -> FourEmbedView:
        """The morphon's payload has at least one of the reserved keys —
        read each channel directly and roll any leftover keys into state."""
        constraint = payload.get("constraint")
        state = payload.get("state")
        evidence = payload.get("evidence")
        operator = payload.get("operator")

        # Any non-reserved keys roll into state as residual data. If state
        # was explicitly None or missing, the residual becomes state.
        residual = {k: v for k, v in payload.items() if k not in _EXPLICIT_KEYS}
        if residual:
            if state is None:
                state = residual
            elif isinstance(state, dict):
                state = {**state, "_residual": residual}
            # else: state is a non-dict value; drop residual silently
            #       (the user's explicit state wins)

        # Evidence augmentation: if the user didn't supply evidence and
        # the morphon has receipts, surface those as provenance.
        if evidence is None and self.include_receipt_evidence:
            evidence = self._receipts_as_evidence(morphon)

        return FourEmbedView(
            constraint=constraint,
            state=state,
            evidence=evidence,
            operator=operator,
            morphon_id=morphon.id,
        )

    def _decompose_implicit(self, morphon: Morphon, payload: Any) -> FourEmbedView:
        """No reserved keys — the whole payload is the state channel."""
        evidence = (
            self._receipts_as_evidence(morphon)
            if self.include_receipt_evidence
            else None
        )
        return FourEmbedView(
            constraint=None,
            state=payload,
            evidence=evidence,
            operator=None,
            morphon_id=morphon.id,
        )

    def _receipts_as_evidence(self, morphon: Morphon) -> list[dict] | None:
        """Summarize the morphon's receipt chain as evidence entries.

        Returns None when the morphon has no receipts. Each entry is a
        small dict with the operation, timestamp, and detail — enough
        for downstream consumers to assess provenance without traversing
        the chain themselves.
        """
        receipts = getattr(morphon, "receipts", None)
        if not receipts:
            return None
        return [
            {
                "operation": getattr(r, "operation", ""),
                "timestamp": getattr(r, "timestamp", ""),
                "detail": dict(getattr(r, "detail", {}) or {}),
            }
            for r in receipts
        ]

    def _maybe_get_symbolic(self) -> Any:
        try:
            from cmplx.morphon import MorphonController
            return MorphonController.get().get_provider("symbolic")
        except (LookupError, ImportError):
            return None

    def _fallback_encode_to_etp(self, morphon: Morphon) -> str:
        """Byte-identical with TarPitSymbolicProvider's encoding."""
        alphabet = "}<>+01"
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
        return "".join(alphabet[b % len(alphabet)] for b in digest)

    def _fallback_decode_from_etp(self, ledger: list[dict]) -> Morphon:
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
