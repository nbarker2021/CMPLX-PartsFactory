"""
Provider facade for the cognition brain product.

The brain is not registered as a MorphonController port yet. It is a library
surface that can consume existing ports when they are present: geometry for
projection, memory for storing brain snapshots, and receipt for provenance.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from cmplx.morphon import Morphon, MorphonController

from ._constants import TOP_K
from .core import Brain, BrainState, make_default_brain, vector_from_payload


class BrainImageStore:
    """Local JSON brain-image store used before service persistence exists."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def path_for(self, agent_id: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in agent_id)
        return self.root / f"{safe}.brain.json"

    def save(self, brain: Brain) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.path_for(brain.agent_id)
        path.write_text(
            json.dumps(brain.to_image(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def load(self, agent_id: str) -> Brain:
        data = json.loads(self.path_for(agent_id).read_text(encoding="utf-8"))
        return Brain.from_image(data)


class BrainProvider:
    """Small registry and bridge facade for composed-E8 brains."""

    name = "brain_provider"

    def __init__(
        self,
        brains: Mapping[str, Brain] | None = None,
        *,
        image_store: BrainImageStore | str | Path | None = None,
    ) -> None:
        self._brains: dict[str, Brain] = dict(brains or {})
        if image_store is None or isinstance(image_store, BrainImageStore):
            self.image_store = image_store
        else:
            self.image_store = BrainImageStore(image_store)

    def register_brain(self, brain: Brain, *, overwrite: bool = False) -> Brain:
        if brain.agent_id in self._brains and not overwrite:
            raise RuntimeError(f"brain {brain.agent_id!r} is already registered")
        self._brains[brain.agent_id] = brain
        return brain

    def get_brain(self, agent_id: str, *, create: bool = True) -> Brain:
        if agent_id not in self._brains:
            if not create:
                raise KeyError(agent_id)
            self._brains[agent_id] = make_default_brain(agent_id)
        return self._brains[agent_id]

    def remove_brain(self, agent_id: str) -> Brain:
        return self._brains.pop(agent_id)

    def save_brain(self, agent_id: str) -> Path:
        if self.image_store is None:
            raise RuntimeError("no BrainImageStore configured")
        return self.image_store.save(self.get_brain(agent_id))

    def load_brain(self, agent_id: str, *, register: bool = True) -> Brain:
        if self.image_store is None:
            raise RuntimeError("no BrainImageStore configured")
        brain = self.image_store.load(agent_id)
        if register:
            self.register_brain(brain, overwrite=True)
        return brain

    def think(
        self,
        agent_id: str,
        input_vector: Sequence[float] | np.ndarray,
        *,
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        return self.get_brain(agent_id).think(input_vector, top_k=top_k)

    def learn(
        self,
        agent_id: str,
        input_vector: Sequence[float] | np.ndarray,
        reward: float,
        *,
        context: str = "",
        domain: str | None = None,
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        return self.get_brain(agent_id).learn(
            input_vector,
            reward,
            context=context,
            domain=domain,
            top_k=top_k,
        )

    def think_text(self, agent_id: str, content: str, *, top_k: int = TOP_K) -> dict[str, Any]:
        result = self.think(agent_id, vector_from_payload(content), top_k=top_k)
        result["content_hash"] = _content_hash(content)
        return result

    def learn_text(
        self,
        agent_id: str,
        content: str,
        reward: float,
        *,
        context: str = "",
        domain: str | None = None,
        top_k: int = TOP_K,
        autosave: bool = False,
    ) -> dict[str, Any]:
        result = self.learn(
            agent_id,
            vector_from_payload(content),
            reward,
            context=context,
            domain=domain,
            top_k=top_k,
        )
        result["content_hash"] = _content_hash(content)
        if autosave and self.image_store is not None:
            result["image_path"] = str(self.save_brain(agent_id))
        return result

    def think_manifold(
        self,
        agent_id: str,
        manifold_vector: Sequence[float] | np.ndarray,
        *,
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        return self.get_brain(agent_id).think_manifold(manifold_vector, top_k=top_k)

    def learn_manifold(
        self,
        agent_id: str,
        manifold_vector: Sequence[float] | np.ndarray,
        reward: float,
        *,
        context: str = "",
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        return self.get_brain(agent_id).learn_manifold(
            manifold_vector,
            reward=reward,
            context=context,
            top_k=top_k,
        )

    def contribute(
        self,
        agent_id: str,
        *,
        domain: str = "",
        snap_labels: Sequence[str] = (),
        mi_score: float = 0.0,
    ) -> dict[str, Any]:
        contribution = self.get_brain(agent_id).contribute(
            domain=domain,
            snap_labels=snap_labels,
            mi_score=mi_score,
        )
        return contribution.to_dict()

    def record_observation(
        self,
        agent_id: str,
        *,
        datum_id: str,
        labels: Sequence[str],
        mdhg_address: str = "",
        accepted: bool = True,
        delta_phi: float = 0.0,
        boundary_type: str = "default",
        deception_severity: float = 0.0,
    ) -> dict[str, Any]:
        observation = self.get_brain(agent_id).record_observation(
            datum_id=datum_id,
            labels=labels,
            mdhg_address=mdhg_address,
            accepted=accepted,
            delta_phi=delta_phi,
            boundary_type=boundary_type,
            deception_severity=deception_severity,
        )
        return observation.to_dict()

    def vector_for_morphon(self, morphon: Morphon) -> np.ndarray:
        try:
            coords = morphon.project_to_e8()
            return np.asarray(coords, dtype=float)
        except (LookupError, ImportError, AttributeError, ValueError, TypeError):
            return vector_from_payload(morphon.payload)

    def think_morphon(
        self,
        agent_id: str,
        morphon: Morphon,
        *,
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        result = self.think(agent_id, self.vector_for_morphon(morphon), top_k=top_k)
        result["morphon_id"] = morphon.id
        return result

    def learn_morphon(
        self,
        agent_id: str,
        morphon: Morphon,
        reward: float,
        *,
        context: str = "",
        domain: str | None = None,
        top_k: int = TOP_K,
    ) -> dict[str, Any]:
        result = self.learn(
            agent_id,
            self.vector_for_morphon(morphon),
            reward,
            context=context,
            domain=domain,
            top_k=top_k,
        )
        result["morphon_id"] = morphon.id
        return result

    def snapshot_morphon(self, agent_id: str) -> Morphon:
        brain = self.get_brain(agent_id)
        state = brain.to_state()
        return Morphon.forge(
            payload={
                "type": "brain_state",
                "agent_id": agent_id,
                "brain": asdict(state),
                "image": brain.to_image(),
            }
        )

    def store_snapshot(self, agent_id: str) -> dict[str, Any]:
        snapshot = self.snapshot_morphon(agent_id)
        stored = False
        receipt_hash = None
        controller = MorphonController.get()
        if controller.has("memory"):
            memory = controller.get_provider("memory")
            memory.store(snapshot)
            stored = True
        if controller.has("receipt"):
            receipt = controller.get_provider("receipt").mint_crossing(
                atom_id=snapshot.id,
                boundary="cognition.brain.snapshot",
                agent_id=agent_id,
                payload={"stored": stored},
            )
            receipt_hash = getattr(receipt, "receipt_hash", None) or getattr(receipt, "hash", None)
        return {
            "agent_id": agent_id,
            "snapshot_id": snapshot.id,
            "stored": stored,
            "receipt_hash": receipt_hash,
        }

    @property
    def health(self) -> dict[str, Any]:
        return {
            "ok": True,
            "service": self.name,
            "brains": sorted(self._brains),
            "count": len(self._brains),
            "image_store": str(self.image_store.root) if self.image_store else None,
        }


def _content_hash(content: str) -> str:
    import hashlib

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


__all__ = ["BrainImageStore", "BrainProvider"]
