# GitNexus Repo-Kernel Index Review - 2026-05-13

## Completed Repo-Kernel Indexes

The interrupted heavy scan still completed useful work. Current repo-kernel
GitNexus indexes:

| Alias | Repo | Commit | Files | Symbols | Edges | Clusters | Processes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `rk-cmplx-formalization` | `CMPLX-Formalization` | `1a6617b` | 11 | 20 | 9 | 0 | 0 |
| `rk-scout-demo-service` | `scout-demo-service` | `0de180b` | 4 | 7 | 3 | 0 | 0 |
| `rk-cmplx-manny` | `CMPLX-Manny` | `9ab37f5` | 47 | 146 | 157 | 3 | 2 |
| `rk-cmplx-tmn-main` | `CMPLX-TMN-main` | `d60dfa0` | 215 | 8,931 | 13,619 | 445 | 218 |
| `rk-cmplx-tmn1` | `CMPLX-TMN1` | `bd9d52b` | 71 | 1,599 | 2,272 | 53 | 25 |
| `rk-cmplxmcp` | `CMPLXMCP` | `80edb78` | 153 | 3,294 | 6,156 | 107 | 83 |
| `rk-cmplx-monorepo` | `CMPLX-Monorepo` | `c56c785` | 630 | 18,558 | 27,620 | 512 | 300 |
| `rk-cmplxdevkit` | `CMPLXDevKit` | `49ee0eb` | 4,979 | 220,727 | 320,531 | 3,478 | 299 |
| `rk-cmplxuni` | `CMPLXUNI` | `559b13c` | 2,869 | 143,285 | 213,079 | 2,295 | 300 |

`CMPLX` and `CMPLX-1T` did not complete. A `rk-cmplx-1t` analyzer was still
running after the user stopped the scan; it was killed, leaving only the
GitNexus server process active.

## What The Output Says

`CMPLX-TMN-main` is a service-family system: many routes and controller-like
files, with high density around `bond`, `daemon`, `pipeline`, `portal`, `board`,
`crystal`, `coop`, `tarpit`, `snap_engine`, `morsr`, `personal_node`,
`speedlight_engine`, and related modules.

`CMPLXMCP` is the MCP/API adapter layer: key files include
`polyglot/polyglot-server/main.py`, `polyglot/polyglot-server/mcp_registry.py`,
`polyglot/polyglot-server/mcp_tool_loader.py`,
`polyglot/polyglot-server/mcp_tool_definitions.py`,
`cmplx_integration/registry.py`, `cmplx_integration/advanced_tools.py`, and
`server/tools.py`.

`CMPLXUNI` is the broad unified-family build: high-definition duplicate families
appear in both `src/cmplx/misc/` and `src/cmplx/unified_families/`, especially
`unified_uhp`, `unified_tarpit`, `unified_promutate_construct`,
`unified_morphonic`, `unified_quadratic_frame`, and `unified_e8`. It also
contains API surfaces in `lfai/api_server.py`, `src/cmplx/misc/web_api.py`, and
Next.js API routes.

`CMPLXDevKit` is extremely large and includes many organized external/scientific
code shards under `src/cqe_organized/`. The index completed, but its top symbol
files are dominated by imported/test/vendor-like scientific code. It needs
filtering before being used as a canonical source.

## GitNexus Limits Observed

- GitNexus query/FTS search returned empty results because it tried to create
  FTS indexes against a read-only database handle.
- `cypher` works and was used for structural counts and route/tool extraction.
- Large monoliths are skipped at the 512 KB threshold. This is desirable for the
  first pass because several repos contain multi-MB generated or bundled files.
- `CMPLX-1T` is too broad for one full GitNexus pass. It should be indexed by
  selected subdirectories or with a stronger `.gitnexusignore` first.

## Recommended Next Pass

1. Do not rerun full-root GitNexus on `CMPLX-1T`.
2. Add per-repo `.gitnexusignore` rules or run selected subdirectory indexes for:
   - `CMPLX-1T/SHOWROOM`
   - `CMPLX-1T/docker/foundation`
   - `CMPLX-1T/docker/runtime`
   - `CMPLX-1T/docker/unified/agrm_snap`
   - selected `CMPLX` core directories
3. Use completed indexes as the first composition map:
   - `CMPLX-TMN-main` for service families
   - `CMPLXMCP` for MCP/API entry layers
   - `CMPLXUNI` for unified-family implementation candidates
   - `CMPLX-Monorepo` for historical integration structure
   - `CMPLX-Formalization` for doctrine
4. Treat `CMPLXDevKit` as a large evidence/toolkit mine until filtered.
