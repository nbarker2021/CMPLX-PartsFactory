# agrm — Interface (slot-15)

**AGRM** (Adaptive Geometric Routing Manager) is the geometric routing layer:
Navigator sweep → bidirectional PathBuilder → SalesmanValidator, with MDHG
hash-lane backing.

## Port

- **`routing`** on `MorphonController` (not yet registered in `register_all()`)

## Target spine (manufactured increment)

| Symbol | Role |
|--------|------|
| `AGRMController` | Orchestrates solve / sweeps (currently composed stub) |
| `MDHG` integration | `_build_mdhg`, `MDHGHashTable` sweeps — must align with `cmplx.addressing.mdhg` |
| Receipts | `POST` per solve; `CROSSING` per traversal (ATTRACTOR_FRAME) |

## Dependencies

- slot-12 **mdhg** — channel / hash addressing
- slot-11 **morphon-controller** — port registry
- slot-05 **e8-lattice** — orientation weights (daemon buffer, Wave 2)

## Status

- Occupant confidence **0.3** — `AGRMController.py` is auto-composed, not import-clean
- Escrow corpus: `staging/by-family/agrm/`, CQE `agrmmdhg.py`, `mdhg/_witness/agrmmdhg_manus.py`

See `BRIDGE.md` and `identity_review/reports/agrm-baseline-audit-2026-05-21.md`.
