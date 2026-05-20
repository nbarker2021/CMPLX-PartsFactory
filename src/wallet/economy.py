"""EconomyService — Expert marketplace, staking, and reward distribution.

Marketplace: discover experts by token cost and capability.
Staking: lock tokens for premium service level with yield.
Rewards: distribute based on successful compositions.
"""

from __future__ import annotations
import time
import uuid
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from governance.engine import GeometricGovernance, BoundaryEvent

logger = logging.getLogger("wallet.economy")

COUPLING = 0.030076

ITEM_TYPES = ("brain", "label_set", "training_data", "capability", "template", "artifact")

COMMISSION_STATUSES = ("open", "claimed", "in_progress", "completed", "disputed")

STAKING_POOLS_DEFAULT = {
    "stability": {"name": "Stability Pool", "base_apy": 0.05, "min_stake": 10},
    "growth": {"name": "Growth Pool", "base_apy": 0.12, "min_stake": 50},
    "premium": {"name": "Premium Service Pool", "base_apy": 0.20, "min_stake": 200},
    "venture": {"name": "Venture Pool", "base_apy": 0.25, "min_stake": 200},
    "e8_deep": {"name": "E8 Deep Pool", "base_apy": 0.08, "min_stake": 100},
}


@dataclass
class StakingPool:
    name: str
    base_apy: float
    min_stake: float
    total_staked: float = 0.0
    stakes: Dict[str, float] = field(default_factory=dict)


@dataclass
class ExpertListing:
    listing_id: str
    expert_id: str
    domain: str
    capabilities: List[str]
    token_cost: float
    description: str
    status: str = "active"
    created_at: float = 0.0


