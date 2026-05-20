"""
Six production methods for combining two morphons into a new child.

Each method forges a **new** morphon (new id) with ``parent`` lineage and
``payload["combination"]`` naming the method. Substrate receipts record
``evolved_from`` on the child; the controller may mint an additional spine
``BIRTH`` with parent ids when ``combine`` is invoked through
``MorphonController.combine``.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Optional

from .links import decode_link_from_payload, is_tarpit_linked, link_labels
from .morphon import Morphon


class CombineMethod(str, Enum):
    """Canonical pair-combination methods (slots 10–11)."""

    MERGE = "merge"
    CONCAT = "concat"
    QUAD = "quad"
    UNION_META = "union_meta"
    INHERIT_LINK = "inherit_link"
    PIPELINE = "pipeline"


def _base_payload(
    left: Morphon,
    right: Morphon,
    method: CombineMethod,
    extra: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "combination": method.value,
        "parents": [left.id, right.id],
        "identity_kind": "morphon",
    }
    if extra:
        body.update(extra)
    return body


def combine_merge(left: Morphon, right: Morphon) -> Morphon:
    """Shallow-merge payloads; right keys override left on collision."""
    merged = {**dict(left.payload), **dict(right.payload)}
    merged.update(_base_payload(left, right, CombineMethod.MERGE))
    return Morphon.forge(merged, parent=left.id)


def combine_concat(left: Morphon, right: Morphon, *, width: int = 8) -> Morphon:
    """Join ``concat`` fields (morphonic ingest style), pad/truncate to *width*."""
    a = str(left.payload.get("concat", ""))[:width].ljust(width, "0")
    b = str(right.payload.get("concat", ""))[:width].ljust(width, "0")
    merged = {**dict(left.payload), **dict(right.payload)}
    merged.update(
        _base_payload(
            left,
            right,
            CombineMethod.CONCAT,
            {"concat": (a + b)[: width * 2]},
        )
    )
    return Morphon.forge(merged, parent=left.id)


def combine_quad(left: Morphon, right: Morphon) -> Morphon:
    """CQE quad sum (mod 4) + digital root on the child morphon."""
    from cmplx.engine.cqe.atom import (
        digital_root_of_quad,
        parity_from_quad,
        quad_from_payload,
    )

    q_left = left.quad_encoding or quad_from_payload(left.payload)
    q_right = right.quad_encoding or quad_from_payload(right.payload)
    combined = tuple((q_left[i] + q_right[i]) % 4 + 1 for i in range(4))
    merged = _base_payload(
        left,
        right,
        CombineMethod.QUAD,
        {
            "quad_encoding": list(combined),
            "digital_root": digital_root_of_quad(combined),
            "parity_channels": list(parity_from_quad(combined)),
        },
    )
    child = Morphon.forge(merged, parent=left.id)
    child.quad_encoding = combined
    child.parity_channels = parity_from_quad(combined)
    child.digital_root = digital_root_of_quad(combined)
    return child


def combine_union_meta(left: Morphon, right: Morphon) -> Morphon:
    """Union of receipt operation names + cached geometry without merging bodies."""
    ops = sorted({r.operation for r in left.receipts} | {r.operation for r in right.receipts})
    merged = _base_payload(
        left,
        right,
        CombineMethod.UNION_META,
        {
            "receipt_operations": ops,
            "left_payload_keys": sorted(left.payload.keys()),
            "right_payload_keys": sorted(right.payload.keys()),
        },
    )
    child = Morphon.forge(merged, parent=left.id)
    if left.dr_channel is not None or right.dr_channel is not None:
        child.dr_channel = left.dr_channel or right.dr_channel
    if left.e8_coordinates is not None:
        child.e8_coordinates = left.e8_coordinates
    elif right.e8_coordinates is not None:
        child.e8_coordinates = right.e8_coordinates
    return child


def combine_inherit_link(left: Morphon, right: Morphon) -> Morphon:
    """Child morphon with explicit TarPit labels inherited from first linked parent."""
    merged = _base_payload(left, right, CombineMethod.INHERIT_LINK)
    child = Morphon.forge(merged, parent=left.id)
    for source in (left, right):
        if not is_tarpit_linked(source.payload):
            continue
        link = decode_link_from_payload(source.payload)
        if not link:
            continue
        labels = link_labels(
            child,
            tarpit_atom_id=link["tarpit_atom_id"],
            derivation_hash=link["derivation_hash"],
            tarpit_program=link["tarpit_program"],
        )
        labels["linkage_sources"] = [left.id, right.id]
        labels["linkage_inherited_from"] = source.id
        return child.annotate_links(**labels)
    return child


def combine_pipeline(left: Morphon, right: Morphon, **pipeline_kw: Any) -> dict[str, Any]:
    """Merge payloads then run ``MorphonSubstrateProvider.pipeline``."""
    merged = {**dict(left.payload), **dict(right.payload)}
    merged.update(_base_payload(left, right, CombineMethod.PIPELINE))
    from .substrate import MorphonSubstrateProvider

    return MorphonSubstrateProvider().pipeline(merged, **pipeline_kw)


_COMBINERS = {
    CombineMethod.MERGE: combine_merge,
    CombineMethod.CONCAT: combine_concat,
    CombineMethod.QUAD: combine_quad,
    CombineMethod.UNION_META: combine_union_meta,
    CombineMethod.INHERIT_LINK: combine_inherit_link,
}


def combine_pair(
    left: Morphon,
    right: Morphon,
    method: CombineMethod | str,
    **kwargs: Any,
) -> Morphon | dict[str, Any]:
    """Dispatch a pair combination. ``PIPELINE`` returns a pipeline result dict."""
    if isinstance(method, str):
        method = CombineMethod(method)
    if method is CombineMethod.PIPELINE:
        return combine_pipeline(left, right, **kwargs)
    fn = _COMBINERS[method]
    if method is CombineMethod.CONCAT:
        return fn(left, right, **{k: v for k, v in kwargs.items() if k == "width"})
    return fn(left, right)
