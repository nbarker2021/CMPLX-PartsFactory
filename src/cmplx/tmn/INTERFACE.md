# tmn — Interface

**Triadic Manifold Network (TMN)** is the self-improving neural substrate.
It uses a block-structured weight manifold with 10 micro-controller channels
(8 data + 2 parity) and triadic constraints (Noether / Shannon / Landauer).

## Port

- **`tmn`** on `MorphonController` (not yet registered in `register_all()`)

## Public surface

```python
from cmplx.tmn import TMNProvider, TriadicManifoldNetwork

# Provider (port-facing)
provider = TMNProvider()
provider.health()

# Direct network access
net = TriadicManifoldNetwork(init_dims=24, max_dims=96)
out = net.forward(np.random.randn(24))
mem = net.recall(np.random.randn(24))
metrics = net.learn("input", "output")
net.grow()
net.save("tmn_state.json")
child = net.spawn_next_generation()
```

## Core classes

- `TriadicManifoldNetwork` — main network: forward, recall, learn, grow, crystallize, spawn
- `Manifold` — block-structured weights with 10 micro-controller channels
- `MicroController` — self-healing channel controller (observe, heal, tune_lr)
- `ChannelState` — per-channel health and tuning state
- `ExpertModule` — post-critical-period specialist snapshot
- `TriadicState` — Noether, Shannon, Landauer constraint matrices

## Optional decomposition injection

`TriadicManifoldNetwork` accepts optional `decompose_fn` and `quantum_fn`
callables for `crystallize()`. If absent, a simple SVD fallback is used.

## HTTP adapter

FastAPI service on port **8848** (planned; `_adapters/http_service.py` stub).
