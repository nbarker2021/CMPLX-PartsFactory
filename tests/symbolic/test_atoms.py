"""unified_tarpit atom layer — DerivationKey, Atom, AtomField."""
from __future__ import annotations

from cmplx.symbolic.tarpit.atoms import (
    Atom,
    AtomField,
    BOND_THRESHOLD_DUST,
    DerivationKey,
    bond_atoms,
    wrap_run,
)
from cmplx.symbolic.tarpit._functions import run_etp_with_ledger


def test_derivation_key_hash_stable():
    k1 = DerivationKey(program="}01", dimension=8, max_steps=50)
    k2 = DerivationKey(program="}01", dimension=8, max_steps=50)
    assert k1.deterministic_hash() == k2.deterministic_hash()


def test_atom_from_program_compact():
    atom = Atom.from_program("}01", max_steps=30, dimension=8)
    cr = atom.compact_repr()
    assert cr["atom_id"]
    assert cr["program_len"] == 3
    assert "wall_serial" in cr or "torus" in cr


def test_atom_re_derive_matches_steps():
    atom = Atom.from_program("}01", max_steps=25, dimension=8)
    out = atom.re_derive()
    assert "summary" in out
    assert "ledger" in out
    assert out["summary"]["steps_executed"] >= 0


def test_wrap_run_roundtrip():
    raw = run_etp_with_ledger("}01", max_steps=20, dimension=8)
    key = DerivationKey(program="}01", max_steps=20, dimension=8)
    atom = wrap_run(raw, key)
    assert atom.atom_id
    assert atom.signature.wall_serial


def test_bond_atoms_self_compatible():
    atom = Atom.from_program("}01", max_steps=20)
    br = bond_atoms(atom, atom)
    assert br.bonded
    assert br.compatibility == 1.0


def test_atom_field_screen():
    field = AtomField()
    field.add_program("}01", max_steps=15)
    field.add_program("}10", max_steps=15)
    screen = field.screen_bonds()
    assert len(screen) == 1
    assert "compatibility" in screen[0]


def test_atom_field_threshold():
    field = AtomField(bond_threshold=BOND_THRESHOLD_DUST)
    a = field.add_program("}01", max_steps=15)
    b = field.add_program("}10", max_steps=15)
    br = bond_atoms(a, b, threshold=0.99)
    assert not br.bonded or br.compatibility >= 0.99
