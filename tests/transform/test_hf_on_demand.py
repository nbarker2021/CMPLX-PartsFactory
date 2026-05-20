"""HF on-demand lane — default off, wake only when enabled."""
from __future__ import annotations

import os

import pytest

from cmplx.transform.torch.hf_on_demand import (
    HFOnDemandLane,
    hf_lane_enabled,
    hf_lane_from_env,
    hf_lane_train,
    try_layer_hf_fallback,
)
from cmplx.transform.torch.train_window import (
    TrainWindowConfig,
    run_train_window,
    train_window_from_env,
)


def test_hf_lane_default_off(monkeypatch):
    monkeypatch.delenv("CMPLX_HF_LANE", raising=False)
    assert hf_lane_from_env() == "off"
    assert hf_lane_enabled() is False
    lane = HFOnDemandLane()
    result = lane.wake()
    assert result.woke is False


def test_hf_lane_on_demand_wake_once(monkeypatch):
    monkeypatch.setenv("CMPLX_HF_LANE", "on_demand")
    lane = HFOnDemandLane()
    r1 = lane.wake()
    r2 = lane.wake()
    assert r1.woke is True
    assert r2.woke is True
    assert lane.wake_count == 2


def test_try_layer_hf_fallback_when_nsl_rejects(monkeypatch):
    monkeypatch.setenv("CMPLX_HF_LANE", "on_demand")
    result = try_layer_hf_fallback(
        layer_idx=2,
        nsl_accepted=False,
        use_hf_fallback=True,
    )
    assert result is not None
    assert result.woke is True


def test_hf_lane_train_does_not_enable_on_demand_wake(monkeypatch):
    monkeypatch.setenv("CMPLX_HF_LANE", "train")
    assert hf_lane_from_env() == "train"
    assert hf_lane_train() is True
    assert hf_lane_enabled() is False
    lane = HFOnDemandLane()
    assert lane.wake().woke is False


def test_train_window_off_by_default(monkeypatch):
    monkeypatch.delenv("CMPLX_HF_LANE", raising=False)
    monkeypatch.delenv("CMPLX_TRAIN_WINDOW", raising=False)
    assert train_window_from_env() is False
    result = run_train_window(
        TrainWindowConfig(crystal_bundle=__import__("pathlib").Path(".")),
    )
    assert result.ran is False
    assert result.reason == "train_window_off"


def test_train_window_stub_with_train_lane(tmp_path, monkeypatch):
    monkeypatch.setenv("CMPLX_HF_LANE", "train")
    from cmplx.transform.crystal_pack import CrystalPackager
    from cmplx.transform.token_index import (
        CaseMode,
        TokenIndexBuildConfig,
        TokenIndexBuilder,
        any_filter,
    )

    db = tmp_path / "tw.sqlite"
    bundle = tmp_path / "tw.crystal"
    lib = tmp_path / "libs"
    lib.mkdir()
    (lib / "token").mkdir()
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=(1,),
            alphabet=tuple("ab"),
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=str(db),
            progress_every=0,
            max_entries=10,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    CrystalPackager().pack("tw", db=str(db), libs=str(lib), out=str(bundle))
    row = __import__("sqlite3").connect(str(db)).execute(
        "SELECT concat FROM token_bonds LIMIT 1"
    ).fetchone()
    cfg = TrainWindowConfig(
        crystal_bundle=bundle,
        tokens=[str(row[0])],
        max_steps=2,
        wall_clock_budget_sec=30.0,
    )
    result = run_train_window(cfg)
    assert result.ran is True
    assert result.steps_completed == 2
    assert len(result.steps) == 2


def test_trainer_harness_sketch_admit_mask(tmp_path):
    from cmplx.transform.crystal_pack import CrystalPackager
    from cmplx.transform.torch.hf_adapter import TrainerHarnessSketch
    from cmplx.transform.token_index import (
        CaseMode,
        TokenIndexBuildConfig,
        TokenIndexBuilder,
        any_filter,
    )

    db = tmp_path / "t.sqlite"
    bundle = tmp_path / "t.crystal"
    lib = tmp_path / "libs"
    lib.mkdir()
    (lib / "token").mkdir()
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=(1,),
            alphabet=tuple("ab"),
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=str(db),
            progress_every=0,
            max_entries=10,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    CrystalPackager().pack("harness", db=str(db), libs=str(lib), out=str(bundle))
    row = __import__("sqlite3").connect(str(db)).execute(
        "SELECT concat FROM token_bonds LIMIT 1"
    ).fetchone()
    tokens = [str(row[0])]
    harness = TrainerHarnessSketch(crystal_bundle=bundle, tokens=tokens)
    step = harness.stub_train_step()
    assert step["batch_size"] == 1
    assert "crystal_id" in step


def test_train_window_hf_phase_b_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("CMPLX_HF_LANE", "train")
    monkeypatch.setenv("CMPLX_HF_MODEL", "stub/test-model")
    from cmplx.transform.crystal_pack import CrystalPackager
    from cmplx.transform.token_index import (
        CaseMode,
        TokenIndexBuildConfig,
        TokenIndexBuilder,
        any_filter,
    )

    db = tmp_path / "hf.sqlite"
    bundle = tmp_path / "hf.crystal"
    lib = tmp_path / "libs"
    lib.mkdir()
    (lib / "token").mkdir()
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=(1,),
            alphabet=tuple("ab"),
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=str(db),
            progress_every=0,
            max_entries=10,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    CrystalPackager().pack("hf", db=str(db), libs=str(lib), out=str(bundle))
    row = __import__("sqlite3").connect(str(db)).execute(
        "SELECT concat FROM token_bonds LIMIT 1"
    ).fetchone()
    cfg = TrainWindowConfig(
        crystal_bundle=bundle,
        tokens=[str(row[0])],
        max_steps=1,
        report_dir=tmp_path / "reports",
    )
    result = run_train_window(cfg)
    assert result.ran is True
    assert result.steps[0].get("hf_step", {}).get("model") == "stub/test-model"
    assert result.report_path
