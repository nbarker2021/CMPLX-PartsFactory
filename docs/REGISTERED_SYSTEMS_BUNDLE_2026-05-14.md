# Registered Systems Bundle

Generated: 2026-05-14

## Purpose

PartsFactory is the housing yard. Registered repos are the systems being
wrapped, compared, and eventually unified.

The default bundle now wraps all registered repos, excluding `CMPLX-PartsFactory`
and `scout-demo-service`:

| Order | Repo | Role | Handling |
| ---: | --- | --- | --- |
| 1 | `CMPLX-Formalization` | `mathematical_doctrine` | Kept as a document/specification system. |
| 2 | `CMPLXMCP` | `mcp_layer` | Kept as its own MCP/tool system. |
| 3 | `CMPLXUNI` | `unified_system_build` | Kept as its own unified-system checkout. |
| 4 | `CMPLX-Monorepo` | `historical_monorepo_reference` | Kept as a reference system, not flattened. |
| 5 | `CMPLX` | `baseline_core` | Kept as baseline core. |
| 6 | `CMPLXDevKit` | `developer_toolkit` | Kept as developer toolkit. |
| 7 | `CMPLX-1T` | `geometric_system_build` | Kept as geometric system build. |
| 8 | `CMPLX-TMN1` | `tmn_historical_build` | Kept as historical TMN build. |
| 9 | `CMPLX-TMN-main` | `tmn_primary` | Kept as primary TMN system. |
| 10 | `CMPLX-Manny` | `manny_identity_system` | Kept as Manny identity system. |

## Wrapper Contract

The wrapper does not flatten source. Each repo keeps its own checkout,
settings, paths, and command working directory.

API:

- `GET /api/registered-bundle`
- `POST /api/registered-bundle`
- `POST /api/registered-bundle/run`

MCP:

- `repo_kernel_registered_bundle`
- `repo_kernel_registered_bundle_run`

CLI:

```powershell
python scripts\registered_systems_bundle.py describe
python scripts\registered_systems_bundle.py run status
python scripts\registered_systems_bundle.py run probe
python scripts\registered_systems_bundle.py run tree
python scripts\registered_systems_bundle.py --count 2 run status
```

Native repo commands are allowlisted and dry-run by default:

```powershell
python scripts\registered_systems_bundle.py run native-verify
python scripts\registered_systems_bundle.py run native-verify --execute-native
```

At this stage only `CMPLXMCP` has an allowlisted native verify command:
`python verify-mcp.py`.

## Next Work

With all registered repos behind the wrapper, repeat the same loop repo by repo
or with bounded `--count` slices:

1. Wrap it without moving source.
2. Confirm its status/probe/surface behavior through the shared API and CLI.
3. Record any old paths pointing at missing history.
4. Repath those references to current `repo_kernel/repos/...` or PartsFactory
   staging paths.
5. Compare the growing bundle against historical evidence to find what is still
   absent from the current build.
