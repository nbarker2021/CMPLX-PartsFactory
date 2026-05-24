# CMPLX vendored packages

Installable packages synced from `D:\PartsFactory\work\` development trees.

## lattice-forge

Rule 30 / Niemeier admissibility engine (dual-home with `src/cmplx/worlds/forge`).

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
.\scripts\dev_lattice_forge_env.ps1
.\scripts\verify_lattice_forge_family.ps1
pip install -e "./packages/lattice-forge[all]"   # extras: algebra,solver,theory,proofs,server,witness,decomposition
```

If `pip install -e` fails (bad `SSL_CERT_FILE`), use `PYTHONPATH` — see `packages/lattice-forge/docs/INSTALL.md`.

CMPLX `tests/worlds/` also prepends `packages/lattice-forge/src` via `tests/conftest.py`
when the package is not installed (vendored dev layout).

Promotion sync (work → package):

```powershell
.\scripts\sync_lattice_forge_package.ps1
```

Version **0.2.0-family**: witness API completion, decomposition vendor, local `verify_lattice_forge_family.ps1` (no new GHA workflow).

Development canonical root remains `D:\PartsFactory\work\lattice-forge`; commit vendored copies under `packages/lattice-forge/` after intentional promotion.
