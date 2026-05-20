"""
TarPit aggregation — merge evolving_tarpit, glyphic_tarpit, unified_tarpit behaviors.

- **evolving_tarpit**: ``evolve()`` lineage + session history
- **glyphic_tarpit**: glyph → ETP program encoding + lexicon tags
- **unified_tarpit**: ``run_etp_with_ledger`` + ``RelativityEnvelope`` probe surface
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Literal, Optional

from .ecology import ComputationResult, TarpitEcology
from .glyphic import GLYPH_LEXICON, glyphs_to_etp_program
from ._functions import RelativityEnvelope, run_etp_with_ledger
from ._receipt_bridge import mint_tarpit_operation

ExecutionMode = Literal["etp", "glyph", "jot", "evolve"]


@dataclass
class ExecutionSession:
    """glyphic_tarpit-style session tracking (in-process)."""
    session_id: str
    program: str
    mode: str
    canonical_form: str
    start_time: float = field(default_factory=time.time)
    walls: list[dict[str, Any]] = field(default_factory=list)
    results: list[dict[str, Any]] = field(default_factory=list)
    lineage: list[str] = field(default_factory=list)
    completed: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AggregatedRun:
    """unified_tarpit-style compact summary of one or more runs."""
    program: str
    mode: str
    success: bool
    steps: int
    bonds: int
    mirrors: int
    digital_root: int
    final_mass: float
    envelope_ok: bool
    ledger_rows: int
    canonical_forms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TarpitAggregator:
    """Orchestrates spine + three canonical form behaviors."""

    def __init__(
        self,
        *,
        dimension: int = 8,
        max_steps: int = 200,
        program_length: int = 32,
    ) -> None:
        self.dimension = dimension
        self.max_steps = max_steps
        self.program_length = program_length
        self._sessions: dict[str, ExecutionSession] = {}
        self._ecology = TarpitEcology(dimension=dimension, max_steps=max_steps)

    @property
    def ecology(self) -> TarpitEcology:
        return self._ecology

    def _canonical_form_for_mode(self, mode: ExecutionMode) -> str:
        if mode == "glyph":
            return "glyphic_tarpit"
        if mode == "evolve":
            return "evolving_tarpit"
        return "unified_tarpit"

    def resolve_program(self, program: str, mode: ExecutionMode) -> str:
        if mode == "glyph":
            return glyphs_to_etp_program(program, program_length=self.program_length)
        if mode == "jot":
            filtered = "".join(c for c in program if c in "01") or "0"
            return filtered if all(c in "}<>+[]01" for c in filtered) else glyphs_to_etp_program(
                filtered, program_length=self.program_length
            )
        return program

    def run_unified(
        self,
        program: str,
        *,
        envelope: Optional[RelativityEnvelope] = None,
        mirror_policy: str = "auto",
    ) -> dict[str, Any]:
        """unified_tarpit: ledger + envelope probe via ``run_etp_with_ledger``."""
        env = envelope or RelativityEnvelope(enabled=False)
        return run_etp_with_ledger(
            program,
            dimension=self.dimension,
            max_steps=self.max_steps,
            envelope=env,
            mirror_policy=mirror_policy,
        )

    def run_ecology(self, program: str) -> ComputationResult:
        """Spine ecology run (evolving_tarpit execution path)."""
        return self._ecology.run(program)

    def evolve_lineage(
        self,
        program: str,
        *,
        iterations: int = 5,
        mutation_rate: float = 0.1,
    ) -> list[ComputationResult]:
        """evolving_tarpit: multi-run mutation lineage."""
        self._ecology.load_program(program)
        return self._ecology.evolve(iterations=iterations, mutation_rate=mutation_rate)

    def start_session(
        self,
        program: str,
        mode: ExecutionMode = "etp",
    ) -> ExecutionSession:
        resolved = self.resolve_program(program, mode)
        sid = uuid.uuid4().hex[:12]
        session = ExecutionSession(
            session_id=sid,
            program=resolved,
            mode=mode,
            canonical_form=self._canonical_form_for_mode(mode),
        )
        self._sessions[sid] = session
        return session

    def execute_session(
        self,
        session_id: str,
        *,
        envelope: Optional[RelativityEnvelope] = None,
    ) -> AggregatedRun:
        session = self._sessions.get(session_id)
        if session is None:
            raise LookupError(f"session not found: {session_id}")

        try:
            if session.mode == "evolve":
                results = self.evolve_lineage(session.program, iterations=3)
                session.results = [r.to_dict() for r in results]
                best = results[-1] if results else ComputationResult()
                agg = self._aggregate_ecology_result(session.program, best, session.mode)
                session.lineage = [r.program for r in results]
            elif session.mode in ("etp", "glyph", "jot"):
                ledger_out = self.run_unified(session.program, envelope=envelope)
                eco_result = self.run_ecology(session.program)
                session.results = [ledger_out.get("summary", {}), eco_result.to_dict()]
                agg = self._merge_ledger_and_ecology(
                    session.program, ledger_out, eco_result, session.mode
                )
            else:
                raise ValueError(f"unknown mode: {session.mode}")

            session.walls.append(agg.to_dict())
            session.completed = True
            mint_tarpit_operation(
                "aggregate",
                {"session_id": session_id, "mode": session.mode, **agg.to_dict()},
                atom_id=session_id,
            )
            return agg
        except Exception as exc:  # noqa: BLE001
            session.error = str(exc)
            session.completed = False
            raise

    def _aggregate_ecology_result(
        self, program: str, result: ComputationResult, mode: str
    ) -> AggregatedRun:
        return AggregatedRun(
            program=program,
            mode=mode,
            success=result.success,
            steps=result.steps_executed,
            bonds=result.bonds_formed,
            mirrors=result.mirrors_applied,
            digital_root=result.final_digital_root,
            final_mass=result.final_mass,
            envelope_ok=True,
            ledger_rows=0,
            canonical_forms=[self._canonical_form_for_mode(mode)],  # type: ignore[arg-type]
        )

    def _merge_ledger_and_ecology(
        self,
        program: str,
        ledger_out: dict[str, Any],
        eco: ComputationResult,
        mode: str,
    ) -> AggregatedRun:
        summary = ledger_out.get("summary", {})
        ledger = ledger_out.get("ledger", [])
        final = ledger[-1] if ledger else {}
        return AggregatedRun(
            program=program,
            mode=mode,
            success=bool(summary.get("halted_now") or eco.success),
            steps=int(summary.get("steps", eco.steps_executed)),
            bonds=eco.bonds_formed,
            mirrors=eco.mirrors_applied,
            digital_root=int(
                final.get("digital_root", eco.final_digital_root)
            ),
            final_mass=float(eco.final_mass),
            envelope_ok=bool(final.get("envelope_ok", True)),
            ledger_rows=len(ledger),
            canonical_forms=["unified_tarpit", self._canonical_form_for_mode(mode)],  # type: ignore[arg-type]
        )

    def aggregate_sessions(self, session_ids: list[str]) -> dict[str, Any]:
        """Roll up multiple sessions into one report."""
        runs: list[AggregatedRun] = []
        for sid in session_ids:
            s = self._sessions.get(sid)
            if s and s.walls:
                runs.append(AggregatedRun(**s.walls[-1]))
        if not runs:
            return {"sessions": 0, "success_rate": 0.0}
        ok = sum(1 for r in runs if r.success)
        return {
            "sessions": len(runs),
            "success_rate": ok / len(runs),
            "total_steps": sum(r.steps for r in runs),
            "total_bonds": sum(r.bonds for r in runs),
            "modes": list({r.mode for r in runs}),
            "canonical_forms": sorted(
                {f for r in runs for f in r.canonical_forms}
            ),
        }

    def list_sessions(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._sessions.values()]

    def lexicon_export(self) -> dict[str, Any]:
        return {"glyphic_tarpit": GLYPH_LEXICON, "count": len(GLYPH_LEXICON)}
