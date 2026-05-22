"""Small sample project for PyPP indexing."""

from pathlib import Path


def parse_config(path: str | Path) -> dict[str, str]:
    """Parse a tiny key=value config file."""
    data: dict[str, str] = {}
    text = Path(path).read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


class RuntimeConfig:
    """Example runtime config wrapper."""

    def __init__(self, values: dict[str, str]):
        self.values = values

    def get_required(self, key: str) -> str:
        if key not in self.values:
            raise KeyError(key)
        return self.values[key]
