# Lattice Forge — install notes

## Editable install (preferred)

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
pip install -e "packages/lattice-forge[all]"
```

## TLS / CA bundle failure on Windows

**Symptoms:** `pip install -e` fails with SSL errors referencing an invalid
`SSL_CERT_FILE` or `REQUESTS_CA_BUNDLE` path (often a stale corporate CA file).

**Workaround — PYTHONPATH mode (no pip install):**

```powershell
$env:PYTHONPATH = 'D:\PartsFactory\CMPLX-PartsFactory\packages\lattice-forge\src'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest packages/lattice-forge/tests -q
```

Or source the helper:

```powershell
. D:\PartsFactory\CMPLX-PartsFactory\scripts\dev_lattice_forge_env.ps1
```

**Fix pip TLS:** clear or fix the env vars, then retry editable install:

```powershell
Remove-Item Env:SSL_CERT_FILE -ErrorAction SilentlyContinue
Remove-Item Env:REQUESTS_CA_BUNDLE -ErrorAction SilentlyContinue
pip install -e "packages/lattice-forge[all]"
```

## Dev canonical vs git package

Edit `D:\PartsFactory\work\lattice-forge` first, then sync:

```powershell
.\scripts\sync_lattice_forge_package.ps1
```

## Local family verification

```powershell
.\scripts\verify_lattice_forge_family.ps1
```

Optional sync drift check:

```powershell
.\scripts\verify_lattice_forge_family.ps1 -CheckSync
```
