import importlib.util
from pathlib import Path


def load_bundle_module():
    script = Path(__file__).resolve().parents[1] / "scripts" / "registered_systems_bundle.py"
    spec = importlib.util.spec_from_file_location("registered_systems_bundle", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_selects_two_oldest_non_yard_non_scout_repos():
    bundle = load_bundle_module()
    manifest = bundle.load_manifest(Path("repo_kernel/manifest/repos.json"))
    modules = bundle.select_modules(
        manifest,
        names=None,
        count=2,
        excludes={"CMPLX-PartsFactory", "scout-demo-service"},
    )
    assert [module["name"] for module in modules] == ["CMPLX-Formalization", "CMPLXMCP"]


def test_default_selection_wraps_all_registered_non_yard_non_scout_repos():
    bundle = load_bundle_module()
    manifest = bundle.load_manifest(Path("repo_kernel/manifest/repos.json"))
    modules = bundle.select_modules(
        manifest,
        names=None,
        count=None,
        excludes={"CMPLX-PartsFactory", "scout-demo-service"},
    )
    names = [module["name"] for module in modules]
    assert names == [
        "CMPLX-Formalization",
        "CMPLXMCP",
        "CMPLXUNI",
        "CMPLX-Monorepo",
        "CMPLX",
        "CMPLXDevKit",
        "CMPLX-1T",
        "CMPLX-TMN1",
        "CMPLX-TMN-main",
        "CMPLX-Manny",
    ]
    assert "CMPLX-PartsFactory" not in names
    assert "scout-demo-service" not in names


def test_describe_preserves_per_repo_roots():
    bundle = load_bundle_module()
    manifest = bundle.load_manifest(Path("repo_kernel/manifest/repos.json"))
    modules = bundle.select_modules(
        manifest,
        names=["CMPLX-Formalization", "CMPLXMCP"],
        count=2,
        excludes=set(),
    )
    description = bundle.describe(modules)
    roots = {module["name"]: module["cwd"] for module in description["modules"]}
    assert roots["CMPLX-Formalization"].endswith("repo_kernel\\repos\\CMPLX-Formalization") or roots[
        "CMPLX-Formalization"
    ].endswith("repo_kernel/repos/CMPLX-Formalization")
    assert roots["CMPLXMCP"].endswith("repo_kernel\\repos\\CMPLXMCP") or roots["CMPLXMCP"].endswith(
        "repo_kernel/repos/CMPLXMCP"
    )
