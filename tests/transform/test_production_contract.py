"""Production GeometricTransformer contract — N-ladder, SpeedLight, substrate epoch."""
from __future__ import annotations

import pytest

from cmplx.morphon import Morphon
from cmplx.primitives.core import NLAECNFChain
from cmplx.transform.config import ProductionTransformerConfig
from cmplx.transform.shell import MorphonShell
from cmplx.transform.shell_config import ShellConfig
from cmplx.transform.token_index import (
    CaseMode,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    TokenIndexStore,
    any_filter,
)
from cmplx.transform.token_index.warmstart import IndexEntryPayload
from cmplx.transform.transformer import GeometricTransformer
from cmplx.transform.types import ShellViolation


@pytest.fixture
def production_db(tmp_path):
    db = tmp_path / "prod.sqlite"
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=(1, 2),
            alphabet=tuple("abcde"),
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=str(db),
            progress_every=0,
            max_entries=80,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    return db


def test_production_forward_eight_layer_traces(production_db):
    store = TokenIndexStore(str(production_db))
    shell = MorphonShell(ShellConfig(), store)
    try:
        row = store._conn.execute("SELECT concat FROM token_bonds LIMIT 1").fetchone()
        ribbon = str(row[0])
        model = GeometricTransformer(
            ProductionTransformerConfig(register_ports_on_init=False),
            shell=shell,
        )
        out = model.forward(ribbon)
        assert len(out.layer_traces) == 8
        assert out.summary.get("config_digest")
        assert "substrate_epoch" in out.summary
    finally:
        store.close()


def test_production_speedlight_second_hit(production_db):
    store = TokenIndexStore(str(production_db))
    shell = MorphonShell(ShellConfig(), store)
    try:
        row = store._conn.execute("SELECT concat FROM token_bonds LIMIT 1").fetchone()
        ribbon = str(row[0])
        model = GeometricTransformer(
            ProductionTransformerConfig(register_ports_on_init=False),
            shell=shell,
        )
        first = model.forward(ribbon)
        assert first.speedlight_hit is False
        second = model.forward(ribbon)
        assert second.speedlight_hit is True
        assert first.cache_key == second.cache_key
    finally:
        store.close()


def test_cache_bust_after_substrate_mutation(production_db):
    store = TokenIndexStore(str(production_db))
    shell = MorphonShell(ShellConfig(), store)
    try:
        row = store._conn.execute("SELECT concat FROM token_bonds LIMIT 1").fetchone()
        ribbon = str(row[0])
        model = GeometricTransformer(
            ProductionTransformerConfig(register_ports_on_init=False),
            shell=shell,
        )
        first = model.forward(ribbon)
        second = model.forward(ribbon)
        assert second.speedlight_hit is True
        epoch_before = store.substrate_epoch()

        concat = "zzzzzzzz"
        canonical = NLAECNFChain.full_chain(concat)
        morphon = Morphon.forge(payload={"concat": concat})
        payload = IndexEntryPayload(
            concat=concat,
            morphon_id=morphon.id,
            snap_key=str(canonical["snap_key"]),
            e8_coords=(0.0,) * 8,
            digital_root=int(canonical["digital_root"]),
            lane=str(canonical["lane"]),
            cache_key=f"test::{concat}",
            level=1,
            case_mode="lower",
            language="any",
            warmstart_outcome="cold",
        )
        store.upsert(payload, bond_level=1, case_mode="lower", language="any")
        epoch_after = store.substrate_epoch()
        assert epoch_before != epoch_after

        third = model.forward(ribbon)
        assert third.speedlight_hit is False
        assert third.cache_key != second.cache_key
    finally:
        store.close()


def test_shell_violation_when_shell_bind_rejects(production_db):
    from unittest.mock import MagicMock

    from cmplx.transform.shell import AdmitResult

    store = TokenIndexStore(str(production_db))
    shell = MorphonShell(ShellConfig(), store)
    shell.admit = MagicMock(
        return_value=AdmitResult(False, "badtoken", reason="test_reject")
    )
    model = GeometricTransformer(
        ProductionTransformerConfig(register_ports_on_init=False),
        shell=shell,
    )
    try:
        with pytest.raises(ShellViolation) as exc_info:
            model.forward("badtoken")
        assert exc_info.value.reason == "test_reject"
    finally:
        store.close()
