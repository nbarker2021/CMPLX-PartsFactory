"""Pure economic operations — no I/O, no port dependencies."""
from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Tuple

from .state import BalanceSheet, Commission, CommissionStatus, EconomyState, Listing


def mint(state: EconomyState, agent_balances: Dict[str, BalanceSheet], agent_id: str, amount: float) -> BalanceSheet:
    """Mint new coins into an agent's balance."""
    bal = agent_balances.setdefault(agent_id, BalanceSheet())
    bal.debt -= amount
    if bal.debt < 0:
        bal.debt = 0.0
    return bal


def burn(agent_balances: Dict[str, BalanceSheet], agent_id: str, amount: float) -> Optional[BalanceSheet]:
    """Burn coins from an agent's balance. Returns None if insufficient."""
    bal = agent_balances.get(agent_id)
    if bal is None or bal.debt + amount > bal.credit_limit * 2:
        return None
    bal.debt += amount
    return bal


def transfer(
    agent_balances: Dict[str, BalanceSheet],
    from_id: str,
    to_id: str,
    amount: float,
) -> Tuple[bool, str]:
    """Transfer coins between agents. Returns (success, reason)."""
    src = agent_balances.get(from_id)
    if src is None:
        return False, f"source agent {from_id!r} not found"
    if src.debt + amount > src.credit_limit * 2:
        return False, "insufficient funds"
    src.debt += amount
    dst = agent_balances.setdefault(to_id, BalanceSheet())
    dst.debt -= amount
    if dst.debt < 0:
        dst.debt = 0.0
    return True, ""


def create_commission(
    commissions: Dict[str, Commission],
    requester: str,
    task: str,
    reward: float,
    snap_labels: Optional[List[str]] = None,
    deadline_hours: float = 24.0,
) -> Commission:
    """Create a new open commission."""
    cid = str(uuid.uuid4())
    comm = Commission(
        commission_id=cid,
        requester=requester,
        task=task,
        reward=reward,
        status=CommissionStatus.OPEN,
        snap_labels=snap_labels or [],
        deadline_hours=deadline_hours,
    )
    commissions[cid] = comm
    return comm


def update_prices(state: EconomyState) -> Dict[str, float]:
    """Recompute resource prices based on supply."""
    for key in state.resources:
        supply = max(state.resources[key], 1.0)
        state.prices[key] = 1000.0 / supply * (1.0 + state.market_temp)
    return dict(state.prices)


def tick(state: EconomyState, agent_balances: Dict[str, BalanceSheet]) -> None:
    """Advance the economy one tick — apply interest and price drift."""
    update_prices(state)
    for bal in agent_balances.values():
        if bal.debt > 0:
            bal.debt *= 1.0 + bal.interest
            if bal.debt > bal.credit_limit * 2:
                bal.in_default = True
