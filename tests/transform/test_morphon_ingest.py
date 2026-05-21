"""Transform ingest ↔ morphon combine / store wiring."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from cmplx.morphon import Morphon, MorphonController
from cmplx.morphon.links import is_tarpit_linked, link_labels
from cmplx.transform.ingest import CorpusIngester
from cmplx.transform.morphon_ingest import bond_inherit_link, forge_ingest_morphon


class _FakeMemory:
    def __init__(self) -> None:
        self.stored: dict[str, Morphon] = {}

    def store(self, morphon: Morphon) -> None:
        self.stored[morphon.id] = morphon

    def fetch(self, morphon_id: str) -> Morphon | None:
        return self.stored.get(morphon_id)


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_forge_ingest_bonds_consecutive_segments():
    MorphonController.get().register("memory", _FakeMemory())
    a, _ = forge_ingest_morphon({"concat": "11111111"}, store=True, bond_with_prev=False)
    b, bond = forge_ingest_morphon(
        {"concat": "22222222"},
        prev=a,
        store=True,
        bond_with_prev=True,
    )
    assert bond is not None
    assert bond.payload["combination"] == "inherit_link"
    assert bond.payload["parents"] == [a.id, b.id]
    assert MorphonController.get().fetch(b.id) is not None


def test_bond_inherit_link_carries_tarpit_labels():
    MorphonController.get().register("memory", _FakeMemory())
    left = Morphon.forge({"concat": "aaaaaaaa"})
    left = left.annotate_links(**link_labels(left, tarpit_atom_id="deadbeef1234"))
    right = Morphon.forge({"concat": "bbbbbbbb"})
    bonded = bond_inherit_link(left, right)
    assert is_tarpit_linked(bonded.payload)
    assert bonded.payload["tarpit_atom_id"] == "deadbeef1234"


def test_ingest_chunk_creates_bond_morphons():
    from cmplx.transform.bridge import reset_bootstrap_state

    reset_bootstrap_state()
    MorphonController.reset_for_tests()
    MorphonController.get().register("memory", _FakeMemory())
    with tempfile.TemporaryDirectory() as tmp:
        doc = Path(tmp) / "note.md"
        # Unique body so token index is cold and multiple segments forge bonds.
        doc.write_text(
            "# BondTest\n" + ("xyzzyxwv" * 60) + "\n" + ("qrstuvwx" * 60),
            encoding="utf-8",
        )
        db = Path(tmp) / "token_index.sqlite"
        ing = CorpusIngester(register_ports=True, chunk_size=200)
        stats = ing.ingest_path(Path(tmp), db=db)
        assert stats.chunks_seen >= 1
        assert stats.new_bonds >= 2
        assert stats.bond_morphons >= 1
