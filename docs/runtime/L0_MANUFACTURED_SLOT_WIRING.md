# L0 manufactured slot runtime wiring

**UNIFICATION_PREP_PLAN** checklist item: L0 runtime wiring (HTTP adapters → repo-kernel / compose).

## Source of truth

| Artifact | Role |
|----------|------|
| `catalog/bootstrap_manifest.json` | 18 bootstrap ports / parts |
| `catalog/manufactured_slot_upstream.json` | Host health URLs + repo-kernel global lanes |
| `src/runtime/bootstrap_registry.py` | In-process provider registration |
| `docs/identity-review-wave-2026-05-24/scripts/run_w1c_docker_smoke.py` | Direct slot health + :8845 witness |
| `docs/identity-review-wave-2026-05-24/scripts/run_l0_runtime_wiring_smoke.py` | Repo-kernel global lane smoke |

## Policy

1. **Agents and live work** should call `http://localhost:8786/api/global/<system>/...` first.
2. **W1c / L0 smoke scripts** may probe upstream localhost ports for honest runtime proof.
3. **Writes** remain call-plan / receipt gated — this wiring is read-only.

## Slot → global lane map

See `catalog/manufactured_slot_upstream.json` for the full table (receipt, speedlight, snap,
tarpit, mdhg, mmdb, lattice-forge worlds).

## Lattice Forge (:8845)

- HTTP adapter: `src/cmplx/worlds/forge/_adapters/http_service.py`
- Witness routes: `/witness/spec`, `/witness/regime-c/encode`, …
- Persistent witness index: `overlay/witness/state.sqlite` via `Forge.open(root)` or `FORGE_WITNESS_DB`

## Verify

```powershell
python docs/identity-review-wave-2026-05-24/scripts/run_l0_runtime_wiring_smoke.py
python docs/identity-review-wave-2026-05-24/scripts/run_w1c_docker_smoke.py
```

Both require Docker Desktop engine running for green gates.
