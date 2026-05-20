"""
SpectralHealth — graph-Laplacian diagnostic over the memory graph.

Reads the morphon edge graph from any object exposing a ``neighbors(id)``
or ``edges_of(id)`` method (the canonical case is an MMDBMemoryProvider),
computes the graph Laplacian, and reports a small set of structural-health
metrics: spectral gap (Fiedler value), connected components, degree extrema.

Lives under cmplx.morsr because the MORSR provider owns the `diagnostic`
port; SpectralHealth is a co-component that the diagnostic-port consumer
or downstream callers can invoke. It does NOT currently register as its
own port — that decision waits on the port-trigger-map sub-frame (per
parent frame Slot 24's deferral).

Parent frame Slot 24. Design references:
  - Aletheia Full Stack Ref §6.3 spectral_health_controller.py
  - Aletheia Creative Permutations §16 (Spectral Gap as Universal Loss)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional


@dataclass
class SpectralReport:
    """Result of one SpectralHealth.report() invocation.

    Fields:
        node_count: total nodes in the graph
        edge_count: total undirected edges
        spectral_gap: lambda_2 - lambda_1 (Fiedler value); 0.0 if disconnected
        connected_components: count of zero eigenvalues (numerical tolerance)
        max_degree: highest node degree in the graph
        min_degree: lowest node degree
        mean_degree: average node degree
        eigenvalues_sample: first 8 Laplacian eigenvalues (sorted ascending)
        healthy: heuristic flag — True iff the graph is connected AND has
            a meaningful spectral gap (≥ 0.01)
    """
    node_count: int = 0
    edge_count: int = 0
    spectral_gap: float = 0.0
    connected_components: int = 0
    max_degree: int = 0
    min_degree: int = 0
    mean_degree: float = 0.0
    eigenvalues_sample: list[float] = field(default_factory=list)
    healthy: bool = False


class SpectralHealth:
    """Computes spectral-health metrics over a morphon edge graph.

    Two construction modes:

      1. **Provider-backed**: pass a MemoryProvider-like object whose
         ``neighbors(id)`` method returns adjacency. Combined with a
         seed set of node IDs, the class walks the graph and computes
         metrics over the reachable subgraph.

      2. **Explicit edges**: pass an iterable of ``(from_id, to_id)``
         tuples directly. Useful for tests and offline analysis.

    Reports the graph Laplacian's spectral structure: gap (Fiedler value),
    connected components, degree extrema. Edges are treated as undirected
    for the Laplacian computation; bidirectional edges count once.
    """

    def __init__(
        self,
        *,
        memory_provider: Any = None,
        seed_ids: Optional[Iterable[str]] = None,
        edges: Optional[Iterable[tuple[str, str]]] = None,
        connectivity_tol: float = 1e-9,
        healthy_gap_threshold: float = 0.01,
    ) -> None:
        """
        Args:
            memory_provider: object with ``neighbors(id) -> list[str]``.
                Required if ``edges`` is None.
            seed_ids: iterable of starting node IDs for graph walk. Required
                with ``memory_provider``.
            edges: explicit (from_id, to_id) edges. Bypasses provider walk.
            connectivity_tol: eigenvalues below this are considered zero
                for connected-component counting.
            healthy_gap_threshold: minimum spectral gap for ``healthy=True``
                in the report (default 0.01).
        """
        if edges is None and (memory_provider is None or seed_ids is None):
            raise ValueError(
                "SpectralHealth requires either `edges=` or both "
                "`memory_provider=` and `seed_ids=`"
            )
        self._memory_provider = memory_provider
        self._seed_ids = list(seed_ids) if seed_ids is not None else []
        self._explicit_edges = list(edges) if edges is not None else None
        self._connectivity_tol = connectivity_tol
        self._healthy_gap_threshold = healthy_gap_threshold

    # ── Public API ────────────────────────────────────────────────

    def report(self) -> SpectralReport:
        """Compute and return the SpectralReport over the current graph."""
        nodes, adj = self._collect_graph()
        if not nodes:
            return SpectralReport()  # empty graph → zero-filled report

        index_of = {nid: i for i, nid in enumerate(nodes)}
        n = len(nodes)

        # Build undirected adjacency matrix.
        try:
            import numpy as np
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("SpectralHealth requires numpy") from e

        A = np.zeros((n, n), dtype=float)
        edge_count = 0
        for a, bs in adj.items():
            ia = index_of[a]
            for b in bs:
                if b not in index_of:
                    continue
                ib = index_of[b]
                if A[ia, ib] == 0.0:
                    A[ia, ib] = 1.0
                    A[ib, ia] = 1.0
                    edge_count += 1

        # Degree + Laplacian.
        degree = A.sum(axis=1)
        D = np.diag(degree)
        L = D - A

        # Eigenvalues. eigh returns sorted ascending and is faster for
        # symmetric matrices.
        eigvals = np.linalg.eigvalsh(L)
        eigvals = sorted(float(v) for v in eigvals)

        # Connected components = count of eigenvalues at zero (within tol).
        components = sum(1 for v in eigvals if v < self._connectivity_tol)
        # Spectral gap (algebraic connectivity / Fiedler value):
        #   - For a CONNECTED graph (components == 1), gap = lambda_2.
        #   - For a DISCONNECTED graph, gap is 0 (the graph has no
        #     expansion as a whole — its second-smallest eigenvalue is
        #     also 0). This matches the standard "graph is healthy iff
        #     gap > 0" interpretation.
        if components == 1 and len(eigvals) >= 2:
            spectral_gap = eigvals[1]
        else:
            spectral_gap = 0.0

        max_deg = int(degree.max()) if len(degree) else 0
        min_deg = int(degree.min()) if len(degree) else 0
        mean_deg = float(degree.mean()) if len(degree) else 0.0

        healthy = (
            components == 1
            and spectral_gap >= self._healthy_gap_threshold
        )

        return SpectralReport(
            node_count=n,
            edge_count=edge_count,
            spectral_gap=spectral_gap,
            connected_components=components,
            max_degree=max_deg,
            min_degree=min_deg,
            mean_degree=mean_deg,
            eigenvalues_sample=eigvals[:8],
            healthy=healthy,
        )

    # ── Internals ─────────────────────────────────────────────────

    def _collect_graph(self) -> tuple[list[str], dict[str, list[str]]]:
        """Return (sorted_node_ids, adjacency_dict).

        Either uses the explicit edge list directly, or walks the provider
        starting from seed IDs (BFS), capping the walk size to a sane limit.
        """
        if self._explicit_edges is not None:
            return self._from_explicit_edges()
        return self._walk_provider()

    def _from_explicit_edges(self) -> tuple[list[str], dict[str, list[str]]]:
        nodes: set[str] = set()
        adj: dict[str, list[str]] = {}
        for a, b in self._explicit_edges or []:
            nodes.add(a)
            nodes.add(b)
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
        return sorted(nodes), adj

    def _walk_provider(
        self, max_nodes: int = 1000
    ) -> tuple[list[str], dict[str, list[str]]]:
        nodes: set[str] = set()
        adj: dict[str, list[str]] = {}
        frontier: list[str] = list(self._seed_ids)

        while frontier and len(nodes) < max_nodes:
            current = frontier.pop(0)
            if current in nodes:
                continue
            nodes.add(current)
            try:
                neighbors = self._memory_provider.neighbors(current)
            except Exception:
                neighbors = []
            for nbr in neighbors:
                adj.setdefault(current, []).append(nbr)
                if nbr not in nodes and len(nodes) + len(frontier) < max_nodes:
                    frontier.append(nbr)

        return sorted(nodes), adj
