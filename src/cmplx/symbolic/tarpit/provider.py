"""
TarPitSymbolicProvider — the `symbolic` port provider.

This module implements the SymbolicProvider Protocol against the existing
TarpitEcology runtime + run_etp_with_ledger. It is the canonical source
for ``encode_to_etp(morphon) -> str`` and ``decode_from_etp(ledger) -> Morphon``.
Other Protocols (AddressingProvider, MemoryProvider, TransportProvider)
delegate their ETP encode/decode methods here, possibly after port-specific
prefixing of the program string.

Sub-frame slot F-4. See docs/sub_frames/port_provider_facades.md.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from cmplx.morphon import Morphon, SymbolicReport

from .aggregation import ExecutionMode, TarpitAggregator
from ._functions import RelativityEnvelope, run_etp_with_ledger
from ._receipt_bridge import mint_tarpit_operation


# The 6-symbol "loopless" alphabet used for encode_to_etp. Excludes `[` and `]`
# so no bracket-balancing post-processing is needed; the resulting program is
# always syntactically valid for ETP execution.
#
# Trade-off: encoded programs never use loops, so they don't exercise the full
# ETP IR. That's intentional — encoding is about packing a morphon's identity
# into ETP space deterministically, not about generating maximally rich
# programs. Loops belong to programs that are *authored*, not encoded.
_ENCODE_ALPHABET = "}<>+01"


def _stable_serialize(morphon: Morphon) -> bytes:
    """Deterministic byte serialization for a morphon used as ETP-encoding seed.

    Captures the morphon's identity (id + payload). Receipts, state, and
    cached projections (dr_channel, e8_coordinates, leech_point) are *not*
    included — the encoding depends only on what the morphon IS at a
    structural level, not on its current lifecycle phase.
    """
    return json.dumps(
        {
            "id": morphon.id,
            "payload": morphon.payload,
            "parent": morphon.parent,
        },
        sort_keys=True,
        default=str,
    ).encode("utf-8")


class TarPitSymbolicProvider:
    """The `symbolic` port — ETP IR runtime.

    Conforms to ``cmplx.morphon.SymbolicProvider`` Protocol. Registration:

        MorphonController.get().register("symbolic", TarPitSymbolicProvider())

    Once registered, this provider is the canonical encode_to_etp /
    decode_from_etp source for the entire system. Other port providers
    that need to cross the ETP wire format delegate here.
    """

    name: str = "tarpit_symbolic_provider"

    def __init__(
        self,
        *,
        default_dimension: int = 8,
        default_max_steps: int = 200,
        program_length: int = 32,
    ) -> None:
        """
        Args:
            default_dimension: ETP torus dimension for derive() runs. 8 is
                canonical (aligns with E8 geometry).
            default_max_steps: hard cap on steps per derive() run. Loopless
                encoded programs typically terminate within program_length
                steps, so this is a safety belt rather than a budget.
            program_length: bytes of hash used as program length. 32 = full
                SHA256 → 32-character ETP program. Reduce for shorter
                programs, increase by re-hashing for longer.
        """
        self.default_dimension = default_dimension
        self.default_max_steps = default_max_steps
        self.program_length = program_length
        self.aggregator = TarpitAggregator(
            dimension=default_dimension,
            max_steps=default_max_steps,
            program_length=program_length,
        )

    # ── Core Protocol methods ────────────────────────────────────────

    def derive(self, morphon: Morphon) -> SymbolicReport:
        """Run ETP on the morphon's encoded program. Returns dual-report.

        The encoded program is deterministic per morphon (id + payload + parent).
        The returned SymbolicReport carries both the typed trace (ledger) AND
        the raw ecology, so callers can use either view.

        If the `receipt` port is registered, a Receipt is minted per ETP step
        (subject to receipt-grammar mapping; PROCESS receipts for normal steps,
        GATE receipts on envelope failures, DEATH receipts on ErrorWall).
        Otherwise receipts list is empty.
        """
        program = self.encode_to_etp(morphon)
        result = run_etp_with_ledger(
            program,
            dimension=self.default_dimension,
            max_steps=self.default_max_steps,
        )

        # Pull the ecology out by re-instantiating (run_etp_with_ledger doesn't
        # return the ecology directly; it returns summary+ledger). For dual-
        # report shape, run a separate run() to capture the live ecology.
        # Both runs use the same program and the same gauge_seed (derived
        # deterministically from the program hash via seed_from_program in
        # _functions.py), so they produce identical state — but we must pass
        # the seed explicitly to TarpitEcology or its internal RNG draws from
        # system entropy.
        from .ecology import TarpitEcology
        from ._functions import seed_from_program
        seed = seed_from_program(program, self.default_dimension)
        ecology = TarpitEcology(
            dimension=self.default_dimension,
            max_steps=self.default_max_steps,
            seed=seed,
        )
        ecology_result = ecology.run(program)

        receipts = self._mint_step_receipts(morphon, result["ledger"])

        return SymbolicReport(
            trace=result["ledger"],
            ecology=ecology,
            output_walls=list(ecology_result.output_walls),
            error_walls=list(ecology_result.error_walls),
            receipts=receipts,
            summary=result["summary"],
        )

    def run_program(self, program: str, **kwargs: Any) -> dict:
        """Direct ETP execution — wraps run_etp_with_ledger.

        kwargs forwarded as-is: dimension, max_steps, gauge_seed, envelope,
        mirror_policy, force_mirror_on_error, stop_after_steps.
        """
        kwargs.setdefault("dimension", self.default_dimension)
        kwargs.setdefault("max_steps", self.default_max_steps)
        return run_etp_with_ledger(program, **kwargs)

    def execute_aggregated(
        self,
        program: str,
        mode: ExecutionMode = "etp",
        *,
        envelope: RelativityEnvelope | None = None,
    ) -> dict[str, Any]:
        """Run via ``TarpitAggregator`` (glyphic / unified / evolving modes)."""
        session = self.aggregator.start_session(program, mode=mode)
        agg = self.aggregator.execute_session(
            session.session_id, envelope=envelope
        )
        return {"session": session.to_dict(), "result": agg.to_dict()}

    def evolve_program(
        self,
        program: str,
        *,
        iterations: int = 5,
        mutation_rate: float = 0.1,
    ) -> list[dict[str, Any]]:
        """evolving_tarpit lineage — mutation runs."""
        return [r.to_dict() for r in self.aggregator.evolve_lineage(
            program, iterations=iterations, mutation_rate=mutation_rate
        )]

    def encode_to_etp(self, morphon: Morphon) -> str:
        """Canonical morphon → ETP-program-string encoding.

        Deterministic per (morphon.id, morphon.payload, morphon.parent).
        Uses SHA256 of the stable serialization; each byte mod 6 picks from
        the 6-symbol loopless alphabet ``}<>+01``. Programs are always
        syntactically valid (no bracket-balancing needed).
        """
        digest = hashlib.sha256(_stable_serialize(morphon)).digest()
        # Extend or truncate to the configured program_length.
        if self.program_length > len(digest):
            # Extend by chained hashing.
            buf = bytearray(digest)
            while len(buf) < self.program_length:
                buf.extend(hashlib.sha256(bytes(buf)).digest())
            digest = bytes(buf[: self.program_length])
        else:
            digest = digest[: self.program_length]

        return "".join(_ENCODE_ALPHABET[b % len(_ENCODE_ALPHABET)] for b in digest)

    def decode_from_etp(self, ledger: list[dict]) -> Morphon:
        """Reconstruct a Morphon from an ETP ledger.

        Returns a *derived* morphon whose payload captures the ETP run's
        final state (torus8, wall10, digital_root, halted). This is NOT a
        perfect inverse of encode_to_etp on the original morphon — the
        original payload is not in the ledger. It IS the canonical way to
        materialize an ETP result as a morphon for downstream consumers.

        The morphon's parent is set to the ledger's first-step instruction
        pointer + program-length fingerprint so two decodes of the same
        ledger produce the same morphon ID.
        """
        if not ledger:
            return Morphon.forge(payload={"etp_decode": "empty_ledger"})

        final = ledger[-1]
        payload = {
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
        }
        return Morphon.forge(payload=payload)

    # ── Convenience surface ────────────────────────────────────────

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": self.name,
            "default_dimension": self.default_dimension,
            "default_max_steps": self.default_max_steps,
            "program_length": self.program_length,
            "alphabet": _ENCODE_ALPHABET,
            "sessions": len(self.aggregator._sessions),
            "canonical_forms": [
                "evolving_tarpit",
                "glyphic_tarpit",
                "unified_tarpit",
            ],
        }

    def __repr__(self) -> str:
        return (
            f"<TarPitSymbolicProvider dim={self.default_dimension} "
            f"prog_len={self.program_length}>"
        )

    # ── Internal: receipt minting ────────────────────────────────

    def _mint_step_receipts(
        self, morphon: Morphon, ledger: list[dict]
    ) -> list:
        """Mint one receipt per ledger step via unified receipt bridge."""
        receipts = []
        for row in ledger:
            mint_tarpit_operation(
                "etp_step",
                {
                    "step": row.get("step"),
                    "ip_before": row.get("ip_before"),
                    "instr": row.get("instr"),
                    "wall10": row.get("wall10"),
                    "torus8": row.get("torus8"),
                    "digital_root": row.get("digital_root"),
                    "envelope_ok": row.get("envelope_ok", True),
                    "error_class": row.get("last_error_class"),
                },
                atom_id=morphon.id,
            )
            try:
                from cmplx.morphon import MorphonController

                prov = MorphonController.get().get_provider("receipt")
                if prov is not None and getattr(prov, "chain", None) is not None:
                    receipts.append(prov.chain._chain[-1])
            except Exception:
                pass
        return receipts
