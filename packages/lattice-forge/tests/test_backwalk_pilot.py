from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_PKG_ROOT = Path(__file__).resolve().parents[1]
_SRC = _PKG_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lattice_forge.backwalk import (  # noqa: E402
    PILOT_TERMINAL_IDS,
    WorkStore,
    glue_project_weyl,
    hydrate,
    materialize_exceptional_spine,
    materialize_terminals,
)
from lattice_forge.seed import SeedStore  # noqa: E402
from lattice_forge.substrate_map import WEYL_13_TABLE  # noqa: E402

_PILOT_FAST = ("Niemeier:Leech", "Niemeier:D4^6")
_EXPECTED_STATES = {
    "Niemeier:Leech": 1,
    "Niemeier:D4^6": 7,
    "Niemeier:A2^12": 13,
    "Niemeier:A1^24": 25,
}


@pytest.fixture
def work_db(tmp_path: Path) -> Path:
    return tmp_path / "backwalk_work.db"


def test_pilot_leech_and_d4_states(work_db: Path) -> None:
    seed_before = SeedStore.packaged().verify()
    with WorkStore(work_db) as store:
        store.start_run("test-run", "pilot", {"terminals": list(_PILOT_FAST)})
        stats = materialize_terminals(store, list(_PILOT_FAST))
        ex = materialize_exceptional_spine(store, include={"g2", "f4"})
        assert ex["g2_f4_path"] is True

    seed_after = SeedStore.packaged().verify()
    assert seed_before == seed_after

    by_id = {s.terminal_id: s for s in stats}
    for tid in _PILOT_FAST:
        assert by_id[tid].state_count == _EXPECTED_STATES[tid]
        assert by_id[tid].peel_morphism_count == by_id[tid].state_count - 1

    leech = hydrate(work_db, "Niemeier:Leech")
    assert len(leech["objects"]) == 1
    assert leech["objects"][0]["evidence_level"] in ("exact", "template")

    d4 = hydrate(work_db, "Niemeier:D4^6")
    peel = [m for m in d4["morphisms"] if m["morphism_kind"] == "remove_component"]
    assert len(peel) == 6


def test_glue_weyl_bounded_exec(work_db: Path) -> None:
    chart_state = 3
    partner = WEYL_13_TABLE[chart_state]
    with WorkStore(work_db) as store:
        store.start_run("glue-test", "pilot", {})
        materialize_terminals(store, ["Niemeier:Leech"])
        result = glue_project_weyl(
            store,
            {
                "chart_state": chart_state,
                "source_state_id": f"chart:{chart_state}",
                "target_state_id": f"chart:{partner}",
            },
            "Niemeier:Leech",
        )
    assert result["evidence_level"] == "bounded_exec"
    assert result["weyl_partner"] == partner


def test_cli_pilot_four_terminals(tmp_path: Path) -> None:
    script = _PKG_ROOT / "scripts" / "run_niemeier_backwalk.py"
    work_db = tmp_path / "backwalk_work.db"
    baseline = tmp_path / "baseline_report.json"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(_SRC) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["BACKWALK_EXCEPTIONALS"] = "g2,f4,e6"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--phase",
            "pilot",
            "--work-db",
            str(work_db),
            "--baseline-report",
            str(baseline),
            "--include-exceptionals",
            "g2,f4,e6",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(baseline.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert len(report["terminals"]) == len(PILOT_TERMINAL_IDS)
    for row in report["terminals"]:
        assert row["state_count"] == _EXPECTED_STATES[row["terminal_id"]]


@pytest.mark.skipif(
    os.environ.get("BACKWALK_DOCKER_SMOKE") != "1",
    reason="Set BACKWALK_DOCKER_SMOKE=1 to run Docker batch smoke",
)
def test_docker_backwalk_smoke() -> None:
    repo = _PKG_ROOT.parents[2]
    compose = repo / "docker-compose.backwalk-builder.yml"
    proc = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(compose),
            "run",
            "--rm",
            "-e",
            "BACKWALK_PHASE=pilot",
            "-e",
            "BACKWALK_EXCEPTIONALS=g2,f4",
            "niemeier-backwalk-builder",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
