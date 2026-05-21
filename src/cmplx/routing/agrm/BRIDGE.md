# agrm — Bridge

## MDHG (slot-12)

- Production addressing: `MDHGAddressingProvider` + `MDHG.channel_for`
- Witness import: `addressing/mdhg/_witness/agrmmdhg_manus.py` (Manus AGRM+MDHG monolith — **defer**, do not merge wholesale)
- Staging: `staging/by-family/agrm/mdhg_hierarchy/` — TSP agents, `MDHGHashTable`, bridge scripts

## MMDB (slot-13)

- Persist solved paths / morphon snapshots after routing receipts land
- `dr_channel` on store aligns with MDHG channel at `MMDB.store` time

## Morphon / receipt

- Register solver on `routing` port when bootstrap promotes AGRM
- Mint solve receipts on `receipt` port per ATTRACTOR_FRAME grammar

## Not AGRM

- `src/daemon/` coprime **when** scheduling (slot-33) — not geometric routing
- Root `src/memory/kimi_memory.py` — active memory, not AGRM
