from __future__ import annotations

from lattice_forge.mckay_matrix_tables import (
    BOOTSTRAP_DIMENSIONS,
    build_conjugate_set_tables,
    export_matrix_catalog,
    get_j_matrix,
    j_matrix_for_class,
    nested_block_consistency,
    verify_mckay_matrix_bootstrap,
)
from lattice_forge.j_modular_matrix import J_MATRIX_3A, get_j_matrix as jm_get


def test_bootstrap_dimensions():
    assert BOOTSTRAP_DIMENSIONS == (5, 7, 9)


def test_3a_9x9_matches_legacy():
    assert j_matrix_for_class("3A", 9) == J_MATRIX_3A
    assert jm_get("3A") == J_MATRIX_3A


def test_all_classes_catalog_no_errors():
    cat = build_conjugate_set_tables()
    assert cat["errors"] == []
    for g in ("1A", "2A", "3A", "5A", "7A"):
        for dim in (5, 7, 9):
            assert str(dim) in cat["tables"][g]


def test_nesting_7_in_9_for_3a():
    m7 = j_matrix_for_class("3A", 7)
    m9 = j_matrix_for_class("3A", 9)
    assert nested_block_consistency(m7, m9)


def test_verify_bootstrap_passes():
    r = verify_mckay_matrix_bootstrap()
    assert r["status"] == "pass"
    assert r["3A_9x9_a1_is_783"]


def test_export_catalog(tmp_path):
    path = export_matrix_catalog(tmp_path / "mckay_matrix_catalog.json")
    assert path.is_file()
    assert path.stat().st_size > 1000


def test_get_j_matrix_7a_7x7():
    m = get_j_matrix("7A", 7)
    assert len(m) == 7
    assert m[1][0] == 51
