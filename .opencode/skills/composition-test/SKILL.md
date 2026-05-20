---
name: composition-test
description: "Test a non-destructive CMPLX tool/port composition and record the result with conservation/provenance notes. Use for 'test composition', 'wire tools', 'run pipeline', 'test compatibility', or parity/calibration checks."
---

# Composition Test Skill

## When to Use

- "Test if X and Y work together"
- "Run the grain chain template"
- "Verify this pipeline"
- "Test tool compatibility"

## Workflow

```
1. Run cmplx-memory-review gate for the concepts being composed
2. Confirm tools/ports exist in catalog, live src, or repo-kernel evidence
3. Choose non-destructive test input
4. Build composition graph: sequential / parallel / pipeline
5. Execute with bounded timeout and captured errors
6. Verify conservation constraints when available: dPhi / delta_phi / NSL
7. Record result to catalog/compositions/ or calibration ledger
8. Report behavior, gaps, and parity implications
```

## Checklist

```
- [ ] All tools confirmed in catalog
- [ ] Existing implementations checked
- [ ] Composition graph built
- [ ] Test input prepared (non-destructive)
- [ ] Composition executed
- [ ] Execution time recorded
- [ ] Conservation constraints verified
- [ ] Result saved to catalog/compositions/
- [ ] identity_review updated if this changes concept status
```

## Tools

**CompositionHarness** — compose(), test_pair(), test_family_composition(), test_cross_family()
**CompositionTemplate** — get_template(), create_from_template()

## Example: "Test e8_embed → bond_check"

```
1. Confirm both tools/ports exist.
2. Prepare small test input.
3. Run the harness or direct provider call.
4. Record result and conservation notes.
5. Report success, runtime, output shape, and concept implications.
```
