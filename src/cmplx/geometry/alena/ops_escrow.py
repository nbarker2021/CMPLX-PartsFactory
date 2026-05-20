"""
Escrow merge L01 (2026-05-19T01:10:18Z).
Source: ``D:/Manny Unification 2/datasets from previous review/MannyUnification/mannyunification_staging/systems/SNAP/snap_runtime/src/snap_runtime/ops.py``
Slot: ``slot-08-alena-coupling``
"""
from __future__ import annotations

from pathlib import Path

from snap_runtime.catalog import write_catalog_entry
from snap_runtime.diagnostics import runtime_health
from snap_runtime.exports import export_record_bundle
from snap_runtime.pipeline import SnapRuntime


class SnapOps:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.runtime = SnapRuntime(self.root)

    def snap_and_export(self, datum: str, *, observational_labels: list[str] | None = None) -> dict:
        record = self.runtime.snap(datum, observational_labels=observational_labels)
        bundle_path = export_record_bundle(self.root, record.record_id)
        catalog_path = write_catalog_entry(self.root)
        return {
            "mode": "snap_and_export",
            "record_id": record.record_id,
            "receipt_id": record.metadata.get("receipt_id"),
            "bundle_path": str(bundle_path),
            "catalog_path": str(catalog_path),
            "health": runtime_health(self.root),
        }

    def export_record(self, record_id: str) -> dict:
        bundle_path = export_record_bundle(self.root, record_id)
        catalog_path = write_catalog_entry(self.root)
        receipt = self.runtime.receipts.latest_receipt_for_record(record_id)
        return {
            "mode": "export_record",
            "record_id": record_id,
            "receipt_id": receipt["receipt_id"] if receipt else None,
            "bundle_path": str(bundle_path),
            "catalog_path": str(catalog_path),
            "health": runtime_health(self.root),
        }
