"""End-to-end tests for the TokenIndexBuilder.

These are the falsifiable claims from the spec:

  - A level-1-only build is mostly cold (nothing in cache yet).
  - A level-2 build on top of level-1 is mostly *predecessor* hits.
  - A level-2 build with derived case modes is mostly *case_base* hits
    after LOWER has populated.
  - Re-running the builder with the same config is mostly EXACT hits.

The builder writes to a temporary SQLite, and the SpeedLight provider
is shared across invocations within one process (the controller is a
singleton), which is exactly the behavior we are testing.
"""
from __future__ import annotations

import pytest

from cmplx.transform.token_index import (
    CaseMode,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    TokenIndexStore,
    any_filter,
    english_filter,
)
from cmplx.transform.token_index.warmstart import WarmStartOutcome


@pytest.fixture
def tmp_db(tmp_path):
    return str(tmp_path / "token_index.sqlite")


def _config(tmp_db: str, **overrides) -> TokenIndexBuildConfig:
    base = dict(
        levels=(1,),
        alphabet=tuple("abc"),
        case_modes=[CaseMode.LOWER],
        languages=[any_filter()],
        db_path=tmp_db,
        progress_every=0,
    )
    base.update(overrides)
    return TokenIndexBuildConfig(**base)


def test_level_1_cold_build_populates_index(tmp_db):
    builder = TokenIndexBuilder(_config(tmp_db))
    result = builder.build()
    # alphabet "abc" → 2 level-1 bonds (excluding all-base).
    assert result.total_stored == 2
    # First pass is entirely cold.
    assert result.warmstart_stats.cold == 2
    assert result.warmstart_stats.exact == 0
    # SQLite reflects the rows.
    assert builder.store.count() == 2


def test_rerun_is_all_exact_hits(tmp_db):
    cfg = _config(tmp_db)
    first = TokenIndexBuilder(cfg).build()
    assert first.warmstart_stats.cold == 2

    # Second pass: the SpeedLight cache survived in the controller's
    # singleton SpeedLight provider, so every probe should hit EXACT.
    second = TokenIndexBuilder(cfg).build()
    assert second.warmstart_stats.exact == 2
    assert second.warmstart_stats.cold == 0


def test_level_2_finds_level_1_predecessors(tmp_db):
    cfg = _config(tmp_db, levels=(1, 2))
    result = TokenIndexBuilder(cfg).build()

    # Level 1: alphabet "abc" → 2 bonds, all cold.
    level_1 = result.per_level[1]
    assert level_1.cold == 2

    # Level 2 with alphabet "abc" (base "a") gives 3^2 - 1 = 8 bonds.
    # Their warm-start classification breaks down as follows:
    #   - (outer=b/c, inner=a) → 2 entries. The inner-ring char is base
    #     so the concat collapses to the level-1 form already cached
    #     → EXACT.
    #   - (outer=b/c, inner=b/c) → 4 entries. Genuine level-2 bonds;
    #     their level-1 predecessor (outer ring only) is cached →
    #     PREDECESSOR.
    #   - (outer=a, inner=b/c) → 2 entries. Their level-1 predecessor
    #     would be the all-base bond, which is filtered out and never
    #     published → COLD.
    level_2 = result.per_level[2]
    assert level_2.total == 8
    assert level_2.exact == 2
    assert level_2.predecessor == 4
    assert level_2.cold == 2
    # The substrate's claim: most level-2 entries warm-start. Quantify it.
    assert (level_2.exact + level_2.predecessor) > level_2.cold


def test_derived_case_modes_hit_lower_as_case_base(tmp_db):
    cfg = _config(
        tmp_db,
        case_modes=[CaseMode.LOWER, CaseMode.UPPER, CaseMode.LEAD_LEFT],
    )
    result = TokenIndexBuilder(cfg).build()

    # LOWER first: 2 cold forges populate the case_base keys.
    lower_stats = result.per_case["lower"]
    assert lower_stats.cold == 2

    # UPPER and LEAD_LEFT each have 2 bonds and should hit case_base
    # because the LOWER form is already in cache.
    for derived in ("upper", "lead_left"):
        stats = result.per_case[derived]
        assert stats.total == 2
        assert stats.case_base == 2
        assert stats.cold == 0


def test_english_filter_inherits_from_any(tmp_db):
    cfg = _config(
        tmp_db,
        levels=(1, 2),
        alphabet=tuple("the"),
        languages=[any_filter(), english_filter(min_common=0)],
    )
    result = TokenIndexBuilder(cfg).build()

    # `any` runs first → cold forges.
    any_stats = result.per_language["any"]
    # `english` runs second → every concat already exists from `any`,
    # so probes are EXACT.
    english_stats = result.per_language["english"]
    assert english_stats.cold == 0
    assert english_stats.exact == any_stats.total - any_stats.exact


def test_store_records_warmstart_outcomes(tmp_db):
    cfg = _config(tmp_db, levels=(1, 2))
    TokenIndexBuilder(cfg).build()
    store = TokenIndexStore(tmp_db)
    try:
        stats = store.stats()
    finally:
        store.close()
    # Every row must carry a warmstart classification.
    total_classified = sum(stats["by_warmstart"].values())
    assert total_classified == stats["total_rows"]
    # At least one cold (the very first forge) and at least one
    # non-cold (level-2 predecessors).
    assert stats["by_warmstart"].get("cold", 0) >= 1
    non_cold = sum(v for k, v in stats["by_warmstart"].items() if k != "cold")
    assert non_cold >= 1
