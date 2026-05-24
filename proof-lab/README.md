# Proof Lab

Docker-hosted **active clone** of this repository for formal, machine-checkable validation used in presentations and proof packets.

## Architecture

| Component | Role |
|-----------|------|
| `packages/lattice-forge` | Installable **proven** library (theorems, proofs, Tier A falsify) |
| `proof-lab` HTTP `:8871` | Runs pytest + proofs + regression + Tier A; writes `artifacts/bundles/` |
| `packages/lattice-forge-testkit-mcp` | **Non-proven** MCP toolkit (CONJ, Tier B, pytest subsets) on `:8872` |

## Quick start

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
docker network create cmplx-backend 2>$null
make proof-lab-up
make proof-lab-verify
```

Host-only (no Docker):

```powershell
make -C proof-lab install
make -C proof-lab formal-bundle
```

## Formal docs

- `REQUIREMENTS.md` — FR/NFR split
- `accounting/proof_surfaces.yaml` — proven vs testkit accounting
