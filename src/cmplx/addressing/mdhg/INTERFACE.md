# mdhg — Interface

**MDHG** (Multi-Dimensional Hash Graph) is the system's addressing
layer. Every morphon gets a digital-root channel between 1 and 9 by
hashing its payload and reducing.

The system has exactly nine channels — that's not a tuning parameter,
it's the cardinality of the multiplicative residue group modulo 9 (the
finite group that makes recursive digit-sum collapse to a single
digit). Channels are not buckets; they're addresses with semantic
meaning (see "Channel triads" below).

## What this package exposes

| Symbol | Purpose |
|---|---|
| `MDHG` | The provider class. Instantiate once at boot. |
| `MDHG.channel_for(morphon)` | The primary operation. Returns int 1-9. |
| `MDHG.hierarchical_address(morphon)` | Returns a `(hash_hex, channel, register, triad)` tuple — full address. |
| `digital_root(value)` | Lower-level helper for any digit-sum-to-one collapse. |
| `Channel`, `Register`, `Triad` | Enums for the semantic shape of an address. |

## Algorithm (precise)

1. Serialize the morphon's payload (`json.dumps(payload, sort_keys=True)`).
2. Compute `sha256` → 64 hex chars.
3. Sum the digits of the hex (each char interpreted as 0-15).
4. Recursive digit-sum to a single digit 1-9 (0 maps to 9).
5. That digit is the channel.

This is deterministic, content-addressed, and stable across runs.

## Channel triads

The 9 channels are organized into 3 triads of 3:

| Channels | Register | Meaning |
|---|---|---|
| 1-2-3 | **Initiation / Forge / Apex** | Formative, ground-laying operations |
| 4-5-6 | **Movement / Action / Manifestation** | The working register |
| 7-8-9 | **Archive / Forge / Reset** | Closing, recording, regenerating |

A morphon's channel tells the rest of the system *where in the manifold*
it lives and *which register* it belongs to.

## Hierarchical addressing

A full MDHG address is more than just the channel. The
`hierarchical_address()` method returns the four-tuple:

```python
(sha256_hex, channel, register_name, triad_name)
```

- `sha256_hex` — full content hash (collision-resistant identity).
- `channel` — int 1-9.
- `register_name` — one of "Initiation", "Forge", "Apex", "Movement",
  "Action", "Manifestation", "Archive", "Forge_close", "Reset".
- `triad_name` — one of "low", "mid", "high".

## Invariants

1. **Deterministic**: same payload → same channel, every time.
2. **Pure**: no side effects on the morphon.
3. **No required dependencies**: stdlib only (`hashlib`, `json`).
4. **Caching is the caller's job**: the morphon caches its channel
   on first computation via `morphon.dr_channel`.

## What this package does NOT do

- It doesn't store anything (that's `cmplx.memory.mmdb`).
- It doesn't admit morphons (that's `cmplx.constraints.aletheia`).
- It doesn't compute E8 / Leech projections (that's `cmplx.geometry`).
- It doesn't carry any state across calls — `MDHG` is a stateless
  provider you instantiate once.

## How morphon talks to this

Through the `addressing` port of the bridge contract:

```python
from cmplx.morphon import MorphonController
from cmplx.addressing.mdhg import MDHG

MorphonController.get().register("addressing", MDHG())

# Now:
m = Morphon.forge(payload={"hello": "world"})
m.project_to_channel()  # returns 1-9
```
