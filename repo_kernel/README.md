# Repo Kernel

Clean GitHub clones live under `repo_kernel/repos/` and are treated as mounted
modules by the Repo Kernel FastAPI/MCP service.

The source manifest is `repo_kernel/manifest/repos.json`. Keep repo identity in
that manifest rather than nesting these repos inside the active PartsFactory git
history.

Use:

```powershell
python scripts\repo_kernel_sync.py --manifest-only
python scripts\repo_kernel_sync.py --clone
```

The first command refreshes metadata from GitHub. The second clones or fetches
the modules and records pinned commits.
