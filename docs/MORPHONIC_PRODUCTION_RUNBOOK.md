# Morphonic Production Runbook

Operator guide for the hardened morphonic substrate (crystal v2.1, multistream ingest, compose mutations, production inference).

## Prerequisites

- `PYTHONPATH=src` from `CMPLX-PartsFactory`
- Optional: repo-kernel at `http://localhost:8786` for read-only morphonic routes

## Dual DB policy (production vs template)

Two SQLite substrates serve different roles. **Never** run production `forward --production` with a crystal that does not match the live production DB.

| Database | Role | Typical actions |
|----------|------|-----------------|
| `data/token_index_identity_review.sqlite` | **Production inference** — witness DB for admit/complete, tool-pass, multistream ingest | Bounded ingest waves; tool-pass; **re-crystallize** after ingest or tool-pass |
| `data/token_index.sqlite` | **Template / coverage** — combinatorial frame expansion | `build-index --levels 1,2,3`; `template-stats`; `refine` with `--limit` on convolve |

Production crystal: `crystals/identity_review.crystal/` (`schema_version` **2.1.0**, `crystal_id` **bc00ac8ee26c**).

Workflow:

1. Expand template coverage on `token_index.sqlite` (bounded alphabet/levels first in CI).
2. Ingest and tool-pass on `token_index_identity_review.sqlite`.
3. Re-crystallize identity_review so bundle `token_index.sqlite` matches the live DB.
4. Set **both** env vars together on host and in repo-kernel before production forward or HTTP reads.

```powershell
$env:MORPHONIC_TOKEN_INDEX_DB = "D:/PartsFactory/CMPLX-PartsFactory/data/token_index_identity_review.sqlite"
$env:MORPHONIC_CRYSTAL_BUNDLE = "D:/PartsFactory/CMPLX-PartsFactory/crystals/identity_review.crystal"
```

Optional HF lane (default off): `CMPLX_HF_LANE=off|on_demand|train` — see `src/cmplx/transform/torch/hf_on_demand.py`.

### HF on-demand vs train window

| Env | Effect |
|-----|--------|
| `CMPLX_HF_LANE=off` (default) | No HF wake, no train window |
| `CMPLX_HF_LANE=on_demand` | Layer NSL-reject may call `HFOnDemandLane.wake()` (stub) |
| `CMPLX_HF_LANE=train` | Enables bounded train window |
| `CMPLX_TRAIN_WINDOW=1` | Same as train lane (alternative toggle) |

Train window Phase A: admit-mask substrate loop + JSON job report under `data/train_windows/`. Phase B (optional): set `CMPLX_HF_MODEL` for lazy HF stub forward inside the window — not a full frontier LM by default.

**Planned downtime example (nightly, 3600s wall clock):**

```powershell
$env:PYTHONPATH = "src"
$env:CMPLX_HF_LANE = "train"
# Optional Phase B: $env:CMPLX_HF_MODEL = "stub/local-model"

python -m cmplx.transform train-window `
  --crystal crystals/identity_review.crystal `
  --dataset identity_review `
  --max-steps 200 `
  --wall-clock-budget-sec 3600
```

Dry-run plan only: add `--dry-run`. Custom token list: `--tokens-file path\to\tokens.txt`. Do **not** pass `--allow-mutations` unless port writes during downtime are explicitly intended.

| Knob | Guidance |
|------|----------|
| Crystal | Production: `crystals/identity_review.crystal` |
| DB | Must match crystal `token_index.sqlite` (`token_index_identity_review.sqlite` source) |
| `max_steps` | Bounded step count (default CLI: 10) |
| Reports | `data/train_windows/<UTC-timestamp>.json` |
| `wall_clock_budget_sec` | Hard stop (e.g. 600 = 10 min maintenance window) |
| Tokens | Optional list; empty uses harness default (pull from index in ops scripts) |

Not a default service — unset `CMPLX_HF_LANE` after the window.

## Crystallize workstate

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
$env:PYTHONPATH = "src"
python -m cmplx.transform crystallize `
  --name workstate `
  --db data/token_index.sqlite `
  --lib data/rule_libs `
  --out crystals/workstate.crystal
```

Inspect bundle:

```powershell
python -m cmplx.transform crystal-info --bundle crystals/workstate.crystal
```

Manifest schema: **2.1.0** (optional `morph_signatures.jsonl`, stream counts).

## Multistream ingest (EN-first)

```powershell
python identity_review/scripts/morphonic_ingest_identity_review.py `
  --root D:\PartsFactory\identity_review `
  --db data/token_index_identity_review.sqlite `
  --streams en,native `
  --stats-export data/ingest_stats.json
