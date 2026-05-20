"""
Explicit cross-system linkage labels on Morphon payloads.

When a morphon is tied to a TarPit ``Atom``, both ids must appear in the
payload with ``linkage_kind="morphon_tarpit"`` so downstream SNAP/MDHG/
receipt consumers never conflate substrate UUID with tarpit atom_id.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from .morphon import Morphon

# Payload keys (stable contract for registers + ports)
KEY_IDENTITY_KIND = "identity_kind"
KEY_LINKAGE_KIND = "linkage_kind"
KEY_MORPHON_ID = "morphon_id"
KEY_TARPIT_ATOM_ID = "tarpit_atom_id"
KEY_TARPIT_DERIVATION_HASH = "tarpit_derivation_hash"
KEY_TARPIT_PROGRAM = "tarpit_program"

LINKAGE_MORPHON_TARPIT = "morphon_tarpit"
IDENTITY_MORPHON = "morphon"
IDENTITY_MORPHON_ETP_DERIVED = "morphon_etp_derived"


def is_tarpit_linked(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get(KEY_LINKAGE_KIND) == LINKAGE_MORPHON_TARPIT
        and bool(payload.get(KEY_TARPIT_ATOM_ID))
        and bool(payload.get(KEY_MORPHON_ID))
    )


def link_labels(
    morphon: Morphon,
    *,
    tarpit_atom_id: str,
    derivation_hash: str = "",
    tarpit_program: str = "",
) -> dict[str, Any]:
    """Build explicit linkage fields for a morphon payload."""
    return {
        KEY_LINKAGE_KIND: LINKAGE_MORPHON_TARPIT,
        KEY_MORPHON_ID: morphon.id,
        KEY_TARPIT_ATOM_ID: tarpit_atom_id,
        KEY_TARPIT_DERIVATION_HASH: derivation_hash,
        KEY_TARPIT_PROGRAM: tarpit_program,
    }


def link_morphon_to_tarpit_atom(
    morphon: Morphon,
    atom_probe: Mapping[str, Any],
    *,
    tarpit_program: str = "",
) -> Morphon:
    """Annotate *morphon* (same id) with explicit TarPit atom linkage."""
    atom = atom_probe.get("atom") or {}
    if isinstance(atom, Mapping):
        tarpit_atom_id = str(atom.get("atom_id", ""))
    else:
        tarpit_atom_id = ""
    derivation_hash = str(atom_probe.get("derivation_hash", ""))
    program = tarpit_program or str(morphon.payload.get(KEY_TARPIT_PROGRAM, ""))
    labels = link_labels(
        morphon,
        tarpit_atom_id=tarpit_atom_id,
        derivation_hash=derivation_hash,
        tarpit_program=program,
    )
    return morphon.annotate_links(**labels)


def decode_link_from_payload(payload: Mapping[str, Any]) -> Optional[dict[str, str]]:
    """Read linkage back from a serialized morphon payload."""
    if not is_tarpit_linked(payload):
        return None
    return {
        "morphon_id": str(payload.get(KEY_MORPHON_ID, "")),
        "tarpit_atom_id": str(payload.get(KEY_TARPIT_ATOM_ID, "")),
        "derivation_hash": str(payload.get(KEY_TARPIT_DERIVATION_HASH, "")),
        "tarpit_program": str(payload.get(KEY_TARPIT_PROGRAM, "")),
    }
