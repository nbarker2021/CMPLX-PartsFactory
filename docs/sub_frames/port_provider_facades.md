# Sub-Frame: Port Provider Facades (v1)

**Status:** v1 frozen — slots open for merge proposals
**Parent frame:** [ATTRACTOR_FRAME.md](../ATTRACTOR_FRAME.md)
**Parent slots affected:** 10 (morphon), 11 (morphon-controller), 12 (mdhg), 13 (mmdb), 15 (agrm), 17 (snap), 18 (tarpit), 22 (lambda), 29 (transport-carriers)

---

## 0. Why this sub-frame exists

When Wave 0.2 went to register in-process providers for the ports that have remote-service equivalents, an underlying question surfaced: **what's the contract between a cmplx subpackage and its port?** The parent frame names the port and the subpackage, but it doesn't specify the adapter shape that turns the subpackage's public surface into a port-protocol provider.

There are three distinct shapes of gap, and treating them uniformly would force premature decisions:

1. **Provider exists, just unregistered.** The subpackage already exports a class that satisfies the Protocol. Only the call site at startup is missing.
2. **Provider needed, Protocol defined.** The Protocol in [controller.py](../../src/cmplx/morphon/controller.py) specifies the contract, but the subpackage exports a class with a different surface. An adapter (`provider.py`) is needed.
3. **Provider AND Protocol needed.** The port name exists in `KNOWN_PORTS` but no Protocol has been defined in `controller.py`. Both the contract and the adapter are missing.

Wave 0.2 of the parent frame skips ports in groups 2 and 3 and lets this sub-frame resolve them via the merge protocol. After this sub-frame's slots fill, parent Slot 11/12/13/15/17/18/22/29 close their gaps and parent Wave 1 can complete.

## 1. Merge protocol (inherits from parent)

All four gates (G1 contract, G2 admission, G3 properties, G4 determinism) apply per parent frame §2.1. For slots in this sub-frame, G2/G3/G4 use the *registered provider* (in `tests/morphon/test_smoke.py`-style fixtures with the new provider plugged in) as the reference morphons. Each accepted merge mints a `BIRTH` (first-fill) or `ASSIGN` (replacement) receipt referencing both the parent slot and this sub-frame slot.

The Protocol-extension case (group 3) requires an additional gate **G0 — Protocol design** that lands before G1 can be evaluated: the new Protocol definition is proposed, reviewed, and added to `controller.py` + `KNOWN_PORTS` (if not already present) before any provider class can be matched against it. G0 mints a `GATE` receipt of subtype `protocol_extension`.

## 2. Slot enumeration

### Slot F-1 — constraints (Aletheia)

