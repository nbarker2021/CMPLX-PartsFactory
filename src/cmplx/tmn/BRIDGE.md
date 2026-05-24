# tmn — Bridge

## Dependencies consumed

| Port | Purpose | Required |
|------|---------|----------|
| `numpy` | Linear algebra, SVD, array ops | Yes |
| `decompose` | Custom spectrum decomposition for crystallize | No (fallback provided) |

## Dependencies provided

| Port | Symbol |
|------|--------|
| `tmn` | `TMNProvider` |

## Cross-component semantics

- **cognition.brain** — brain holds 96-D manifold (4× 24-D TMN lattices)
- **geometry.e8 / leech** — weight structure maps to E8/Leech geometry
- **engine.manifold** — `ManifoldPipeline` may wrap TMN outputs
- **economy** — agent actions have economic dimension via TMN1/TMN2 services
- **arena** — competitive evaluation may train TMN instances

## Static imports

`numpy` only. No external services required for core library.
