import importlib.util
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(scope="session")
def server():
    root = ROOT
    os.environ["REPO_KERNEL_MANIFEST"] = str(root / "repo_kernel/manifest/repos.json")
    os.environ["REPO_KERNEL_REPOS"] = str(root / "repo_kernel/repos")
    os.environ["REPO_KERNEL_PROMOTION_LEDGER"] = str(root / "reports/repo_promotion_ledger_2026-05-13.json")
    os.environ["REPO_KERNEL_SELF_STATE"] = str(root / "repo_kernel/state/self_state.sqlite")
    script = root / "services" / "repo-kernel" / "server.py"
    spec = importlib.util.spec_from_file_location("repo_kernel_server", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
