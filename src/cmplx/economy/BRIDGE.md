# economy — Bridge

## Port provided

`economy` — `EconomyProvider` is the canonical provider. **Not yet registered
in `MorphonController.KNOWN_PORTS`.** Pending substrate decision on whether
economy is an application layer (direct import) or a port-provider layer.

## Ports consumed

| Port | What economy does with it |
|---|---|
| `memory` (planned) | Persist agent balances, commissions, listings across process restarts |
| `receipt` (planned) | Mint a Receipt for every transfer, commission, and marketplace transaction |
| `cache` (planned) | Memoize price oracle lookups and commission list queries |

## Static imports

| Imports from | What | Why |
|---|---|---|
| `cmplx.receipt` | `ReceiptProvider`, `ReceiptType` | Transaction provenance (planned) |
| `cmplx.memory.mmdb` | `MMDBMemoryProvider` | Balance/commission persistence (planned) |

## What other components import FROM economy

| Importer (planned) | What |
|---|---|
| `cmplx.worlds.forge` | Query `prices()` for resource costs when minting worlds |
| `cmplx.tools.manus` | Pay per-call pricing for instrument execution |
| `cmplx.engine.cqe` | Commission rewards for solved problems |

## Cross-component semantics

Economy is an **application-layer** module. Unlike substrate providers
(memory, cache, engine), it does not sit on the critical path of morphon
admission and storage. It sits above them:

```
agent action
   │
   ├── cmplx.economy.balance(agent_id) ───────────── (economy-native)
   │
   ├── cmplx.economy.transfer(from, to, amount) ──── (economy-native)
   │       ↓ mints Receipt via cmplx.receipt (planned)
   │
   ├── cmplx.economy.create_commission(...) ──────── (economy-native)
   │       ↓ stored via cmplx.memory (planned)
   │
   └── cmplx.economy.tick() ──────────────────────── (economy-native)
           ↓ updates prices, applies interest
```

The Coexistence Pattern: economy balances and commissions are NOT
morphons. They are economic primitives. When a commission is resolved,
the resulting morphon (if any) is stored via the `memory` port, and the
economic transaction is recorded via the `receipt` port.
