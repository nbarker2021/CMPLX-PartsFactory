"""Tests for N-ladder typed layers and shell-bound forward."""
from __future__ import annotations

import pytest

from cmplx.transform.config import ProductionTransformerConfig, TransformerConfig
from cmplx.transform.n_ladder import default_n_ladder_stack, layer_configs_from_n_ladder
from cmplx.transform.shell import MorphonShell
from cmplx.transform.shell_config import ShellConfig
from cmplx.transform.token_index.store import TokenIndexStore
from cmplx.transform.transformer import GeometricTransformer
from cmplx.transform.types import ShellViolation


def test_n_ladder_eight_distinct_policies():
    stack = default_n_ladder_stack()
    assert len(stack) == 8
    layers = layer_configs_from_n_ladder()
    assert len(layers) == 8
    modes = {l.attention.mode for l in layers}
    assert len(modes) >= 2


def test_transformer_config_use_n_ladder():
    cfg = TransformerConfig(num_layers=4, use_n_ladder=True, register_ports_on_init=False)
    assert cfg.num_layers == 8
    assert len(cfg.layers) == 8


def test_production_transformer_config_preset():
    cfg = ProductionTransformerConfig(register_ports_on_init=False)
    assert cfg.use_n_ladder is True
    assert cfg.shell_bind is True
    assert cfg.num_layers == 8
    assert len(cfg.layers) == 8


def test_shell_bind_raises_when_admit_fails(tmp_path):
    from unittest.mock import MagicMock

    from cmplx.transform.shell import AdmitResult

    db = tmp_path / "t.sqlite"
    store = TokenIndexStore(db)
    shell = MorphonShell(ShellConfig(), store)
    shell.admit = MagicMock(
        return_value=AdmitResult(False, "badtoken", reason="test_reject")
    )
    model = GeometricTransformer(
        TransformerConfig(num_layers=1, shell_bind=True, register_ports_on_init=False),
        shell=shell,
    )
    with pytest.raises(ShellViolation):
        model._shell_bind_ribbon_out("badtoken", [])
    store.close()
