from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lattice_forge import Forge


def run_smoke() -> int:
    root = Path(tempfile.mkdtemp(prefix="lattice-forge-smoke-"))
    forge = Forge.open(root)
    status = forge.status()
    if status["seed_integrity"] != "ok":
        print("SMOKE_FAIL seed integrity")
        return 1
    close = forge.can_close("G2", "A2^12")
    if close["answer"] != "yes_with_template_glue":
        print("SMOKE_FAIL closure")
        return 2
    tree = forge.terminal_tree("A2^12")
    if tree["result"]["closure_residue"]["status"] != "residue_closes_by_required_index":
        print("SMOKE_FAIL terminal tree")
        return 3
    verify_trees = forge.verify_terminal_trees()
    if verify_trees["result"]["status"] != "pass" or verify_trees["result"]["terminal_count"] != 24:
        print("SMOKE_FAIL terminal tree verification")
        return 4
    verify_morphonics = forge.verify_morphonics()
    if not verify_morphonics["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL morphonics verification")
        return 5
    verify_rule30 = forge.verify_rule30(max_depth=5)
    if not verify_rule30["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 verification")
        return 6
    verify_vignettes = forge.verify_rule30_vignettes(max_order=4)
    if not verify_vignettes["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 vignette verification")
        return 7
    verify_moving = forge.verify_rule30_moving_frame(max_depth=8, max_order=4)
    if not verify_moving["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 moving-frame verification")
        return 8
    verify_chiral = forge.verify_rule30_color_chirality(max_depth=8, max_order=4)
    if not verify_chiral["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 color/chirality verification")
        return 9
    verify_lagrangian = forge.verify_rule30_lagrangian(max_depth=8, max_order=4)
    if not verify_lagrangian["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 lagrangian verification")
        return 10
    verify_trace = forge.verify_rule30_lagrangian_depth_trace(max_depth=64, max_order=4)
    if not verify_trace["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 lagrangian trace verification")
        return 11
    verify_scalar = forge.verify_rule30_mandelbrot_scalar(max_depth=64, max_order=4)
    if not verify_scalar["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 mandelbrot scalar verification")
        return 12
    verify_reduced = forge.verify_rule30_reduced_alphabet(max_depth=128, max_order=4)
    if not verify_reduced["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 reduced alphabet verification")
        return 13
    verify_symmetry = forge.verify_rule30_symmetry_environment(max_depth=128, max_period=32, max_order=4)
    if not verify_symmetry["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 symmetry environment verification")
        return 14
    verify_stack = forge.verify_rule30_physics_method_stack(max_depth=128, max_period=32, max_order=4, max_block=6)
    if not verify_stack["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 physics stack verification")
        return 15
    verify_coverage = forge.verify_rule30_whole_integer_n_coverage(max_depth=1024, max_order=4)
    if not verify_coverage["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 whole-integer N coverage verification")
        return 16
    verify_ribbon = forge.verify_rule30_readout_ribbon_machine(max_depth=1024, max_order=4)
    if not verify_ribbon["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 readout ribbon verification")
        return 17
    verify_hypervisor = forge.verify_rule30_dihedral_block_hypervisor(max_depth=512, block_size=8, max_order=4)
    if not verify_hypervisor["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 dihedral hypervisor verification")
        return 18
    verify_extension = forge.verify_rule30_hypervisor_extension_tape(page_count=2, page_size=512, block_size=8, max_order=4)
    if not verify_extension["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 hypervisor extension tape verification")
        return 19
    verify_sheet = forge.verify_rule30_sheet_operator(page_count=2, page_size=128, block_size=8, max_order=4)
    if not verify_sheet["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 sheet operator verification")
        return 20
    verify_nth = forge.verify_rule30_nth_bit_expression(129, page_size=128, block_size=8, max_order=4)
    if not verify_nth["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 nth-bit expression verification")
        return 21
    verify_proof = forge.verify_rule30_proof_obligations(
        max_depth=128,
        page_count=2,
        page_size=128,
        block_size=8,
        max_order=4,
    )
    if not verify_proof["result"]["status"].startswith("pass"):
        print("SMOKE_FAIL rule30 proof-obligation ledger verification")
        return 22
    if not forge.latest_receipts(1):
        print("SMOKE_FAIL receipts")
        return 23
    print("SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_smoke())
