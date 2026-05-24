# Umbrella paper corpus (Ring 3)

**`not_in_ring1: true`** — companions only; do not duplicate Ring 1 T1–T8 abstract numbering.

Source of truth for P0 code port: `D:\tmp\umbrella-submission` (excluding `repaired-v1/`,
backups, duplicate `rule30-paper/`).

## Contents

| Path | Origin | Role |
|------|--------|------|
| `IDENTITY_PAPER.md` | umbrella submission | Identity / universality narrative |
| `AUDIT_RESPONSE.md` | umbrella submission | Audit Q&A |
| `theorems/THEOREM_REGISTRY.md` | umbrella submission | Theorem index |
| `theorems/OPEN_OBLIGATIONS.md` | umbrella submission | Open obligations (CONJ preserved) |
| `papers/README.md` | curated index | Pointer to dressed paper corpus |

## Proof keys (P0)

See handoff `docs/agents/handoffs/R30-C-to-D.md`:

- `RULE90_LINEARIZATION`, `F2_MAJORANA`, `OLOID_*` — regression in `expected_outputs_umbrella.json`

## Honesty

- `rule30.prize.depth_only_shortcut` stays **CONJ**
- `OLOID_DUAL_PATH.tape_readout_match_rate` ~0.528 is structural-only
- WP-OLOID-01 and WP-MOONSHINE remain deferred in sidecar manifest

## Verify

```powershell
.\scripts\verify_lattice_forge_family.ps1 -Umbrella
```

## Install

```powershell
pip install -e "packages/lattice-forge[umbrella]"
```
