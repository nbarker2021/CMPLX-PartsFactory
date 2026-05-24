# Checkpoint 034 — W1c Docker runtime smoke + lattice-forge :8845 witness

**Date:** 2026-05-24  
**Slot:** 19 (`docker-compose.lattice-forge.yml`, port 8845)  
**Script:** `identity_review/scripts/run_w1c_docker_smoke.py`  
**Report:** `identity_review/reports/w1c-docker-smoke-2026-05-24.json`

## Scope

- Extend W1c probes: `:8845/health`, `/witness/spec`, `POST /witness/regime-c/encode`, `POST /witness/proof-bundle`
- Required set includes `lattice-forge` when Docker stack is up
- Honesty: witness POST samples record `honesty_status` — no gap laundering

## Result

See JSON report `all_required_ok` and `forge_routes_ok`. If Docker Desktop engine is down, run is **skipped** (exit 1) — same discipline as checkpoint 032.

## Compose (when Docker up)

```powershell
docker network create cmplx-backend 2>$null
cd D:\PartsFactory\CMPLX-PartsFactory
docker compose -f docker-compose.repo-kernel.yml up -d
docker compose -f docker-compose.receipt.yml up -d
docker compose -f docker-compose.speedlight.yml up -d
docker compose -f docker-compose.snap.yml up -d
docker compose -f docker-compose.tarpit.yml up -d
docker compose -f docker-compose.lattice-forge.yml up -d
python D:\PartsFactory\identity_review\scripts\run_w1c_docker_smoke.py
```
