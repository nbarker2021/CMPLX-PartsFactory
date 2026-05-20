"""Tests for rule library loader."""
from __future__ import annotations

from pathlib import Path

import pytest

from cmplx.transform.rule_lib import RuleLibraryLoader


ROOT = Path(__file__).resolve().parents[2] / "data" / "rule_libs"


def test_lib_list_finds_yaml_files():
    loader = RuleLibraryLoader(ROOT)
    libs = loader.list_libraries()
    assert any("english_bigrams.yaml" in p for p in libs)


def test_merge_loads_language_and_shell():
    loader = RuleLibraryLoader(ROOT)
    bundle = loader.merge(ROOT)
    assert "english" in bundle.language_filters or "identity_review" in bundle.language_filters
    assert bundle.shell_config is not None
    assert bundle.shell_config.max_arity == 8


def test_validate_passes_default_tree():
    loader = RuleLibraryLoader(ROOT)
    errors = loader.validate(ROOT)
    assert errors == []


def test_validate_reports_missing_file(tmp_path):
    loader = RuleLibraryLoader(tmp_path)
    missing = tmp_path / "nope.yaml"
    errors = loader.validate(missing)
    assert any("missing" in e for e in errors)
