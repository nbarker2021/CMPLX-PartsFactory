from __future__ import annotations

from fastapi.testclient import TestClient

from cmplx.cognition.brain import BrainProvider
from cmplx.cognition.brain.provider import BrainImageStore
from cmplx.cognition.brain.service import create_app


def test_brain_http_service_core_routes(tmp_path) -> None:
    provider = BrainProvider(image_store=BrainImageStore(tmp_path))
    client = TestClient(create_app(provider))

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "cmplx-cognition-brain"

    response = client.post("/register", json={"agent_id": "svc-a"})
    assert response.status_code == 200
    assert response.json()["registered"] == "svc-a"

    response = client.post(
        "/think_text",
        json={"agent_id": "svc-a", "content": "route this evidence"},
    )
    assert response.status_code == 200
    assert response.json()["experts"]

    response = client.post(
        "/learn_text",
        json={
            "agent_id": "svc-a",
            "content": "route this evidence",
            "reward": 0.8,
            "autosave": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["image_path"].endswith(".brain.json")

    response = client.get("/brain/svc-a")
    assert response.status_code == 200
    assert response.json()["agent_id"] == "svc-a"


def test_brain_http_service_manifold_and_lineage_routes(tmp_path) -> None:
    provider = BrainProvider(image_store=BrainImageStore(tmp_path))
    client = TestClient(create_app(provider))
    client.post("/register", json={"agent_id": "svc-parent"})

    response = client.post(
        "/learn_manifold",
        json={
            "agent_id": "svc-parent",
            "manifold_vector": [1.0] * 96,
            "reward": 0.7,
            "context": "service-test",
        },
    )
    assert response.status_code == 200
    assert response.json()["learned"] is True

    response = client.post(
        "/contribute",
        json={
            "agent_id": "svc-parent",
            "domain": "operations",
            "snap_labels": ["docker", "body"],
            "mi_score": 0.6,
        },
    )
    assert response.status_code == 200
    assert response.json()["domain"] == "operations"

    response = client.post(
        "/observation",
        json={
            "agent_id": "svc-parent",
            "datum_id": "datum-service",
            "labels": ["service", "brain"],
            "mdhg_address": "mdhg://service",
        },
    )
    assert response.status_code == 200
    assert response.json()["label_sig"]

    response = client.post(
        "/fork",
        json={"parent_id": "svc-parent", "child_id": "svc-child", "domain_boost": "service"},
    )
    assert response.status_code == 200
    assert response.json()["forked"] is True

    response = client.post(
        "/merge",
        json={"target_id": "svc-parent", "source_id": "svc-child", "weight": 0.25},
    )
    assert response.status_code == 200
    assert response.json()["target"] == "svc-parent"


def test_brain_http_service_compatibility_and_bridge_stubs(tmp_path) -> None:
    provider = BrainProvider(image_store=BrainImageStore(tmp_path))
    client = TestClient(create_app(provider))

    response = client.post(
        "/probe",
        json={"agent_id": "svc-compat", "query": "brain route?", "domain": "general"},
    )
    assert response.status_code == 200
    assert response.json()["experts"]

    response = client.post(
        "/run",
        json={"agent_id": "svc-compat", "task": "inspect state", "domain": "brain"},
    )
    assert response.status_code == 200
    assert response.json()["thought"]["experts"]

    response = client.get("/bridges")
    assert response.status_code == 200
    assert "conservation_gate" in response.json()

    response = client.post(
        "/bridges/conservation_gate/plan",
        json={"payload": {"delta_phi": 0.1}},
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is False
