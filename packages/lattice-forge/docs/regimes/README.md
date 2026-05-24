# Regimes — Ring 2 engineering layer

Installable extra `[regimes]` for substrate I/O and codec regression gates.
This layer is **not** part of the Ring 1 prize-core proof envelope in
`scripts/run_all_proofs.py`.

## Canonical status doc

See [`../REGIMES_ABC_D4.md`](../REGIMES_ABC_D4.md) for honest regime definitions
(A block tower / extractor, B reserved, C S₃ codec, C′ D₄ full-chart codec),
entropy findings, and what does **not** compress.

## Install

```powershell
pip install -e "packages/lattice-forge[regimes]"
```

## Proof regression

```powershell
cd packages/lattice-forge
python scripts/run_regimes_proofs.py --quick
```

Full Ring 2 gate (regimes + decomposition + transport tower): see
[`../ring2/RING2_EXECUTION_PLAN.md`](../ring2/RING2_EXECUTION_PLAN.md) and
`python scripts/run_ring2_bundle.py --quick`.

Family verify (optional gate):

```powershell
.\scripts\verify_lattice_forge_family.ps1 -Regimes
```

## Proof keys

| Proof key | Regime | Module |
|-----------|--------|--------|
| `SUBSTRATE_MAP` | substrate | `substrate_map.py` |
| `BLOCK_TOWER` | A | `block_tower.py` |
| `BLOCK_EXTRACTOR` | A | `rule30_block_extractor.py` |
| `CHART_CODEC` | C | `chart_codec.py` |
| `CHART_CODEC_D4` | C′ | `chart_codec_d4.py` |

## Tests

```powershell
python -m pytest tests/test_block_tower.py tests/test_chart_codec.py tests/test_chart_codec_d4.py tests/test_substrate_map.py -q
```

## Honesty invariant

`rule30.prize.depth_only_shortcut` remains **CONJ**. Regime A provides
bounded checkpoint I/O, not log-time extraction from depth alone. Never map
`pass_with_open_gaps` or CONJ obligations to unconditional `pass` in harness
output or paper abstracts.
