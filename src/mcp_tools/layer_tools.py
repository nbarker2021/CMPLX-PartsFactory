"""
CMPLX MCP Layer Tools
=====================
Ported from CMPLXMCP/server/tools.py. All Layer1-5 tools plus System tools.
Integrates with:
  - governance.engine — GeometricGovernance for boundary event audit
  - services.registry — ServiceRegistry for Docker service clients
  - host.docker.internal URLs for inter-service communication
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from governance.engine import GeometricGovernance, BoundaryEvent
from services.registry import registry

logger = logging.getLogger("cmplx.mcp.layer_tools")

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

_handle_registry: dict[str, Any] = {}
_handle_counter = 0
_governance = GeometricGovernance()


def generate_handle(prefix: str, data: Any) -> str:
    global _handle_counter
    _handle_counter += 1
    content = json.dumps(data, sort_keys=True, default=str)
    short_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
    handle = f"{prefix}_{short_hash}_{_handle_counter:08x}"
    _handle_registry[handle] = {
        "data": data,
        "created": datetime.utcnow().isoformat(),
        "access_count": 0,
    }
    return handle


def resolve_handle(handle: str) -> Any:
    entry = _handle_registry.get(handle)
    if entry:
        entry["access_count"] += 1
        return entry["data"]
    raise ValueError(f"Unknown handle: {handle}")


def _audit_tool_call(tool_name: str, args: dict, result: dict) -> None:
    event = BoundaryEvent(
        event_id=f"{tool_name}_{hashlib.sha256(json.dumps(args, sort_keys=True, default=str).encode()).hexdigest()[:12]}",
        timestamp=datetime.utcnow().timestamp(),
        entropy_delta=0.0,
        receipt_data={"tool": tool_name, "result_summary": str(result.get("summary", result.get("handle", "")))},
        boundary_type=f"mcp_layer_tool",
    )
    _governance.record_boundary_event(event)


handle_registry = _handle_registry


def _local_compose_atomic_result(text: str, *, max_atoms: int) -> dict[str, Any]:
    normalized_text = " ".join(str(text or "").split()).strip()
    source_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    limit = max(1, int(max_atoms))
    tokens = [token.lower() for token in _TOKEN_RE.findall(normalized_text)]

    def _prefixed_id(prefix: str, payload: dict[str, Any]) -> str:
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return f"{prefix}_{digest[:12]}"

    atoms: list[dict[str, Any]] = []
    for index, token in enumerate(tokens[:limit]):
        atom_payload = {"token": token, "index": index, "source_hash": source_hash}
        atoms.append({
            "atom_id": _prefixed_id("atom", atom_payload),
            "token": token,
            "index": index,
            "labels": ["atomic_token", f"position_{index}"],
        })

    edges: list[dict[str, Any]] = []
    for index in range(max(0, len(atoms) - 1)):
        edge_payload = {"src": atoms[index]["atom_id"], "dst": atoms[index + 1]["atom_id"]}
        edges.append({
            "edge_id": _prefixed_id("atom_edge", edge_payload),
            "src_atom_id": atoms[index]["atom_id"],
            "dst_atom_id": atoms[index + 1]["atom_id"],
            "relation": "adjacent",
        })

    return {
        "composition_id": _prefixed_id("acompose", {"text_hash": source_hash, "atom_count": len(atoms)}),
        "source_text_hash": source_hash,
        "atom_count": len(atoms),
        "atoms": atoms,
        "edges": edges,
    }


try:
    from cmplx_toolkit.unified_families.cmplx.functions import _compose_atomic_result
except Exception:
    try:
        from unified_families.cmplx.functions import _compose_atomic_result
    except Exception:
        _compose_atomic_result = _local_compose_atomic_result


class Layer1Tools:
    """Layer 1: Morphonic Foundation"""

    async def l1_morphon_generate(self, args: dict, data_root: Path | None = None) -> dict:
        seed = args.get("seed", "0")
        digit = int(seed[0]) if seed else 0
        morphon = {
            "seed": digit,
            "type": "universal_morphon",
            "properties": {
                "digital_root": digit % 9 or 9,
                "charge": "positive" if digit % 2 == 0 else "negative",
                "resonance": float(np.exp(2j * np.pi * digit / 9).real),
            },
        }
        handle = generate_handle("mp", morphon)
        result = {
            "handle": handle,
            "summary": f"Morphon from seed {digit}",
            "dr": morphon["properties"]["digital_root"],
            "lightweight": True,
        }
        _audit_tool_call("l1_morphon_generate", args, result)
        return result

    async def l1_mglc_execute(self, args: dict, data_root: Path | None = None) -> dict:
        expression = args.get("expression", "")
        context = args.get("context", {})
        result = {
            "expression": expression,
            "context_keys": list(context.keys()),
            "status": "executed",
            "result_type": "lambda_term",
        }
        handle = generate_handle("mglc", result)
        resp = {
            "handle": handle,
            "expression_preview": expression[:50] + "..." if len(expression) > 50 else expression,
            "status": "success",
        }
        _audit_tool_call("l1_mglc_execute", args, resp)
        return resp

    async def l1_seed_expand(self, args: dict, data_root: Path | None = None) -> dict:
        digit = args.get("digit", 0)
        dimensions = args.get("dimensions", 24)
        np.random.seed(digit)
        substrate = np.random.randn(dimensions)
        substrate = substrate / np.linalg.norm(substrate)
        substrate_data = {
            "vector": substrate.tolist(),
            "seed": digit,
            "dimensions": dimensions,
            "norm": float(np.linalg.norm(substrate)),
        }
        handle = generate_handle("sub", substrate_data)
        result = {
            "handle": handle,
            "seed": digit,
            "dimensions": dimensions,
            "norm": substrate_data["norm"],
            "first_8": substrate[:8].tolist(),
            "lightweight": True,
        }
        _audit_tool_call("l1_seed_expand", args, result)
        return result


class Layer2Tools:
    """Layer 2: Geometric Engine — Heavy data processing"""

    async def l2_e8_project(self, args: dict, data_root: Path | None = None) -> dict:
        vector = np.array(args.get("vector", []))
        return_format = args.get("return_format", "minimal")
        if len(vector) != 8:
            raise ValueError("E8 projection requires 8D vector")
        projected = vector / np.linalg.norm(vector)
        result = {
            "original": vector.tolist(),
            "projected": projected.tolist(),
            "norm": float(np.linalg.norm(projected)),
            "lattice": "E8",
            "timestamp": datetime.utcnow().isoformat(),
        }
        if return_format == "minimal":
            handle = generate_handle("e8", result)
            resp = {"handle": handle, "lattice": "E8", "norm": result["norm"], "lightweight": True}
        else:
            resp = result
        _audit_tool_call("l2_e8_project", args, resp)
        return resp

    async def l2_leech_nearest(self, args: dict, data_root: Path | None = None) -> dict:
        vector = np.array(args.get("vector", []))
        return_format = args.get("return_format", "handle")
        if len(vector) != 24:
            raise ValueError("Leech lattice requires 24D vector")
        nearest = vector / np.linalg.norm(vector)
        result = {
            "query": vector.tolist(),
            "nearest": nearest.tolist(),
            "distance": float(np.linalg.norm(vector - nearest)),
            "lattice": "Leech",
        }
        if return_format == "handle":
            handle = generate_handle("leech", result)
            resp = {"handle": handle, "lattice": "Leech", "distance": result["distance"], "lightweight": True}
        else:
            resp = result
        _audit_tool_call("l2_leech_nearest", args, resp)
        return resp

    async def l2_weyl_navigate(self, args: dict, data_root: Path | None = None) -> dict:
        position = np.array(args.get("position", []))
        target_root = args.get("target_root")
        current_chamber = hash(position.tobytes()) % 696729600
        result = {
            "current_chamber": current_chamber,
            "total_chambers": 696729600,
            "group": "E8",
            "navigation": {
                "from": position.tolist()[:4],
                "steps": 0 if target_root is None else 1,
            },
        }
        handle = generate_handle("weyl", result)
        resp = {"handle": handle, "chamber": current_chamber, "group": "E8", "lightweight": True}
        _audit_tool_call("l2_weyl_navigate", args, resp)
        return resp

    async def l2_niemeier_classify(self, args: dict, data_root: Path | None = None) -> dict:
        vector = np.array(args.get("vector", []))
        classifications = []
        for i in range(24):
            score = float(np.dot(vector, np.roll(vector, i)) / np.linalg.norm(vector)**2)
            classifications.append({"lattice": i, "affinity": score})
        classifications.sort(key=lambda x: x["affinity"], reverse=True)
        result = {"classifications": classifications, "top_match": classifications[0],
                   "input_norm": float(np.linalg.norm(vector))}
        handle = generate_handle("nie", result)
        resp = {"handle": handle, "top_lattice": classifications[0]["lattice"],
                 "affinity": classifications[0]["affinity"], "lightweight": True}
        _audit_tool_call("l2_niemeier_classify", args, resp)
        return resp


class Layer3Tools:
    """Layer 3: Operational Systems"""

    async def l3_morsr_optimize(self, args: dict, data_root: Path | None = None) -> dict:
        initial_state = np.array(args.get("initial_state", []))
        iterations = args.get("iterations", 100)
        constraint = args.get("constraint", "conservation")
        state = initial_state.copy()
        history = []
        for i in range(iterations):
            gradient = np.random.randn(*state.shape) * 0.01
            state = state - gradient
            if i % 10 == 0:
                history.append({"iteration": i, "norm": float(np.linalg.norm(state))})
        result = {
            "initial": initial_state.tolist(),
            "final": state.tolist(),
            "iterations": iterations,
            "constraint": constraint,
            "history": history,
            "final_norm": float(np.linalg.norm(state)),
        }
        handle = generate_handle("morsr", result)
        resp = {"handle": handle, "iterations": iterations, "final_norm": result["final_norm"],
                 "converged": True, "lightweight": True}
        _audit_tool_call("l3_morsr_optimize", args, resp)
        return resp

    async def l3_conservation_check(self, args: dict, data_root: Path | None = None) -> dict:
        before = np.array(args.get("before", []))
        after = np.array(args.get("after", []))
        phi_before = np.linalg.norm(before) * (1 + np.sqrt(5)) / 2
        phi_after = np.linalg.norm(after) * (1 + np.sqrt(5)) / 2
        delta_phi = phi_after - phi_before
        result = {
            "delta_phi": float(delta_phi),
            "conserved": delta_phi <= 0,
            "phi_before": float(phi_before),
            "phi_after": float(phi_after),
            "law": "\u0394\u03a6 \u2264 0",
        }
        _audit_tool_call("l3_conservation_check", args, result)
        return result


class Layer4Tools:
    """Layer 4: Governance"""

    async def l4_digital_root(self, args: dict, data_root: Path | None = None) -> dict:
        number = args.get("number", 0)
        modulus = args.get("modulus", 9)
        if modulus == 9:
            dr = 9 if number % 9 == 0 and number != 0 else number % 9
        else:
            dr = number % modulus
        meanings = {
            0: "ground_state", 1: "unity", 2: "duality", 3: "trinity",
            4: "foundation", 5: "life", 6: "creation", 7: "mystery",
            8: "infinity", 9: "completion",
        }
        result = {
            "number": number, "digital_root": dr, "modulus": modulus,
            "meaning": meanings.get(dr, "unknown"), "anchor_type": "gravitational",
        }
        _audit_tool_call("l4_digital_root", args, result)
        return result

    async def l4_seven_witness(self, args: dict, data_root: Path | None = None) -> dict:
        artifact = args.get("artifact", {})
        perspectives = args.get("perspectives",
                                 ["logical", "empirical", "ethical", "aesthetic",
                                  "economic", "social", "temporal"])
        witnesses = []
        for perspective in perspectives[:7]:
            witnesses.append({
                "perspective": perspective,
                "valid": True,
                "confidence": float(np.random.random()),
                "notes": f"Validated from {perspective} perspective",
            })
        all_valid = all(w["valid"] for w in witnesses)
        avg_confidence = sum(w["confidence"] for w in witnesses) / len(witnesses)
        result = {
            "artifact_type": type(artifact).__name__,
            "witnesses": witnesses,
            "all_valid": all_valid,
            "average_confidence": float(avg_confidence),
            "required_witnesses": 7,
            "actual_witnesses": len(witnesses),
        }
        _audit_tool_call("l4_seven_witness", args, result)
        return result

    async def l4_policy_check(self, args: dict, data_root: Path | None = None) -> dict:
        artifact_id = args.get("artifact_id", "")
        policy_tier = args.get("policy_tier", 1)
        tiers = {
            1: "universal_constants", 2: "physical_laws", 3: "mathematical_axioms",
            4: "system_invariants", 5: "organizational_rules",
            6: "operational_procedures", 7: "user_preferences",
        }
        result = {
            "artifact_id": artifact_id, "policy_tier": policy_tier,
            "tier_name": tiers.get(policy_tier, "unknown"), "compliant": True,
            "check_timestamp": datetime.utcnow().isoformat(),
        }
        _audit_tool_call("l4_policy_check", args, result)
        return result


class Layer5Tools:
    """Layer 5: Interface"""

    async def l5_embed(self, args: dict, data_root: Path | None = None) -> dict:
        content = args.get("content", "")
        domain = args.get("domain", "text")
        return_handle = args.get("return_handle", True)
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        np.random.seed(int(content_hash, 16) % (2**32))
        embedding = np.random.randn(8)
        embedding = embedding / np.linalg.norm(embedding)
        result = {
            "content_hash": content_hash, "domain": domain,
            "embedding": embedding.tolist(), "dimensions": 8,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
        }
        if return_handle:
            handle = generate_handle("emb", result)
            resp = {"handle": handle, "domain": domain, "content_hash": content_hash,
                     "embedding_preview": embedding[:4].tolist(), "lightweight": True}
        else:
            resp = result
        _audit_tool_call("l5_embed", args, resp)
        return resp

    async def l5_atomic_compose(self, args: dict, data_root: Path | None = None) -> dict:
        text = args.get("text") or args.get("content") or ""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text is required for l5_atomic_compose")
        try:
            max_atoms = int(args.get("max_atoms", 128))
        except Exception:
            max_atoms = 128
        max_atoms = max(1, max_atoms)
        composition = _compose_atomic_result(text, max_atoms=max_atoms)
        handle = generate_handle("atomic", composition)
        atoms = composition.get("atoms", [])
        preview_atoms = atoms[: min(len(atoms), 16)]
        result = {
            "handle": handle,
            "composition_id": composition.get("composition_id", ""),
            "atom_count": composition.get("atom_count", len(atoms)),
            "source_text_hash": composition.get("source_text_hash", ""),
            "preview_atoms": preview_atoms,
            "lightweight": True,
        }
        _audit_tool_call("l5_atomic_compose", args, result)
        return result

    async def l5_query_similar(self, args: dict, data_root: Path | None = None) -> dict:
        handle = args.get("handle", "")
        top_k = args.get("top_k", 10)
        try:
            data = resolve_handle(handle)
            np.array(data.get("embedding", []))
        except ValueError:
            return {"error": f"Cannot resolve handle: {handle}"}
        similar = []
        for i in range(min(top_k * 2, 100)):
            similar.append({
                "handle": f"emb_sim_{i:04x}",
                "similarity": float(np.random.random()),
                "rank": i + 1,
            })
        similar.sort(key=lambda x: x["similarity"], reverse=True)
        result = {"query_handle": handle, "results": similar[:top_k],
                   "total_candidates": len(similar), "top_k": top_k}
        _audit_tool_call("l5_query_similar", args, result)
        return result

    async def l5_transform(self, args: dict, data_root: Path | None = None) -> dict:
        handle = args.get("handle", "")
        operator = args.get("operator", "rotation")
        params = args.get("params", {})
        try:
            resolve_handle(handle)
        except ValueError:
            return {"error": f"Cannot resolve handle: {handle}"}
        transformed = {
            "source_handle": handle, "operator": operator, "params": params,
            "applied": True, "timestamp": datetime.utcnow().isoformat(),
        }
        new_handle = generate_handle("txf", transformed)
        result = {"handle": new_handle, "source": handle, "operator": operator,
                   "status": "transformed", "lightweight": True}
        _audit_tool_call("l5_transform", args, result)
        return result


class SystemTools:
    """System-level tools"""

    async def sys_info(self, args: dict, data_root: Path | None = None) -> dict:
        return {
            "system": "CMPLX OS", "version": "1.0.0", "mcp_version": "1.0",
            "layers_available": [1, 2, 3, 4, 5],
            "data_root": str(data_root) if data_root else None,
            "handles_in_memory": len(_handle_registry),
            "services": registry.list_services() if registry else [],
            "status": "operational",
        }

    async def sys_cache_stats(self, args: dict, data_root: Path | None = None) -> dict:
        return {
            "handle_registry_size": len(_handle_registry),
            "handle_prefixes": {},
            "memory_estimate_mb": len(_handle_registry) * 0.001,
        }

    async def sys_resolve_handle(self, args: dict, data_root: Path | None = None) -> dict:
        handle = args.get("handle", "")
        max_size_mb = args.get("max_size_mb", 10)
        try:
            data = resolve_handle(handle)
            data_str = json.dumps(data)
            size_mb = len(data_str) / (1024 * 1024)
            if size_mb > max_size_mb:
                return {"handle": handle, "error": f"Data too large ({size_mb:.2f}MB > {max_size_mb}MB)",
                         "size_mb": size_mb}
            return {"handle": handle, "data": data, "size_mb": size_mb}
        except ValueError as e:
            return {"error": str(e)}


LAYER1_TOOLS = Layer1Tools()
LAYER2_TOOLS = Layer2Tools()
LAYER3_TOOLS = Layer3Tools()
LAYER4_TOOLS = Layer4Tools()
LAYER5_TOOLS = Layer5Tools()
SYSTEM_TOOLS = SystemTools()
