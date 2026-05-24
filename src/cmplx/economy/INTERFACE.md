# economy — Interface

**Agent marketplace, compute purchasing, and resource economy.**

Every agent action in TMN1 has an economic dimension. The economy module
tracks balances, commissions, marketplace listings, and resource pricing.

## Surface

### Types

- `BalanceSheet(debt, interest, credit_limit, in_default)` — per-agent ledger
- `EconomyState(resources, prices, market_temp, supply_chain)` — global state
- `Commission(commission_id, requester, task, reward, status, ...)` — bounty
- `Listing(listing_id, seller_id, item_type, price, ...)` — marketplace item
- `CommissionStatus` — `OPEN | CLAIMED | IN_PROGRESS | COMPLETED | DISPUTED`
- `ItemType` — `BRAIN | LABEL_SET | TRAINING_DATA`

### Provider

- `EconomyProvider(state)` — canonical provider
  - `balance(agent_id)` → `BalanceSheet`
  - `mint(agent_id, amount)` → `BalanceSheet`
  - `burn(agent_id, amount)` → `BalanceSheet | None`
  - `transfer(from_id, to_id, amount)` → `(success, reason)`
  - `create_commission(requester, task, reward, ...)` → `Commission`
  - `list_commissions(status)` → `List[Commission]`
  - `claim_commission(commission_id, claimant)` → `(success, reason)`
  - `list_item(listing)` → `listing_id`
  - `get_listing(listing_id)` → `Listing | None`
  - `tick()` — advance economy state
  - `prices()` → `Dict[str, float]`
  - `health()` → status dict

### Pure operations (no provider needed)

- `mint(state, balances, agent_id, amount)`
- `burn(balances, agent_id, amount)`
- `transfer(balances, from_id, to_id, amount)`
- `create_commission(commissions, ...)`
- `update_prices(state)`
- `tick(state, balances)`

## What's NOT in this layer (yet)

- PostgreSQL persistence — prototype used raw `psycopg2`; canonical form
  uses in-memory state until `memory` port integration is wired.
- FastAPI service skin — lives in `_adapters/http_service.py`, pending.
- Receipt minting for every transaction — pending `receipt` port wiring.
- Lending interest compounding beyond simple tick application.
- Buyback and staking pool yield calculations (in prototype, not canonical).
