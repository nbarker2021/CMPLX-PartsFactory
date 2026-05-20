# Validation Report

## Per-batch summary

| Batch | Spec | done | no_witness | failed | total |
|---|---|---:|---:|---:|---:|
| 1 | agenthub | 3 | 0 | 0 | 3 |
| 2 | agrm | 129 | 0 | 0 | 129 |
| 3 | aletheia | 132 | 0 | 0 | 132 |
| 4 | arena | 1 | 0 | 0 | 1 |
| 5 | brain | 85 | 0 | 0 | 85 |
| 6 | chirp | 28 | 0 | 0 | 28 |
| 7 | cmplx | 170 | 0 | 0 | 170 |
| 8 | cqe | 251 | 0 | 0 | 251 |
| 9 | daemon | 56 | 0 | 0 | 56 |
| 10 | document_decomposer | 1 | 0 | 0 | 1 |
| 11 | e8 | 251 | 0 | 0 | 251 |
| 12 | golay | 12 | 0 | 0 | 12 |
| 13 | interrogation | 44 | 0 | 0 | 44 |
| 14 | leech | 43 | 0 | 0 | 43 |
| 15 | mannyai | 1 | 0 | 0 | 1 |
| 16 | mdhg | 251 | 0 | 0 | 251 |
| 17 | mmdb | 210 | 0 | 0 | 210 |
| 18 | morphon | 251 | 0 | 0 | 251 |
| 19 | niemeier | 72 | 2 | 0 | 74 |
| 20 | pipeline | 3 | 0 | 0 | 3 |
| 21 | snap | 251 | 0 | 0 | 251 |
| 22 | swarm | 40 | 0 | 0 | 40 |
| 23 | tarpit | 251 | 0 | 0 | 251 |
| 24 | tmn | 230 | 6 | 0 | 236 |

## AST re-validation pass

- done decisions checked: **2742**
- AST-extracted name matches qualname: **2742** (100.0%)
- name MISMATCH (variant slipped past validation): **0**
- chosen source failed to parse: **0**

## Failed decisions (post-AST-validation)

Total: **0**

## No-witness decisions (spec named, index doesn't have it)

Total: **8**

- assign: 8

Sample (first 30):

| Batch | Kind | Qualname |
|---|---|---|
| 19 | assign | `ade_cols` |
| 19 | assign | `ade_vals` |
| 24 | assign | `ATLAS` |
| 24 | assign | `_DOWN_CHANNELS` |
| 24 | assign | `_E8_DOWN_ROOT` |
| 24 | assign | `_E8_UP_ROOT` |
| 24 | assign | `_META_CHANNELS` |
| 24 | assign | `_UP_CHANNELS` |

## Variant count distribution (done decisions)

How many distinct exact-source variants were observed per chosen pick:

| variants | decisions |
|---:|---:|
| 1 | 905 |
| 2 | 411 |
| 3 | 226 |
| 4 | 368 |
| 5 | 128 |
| 6 | 116 |
| 7 | 99 |
| 8 | 128 |
| 9 | 38 |
| 10 | 54 |
| 11 | 19 |
| 12 | 24 |
| 13 | 5 |
| 14 | 17 |
| 15 | 7 |
| 16 | 7 |
| 17 | 4 |
| 18 | 4 |
| 19 | 9 |
| 20 | 15 |
| 21 | 1 |
| 22 | 18 |
| 23 | 6 |
| 24 | 7 |
| 26 | 4 |
| 27 | 5 |
| 28 | 7 |
| 29 | 13 |
| 30 | 6 |
| 31 | 2 |
| 32 | 4 |
| 33 | 2 |
| 34 | 1 |
| 36 | 1 |
| 37 | 2 |
| 38 | 16 |
| 40 | 12 |
| 44 | 4 |
| 45 | 7 |
| 48 | 1 |
| 60 | 2 |
| 66 | 8 |
| 71 | 5 |
| 76 | 9 |
| 497 | 15 |

## Most-absorbed decisions (top 25 by # of alternatives considered)

| Batch | Kind | Qualname | Picked replicas | # alternatives |
|---|---|---|---:|---:|
| 7 | class | `E8Lattice` | 28 | 28 |
| 8 | class | `E8Lattice` | 28 | 28 |
| 11 | class | `E8Lattice` | 28 | 28 |
| 18 | class | `E8Lattice` | 28 | 28 |
| 2 | function | `demo` | 6 | 49 |
| 8 | function | `demo` | 6 | 49 |
| 11 | function | `demo` | 6 | 49 |
| 13 | function | `health` | 7 | 49 |
| 16 | function | `health` | 7 | 49 |
| 17 | function | `health` | 7 | 49 |
| 18 | function | `health` | 7 | 49 |
| 24 | function | `health` | 7 | 49 |
| 2 | assign | `__all__` | 29 | 49 |
| 3 | assign | `__all__` | 29 | 49 |
| 5 | assign | `__all__` | 29 | 49 |
| 8 | assign | `__all__` | 29 | 49 |
| 11 | assign | `__all__` | 29 | 49 |
| 14 | assign | `__all__` | 29 | 49 |
| 16 | assign | `__all__` | 29 | 49 |
| 17 | assign | `__all__` | 29 | 49 |
| 18 | assign | `__all__` | 29 | 49 |
| 21 | assign | `__all__` | 29 | 49 |
| 23 | assign | `__all__` | 29 | 49 |
| 8 | assign | `app` | 7 | 49 |
| 11 | assign | `app` | 7 | 49 |
