# Library needs enumeration (primary focus)

**Canonical artifact:** `claims/library_needs.jsonl` (+ `library_needs.meta.json` summary)

Regenerate after any registry, harness, or proof-key change:

```powershell
cd packages/lattice-forge
python scripts/enumerate_library_needs.py
```

## Why needs-first

The solve is not “one more proof run” — it is a **complete map** of what `lattice-forge` must provide:

| Column | Meaning |
|--------|---------|
| `need_id` | Stable id (claim, proof key, or explicit backlog id) |
| `need_statement` | One-line requirement |
| `honesty_current` / `honesty_target` | Where we are vs where we stop |
| `impl_status` | Code present? (`present` / `partial` / `missing` / `stub`) |
| `harness_status` | Machine check? (`proven` / `bounded` / `gaps` / `conj` / `none`) |
| `priority` | P0 = blocks prize narrative; P1 = unlocks companions; P2 = umbrella |

Work **closes rows** (impl + harness + artifact), not loose narrative.

## Layers (rings)

| Ring | Subpackage extra | What it covers |
|------|------------------|----------------|
| 1 | `prize-core` | T1–T8, BONUS, P1–P3, obligations, honesty harness |
| 2 | `regimes`, `transport-tower`, `decomposition` | Codecs, block tower, transport lemmas, monster lifts |
| 3 | `umbrella` | Oloid, Rule90, VOA, actuation, moonshine scaffolding |
| 0 | `proofs` | Infra: reports, expected_outputs depth ladders, CI |

## Harness bundles (how needs get checked)

| Script | Closes |
|--------|--------|
| `run_all_proofs.py` | ~31 proof keys (prize + umbrella) |
| `run_regimes_proofs.py` | 5 regime keys |
| `run_transport_tower_proofs.py` | 5 transport keys |
| `run_open_claims_harness.py` | CONJ → BOUNDED_EXEC promotions |
| `run_ring1_ring2_pipeline.py` | Ordered gate + all of the above |
| `enumerate_library_needs.py` | **Inventory** (this doc) |

## P0 backlog (from enumeration)

1. `need.P1.readout_injectivity` — no harness yet  
2. `need.P3.weyl_e8_full_table` — prototype not in repo  
3. `need.infra.proofs_report_4096` — prize-depth baseline artifact  
4. `rule30.prize.depth_only_shortcut` — stays CONJ; surrogate is `rule30.extraction.block_addressed`

## Query examples

```powershell
# Count open harness gaps
python -c "import json; rows=[json.loads(l) for l in open('claims/library_needs.jsonl')]; print(sum(1 for r in rows if r['harness_status'] in ('conj','none','gaps')))"

# List P0
python -c "import json; [print(r['need_id']) for l in open('claims/library_needs.jsonl') if (r:=json.loads(l))['priority']=='P0']"
```

## Relation to field research

Agent reports (4096 scaling, Weyl prototype, codec analysis) **land as rows**:

- set `artifact_present: true`  
- attach `artifact_expected` path  
- bump `honesty_current` only when harness agrees  

No “submission ready” without rows closed at the target depth ladder.
