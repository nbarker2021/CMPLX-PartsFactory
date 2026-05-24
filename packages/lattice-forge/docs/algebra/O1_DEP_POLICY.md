# O(1) deps vs ported constants

## Rule

| Established lib gives | Action |
|----------------------|--------|
| **O(1)** lookup (order, rank, fixed small table) | **Port into** `lattice_forge.algebra.o1_registry` — no runtime CAS |
| **Bounded** (e.g. 240 E₈ roots) | **Port once** into seed / `ledger.roots` (already done) |
| **Unbounded** (696M Weyl elements, full glue cosets) | **Custom batched** `backwalk` + checkpoints — never a pip dep loop |

Optional **`lattice-forge[theory]`** adds SymPy only for `scripts/verify_algebra_o1.py` (CI/dev), not Docker proof-lab.

## Already O(1) in this repo (keep as native code)

| Quantity | Where |
|----------|--------|
| 8×8 chart Weyl route | `substrate_map.route(src, tgt)` |
| Weyl involution partner | `WEYL_13_TABLE[i]` |
| \|W(E₈)\| | `algebra.o1_registry.E8_WEYL_ORDER` |
| E₈ root shell | `ledger.roots.root_system_E8()` (≤240 vectors, build-time) |
| 24 Niemeier terminals | `ledger.build.NIEMEIER_FORMS` |

## Not O(1) — do not add as runtime deps

| Quantity | Why |
|----------|-----|
| Iterate all of W(E₈) | 696,729,600 elements |
| Full Niemeier overlattice glue | coset enumeration per terminal |
| Arbitrary lattice reduction | LLL / fpylll — use only if solver profile added later |

## Libraries (reference only)

| Lib | Use here |
|-----|----------|
| SageMath `WeylGroup(['E',8]).order()` | Verify `E8_WEYL_ORDER` in theory CI |
| SymPy `liealgebras` | Same — optional cross-check |
| LiE (`lie` package) | Requires binary; not a constant dep |
| fpylll | Only if we add explicit LLL solver phase |

## Verify (optional)

```powershell
pip install -e "./packages/lattice-forge[theory]"
python packages/lattice-forge/scripts/verify_algebra_o1.py
```
