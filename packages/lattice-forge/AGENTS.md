# AGENTS.md

This repository is intended for AI-assisted development.

## Agent operating rules

1. Do not treat first-pass interpretations as truth.
2. Preserve candidate fields and failure states.
3. Run `scripts/smoke.py` after changing core CLI/store/server/control code.
4. Do not silently overwrite schema meaning; add migration-compatible tables or columns.
5. Failures should become memory, not be hidden.
6. If a memory object supersedes, contradicts, or compresses prior memory, it must account for the prior object.
7. Prefer dependency-free blocks until a feature clearly requires an external package.

## Current smoke command

```bash
$env:PYTHONPATH = "src"
python -S scripts/smoke.py
```
