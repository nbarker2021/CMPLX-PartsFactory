"""Basic compose_pipeline integration tests."""
from __future__ import annotations

import pytest

from cmplx.transform.compose_pipeline import compose_pipeline
from cmplx.transform.config import ProductionTransformerConfig
from cmplx.transform.index_supervisor import IndexSupervisor
from cmplx.transform.shell import MorphonShell
from cmplx.transform.shell_config import ShellConfig
from cmplx.transform.token_index import (
    CaseMode,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    any_filter,
)
from cmplx.transform.token_index.store import TokenIndexStore
from cmplx.transform.transformer import GeometricTransformer


@pytest.fixture
def compose_db(tmp_path):
    db = str(tmp_path / "token_index.sqlite")
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=(1,),
            alphabet=tuple("abcde"),
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=db,
            progress_every=0,
            max_entries=80,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    return db


def test_compose_pipeline_supervisor_before_complete(compose_db):
    store = TokenIndexStore(compose_db)
    shell = MorphonShell(ShellConfig(), store)
    sup = IndexSupervisor.from_db(compose_db, run_mutations=False)
    result = compose_pipeline(shell, "baa", supervisor=sup, max_candidates=8)
    assert "steps" in result.supervisor
    assert isinstance(result.candidates, list)
    store.close()


def test_compose_partial_seed_in_supervisor_report(compose_db):
    store = TokenIndexStore(compose_db)
    shell = MorphonShell(ShellConfig(), store)
    result = compose_pipeline(shell, "baaaaaa", max_candidates=8)
    steps = result.supervisor.get("steps", [])
    template_steps = [s for s in steps if s.get("action") == "template" and s.get("pattern")]
    if template_steps:
        assert "b" in template_steps[0]["pattern"]
    store.close()


def test_production_forward_config_builds(compose_db):
    store = TokenIndexStore(compose_db)
    shell = MorphonShell(ShellConfig(), store)
    model = GeometricTransformer(
        ProductionTransformerConfig(register_ports_on_init=False),
        shell=shell,
    )
    rows = store.by_left("baaa", limit=1)
    if rows:
        token = rows[0]["concat"]
        out = model.forward(token)
        assert out.layer_traces
        modes = {t.attention.mode for t in out.layer_traces if t.attention}
        assert len(modes) >= 1
    store.close()
