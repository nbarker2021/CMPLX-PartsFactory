"""
Actually USE each underlying tool, watch what it produces.

  1. ALENA              — r_theta_snap on a vector, see Fibonacci-radius snap
  2. SpeedLight         — idempotent compute: f(f(x)) == f(x), prove it
  3. NSL                — delta_phi, potential, gate decision on a transition
  4. NSL sectors        — 8-D → 24-D Leech embedding
  5. SNAP labeler       — exhaustive rule-based label of a code string
  6. MORSR sonar scan   — 240-direction ping from a coordinate
  7. TarPit derive      — run an actual ETP program through the symbolic runtime
  8. Receipt mint       — mint a real receipt with payload + chain
"""
from __future__ import annotations

import json
import sys

from cmplx.geometry.alena.ops import ALENA
from cmplx.morphon import Morphon
from cmplx.morsr.sonar import SonarScan
from cmplx.nsl.gate import GateMode, gate
from cmplx.nsl.phi import delta_phi, potential, shannon_bound, landauer_cost
from cmplx.nsl.sectors import NSLSectors, NSLTriads
from cmplx.receipt.provider import ReceiptProvider
from cmplx.snap.labeler import SNAPLabeler
from cmplx.speedlight.cache import SpeedLight
from cmplx.symbolic.tarpit.provider import TarPitSymbolicProvider


# ───────────────────────────────────────────────────────────────────────────
# 1. ALENA — snap a vector to the Fibonacci-radius E8 lattice
# ───────────────────────────────────────────────────────────────────────────

def demo_alena() -> dict:
    alena = ALENA()
    v = (0.5, 0.5, 0.3, -0.2, 0.0, 0.0, 0.0, 0.0)
    snapped = alena.r_theta_snap(v)
    return {
        "input_vector":  list(v),
        "snapped_to":    [round(x, 4) for x in snapped],
        "fib_radii_top": [round(r, 4) for r in alena._fib_radii[-5:]],
        "fib_radii_bot": [round(r, 4) for r in alena._fib_radii[:5]],
    }


# ───────────────────────────────────────────────────────────────────────────
# 2. SpeedLight — idempotent computation
# ───────────────────────────────────────────────────────────────────────────

def demo_speedlight() -> dict:
    cache = SpeedLight()
    call_count = {"n": 0}

    def expensive() -> int:
        call_count["n"] += 1
        return 11 * 11 + 7

    address = "demo.alpha.calc.cell.A.42"
    val1, cost1, receipt1 = cache.compute(address, expensive)
    val2, cost2, receipt2 = cache.compute(address, expensive)
    val3, cost3, receipt3 = cache.compute(address, expensive)

    return {
        "address":             address,
        "first_value":         val1,
        "first_cost_seconds":  round(cost1, 9),
        "second_value":        val2,
        "second_cost_seconds": round(cost2, 9),
        "third_value":         val3,
        "third_cost_seconds":  round(cost3, 9),
        "receipt_id":          receipt1.receipt_id,
        "same_receipt_each_call": (receipt1.receipt_id == receipt2.receipt_id == receipt3.receipt_id),
        "underlying_fn_calls": call_count["n"],
        "idempotent":          (val1 == val2 == val3) and call_count["n"] == 1,
    }


# ───────────────────────────────────────────────────────────────────────────
# 3. NSL — delta_phi, potential, gate decision
# ───────────────────────────────────────────────────────────────────────────

