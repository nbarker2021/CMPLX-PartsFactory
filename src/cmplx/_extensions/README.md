# Extension attractors (`_extensions/`)

This tree **grows without bound** as assembly work discovers new named organs.

## Layout

```
_extensions/
  L00/   # substrate-class extensions
  L01/   # geometry
  ...
  L10/   # applications / speculative
  <slug>/   # one directory per extension attractor
    INTERFACE.md
    ... merged modules ...
```

## Registration

1. `python identity_review/scripts/attractor_registry.py register ...`
2. Or append to `work/attractor-assembly/registry/extensions.jsonl`
3. Re-run `attractor_wave_pull.py` for that layer

Promoted inbound dedupe attractors land here via `attractor_registry.py promote`.

Frame slots in `docs/ATTRACTOR_FRAME.md` remain authoritative when assigned; `_extensions/` holds everything not yet slotted.
