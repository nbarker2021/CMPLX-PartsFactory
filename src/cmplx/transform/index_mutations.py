"""
Index mutations — convolve, involute, abstract, and refine coverage loops.

Used by ``IndexSupervisor`` compose steps (digits 2–4) and the ``refine`` CLI.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

from cmplx.morphon import Morphon
from cmplx.primitives.core import NLAECNFChain

from .bridge import ensure_bootstrapped, get_cache_provider, has_provider
from .meaning_store import AddressMeaningStore
from .token_index.bonds import DEFAULT_ALPHABET, QuadBond, enumerate_bonds
from .token_index.case import CaseMode
from .token_index.store import TokenIndexStore
from .token_index.template_frame import SlotCoverage, TemplateFrame
from .token_index.warmstart import (
    IndexEntryPayload,
    WarmStartLookup,
    WarmStartOutcome,
    key_exact,
    predecessor_concat,
    publish_entry,
)

logger = logging.getLogger(__name__)


@dataclass
class MutationStats:
    action: str
    bonds_touched: int = 0
    warmstart_published: int = 0
    bonds_seeded: int = 0
    meanings_collapsed: int = 0
    notes: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "bonds_touched": self.bonds_touched,
            "warmstart_published": self.warmstart_published,
            "bonds_seeded": self.bonds_seeded,
            "meanings_collapsed": self.meanings_collapsed,
            "notes": self.notes,
        }


def aggregate_slot_coverage_fraction(cov: SlotCoverage) -> float:
    """Mean per-slot coverage as a fraction in [0, 1]."""
    if not cov.seen:
        return 0.0
    total_pct = sum(
        cov.coverage_pct(level, pos, case_mode)
        for level, pos, case_mode in cov.seen
    )
    return total_pct / (100.0 * len(cov.seen))


def convolve(
    db_path: str | Path,
    *,
    register_ports: bool = False,
    limit: Optional[int] = None,
) -> MutationStats:
    """Publish warm-start neighbor hints for every bond row (DR + lane buckets)."""
    stats = MutationStats(action="convolve")
    if register_ports:
        ensure_bootstrapped()
    cache = get_cache_provider() if has_provider("cache") else None
    store = TokenIndexStore(db_path)
    try:
        sql = (
            "SELECT concat, bond_level, case_mode, language, stream, "
            "morphon_id, snap_key, digital_root, lane "
            "FROM token_bonds"
        )
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        cur = store._conn.execute(sql)
        for row in cur.fetchall():
            concat, level, case_mode, language, stream, morphon_id, snap_key, dr, lane = row
            canonical = NLAECNFChain.full_chain(str(concat))
            payload = IndexEntryPayload(
                concat=str(concat),
                morphon_id=str(morphon_id),
                snap_key=str(snap_key),
                e8_coords=tuple(float(c) for c in canonical["e8_coords"]),
                digital_root=int(dr),
                lane=str(lane),
                cache_key=key_exact(str(concat)),
                level=int(level),
                case_mode=str(case_mode),
                language=str(language),
                warmstart_outcome=WarmStartOutcome.NEIGHBOR.value,
            )
            try:
                cm = CaseMode(case_mode)
            except ValueError:
                cm = CaseMode.LOWER
            publish_entry(cache, payload, cm)
            stats.warmstart_published += 1
            stats.bonds_touched += 1
    finally:
        store.close()
    return stats


def involute(
    db_path: str | Path,
    *,
    alphabet: Sequence[str] = DEFAULT_ALPHABET,
    register_ports: bool = False,
    max_seed: Optional[int] = 5000,
) -> MutationStats:
    """Seed missing L2/L3 bond rows from existing L1 predecessors."""
    stats = MutationStats(action="involute")
    if register_ports:
        ensure_bootstrapped()
    cache = get_cache_provider() if has_provider("cache") else None
    lookup = WarmStartLookup(cache)
    store = TokenIndexStore(db_path)
    try:
        cur = store._conn.execute(
            "SELECT DISTINCT concat, case_mode, language, stream "
            "FROM token_bonds WHERE bond_level = 1"
        )
        l1_rows = cur.fetchall()
        for target_level in (2, 3):
            for concat, case_mode, language, stream in l1_rows:
                bond_l1 = QuadBond(
                    quad_left=str(concat)[:4],
                    quad_right=str(concat)[4:],
                    level=1,
                )
                for bond in enumerate_bonds(target_level, alphabet=alphabet):
                    pred = predecessor_concat(bond)
                    if pred != bond_l1.concat:
                        continue
                    try:
                        cm = CaseMode(case_mode)
                    except ValueError:
                        cm = CaseMode.LOWER
                    cased = bond
                    if store.by_concat(bond.concat, stream=stream):
                        continue
                    hit = lookup.probe(bond, cm)
                    if hit.outcome is WarmStartOutcome.EXACT:
                        continue
                    canonical = NLAECNFChain.full_chain(bond.concat)
                    morphon = Morphon.forge(
                        payload={
                            "concat": bond.concat,
                            "snap_key": str(canonical["snap_key"]),
                            "involute_from": bond_l1.concat,
                        },
                        parent=None,
                    )
                    morphon.e8_coordinates = tuple(float(c) for c in canonical["e8_coords"])
                    payload = IndexEntryPayload(
                        concat=bond.concat,
                        morphon_id=morphon.id,
                        snap_key=str(canonical["snap_key"]),
                        e8_coords=tuple(float(c) for c in canonical["e8_coords"]),
                        digital_root=int(canonical["digital_root"]),
                        lane=str(canonical["lane"]),
                        cache_key=key_exact(bond.concat),
                        level=target_level,
                        case_mode=cm.value,
                        language=str(language),
                        warmstart_outcome=WarmStartOutcome.PREDECESSOR.value,
                        parent_morphon_id=None,
                    )
                    store.upsert(
                        payload,
                        bond_level=target_level,
                        case_mode=cm.value,
                        language=str(language),
                        stream=str(stream),
                    )
                    publish_entry(cache, payload, cm)
                    stats.bonds_seeded += 1
                    if max_seed is not None and stats.bonds_seeded >= max_seed:
                        stats.notes["capped"] = max_seed
                        return stats
        stats.bonds_touched = len(l1_rows)
    finally:
        store.close()
    return stats


def abstract(db_path: str | Path) -> MutationStats:
    """Collapse duplicate labels per snap_key into representative + alias rows."""
    stats = MutationStats(action="abstract")
    meaning = AddressMeaningStore(db_path)
    try:
        cur = meaning._conn.execute(
            "SELECT snap_key, lane, digital_root, label, source_doc "
            "FROM address_meaning ORDER BY snap_key, label"
        )
        groups: dict[tuple[str, str, int], list[tuple[str, Optional[str]]]] = {}
        for snap_key, lane, dr, label, doc in cur.fetchall():
            key = (str(snap_key), str(lane), int(dr))
            groups.setdefault(key, []).append((str(label), doc))

        for (snap_key, lane, dr), labels in groups.items():
            unique = sorted({lbl for lbl, _ in labels})
            if len(unique) <= 1:
                continue
            representative = min(unique, key=len)
            for label in unique:
                if label == representative:
                    continue
                meaning.upsert(
                    snap_key=snap_key,
                    lane=lane,
                    digital_root=dr,
                    label=f"@{representative}",
                    label_source=f"alias:{label}",
                    source_doc=None,
                    source_span=f"abstract:{label}",
                )
                stats.meanings_collapsed += 1
            stats.bonds_touched += 1
    finally:
        meaning.close()
    return stats


def refine_to_coverage(
    db_path: str | Path,
    target_coverage: float,
    *,
    max_rounds: int = 5,
    register_ports: bool = False,
    convolve_limit: Optional[int] = None,
) -> dict[str, Any]:
    """Run mutation rounds until mean slot coverage reaches ``target_coverage``."""
    frame = TemplateFrame(db_path)
    try:
        rounds: list[dict[str, Any]] = []
        start_cov = aggregate_slot_coverage_fraction(frame.slot_coverage())
        cov = start_cov
        for i in range(max_rounds):
            if cov >= target_coverage:
                break
            round_stats = {
                "round": i + 1,
                "coverage_before": round(cov, 4),
                "mutations": [],
            }
            for mutator in (convolve, involute, abstract):
                if mutator is abstract:
                    result = mutator(db_path)
                elif mutator is convolve:
                    result = mutator(
                        db_path,
                        register_ports=register_ports,
                        limit=convolve_limit,
                    )
                else:
                    result = mutator(db_path, register_ports=register_ports)
                round_stats["mutations"].append(result.as_dict())
            cov = aggregate_slot_coverage_fraction(frame.slot_coverage())
            round_stats["coverage_after"] = round(cov, 4)
            rounds.append(round_stats)
        return {
            "target_coverage": target_coverage,
            "coverage_start": round(start_cov, 4),
            "coverage_end": round(cov, 4),
            "reached_target": cov >= target_coverage,
            "rounds": rounds,
        }
    finally:
        frame.close()


__all__ = [
    "MutationStats",
    "aggregate_slot_coverage_fraction",
    "convolve",
    "involute",
    "abstract",
    "refine_to_coverage",
]
