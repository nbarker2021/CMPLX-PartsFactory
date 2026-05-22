from pathlib import Path

from sample import RuntimeConfig, parse_config


def test_parse_config(tmp_path: Path):
    path = tmp_path / "config.txt"
    path.write_text("name = lattice-forge\n", encoding="utf-8")
    assert parse_config(path)["name"] == "lattice-forge"


def test_runtime_config_required():
    cfg = RuntimeConfig({"name": "lattice-forge"})
    assert cfg.get_required("name") == "lattice-forge"
