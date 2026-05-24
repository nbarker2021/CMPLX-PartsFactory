# Proof Lab — formal requirements

## Purpose

Provide a **reproducible, machine-checkable** validation surface for Lattice Forge / Rule 30 work that feeds presentations, whitepapers, and formal proof packets. The lab runs in Docker against an **active, push-ready** clone of `CMPLX-PartsFactory`.

## Surfaces (split)

| Surface | Delivery | Contents |
|---------|----------|----------|
| **Proven / formalized** | Installable Python package `lattice-forge` (`packages/lattice-forge`) | Ring-1 theorems (T1–T8, BONUS), transported IT/P rows, bounded obligations with verifiers, proof scripts, `claims/registry.jsonl` PROVEN rows, falsify Tier A breaks |
| **Non-proven / test toolkit** | MCP server `lattice-forge-testkit-mcp` | CONJ and exploratory claims, Tier B falsify, pytest subsets, regime/umbrella probes, companion `pass_with_open_gaps` harness controls |

## Functional requirements

### FR-1 Repository fidelity

- Container bind-mounts host repo at `/workspace/CMPLX-PartsFactory` (read-write for `proof-lab/artifacts/` only under that tree).
- On start, record `git rev-parse HEAD`, branch, and dirty flag into `proof-lab/artifacts/meta/last_clone.json`.

### FR-2 Proven validation (library path)

- `pip install -e "packages/lattice-forge[all]"` and `pip install -e ".[dev]"` inside the lab image.
- `make verify` (or `make formal-bundle`) runs: pytest (package + worlds forge), `run_all_proofs --quick`, expected_outputs regression, falsify `--tier-a`.
- Outputs land in `proof-lab/artifacts/` with timestamped bundles for presentation export.

### FR-3 Non-proven toolkit (MCP path)

- MCP SSE at `http://localhost:8872/mcp/sse` (service `lf-testkit-mcp`).
- Tools must not promote CONJ claims to PROVEN; they only **execute** or **report** test state.
- Tier B falsify and selective pytest are exposed for agent-driven exploration.

### FR-4 Accounting

- `proof-lab/accounting/proof_surfaces.yaml` is the canonical split manifest.
- Each formal bundle includes: git meta, `proofs_report.json`, claims snapshot, falsify tier-a JSON.

### FR-5 Operations

- `docker compose -f docker-compose.proof-lab.yml up -d`
- Health: `curl http://localhost:8871/health` (proof runner), `curl http://localhost:8872/health` (testkit MCP)

## Non-goals

- Not a replacement for GitHub Actions (`lattice-forge-family.yml`); CI remains authoritative for merges.
- Not a write path to Postgres or evidence substrate without explicit approval.
