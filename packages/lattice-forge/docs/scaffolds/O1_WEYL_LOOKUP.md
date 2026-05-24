# O1 — W(E_8) Weyl lookup (engineering epic)

**Status:** CONJ / engineering stub — not in Ring 1 prize envelope.

See `docs/umbrella/theorems/OPEN_OBLIGATIONS.md` (O1) and `src/lattice_forge/o1_weyl_lookup.py`.

## Harness (honest)

- `weyl_lookup_table_stub(n)` → `status: conj`, `table_populated: false`
- Umbrella key `VOA_LOOKUP` reports **CONJ** via `verify_voa_lookup_harness()`

## Milestones (no 2.6GB table in-repo)

| Phase | Deliverable |
|-------|-------------|
| M0 | API contract + stub tests |
| M1 | External shard index spec |
| M2 | Lazy loader + bounded spot checks |
| M3 | McKay-Thompson parity (O1') |
| M4 | Optional manifest companion |

## Do not

- Promote `rule30.prize.depth_only_shortcut` from CONJ
- Map `pass_with_open_gaps` to unconditional `pass`

See also `docs/scaffolds/EPIC_O1_WEYL_LOOKUP.md`.
