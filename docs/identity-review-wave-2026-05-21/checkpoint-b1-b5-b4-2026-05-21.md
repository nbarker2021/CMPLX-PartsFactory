# Checkpoint: B1 + B5 + B4 (2026-05-21)

## B1 — Phase H / pluggability truth refresh

- `phase_h_slots_pluggability.py` reads `bootstrap_manifest.json`, reports **17** bootstrap ports.
- Re-ran with live repo-kernel + GitNexus **ok**.
- `emit_promotions_bootstrap.py` → `registers/promotions-bootstrap.jsonl`.

## B5 — AGRM landmine quarantine

- `routing/agrm/AGRMController.py` → `_composed_DO_NOT_IMPORT.py`
- `agrm/__init__.py` no longer exports broken controller.

## B4 — Hash-lanes (slot-16)

- `cmplx.hash_lanes.HashLanesProvider` on port `hash_lanes` (17th bootstrap port).
- Gate: `run_hash_lanes_done_gate.py` intent_met.
