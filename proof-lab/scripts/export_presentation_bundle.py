"""Zip latest proof-lab bundle for presentation handoff."""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LATEST = ROOT / "proof-lab" / "artifacts" / "latest"
OUT = ROOT / "proof-lab" / "artifacts" / "presentation_export.zip"


def main() -> None:
    if not LATEST.exists():
        raise SystemExit("No proof-lab/artifacts/latest — run `make formal-bundle` or POST /api/formal/run")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.is_file():
        OUT.unlink()
    shutil.make_archive(str(OUT.with_suffix("")), "zip", LATEST)
    print(f"Wrote {OUT.with_suffix('.zip')}")


if __name__ == "__main__":
    main()
