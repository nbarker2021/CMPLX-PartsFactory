# Wave 0 Merge Proposals (v1)

**Status:** v2 — decisions resolved, approved to execute
**Frame reference:** [ATTRACTOR_FRAME.md](ATTRACTOR_FRAME.md)
**Wave 0 goal:** Two foundational gates — (A) mesh ↔ MorphonController bridge, (B) unified receipt grammar.

## Decisions resolved (2026-05-17)

| Decision | Resolution |
|---|---|
| Manny port name | **Skip** — don't register manny as a port in 0.2. Manny is the user-facing conversational LLM service; its role is structurally larger than one port and will be addressed in a later slot. It stays mesh-addressable via `mesh.request("manny", ...)`. |
| In-process vs remote precedence | **Remote-preferred when reachable; in-process fallback; single registration per port (no overwrites).** Tests in `src/cmplx/` use in-process unchanged because they never see the mesh. |
| `MintService.governance` parameter | **Drop it cleanly.** Main governance handles non-receipt governance hooks elsewhere. |
| Health-check policy at startup | **Block with 3s per-service timeout.** In-process fallback means the agent always boots successfully even if every remote service is down. Promote to async-with-retry later if production traffic demands it. |

---

## Wave 0.1 — Mesh-to-Morphon Bridge Adapter

**Target slot(s):** Slot 31 (mesh-orchestrator), Slot 11 (morphon-controller)
**Operation type:** BIRTH (new file) + adapter
**Source(s):** [src/mesh/mesh.py](../src/mesh/mesh.py), [src/cmplx/morphon/controller.py](../src/cmplx/morphon/controller.py)
**Destination file(s):** `src/mesh/morphon_bridge.py` (new), modified `src/cmplx/morphon/controller.py`

**Contract surface (G1):**
- `MorphonController.register_remote_provider(port: str, mesh: MeshOrchestrator, service_name: str) -> None`
- `_MeshServiceProxy(provider_interface, service_name, mesh)` — adapter wrapping HTTP calls in provider-protocol methods
- `_MeshServiceProxy.__getattr__(method_name) → callable that dispatches via mesh`

**Receipt grammar:**
- On merge: `BIRTH` receipt `{slot_id: "morphon_bridge", bridge_target_ports: [...], mesh_service_mapping: {...}}`
- At runtime: none directly from bridge; bridge is transparent. Remote providers mint receipts on their own schedule.

**Dependencies:**
- Prereq slots: Slot 11 ✅, Slot 31 ✅
- Prereq Wave 0 steps: none (this is the foundation)

**Blast radius:**
- Existing consumers affected: none yet (remote providers not wired in until 0.2)
- Backwards compat: full — additive only
- Test coverage: new tests for `_MeshServiceProxy` calling correct HTTP endpoints via mocked mesh

**Sketch:**
```python
# src/mesh/morphon_bridge.py (new)
from cmplx.morphon.controller import MorphonController

class _MeshServiceProxy:
    """HTTP-via-mesh adapter satisfying any port provider protocol."""
    def __init__(self, service_name: str, mesh):
        self._service = service_name
        self._mesh = mesh

    def __getattr__(self, method_name: str):
        def remote_call(*args, **kwargs):
            return self._mesh.request(
                self._service, method_name,
                {"args": args, "kwargs": kwargs}
            )
        return remote_call

# In src/cmplx/morphon/controller.py:
def register_remote_provider(self, port: str, mesh, service_name: str) -> None:
    proxy = _MeshServiceProxy(service_name, mesh)
    self.register(port, proxy)
```

**Risks & open questions:**
1. Error handling: if `mesh.request()` fails (timeout, HTTP 500), what exception does the proxy raise? Must match provider protocol expectations.
2. Type safety: `__getattr__` bypasses static checking. Optional: generate typed proxy classes at startup per port.
3. Latency: remote calls ~50–200ms vs in-process ~1ms. No caching at bridge layer yet.
4. Service-name vs port-name: bridge uses arbitrary service names; the port→service mapping lives in 0.2.

