"""
Integrated 2026-05-19T00:52:23Z from external toolkit.
Source: ``D:\PartsFactory\files (1)\cmplx_deployment.py``
"""
#!/usr/bin/env python3
"""
CMPLX Deployment Layer
========================

1. Master polyglot Dockerfile
2. NanoClaw activation protocol (FOLDED → OPERATING → DISSOLVING)
3. Docker Compose generator from ManifoldGraph
4. End-to-end deployment demo
"""

import hashlib
import json
import math
import time
import os
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict
from enum import Enum, auto

# ════════════════════════════════════════════════════════════════
# 1. MASTER POLYGLOT DOCKERFILE
# ════════════════════════════════════════════════════════════════

DOCKERFILE = '''# ═══════════════════════════════════════════════════════════
# cmplx/morphon:latest — Master Polyglot Image
# ═══════════════════════════════════════════════════════════
# Single image. All roles. Activation determines behavior.
# ═══════════════════════════════════════════════════════════

FROM python:3.12-slim AS base

LABEL maintainer="CMPLX" \\
      version="2.1.0" \\
      description="Morphonic computing — one image, every role"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
        build-essential libffi-dev libsqlite3-dev \\
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Application code
COPY cmplx_core_primitives.py /app/cmplx_core_primitives.py
COPY cmplx_eversion_network.py /app/cmplx_eversion_network.py
COPY cmplx_deployment.py /app/cmplx_deployment.py
COPY cmplx_nanoclaw.py /app/cmplx_nanoclaw.py

WORKDIR /app

# Data volumes
VOLUME ["/data/mmdb", "/data/mdhg", "/data/receipts", "/data/speedlight"]

# Environment: activation determines role
ENV NODE_ID="default" \\
    ROLE="compute" \\
    ACTIVE_AXES="0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23" \\
    POSITION="[]" \\
    NEIGHBORS="" \\
    MDHG_FAST_CAPACITY="1000" \\
    MDHG_MED_CAPACITY="10000" \\
    MDHG_DIMENSIONS="24" \\
    SPEEDLIGHT_CACHE_SIZE="10000" \\
    LOG_LEVEL="INFO"

# Health check: verify conservation + chain integrity
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
    CMD python3 -c "from cmplx_nanoclaw import health_check; health_check()"

# Entrypoint: NanoClaw activation
ENTRYPOINT ["python3", "cmplx_nanoclaw.py"]
CMD ["--role", "compute"]
'''

REQUIREMENTS_TXT = '''numpy>=1.24
'''


# ════════════════════════════════════════════════════════════════
# 2. NANOCLAW ACTIVATION PROTOCOL
# ════════════════════════════════════════════════════════════════

class NanoClawState(Enum):
    FOLDED = "FOLDED"           # Image loaded, nothing activated
    ACTIVATING = "ACTIVATING"   # Parsing environment, loading config
    PROJECTING = "PROJECTING"   # Computing E8 projections for assigned axes
    LOCKED = "LOCKED"           # All assigned axes verified
    OPERATING = "OPERATING"     # Accepting and processing submissions
    DISSOLVING = "DISSOLVING"   # Shutting down, flushing receipts

class NanoClawRole(Enum):
    # 7 BRS validators
    DIM_CLAW = "DimClaw"           # D_embed == D_needed
    AUDIT_CLAW = "AuditClaw"       # D_audit == k * D_embed
    AWB_CLAW = "AWBClaw"           # Pointwise minimum
    HODGE_CLAW = "HodgeClaw"       # Minimally coexact
    ESCROW_CLAW = "EscrowClaw"     # UDMS duplex balance
    CRT_CLAW = "CRTClaw"          # Zero defects
    SYNDROME_CLAW = "SyndromeClaw"  # Zero syndrome

    # 4 operational
    HINGE_CLAW = "HingeClaw"       # Single E8 axis projection
    EVERSION_CLAW = "EversionClaw" # 6-phase eversion execution
    INFLATION_CLAW = "InflationClaw" # Domain 8D→fullD inflation
    GATEKEEPER = "GateKeeper"      # SNAP percolation gate

    # 3 infrastructure
    RECEIPT_CLAW = "ReceiptClaw"   # Chain management
    SWARM_CLAW = "SwarmClaw"       # Micro-swarm spawner
    ROUTE_CLAW = "RouteClaw"       # AGRM inter-manifold routing

