"""
TransportProviderFacade — the `transport` port provider.

Wraps a ``CarrierRegistry`` (or a single ``Carrier``) and exposes the
extended TransportProvider Protocol: ``encode`` / ``decode`` for physical
channel bytes plus the ETP wire format for cross-channel transport.

Sub-frame slot F-5. See docs/sub_frames/port_provider_facades.md.

The facade serializes/deserializes a ``CarrierFrame`` to/from JSON-bytes so
the Protocol's ``encode(morphon) -> bytes`` / ``decode(bytes) -> Morphon``
contract is satisfiable in one round-trip. The default carrier can be
named at construction or inferred (first registered) at first use.
"""
from __future__ import annotations

import base64
import json
from typing import Any

from cmplx.morphon import Morphon

from .carrier import Carrier, CarrierFrame, CarrierRegistry


class TransportProviderFacade:
    """The `transport` port — multi-carrier encode/decode + ETP wire format.

    Conforms to ``cmplx.morphon.TransportProvider`` Protocol. Registration:

        registry = CarrierRegistry()
        registry.register(DTMFCarrier())
        # registry.register(PixelCarrier())
        MorphonController.get().register(
            "transport", TransportProviderFacade(registry)
        )

    The facade picks ``default_carrier`` for encode/decode calls. Callers
    that want multi-carrier dispatch can access the registry directly
    via ``self.registry``.
    """

    name: str = "transport_provider_facade"

    def __init__(
        self,
        registry: CarrierRegistry | None = None,
        *,
        default_carrier: str | None = None,
    ) -> None:
        self.registry = registry or CarrierRegistry()
        self._default_carrier_name = default_carrier

    # ── Core physical-channel encode/decode ─────────────────────────

    def encode(self, morphon: Morphon) -> bytes:
        """Encode the morphon as channel bytes via the default carrier.

        The returned bytes are a JSON envelope containing the carrier name,
        the morphon ID + channel, and the carrier's payload_bytes (base64'd
        to stay inside JSON). ``decode()`` reverses this exactly.
        """
        carrier = self._default_carrier()
        frame = carrier.encode(morphon)
        envelope = {
            "carrier_name": frame.carrier_name,
            "morphon_id": frame.morphon_id,
            "channel": frame.channel,
            "payload_b64": base64.b64encode(frame.payload_bytes).decode("ascii"),
        }
        return json.dumps(envelope).encode("utf-8")

    def decode(self, payload: bytes) -> Morphon:
        """Decode channel bytes back into a (partial) Morphon.

        Returns a morphon carrying the identifying fields recovered from
        the carrier (morphon_id, channel, plus any carrier-specific extras
        from carrier.decode). The original payload is *not* recovered from
        channel bytes — that's by Carrier-ABC design (full payload lives in
        MMDB). The returned morphon is shaped as a transport-decoded view.
        """
        envelope = json.loads(payload.decode("utf-8"))
        frame = CarrierFrame(
            carrier_name=envelope["carrier_name"],
            morphon_id=envelope["morphon_id"],
            channel=envelope["channel"],
            payload_bytes=base64.b64decode(envelope["payload_b64"].encode("ascii")),
        )
        carrier = self.registry.get(frame.carrier_name)
        decoded_fields = carrier.decode(frame)

        # Wrap the recovered fields in a fresh morphon. The transport
        # contract is "identity + cached projections only" — full payload
        # retrieval requires the `memory` port.
        return Morphon.forge(
            payload={
                "transport_decode": True,
                "carrier_name": frame.carrier_name,
                "morphon_id": decoded_fields.get("morphon_id", frame.morphon_id),
                "channel": decoded_fields.get("channel", frame.channel),
                "carrier_fields": {
                    k: v for k, v in decoded_fields.items()
                    if k not in ("morphon_id", "channel")
                },
            }
        )

    # ── ETP integration ─────────────────────────────────────────────

    def encode_to_etp(self, morphon: Morphon) -> str:
        """Encode the morphon as an ETP program for cross-channel transport.

        Delegates to the registered ``symbolic`` provider when present;
        falls back to a local SHA256 → loopless-alphabet encoding.
        """
        symbolic = self._maybe_get_symbolic()
        if symbolic is not None:
            return symbolic.encode_to_etp(morphon)
        return self._fallback_encode_to_etp(morphon)

    def decode_from_etp(self, ledger: list[dict]) -> Morphon:
        """Reconstruct a morphon from an ETP ledger received over a channel."""
        symbolic = self._maybe_get_symbolic()
        if symbolic is not None:
            return symbolic.decode_from_etp(ledger)
        return self._fallback_decode_from_etp(ledger)

    # ── Convenience surface ────────────────────────────────────────

    @property
    def health(self) -> dict:
        carriers = sorted(self.registry._carriers.keys())
        return {
            "ok": True,
            "service": self.name,
            "carriers": carriers,
            "default_carrier": self._default_carrier_name or (carriers[0] if carriers else None),
        }

    def __repr__(self) -> str:
        carriers = sorted(self.registry._carriers.keys())
        return f"<TransportProviderFacade carriers={carriers}>"

    # ── Internals ──────────────────────────────────────────────────

    def _default_carrier(self) -> Carrier:
        """Return the default carrier (named at init, else first registered)."""
        if self._default_carrier_name is not None:
            return self.registry.get(self._default_carrier_name)
        if not self.registry._carriers:
            raise LookupError(
                "TransportProviderFacade has no registered carriers; "
                "register at least one before calling encode/decode"
            )
        name = sorted(self.registry._carriers.keys())[0]
        return self.registry.get(name)

    def _maybe_get_symbolic(self) -> Any:
        try:
            from cmplx.morphon import MorphonController
            return MorphonController.get().get_provider("symbolic")
        except (LookupError, ImportError):
            return None

    def _fallback_encode_to_etp(self, morphon: Morphon) -> str:
        """Matches TarPitSymbolicProvider's encoding byte-for-byte."""
        import hashlib
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
