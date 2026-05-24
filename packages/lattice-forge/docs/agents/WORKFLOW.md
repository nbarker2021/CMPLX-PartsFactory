# Lattice Forge + Rule 30 — git workflow

**Canonical integration branch:** `main` (Rule 30 program merged via PRs #1–#6).

Use short-lived `feature/lf-*` or `feature/w1c-*` branches off `main` for scoped work.

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

Commit on **`main`** via focused PRs (one stream per PR when possible).

## Verify gate

```powershell
.\scripts\verify_lattice_forge_family.ps1 -CheckSync -Umbrella -Regimes
python -m lattice_forge.cli falsify --tier-a
```

Generated artifacts (`proofs_report*.json`) are gitignored; `expected_outputs*.json` stay tracked.

## Honesty (do not regress)

- `rule30.prize.depth_only_shortcut` stays **CONJ**
- `pass_with_open_gaps` must not become unconditional `pass` in harness, receipts, or papers
- WP-TOWER-01: only **PROVEN** transport rows count — see `docs/tower/TRANSPORT_TOWER_POLICY.md`
