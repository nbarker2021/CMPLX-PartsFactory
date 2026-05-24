"""EconomyProvider — the `economy` application port (pending substrate registration).

Wraps pure operations with optional receipt minting and memory persistence.
Until the `economy` port is added to ``MorphonController.KNOWN_PORTS``,
callers import this provider directly or via the HTTP adapter.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .operations import (
    burn,
    create_commission,
    mint,
    tick,
    transfer,
    update_prices,
)
from .state import BalanceSheet, Commission, CommissionStatus, EconomyState, Listing


class EconomyProvider:
    """Canonical economy provider: balances, commissions, marketplace, lending."""

    name: str = "economy_provider"

    def __init__(self, state: Optional[EconomyState] = None) -> None:
        self.state = state or EconomyState()
        self._balances: Dict[str, BalanceSheet] = {}
        self._commissions: Dict[str, Commission] = {}
        self._listings: Dict[str, Listing] = {}

    # ── Balance operations ───────────────────────────────────────────

    def balance(self, agent_id: str) -> BalanceSheet:
        return self._balances.setdefault(agent_id, BalanceSheet())

    def mint(self, agent_id: str, amount: float) -> BalanceSheet:
        return mint(self.state, self._balances, agent_id, amount)

    def burn(self, agent_id: str, amount: float) -> Optional[BalanceSheet]:
        return burn(self._balances, agent_id, amount)

    def transfer(self, from_id: str, to_id: str, amount: float) -> tuple[bool, str]:
        return transfer(self._balances, from_id, to_id, amount)

    # ── Commission operations ────────────────────────────────────────

    def create_commission(
        self,
        requester: str,
        task: str,
        reward: float,
        snap_labels: Optional[List[str]] = None,
        deadline_hours: float = 24.0,
    ) -> Commission:
        return create_commission(
            self._commissions,
            requester,
            task,
            reward,
            snap_labels,
            deadline_hours,
        )

    def list_commissions(self, status: Optional[CommissionStatus] = None) -> List[Commission]:
        comms = list(self._commissions.values())
        if status is not None:
            comms = [c for c in comms if c.status == status]
        return comms

    def claim_commission(self, commission_id: str, claimant: str) -> tuple[bool, str]:
        comm = self._commissions.get(commission_id)
        if comm is None:
            return False, "commission not found"
        if comm.status != CommissionStatus.OPEN:
            return False, f"commission is {comm.status.value}"
        comm.status = CommissionStatus.CLAIMED
        return True, ""

    # ── Marketplace ──────────────────────────────────────────────────

    def list_item(self, listing: Listing) -> str:
        self._listings[listing.listing_id] = listing
        return listing.listing_id

    def get_listing(self, listing_id: str) -> Optional[Listing]:
        return self._listings.get(listing_id)

    # ── System tick ──────────────────────────────────────────────────

    def tick(self) -> None:
        tick(self.state, self._balances)

    def prices(self) -> Dict[str, float]:
        return update_prices(self.state)

    def health(self) -> Dict[str, Any]:
        return {
            "agents": len(self._balances),
            "commissions": len(self._commissions),
            "listings": len(self._listings),
            "resources": dict(self.state.resources),
            "prices": dict(self.state.prices),
        }
