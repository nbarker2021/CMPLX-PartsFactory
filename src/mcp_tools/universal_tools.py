"""
CMPLX MCP Universal Tools
=========================
Ported from CMPLXMCP/server/universal_tools.py.
Universal Translator, Crystal Storage, Temporal Layer, Identity Family.

Integrates with:
  - governance.engine — GeometricGovernance for boundary event audit
  - services.registry — ServiceRegistry for Docker service clients
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from governance.engine import GeometricGovernance, BoundaryEvent
from services.registry import registry

from .layer_tools import generate_handle, resolve_handle

logger = logging.getLogger("cmplx.mcp.universal")

_governance = GeometricGovernance()


def _audit_tool_call(tool_name: str, args: dict, result: dict) -> None:
    event = BoundaryEvent(
        event_id=f"{tool_name}_{hashlib.sha256(json.dumps(args, sort_keys=True, default=str).encode()).hexdigest()[:12]}",
        timestamp=datetime.utcnow().timestamp(),
        entropy_delta=0.0,
        receipt_data={"tool": tool_name, "result_summary": str(result.get("crystal_id", result.get("handle", "")))},
        boundary_type="mcp_universal_tool",
    )
    _governance.record_boundary_event(event)


class UniversalTools:
    """
    Universal System tools for MCP.

    Connects to the Universal Translator, Crystal Lattice,
    Temporal Layer, and Identity Family systems.
    """

    def __init__(self):
        self._translator = None
        self._lattice = None
        self._temporal = None
        self._identity_family = None

    def _init_systems(self, data_root: Path) -> None:
        if self._translator is None:
            try:
                from cmplx_toolkit.unified_families.cmplx.universal import (
                    UniversalTranslator, CrystalLattice, TemporalLayer, IdentityFamily,
                )
            except ImportError:
                logger.warning("Universal family imports unavailable; using stubs")
                return

            self._translator = UniversalTranslator()
            self._lattice = CrystalLattice(data_root / "crystal_lattice.db")
            self._temporal = TemporalLayer(self._lattice, data_root / "temporal_layer.db")
            self._identity_family = IdentityFamily(
                self._lattice, self._temporal, data_root / "identity_family.db"
            )
            logger.info("Universal systems initialized")

    # ===== Universal Translation =====

    async def universal_translate(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        content = args.get("content", "")
        content_type = args.get("content_type")
        identity = args.get("identity", "anonymous")

        if self._translator:
            form = await self._translator.translate(content, content_type=content_type, identity=identity)
            form_data = form.to_dict()
        else:
            form_data = {
                "content": content[:100],
                "content_type": content_type or "unknown",
                "atoms": [],
                "bonds": [],
                "envelope": {"content_type": content_type or "text", "identity": identity},
                "symmetry_signature": hashlib.sha256(content.encode()).hexdigest()[:16],
            }

        handle = generate_handle("form", form_data)
        result = {
            "handle": handle,
            "content_type": form_data.get("envelope", {}).get("content_type", "unknown"),
            "atom_count": len(form_data.get("atoms", [])),
            "bond_count": len(form_data.get("bonds", [])),
            "symmetry_signature": form_data.get("symmetry_signature", ""),
            "lightweight": True,
        }
        _audit_tool_call("universal_translate", args, result)
        return result

    # ===== Crystal Operations =====

    async def crystal_store(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        form_handle = args.get("form_handle")
        name = args.get("name", "")
        identity = args.get("identity", "anonymous")
        temporal_phase = args.get("temporal_phase", "present")
        tags = args.get("tags", [])

        form_data = resolve_handle(form_handle)

        if self._identity_family:
            try:
                from cmplx_toolkit.unified_families.cmplx.universal.translator import GeometricForm
                from cmplx_toolkit.unified_families.cmplx.universal.snap_atom import SNAPAtom

                form = GeometricForm(
                    atoms=[SNAPAtom(**a) for a in form_data.get("atoms", [])],
                    bonds=form_data.get("bonds", []),
                    envelope=form_data.get("envelope", {}),
                    symmetry_signature=form_data.get("symmetry_signature", ""),
                )
                result = await self._identity_family.atomic_action(
                    identity_id=identity, action_type="crystal_store",
                    geometric_form=form, description=f"Stored crystal: {name}",
                    temporal_phase=temporal_phase,
                )
                if tags:
                    crystal = self._lattice.retrieve(result["crystal_id"])
                    if crystal:
                        crystal.tags.extend(tags)
                        self._lattice.store(crystal)
                resp = {
                    "crystal_id": result["crystal_id"],
                    "tx_id": result["tx_id"],
                    "receipt_id": result["receipt_id"],
                    "resonance_signature": result["resonance_signature"],
                    "verified": result["verified"],
                    "temporal_phase": temporal_phase,
                }
            except ImportError:
                resp = {"error": "GeometricForm/SNAPAtom unavailable"}
        elif registry.mmdb:
            db_result = registry.mmdb.store(
                content=json.dumps(form_data),
                domain="crystal",
                snap_labels=tags,
            )
            resp = {"crystal_id": db_result.get("id", ""), "stored": True,
                     "source": "mmdb", "tags": tags}
        else:
            resp = {"error": "No crystal store available"}

        _audit_tool_call("crystal_store", args, resp)
        return resp

    async def crystal_retrieve(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        crystal_id = args.get("crystal_id")

        if self._lattice:
            crystal = self._lattice.retrieve(crystal_id)
            if not crystal:
                resp = {"error": "Crystal not found"}
            else:
                resp = {
                    "crystal_id": crystal.crystal_id,
                    "name": crystal.name,
                    "atom_count": len(crystal.atoms),
                    "bond_count": len(crystal.bonds),
                    "resonance_signature": crystal.resonance_signature,
                    "temporal_phase": crystal.temporal_phase,
                    "tags": crystal.tags,
                    "created_at": crystal.created_at,
                    "access_count": crystal.access_count,
                }
        elif registry.mmdb:
            resp = registry.mmdb.get_crystal(crystal_id)
        else:
            resp = {"error": "No crystal store available"}

        _audit_tool_call("crystal_retrieve", args, resp)
        return resp

    async def crystal_resonance_query(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        crystal_id = args.get("crystal_id")
        threshold = args.get("threshold", 0.7)
        limit = args.get("limit", 10)

        if self._lattice:
            query_crystal = self._lattice.retrieve(crystal_id)
            if not query_crystal:
                return {"error": "Query crystal not found"}
            results = self._lattice.find_by_resonance(query_crystal, threshold, limit)
            resp = {
                "query_crystal": crystal_id,
                "threshold": threshold,
                "results": [
                    {"crystal_id": c.crystal_id, "name": c.name,
                     "resonance": float(score), "temporal_phase": c.temporal_phase}
                    for c, score in results
                ],
            }
        elif registry.mmdb:
            resp = registry.mmdb.search(snap_labels=[crystal_id], limit=limit)
        else:
            resp = {"error": "No resonance query available"}

        _audit_tool_call("crystal_resonance_query", args, resp)
        return resp

    async def crystal_merge(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        crystal_ids = args.get("crystal_ids", [])
        name = args.get("name", "")

        if not self._lattice:
            return {"error": "Crystal lattice unavailable"}

        crystals = []
        for cid in crystal_ids:
            c = self._lattice.retrieve(cid)
            if c:
                crystals.append(c)

        if len(crystals) < 2:
            return {"error": "Need at least 2 crystals to merge"}

        try:
            from cmplx_toolkit.unified_families.cmplx.universal.crystal import CrystalFactory
            merged = CrystalFactory.merge(crystals, name)
            merged_id = self._lattice.store(merged)
            resp = {"merged_crystal_id": merged_id, "source_crystals": crystal_ids,
                     "atom_count": len(merged.atoms), "name": merged.name}
        except ImportError:
            resp = {"error": "CrystalFactory unavailable"}

        _audit_tool_call("crystal_merge", args, resp)
        return resp

    # ===== Temporal Operations =====

    async def temporal_query(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        phase = args.get("phase", "present")
        limit = args.get("limit", 100)

        if self._lattice:
            crystals = list(self._lattice.find_by_temporal_phase(phase))
            resp = {
                "phase": phase, "total": len(crystals),
                "crystals": [
                    {"crystal_id": c.crystal_id, "name": c.name,
                     "resonance_signature": c.resonance_signature[:16] + "..."}
                    for c in crystals[:limit]
                ],
            }
        else:
            resp = {"error": "Temporal query unavailable"}

        _audit_tool_call("temporal_query", args, resp)
        return resp

    async def temporal_remember(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        crystal_id = args.get("crystal_id")
        description = args.get("description", "")
        reliability = args.get("reliability", 1.0)

        if not self._temporal:
            return {"error": "Temporal layer unavailable"}

        crystal = self._lattice.retrieve(crystal_id)
        if not crystal:
            return {"error": "Crystal not found"}

        memory = self._temporal.remember(crystal, description, reliability)
        resp = {
            "memory_id": memory.memory_id,
            "crystal_id": crystal_id,
            "reliability": memory.current_reliability,
            "temporal_phase": "past",
        }
        _audit_tool_call("temporal_remember", args, resp)
        return resp

    async def hypothesis_generate(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        crystal_id = args.get("crystal_id")
        num_hypotheses = args.get("num_hypotheses", 3)
        description = args.get("description", "")

        if not self._temporal:
            return {"error": "Temporal layer unavailable"}

        context = self._lattice.retrieve(crystal_id)
        if not context:
            return {"error": "Context crystal not found"}

        hypotheses = self._temporal.hypothesize(context, description, num_hypotheses)
        resp = {
            "context_crystal": crystal_id,
            "hypotheses": [
                {
                    "hypothesis_id": h.hypothesis_id,
                    "description": h.description,
                    "probability": h.posterior_probability,
                    "status": h.status,
                    "temporal_phase": "future",
                }
                for h in hypotheses
            ],
        }
        _audit_tool_call("hypothesis_generate", args, resp)
        return resp

    async def hypothesis_validate(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        hypothesis_id = args.get("hypothesis_id")
        actual_crystal_id = args.get("actual_crystal_id")

        if not self._temporal:
            return {"error": "Temporal layer unavailable"}

        actual = self._lattice.retrieve(actual_crystal_id)
        if not actual:
            return {"error": "Actual outcome crystal not found"}

        confirmed = self._temporal.hypothesis_engine.validate(hypothesis_id, actual)
        resp = {"hypothesis_id": hypothesis_id, "confirmed": confirmed,
                 "actual_crystal": actual_crystal_id}
        _audit_tool_call("hypothesis_validate", args, resp)
        return resp

    async def temporal_counterfactual(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        crystal_id = args.get("crystal_id")
        changes = args.get("changes", {})

        if not self._temporal:
            return {"error": "Temporal layer unavailable"}

        actual = self._lattice.retrieve(crystal_id)
        if not actual:
            return {"error": "Crystal not found"}

        cf = self._temporal.counterfactual(actual, changes)
        resp = {
            "counterfactual_id": cf.crystal_id,
            "based_on": crystal_id,
            "changes": changes,
            "temporal_phase": "future",
        }
        _audit_tool_call("temporal_counterfactual", args, resp)
        return resp

    # ===== Identity Operations =====

    async def identity_register(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        name = args.get("name")
        identity_id = args.get("identity_id")

        if not self._identity_family:
            return {"error": "Identity family unavailable"}

        identity = self._identity_family.register_identity(name, identity_id)
        resp = {
            "identity_id": identity.identity_id,
            "name": identity.name,
            "public_key": identity.public_key,
            "created_at": identity.created_at,
        }
        _audit_tool_call("identity_register", args, resp)
        return resp

    async def identity_history(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        identity_id = args.get("identity_id")

        if not self._identity_family:
            return {"error": "Identity family unavailable"}

        resp = self._identity_family.get_identity_history(identity_id)
        _audit_tool_call("identity_history", args, resp)
        return resp

    async def audit_provenance(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        crystal_id = args.get("crystal_id")

        if not self._identity_family:
            return {"error": "Identity family unavailable"}

        resp = self._identity_family.audit(crystal_id)
        _audit_tool_call("audit_provenance", args, resp)
        return resp

    async def verify_receipt(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        receipt_id = args.get("receipt_id")

        if self._identity_family:
            verified = self._identity_family.verify_receipt(receipt_id)
            resp = {"receipt_id": receipt_id, "verified": verified}
        elif registry.speedlight:
            receipt = registry.speedlight.receipt(receipt_id)
            resp = {"receipt_id": receipt_id, "verified": receipt is not None}
        else:
            resp = {"error": "No receipt verification available"}

        _audit_tool_call("verify_receipt", args, resp)
        return resp

    # ===== System Stats =====

    async def universal_stats(self, args: dict, data_root: Path | None = None) -> dict:
        self._init_systems(data_root if data_root else Path("/data"))
        return {
            "identity_family": self._identity_family.stats() if self._identity_family else {},
            "crystal_lattice": self._lattice.stats() if self._lattice else {},
            "temporal_layer": self._temporal.get_timeline() if self._temporal else {},
        }


UNIVERSAL_TOOLS = UniversalTools()
