"""HF adapter stub — admit mask export and production config."""
from __future__ import annotations

import pytest

from cmplx.transform.config import ProductionTransformerConfig, TransformerConfig
from cmplx.transform.shell import MorphonShell
from cmplx.transform.shell_config import ShellConfig
from cmplx.transform.token_index import (
    CaseMode,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    TokenIndexStore,
    any_filter,
)
from cmplx.transform.torch.hf_adapter import HFAdapterConfig, HuggingFaceAdapterStub


@pytest.fixture
def indexed_db(tmp_path):
    db = str(tmp_path / "token_index.sqlite")
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=(1, 2),
            alphabet=tuple("abcde"),
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=db,
            progress_every=0,
            max_entries=120,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    return db


def test_production_transformer_config_builds():
    cfg = ProductionTransformerConfig(register_ports_on_init=False)
    assert cfg.use_n_ladder is True
    assert cfg.shell_bind is True
    assert cfg.num_layers >= 7


def test_export_admit_mask_matches_shell(indexed_db: str):
    store = TokenIndexStore(indexed_db)
    shell = MorphonShell(ShellConfig(), store)
    try:
        row = store._conn.execute(
            "SELECT concat FROM token_bonds LIMIT 3"
        ).fetchall()
        tokens = [str(r[0]) for r in row]
        expected = [shell.admit(t).admitted for t in tokens]
    finally:
        store.close()

    adapter = HuggingFaceAdapterStub(
        TransformerConfig(num_layers=1, register_ports_on_init=False),
        shell=MorphonShell(ShellConfig(), TokenIndexStore(indexed_db)),
    )
    mask = adapter.export_admit_mask(tokens)
    assert mask == expected


def test_hf_adapter_production_preset(indexed_db: str):
    store = TokenIndexStore(indexed_db)
    shell = MorphonShell(ShellConfig(), store)
    adapter = HuggingFaceAdapterStub(
        hf_config=HFAdapterConfig(production=True, num_layers=8),
        shell=shell,
    )
    assert adapter.transformer.config.use_n_ladder is True
    out = adapter.forward("abcdeabc")
    assert "cache_key" in out
    store.close()
