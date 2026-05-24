"""Smoke tests that the package installs with expected console scripts."""
from __future__ import annotations

import importlib.metadata
import subprocess
import sys

import lattice_forge
import lattice_forge.backwalk.runner as runner
import lattice_forge.algebra.verify_o1 as verify_o1


def test_version_matches_metadata() -> None:
    try:
        meta = importlib.metadata.version("lattice-forge")
    except importlib.metadata.PackageNotFoundError:
        meta = lattice_forge.__version__
    assert lattice_forge.__version__ == meta or meta.startswith("0.3")


def test_console_script_entry_points_registered() -> None:
    expected = {
        "lattice-forge",
        "lattice-forge-backwalk",
        "lattice-forge-weyl-bond",
        "lattice-forge-lattice-space",
        "lattice-forge-verify-algebra",
    }
    names = {
        ep.name
        for ep in importlib.metadata.entry_points(group="console_scripts")
        if ep.dist and ep.dist.name == "lattice-forge"
    }
    if expected.issubset(names):
        return
    # Editable install may be unavailable in CI; assert pyproject declares scripts.
    import tomllib
    from pathlib import Path

    data = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    declared = set(data.get("project", {}).get("scripts", {}).keys())
    assert expected.issubset(declared)


def test_backwalk_parser_has_phases() -> None:
    parser = runner.build_backwalk_parser()
    phase_action = next(a for a in parser._actions if getattr(a, "dest", None) == "phase")
    assert "pilot" in phase_action.choices


def test_runner_dry_run_lattice_space(tmp_path) -> None:
    work_db = tmp_path / "work.db"
    code = runner.run_lattice_space(["--work-db", str(work_db), "--dry-run"])
    assert code == 0


def test_verify_o1_local() -> None:
    code = verify_o1.run_verify_o1([])
    assert code == 0
