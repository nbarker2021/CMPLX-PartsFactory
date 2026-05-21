"""
Morphon payload → SNAP label context (slot-17 ↔ slots 10–11).

When labeling during transform ingest or via ``SNAPEngine``, pass
``label_context_from_morphon`` so ``linkage_kind``, ``morphon_id``, and
``tarpit_atom_id`` appear on the ``SNAPLabel`` custom dimensions.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from .label import SNAPLabel

try:
    from cmplx.morphon import Morphon
    from cmplx.morphon.links import (
        KEY_IDENTITY_KIND,
        KEY_LINKAGE_KIND,
        KEY_MORPHON_ID,
        KEY_TARPIT_ATOM_ID,
        KEY_TARPIT_DERIVATION_HASH,
        KEY_TARPIT_PROGRAM,
        LINKAGE_MORPHON_TARPIT,
        decode_link_from_payload,
        is_tarpit_linked,
    )
except ImportError:  # pragma: no cover
    Morphon = Any  # type: ignore[misc, assignment]


def label_context_from_morphon(
    morphon: "Morphon",
    *,
    base: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Build a SNAP labeler ``context`` dict from a morphon payload."""
    payload = dict(morphon.payload)
    ctx: dict[str, Any] = dict(base or {})
    ctx["morphon_id"] = morphon.id
    if payload.get("snap_key") is not None:
        ctx["snap_key"] = str(payload["snap_key"])
    if payload.get("concat") is not None:
        ctx["concat"] = str(payload["concat"])
    if payload.get(KEY_IDENTITY_KIND):
        ctx[KEY_IDENTITY_KIND] = str(payload[KEY_IDENTITY_KIND])
    if is_tarpit_linked(payload):
        ctx[KEY_LINKAGE_KIND] = LINKAGE_MORPHON_TARPIT
        ctx[KEY_MORPHON_ID] = str(payload.get(KEY_MORPHON_ID, morphon.id))
        ctx[KEY_TARPIT_ATOM_ID] = str(payload.get(KEY_TARPIT_ATOM_ID, ""))
        if payload.get(KEY_TARPIT_DERIVATION_HASH):
            ctx[KEY_TARPIT_DERIVATION_HASH] = str(payload[KEY_TARPIT_DERIVATION_HASH])
        if payload.get(KEY_TARPIT_PROGRAM):
            ctx[KEY_TARPIT_PROGRAM] = str(payload[KEY_TARPIT_PROGRAM])
        if payload.get("linkage_inherited_from"):
            ctx["linkage_inherited_from"] = str(payload["linkage_inherited_from"])
    if payload.get("combination"):
        ctx["combination"] = str(payload["combination"])
    if payload.get("parents"):
        ctx["parents"] = list(payload["parents"])
    return ctx


def enrich_label_from_morphon(label: SNAPLabel, morphon: "Morphon") -> SNAPLabel:
    """Merge morphon linkage fields into an existing ``SNAPLabel``."""
    payload = morphon.payload
    if payload.get("snap_key"):
        label.custom.setdefault("snap_key", set()).add(str(payload["snap_key"]))
    if payload.get("concat"):
        label.custom.setdefault("concat", set()).add(str(payload["concat"]))
    label.custom.setdefault("morphon_id", set()).add(morphon.id)
    if payload.get(KEY_IDENTITY_KIND):
        label.custom.setdefault(KEY_IDENTITY_KIND, set()).add(str(payload[KEY_IDENTITY_KIND]))
    if is_tarpit_linked(payload):
        label.semantic.add("tarpit_linked")
        label.custom.setdefault(KEY_LINKAGE_KIND, set()).add(LINKAGE_MORPHON_TARPIT)
        label.custom.setdefault(KEY_TARPIT_ATOM_ID, set()).add(
            str(payload.get(KEY_TARPIT_ATOM_ID, ""))
        )
        if payload.get(KEY_TARPIT_DERIVATION_HASH):
            label.custom.setdefault(KEY_TARPIT_DERIVATION_HASH, set()).add(
                str(payload[KEY_TARPIT_DERIVATION_HASH])
            )
    if payload.get("combination") == "inherit_link":
        label.semantic.add("morphon_bond")
    return label
