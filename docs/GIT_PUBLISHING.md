# Git publishing — CMPLX-PartsFactory

Repo: `D:\PartsFactory\CMPLX-PartsFactory` (initialized, **no commits yet** on `main`).
Remote: `origin https://github.com/nbarker2021/CMPLX-PartsFactory.git`.

Generated runtime output should go to `CMPLX_RUNTIME_DIR`, defaulting on this
machine to `D:\PartsFactory\runtime\CMPLX-PartsFactory`. Do not let new scripts
default to repo-local `data/`, `reports/`, or `export/` unless that path is
explicitly ignored and documented as disposable.

## Before first commit

1. Confirm `.gitignore` excludes catalog trees (`CMPLX-1T/`, `CMPLX-Manny/`, …).
2. Confirm imported repo bodies stay ignored or are represented only as submodule gitlinks through `.gitmodules`, `repo_kernel/manifest/repos.json`, and `repo_kernel/manifest/linking_policy.json`.
3. Confirm generated outputs are ignored: `data/*.sqlite*`, `repo_kernel/repos/*`, `repo_kernel/state/`, `repo_kernel/quarantine/`, `reports/`, `results/`, `export/`, caches, archives, and local agent package caches.
4. No secrets: `.env`, `*.pem`, `*.key`, `*.p12`, `*.pfx` are ignored. `SECRETS_ROTATION_REQUIRED.md` is tracked as a reminder only — rotate before public remote.
5. Confirm the GitHub remote exists and is accessible.

## First commit (local)

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
git add -A
git status   # verify repo_kernel/repos/* appear as submodules, not file trees
git commit -m "Initial publish: src/cmplx landing pad, services, repo-kernel, tests"
```

## Push

```powershell
git push -u origin main
```

## Scope policy

| Track | Do not track |
|-------|----------------|
| `src/cmplx/**` | `CMPLX-1T/`, `CMPLX-Manny/`, `CMPLXUNI/` |
| `services/`, `tests/`, `docs/` | `staging/`, `data/*.sqlite*`, `data/*.db` |
| `.gitmodules`, `repo_kernel/repos/*` gitlinks | repo-kernel repo contents as parent-tracked files |
| `docker-compose*.yml`, `pyproject.toml` | `repo_kernel/state/`, `repo_kernel/quarantine/` |
| `.opencode` skills/agents/tools, `.agents`, selected `.claude` skills | `.opencode/node_modules`, local package locks |
| selected small fixtures under `data/` | generated calibration/run/export outputs |

Iteration trail stays in `D:\PartsFactory\CMPLX-history\` and PartsFactory `work/`.

## Linked Repo Policy

Treat historical and sibling repos as submodule pointers when they have stable
remotes and pinned commits, not as vendored source. Their content is already
tracked in their own repositories, and this repo should track their identity,
role, local path, and pinned commit rather than copying their files into the
first commit.

`repo_kernel/manifest/repos.json` is the canonical discovered repo list.
`repo_kernel/manifest/linking_policy.json` records the superproject decision
layer. `.gitmodules` now carries active submodule pointers for stable
`repo_kernel/repos/*` checkouts, each with `ignore = dirty` so the parent tracks
commit movement without tracking local nested worktree changes. Top-level
duplicate roots stay ignored.

The current linked-local exception is `repo_kernel/repos/CMPLX-PartsFactory`,
which is a self-referential upstream placeholder for this parent repo and had no
checked-out commit during conversion.