```

Policy: ingest **EN** first, then sidecar streams with shared `translation_key` per chunk.

## Refine index (compose mutations)

```powershell
python -m cmplx.transform refine `
  --db data/token_index.sqlite `
  --target-coverage 0.45
```

Runs `convolve` → `involute` → `abstract` until slot coverage reaches target (or max rounds).

Check template stats:

```powershell
python -m cmplx.transform template-stats --db data/token_index.sqlite
```

## Compose + forward (production preset)

Production inference uses **identity_review** DB + crystal (not the template DB alone):

```powershell
python -m cmplx.transform forward `
  --ribbon "baaaaaab" `
  --production `
  --crystal crystals/identity_review.crystal
```

Production preset: N-ladder (8 layers), `shell_bind=True`, ports registered on init.

Dev-only (non-production config): explicit smaller `TransformerConfig` without `--production` — do not use for ops sign-off.

With a scratch workstate bundle:

```powershell
python -m cmplx.transform forward `
  --ribbon "baaaaaab" `
  --production `
  --crystal crystals/workstate.crystal
```

## Repo-kernel read routes

| Route | Purpose |
|-------|---------|
| `GET /api/morphonic/status` | Substrate availability |
| `GET /api/morphonic/template-stats?db=...` | Template frame report |
| `GET /api/morphonic/crystal-info?bundle=...` | Crystal bundle inspection |

Health: `GET /api/health` includes a `morphonic` subsection.

### Repo-kernel env (host vs container)

`docker-compose.repo-kernel.yml` bind-mounts `D:/PartsFactory` at `/sources/PartsFactory`.
Defaults inside the container:

| Variable | Default (container path) |
|----------|--------------------------|
| `MORPHONIC_TOKEN_INDEX_DB` | `/sources/PartsFactory/CMPLX-PartsFactory/data/token_index_identity_review.sqlite` |
| `MORPHONIC_CRYSTAL_BUNDLE` | `/sources/PartsFactory/CMPLX-PartsFactory/crystals/identity_review.crystal` |
| `CMPLX_PARTS_FACTORY_SRC` | `/sources/PartsFactory/CMPLX-PartsFactory/src` |

On Windows before `docker compose up`, override host paths if needed:

```powershell
$env:MORPHONIC_TOKEN_INDEX_DB = "D:/PartsFactory/CMPLX-PartsFactory/data/token_index_identity_review.sqlite"
$env:MORPHONIC_CRYSTAL_BUNDLE = "D:/PartsFactory/CMPLX-PartsFactory/crystals/identity_review.crystal"
docker compose -f docker-compose.repo-kernel.yml up -d --build
```

Compose cannot mount arbitrary Windows paths unless they are listed under `volumes:`.
Use the existing `D:/PartsFactory` bind or add a new bind for custom DB/crystal locations.

## E2E smoke (CI / local)

```powershell
python scripts/morphonic_e2e_smoke.py --quick
```

Optional production gate (when identity_review artifacts exist locally):

```powershell
python scripts/morphonic_e2e_smoke.py --quick --production-db
```

Chains: temp `build-index` seed → `refine --target-coverage 0.1` (with convolve limit) →
`crystallize` (asserts `schema_version == 2.1.0`) → production `forward`.
With `--production-db`, also records `forced_pct` from template stats and validates
`crystals/identity_review.crystal` manifest schema. Exit code non-zero on failure.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| `ShellViolation` on forward | `admit --token ...`; ribbon not in index |
| Low refine coverage | Run `build-index` L1–L2 first; verify `index-stats` |
| Re-ingest not warm-starting | Ports/cache; second pass should show high `cache_hits` |
| Linked EN/native mismatch | `lift_linked_pair` E8 distance; tool pass geometry rows |
| MT hub errors | Set `CMPLX_TRANSLATE_HUB=noop` (default) |

## Tests

```powershell
python -m pytest tests/transform/ tests/primitives/ -q
python scripts/morphonic_e2e_smoke.py --quick
```

CI: `.github/workflows/morphonic-pytest.yml` runs pytest + e2e smoke on push.

## Repo-kernel environment (host)

When running repo-kernel with PartsFactory bind mount:

```powershell
$env:MORPHONIC_TOKEN_INDEX_DB = "D:/PartsFactory/CMPLX-PartsFactory/data/token_index_identity_review.sqlite"
$env:MORPHONIC_CRYSTAL_BUNDLE = "D:/PartsFactory/CMPLX-PartsFactory/crystals/identity_review.crystal"
docker compose -f docker-compose.repo-kernel.yml up -d
```

Container defaults are set in `docker-compose.repo-kernel.yml` under `/sources/PartsFactory/...`.