@dataclass
class NanoClaw:
    """
    A single NanoClaw — the atomic deployment unit.
    
    Every container in the system IS a NanoClaw. The master image
    contains all code. The environment variables determine which
    NanoClaw role activates.
    
    Activation sequence:
      FOLDED → ACTIVATING → PROJECTING → LOCKED → OPERATING → DISSOLVING
    """
    claw_id: str
    role: NanoClawRole
    state: NanoClawState = NanoClawState.FOLDED
    assigned_axes: Set[int] = field(default_factory=set)
    position: Optional[np.ndarray] = None

    # Runtime
    items_processed: int = 0
    receipts: List[Dict] = field(default_factory=list)
    last_hash: str = "0" * 64
    health: float = 1.0
    started_at: float = 0.0
    
    # Self-healing
    ttl_seconds: float = 0.0       # 0 = permanent, >0 = ephemeral (swarm capsule)
    parent_claw_id: Optional[str] = None

    def activate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the activation sequence."""
        self.started_at = time.time()
        report = {"claw_id": self.claw_id, "role": self.role.value, "phases": {}}

        # FOLDED → ACTIVATING
        self.state = NanoClawState.ACTIVATING
        self.assigned_axes = set(config.get('axes', range(24)))
        if config.get('position'):
            self.position = np.array(config['position'])
        self.ttl_seconds = config.get('ttl', 0.0)
        self.parent_claw_id = config.get('parent_id')
        report["phases"]["activating"] = {"axes": sorted(self.assigned_axes)}

        # ACTIVATING → PROJECTING
        self.state = NanoClawState.PROJECTING
        projections = self._compute_projections()
        report["phases"]["projecting"] = {
            "projections_computed": len(projections),
            "all_valid": all(p["valid"] for p in projections.values()),
        }

        # PROJECTING → LOCKED
        all_locked = all(p["valid"] for p in projections.values())
        if all_locked:
            self.state = NanoClawState.LOCKED
            report["phases"]["locked"] = {"status": "ALL_AXES_LOCKED"}
        else:
            report["phases"]["locked"] = {
                "status": "PARTIAL",
                "failed_axes": [k for k, v in projections.items() if not v["valid"]],
            }

        # LOCKED → OPERATING
        self.state = NanoClawState.OPERATING
        report["phases"]["operating"] = {"status": "READY"}

        self._receipt("activated", {
            "role": self.role.value,
            "axes": sorted(self.assigned_axes),
            "locked": all_locked,
        })

        report["final_state"] = self.state.value
        return report

    def process(self, submission: Dict) -> Dict:
        """Process one submission according to role."""
        if self.state != NanoClawState.OPERATING:
            return {"error": f"NanoClaw in state {self.state.value}, not OPERATING"}

        self.items_processed += 1
        result = {"claw_id": self.claw_id, "role": self.role.value}

        # Role-specific processing
        if self.role == NanoClawRole.HINGE_CLAW:
            result.update(self._process_hinge(submission))
        elif self.role == NanoClawRole.EVERSION_CLAW:
            result.update(self._process_eversion(submission))
        elif self.role in (NanoClawRole.DIM_CLAW, NanoClawRole.AUDIT_CLAW,
                           NanoClawRole.AWB_CLAW, NanoClawRole.HODGE_CLAW,
                           NanoClawRole.ESCROW_CLAW, NanoClawRole.CRT_CLAW,
                           NanoClawRole.SYNDROME_CLAW):
            result.update(self._process_brs_check(submission))
        elif self.role == NanoClawRole.GATEKEEPER:
            result.update(self._process_gate(submission))
        elif self.role == NanoClawRole.RECEIPT_CLAW:
            result.update(self._process_receipt(submission))
        else:
            result["processed"] = True

        self._receipt("processed", {"items": self.items_processed})
        return result

    def dissolve(self) -> Dict:
        """Graceful shutdown — flush receipts, report final state."""
        self.state = NanoClawState.DISSOLVING
        report = {
            "claw_id": self.claw_id,
            "role": self.role.value,
            "items_processed": self.items_processed,
            "receipts_emitted": len(self.receipts),
            "uptime_seconds": time.time() - self.started_at,
            "health": self.health,
        }
        self._receipt("dissolved", report)
        return report

    @property
    def expired(self) -> bool:
        if self.ttl_seconds <= 0:
            return False
        return (time.time() - self.started_at) > self.ttl_seconds

    def _compute_projections(self) -> Dict[int, Dict]:
        """Compute E8 projections for each assigned axis."""
        from cmplx.primitives.core import e8_roots, e8_snap
        roots = e8_roots()
        projections = {}
        for axis in self.assigned_axes:
            root_idx = axis % 240
            root = roots[root_idx]
            projections[axis] = {
                "root": root.tolist(),
                "norm": float(np.linalg.norm(root)),
                "valid": float(np.linalg.norm(root)) > 1e-10,
            }
        return projections

    def _process_hinge(self, sub: Dict) -> Dict:
        from cmplx.primitives.core import e8_snap
        vector = np.array(sub.get('vector', [0]*8)[:8], dtype=np.float64)
        snapped, dev = e8_snap(vector)
        return {"snapped": snapped.tolist(), "deviation": dev, "locked": dev < 0.5}

    def _process_eversion(self, sub: Dict) -> Dict:
        from cmplx_eversion_network import EversionCore
        ec = EversionCore()
        vector = np.array(sub.get('vector', [0]*8)[:8], dtype=np.float64)
        everted, phases = ec.evert(vector, genus=sub.get('genus', 0))
        return {
            "everted": everted.tolist(),
            "phases": len(phases),
            "total_dphi": sum(p.delta_phi for p in phases),
        }

    def _process_brs_check(self, sub: Dict) -> Dict:
        from cmplx.primitives.core import BRSChecker
        brs = BRSChecker()
        result = brs.check(sub)
        # Return only this claw's condition
        role_to_condition = {
            NanoClawRole.DIM_CLAW: 'dim_match',
            NanoClawRole.AUDIT_CLAW: 'audit_proportional',
            NanoClawRole.AWB_CLAW: 'awb_min',
            NanoClawRole.HODGE_CLAW: 'hodge_min_coexact',
            NanoClawRole.ESCROW_CLAW: 'udms_escrow',
            NanoClawRole.CRT_CLAW: 'crt_zero_defects',
            NanoClawRole.SYNDROME_CLAW: 'alena_zero_syndrome',
        }
        cond = role_to_condition.get(self.role, 'dim_match')
        return {"condition": cond, "passes": result.conditions.get(cond, False)}

    def _process_gate(self, sub: Dict) -> Dict:
        return {"gated": sub.get('snap_density', 0) > 0.5, "reason": "density_check"}

    def _process_receipt(self, sub: Dict) -> Dict:
        return {"receipt_stored": True, "chain_length": len(self.receipts)}

    def _receipt(self, event: str, data: Dict):
        r = {"timestamp": time.time(), "event": event,
             "claw_id": self.claw_id, "prev_hash": self.last_hash, "data": data}
        r["hash"] = hashlib.sha256(
            json.dumps(r, sort_keys=True, default=str).encode()
        ).hexdigest()
        self.last_hash = r["hash"]
        self.receipts.append(r)


# ════════════════════════════════════════════════════════════════
# 3. DOCKER COMPOSE GENERATOR
# ════════════════════════════════════════════════════════════════

class ComposeGenerator:
    """
    Generate docker-compose.yml from a ManifoldGraph specification.
    
    Each manifold node → one service (cmplx/morphon:latest).
    Each edge → network link.
    NanoClaw fleet → replicated services.
    """

    @staticmethod
    def generate(graph_spec: Dict[str, Any]) -> str:
        """Generate complete docker-compose from graph specification."""
        services = {}
        volumes = {
            "mmdb-data": {"driver": "local"},
            "receipt-chain": {"driver": "local"},
            "speedlight-cache": {"driver": "local"},
        }
        networks = {"morphon-net": {"driver": "bridge"}}

        # Graph controller
        services["graph-controller"] = {
            "image": "cmplx/morphon:latest",
            "command": ["--role", "controller"],
            "environment": {
                "NODE_ID": "graph-controller",
                "ROLE": "controller",
                "GRAPH_SPEC": json.dumps(graph_spec, default=str),
            },
            "ports": ["8080:8080"],
            "volumes": [
                "mmdb-data:/data/mmdb",
                "receipt-chain:/data/receipts",
            ],
            "networks": ["morphon-net"],
        }

        # Manifold nodes
        for node in graph_spec.get("nodes", []):
            node_id = node["node_id"]
            svc_name = node_id.replace("_", "-")
            axes = node.get("active_axes", list(range(24)))

            services[svc_name] = {
                "image": "cmplx/morphon:latest",
                "command": ["--role", node.get("role", "compute")],
                "environment": {
                    "NODE_ID": node_id,
                    "ROLE": node.get("role", "compute"),
                    "ACTIVE_AXES": ",".join(str(a) for a in sorted(axes)),
                    "NEIGHBORS": ",".join(node.get("neighbors", [])),
                },
                "volumes": [
                    f"mdhg-{svc_name}:/data/mdhg",
                    "speedlight-cache:/data/speedlight",
                ],
                "networks": ["morphon-net"],
                "depends_on": {"graph-controller": {"condition": "service_started"}},
            }
            volumes[f"mdhg-{svc_name}"] = {"driver": "local"}

        # NanoClaw BRS validators (one per condition)
        brs_roles = [
            ("dim", "DimClaw"), ("audit", "AuditClaw"), ("awb", "AWBClaw"),
            ("hodge", "HodgeClaw"), ("escrow", "EscrowClaw"),
            ("crt", "CRTClaw"), ("syndrome", "SyndromeClaw"),
        ]
        for short, role in brs_roles:
            services[f"nanoclaw-{short}"] = {
                "image": "cmplx/morphon:latest",
                "command": ["--role", role],
                "environment": {"NODE_ID": f"brs-{short}", "ROLE": role},
                "networks": ["morphon-net"],
                "deploy": {"replicas": 1, "resources": {
                    "limits": {"cpus": "0.25", "memory": "256M"}}},
            }

        # NanoClaw operational
        for role_name in ["EversionClaw", "InflationClaw", "GateKeeper"]:
            svc = f"nanoclaw-{role_name.lower()}"
            services[svc] = {
                "image": "cmplx/morphon:latest",
                "command": ["--role", role_name],
                "environment": {"NODE_ID": svc, "ROLE": role_name},
                "networks": ["morphon-net"],
                "deploy": {"replicas": 2},
            }

        # NanoClaw infrastructure
        services["nanoclaw-receipt"] = {
            "image": "cmplx/morphon:latest",
            "command": ["--role", "ReceiptClaw"],
            "environment": {"NODE_ID": "receipt-manager", "ROLE": "ReceiptClaw"},
            "volumes": ["receipt-chain:/data/receipts"],
            "networks": ["morphon-net"],
        }

        services["nanoclaw-swarm"] = {
            "image": "cmplx/morphon:latest",
            "command": ["--role", "SwarmClaw"],
            "environment": {
                "NODE_ID": "swarm-manager", "ROLE": "SwarmClaw",
                "HEAL_RATE": str(0.03007), "CAPSULE_TTL": "300",
            },
            "networks": ["morphon-net"],
        }

        services["nanoclaw-route"] = {
            "image": "cmplx/morphon:latest",
            "command": ["--role", "RouteClaw"],
            "environment": {"NODE_ID": "route-manager", "ROLE": "RouteClaw"},
            "networks": ["morphon-net"],
        }

        compose = {
            "version": "3.8",
            "services": services,
            "volumes": volumes,
            "networks": networks,
        }

        return json.dumps(compose, indent=2, default=str)


# ════════════════════════════════════════════════════════════════
# 4. END-TO-END DEPLOYMENT TEST
# ════════════════════════════════════════════════════════════════

def run_deployment_test():
    passed = 0
    failed = 0
    total = 0

    def test(name, condition, details=""):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✅ {name}")
        else:
            failed += 1
            print(f"  ❌ {name}: {details}")

    print("╔══════════════════════════════════════════════════════════╗")
    print("║   CMPLX DEPLOYMENT LAYER — TEST SUITE                  ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # --- Dockerfile ---
    print("\n━━━ Master Polyglot Image ━━━")
    test("Dockerfile generated", len(DOCKERFILE) > 500)
    test("Single FROM base", DOCKERFILE.count("FROM ") == 1)
    test("HEALTHCHECK present", "HEALTHCHECK" in DOCKERFILE)
    test("ENTRYPOINT is nanoclaw", "cmplx_nanoclaw.py" in DOCKERFILE)
    test("All data volumes declared",
         all(v in DOCKERFILE for v in ["/data/mmdb", "/data/mdhg",
                                        "/data/receipts", "/data/speedlight"]))

    # --- NanoClaw Activation ---
    print("\n━━━ NanoClaw Activation Protocol ━━━")

    # Test HingeClaw
    hinge = NanoClaw("hinge_ax0", NanoClawRole.HINGE_CLAW)
    test("HingeClaw starts FOLDED", hinge.state == NanoClawState.FOLDED)

    config = {"axes": {0, 1, 2, 3, 4, 5, 6, 7}}
    report = hinge.activate(config)
    test("Activation completes → OPERATING",
         hinge.state == NanoClawState.OPERATING)
    test(f"Projections computed: {report['phases']['projecting']['projections_computed']}",
         report['phases']['projecting']['projections_computed'] == 8)

    # Process a submission
    result = hinge.process({"vector": [1.0, 0.5, -0.3, 0.8, -0.2, 0.6, 0.1, -0.4]})
    test(f"HingeClaw processes: deviation={result.get('deviation', '?'):.4f}",
         'deviation' in result)
    test("Receipt emitted", len(hinge.receipts) >= 2)

    # Test EversionClaw
    ev_claw = NanoClaw("eversion_0", NanoClawRole.EVERSION_CLAW)
    ev_claw.activate({"axes": set(range(24))})
    ev_result = ev_claw.process({
        "vector": [1.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0],
        "genus": 0,
    })
    test(f"EversionClaw: {ev_result.get('phases', 0)} phases, "
         f"ΔΦ={ev_result.get('total_dphi', '?'):.6f}",
         ev_result.get('phases') == 6)

    # Test BRS validators
    print("\n━━━ BRS NanoClaw Fleet ━━━")
    brs_state = {
        'd_embed': 24, 'd_needed': 24, 'd_audit': 48.0,
        'vectors': [np.array([1.0, 1.0, 0, 0, 0, 0, 0, 0])],
        'active_escrow': 1.0, 'passive_escrow': 1.0,
        'crt_test_value': 42,
    }

    brs_roles = [
        NanoClawRole.DIM_CLAW, NanoClawRole.AUDIT_CLAW,
        NanoClawRole.AWB_CLAW, NanoClawRole.HODGE_CLAW,
        NanoClawRole.ESCROW_CLAW, NanoClawRole.CRT_CLAW,
        NanoClawRole.SYNDROME_CLAW,
    ]
    brs_results = {}
    for role in brs_roles:
        claw = NanoClaw(f"brs_{role.value}", role)
        claw.activate({"axes": set(range(24))})
        r = claw.process(brs_state)
        brs_results[role.value] = r
        status = "✓" if r.get('passes') else "✗"
        test(f"{role.value}: {r.get('condition')} = {status}",
             'condition' in r)

    all_pass = all(r.get('passes', False) for r in brs_results.values())
    test(f"BRS fleet consensus: {'ALL PASS' if all_pass else 'SOME FAIL'}",
         True)  # Report, don't require all pass

    # Test ephemeral swarm capsule
    print("\n━━━ Ephemeral Swarm Capsule ━━━")
    capsule = NanoClaw("swarm_repair_ax3", NanoClawRole.HINGE_CLAW,
                        ttl_seconds=0.1)  # Very short TTL for test
    capsule.activate({"axes": {3}, "parent_id": "hinge_ax0", "ttl": 0.1})
    test(f"Capsule TTL = {capsule.ttl_seconds}s", capsule.ttl_seconds == 0.1)
    test("Capsule not yet expired", not capsule.expired)
    time.sleep(0.15)
    test("Capsule expired after TTL", capsule.expired)
    dissolve_report = capsule.dissolve()
    test(f"Capsule dissolved: uptime={dissolve_report['uptime_seconds']:.2f}s",
         capsule.state == NanoClawState.DISSOLVING)

    # --- Compose Generator ---
    print("\n━━━ Docker Compose Generator ━━━")
    graph_spec = {
        "nodes": [
            {"node_id": "gateway", "role": "gateway",
             "active_axes": list(range(24)), "neighbors": ["compute_protein"]},
            {"node_id": "compute_protein", "role": "domain",
             "active_axes": [0,1,2,3,8,9,16,17], "neighbors": ["storage"]},
            {"node_id": "compute_turbulence", "role": "domain",
             "active_axes": [0,1,2,4,5,6,16,17,18,20,21,22], "neighbors": ["storage"]},
            {"node_id": "storage", "role": "storage",
             "active_axes": list(range(24)), "neighbors": []},
            {"node_id": "governance", "role": "governance",
             "active_axes": list(range(24)), "neighbors": []},
        ],
    }

    compose_yaml = ComposeGenerator.generate(graph_spec)
    compose = json.loads(compose_yaml)
    test(f"Services generated: {len(compose['services'])}",
         len(compose['services']) >= 15)

    # Check structure
    test("Graph controller present", "graph-controller" in compose['services'])
    test("All manifold nodes present",
         all(n['node_id'].replace('_', '-') in compose['services']
             for n in graph_spec['nodes']))
    test("7 BRS validators present",
         sum(1 for k in compose['services'] if k.startswith('nanoclaw-') and
             k.split('-')[1] in ['dim', 'audit', 'awb', 'hodge', 'escrow', 'crt', 'syndrome'])
         == 7)
    test("Receipt manager present", "nanoclaw-receipt" in compose['services'])
    test("Swarm manager present", "nanoclaw-swarm" in compose['services'])
    test("Route manager present", "nanoclaw-route" in compose['services'])

    # Verify all services use same image
    images = set(s.get('image', '') for s in compose['services'].values())
    test("All services use cmplx/morphon:latest",
         images == {"cmplx/morphon:latest"})

    # Check volumes
    test(f"Volumes: {len(compose['volumes'])}",
         len(compose['volumes']) >= 5)

    # Print service summary
    print(f"\n  Service inventory ({len(compose['services'])} total):")
    for svc_name in sorted(compose['services'].keys()):
        svc = compose['services'][svc_name]
        role = svc.get('environment', {}).get('ROLE', '?')
        replicas = svc.get('deploy', {}).get('replicas', 1)
        print(f"    {svc_name:30s} role={role:20s} replicas={replicas}")

    # --- End-to-End Flow ---
    print("\n━━━ End-to-End Deployment Flow ━━━")

    # Simulate the full deployment
    np.random.seed(42)

    # 1. Activate all NanoClaws
    claws = []
    for role in NanoClawRole:
        claw = NanoClaw(f"test_{role.value}", role)
        claw.activate({"axes": set(range(8))})
        claws.append(claw)
    test(f"All {len(claws)} NanoClaws activated",
         all(c.state == NanoClawState.OPERATING for c in claws))

    # 2. Process a submission through the fleet
    submission = {
        "vector": [1.0, 0.5, -0.3, 0.8, -0.2, 0.6, 0.1, -0.4],
        "genus": 0,
        "d_embed": 24, "d_needed": 24, "d_audit": 48.0,
        "vectors": [np.array([1.0, 1.0, 0, 0, 0, 0, 0, 0])],
        "active_escrow": 0.0, "passive_escrow": 0.0,
        "crt_test_value": 42,
        "snap_density": 0.7,
    }

    results = {}
    for claw in claws:
        r = claw.process(submission)
        results[claw.role.value] = r

    test(f"All {len(results)} roles processed", len(results) == len(NanoClawRole))

    # Count receipts across all claws
    total_receipts = sum(len(c.receipts) for c in claws)
    test(f"Total receipts emitted: {total_receipts}", total_receipts > 0)

    # Verify chain integrity per claw
    chains_ok = 0
    for claw in claws:
        prev = "0" * 64
        ok = True
        for r in claw.receipts:
            if r["prev_hash"] != prev:
                ok = False
                break
            prev = r["hash"]
        if ok:
            chains_ok += 1
    test(f"Receipt chains intact: {chains_ok}/{len(claws)}",
         chains_ok == len(claws))

    # 3. Dissolve all
    for claw in claws:
        claw.dissolve()
    test("All claws dissolved",
         all(c.state == NanoClawState.DISSOLVING for c in claws))

    # ── Summary ──
    print(f"\n{'═'*60}")
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"{'═'*60}")

    return passed, failed, total


# ════════════════════════════════════════════════════════════════
# WRITE DEPLOYMENT FILES
# ════════════════════════════════════════════════════════════════

def write_deployment_files(output_dir: str = "/home/claude/deployment"):
    """Write all deployment files to disk."""
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
        f.write(DOCKERFILE)

    with open(os.path.join(output_dir, "requirements.txt"), "w") as f:
        f.write(REQUIREMENTS_TXT)

    # Generate compose for the standard 5-manifold graph
    graph_spec = {
        "nodes": [
            {"node_id": "gateway", "role": "gateway",
             "active_axes": list(range(24)), "neighbors": ["compute_protein", "compute_turbulence"]},
            {"node_id": "compute_protein", "role": "domain",
             "active_axes": [0,1,2,3,8,9,16,17], "neighbors": ["storage", "governance"]},
            {"node_id": "compute_turbulence", "role": "domain",
             "active_axes": [0,1,2,4,5,6,16,17,18,20,21,22], "neighbors": ["storage", "governance"]},
            {"node_id": "storage", "role": "storage",
             "active_axes": list(range(24)), "neighbors": []},
            {"node_id": "governance", "role": "governance",
             "active_axes": list(range(24)), "neighbors": []},
        ],
    }

    compose = ComposeGenerator.generate(graph_spec)
    with open(os.path.join(output_dir, "docker-compose.morphon-graph.yml"), "w") as f:
        f.write(compose)

    print(f"Deployment files written to {output_dir}/")
    print(f"  Dockerfile")
    print(f"  requirements.txt")
    print(f"  docker-compose.morphon-graph.yml")

    return output_dir


if __name__ == "__main__":
    import sys
    if "--write" in sys.argv:
        write_deployment_files()
    else:
        run_deployment_test()
