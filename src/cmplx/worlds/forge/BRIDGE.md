# Worlds Forge — cross-port bridges

Slot **19** (`worlds` / `lattice-forge`). Package implementation lives in
`packages/lattice-forge`; this directory is the CMPLX manufacturing shim.

## Consumes

| Port | Slot | Bridge | Status |
|------|------|--------|--------|
| `receipt` | slot-01 | `_receipt_bridge.mint_forge_operation` — overlay verify → spine mint when `FORGE_MINT_RECEIPT=1` | implemented |
| `geometry` | slot-05 | Leech / E8 cross-check vs `terminal_tree` and morphonics `failure:leech_construction_pending` | escrow (`forge-leech-golay`) |
| `symbolic` | slot-18 | TarPit center-bit calibration vs Rule 30 readout | escrow (`forge-tarpit-calibration`) |

## Escrow out

| Target | Residue |
|--------|---------|
| `geometry` | Golay / Construction A import for Leech exact rows |

## Do not duplicate

- **TarPit** (:8844) — consume symbolic ecology; do not re-embed ETP runtime here.
- **geometry-e8** runtime — delegate Leech proof obligations to forge package, not inline in `cmplx.geometry`.

## HTTP

- Manufacturing: `docker-compose.lattice-forge.yml` → **:8845**
- Package dev server (non-slot): lattice-forge optional `[server]` on **:8765**
