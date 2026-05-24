# Whitepaper sidecar (Agent D)

Read-only rubric for pairing whitepapers to verified claims. Implementation profile:
`D:\PartsFactory\.cursor\agents\r30-whitepaper-sidecar.md`.

## Workflow

1. Run proof harnesses (`run_all_proofs`, optional `-Regimes`, `-Umbrella`).
2. Read agent handoffs `docs/agents/handoffs/R30-*-to-D.md`.
3. Run `python scripts/run_whitepaper_sidecar.py` to refresh manifest.
4. Human/agent review before commit.

## Inputs

| Source | Path |
|--------|------|
| Proofs report | `proofs_report.json` |
| Expected outputs | `expected_outputs.json` (+ regime/umbrella splits) |
| Claim registry | `claims/registry.jsonl` |
| Handoffs | `docs/agents/handoffs/R30-*-to-D.md` |

## Output

`docs/prize/whitepaper_manifest.yaml` — cap **1 core + ≤4 companions**.

## Honesty

Never upgrade CONJ or `pass_with_open_gaps` to unconditional pass. Umbrella companions
carry `not_in_ring1: true`.

## Verify

```powershell
.\scripts\verify_lattice_forge_family.ps1
python scripts/run_whitepaper_sidecar.py
```
