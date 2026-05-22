# CMPLX vendored packages

Installable packages synced from `D:\PartsFactory\work\` development trees.

## lattice-forge

Rule 30 / Niemeier admissibility engine (dual-home with `src/cmplx/worlds/forge`).

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
pip install -e "./packages/lattice-forge[test]"
```

CMPLX `tests/worlds/` also prepends `packages/lattice-forge/src` via `tests/conftest.py`
when the package is not installed (vendored dev layout).

Promotion sync (work → package):

```powershell
.\scripts\sync_lattice_forge_package.ps1
```

Development canonical root remains `D:\PartsFactory\work\lattice-forge`; commit vendored copies under `packages/lattice-forge/` after intentional promotion.
