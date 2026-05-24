# Transport lemma registry (stub)

Backlog for sheet-lift / torsor-functor / glue transport lemmas. Companion
**WP-TOWER-01** pairs only when ≥5 rows move from **TO_ADD** to **PROVEN**.

| moment | lemma_id | verifier | status | notes |
|--------|----------|----------|--------|-------|
| sheet_lift | transport.sheet_lift.finite_window | `verify_rule30_sheet_lift` | pass_with_open_gaps | Bounded N window; not global closure |
| torsor_functor | transport.torsor_functor.coherence | `verify_rule30_torsor_functor_term` | pass_with_open_gaps | Functor term checked at declared depth |
| glue_O7 | transport.glue.julia_resolution | `verify_rule30_julia_resolution` | pass_with_open_gaps | O7 glue via Julia resolution stack |
| field_address | transport.field_address.mandelbrot | `verify_rule30_mandelbrot_field_address` | pass_with_open_gaps | Harness key `TRANSPORT_FIELD_ADDRESS` |
| exit_trajectory | transport.exit_trajectory.julia | `verify_rule30_exit_trajectory` | pass_with_open_gaps | Harness key `TRANSPORT_EXIT_TRAJECTORY` |

## Honesty

Statuses **PROVEN** | **CONJ** | **TO_ADD** | **pass_with_open_gaps** only. Do not
map `rule30.prize.depth_only_shortcut` to PROVEN.

## Extra

Install stub: `pip install -e "packages/lattice-forge[transport-tower]"` (empty dep set).

## Sidecar link

Deferred in manifest until backlog closes:

```yaml
deferred_whitepapers:
  - id: WP-TOWER-01
    trigger: ">=5 transport lemma rows move from TO_ADD to PROVEN"
```

Currently **0 TO_ADD** rows; **5 pass_with_open_gaps** (not PROVEN) — WP-TOWER-01 remains deferred until ≥5 rows reach **PROVEN**.