class EconomyService:
    def __init__(self, governance: GeometricGovernance, wallet):
        self.governance = governance
        self.wallet = wallet
        self.pools: Dict[str, StakingPool] = {
            name: StakingPool(**pool)
            for name, pool in STAKING_POOLS_DEFAULT.items()
        }
        self.listings: Dict[str, ExpertListing] = {}
        self.reward_log: List[Dict[str, Any]] = []
        self.item_listings: Dict[str, Dict[str, Any]] = {}
        self.commissions: Dict[str, Dict[str, Any]] = {}
        self.loans: Dict[str, Dict[str, Any]] = {}
        self.transaction_log: List[Dict[str, Any]] = []

    def list_expert(self, expert_id: str, domain: str,
                    capabilities: List[str], token_cost: float,
                    description: str = "") -> str:
        lid = f"lst_{uuid.uuid4().hex[:12]}"
        self.listings[lid] = ExpertListing(
            listing_id=lid, expert_id=expert_id, domain=domain,
            capabilities=capabilities, token_cost=token_cost,
            description=description, status="active",
            created_at=time.time(),
        )
        self.governance.record_boundary_event(BoundaryEvent(
            event_id=f"listing_{lid}",
            timestamp=time.time(),
            entropy_delta=0.05,
            receipt_data={
                "listing_id": lid, "expert_id": expert_id,
                "domain": domain, "token_cost": token_cost,
            },
            boundary_type="expert_listing",
        ))
        logger.info("Listed expert %s at cost %.2f", expert_id, token_cost)
        return lid

    def search_experts(self, domain: str = None,
                       capability: str = None,
                       max_cost: float = None,
                       min_cost: float = None) -> List[Dict[str, Any]]:
        results = []
        for listing in self.listings.values():
            if listing.status != "active":
                continue
            if domain and listing.domain != domain:
                continue
            if capability and capability not in listing.capabilities:
                continue
            if max_cost is not None and listing.token_cost > max_cost:
                continue
            if min_cost is not None and listing.token_cost < min_cost:
                continue
            results.append({
                "listing_id": listing.listing_id,
                "expert_id": listing.expert_id,
                "domain": listing.domain,
                "capabilities": listing.capabilities,
                "token_cost": listing.token_cost,
                "description": listing.description,
                "created_at": listing.created_at,
            })
        return sorted(results, key=lambda r: r["token_cost"])

    def hire_expert(self, buyer_id: str, listing_id: str,
                    governance_event_id: str = None) -> Dict[str, Any]:
        listing = self.listings.get(listing_id)
        if not listing or listing.status != "active":
            return {"error": "Listing not found or inactive"}
        tx = self.wallet.adjust_balance(
            buyer_id, -listing.token_cost, "spend",
            counterparty=listing.expert_id,
            memo=f"Hire: {listing.expert_id} ({listing.domain})",
            governance_event_id=governance_event_id,
        )
        self.wallet.adjust_balance(
            listing.expert_id, listing.token_cost * 0.95, "earn",
            counterparty=buyer_id,
            memo=f"Service: hired by {buyer_id}",
            governance_event_id=governance_event_id,
        )
        treasury_fee = listing.token_cost * 0.05
        self._distribute_treasury(treasury_fee, "marketplace_fee")

        listing.status = "hired"
        return {
            "tx_id": tx.tx_id,
            "buyer_id": buyer_id,
            "expert_id": listing.expert_id,
            "cost": listing.token_cost,
            "fee": treasury_fee,
            "domain": listing.domain,
        }

    def stake_tokens(self, expert_id: str, pool_name: str,
                     amount: float) -> Dict[str, Any]:
        pool = self.pools.get(pool_name)
        if not pool:
            return {"error": f"Pool {pool_name} not found"}
        if amount < pool.min_stake:
            return {"error": f"Min stake for {pool_name}: {pool.min_stake}"}
        self.wallet.adjust_balance(
            expert_id, -amount, "transfer",
            memo=f"Stake: {amount} to {pool_name}",
        )
        pool.stakes[expert_id] = pool.stakes.get(expert_id, 0) + amount
        pool.total_staked += amount
        apy = self._compute_apy(pool_name)
        event = BoundaryEvent(
            event_id=f"stake_{expert_id}_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            entropy_delta=amount * 0.01,
            receipt_data={
                "expert_id": expert_id, "pool": pool_name,
                "amount": amount, "apy": apy,
            },
            boundary_type="token_stake",
        )
        self.governance.record_boundary_event(event)
        logger.info("Staked %.2f in %s for %s", amount, pool_name, expert_id)
        return {
            "expert_id": expert_id, "pool": pool_name,
            "amount": amount, "apy": apy,
            "estimated_annual_yield": round(amount * apy, 4),
        }

    def unstake_tokens(self, expert_id: str, pool_name: str,
                       amount: float = None) -> Dict[str, Any]:
        pool = self.pools.get(pool_name)
        if not pool:
            return {"error": f"Pool {pool_name} not found"}
        staked = pool.stakes.get(expert_id, 0)
        unstake_amount = min(amount or staked, staked)
        pool.stakes[expert_id] = staked - unstake_amount
        pool.total_staked -= unstake_amount
        self.wallet.adjust_balance(
            expert_id, unstake_amount, "earn",
            memo=f"Unstake: {unstake_amount} from {pool_name}",
        )
        logger.info("Unstaked %.2f from %s for %s", unstake_amount, pool_name, expert_id)
        return {"expert_id": expert_id, "amount": unstake_amount, "pool": pool_name}

    def distribute_rewards(self, composition_results: List[Dict[str, Any]],
                           total_reward: float = None) -> List[Dict[str, Any]]:
        distributed = []
        for result in composition_results:
            expert_id = result.get("expert_id")
            contribution = result.get("contribution", 1.0)
            amount = total_reward or contribution * COUPLING
            if total_reward:
                total_contrib = sum(
                    r.get("contribution", 1.0) for r in composition_results
                ) or 1.0
                amount = total_reward * (contribution / total_contrib)
            self.wallet.adjust_balance(
                expert_id, amount, "earn",
                memo=f"Composition reward: convergence={result.get('convergence', 0):.3f}",
            )
            distributed.append({
                "expert_id": expert_id,
                "amount": round(amount, 6),
                "contribution": contribution,
            })
        self.reward_log.append({
            "timestamp": time.time(),
            "distributions": distributed,
            "total": sum(d["amount"] for d in distributed),
        })
        return distributed

    def _distribute_treasury(self, amount: float, reason: str) -> None:
        self.wallet.adjust_balance("__treasury__", amount, "earn", memo=reason)

    def _compute_apy(self, pool_name: str) -> float:
        pool = self.pools.get(pool_name)
        if not pool:
            return 0.0
        utilization_factor = 1.0 / (1.0 + pool.total_staked * COUPLING)
        return round(pool.base_apy * utilization_factor, 6)

    def get_pool_status(self, pool_name: str = None) -> Dict[str, Any]:
        if pool_name:
            pool = self.pools.get(pool_name)
            if not pool:
                return {"error": "Pool not found"}
            return {
                "name": pool.name,
                "base_apy": pool.base_apy,
                "current_apy": self._compute_apy(pool_name),
                "min_stake": pool.min_stake,
                "total_staked": pool.total_staked,
                "stakers": len(pool.stakes),
            }
        return {
            name: {
                "name": p.name,
                "base_apy": p.base_apy,
                "current_apy": self._compute_apy(name),
                "min_stake": p.min_stake,
                "total_staked": p.total_staked,
                "stakers": len(p.stakes),
            }
            for name, p in self.pools.items()
        }

    def get_reward_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.reward_log[-limit:]

    def get_marketplace_summary(self) -> Dict[str, Any]:
        active = [l for l in self.listings.values() if l.status == "active"]
        domains = {}
        for l in active:
            domains[l.domain] = domains.get(l.domain, 0) + 1
        return {
            "total_listings": len(self.listings),
            "active_listings": len(active),
            "domains": domains,
            "pool_status": self.get_pool_status(),
        }

    # ── TMN2 Integration: Generic item marketplace ────────────────

    def list_item(self, seller_id: str, item_type: str, price: float,
                  title: str, description: str = "",
                  snap_labels: List[str] = None) -> Dict[str, Any]:
        """List a generic item on the marketplace."""
        if item_type not in ITEM_TYPES:
            return {"error": f"Invalid item type: {item_type}. Must be one of {ITEM_TYPES}"}
        lid = f"item-{uuid.uuid4().hex[:12]}"
        listing = {
            "listing_id": lid, "seller_id": seller_id,
            "item_type": item_type, "title": title,
            "description": description, "price": price,
            "snap_labels": snap_labels or [],
            "status": "active", "created_at": time.time(),
            "buyer_id": None,
        }
        self.item_listings[lid] = listing
        self.governance.record_boundary_event(BoundaryEvent(
            event_id=f"item_listing_{lid}", timestamp=time.time(),
            entropy_delta=0.02,
            receipt_data={"listing_id": lid, "seller_id": seller_id, "item_type": item_type, "price": price},
            boundary_type="item_listing",
        ))
        return {
            "listing_id": lid, "status": "active",
            "price": price, "item_type": item_type,
        }

    def buy_item(self, buyer_id: str, listing_id: str) -> Dict[str, Any]:
        """Buy an item from the marketplace."""
        listing = self.item_listings.get(listing_id)
        if not listing:
            return {"error": "Listing not found"}
        if listing["status"] != "active":
            return {"error": f"Listing is {listing['status']}"}
        if listing["seller_id"] == buyer_id:
            return {"error": "Cannot buy your own listing"}

        price = listing["price"]
        self.wallet.adjust_balance(
            buyer_id, -price, "spend",
            counterparty=listing["seller_id"],
            memo=f"Purchase: {listing['title']}",
        )
        self.wallet.adjust_balance(
            listing["seller_id"], price * 0.95, "earn",
            counterparty=buyer_id,
            memo=f"Sale: {listing['title']}",
        )
        self._distribute_treasury(price * 0.05, "marketplace_fee")

        listing["status"] = "sold"
        listing["buyer_id"] = buyer_id
        listing["sold_at"] = time.time()

        return {
            "listing_id": listing_id, "buyer_id": buyer_id,
            "seller_id": listing["seller_id"], "price": price,
            "fee": round(price * 0.05, 4), "status": "sold",
        }

    def get_marketplace(self, item_type: str = None,
                        max_price: float = None) -> Dict[str, Any]:
        """List all active item listings."""
        result = []
        for l in self.item_listings.values():
            if l["status"] != "active":
                continue
            if item_type and l["item_type"] != item_type:
                continue
            if max_price and l["price"] > max_price:
                continue
            result.append({
                "listing_id": l["listing_id"], "seller_id": l["seller_id"],
                "item_type": l["item_type"], "title": l["title"],
                "price": l["price"], "snap_labels": l["snap_labels"],
                "created_at": l["created_at"],
            })
        result.sort(key=lambda x: x["created_at"], reverse=True)
        return {"listings": result, "total": len(result)}

    # ── TMN2 Integration: Commissions ─────────────────────────────

    def create_commission(self, requester: str, task: str, reward: float,
                          snap_labels: List[str] = None,
                          deadline_hours: float = 24.0) -> Dict[str, Any]:
        """Create a commission request with escrowed reward."""
        cid = f"com-{uuid.uuid4().hex[:12]}"
        self.wallet.adjust_balance(
            requester, -reward, "transfer",
            memo=f"Commission escrow: {cid}",
        )
        commission = {
            "commission_id": cid, "requester": requester,
            "task": task, "reward": reward,
            "snap_labels": snap_labels or [],
            "status": "open", "created_at": time.time(),
            "deadline_hours": deadline_hours,
            "claimed_by": None, "claimed_at": None, "completed_at": None,
        }
        self.commissions[cid] = commission
        return {
            "commission_id": cid, "status": "open",
            "reward": reward, "escrowed": True,
            "deadline_hours": deadline_hours,
        }

    def claim_commission(self, agent_id: str, commission_id: str) -> Dict[str, Any]:
        """Claim an open commission."""
        com = self.commissions.get(commission_id)
        if not com:
            return {"error": "Commission not found"}
        if com["status"] != "open":
            return {"error": f"Commission is {com['status']}"}
        com["status"] = "claimed"
        com["claimed_by"] = agent_id
        com["claimed_at"] = time.time()
        return {"commission_id": commission_id, "status": "claimed", "claimed_by": agent_id}

    def complete_commission(self, agent_id: str, commission_id: str) -> Dict[str, Any]:
        """Complete a commission and release reward."""
        com = self.commissions.get(commission_id)
        if not com:
            return {"error": "Commission not found"}
        if com["claimed_by"] != agent_id:
            return {"error": f"Commission not claimed by {agent_id}"}
        if com["status"] not in ("claimed", "in_progress"):
            return {"error": f"Commission is {com['status']}"}
        com["status"] = "completed"
        com["completed_at"] = time.time()
        self.wallet.adjust_balance(
            agent_id, com["reward"], "earn",
            memo=f"Commission reward: {commission_id}",
        )
        return {
            "commission_id": commission_id, "status": "completed",
            "agent_id": agent_id, "reward": com["reward"],
        }

    def get_commissions(self, status: str = None) -> Dict[str, Any]:
        """List commissions, optionally filtered by status."""
        result = []
        for c in self.commissions.values():
            if status and c["status"] != status:
                continue
            result.append({
                "commission_id": c["commission_id"],
                "requester": c["requester"],
                "task": c["task"][:100],
                "reward": c["reward"],
                "status": c["status"],
                "snap_labels": c["snap_labels"],
                "created_at": c["created_at"],
                "deadline_hours": c["deadline_hours"],
            })
        return {"commissions": result, "total": len(result)}

    # ── TMN2 Integration: Lending ─────────────────────────────────

    def create_loan(self, lender_id: str, amount: float, rate: float,
                    duration_hours: float) -> Dict[str, Any]:
        """Create a lending offer."""
        loan_id = f"loan-{uuid.uuid4().hex[:12]}"
        self.wallet.adjust_balance(
            lender_id, -amount, "transfer",
            memo=f"Loan issued: {loan_id}",
        )
        interest = round(amount * rate * (duration_hours / 720), 4)
        loan = {
            "loan_id": loan_id, "lender_id": lender_id,
            "amount": amount, "rate": rate, "interest": interest,
            "total_repayment": amount + interest,
            "duration_hours": duration_hours, "status": "active",
            "created_at": time.time(), "borrower_id": None,
        }
        self.loans[loan_id] = loan
        return {
            "loan_id": loan_id, "amount": amount, "rate": rate,
            "interest": interest, "total_repayment": loan["total_repayment"],
            "duration_hours": duration_hours, "status": "active",
        }

    def repay_loan(self, borrower_id: str, loan_id: str) -> Dict[str, Any]:
        """Repay a loan (borrower repays lender)."""
        loan = self.loans.get(loan_id)
        if not loan:
            return {"error": "Loan not found"}
        if loan["status"] != "active":
            return {"error": f"Loan is {loan['status']}"}

        repayment = loan["total_repayment"]
        self.wallet.adjust_balance(
            borrower_id, -repayment, "spend",
            counterparty=loan["lender_id"],
            memo=f"Loan repayment: {loan_id}",
        )
        self.wallet.adjust_balance(
            loan["lender_id"], repayment, "earn",
            counterparty=borrower_id,
            memo=f"Loan return: {loan_id}",
        )
        loan["status"] = "repaid"
        loan["repaid_at"] = time.time()

        self._log_tx(borrower_id, repayment, "loan_repayment", loan_id)
        return {
            "loan_id": loan_id, "status": "repaid",
            "total_repayment": repayment, "borrower_id": borrower_id,
        }

    # ── TMN2 Integration: Buyback ──────────────────────────────────

    def buyback(self, amount: float, max_price: float) -> Dict[str, Any]:
        """Treasury buyback of coins from the market."""
        treasury_balance = self.wallet.get_balance("__treasury__")
        cost = min(amount * max_price, treasury_balance)
        coins_bought = cost / max_price if max_price > 0 else 0

        if coins_bought <= 0:
            return {"error": "Treasury has insufficient funds for buyback"}

        self.wallet.adjust_balance(
            "__treasury__", -cost, "spend",
            memo=f"Buyback: {round(coins_bought, 2)} coins",
        )

        bid = f"bb-{uuid.uuid4().hex[:8]}"
        self._log_tx("__treasury__", cost, "buyback", bid)
        return {
            "buyback_id": bid, "coins_bought": round(coins_bought, 4),
            "cost": round(cost, 4),
            "effective_price": round(cost / coins_bought, 4) if coins_bought > 0 else 0,
            "max_price": max_price,
            "treasury_remaining": round(self.wallet.get_balance("__treasury__"), 4),
        }

    # ── TMN2 Integration: Transaction log ──────────────────────────

    def get_transaction_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(reversed(self.transaction_log[-limit:]))

    def get_pool_details(self, pool_name: str = None) -> Dict[str, Any]:
        """Get detailed staking pool info including all stakers."""
        if pool_name:
            pool = self.pools.get(pool_name)
            if not pool:
                return {"error": "Pool not found"}
            stakers = [
                {"agent_id": aid, "staked": amt}
                for aid, amt in pool.stakes.items()
            ]
            return {
                "name": pool.name, "base_apy": pool.base_apy,
                "current_apy": self._compute_apy(pool_name),
                "min_stake": pool.min_stake,
                "total_staked": pool.total_staked,
                "stakers": stakers,
            }
        return {
            name: {
                "name": p.name, "base_apy": p.base_apy,
                "current_apy": self._compute_apy(name),
                "min_stake": p.min_stake,
                "total_staked": p.total_staked,
                "stakers": [{"agent_id": aid, "staked": amt} for aid, amt in p.stakes.items()],
            }
            for name, p in self.pools.items()
        }

    # ── Internal helpers ───────────────────────────────────────────

    def _log_tx(self, agent_id: str, amount: float, reason: str,
                ref_id: str = None):
        entry = {
            "tx_id": f"tx-{uuid.uuid4().hex[:8]}",
            "agent_id": agent_id, "amount": amount,
            "reason": reason, "ref_id": ref_id,
            "timestamp": time.time(),
        }
        self.transaction_log.append(entry)
        if len(self.transaction_log) > 10000:
            self.transaction_log[:] = self.transaction_log[-5000:]
