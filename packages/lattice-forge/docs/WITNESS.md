# Witness API — ledger vs readout

Canonical routes live under `/witness/*` on port **8845** (CMPLX `WorldsForgeProvider`) or standalone `lattice-forge serve`.

## Naming collision (intentional)

| Route | Meaning |
|-------|---------|
| `POST /witness/classify` | **Ledger** morphism witness classification (`WitnessEngine.classify`) |
| `POST /witness/readout/classify` | **LCR** local readout path (`shell2` vs `default_cr`) |

Do not confuse ledger classify with LCR classify.

## Regimes

| Route | Regime | Backing |
|-------|--------|---------|
| `POST /witness/regime-a/query` | A | Block tower / checkpoint I/O |
| `POST /witness/regime-c/encode` | C | `chart_codec` + shell2 subtrajectory |
| `POST /witness/regime-cprime/encode` | C′ | `chart_codec_d4` |
| `POST /witness/syndrome` | ECC/shed | Structured report + TarPit labels |

## Proof bundles

| Route | Scope |
|-------|--------|
| `POST /witness/proof-bundle` | Proof-obligation ledger verify (honest `pass_with_open_gaps`) |
| `POST /witness/proof-bundle/full` | Full `run_all_proofs` report (`quick` caps depth) |

## Receipt mint

When mounted via CMPLX `http_service`, ledger/regime-a/proof routes mint through `mint_forge_operation` when the router receives a `mint_fn`. **Never** map `pass_with_open_gaps` to unconditional `pass` in mint payloads.

Legacy flat `*-mint` routes from pass 1 were removed; use canonical `/witness/*` paths.
