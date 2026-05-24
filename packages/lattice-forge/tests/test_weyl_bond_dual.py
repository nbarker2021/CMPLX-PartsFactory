from __future__ import annotations

import tempfile
from pathlib import Path

from lattice_forge.backwalk.schema import WorkStore
from lattice_forge.backwalk.weyl_bond_dual import (
    MIDDLE_CHART_INDICES,
    QUADRANT_CHART_INDICES,
    iter_batch_specs,
    materialize_weyl_bond_batch,
)
from lattice_forge.backwalk.weyl_bond_quadrant import concatenate_quadrant_trees


def test_dual_batch_count_single_quadrant():
    # Each quadrant has 2 chart states at one dual_depth → 25 pairs × 2 directions × 1 depth = 50
    assert len(list(iter_batch_specs(quadrant=2))) == 50


def test_dual_batch_count_all_quadrants():
    assert len(list(iter_batch_specs())) == 200


def test_single_batch_writes_bonds():
    spec = next(iter(iter_batch_specs(quadrant=2)))
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "t.db"
        with WorkStore(db) as store:
            stats = materialize_weyl_bond_batch(store, spec, max_rows=64, mirror_oloid=True)
            assert stats["rows_written"] >= 1
            assert store.count_weyl_bonds() >= 1


def test_middle_chart_is_axis2_doublet():
    assert set(MIDDLE_CHART_INDICES) == {2, 5}


def test_quadrants_partition_chart():
    seen = set()
    for q, indices in QUADRANT_CHART_INDICES.items():
        assert len(indices) == 2
        for i in indices:
            assert i not in seen
            seen.add(i)
    assert seen == set(range(8))


def test_concatenate_quadrant_tree():
    spec = next(iter(iter_batch_specs(quadrant=1)))
    with tempfile.TemporaryDirectory() as tmp:
        with WorkStore(Path(tmp) / "t.db") as store:
            materialize_weyl_bond_batch(store, spec, max_rows=64, mirror_oloid=False)
            root = concatenate_quadrant_trees(store)
            assert root["quadrant_count"] == 4
