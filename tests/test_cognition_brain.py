from __future__ import annotations

import numpy as np

from cmplx.cognition.brain import (
    Brain,
    BrainImageStore,
    BrainProvider,
    label_signature,
    make_default_brain,
)
from cmplx.morphon import Morphon, MorphonController


def test_default_brain_thinks_learns_and_round_trips() -> None:
    brain = make_default_brain("agent-a")
    assert len(brain.experts) == 11
    assert brain.manifold().shape == (96,)

    vector = np.ones(8, dtype=float)
    thought = brain.think(vector)
    assert len(thought["experts"]) == 3

    learned = brain.learn(vector, 0.8, context="unit-test", domain="code")
    assert learned["learned"] is True
    assert brain.epoch == 1
    assert brain.contribution_points > 0

    restored = Brain.from_state(brain.to_state())
    assert restored.agent_id == brain.agent_id
    assert len(restored.experts) == len(brain.experts)
    assert restored.manifold().shape == (96,)

    image_restored = Brain.from_image(brain.to_image())
    assert image_restored.agent_id == brain.agent_id
    assert image_restored.capacity()["experts"] == len(brain.experts)


def test_brain_provider_uses_payload_fallback_without_registered_ports() -> None:
    MorphonController.reset_for_tests()
    provider = BrainProvider()
    morphon = Morphon.forge({"kind": "evidence", "value": "fallback"})

    thought = provider.think_morphon("agent-b", morphon)
    assert thought["morphon_id"] == morphon.id
    assert thought["experts"]

    learned = provider.learn_morphon("agent-b", morphon, 0.5, context="payload")
    assert learned["learned"] is True
    assert provider.get_brain("agent-b").epoch == 1


def test_brain_provider_snapshot_is_a_morphon() -> None:
    MorphonController.reset_for_tests()
    provider = BrainProvider()
    provider.get_brain("agent-c")

    snapshot = provider.snapshot_morphon("agent-c")
    assert snapshot.payload["type"] == "brain_state"
    assert snapshot.payload["agent_id"] == "agent-c"
    assert snapshot.payload["brain"]["agent_id"] == "agent-c"

    stored = provider.store_snapshot("agent-c")
    assert stored["agent_id"] == "agent-c"
    assert stored["stored"] is False


def test_brain_expertise_fork_merge_and_compress() -> None:
    brain = make_default_brain("agent-d")
    expertise = brain.expertise()
    assert expertise[0]["domain"]

    child = brain.fork("agent-d-child", domain_boost="curation")
    assert child.agent_id == "agent-d-child"
    assert len(child.experts) == len(brain.experts) + 1

    before = len(brain.experts)
    receipt = brain.merge(child, weight=0.25)
    assert receipt["merged"] >= before
    assert len(brain.experts) >= before

    compact = brain.compress(0.01)
    assert compact["total"] == len(brain.experts) * 8


def test_brain_image_store_and_text_routing(tmp_path) -> None:
    provider = BrainProvider(image_store=BrainImageStore(tmp_path))

    thought = provider.think_text("agent-e", "classify this CMPLX evidence")
    assert thought["content_hash"]
    assert thought["experts"]

    learned = provider.learn_text(
        "agent-e",
        "classify this CMPLX evidence",
        0.9,
        context="text-routing",
        autosave=True,
    )
    assert learned["learned"] is True
    assert learned["image_path"].endswith(".brain.json")

    provider.remove_brain("agent-e")
    restored = provider.load_brain("agent-e")
    assert restored.agent_id == "agent-e"
    assert restored.epoch == 1


def test_brain_manifold_contribution_capacity_and_observation() -> None:
    brain = make_default_brain("agent-f")
    manifold = np.linspace(-1.0, 1.0, 96)

    thought = brain.think_manifold(manifold)
    assert set(thought["roles"]) == {"SELF", "MEMORY", "BODY", "ATTENTION"}

    learned = brain.learn_manifold(manifold, reward=0.8, context="system-state")
    assert learned["learned"] is True
    assert brain.epoch == 12

    contribution = brain.contribute(
        domain="labeling",
        snap_labels=["snap", "brain", "routing"],
        mi_score=0.8,
    )
    assert contribution.domain == "labeling"
    assert brain.specialist_profile()["labeling"] >= 0.8

    observation = brain.record_observation(
        datum_id="datum-1",
        labels=["snap", "brain"],
        mdhg_address="mdhg://3/6/9",
        accepted=True,
        delta_phi=-0.1,
    )
    assert observation.label_sig == label_signature(["brain", "snap"])
    assert brain.metadata["observations"][-1]["accepted"] is True

    capacity = brain.capacity_score(mi_history=[0.5] * 10, step_count=8000)
    assert capacity["capacity_score"] > 0.0


def test_provider_manifold_and_label_memory_helpers() -> None:
    provider = BrainProvider()
    manifold = np.ones(96)

    learned = provider.learn_manifold("agent-g", manifold, 0.7, context="provider")
    assert learned["learned"] is True

    contribution = provider.contribute(
        "agent-g",
        domain="operations",
        snap_labels=["docker", "body"],
        mi_score=0.6,
    )
    assert contribution["agent_id"] == "agent-g"

    observation = provider.record_observation(
        "agent-g",
        datum_id="datum-2",
        labels=["docker", "body"],
        mdhg_address="mdhg://body",
    )
    assert observation["label_sig"] == label_signature(["body", "docker"])
