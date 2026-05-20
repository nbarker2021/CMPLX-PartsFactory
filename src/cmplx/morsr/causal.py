"""
CausalDAG — receipt-chain-derived causal diagnostic.

Per Aletheia Creative Permutations §7 ("Receipt Chain as Causal DAG"),
the receipt chain from any pipeline run IS a causal DAG. Each receipt
becomes a node; the prev_receipt_hash link becomes an edge; the artifact
hash + receipt type becomes node features.

Surface:
  - ``nodes()``: receipt-shaped node summaries
  - ``ancestors(hash, depth)`` / ``descendants(hash, depth)``: walks
  - ``attribution(outcome_hash, depth)``: scored upstream contributions
  - ``predict_delta(scenario)``: counterfactual stub (returns structured
    "deferred — needs domain model" result)

Lives next to SpectralHealth under cmplx.morsr because the diagnostic
port is MORSRProvider's home. Doesn't register its own port (port-trigger
map decides whether to elevate it; for now it's a class consumers
instantiate against the receipt port).

Parent frame Slot 25. Design references:
  - Aletheia Creative Permutations §3 (Causal Reverser)
  - Aletheia Creative Permutations §7 (Receipt Chain as Causal DAG)
  - Aletheia Creative Permutations §11 (Causal Attribution + Geometry)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional


@dataclass
class CausalNode:
    """A single node in the causal DAG, derived from a receipt.

    Fields:
        receipt_hash: the hash that uniquely identifies this node
        receipt_id: the receipt's own id (when distinct)
        receipt_type: PROCESS/CROSSING/BOND/etc. — the type acts as a
            categorical feature for attribution scoring
        operation: the receipt's operation string
        atom_id: the atom the receipt was about
        agent_id: the agent that minted the receipt
        parent_hash: the prev_receipt_hash; "" for the chain root
        timestamp: ISO-format string if available
        payload_keys: the keys present in the receipt's payload (used
            as lightweight features without copying full payloads)
    """
    receipt_hash: str = ""
    receipt_id: str = ""
    receipt_type: str = ""
    operation: str = ""
    atom_id: str = ""
    agent_id: str = ""
    parent_hash: str = ""
    timestamp: str = ""
    payload_keys: tuple[str, ...] = ()


@dataclass
class AttributionScore:
    """One upstream receipt's scored contribution to an outcome.

    score in [0.0, 1.0]; higher = more influence.
    """
    node: CausalNode
    score: float = 0.0
    distance: int = 0
    reason: str = ""


@dataclass
class CausalReport:
    """Result of a CausalDAG.attribution() invocation."""
    outcome_hash: str = ""
    upstream_count: int = 0
    attributions: list[AttributionScore] = field(default_factory=list)
    # Highest-scoring attribution for quick access.
    top_attribution: Optional[AttributionScore] = None


# Receipt type → attribution weight. Heuristic: GATE/DEATH receipts have
# high causal weight (they're decision points); CROSSING and BOND have
# medium weight (state transitions); PROCESS is low (everyday work).
# Domain-specific weights can override via constructor.
_DEFAULT_TYPE_WEIGHTS: dict[str, float] = {
    "gate": 1.0,
    "death": 1.0,
    "vote": 0.9,
    "assign": 0.8,
    "bond": 0.7,
    "crossing": 0.7,
    "birth": 0.6,
    "mint": 0.5,
    "process": 0.4,
    "post": 0.3,
}


class CausalDAG:
    """Receipt-chain-derived causal DAG.

    Instantiate with a receipt provider (anything exposing the
    ``cmplx.receipt.ReceiptProvider`` query surface — at minimum
    ``recent()`` and ``walk_chain()``). The DAG is computed lazily on
    first access and cached; call ``refresh()`` to rebuild after the
    receipt chain has grown.

    Edges follow prev_receipt_hash: a node's parent is the receipt whose
    hash equals this node's parent_hash. Multiple children per parent
    are allowed (a receipt can be branched from).
    """

    def __init__(
        self,
        receipt_provider: Any,
        *,
        type_weights: Optional[dict[str, float]] = None,
        depth_decay: float = 0.7,
    ) -> None:
        """
        Args:
            receipt_provider: ReceiptProvider-like object with
                ``recent(limit)`` returning Receipt objects.
            type_weights: optional override map ``{receipt_type: weight}``
                for attribution scoring. Defaults to a sensible heuristic.
            depth_decay: multiplier per chain-distance step when scoring
                upstream attributions. 0.7 means an ancestor 3 steps
                away gets 0.7^3 ≈ 0.343 of its base weight.
        """
        self._provider = receipt_provider
        self._type_weights = dict(_DEFAULT_TYPE_WEIGHTS)
        if type_weights:
            self._type_weights.update({k.lower(): v for k, v in type_weights.items()})
        self._depth_decay = depth_decay

        self._nodes: dict[str, CausalNode] = {}
        self._children: dict[str, list[str]] = {}
        self._built = False

    # ── Public API ────────────────────────────────────────────────

    def refresh(self) -> None:
        """Rebuild the DAG from the current receipt chain."""
        self._nodes.clear()
        self._children.clear()
        self._build()
        self._built = True

    def nodes(self) -> list[CausalNode]:
        """Return all causal nodes (chain order is implementation-dependent)."""
        self._ensure_built()
        return list(self._nodes.values())

    def node(self, receipt_hash: str) -> Optional[CausalNode]:
        """Return one node by its receipt_hash, or None."""
        self._ensure_built()
        return self._nodes.get(receipt_hash)

    def ancestors(self, receipt_hash: str, depth: int = 10) -> list[CausalNode]:
        """Walk up the parent chain from receipt_hash, up to `depth` steps.

        The returned list is ordered nearest-first; the receipt at
        ``receipt_hash`` itself is NOT included.
        """
        self._ensure_built()
        out: list[CausalNode] = []
        current = receipt_hash
        for _ in range(depth):
            node = self._nodes.get(current)
            if node is None or not node.parent_hash:
                break
            parent = self._nodes.get(node.parent_hash)
            if parent is None:
                break
            out.append(parent)
            current = parent.receipt_hash
        return out

    def descendants(self, receipt_hash: str, depth: int = 10) -> list[CausalNode]:
        """BFS down children of `receipt_hash`, up to `depth` levels.

        Order: BFS frontier-first within depth limit.
        """
        self._ensure_built()
        if receipt_hash not in self._nodes:
            return []
        out: list[CausalNode] = []
        frontier: list[tuple[str, int]] = [(receipt_hash, 0)]
        seen: set[str] = {receipt_hash}
        while frontier:
            current, d = frontier.pop(0)
            if d >= depth:
                continue
            for child_hash in self._children.get(current, []):
                if child_hash in seen:
                    continue
                seen.add(child_hash)
                child = self._nodes.get(child_hash)
                if child is None:
                    continue
                out.append(child)
                frontier.append((child_hash, d + 1))
        return out

    def attribution(
        self,
        outcome_hash: str,
        depth: int = 10,
    ) -> CausalReport:
        """Score upstream contributions to an outcome receipt.

        Scoring: each ancestor's base weight (from receipt-type weights)
        is multiplied by ``depth_decay**distance``. Results sorted high→low.
        """
        self._ensure_built()
        ancestors = self.ancestors(outcome_hash, depth=depth)
        attributions: list[AttributionScore] = []
        for i, anc in enumerate(ancestors, start=1):
            base = self._type_weights.get(anc.receipt_type.lower(), 0.2)
            decayed = base * (self._depth_decay ** (i - 1))
            attributions.append(AttributionScore(
                node=anc,
                score=decayed,
                distance=i,
                reason=f"type={anc.receipt_type} weight={base:.2f} decay={self._depth_decay**(i-1):.3f}",
            ))
        attributions.sort(key=lambda a: a.score, reverse=True)
        return CausalReport(
            outcome_hash=outcome_hash,
            upstream_count=len(attributions),
            attributions=attributions,
            top_attribution=attributions[0] if attributions else None,
        )

    def predict_delta(self, scenario: dict) -> dict:
        """Counterfactual delta prediction stub.

        True counterfactual analysis requires a domain-specific transition
        model. This method returns a structured placeholder so callers can
        wire the API today and plug a domain model later. The ``scenario``
        argument is reflected back in the result for traceability.
        """
        return {
            "status": "deferred",
            "reason": "predict_delta requires a domain-specific transition model "
                      "(receipt grammar alone underdetermines counterfactuals)",
            "scenario": scenario,
            "next_step": "supply a model via causal_dag.set_transition_model(...)",
        }

    # ── Internals ─────────────────────────────────────────────────

    def _ensure_built(self) -> None:
        if not self._built:
            self.refresh()

    def _build(self) -> None:
        """Pull receipts from the provider and index them as DAG nodes."""
        receipts = self._fetch_receipts()
        for r in receipts:
            node = self._receipt_to_node(r)
            if not node.receipt_hash:
                continue
            self._nodes[node.receipt_hash] = node

        # Build child index in a second pass so all nodes exist first.
        for node in self._nodes.values():
            if node.parent_hash and node.parent_hash in self._nodes:
                self._children.setdefault(node.parent_hash, []).append(node.receipt_hash)

    def _fetch_receipts(self) -> Iterable[Any]:
        """Pull receipts from the provider.

        Prefers ``recent()`` (returns a list) but falls back to manually
        walking the chain via ``walk_chain`` if recent isn't available.
        """
        if hasattr(self._provider, "recent"):
            try:
                return list(self._provider.recent(limit=10000))
            except Exception:
                pass
        if hasattr(self._provider, "walk_chain"):
            try:
                return list(self._provider.walk_chain())
            except Exception:
                pass
        return []

    def _receipt_to_node(self, r: Any) -> CausalNode:
        """Adapt one receipt (dict or object) into a CausalNode."""
        def pick(name: str, default: str = "") -> str:
            if isinstance(r, dict):
                v = r.get(name, default)
            else:
                v = getattr(r, name, default)
            return v if isinstance(v, str) else (str(v) if v is not None else default)

        payload = None
        if isinstance(r, dict):
            payload = r.get("payload")
        else:
            payload = getattr(r, "payload", None)
        payload_keys = tuple(sorted(payload.keys())) if isinstance(payload, dict) else ()

        return CausalNode(
            receipt_hash=pick("receipt_hash"),
            receipt_id=pick("receipt_id"),
            receipt_type=pick("receipt_type"),
            operation=pick("operation"),
            atom_id=pick("atom_id"),
            agent_id=pick("agent_id"),
            parent_hash=pick("parent_hash") or pick("prev_hash"),
            timestamp=pick("created_at") or pick("timestamp"),
            payload_keys=payload_keys,
        )
