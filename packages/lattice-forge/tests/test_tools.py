from __future__ import annotations

from lattice_forge.ledger.nsl import NSLTerm
from lattice_forge.tools import (
    MDHGTool,
    NSLTool,
    ReceiptTool,
    TransportTool,
)


def test_receipt_tool_graceful():
    tool = ReceiptTool()
    result = tool.invoke(operation="probe", payload={"status": "pass"})
    assert result["provenance"]["port"] == "receipt"
    assert "available" in result


def test_nsl_tool_local_term():
    tool = NSLTool()
    term = NSLTerm(noether_residue=0.1, shannon_residue=0.2, landauer_cost=0.3)
    result = tool.invoke(term=term)
    assert "provenance" in result


def test_mdhg_local_address():
    tool = MDHGTool()
    result = tool.invoke(page=2, block=1)
    assert "provenance" in result
    if not result.get("available"):
        assert "local_address" in result


def test_transport_local_record():
    tool = TransportTool()
    result = tool.invoke(step="regime_advance", from_regime="A", to_regime="C")
    assert "provenance" in result
