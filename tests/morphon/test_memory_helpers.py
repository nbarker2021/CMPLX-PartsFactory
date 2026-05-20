"""MorphonController store / fetch helpers."""
from __future__ import annotations

import pytest

from cmplx.morphon import Morphon, MorphonController
from cmplx.receipt.provider import ReceiptProvider
from cmplx.receipt.types import ReceiptType


class _FakeMemory:
    def __init__(self) -> None:
        self._data: dict[str, Morphon] = {}

    def store(self, morphon: Morphon) -> None:
        self._data[morphon.id] = morphon

    def fetch(self, morphon_id: str) -> Morphon | None:
        return self._data.get(morphon_id)


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_store_and_fetch_roundtrip():
    mem = _FakeMemory()
    ctrl = MorphonController.get()
    ctrl.register("memory", mem)
    m = Morphon.forge(payload={"x": 1})
    ctrl.store(m)
    back = ctrl.fetch(m.id)
    assert back is not None
    assert back.id == m.id


def test_fetch_without_memory_returns_none():
    m = Morphon.forge(payload={})
    assert MorphonController.get().fetch(m.id) is None


def test_fetch_required_raises_when_missing():
    MorphonController.get().register("memory", _FakeMemory())
    with pytest.raises(LookupError, match="not found"):
        MorphonController.get().fetch_required("missing-id")


def test_store_mints_process_receipt():
    MorphonController.get().register("receipt", ReceiptProvider())
    MorphonController.get().register("memory", _FakeMemory())
    m = Morphon.forge(payload={})
    MorphonController.get().store(m)
    prov = MorphonController.get().get_provider("receipt")
    assert prov.chain._chain[-1].receipt_type == ReceiptType.PROCESS.value
    assert prov.chain._chain[-1].atom_id == m.id
