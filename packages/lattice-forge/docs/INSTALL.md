# Installing Lattice Forge

Lattice Forge is a standard Python package (stdlib + bundled seed SQLite only). No Sage, LiE, or SymPy is required at runtime.

## From a local checkout

```bash
cd packages/lattice-forge
python -m pip install -e .
```

## From the monorepo root

```bash
python -m pip install -e "./packages/lattice-forge"
```

## From Git (any machine with Python 3.10+)

```bash
python -m pip install "git+https://github.com/nbarker2021/CMPLX-PartsFactory.git#subdirectory=packages/lattice-forge"
```

## Optional extras

| Extra | Purpose |
|-------|---------|
| `[theory]` | SymPy cross-check for O(1) algebra constants (`lattice-forge-verify-algebra`) |
| `[server]` | FastAPI HTTP server (`lattice-forge serve`) |
| `[test]` | pytest for development |
| `[all]` | All optional components |

```bash
pip install "lattice-forge[theory]"
lattice-forge-verify-algebra
```

## Console commands

After install, these entry points are on `PATH`:

| Command | Role |
|---------|------|
| `lattice-forge` | Core admissibility CLI (seed verify, terminal trees, Rule 30, …) |
| `lattice-forge-backwalk` | Niemeier backward-category builder (pilot / full24) |
| `lattice-forge-weyl-bond` | Quadrant-sharded dual Weyl-bond orchestrator |
| `lattice-forge-lattice-space` | Full lattice-space exhaustion job |
| `lattice-forge-verify-algebra` | Optional O(1) registry verify |

Equivalent nested commands:

```bash
lattice-forge backwalk run --phase pilot
lattice-forge weyl-bond run --all-quadrants --resume
lattice-forge lattice-space run --resume
```

## Writable state (pip / bare metal)

Defaults (no Docker):

- Work DB: `./.lattice_forge/backwalk/backwalk_work.db`
- Reports: same directory (`baseline_report.json`, `weyl_bond_orchestrator_report.json`, …)

Override with environment variables:

```bash
export LATTICE_FORGE_WORK_DB=/path/to/backwalk_work.db
export LATTICE_FORGE_BACKWALK_DIR=/path/to/backwalk
```

## Typical backwalk sequence

```bash
lattice-forge-backwalk --phase pilot
lattice-forge-backwalk --phase full24 --resume
lattice-forge-weyl-bond --all-quadrants --resume
lattice-forge-lattice-space --resume
```

## Python API

```python
from lattice_forge import Forge
from lattice_forge.backwalk import WorkStore, materialize_terminals, PILOT_TERMINAL_IDS
from lattice_forge.algebra.o1_registry import E8_WEYL_ORDER, weyl_order

forge = Forge.open()
print(weyl_order("E8"), E8_WEYL_ORDER)

with WorkStore(".lattice_forge/backwalk/backwalk_work.db") as store:
    materialize_terminals(store, list(PILOT_TERMINAL_IDS), resume=False)
```

## Docker (optional)

For reproducible batch jobs with a named volume, use the compose files in the CMPLX-PartsFactory repo root (`docker-compose.backwalk-*.yml`). Containers set `LATTICE_FORGE_WORK_DB=/data/backwalk_work.db`.

See `docs/backwalk/DEPLOY.md` in the monorepo when present, or `docs/backwalk/BASELINE_PILOT.md`.
