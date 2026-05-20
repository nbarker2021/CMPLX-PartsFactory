"""
HTTP/service wrapper for the CMPLX cognition brain product.

The service wraps ``BrainProvider``. It keeps HTTP, compatibility routes, and
deferred bridge stubs outside the core brain image so the library remains the
source of truth.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cmplx.runtime_paths import runtime_path

from ._constants import TOP_K
from .core import Brain, make_default_brain
from .provider import BrainImageStore, BrainProvider


DEFAULT_AGENT_ID = os.getenv("CMPLX_BRAIN_AGENT_ID", "manny")
DEFAULT_IMAGE_DIR = os.getenv(
    "CMPLX_BRAIN_IMAGE_DIR",
    str(runtime_path("brain_images")),
)


@dataclass(frozen=True)
class BridgeStub:
    """A known future bridge point that should not be guessed today."""

    name: str
    status: str
    current_behavior: str
    deferred_need: str
    expected_port: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class BrainBridgeStubs:
    """Registry of explicit no-op bridge placeholders."""

    def __init__(self) -> None:
        self._stubs = {
            "controller_port": BridgeStub(
                name="controller_port",
                status="deferred",
                current_behavior="Brain service remains a normal HTTP/library wrapper.",
                deferred_need="Protocol decision for a first-class cognition or brain port.",
                expected_port="cognition|brain",
            ),
            "conservation_gate": BridgeStub(
                name="conservation_gate",
                status="stub",
                current_behavior="Requests expose delta_phi fields but do not enforce NSL.",
                deferred_need="Wire to the live conservation port before gating learning.",
                expected_port="conservation",
            ),
            "pg_persistence": BridgeStub(
                name="pg_persistence",
                status="stub",
                current_behavior="Brain images persist through optional JSON image store.",
                deferred_need="Add PG tables only as a service adapter, not core state.",
                expected_port="external_postgres",
            ),
            "docker_lattice_seed": BridgeStub(
                name="docker_lattice_seed",
                status="stub",
                current_behavior="96-D manifold learning accepts supplied vectors.",
                deferred_need=(
                    "Collect live Docker/service body lattice through controller evidence."
                ),
                expected_port="repo_kernel|docker",
            ),
            "cqe_personal_step": BridgeStub(
                name="cqe_personal_step",
                status="stub",
                current_behavior="CQE/dPhi personal-node operations are not executed here.",
                deferred_need="Bridge to engine.cqe and conservation ports with receipts.",
                expected_port="engine|conservation|receipt",
            ),
        }

    def all(self) -> dict[str, dict[str, str]]:
        return {name: stub.to_dict() for name, stub in self._stubs.items()}

    def get(self, name: str) -> dict[str, str]:
        if name not in self._stubs:
            raise KeyError(name)
        return self._stubs[name].to_dict()

    def plan(self, name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        stub = self.get(name)
        return {
            **stub,
            "accepted": False,
            "payload_keys": sorted((payload or {}).keys()),
            "reason": "bridge stub only; no external mutation performed",
        }


class RegisterRequest(BaseModel):
    agent_id: str = DEFAULT_AGENT_ID
    image: dict[str, Any] | None = None
    overwrite: bool = True


class VectorRequest(BaseModel):
    agent_id: str = DEFAULT_AGENT_ID
    input_vector: list[float] = Field(default_factory=list)
    top_k: int = TOP_K


class LearnRequest(VectorRequest):
    reward: float = 0.0
    context: str = ""
    domain: str | None = None


class TextRequest(BaseModel):
    agent_id: str = DEFAULT_AGENT_ID
    content: str
    top_k: int = TOP_K


class LearnTextRequest(TextRequest):
    reward: float = 0.0
    context: str = ""
    domain: str | None = None
    autosave: bool = False


class ManifoldRequest(BaseModel):
    agent_id: str = DEFAULT_AGENT_ID
    manifold_vector: list[float] = Field(default_factory=list)
    top_k: int = TOP_K


class LearnManifoldRequest(ManifoldRequest):
    reward: float = 0.0
    context: str = ""


class ContributionRequest(BaseModel):
    agent_id: str = DEFAULT_AGENT_ID
    domain: str = ""
    snap_labels: list[str] = Field(default_factory=list)
    mi_score: float = 0.0


class ObservationRequest(BaseModel):
    agent_id: str = DEFAULT_AGENT_ID
    datum_id: str
    labels: list[str] = Field(default_factory=list)
    mdhg_address: str = ""
    accepted: bool = True
    delta_phi: float = 0.0
    boundary_type: str = "default"
    deception_severity: float = 0.0


class ForkRequest(BaseModel):
    parent_id: str
    child_id: str
    domain_boost: str = ""


class MergeRequest(BaseModel):
    target_id: str
    source_id: str
    weight: float = 0.5


class CompressRequest(BaseModel):
    agent_id: str = DEFAULT_AGENT_ID
    ratio: float = 0.3


class RunRequest(BaseModel):
    task: str
    domain: str = "general"
    context: dict[str, Any] = Field(default_factory=dict)
    agent_id: str = DEFAULT_AGENT_ID


class ProbeRequest(BaseModel):
    query: str
    domain: str = "general"
    agent_id: str = DEFAULT_AGENT_ID


class BridgePlanRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


class BrainHTTPService:
    """Service facade with old brain-service compatibility routes."""

    def __init__(
        self,
        provider: BrainProvider | None = None,
        *,
        bridges: BrainBridgeStubs | None = None,
    ) -> None:
        self.provider = provider or BrainProvider(image_store=DEFAULT_IMAGE_DIR)
        self.bridges = bridges or BrainBridgeStubs()

    def health(self) -> dict[str, Any]:
        return {
            **self.provider.health,
            "service": "cmplx-cognition-brain",
            "bridges": self.bridges.all(),
        }

    def status(self) -> dict[str, Any]:
        brains = []
        for agent_id in self.provider.health["brains"]:
            brain = self.provider.get_brain(agent_id, create=False)
            brains.append({"agent_id": agent_id, **brain.capacity()})
        return {"brains": brains, "count": len(brains), "bridges": self.bridges.all()}

    def register(self, body: RegisterRequest) -> dict[str, Any]:
        brain = Brain.from_image(body.image) if body.image else make_default_brain(body.agent_id)
        self.provider.register_brain(brain, overwrite=body.overwrite)
        return {"registered": brain.agent_id, "capacity": brain.capacity()}

    def image(self, agent_id: str) -> dict[str, Any]:
        try:
            return self.provider.get_brain(agent_id, create=False).to_image()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Brain not registered") from exc

    def experts(self, domain: str = "", min_confidence: float = 0.0) -> dict[str, Any]:
        rows = []
        for agent_id in self.provider.health["brains"]:
            rows.extend(
                self.provider.get_brain(agent_id, create=False).expertise(
                    domain=domain,
                    min_confidence=min_confidence,
                )
            )
        return {"experts": rows, "total": len(rows)}

    def capacity(self, agent_id: str | None = None) -> dict[str, Any]:
        if agent_id:
            brain = self.provider.get_brain(agent_id)
            return {"agent_id": agent_id, **brain.capacity_score(), "capacity": brain.capacity()}
        return {
            agent_id: self.provider.get_brain(agent_id, create=False).capacity()
            for agent_id in self.provider.health["brains"]
        }


def create_app(provider: BrainProvider | None = None) -> FastAPI:
    service = BrainHTTPService(provider)
    app = FastAPI(
        title="CMPLX Cognition Brain",
        description="HTTP wrapper for the composed-E8 brain product.",
    )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return service.health()

    @app.get("/status")
    def status() -> dict[str, Any]:
        return service.status()

    @app.post("/register")
    def register(body: RegisterRequest) -> dict[str, Any]:
        return service.register(body)

    @app.get("/brain/{agent_id}")
    def brain_image(agent_id: str) -> dict[str, Any]:
        return service.image(agent_id)

    @app.post("/think")
    def think(body: VectorRequest) -> dict[str, Any]:
        return service.provider.think(body.agent_id, body.input_vector, top_k=body.top_k)

    @app.post("/learn")
    def learn(body: LearnRequest) -> dict[str, Any]:
        return service.provider.learn(
            body.agent_id,
            body.input_vector,
            body.reward,
            context=body.context,
            domain=body.domain,
            top_k=body.top_k,
        )

    @app.post("/think_text")
    def think_text(body: TextRequest) -> dict[str, Any]:
        return service.provider.think_text(body.agent_id, body.content, top_k=body.top_k)

    @app.post("/learn_text")
    def learn_text(body: LearnTextRequest) -> dict[str, Any]:
        return service.provider.learn_text(
            body.agent_id,
            body.content,
            body.reward,
            context=body.context,
            domain=body.domain,
            top_k=body.top_k,
            autosave=body.autosave,
        )

    @app.post("/think_manifold")
    def think_manifold(body: ManifoldRequest) -> dict[str, Any]:
        return service.provider.think_manifold(
            body.agent_id,
            body.manifold_vector,
            top_k=body.top_k,
        )

    @app.post("/learn_manifold")
    def learn_manifold(body: LearnManifoldRequest) -> dict[str, Any]:
        return service.provider.learn_manifold(
            body.agent_id,
            body.manifold_vector,
            body.reward,
            context=body.context,
            top_k=body.top_k,
        )

    @app.post("/contribute")
    def contribute(body: ContributionRequest) -> dict[str, Any]:
        return service.provider.contribute(
            body.agent_id,
            domain=body.domain,
            snap_labels=body.snap_labels,
            mi_score=body.mi_score,
        )

    @app.post("/observation")
    def observation(body: ObservationRequest) -> dict[str, Any]:
        return service.provider.record_observation(
            body.agent_id,
            datum_id=body.datum_id,
            labels=body.labels,
            mdhg_address=body.mdhg_address,
            accepted=body.accepted,
            delta_phi=body.delta_phi,
            boundary_type=body.boundary_type,
            deception_severity=body.deception_severity,
        )

    @app.post("/fork")
    def fork(body: ForkRequest) -> dict[str, Any]:
        parent = service.provider.get_brain(body.parent_id)
        child = parent.fork(body.child_id, domain_boost=body.domain_boost)
        service.provider.register_brain(child, overwrite=True)
        return {"forked": True, "parent": body.parent_id, "child": body.child_id}

    @app.post("/merge")
    def merge(body: MergeRequest) -> dict[str, Any]:
        target = service.provider.get_brain(body.target_id)
        source = service.provider.get_brain(body.source_id, create=False)
        return {
            "target": body.target_id,
            "source": body.source_id,
            **target.merge(source, weight=body.weight),
        }

    @app.post("/compress")
    def compress(body: CompressRequest) -> dict[str, Any]:
        return service.provider.get_brain(body.agent_id).compress(body.ratio)

    @app.post("/snapshot/{agent_id}")
    def snapshot(agent_id: str) -> dict[str, Any]:
        morphon = service.provider.snapshot_morphon(agent_id)
        return morphon.serialize()

    @app.post("/snapshot/{agent_id}/store")
    def store_snapshot(agent_id: str) -> dict[str, Any]:
        return service.provider.store_snapshot(agent_id)

    @app.post("/image/{agent_id}/save")
    def save_image(agent_id: str) -> dict[str, Any]:
        return {"agent_id": agent_id, "path": str(service.provider.save_brain(agent_id))}

    @app.post("/image/{agent_id}/load")
    def load_image(agent_id: str) -> dict[str, Any]:
        brain = service.provider.load_brain(agent_id)
        return {"agent_id": brain.agent_id, "capacity": brain.capacity()}

    @app.get("/expertise")
    def expertise(domain: str = "", min_confidence: float = 0.0) -> dict[str, Any]:
        return service.experts(domain=domain, min_confidence=min_confidence)

    @app.get("/capacity")
    def capacity(agent_id: str | None = None) -> dict[str, Any]:
        return service.capacity(agent_id)

    @app.get("/experts")
    def experts(domain: str = "", min_confidence: float = 0.0) -> dict[str, Any]:
        return service.experts(domain=domain, min_confidence=min_confidence)

    @app.post("/probe")
    def probe(body: ProbeRequest) -> dict[str, Any]:
        return {
            "agent_id": body.agent_id,
            "domain": body.domain,
            **service.provider.think_text(body.agent_id, body.query),
        }

    @app.post("/run")
    def run(body: RunRequest) -> dict[str, Any]:
        content = f"{body.domain}:{body.task}:{body.context}"
        thought = service.provider.think_text(body.agent_id, content)
        return {"agent_id": body.agent_id, "domain": body.domain, "thought": thought}

    @app.get("/verbalize")
    def verbalize(topic: str) -> dict[str, Any]:
        return {
            "topic": topic,
            "summary": "brain service wrapper is active; generation bridge deferred",
            "bridge": service.bridges.get("controller_port"),
        }

    @app.post("/learn_forward")
    def learn_forward(body: LearnRequest) -> dict[str, Any]:
        return learn(body)

    @app.post("/think_forward")
    def think_forward(body: VectorRequest) -> dict[str, Any]:
        return think(body)

    @app.get("/bridges")
    def bridges() -> dict[str, dict[str, str]]:
        return service.bridges.all()

    @app.get("/bridges/{name}")
    def bridge(name: str) -> dict[str, str]:
        try:
            return service.bridges.get(name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown bridge stub") from exc

    @app.post("/bridges/{name}/plan")
    def bridge_plan(name: str, body: BridgePlanRequest) -> dict[str, Any]:
        try:
            return service.bridges.plan(name, body.payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown bridge stub") from exc

    @app.post("/tick")
    def tick() -> dict[str, Any]:
        return {
            "ok": True,
            "service": "brain",
            "registered_brains": service.provider.health["count"],
        }

    return app


__all__ = [
    "BrainBridgeStubs",
    "BrainHTTPService",
    "BridgeStub",
    "create_app",
]
