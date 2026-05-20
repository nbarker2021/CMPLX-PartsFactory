# Morphonic Unified Doctrine

**Status:** Living doctrine (2026-05-19)  
**Supersedes:** stale gap lists in `MORPHONIC_SUBSTRATE_CRYSTAL_PLAN.md` §3.2  
**Code home:** `src/cmplx/transform/`, `src/cmplx/primitives/superperm.py`

## North star

Substrate-first geometric transformer: derive once → receipt → cache → calibrate; shell-valid tokens only; living index + reloadable crystal(s). Slot 48 is the transformer platform; CMPLX owns law (shell + NSL), memory (index + SpeedLight), and provenance.

## N-ladder (transformer depth)

| N | Role | Engineering hook |
|---|------|------------------|
| 1 | Contextual mark / notation | Tokenizer + `SurfaceMode` |
| 2 | Mandatory interaction floor | G₂ horizontal legality |
| 3 | Centroid / triad | SU(3)-like orientation |
| 4 | F₄ quad matching | Involution rings + template frame |
| 5 | Octad / T₅ sheet | `OctadSheet` (1 pal + 7 trees) |
| 6 | Coupling | Spin(6) / E₆ plot (`e6_lift.py`) |
| 7 | Penultimate tighten | E₇ / strict NSL |
| 8 | Closure + observer | E₈ neighbors; shell-bound forward |

Eight layers are **eight policies** (`NLadderLayerConfig`), not eight identical blocks.

## Superpermutation / octad

- `SUPERPERM_N4` lives in `data/superpermutations/n4.json` and `cmplx.primitives.superperm`.
- Quad bond `1234|4321` is the F₄ cell on the 1D ribbon — **not** SP string content.
- SP is walked by `IndexSupervisor` only (scheduling cursor).
- n=4→n=5 octad = one palindromic superset + seven sequence trees (`OctadSheet`).

## HP vs CQE-HP

| Concept | Location | Use |
|---------|----------|-----|
| Combinatorial HP / NHyperTower | Spec §9, `HP_NHYPER_TOWER_INTEGRATION.md` | MDHG-scale superperm stack |
| CQE `hyperperm_update` | `engine/cqe/_functions.py` | Operator-order oracle (gated if `glyphs_lambda` missing) |

Do not conflate the two.

## Token metrics

- **arity** — window length along ribbon (≤ 8).
- **token_mass** — unique symbols in window.
- **mass** — dual witness: kissing proxy + TarPit `mean_mass`; NSL on disagreement.

See `transform/metrics.py` and `morph-probe` CLI.

## Multistream universal lib

1. Optional EN hub translate (`TranslateHub` stub).
2. EN stream — main ingest (`stream=en`).
3. Native / math / notation — `LibEncoder` + YAML (`ingest --stream … --lib …`).
4. TarPit-first tool pass on linked `translation_key` (`tool_pass.py`).
5. E6 plot → E8 lift (`e6_lift.py`).
6. Compose — `compose_pipeline.py` (supervisor + shell + forward).
7. Token bag / shell admit.
8. Crystal bundle v2 — `streams[]`, `translation_links.jsonl`.

**Merge rule:** single sqlite + `stream` column + `translation_links` table (Decision D1).

## Cross-links

- Substrate MVP: `MORPHONIC_SUBSTRATE_CRYSTAL_PLAN.md`
- HP tower: `HP_NHYPER_TOWER_INTEGRATION.md`
- Escrow: `NHYPER_TOWER_ESCROW.md`
- Internal spec §9: `docs/external/CMPLX_INTERNAL_SYSTEMS_SPEC.md`
