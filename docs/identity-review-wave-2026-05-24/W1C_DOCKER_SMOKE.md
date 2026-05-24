# W1c Docker runtime smoke (stream 1)

Canonical script (PartsFactory workspace, not in this git repo):

`D:\PartsFactory\identity_review\scripts\run_w1c_docker_smoke.py`

Report: `identity_review/reports/w1c-docker-smoke-2026-05-24.json`  
Checkpoint: `identity_review/checkpoints/2026-05-24-034-w1c-docker-smoke.md`

## CMPLX compose slice

```powershell
docker network create cmplx-backend 2>$null
docker compose -f docker-compose.lattice-forge.yml up -d
curl http://localhost:8845/health
curl http://localhost:8845/witness/spec
```

Witness persistence: `FORGE_WITNESS_DB` on overlay volume (see `docker-compose.lattice-forge.yml`).
