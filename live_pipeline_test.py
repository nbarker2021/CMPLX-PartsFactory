#!/usr/bin/env python3
"""Live pipeline test from inside the container."""
import time, json, sys
sys.path.insert(0, "/workspace/PartsFactory/CMPLX-PartsFactory/src")

# Service connectivity test
import httpx
services = {
    "research": ("http://host.docker.internal:3000/health", False),
    "mmdb": ("http://host.docker.internal:8824/health", True),
    "mdhg": ("http://host.docker.internal:8825/health", True),
    "snap": ("http://host.docker.internal:8823/health", True),
    "tarpit": ("http://host.docker.internal:8844/health", False),
    "manny": ("http://host.docker.internal:8870/health", False),
}
results = {}
for name, (url, try_json) in services.items():
    try:
        r = httpx.get(url, timeout=3.0)
        body = r.text[:200] if try_json else "connected"
        results[name] = {"status": r.status_code, "body": body}
    except Exception as e:
        results[name] = {"status": "error", "error": str(e)[:60]}

print("=" * 55)
print("  LIVE PIPELINE TEST — inside container")
print("=" * 55)
print()
print("  SERVICE CONNECTIVITY:")
for name, r in results.items():
    code = r.get("status", "ERR")
    icon = "OK" if code == 200 else "!!"
    print(f"    {name:12s}: {icon} ({code})")

# Core systems
from governance.engine import GeometricGovernance, BoundaryEvent
from thinktank.engine import ThinkTankEngine
from snapdna.factory import factory
from services.registry import registry
from governance.sap import SAPGovernance

gov = GeometricGovernance()
tt = ThinkTankEngine()
sap = SAPGovernance()

# Read a test paper
paper_path = "/workspace/MannyUnification2/historical builds/Aletheia2/Aletheia2/cqe_unified_runtime_v8.0_RELEASE/cqe_unified_runtime/COMPREHENSIVE_REVIEW.md"
with open(paper_path) as f:
    content = f.read()
head = content[:3000]

print()
print("  PROCESSING:")
print(f"    File: COMPREHENSIVE_REVIEW.md ({len(content)} chars)")

# 1. ThinkTank
r = tt.reason(head[:2000])
analyses = r.get("perspectives", [])
consensus = r.get("consensus", {})
print(f"    [1] THINKTANK: {len(analyses)} perspectives, verdict={consensus.get('verdict')}")

# 2. SNAP via running service
snap = registry.snap
snap_ok = False
if snap:
    try:
        sr = snap.stratify(head[:1000], depth=2)
        snap_ok = True
        print(f"    [2] SNAP: stratify ok")
    except Exception as e:
        pass
if not snap_ok:
    from services.semantic_service import SemanticService
    sem = SemanticService()
    labels = [f"SNAPdomain_{w}" for w in ["e8","lattice","conservation","governance","receipt","agent","pipeline"] if w in head.lower()]
    print(f"    [2] SNAP: unavailable (labels={labels})")

# 3. Governance audit
gov.record_boundary_event(BoundaryEvent(
    event_id=f"live_test_{int(time.time())}", timestamp=time.time(),
    entropy_delta=0.0, receipt_data={"test": "live_container", "chars": len(content)},
    boundary_type="live_test",
))
print(f"    [3] GOVERNANCE: {len(gov.audit_trail)} events")

# 4. Expert derivation
spec = factory.new_spec("ReviewAnalyst", "document_review",
    "Analyze CQE review documents",
    {"text": "str"}, {"analysis": "dict"},
    {"lane": "analytical", "dr": 7})
paths = factory.emit_agent(spec)
print(f"    [4] EXPERT: created ReviewAnalyst")

# 5. SAP governance check
try:
    j = sap.judge(agent_id="test_agent", content=head[:500],
                  snap_labels=["SNAPdomain_test"], delta_phi=0.0,
                  boundary_type="default")
    print(f"    [5] SAP: sentinel={j.get('sentinel',{}).get('status','?')}, score={j.get('arbiter',{}).get('score',0):.2f}")
except Exception as e:
    print(f"    [5] SAP: error ({str(e)[:60]})")

# Summary
print()
print("  RESULTS:")
healthy = len([r for r in results.values() if r.get("status") == 200])
print(f"    Services: {healthy}/6 reachable")
print(f"    ThinkTank perspectives: {len(analyses)}")
print(f"    Governance events: {len(gov.audit_trail)}")
print(f"    New expert: ReviewAnalyst")
print(f"    SAP: governance triage active")
print()
print("=" * 55)
print("  LIVE TEST COMPLETE")
print("=" * 55)
