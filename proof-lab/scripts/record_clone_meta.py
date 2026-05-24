"""Write git HEAD / branch / dirty flag for proof-lab accounting."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
META = ROOT / "proof-lab" / "artifacts" / "meta" / "last_clone.json"


def _run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()


def main() -> None:
    META.parent.mkdir(parents=True, exist_ok=True)
    dirty = bool(subprocess.call(["git", "diff", "--quiet"], cwd=ROOT))
    payload = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "head": _run("git", "rev-parse", "HEAD"),
        "branch": _run("git", "rev-parse", "--abbrev-ref", "HEAD"),
        "describe": _run("git", "describe", "--tags", "--always", "--dirty"),
        "dirty": dirty,
        "remote": _run("git", "remote", "get-url", "origin") if Path(ROOT / ".git").exists() else None,
    }
    META.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[proof-lab] wrote {META}")


if __name__ == "__main__":
    main()