---

## Wave 0.2 — Remote Provider Registration at Startup

**Target slot(s):** Slot 32 (runtime-agent), Slot 11 (morphon-controller)
**Operation type:** ASSIGN (modify server.py startup)
**Source(s):** [src/runtime/server.py](../src/runtime/server.py), [src/runtime/persistent_agent.py](../src/runtime/persistent_agent.py)
**Destination file(s):** modified `src/runtime/server.py`, new `_register_providers()` hook in `persistent_agent.py`

**Contract surface (G1):**
- No new public methods; uses existing `MorphonController.register()` and `register_remote_provider()` (from 0.1)
- Internal hook `AgentProcess._register_providers()` follows existing pattern (`_register_core_invariants`)

**Receipt grammar:**
- On merge: `ASSIGN` receipt recording the full registration map
- At runtime: one `ASSIGN` per port registered (via MorphonController's register() contract)

**Dependencies:**
- Prereq slots: Slot 11 ✅, Slot 04 ✅, all in-process L0-L2 providers
- Prereq Wave 0 steps: **0.1 must land first**

**Blast radius:**
- Existing consumers: `AgentProcess.__init__()` and server startup get a new registration step
- Backwards compat: full — startup still works the same
- Test coverage: mock mesh with 6 services on test ports; verify `MorphonController.has(port)` is True after startup

**Sketch:**
```python
# In src/runtime/persistent_agent.py:
HEALTH_CHECK_TIMEOUT = 3.0  # seconds per service

def _register_port(self, port: str, factory, remote_service: str | None = None):
    """Single registration per port: prefer remote when reachable, else in-process."""
    if remote_service and self.services.health_check(remote_service, timeout=HEALTH_CHECK_TIMEOUT):
        self.ctrl.register_remote_provider(port, self.mesh, remote_service)
    else:
        self.ctrl.register(port, factory())

def _register_providers(self) -> None:
    from cmplx.morphon.controller import MorphonController
    from cmplx.receipt.provider import ReceiptProvider
    from cmplx.nsl.provider import NSLProvider
    from cmplx.constraints.aletheia import Aletheia
    from cmplx.speedlight.provider import SpeedlightProvider
    from cmplx.geometry.provider import GeometryProvider
    from cmplx.morsr.provider import MORSRProvider
    # plus MDHG / MMDB / Snap / TarPit providers when their port providers exist

    self.ctrl = MorphonController.get()

    # L0 / L1 / L3 providers that have no remote equivalent today
    self._register_port("receipt",      ReceiptProvider)
    self._register_port("conservation", NSLProvider)
    self._register_port("constraints",  Aletheia)
    self._register_port("geometry",     GeometryProvider)
    self._register_port("diagnostic",   MORSRProvider)

    # Ports where both an in-process provider and a remote service exist
    self._register_port("cache",      SpeedlightProvider, remote_service="speedlight")
    self._register_port("memory",     MMDBProvider,       remote_service="mmdb")
    self._register_port("addressing", MDHGProvider,       remote_service="mdhg")
    self._register_port("snap",       SnapProvider,       remote_service="snap")
    self._register_port("symbolic",   TarPitProvider,     remote_service="tarpit")

    # Manny intentionally not registered as a port (held — see decisions table)
```

**Notes on resolved decisions:**
- One registration per port, no overwrites. Health check is a 3s blocking call per service.
- In-process providers are still imported and ready as the fallback — if a remote service is down or its mesh URL is unset, the factory is invoked locally and the port is filled with the in-process instance.
- `MDHGProvider`, `MMDBProvider`, `SnapProvider`, `TarPitProvider` are the in-process port-providers for slots that currently exist as cmplx subpackages without a port facade. Adding those facades is a Wave 1 follow-up; the registration call sites in 0.2 are written against the named import so they activate the moment those provider classes land.

**Remaining risks:**
1. **Where does `self.mesh` come from?** `persistent_agent.py` doesn't currently instantiate `MeshOrchestrator`. Likely `server.py` creates it after `mesh.start()` and passes it into `AgentProcess`. Verify during implementation.
2. **Verify `self.services.health_check(name, timeout=...)` exists** — if not, add timeout kwarg as part of 0.2.

---

## Wave 0.3 — Migrate Wallet Receipts to Unified Ledger

**Target slot(s):** Slot 37 (wallet-economy), Slot 01 (receipt-chain)
**Operation type:** ASSIGN (refactor wallet/receipts.py + wallet/mint.py)
**Source(s):** [src/wallet/receipts.py](../src/wallet/receipts.py), [src/wallet/mint.py](../src/wallet/mint.py)
**Destination file(s):** modified `src/wallet/receipts.py`, modified `src/wallet/mint.py`

**Contract surface (G1):**
- Public methods unchanged: `ReceiptLedger.record()`, `MintService.mint_tokens()`, `MintService.burn_tokens()`, `MintService.reward_expert()`
- Internals now consume `MorphonController.get("receipt")` instead of `BoundaryEvent` + local SHA256

**Receipt grammar:**
- On merge: `ASSIGN` receipt recording migration from local SHA256 to unified provider
- At runtime: `PROCESS` per token op with payload `{"expert_id", "amount", "balance_before", "balance_after", "operation_kind": "MINT|BURN|EARN|SPEND|TRANSFER|STAKE|REWARD"}`

**Dependencies:**
- Prereq slots: Slot 01 ✅, Slot 11 ✅
- Prereq Wave 0 steps: **0.1 + 0.2 must land first**

**Blast radius:**
- Existing consumers: `MintService` callers (governance, expertise, runtime) — return-shape stays the same
- Backwards compat: wallet.py SQLite state table unchanged; only receipt persistence migrates
- Test coverage: existing wallet tests verify chain length matches op count; add assertion that no `BoundaryEvent` import remains

**Sketch:**
```python
# src/wallet/mint.py — remove governance import, add controller
from cmplx.morphon.controller import MorphonController

def mint_tokens(self, expert_id: str, amount: float = None,
                reason: str = "expert_creation", ...):
    # ... existing balance logic unchanged ...

    receipt_provider = MorphonController.get().get_provider("receipt")
    receipt = receipt_provider.mint_process(
        agent_id=expert_id,
        operation="mint_tokens",
        payload={
            "expert_id": expert_id,
            "amount": mint_amount,
            "reason": reason,
            "is_new_expert": is_new,
            "operation_kind": "MINT",
        }
    )

    self.mint_log.append({
        "expert_id": expert_id,
        "amount": mint_amount,
        "reason": reason,
        "receipt": receipt,
        "timestamp": time.time(),
    })
    return {
        "expert_id": expert_id,
        "amount": mint_amount,
        "reason": reason,
        "receipt": receipt,
        "is_new_expert": is_new,
    }
```

**Decision applied:** `MintService.__init__()` drops the `governance` parameter entirely. Non-receipt governance hooks live in main governance and are not the wallet's concern.

**Remaining risks:**
1. **Return-type shape:** old `mint_log[i]["receipt"]` was a dict with `receipt_hash` (str). New is a Receipt object. Callers may expect string — check `get_mint_history()` consumers and migrate them in the same pass.
2. **Fail-mode if `receipt` port unregistered:** `MorphonController.get_provider("receipt")` raises `LookupError`. Fail loud is correct (misconfigured runtime); 0.2 ensures the port is always registered at startup.
3. **Verify `mint_process` exists on current ReceiptProvider:** the agent proposal assumes typed helpers (`mint_process`, `mint_crossing`). If they don't exist yet, use generic `mint(receipt_type=ReceiptType.PROCESS, ...)`.

---

## Wave 0.4 — Migrate Governance Receipts to Unified Ledger

**Target slot(s):** Slot 30 (governance-kernel), Slot 01 (receipt-chain)
**Operation type:** ASSIGN (refactor governance/engine.py)
**Source(s):** [src/governance/engine.py](../src/governance/engine.py)
**Destination file(s):** modified `src/governance/engine.py` (BoundaryEvent.generate_receipt + GeometricGovernance.record_boundary_event)

**Contract surface (G1):**
- `BoundaryEvent.generate_receipt() -> Dict[str, Any]` — signature unchanged for backwards compat
- `BoundaryEvent` remains a domain dataclass

**Receipt grammar:**
- On merge: `ASSIGN` recording migration
- At runtime: `CROSSING` per boundary event with payload `{event_id, timestamp, entropy_delta, boundary_type, receipt_data}`

**Dependencies:**
- Prereq slots: Slot 01 ✅, Slot 11 ✅
- Prereq Wave 0 steps: **0.1 + 0.2 must land first**

**Blast radius:**
- Existing consumers: `GeometricGovernance.record_boundary_event()`, mesh.audit() callers
- Backwards compat: `generate_receipt()` still returns a dict with same keys; backing changes
- Test coverage: existing governance tests verify dict shape; add assertion that the unified ledger received a CROSSING

**Sketch:**
```python
# src/governance/engine.py
@dataclass(frozen=True)
class BoundaryEvent:
    event_id: str
    timestamp: float
    entropy_delta: float
    receipt_data: Dict[str, Any]
    boundary_type: str

    def generate_receipt(self) -> Dict[str, Any]:
        from cmplx.morphon.controller import MorphonController

        receipt_provider = MorphonController.get().get_provider("receipt")
        receipt = receipt_provider.mint_crossing(
            atom_id=self.event_id,
            boundary=self.boundary_type,
            payload={
                "event_id": self.event_id,
                "timestamp": self.timestamp,
                "entropy_delta": self.entropy_delta,
                "boundary_type": self.boundary_type,
                "receipt_data": self.receipt_data,
            }
        )
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "entropy_delta": self.entropy_delta,
            "boundary_type": self.boundary_type,
            "receipt_hash": receipt.receipt_hash,
            "receipt_data": self.receipt_data,
        }
```

**Risks & open questions:**
1. **`atom_id` mapping:** CROSSING receipts take an `atom_id`. What morphon ID for a BoundaryEvent? Recommend using event_id as synthetic atom_id (governance events are domain events, not morphons per se).
2. **Entropy accounting:** `entropy_delta` stays as a governance-domain value. Don't couple to NSL-Phi (Slot 02) yet — separate concern.
3. **Circular import risk:** `governance/engine.py` importing `cmplx.morphon.controller`. Need to verify no cycle. (Quick check: controller imports from morphon; morphon imports from receipt; receipt doesn't import governance. Should be safe.)
4. **Verify `mint_crossing` exists** (same as 0.3 risk #4).

---

## Strict ordering

```
0.1 ──┬─→ 0.3 ─┐
      │        ├─→ done
0.2 ──┴─→ 0.4 ─┘
```

1. **0.1 lands first.** Bridge file + controller method. Skips G2–G4 (first-fill); passes G1.
2. **0.2 lands second.** Startup registration. Requires 0.1.
3. **0.3 + 0.4 in parallel.** Both require 0.1 + 0.2; independent of each other.

**Gate evidence required for each:**

| Step | G1 (contract) | G2 (admission) | G3 (properties) | G4 (determinism) |
|---|---|---|---|---|
| 0.1 | new contract, intentional | skip (first-fill) | skip (first-fill) | skip (first-fill) |
| 0.2 | uses existing APIs ✅ | no admission change ✅ | registrations deterministic ✅ | startup replays identically ✅ |
| 0.3 | wallet API unchanged ✅ | no admission change ✅ | token ops deterministic ✅ | mint_log replays identically ✅ |
| 0.4 | BoundaryEvent API unchanged ✅ | no admission change ✅ | event recording deterministic ✅ | audit_trail replays identically ✅ |

**Time estimate:** ~11 hours total (0.1: 4h, 0.2: 3h, 0.3: 2h, 0.4: 2h).

---

**End of Wave 0 proposals v2. Approved 2026-05-17. Executing 0.1 first.**