def demo_nsl_basics() -> dict:
    # Move a morphon from one geometric position to a nearby one.
    v_before = (0.6, 0.3, 0.1, -0.2, 0.4, 0.0, 0.0, 0.0)
    v_after  = (0.5, 0.4, 0.1, -0.2, 0.3, 0.0, 0.0, 0.0)

    p_before = potential(v_before)
    p_after  = potential(v_after)
    phi      = delta_phi(v_before, v_after)
    h_before = shannon_bound(v_before)
    h_after  = shannon_bound(v_after)
    e_cost   = landauer_cost(phi)

    sectors = NSLSectors(
        dN=phi * 0.4,
        dI=phi * 0.3,
        dL=phi * 0.3,
    )
    g_govern   = gate(sectors, mode=GateMode.GOVERN)
    g_amortize = gate(sectors, mode=GateMode.AMORTIZE, budget=1.0)
    g_signal   = gate(sectors, mode=GateMode.SIGNAL)

    return {
        "v_before":          list(v_before),
        "v_after":           list(v_after),
        "potential_before":  round(p_before, 6),
        "potential_after":   round(p_after, 6),
        "delta_phi":         round(phi, 6),
        "shannon_bound_before": round(h_before, 6),
        "shannon_bound_after":  round(h_after, 6),
        "landauer_cost_joules": e_cost,
        "sectors":              {"dN": sectors.dN, "dI": sectors.dI, "dL": sectors.dL, "total": sectors.total},
        "sectors_conserved":    sectors.is_conserved(),
        "gate_govern":   {"accepted": g_govern.accepted,   "reason": g_govern.reason},
        "gate_amortize": {"accepted": g_amortize.accepted, "reason": g_amortize.reason,
                          "remaining_budget": g_amortize.remaining_budget},
        "gate_signal":   {"accepted": g_signal.accepted,   "reason": g_signal.reason},
    }


# ───────────────────────────────────────────────────────────────────────────
# 4. NSL sectors — 8-D → 24-D Leech embedding
# ───────────────────────────────────────────────────────────────────────────

def demo_nsl_sectors() -> dict:
    # Build the 24-D Leech embedding by laying the 8-D E8 vector into
    # each of the three sector triads. Then score a witness E8 vector
    # against the triads to recover its (dN, dI, dL) summary.
    e8 = (0.6, 0.3, 0.1, -0.2, 0.4, 0.0, 0.0, 0.0)
    triads = NSLTriads(
        noether=list(e8),
        shannon=[x * 0.5 for x in e8],
        landauer=[x * -0.3 for x in e8],
    )
    leech24 = triads.as_leech_vector
    witness = (0.5, 0.4, 0.1, -0.2, 0.3, 0.0, 0.0, 0.0)
    score = triads.score(witness)
    return {
        "noether_triad":  [round(x, 4) for x in triads.noether],
        "shannon_triad":  [round(x, 4) for x in triads.shannon],
        "landauer_triad": [round(x, 4) for x in triads.landauer],
        "leech_24d":      [round(x, 4) for x in leech24],
        "leech_dim":      len(leech24),
        "witness_score":  {"dN": round(score.dN, 6), "dI": round(score.dI, 6), "dL": round(score.dL, 6)},
    }


# ───────────────────────────────────────────────────────────────────────────
# 5. SNAP labeler — exhaustive rule-based labels
# ───────────────────────────────────────────────────────────────────────────

def demo_snap_labeler() -> dict:
    labeler = SNAPLabeler()

    code_sample = """
    class MorphonForge:
        '''Builds morphons on the E8 lattice using Weyl reflection.'''
        def forge(self, payload: dict) -> 'Morphon':
            # uses delta_phi conservation
            return Morphon(payload=payload)
    """

    label_code = labeler.label(code_sample, key="MorphonForge")

    plain_text = "The repo-kernel routes requests through the GitNexus bridge."
    label_text = labeler.label(plain_text, key="kernel_routes")

    return {
        "code": {
            "key":        label_code.item_key,
            "structural": sorted(label_code.structural),
            "domain":     sorted(label_code.domain),
            "quality":    sorted(label_code.quality),
            "risk":       sorted(label_code.risk),
        },
        "text": {
            "key":        label_text.item_key,
            "structural": sorted(label_text.structural),
            "domain":     sorted(label_text.domain),
        },
        "rules_registered": labeler.rule_count,
    }


# ───────────────────────────────────────────────────────────────────────────
# 6. MORSR sonar — 240-direction ping
# ───────────────────────────────────────────────────────────────────────────

