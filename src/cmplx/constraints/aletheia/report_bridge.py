"""
Escrow merge (2026-05-19T00:00:31Z).
Source: ``CMPLX-history/staging/by-family/aletheia/observability/aletheia_bridge.py``
Slot: ``slot-03-aletheia-law-chain``
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cmplx._adapters._hashing import deterministic_iso_from_hash, prefixed_id, sha256_hex


def ingest_aletheia_report(report_path: str, *, decision_id: str = "") -> dict[str, Any]:
    path = Path(report_path).expanduser().resolve()
    if not path.exists():
        return {
            "status": "missing_report",
            "report_path": str(path),
            "decision_id": decision_id,
        }

    text = path.read_text(encoding="utf-8", errors="ignore")
    payload: dict[str, Any]
    try:
        loaded = json.loads(text)
        payload = loaded if isinstance(loaded, dict) else {"raw": loaded}
    except Exception:
        payload = {"text": text}

    degradation = float(payload.get("knowledge_degradation", 0.0) or 0.0)
    confidence = float(payload.get("confidence", 0.0) or 0.0)
    score = max(0.0, 1.0 - degradation) * (confidence if confidence > 0 else 1.0)
    envelope = {
        "report_path": str(path),
        "decision_id": decision_id,
        "degradation": degradation,
        "confidence": confidence,
        "score": score,
        "payload": payload,
    }
    payload_hash = sha256_hex(envelope)
    bridge_id = prefixed_id("aletheia", envelope)
    created_at = deterministic_iso_from_hash(payload_hash)
    return {
        "bridge_id": bridge_id,
        "status": "ok",
        "report_path": str(path),
        "decision_id": decision_id,
        "knowledge_degradation": degradation,
        "confidence": confidence,
        "score": score,
        "payload_hash": payload_hash,
        "created_at": created_at,
        "payload": payload,
    }
