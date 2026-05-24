# Reproduction Guide

Every proven theorem in `03_PROVEN_THEOREMS.md` is reproducible by extracting the companion executable package and running the verification harness. This guide gives step-by-step instructions.

## Setup

### 1. Extract the executable package

```
unzip lattice-forge-executable-build.zip -d ./lattice-forge-build/
cd lattice-forge-build/
```

### 2. Python environment

```
# Python 3.10+ recommended; no external dependencies required for the proofs.
# Optional: install fastapi+uvicorn for the API server tests.

python --version    # confirm 3.10+
```

### 3. Run the full proofs harness

```
python scripts/run_all_proofs.py
```

Expected runtime: ~3-5 minutes on consumer hardware. Output:

- Console: human-readable summary per theorem
- `proofs_report.json`: machine-readable status, residuals, check counts
- `proofs_report.json.sha256`: SHA-256 of the report for tamper-evidence

### 4. Compare against expected output

```
python scripts/verify_proofs_report.py
```

This compares `proofs_report.json` against `expected_outputs.json` and exits 0 if all theorems pass.

---

## Per-theorem reproduction

### T1: Octonion algebra axioms

```
python -c "from lattice_forge.octonion import verify_octonion_axioms; import json; print(json.dumps(verify_octonion_axioms(), indent=2))"
```

Expected: `"status": "pass"`, `"errors": []`.

### T2: J₃(𝕆) Jordan algebra axioms

```
python -c "from lattice_forge.jordan_j3 import verify_j3o_axioms; import json; print(json.dumps(verify_j3o_axioms(), indent=2))"
```

Expected: `"status": "pass"`, `"errors": []`.

### T3: Chart ↔ J₃(𝕆) isomorphism

```
python -c "from lattice_forge.rule30 import verify_chart_j3o_isomorphism; import json; r = verify_chart_j3o_isomorphism(max_depth=4096); print(json.dumps({k:v for k,v in r.items() if k != 'first_failures'}, indent=2))"
```

Expected:
```json
{
  "status": "pass",
  "bijection_failures": 0,
  "trace_mismatches": 0,
  "weyl_mismatches": 0,
  "readout_mismatches": 0,
  "trace_2_stratum_count": 1568,
  "trace_2_idempotent_count": 1568,
  "trace_2_all_idempotent": true
}
```

### T4: Exact rational n=3 SU(3) Weyl closure

```
python -c "from lattice_forge.f4_action import verify_n3_su3_closure_exact; import json; print(json.dumps(verify_n3_su3_closure_exact(), indent=2))"
```

Expected:
- `"status": "pass"`
- `"residual_squared_exact": "0"` (string "0", from Fraction arithmetic)
- `"is_exact_group_ring_element": true`
- `"s3_coefficients_exact_strings": {"e": "0", "(1 2)": "1/3", "(1 3)": "1/3", "(2 3)": "1/3", "(1 2 3)": "0", "(1 3 2)": "0"}`

### T5: Idempotency of M₃ and closure scale search

```
python -c "from lattice_forge.f4_action import search_for_su3_closure_scale; import json; r = search_for_su3_closure_scale(max_scale=16); print(json.dumps(r['results_per_scale'], indent=2))"
```

Expected: residual `~8e-1` at n=1, `~4e-1` at n=2, `~2.5e-16` at n=3, machine zero at n≥3.

### T6: Both trace-blocks close identically

```
python -c "from lattice_forge.f4_action import decompose_8x8_via_block_action_exact; import json; r = decompose_8x8_via_block_action_exact(n_steps=3); print(json.dumps(r['claim'], indent=2))"
```

Expected:
- `"trace_grading_preserved_at_n_steps": false` (cross-block transitions exist)
- `"both_trace_blocks_close_as_s3_elements": true`

### T7: Closed-form 8x8 from Rule 30 truth table

```
python -c "from lattice_forge.f4_action import closed_form_rule30_8x8_transition_exact; r = closed_form_rule30_8x8_transition_exact(); print(r['matrix'][0])"
```

Expected: row of Fractions for state (0,0,0) showing `[1/4, 1/4, 0, 0, 1/4, 1/4, 0, 0]` (exact rationals).

### T8: F₄ → Niemeier paths (commutability tree)

```
python -c "
import tempfile, pathlib
from lattice_forge import Forge
forge = Forge.open(pathlib.Path(tempfile.mkdtemp(prefix='lf-verify-')))
niemeiers = ['Niemeier:E8^3', 'Niemeier:D16_E8', 'Niemeier:A17_E7', 'Niemeier:D10_E7^2',
             'Niemeier:A11_D7_E6', 'Niemeier:E6^4', 'Niemeier:A5^4_D4', 'Niemeier:D4^6']
for t in niemeiers:
    r = forge.can_close('F4', t).get('result', {}).get('can_close', {})
    print(f'{t}: {r.get(\"answer\")} via {r.get(\"path\")}')"
```

Expected: 8 lines, each showing `yes_with_template_glue` and a specific path through D₄, E₆, E₇, or G₂×F₄→E₈.

---

## Test suite

The package ships with a pytest-based test suite covering CLI and API surfaces:

```
cd lattice-forge-build/
python -m pytest tests/ -q
```

Expected: 30 passed.

## Smoke test

```
cd lattice-forge-build/
$env:PYTHONPATH = "src"      # PowerShell
python scripts/smoke.py
```

Expected output (last line): `SMOKE_OK`

---

## Troubleshooting

**ImportError for `lattice_forge`:** Set `PYTHONPATH=src` (Linux/macOS: `export PYTHONPATH=src`; Windows PowerShell: `$env:PYTHONPATH="src"`).

**Slow runtime for `verify_chart_j3o_isomorphism(4096)`:** The CA simulation is O(n²) total; ~30 seconds is normal. Reduce `max_depth=128` for a quick smoke check.

**Output differs from expected:** Check Python version (must be 3.10+); check that no source files were modified; rerun in a fresh directory.

---

## Verification of authenticity

To verify this submission has not been tampered with:

```
python scripts/run_all_proofs.py
sha256sum proofs_report.json
# Compare against the expected SHA-256 in expected_outputs.json
```

The SHA-256 is deterministic given the same source code and Python version. Any deviation indicates either a code modification or a Python-arithmetic-differs-from-our-implementation issue.

---

## Contact

For reproduction issues, refer to the file inventory in `MANIFEST.md` to confirm all files are present.
