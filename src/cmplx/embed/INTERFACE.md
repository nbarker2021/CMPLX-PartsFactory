# cmplx.embed — 4-Embed Model

## Contract

The `embed` port decomposes a morphon's payload into four explicit typed channels — Constraint, State, Evidence, Operator — so downstream consumers (Aletheia laws, MORSR diagnostics, ThinkTank deliberation) can read fact / assumption / current-value / available-action separately rather than scraping a generic payload.

This is the 4-Embed Model from the Aletheia_CQE_Operational_Package formalization document. The four channels are independent and complementary:

| Channel | Semantic role |
|---|---|
| **constraint** | Laws, policies, invariants this morphon must satisfy. Read-only contract surface. |
| **state** | The current value/payload. The mutable "what is." |
| **evidence** | Facts/data backing the state. Provenance + witness. |
| **operator** | How to transform this morphon. Available actions. |

## Provider surface

`FourEmbedProvider` implements `cmplx.morphon.EmbedProvider`:

```python
class FourEmbedProvider:
    def decompose(self, morphon: Morphon) -> FourEmbedView: ...
    def encode_to_etp(self, morphon: Morphon) -> str: ...
    def decode_from_etp(self, ledger: list[dict]) -> Morphon: ...
```

`decompose(morphon)` returns a `FourEmbedView` (defined in `cmplx.morphon.controller`):

- If `morphon.payload` has the explicit shape `{"constraint": ..., "state": ..., "evidence": ..., "operator": ...}`, those keys map directly to the corresponding channels.
- Otherwise the entire payload is treated as the **state** channel; constraint / evidence / operator default to empty (`None`).
- `evidence` is augmented (when not explicitly provided) with a summary of the morphon's receipt chain, so consumers can read provenance without traversing receipts manually.

## ETP delegation

`encode_to_etp` / `decode_from_etp` delegate to the registered `symbolic` port when present (canonical ETP source) and fall back to the local encoding otherwise — byte-identical with the other facade fallbacks (F-2 / F-3 / F-5). The 4-Embed view doesn't fundamentally change the wire format; it changes the *typed lens* applied to the same morphon payload.

## Consumer pattern

Embed-aware code reads the channel it cares about and ignores the rest:

```python
ctrl = MorphonController.get()
view = ctrl.get_provider("embed").decompose(morphon)
# Aletheia: check constraint channel
constraints = ctrl.get_provider("constraints")
admitted, reason = constraints.admit(morphon)  # uses full morphon
# MORSR: read state + evidence; ignore operator
state = view.state
provenance = view.evidence
```

## Status

- ✅ canonical (Slot 19 — first build)
- Aletheia integration via embed-aware laws is a Wave-1 follow-up (existing laws keep working unchanged; new laws can opt into the 4-channel view).
- Crystal-fabric / port-trigger map integration deferred — embed is a *view*, not a *trigger*. Triggers belong to the port-trigger sub-frame.