def demo_sonar_scan() -> dict:
    scanner = SonarScan()
    # Register a small set of atoms so the ping has something to hit.
    scanner.register_atoms_batch([
        {"atom_id": "north",  "e8_coords": (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), "labels": ["axis_x"]},
        {"atom_id": "east",   "e8_coords": (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), "labels": ["axis_y"]},
        {"atom_id": "diag1",  "e8_coords": (0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), "labels": ["diag"]},
        {"atom_id": "diag2",  "e8_coords": (0.7, 0.0, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0)},
        {"atom_id": "off",    "e8_coords": (0.0, 0.0, 0.0, 0.0, 0.6, -0.6, 0.0, 0.0)},
        {"atom_id": "far",    "e8_coords": (5.0, 5.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0)},
    ])
    result = scanner.ping(source=(0.0,) * 8, radius=1.5)
    return {
        "source":              [0.0] * 8,
        "radius":              1.5,
        "registered_atoms":    scanner.atom_count,
        "directions_total":    result.directions_total,
        "hit_count":           result.hit_count,
        "depth_score":         round(result.depth_score, 4),
        "shell":               result.shell,
        "hits_first_5":        dict(list(result.hits_by_direction.items())[:5]),
        "coverage_by_category": result.coverage_by_category(),
        "shadow_actions_top_3": [
            {"category": a.category, "dim": a.dimension, "unhit": a.unhit_count, "suggestion": a.suggestion}
            for a in result.shadow_actions[:3]
        ],
    }


# ───────────────────────────────────────────────────────────────────────────
# 7. TarPit — run an actual ETP program through the symbolic runtime
# ───────────────────────────────────────────────────────────────────────────

def demo_tarpit_derive() -> dict:
    provider = TarPitSymbolicProvider()

    morphon = Morphon.forge(
        payload={"name": "test_seed", "concat": "wallread", "lane": "transformative"}
    )

    # encode_to_etp: morphon → ETP program (a string of }<>+01 symbols)
    program = provider.encode_to_etp(morphon)

    # derive: run the program, get a structured report
    report = provider.derive(morphon)

    # And straight run_program with the encoded form
    direct = provider.run_program(program, max_steps=100)

    return {
        "morphon_id":         morphon.id,
        "etp_program":        program,
        "etp_program_length": len(program),
        "derive_report_keys": sorted(report.keys()) if isinstance(report, dict) else type(report).__name__,
        "derive_report_excerpt": (
            {k: report[k] for k in list(report.keys())[:6]}
            if isinstance(report, dict) else str(report)[:200]
        ),
        "run_program_keys": sorted(direct.keys()) if isinstance(direct, dict) else type(direct).__name__,
    }


# ───────────────────────────────────────────────────────────────────────────
# 8. Receipt — mint a real receipt with chain head
# ───────────────────────────────────────────────────────────────────────────

def demo_receipt() -> dict:
    receiver = ReceiptProvider()
    r1 = receiver.mint(
        receipt_type="PROCESS",
        atom_id="demo_atom_001",
        operation="see_tools_in_action.run",
        payload={"phase": "demo", "step": 1},
    )
    r2 = receiver.mint(
        receipt_type="GATE",
        atom_id="demo_atom_001",
        operation="see_tools_in_action.verify",
        delta_phi=-0.02,
        snap_labels=["demo", "verified"],
        payload={"phase": "demo", "step": 2, "result": "ok"},
        parent_hash=r1.receipt_hash,
    )
    chain_size = len(receiver.chain)
    return {
        "chain_length": chain_size,
        "receipt_1": {
            "type":      r1.receipt_type,
            "id":        r1.receipt_id,
            "atom_id":   r1.atom_id,
            "operation": r1.operation,
            "hash":      r1.receipt_hash,
        },
        "receipt_2": {
            "type":      r2.receipt_type,
            "id":        r2.receipt_id,
            "operation": r2.operation,
            "delta_phi": r2.delta_phi,
            "snap_labels": r2.snap_labels,
            "hash":      r2.receipt_hash,
            "prev_hash": r2.prev_hash,
            "chains_to_r1": r2.prev_hash == r1.receipt_hash,
        },
    }


# ───────────────────────────────────────────────────────────────────────────
# main
# ───────────────────────────────────────────────────────────────────────────

DEMOS = {
    "alena":        demo_alena,
    "speedlight":   demo_speedlight,
    "nsl_basics":   demo_nsl_basics,
    "nsl_sectors":  demo_nsl_sectors,
    "snap_labeler": demo_snap_labeler,
    "sonar":        demo_sonar_scan,
    "tarpit":       demo_tarpit_derive,
    "receipt":      demo_receipt,
}


def main() -> None:
    output: dict = {}
    for name, fn in DEMOS.items():
        try:
            output[name] = fn()
        except Exception as exc:
            output[name] = {"error": f"{type(exc).__name__}: {exc}"}
    json.dump(output, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
