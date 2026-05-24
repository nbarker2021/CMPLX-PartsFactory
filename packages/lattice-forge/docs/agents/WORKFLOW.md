# Lattice Forge + Rule 30 — git workflow

**Canonical integration branch:** `feature/lattice-forge-0.2.0-family-hardening` (PR #1 → `main`).

All Rule 30 work (prize-core, regimes, umbrella, sidecar/meta) is merged **into that branch**, not stacked as parallel PRs off the same base.

## Dev vs package

| Tree | Role |
|------|------|
| `D:\PartsFactory\work\lattice-forge` | Day-to-day edits |
| `packages/lattice-forge` | Git-tracked installable package |

After editing work tree:

```powershell
.\scripts\sync_lattice_forge_package.ps1
.\scripts\verify_lattice_forge_family.ps1 -CheckSync -Umbrella -Regimes
```

Commit on **`feature/lattice-forge-0.2.0-family-hardening`** only until PR #1 merges.

## Verify gate

```powershell
.\scripts\verify_lattice_forge_family.ps1 -CheckSync -Umbrella -Regimes
python -m lattice_forge.cli falsify --tier-a
```

Generated artifacts (`proofs_report*.json`) are gitignored; `expected_outputs*.json` stay tracked.

## Honesty (do not regress)

- `rule30.prize.depth_only_shortcut` stays **CONJ**
- `pass_with_open_gaps` must not become unconditional `pass` in harness, receipts, or papers
