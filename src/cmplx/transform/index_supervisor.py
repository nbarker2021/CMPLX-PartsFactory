"""
IndexSupervisor — walk superpermutation cursor and apply compose stubs.

Maps SP digits to compose actions before Slot 48 forward. Palindrome
phases query ``TemplateFrame`` partial templates to measure forced-cell
gain without full alphabet enumeration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from cmplx.primitives.n5_octad import N5OctadSchedule, load_n5_octad_schedule
from cmplx.primitives.superperm import SUPERPERM_N4, superperm_n

from .index_mutations import abstract, convolve, involute
from .nhyper_tower import active_n_from_manifest, tower_level_for_supervisor
from .octad import OctadSheet, octad_phase_at
from .token_index.template_frame import AdmitSet, ForcedCellReport, TemplateFrame


class ComposeAction(str, Enum):
    TEMPLATE = "template"
    CONVOLVE = "convolve"
    INVOLUTE = "involute"
    ABSTRACT = "abstract"


_DIGIT_ACTION: dict[str, ComposeAction] = {
    "1": ComposeAction.TEMPLATE,
    "2": ComposeAction.CONVOLVE,
    "3": ComposeAction.INVOLUTE,
    "4": ComposeAction.ABSTRACT,
}


@dataclass
class SupervisorStep:
    index: int
    digit: str
    phase: int
    slot_id: str
    action: ComposeAction
    pattern: Optional[str] = None
    admit: Optional[AdmitSet] = None
    forced: bool = False
    sp_label: Optional[str] = None
    alternate_index: Optional[int] = None
    journal_ref: Optional[str] = None
    is_palindrome_sp: bool = False

    def as_dict(self) -> dict:
        out = {
            "index": self.index,
            "digit": self.digit,
            "phase": self.phase,
            "slot_id": self.slot_id,
            "action": self.action.value,
            "pattern": self.pattern,
            "admit_size": self.admit.size if self.admit else 0,
            "completion_count": self.admit.completion_count if self.admit else 0,
            "forced": self.forced,
        }
        if self.sp_label is not None:
            out["sp_label"] = self.sp_label
        if self.alternate_index is not None:
            out["alternate_index"] = self.alternate_index
        if self.journal_ref is not None:
            out["journal_ref"] = self.journal_ref
        if self.is_palindrome_sp:
            out["is_palindrome_sp"] = True
        return out


@dataclass
class IndexSupervisorRun:
    steps: list[SupervisorStep] = field(default_factory=list)
    palindrome_forced: int = 0
    palindrome_template_steps: int = 0
    tower_level: Optional[int] = None
    active_n: int = 4
    sp_length: int = 0
    n5_octad: bool = False
    octad_slots_used: list[str] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "total_steps": len(self.steps),
            "palindrome_forced": self.palindrome_forced,
            "palindrome_template_steps": self.palindrome_template_steps,
            "tower_level": self.tower_level,
            "active_n": self.active_n,
            "sp_length": self.sp_length,
            "n5_octad": self.n5_octad,
            "octad_slots_used": self.octad_slots_used,
            "steps": [s.as_dict() for s in self.steps],
            "events": self.events,
        }


def _resolve_sp(*, active_n: int, sp: Optional[str] = None) -> tuple[str, int]:
    n = int(active_n)
    if sp is not None:
        return sp, n
    if n == 4:
        try:
            return superperm_n(4), 4
        except ValueError:
            return SUPERPERM_N4, 4
    return superperm_n(n), n


def _octad_phase(index: int, *, active_n: int) -> int:
    """n=4 uses octad sheet; n>4 uses modulo-8 scheduling (v1)."""
    if active_n <= 4:
        return octad_phase_at(index)
    return index % 8


class IndexSupervisor:
    """Walk SP string and map each digit to a compose action."""

    def __init__(
        self,
        template_frame: TemplateFrame,
        *,
        octad: Optional[OctadSheet] = None,
        sp: Optional[str] = None,
        active_n: int = 4,
        case_mode: str = "lower",
        language: Optional[str] = None,
        db_path: Optional[str] = None,
        register_ports: bool = False,
        run_mutations: bool = True,
        tower_level: Optional[int] = None,
    ) -> None:
        self.frame = template_frame
        self.db_path = db_path or getattr(template_frame, "db_path", None)
        self.register_ports = register_ports
        self.run_mutations = run_mutations
        self.tower_level = tower_level
        self.active_n = int(active_n)
        self.n5_schedule: Optional[N5OctadSchedule] = None
        if self.active_n == 5 and sp is None:
            try:
                self.n5_schedule = load_n5_octad_schedule()
                self.sp = self.n5_schedule.palindrome_slot().superpermutation
                self.active_n = 5
            except ValueError:
                self.sp, self.active_n = _resolve_sp(active_n=active_n, sp=sp)
        else:
            self.sp, self.active_n = _resolve_sp(active_n=active_n, sp=sp)
        self.case_mode = case_mode
        self.language = language
        self.octad = octad or OctadSheet.for_active_n(self.active_n)

    @classmethod
    def from_db(
        cls,
        db_path: str | Path,
        *,
        octad: Optional[OctadSheet] = None,
        sp: Optional[str] = None,
        active_n: int = 4,
        case_mode: str = "lower",
        language: Optional[str] = None,
        tower_level: Optional[int] = None,
        run_mutations: bool = True,
    ) -> "IndexSupervisor":
        return cls(
            TemplateFrame(db_path),
            octad=octad,
            sp=sp,
            active_n=active_n,
            case_mode=case_mode,
            language=language,
            db_path=str(db_path),
            tower_level=tower_level,
            run_mutations=run_mutations,
        )

    @classmethod
    def from_manifest(
        cls,
        db_path: str | Path,
        manifest: dict,
        *,
        octad: Optional[OctadSheet] = None,
        sp: Optional[str] = None,
        active_n: Optional[int] = None,
        tower_level: Optional[int] = None,
        run_mutations: bool = True,
    ) -> "IndexSupervisor":
        """Build supervisor using crystal ``nhyper_tower`` / superperm manifest."""
        resolved_level = tower_level_for_supervisor(manifest, override=tower_level)
        resolved_n = active_n if active_n is not None else active_n_from_manifest(
            manifest, tower_level=resolved_level
        )
        return cls.from_db(
            db_path,
            octad=octad,
            sp=sp,
            active_n=resolved_n,
            tower_level=resolved_level,
            run_mutations=run_mutations,
        )

    def _allows_template_query(self, digit: str, phase: int) -> bool:
        """Tower level gates template depth (doctrine: level caps bond-depth proxy)."""
        if self.tower_level is None:
            return True
        try:
            d = int(digit)
        except ValueError:
            return False
        if d > self.active_n:
            return False
        if self.tower_level == 0:
            return d <= 4
        return d <= min(self.active_n, self.tower_level + 4)

    def walk(self, partial_seed: Optional[str] = None) -> IndexSupervisorRun:
        if self.n5_schedule is not None:
            return self._walk_n5_octad(partial_seed)
        return self._walk_single_sp(partial_seed)

    def _walk_n5_octad(self, partial_seed: Optional[str] = None) -> IndexSupervisorRun:
        schedule = self.n5_schedule
        assert schedule is not None
        run = IndexSupervisorRun(
            tower_level=self.tower_level,
            active_n=5,
            sp_length=schedule.walk_length,
            n5_octad=True,
            octad_slots_used=[s.slot_id for s in schedule.slots],
        )
        mutation_done: set[ComposeAction] = set()
        tree_phases_seen: set[int] = set()
        for i in range(schedule.walk_length):
            phase, digit_char, slot = schedule.digit_at_step(i)
            digit = digit_char
            slot_id = slot.slot_id
            action = _DIGIT_ACTION.get(digit, ComposeAction.ABSTRACT)
            step = SupervisorStep(
                index=i,
                digit=digit,
                phase=phase,
                slot_id=slot_id,
                action=action,
                sp_label=slot.label,
                alternate_index=slot.alternate_index,
                journal_ref=slot.journal_ref,
                is_palindrome_sp=slot.is_palindrome,
            )
            if action is ComposeAction.TEMPLATE and self._allows_template_query(digit, phase):
                pattern = self._partial_pattern_n5(digit, phase=phase)
                if partial_seed:
                    seed_pat = partial_seed[:8].ljust(8, "?")
                    if phase == 0 or not pattern:
                        pattern = seed_pat
                    else:
                        merged = list(pattern)
                        for pos, ch in enumerate(seed_pat):
                            if ch != "?" and pos < len(merged):
                                merged[pos] = ch
                        pattern = "".join(merged)
                step.pattern = pattern
                if pattern:
                    admit = self.frame.admit_set_by_partial(
                        pattern,
                        case_mode=self.case_mode,
                        language=self.language,
                    )
                    step.admit = admit
                    step.forced = admit.is_forced
                    if phase == 0:
                        run.palindrome_template_steps += 1
                        if admit.is_forced:
                            run.palindrome_forced += 1
                    elif phase not in tree_phases_seen:
                        tree_phases_seen.add(phase)
            mutation_payload = None
            if (
                self.run_mutations
                and self.db_path
                and action in (ComposeAction.CONVOLVE, ComposeAction.INVOLUTE, ComposeAction.ABSTRACT)
                and action not in mutation_done
            ):
                mutation_done.add(action)
                mutation_payload = self._run_mutation(action)
            run.steps.append(step)
            event: dict = {
                "index": i,
                "phase": phase,
                "slot_id": slot_id,
                "action": action.value,
                "forced": step.forced,
                "tower_level": self.tower_level,
                "active_n": 5,
                "sp_label": slot.label,
                "alternate_index": slot.alternate_index,
                "journal_ref": slot.journal_ref,
                "is_palindrome_sp": slot.is_palindrome,
            }
            if mutation_payload is not None:
                event["mutation"] = mutation_payload
            run.events.append(event)
        return run

    def _partial_pattern_n5(self, digit: str, *, phase: int) -> Optional[str]:
        schedule = self.n5_schedule
        if schedule is None:
            return self.octad.partial_pattern(digit, phase=phase)
        letter_map = schedule.digit_to_letter
        letter = letter_map.get(digit, self.octad.letter_for_digit(digit))
        if phase % 8 == 0:
            return f"{letter}??????{letter}"
        return f"{letter}???????"

    def _walk_single_sp(self, partial_seed: Optional[str] = None) -> IndexSupervisorRun:
        run = IndexSupervisorRun(
            tower_level=self.tower_level,
            active_n=self.active_n,
            sp_length=len(self.sp),
        )
        mutation_done: set[ComposeAction] = set()
        for i, digit in enumerate(self.sp):
            phase = _octad_phase(i, active_n=self.active_n)
            slot_id = self.octad.slot_id(phase)
            action = _DIGIT_ACTION.get(digit, ComposeAction.ABSTRACT)
            step = SupervisorStep(
                index=i,
                digit=digit,
                phase=phase,
                slot_id=slot_id,
                action=action,
            )
            if action is ComposeAction.TEMPLATE and self._allows_template_query(digit, phase):
                pattern = self.octad.partial_pattern(digit, phase=phase)
                if partial_seed:
                    seed_pat = partial_seed[:8].ljust(8, "?")
                    if phase == 0 or not pattern:
                        pattern = seed_pat
                    else:
                        merged = list(pattern)
                        for pos, ch in enumerate(seed_pat):
                            if ch != "?" and pos < len(merged):
                                merged[pos] = ch
                        pattern = "".join(merged)
                step.pattern = pattern
                if pattern:
                    admit = self.frame.admit_set_by_partial(
                        pattern,
                        case_mode=self.case_mode,
                        language=self.language,
                    )
                    step.admit = admit
                    step.forced = admit.is_forced
                    if phase == 0:
                        run.palindrome_template_steps += 1
                        if admit.is_forced:
                            run.palindrome_forced += 1
            mutation_payload = None
            if (
                self.run_mutations
                and self.db_path
                and action in (ComposeAction.CONVOLVE, ComposeAction.INVOLUTE, ComposeAction.ABSTRACT)
                and action not in mutation_done
            ):
                mutation_done.add(action)
                mutation_payload = self._run_mutation(action)
            run.steps.append(step)
            event: dict = {
                "index": i,
                "phase": phase,
                "slot_id": slot_id,
                "action": action.value,
                "forced": step.forced,
                "tower_level": self.tower_level,
                "active_n": self.active_n,
            }
            if mutation_payload is not None:
                event["mutation"] = mutation_payload
            run.events.append(event)
        return run

    def _run_mutation(self, action: ComposeAction) -> dict:
        if self.db_path is None:
            return {"skipped": "no_db_path"}
        if action is ComposeAction.CONVOLVE:
            return convolve(
                self.db_path, register_ports=self.register_ports
            ).as_dict()
        if action is ComposeAction.INVOLUTE:
            return involute(
                self.db_path, register_ports=self.register_ports
            ).as_dict()
        if action is ComposeAction.ABSTRACT:
            return abstract(self.db_path).as_dict()
        return {"skipped": action.value}

    def forced_cell_report(self) -> dict:
        """Compare baseline sweep vs palindrome-template constrained steps."""
        baseline: ForcedCellReport = self.frame.forced_cell_sweep(
            n_samples=100,
            case_mode=self.case_mode,
            language=self.language,
        )
        run = self.walk()
        return {
            "baseline_forced_pct": baseline.as_dict()["forced_pct"],
            "palindrome_forced_steps": run.palindrome_forced,
            "palindrome_template_steps": run.palindrome_template_steps,
            "supervisor_forced_gain": run.palindrome_forced,
            "tower_level": self.tower_level,
            "active_n": self.active_n,
            "sp_length": run.sp_length,
            "run": run.as_dict(),
        }


__all__ = [
    "ComposeAction",
    "SupervisorStep",
    "IndexSupervisorRun",
    "IndexSupervisor",
]
