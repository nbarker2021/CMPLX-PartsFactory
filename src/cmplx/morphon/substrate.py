"""
Morphon substrate provider — production entry for slots 10–11.

Not registered on ``MorphonController`` (the controller *is* the registry).
Use this for datum → morphon → optional symbolic/TarPit link → admit/store.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from .controller import MorphonController
from .links import (
    KEY_TARPIT_PROGRAM,
    decode_link_from_payload,
    is_tarpit_linked,
    link_morphon_to_tarpit_atom,
)
from .morphon import Morphon, MorphonState


class MorphonSubstrateProvider:
    """Production orchestration for morphon-based atoms."""

    name: str = "morphon_substrate"

    def materialize(
        self,
        payload: Mapping[str, Any],
        *,
        parent: Optional[str] = None,
        morphon_id: Optional[str] = None,
    ) -> Morphon:
        """Datum → morphon (BIRTH receipt when receipt port registered)."""
        return Morphon.forge(payload, parent=parent, morphon_id=morphon_id)

    def encode_program(self, morphon: Morphon) -> str:
        ctrl = MorphonController.get()
        symbolic = ctrl.get_provider("symbolic")
        return symbolic.encode_to_etp(morphon)

    def derive_symbolic(self, morphon: Morphon) -> Any:
        """Run symbolic port derive (ETP ledger + ecology report)."""
        ctrl = MorphonController.get()
        return ctrl.get_provider("symbolic").derive(morphon)

    def link_tarpit(
        self,
        morphon: Morphon,
        *,
        program: Optional[str] = None,
    ) -> tuple[Morphon, dict[str, Any]]:
        """Probe TarPit atom and write explicit linkage labels on morphon."""
        ctrl = MorphonController.get()
        symbolic = ctrl.get_provider("symbolic")
        prog = program or self.encode_program(morphon)
        if hasattr(symbolic, "probe_atom_for_morphon"):
            atom_out, linked = symbolic.probe_atom_for_morphon(morphon, prog)
            return linked, atom_out
        atom_out = symbolic.aggregator.probe_atom(prog)  # type: ignore[attr-defined]
        linked = link_morphon_to_tarpit_atom(morphon, atom_out, tarpit_program=prog)
        return linked, atom_out

    def pipeline(
        self,
        payload: Mapping[str, Any],
        *,
        link_tarpit: bool = True,
        admit_and_store: bool = False,
    ) -> dict[str, Any]:
        """Datum → morphon → [ETP derive] → [tarpit link] → [admit_and_store]."""
        morphon = self.materialize(payload)
        out: dict[str, Any] = {
            "morphon_id": morphon.id,
            "identity_kind": morphon.payload.get("identity_kind"),
        }
        program = self.encode_program(morphon)
        out["tarpit_program"] = program
        morphon = morphon.annotate_links(**{KEY_TARPIT_PROGRAM: program})

        report = self.derive_symbolic(morphon)
        out["symbolic_summary"] = getattr(report, "summary", {}) or {}

        if link_tarpit:
            morphon, atom_out = self.link_tarpit(morphon, program=program)
            out["tarpit_atom"] = atom_out.get("atom")
            out["linkage"] = decode_link_from_payload(morphon.payload)
            out["linkage_explicit"] = is_tarpit_linked(morphon.payload)

        if admit_and_store:
            ctrl = MorphonController.get()
            morphon = ctrl.admit_and_store(morphon)
            out["admitted"] = True

        out["morphon_id"] = morphon.id
        out["state"] = morphon.state.name
        return out

    def transition(self, morphon: Morphon, state: MorphonState) -> Morphon:
        return morphon.transition_to(state)
