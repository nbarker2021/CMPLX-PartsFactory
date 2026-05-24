"""Smoke tests for cmplx.economy — can we construct, mint, transfer, commission?"""
from __future__ import annotations

import pytest

from cmplx.economy import (
    BalanceSheet,
    CommissionStatus,
    EconomyProvider,
    EconomyState,
    ItemType,
    Listing,
    create_commission,
    mint,
    tick,
    transfer,
)


class TestConstruction:
    def test_provider_constructs_with_defaults(self):
        p = EconomyProvider()
        assert p.state.market_temp == 0.2
        assert p.health()["agents"] == 0

    def test_provider_constructs_with_state(self):
        s = EconomyState(market_temp=0.5)
        p = EconomyProvider(s)
        assert p.state.market_temp == 0.5


class TestBalanceOperations:
    def test_mint_increases_balance(self):
        p = EconomyProvider()
        bal = p.mint("agent-a", 100.0)
        assert bal.debt == 0.0  # mint subtracts debt

    def test_burn_decreases_balance(self):
        p = EconomyProvider()
        p.mint("agent-a", 100.0)
        result = p.burn("agent-a", 50.0)
        assert result is not None
        assert result.debt == 50.0

    def test_transfer_between_agents(self):
        p = EconomyProvider()
        p.mint("alice", 200.0)
        ok, reason = p.transfer("alice", "bob", 50.0)
        assert ok
        assert p.balance("alice").debt == 50.0
        assert p.balance("bob").debt == 0.0  # minted then transferred

    def test_transfer_fails_if_source_missing(self):
        p = EconomyProvider()
        ok, reason = p.transfer("alice", "bob", 50.0)
        assert not ok
        assert "not found" in reason.lower()

    def test_transfer_fails_if_insufficient(self):
        p = EconomyProvider()
        p.mint("alice", 10.0)
        ok, reason = p.transfer("alice", "bob", 500.0)
        assert not ok
        assert "insufficient" in reason.lower()


class TestCommissionOperations:
    def test_create_commission(self):
        p = EconomyProvider()
        comm = p.create_commission("alice", "build a module", 100.0)
        assert comm.status == CommissionStatus.OPEN
        assert comm.reward == 100.0
        assert p.health()["commissions"] == 1

    def test_list_commissions_filter(self):
        p = EconomyProvider()
        p.create_commission("alice", "task 1", 10.0)
        c2 = p.create_commission("bob", "task 2", 20.0)
        p.claim_commission(c2.commission_id, "charlie")
        open_comms = p.list_commissions(CommissionStatus.OPEN)
        claimed_comms = p.list_commissions(CommissionStatus.CLAIMED)
        assert len(open_comms) == 1
        assert len(claimed_comms) == 1


class TestMarketplace:
    def test_list_and_get_item(self):
        p = EconomyProvider()
        item = Listing(
            listing_id="lst-1",
            seller_id="alice",
            item_type=ItemType.BRAIN,
            price=50.0,
        )
        lid = p.list_item(item)
        assert lid == "lst-1"
        fetched = p.get_listing(lid)
        assert fetched is not None
        assert fetched.price == 50.0


class TestPureOperations:
    def test_mint_pure(self):
        state = EconomyState()
        balances = {}
        bal = mint(state, balances, "a", 100.0)
        assert bal.debt == 0.0

    def test_transfer_pure(self):
        state = EconomyState()
        balances = {"alice": BalanceSheet(debt=0.0)}
        ok, reason = transfer(balances, "alice", "bob", 50.0)
        assert ok
        assert balances["alice"].debt == 50.0

    def test_tick_applies_interest(self):
        state = EconomyState()
        balances = {"alice": BalanceSheet(debt=100.0, interest=0.05)}
        tick(state, balances)
        assert balances["alice"].debt == pytest.approx(105.0, rel=1e-3)


class TestHealth:
    def test_health_returns_counts(self):
        p = EconomyProvider()
        p.mint("a", 10.0)
        p.create_commission("a", "task", 5.0)
        h = p.health()
        assert h["agents"] == 1
        assert h["commissions"] == 1
        assert "prices" in h
