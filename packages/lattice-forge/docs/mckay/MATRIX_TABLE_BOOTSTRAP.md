# McKay-Thompson matrix table bootstrap (5×5, 7×7, 9×9)

## Purpose

Materialize **global convolution matrices** for the five tabulated Monster conjugacy
classes (`1A`, `2A`, `3A`, `5A`, `7A`) at bootstrap dimensions **5, 7, and 9**.
These are the portable tables any proof harness or pip install can load without
Sage/LiE.

## API

```python
from lattice_forge.mckay_matrix_tables import (
    j_matrix_for_class,
    build_conjugate_set_tables,
    verify_mckay_matrix_bootstrap,
    export_matrix_catalog,
)

m9 = j_matrix_for_class("3A", 9)   # 9×9, a₁ anchor 783
m7 = j_matrix_for_class("7A", 7)   # 7×7, a₁ anchor 51
m5 = j_matrix_for_class("5A", 5)   # 5×5, a₁ anchor 134
```

CLI:

```bash
lattice-forge mckay-matrices verify
lattice-forge mckay-matrices export --out ./mckay_matrix_catalog.json
```

## Conjugate-set layout

| Class | Lane (5-lane) | Preferred dim | Role |
|-------|---------------|---------------|------|
| 1A | C | 9 | j−744 center / identity |
| 2A | C | 9 | correction partner (axis 2, sheet 0) |
| 3A | C | 9 | level-9 hauptmodul hub |
| 5A | L | 5 | pentic left chirality |
| 7A | R | 7 | pentic right chirality |

All five classes also receive **9×9** tables when coefficient length allows
(bootstrap into the same `V_9` shell as `j_modular_matrix`).

## Proofs produced (`verify_mckay_matrix_bootstrap`)

- Every class has valid **5×5, 7×9, 9×9** tables (where coeffs permit).
- **3A** `J[1,0]=783`, **2A** `J[1,0]=4372`.
- Lower-triangular convolution shape; diagonal ones.
- **7×7** leading block equals top-left **7×7** of **9×9** (nesting).
- Parity rows `k=1..9` match `mckay_thompson_coefficient_parity`.

Honesty: **BOUNDED_EXEC** (hardcoded Atlas truncations, not full `T_g` series).

## Global expansion path

1. Extend `voa_harness.T_*_COEFFICIENTS` (or load from JSON catalog).
2. Re-run `export_matrix_catalog` → ingest into proof-lab / `proof_capture_queue`.
3. Wire new classes into `five_lane_router` and `g2_f4_t5_conjugate` depth tables.
4. Optional: add **11×11** when 11A coefficients are tabulated (not in v0 bootstrap).
