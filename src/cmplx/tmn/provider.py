from __future__ import annotations

from typing import Any, Dict, Optional

from .network import TriadicManifoldNetwork


class TMNProvider:
    """Port-facing provider for the Triadic Manifold Network.

    Thin wrapper around TriadicManifoldNetwork that adds a health()
    method for MorphonController integration.
    """

    def __init__(
        self,
        init_dims: int = 24,
        max_dims: int = 96,
        growth_increment: int = 8,
        prune_threshold: float = 0.03,
        critical_epoch: int = 300,
        *,
        decompose_fn=None,
        quantum_fn=None,
    ) -> None:
        self.network = TriadicManifoldNetwork(
            init_dims=init_dims,
            max_dims=max_dims,
            growth_increment=growth_increment,
            prune_threshold=prune_threshold,
            critical_epoch=critical_epoch,
            decompose_fn=decompose_fn,
            quantum_fn=quantum_fn,
        )

    def health(self) -> Dict[str, Any]:
        mhr = self.network.manifold.health_report()
        return {
            "dims": self.network.dims,
            "epoch": self.network.epoch,
            "frozen": self.network.frozen,
            "crystallized": self.network.crystallized,
            "generation": self.network.generation,
            "experts": len(self.network.experts),
            "avg_stability": mhr.get("avg_stability", 1.0),
            "min_stability": mhr.get("min_stability", 1.0),
            "total_repairs": mhr.get("total_repairs", 0),
            "triadic_energy": float(self.network.triads.energy()),
        }

    def state_dict(self) -> Dict[str, Any]:
        return self.network.state_dict()

    def save(self, path: str) -> str:
        return self.network.save(path)

    @classmethod
    def load(cls, path: str) -> TMNProvider:
        inst = cls.__new__(cls)
        inst.network = TriadicManifoldNetwork.load(path)
        return inst