- **Parent slot:** 03 (aletheia-law-chain), 11 (morphon-controller)
- **Group:** **1** — provider exists, just unregistered
- **Protocol:** [`ConstraintsProvider`](../../src/cmplx/morphon/controller.py) — requires `admit(morphon) -> tuple[bool, str]`
- **Subpackage surface:** [`Aletheia.admit(morphon) -> LawResult`](../../src/cmplx/constraints/aletheia/aletheia.py) where `LawResult = tuple[bool, str]` ✅
- **Adapter required?** No. `Aletheia` instance satisfies the Protocol directly.
- **Merge proposal:** at startup, `MorphonController.get().register("constraints", Aletheia())` after registering its default laws.
- **Status:** ◐ multi-candidate (Aletheia ready; no `provider.py` facade because none is needed)
- **Gate evidence required:** G1 ✅ (signature match), G2 ✅ (admission self-test), G3 ✅ (existing aletheia 12 tests stand in for properties), G4 ✅ (Aletheia is pure deterministic per existing test coverage)
- **Time estimate:** ~30 min (one-line registration + test that verifies parent's `admit_and_store` works with real Aletheia in place of `_FakeConstraints`)

### Slot F-2 — addressing (MDHG)

- **Parent slot:** 12 (mdhg)
- **Group:** **2** — provider needed, Protocol defined
- **Protocol:** [`AddressingProvider`](../../src/cmplx/morphon/controller.py) — requires `channel_for(morphon) -> int` returning digital-root 1-9
- **Subpackage surface:**
  - [`MDHG`](../../src/cmplx/addressing/mdhg/hash.py) class — has digital-root computation but signature unconfirmed against the Protocol
  - [`MDHGAddress`](../../src/cmplx/addressing/mdhg/address.py)
  - [`MDHGMultiScale`](../../src/cmplx/addressing/mdhg/multiscale.py) — for cross-scale links
- **Adapter required?** Yes. Need an `MDHGProvider` class wrapping these for the single `channel_for(morphon) -> int` method, plus potentially `quantize24(morphon) -> tuple[int, ...]` if we extend the Protocol with multi-scale addressing.
- **Open design questions:**
  - Does `channel_for` take the whole morphon or just its payload?
  - Should the Protocol be extended with `quantize24` / `slot_id` for parent slot 16 (hash-lanes) consumption?
- **Status:** ⊙ stub-only
- **Time estimate:** ~2h (design adapter, write tests, decide on Protocol extension)

### Slot F-3 — memory (MMDB)

- **Parent slot:** 13 (mmdb)
- **Group:** **2** — provider needed, Protocol defined
- **Protocol:** [`MemoryProvider`](../../src/cmplx/morphon/controller.py) — requires `store(morphon) -> None` and `fetch(morphon_id) -> Morphon | None`
- **Subpackage surface:** [`MMDB`](../../src/cmplx/memory/mmdb/store.py) — needs signature confirmation
- **Adapter required?** Yes. Need `MMDBProvider` exposing `store` / `fetch` against the live MMDB instance.
- **Open design questions:**
  - The remote `mmdb` service at port 8824 needs a parallel-shape wire contract — the proxy's `{"args": ..., "kwargs": ...}` payload must align with whatever the mmdb service expects on its `/store` and `/fetch` endpoints. The cmplx in-process MMDB and the remote mmdb service should converge on identical operation semantics.
  - Should the Protocol be extended with `store_edge`, `traverse`, `query_by_e8` for parent slot 24 (spectral-health) and slot 25 (causal-dag) consumption?
- **Status:** ⊙ stub-only
- **Time estimate:** ~3h (design adapter + parallel-wire contract negotiation with the remote mmdb service)

### Slot F-4 — symbolic (TarPit)

- **Parent slot:** 18 (tarpit)
- **Group:** **3** — Protocol AND provider both missing
- **Protocol:** *not defined* in [controller.py](../../src/cmplx/morphon/controller.py); `KNOWN_PORTS` includes `"symbolic"` but no `SymbolicProvider` Protocol exists
- **Subpackage surface:** [`TarpitEcology`](../../src/cmplx/symbolic/tarpit/) (class) + ~16 free functions (run_etp_with_ledger, check_envelope, gram_effective_dim, state_vector_for_torus, etc.). No single entry-point method.
- **G0 — Protocol design required:** What does a `symbolic` port consumer want from tarpit? Options:
  - `derive(morphon) -> SymbolicTrace` — single-call symbolic derivation
  - `ecology() -> TarpitEcology` — hand back the ecology and let caller orchestrate
  - `run_program(program: str, ...) -> LedgerResult` — wrap `run_etp_with_ledger`
- **Adapter required?** Yes — and the adapter's shape depends on the Protocol decision above.
- **Status:** ○ not-built (Protocol stage)
- **Time estimate:** ~4h (Protocol design first, then adapter)
- **Cross-cutting:** the lambda port (Slot F-7) faces the same Protocol-design problem; the two should be designed coherently so the symbolic↔lambda interaction is clean.

### Slot F-5 — transport (Chirp/Pixel/DTMF/Numbers/Video)

- **Parent slot:** 29 (transport-carriers)
- **Group:** **2** — provider needed, Protocol defined (minimally)
- **Protocol:** [`TransportProvider`](../../src/cmplx/morphon/controller.py) — requires `encode(morphon) -> bytes`. Note: no `decode` method declared in the Protocol.
- **Subpackage surface:** [`Carrier`](../../src/cmplx/transport/carrier.py) base class + [`CarrierRegistry`](../../src/cmplx/transport/carrier.py) (multi-carrier dispatcher) + [`CarrierFrame`](../../src/cmplx/transport/carrier.py). Concrete carriers: chirp, pixel, dtmf, numbers_station, video.
- **Adapter required?** Yes — need a `TransportProvider` facade that picks a carrier (default chirp?) and exposes `encode`. Protocol extension to add `decode(bytes) -> Morphon` should also be considered.
- **Open design questions:**
  - Does the Protocol need a `carrier` selector or always pick a default?
  - Decode round-trip should land in the Protocol since transport without decode is half a carrier.
- **Status:** ⊙ stub-only
- **Time estimate:** ~2h

### Slot F-6 — routing (AGRM)

- **Parent slot:** 15 (agrm)
- **Group:** **3** — Protocol AND provider both missing
- **Protocol:** *not defined*. `KNOWN_PORTS` includes `"routing"` but no `RoutingProvider` Protocol.
- **Subpackage surface:** [`AGRMController`](../../src/cmplx/routing/agrm/AGRMController.py) — stub only per parent frame
- **G0 — Protocol design required:** AGRM's three-phase TSP needs a public shape. Candidate:
  - `solve(start: Morphon, end: Morphon, orientation_weight: dict | None = None) -> list[Morphon]` returning path
- **Status:** ○ not-built (Protocol + implementation both pending)
- **Cross-cutting:** parent slot 33 (daemon-crt) publishes E8 orientation that should flow into AGRM via `orientation_weight`. Protocol must accept it.
- **Time estimate:** AGRM substantive implementation is multi-day; Protocol design + stub wrapper to make registration possible is ~3h.

### Slot F-7 — lambda

- **Parent slot:** 22 (lambda) — also pending addition to `KNOWN_PORTS`
- **Group:** **3** + **port-add**
- **Protocol:** *not defined*; `"lambda"` is not in `KNOWN_PORTS` (parent slot 22 calls this out)
- **Subpackage surface:** [`LambdaTerm`](../../src/cmplx/lambda/LambdaTerm.py) — draft only
- **G0 — Protocol design required:** What does a lambda-as-port consumer want?
  - `reduce(term: LambdaTerm) -> LambdaTerm` — beta reduction
  - `evaluate(term: LambdaTerm, env: dict) -> Any` — execution
  - `typecheck(term: LambdaTerm) -> TypeJudgment`
- **Status:** ○ not-built (Protocol + implementation both pending)
- **Cross-cutting:** Λ⊗E₈ bridge needs `geometry` port; the lambda Protocol's evaluate path needs to consume geometry providers.
- **Time estimate:** lambda is a multi-week build per parent frame; this sub-frame only handles the Protocol shape and a minimal stub provider that can be registered.

### Slot F-8 — engine (CQE) — verification only

- **Parent slot:** 20 (cqe-engine), 11 (morphon-controller)
- **Group:** **1** — provider exists, just unregistered
- **Protocol:** [`EngineProvider`](../../src/cmplx/morphon/controller.py) — requires `evolve(morphon, op, **kw) -> Morphon`
- **Subpackage surface:** [`CQEProvider`](../../src/cmplx/engine/cqe/provider.py) ✅
- **Adapter required?** No, but confirm signature alignment.
- **Status:** ◐ multi-candidate (provider exists; just needs registration call at startup)
- **Time estimate:** ~15 min

### Slot F-9 — geometry / snap / cache / conservation / diagnostic / receipt — verification only

- **Parent slots:** 04, 05, 17, 02, 21, 01
- **Group:** **1** — providers exist (their `provider.py` files are in the tree)
- **Status:** ✅ ready (these are the slots Wave 0.2 will register without controversy)
- **Time estimate:** combined ~15 min (registration calls only)

## 3. Slot dependency lattice

```
                       ┌── F-1 constraints (Aletheia, group 1)
                       │
Wave 0.2 minimal set ──┤── F-8 engine (CQE, group 1)
(today's targets)      │
                       └── F-9 verifications (geometry/snap/cache/conservation/diagnostic/receipt)

Wave 1 design+build ──┬── F-2 addressing (MDHG, group 2)
                      │
                      ├── F-3 memory (MMDB, group 2)
                      │
                      └── F-5 transport (group 2)

Wave 1 design ────────┬── F-4 symbolic (group 3, G0 first)
                      │
                      └── F-6 routing (group 3, G0 first)

Wave 2+ design ───────── F-7 lambda (group 3, port-add + G0 first)
```

## 4. What Wave 0.2 should do now

With this sub-frame defining the resolution path, Wave 0.2 in the parent frame becomes scoped to **group-1 slots only**:

**In-process providers registered at startup:**
- `receipt` ← `ReceiptProvider()` (slot F-9)
- `conservation` ← `NSLProvider()` (slot F-9)
- `constraints` ← `Aletheia()` (slot F-1)
- `cache` ← `SpeedlightProvider()` (slot F-9)
- `geometry` ← `GeometryProvider()` (slot F-9)
- `diagnostic` ← `MORSRProvider()` (slot F-9)
- `snap` ← `SnapProvider()` (slot F-9)
- `engine` ← `CQEProvider()` (slot F-8)

**Remote-only via mesh bridge** (ports with no in-process facade yet — sub-frame F-2/F-3/F-4/F-5 pending):
- `memory` ← remote `mmdb` (port 8824) *if reachable*
- `addressing` ← remote `mdhg` (port 8825) *if reachable*
- `symbolic` ← remote `tarpit` (port 8844) *if reachable*
- *(transport has no remote service to fall back on; port stays unregistered until F-5 lands)*

**Unregistered until later waves:**
- `routing` (F-6 needs G0 + AGRM build)
- `transport` (F-5 design pending)
- `crystal` (composite, may not need a single provider)

This is unambiguous, doesn't require guessing, and respects every group's actual readiness. The remaining ambiguity moves into this sub-frame's own merge process where it gets properly designed.

## 5. Open questions — resolved 2026-05-17

The four questions raised in v1 were resolved by the user. The decisions are recorded here and propagated into the slot designs above.

1. **Symbolic Protocol return shape** → **Dual reporting.** Return both a typed `SymbolicTrace` AND hand back the raw `TarpitEcology` so all categorical types, labels, and receipts associated with each are available to callers. Affects F-4: the `SymbolicProvider` Protocol returns a structured pair (or single object with both views).

2. **Extend `addressing` / `memory` Protocols now** → **Yes.** This is how most everything in the build needs to be shaped to work. Land F-2/F-3 with the full surface (multi-scale slots for addressing; edge traversal + e8-query for memory). Contract churn is the bigger risk than delivery time; do it once correctly.

3. **Transport Protocol `decode`** → **Yes, add it.** Plus: the user notes that **there is an existing IR inside the best version of the Tarpit**, and that IR is meant to work for everything. Find it. Use it as the universal substrate underlying `symbolic`, `addressing`, `memory`, and `transport` contracts — they all encode/decode through the same IR rather than each defining its own wire shape.

4. **`lambda` and `crystal` ports** → **Yes eventually, but not yet.** They wait until the full port-mapping is figured out. The reason: port triggers will be handled by **daemons and local controls** — each system needs to explicitly know and be known for *where and when* its porting occurs. That's a parent-frame design step (likely fitting under parent slot 33 daemon-crt and a new "port trigger map" slot) that this sub-frame doesn't try to resolve.

## 6. Build order (after decision resolution)

1. **Locate the Tarpit IR.** Mine [`src/cmplx/symbolic/tarpit/`](../../src/cmplx/symbolic/tarpit/) and the parts catalog (CMPLX-1T, Wolfram study) for the canonical IR pattern. Report: AST/grammar, op set, ledger shape, receipt grammar, encode/decode surface.

2. **Design the unified IR-based Protocol surface.** Once the IR is in hand, derive:
   - `SymbolicProvider` Protocol (new) — dual-report shape from #1
   - Extended `AddressingProvider` — adds multi-scale slot methods on top of `channel_for`
   - Extended `MemoryProvider` — adds edge traversal + e8-query
   - Extended `TransportProvider` — adds `decode(bytes) -> Morphon`
   All four share the IR as the wire representation: a morphon is encoded *into the IR* by its provider; consumers decode *from the IR* to get a morphon back. The IR is the lingua franca.

3. **Implement F-1 through F-5 facades** against the IR-based Protocols. F-1 (constraints) is trivial. F-2/F-3/F-5 use the IR for their encode/decode paths. F-4 (symbolic) is the IR's home — its provider is essentially the IR runtime exposed as a port.

4. **Run Wave 0.2** with all in-process registrations live. memory/addressing/symbolic no longer fall back to "remote-only when remote is healthy" — they're fully in-process *and* the bridge can proxy to remote when configured.

5. **Defer F-6 (AGRM), F-7 (lambda), and crystal port** to the parent-frame design pass that maps port triggers to daemons + local controls per decision #4.

---

## 7. ETP — the universal substrate

**Canonical name:** ETP — Encoded Tarpit Program.
**Location:** [src/cmplx/symbolic/tarpit/](../../src/cmplx/symbolic/tarpit/) (clean-tree version is canonical; CMPLX-1T prototypes preserved as reference but not authoritative).
**Reference memory:** [reference-etp-ir](../../../../../C:/Users/borke/.claude/projects/d--PartsFactory/memory/reference_etp_ir.md)

**Surface in one paragraph.** ETP is an 8-symbol IR (`}<>+[]01`) operating on a grain-tape with dynamic bonding. Grains bond into Dusts (3-body composites) which stabilize into Triads (passing closure `bond_mass ≥ 0.03`) which emit Walls (OutputWall = success digest `"X.ddd"`, ErrorWall = recovery hint with MirrorOperator suggestion). Execution is via `run_etp_with_ledger(program, dimension=8, max_steps, envelope)` and produces `{summary, ledger}` where `ledger` is one row per step with full state snapshot (ip, ptr, grain count, entropy, mean_mass, digital_root, wall10, torus8, torus8_mirror, envelope_ok, error_class). The 8D torus chart aligns natively with E8 geometry. The E6 codec (`derive_return_tokens`) projects ETP state onto 6-bit canonical tokens consumable across all four target ports.

**Why this IR satisfies all four ports:**

| Port | What ETP provides |
|---|---|
| `symbolic` | The IR *is* the symbolic substrate. Grain/Dust/Triad/Wall taxonomy + deterministic ledger + MirrorOperator recovery. |
| `addressing` | Each grain has a SHA256 hashable identity. E6 tokens encode addressable slots. Torus8 quantization gives natural DR-channel mapping (digital_root field is a row column). |
| `memory` | GrainField is an addressable 1D tape. Dust/Triad form higher-order addressable composites with extent-vector lineage. Edge traversal is the bond graph. |
| `transport` | OutputWall `"X.ddd"` is the wire-encoded success format. ErrorWall + MirrorOperator + return-token derivation handle round-trip + recovery. E6 codec is the cross-channel canonical tokenization. |

**Design implication for Protocols below.** All four port Protocols have a common `encode_to_etp(morphon) -> str` (returns ETP program) and `decode_from_etp(ledger_or_tokens) -> Morphon` surface. Each port's port-specific methods are *built on top of* this common encode/decode pair. The ETP runtime is the shared bottom layer; each port adds its specialized read/write semantics above it.

## 8. Designed Protocol surface (proposed; pending implementation)

The new and extended Protocols added to [src/cmplx/morphon/controller.py](../../src/cmplx/morphon/controller.py):

### `SymbolicProvider` (NEW)
```python
class SymbolicProvider(Protocol):
    """`symbolic` port — cmplx.symbolic.tarpit; ETP IR runtime."""

    def derive(self, morphon: Morphon) -> "SymbolicReport":
        """Run ETP on the morphon's payload. Returns dual-report carrying
        both the typed trace AND the raw TarpitEcology, per user decision."""

    def run_program(self, program: str, **kwargs) -> dict:
        """Direct ETP execution. Returns {summary, ledger}."""

    def encode_to_etp(self, morphon: Morphon) -> str:
        """Morphon → ETP program string. Wire format."""

    def decode_from_etp(self, ledger: list[dict]) -> Morphon:
        """ETP ledger → reconstructed Morphon. Round-trip from encode_to_etp."""
```

### `AddressingProvider` (EXTENDED)
```python
class AddressingProvider(Protocol):
    # existing
    def channel_for(self, morphon: Morphon) -> int: ...

    # extended for multi-scale addressing
    def quantize24(self, morphon: Morphon) -> tuple[int, ...]: ...
    def slot_id(self, q24: tuple[int, ...]) -> str: ...

    # ETP integration
    def encode_to_etp(self, morphon: Morphon) -> str: ...
    def decode_from_etp(self, ledger: list[dict]) -> Morphon: ...
```

### `MemoryProvider` (EXTENDED)
```python
class MemoryProvider(Protocol):
    # existing
    def store(self, morphon: Morphon) -> None: ...
    def fetch(self, morphon_id: str) -> Morphon | None: ...

    # extended for edge traversal
    def store_edge(self, from_id: str, to_id: str, relation: str, weight: float = 1.0) -> None: ...
    def neighbors(self, morphon_id: str, relation: str | None = None) -> list[str]: ...

    # e8-query
    def by_e8_coordinates(
        self, coords: tuple[float, ...], radius: float = 0.0
    ) -> list[Morphon]: ...

    # ETP integration
    def encode_to_etp(self, morphon: Morphon) -> str: ...
    def decode_from_etp(self, ledger: list[dict]) -> Morphon: ...
```

### `TransportProvider` (EXTENDED)
```python
class TransportProvider(Protocol):
    # existing (refined)
    def encode(self, morphon: Morphon) -> bytes: ...

    # added decode (closes the round trip)
    def decode(self, payload: bytes) -> Morphon: ...

    # ETP integration (wire format)
    def encode_to_etp(self, morphon: Morphon) -> str: ...
    def decode_from_etp(self, ledger: list[dict]) -> Morphon: ...
```

### `SymbolicReport` dataclass (NEW, dual-report shape)
```python
@dataclass
class SymbolicReport:
    """Dual-report from SymbolicProvider.derive().

    Carries the typed trace AND the raw ecology so all categorical types,
    labels, and receipts are available to callers (per user 2026-05-17).
    """
    trace: list[dict]              # the ledger view (typed step records)
    ecology: Any                   # raw TarpitEcology, mutable
    output_walls: list             # OutputWall instances
    error_walls: list              # ErrorWall instances
    receipts: list                 # cmplx.receipt.Receipt per step (when receipt port is registered)
    summary: dict                  # final summary from run_etp_with_ledger
```

---

**End of sub-frame v3. Protocols designed, awaiting implementation. Slots F-1 through F-5 unblocked for build.**
