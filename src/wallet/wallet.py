"""ExpertWallet — Token balance and transaction history per expert.

Persistent SQLite storage. Linked to agent identity from sidecar.
Supports earn, spend, transfer, mint, burn transaction types.
"""

from __future__ import annotations
import os
import json
import sqlite3
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("wallet")


def _runtime_path(*parts: str) -> str:
    root = os.environ.get("CMPLX_RUNTIME_DIR")
    if root:
        return str(Path(root).joinpath(*parts))
    if os.name == "nt":
        return str(Path("D:/PartsFactory/runtime/CMPLX-PartsFactory").joinpath(*parts))
    return str(
        Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
        .joinpath("cmplx-partsfactory", *parts)
    )


DEFAULT_WALLET_PATH = _runtime_path("data", "wallet.sqlite")

WALLET_SCHEMA = """
CREATE TABLE IF NOT EXISTS wallets (
    expert_id TEXT PRIMARY KEY,
    identity_label TEXT,
    token_type TEXT NOT NULL DEFAULT 'EXPERT',
    balance REAL NOT NULL DEFAULT 0.0,
    lifetime_earned REAL NOT NULL DEFAULT 0.0,
    lifetime_spent REAL NOT NULL DEFAULT 0.0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    tx_id TEXT PRIMARY KEY,
    expert_id TEXT NOT NULL,
    tx_type TEXT NOT NULL,
    token_type TEXT NOT NULL DEFAULT 'EXPERT',
    amount REAL NOT NULL,
    balance_before REAL NOT NULL,
    balance_after REAL NOT NULL,
    counterparty TEXT,
    memo TEXT,
    receipt_hash TEXT,
    governance_event_id TEXT,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS spending_limits (
    expert_id TEXT PRIMARY KEY,
    daily_limit REAL DEFAULT 100.0,
    daily_spent REAL DEFAULT 0.0,
    daily_reset_at REAL,
    per_tx_limit REAL DEFAULT 50.0
);

CREATE INDEX IF NOT EXISTS idx_tx_expert ON transactions(expert_id);
CREATE INDEX IF NOT EXISTS idx_tx_type ON transactions(tx_type);
CREATE INDEX IF NOT EXISTS idx_tx_created ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_tx_receipt ON transactions(receipt_hash);
"""


class WalletError(Exception):
    pass


class InsufficientBalanceError(WalletError):
    pass


class SpendingLimitError(WalletError):
    pass


@dataclass
class Transaction:
    tx_id: str
    expert_id: str
    tx_type: str
    amount: float
    balance_before: float
    balance_after: float
    counterparty: Optional[str]
    memo: Optional[str]
    receipt_hash: Optional[str]
    governance_event_id: Optional[str]
    created_at: float


class ExpertWallet:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_WALLET_PATH
        self._conn: Optional[sqlite3.Connection] = None
        self._cache: Dict[str, Dict[str, Any]] = {}

    def connect(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(WALLET_SCHEMA)
        self._conn.commit()
        self._load_cache()

    def _load_cache(self) -> None:
        cursor = self._conn.execute("SELECT * FROM wallets")
        for row in cursor.fetchall():
            self._cache[row["expert_id"]] = dict(row)

    def create_wallet(self, expert_id: str, identity_label: str = None,
                      token_type: str = "EXPERT", initial_balance: float = 0.0) -> str:
        now = time.time()
        self._conn.execute("""
            INSERT OR IGNORE INTO wallets (expert_id, identity_label, token_type, balance,
                                           lifetime_earned, lifetime_spent, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (expert_id, identity_label, token_type, initial_balance,
              max(initial_balance, 0), max(-initial_balance, 0), now, now))
        self._conn.commit()
        self._cache[expert_id] = {
            "expert_id": expert_id, "identity_label": identity_label,
            "token_type": token_type, "balance": initial_balance,
            "lifetime_earned": max(initial_balance, 0),
            "lifetime_spent": max(-initial_balance, 0),
            "created_at": now, "updated_at": now,
        }
        self._conn.execute("""
            INSERT OR IGNORE INTO spending_limits (expert_id, daily_limit, daily_spent, daily_reset_at)
            VALUES (?, ?, 0, ?)
        """, (expert_id, 100.0, now))
        self._conn.commit()
        return expert_id

    def get_balance(self, expert_id: str) -> float:
        wallet = self._cache.get(expert_id)
        if not wallet:
            return 0.0
        return wallet["balance"]

    def get_wallet(self, expert_id: str) -> Optional[Dict[str, Any]]:
        if expert_id in self._cache:
            return dict(self._cache[expert_id])
        cursor = self._conn.execute(
            "SELECT * FROM wallets WHERE expert_id = ?", (expert_id,)
        )
        row = cursor.fetchone()
        if row:
            w = dict(row)
            self._cache[expert_id] = w
            return w
        return None

    def adjust_balance(self, expert_id: str, amount: float, tx_type: str,
                       counterparty: str = None, memo: str = None,
                       receipt_hash: str = None,
                       governance_event_id: str = None) -> Transaction:
        if expert_id not in self._cache:
            raise WalletError(f"Wallet not found for {expert_id}")

        wallet = self._cache[expert_id]
        balance_before = wallet["balance"]

        if amount < 0 and balance_before + amount < 0:
            raise InsufficientBalanceError(
                f"Insufficient balance: {balance_before}, need {-amount}"
            )

        self._check_spending_limit(expert_id, abs(amount), tx_type)

        balance_after = balance_before + amount
        tx_id = f"tx_{uuid.uuid4().hex[:12]}"
        now = time.time()

        self._conn.execute("""
            INSERT INTO transactions (tx_id, expert_id, tx_type, amount,
                                       balance_before, balance_after,
                                       counterparty, memo, receipt_hash,
                                       governance_event_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tx_id, expert_id, tx_type, amount, balance_before,
              balance_after, counterparty, memo, receipt_hash,
              governance_event_id, now))

        lifetime_earned = wallet["lifetime_earned"] + max(amount, 0)
        lifetime_spent = wallet["lifetime_spent"] + max(-amount, 0)

        self._conn.execute("""
            UPDATE wallets SET balance = ?, lifetime_earned = ?, lifetime_spent = ?,
                               updated_at = ? WHERE expert_id = ?
        """, (balance_after, lifetime_earned, lifetime_spent, now, expert_id))
        self._conn.commit()

        wallet["balance"] = balance_after
        wallet["lifetime_earned"] = lifetime_earned
        wallet["lifetime_spent"] = lifetime_spent
        wallet["updated_at"] = now

        tx = Transaction(
            tx_id=tx_id, expert_id=expert_id, tx_type=tx_type,
            amount=amount, balance_before=balance_before,
            balance_after=balance_after, counterparty=counterparty,
            memo=memo, receipt_hash=receipt_hash,
            governance_event_id=governance_event_id, created_at=now,
        )
        return tx

    def _check_spending_limit(self, expert_id: str, amount: float, tx_type: str) -> None:
        if tx_type not in ("spend", "transfer"):
            return
        cursor = self._conn.execute(
            "SELECT * FROM spending_limits WHERE expert_id = ?", (expert_id,)
        )
        row = cursor.fetchone()
        if not row:
            return
        limit = dict(row)
        now = time.time()
        if limit.get("per_tx_limit", 0) and amount > limit["per_tx_limit"]:
            raise SpendingLimitError(
                f"Per-transaction limit {limit['per_tx_limit']} exceeded: {amount}"
            )
        if limit.get("daily_reset_at") and now - limit["daily_reset_at"] > 86400:
            self._conn.execute("""
                UPDATE spending_limits SET daily_spent = 0, daily_reset_at = ? WHERE expert_id = ?
            """, (now, expert_id))
            self._conn.commit()
            limit["daily_spent"] = 0
        if limit.get("daily_limit", 0) and limit["daily_spent"] + amount > limit["daily_limit"]:
            raise SpendingLimitError(
                f"Daily limit {limit['daily_limit']} exceeded: "
                f"{limit['daily_spent'] + amount}"
            )
        self._conn.execute("""
            UPDATE spending_limits SET daily_spent = daily_spent + ? WHERE expert_id = ?
        """, (amount, expert_id))
        self._conn.commit()

    def get_transactions(self, expert_id: str, tx_type: str = None,
                         limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        conditions = ["expert_id = ?"]
        params = [expert_id]
        if tx_type:
            conditions.append("tx_type = ?")
            params.append(tx_type)
        sql = (f"SELECT * FROM transactions WHERE {' AND '.join(conditions)} "
               f"ORDER BY created_at DESC LIMIT ? OFFSET ?")
        params.extend([limit, offset])
        cursor = self._conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_transactions_by_time(self, expert_id: str = None,
                                  start_time: float = None,
                                  end_time: float = None,
                                  limit: int = 100) -> List[Dict[str, Any]]:
        conditions = []
        params = []
        if expert_id:
            conditions.append("expert_id = ?")
            params.append(expert_id)
        if start_time:
            conditions.append("created_at >= ?")
            params.append(start_time)
        if end_time:
            conditions.append("created_at <= ?")
            params.append(end_time)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM transactions {where} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = self._conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def link_identity(self, expert_id: str, identity_label: str) -> None:
        self._conn.execute(
            "UPDATE wallets SET identity_label = ?, updated_at = ? WHERE expert_id = ?",
            (identity_label, time.time(), expert_id)
        )
        self._conn.commit()
        if expert_id in self._cache:
            self._cache[expert_id]["identity_label"] = identity_label

    def set_spending_limits(self, expert_id: str, daily_limit: float = None,
                            per_tx_limit: float = None) -> None:
        updates = []
        params = []
        if daily_limit is not None:
            updates.append("daily_limit = ?")
            params.append(daily_limit)
        if per_tx_limit is not None:
            updates.append("per_tx_limit = ?")
            params.append(per_tx_limit)
        if updates:
            params.append(expert_id)
            self._conn.execute(
                f"UPDATE spending_limits SET {', '.join(updates)} WHERE expert_id = ?",
                params
            )
            self._conn.commit()

    def get_all_wallets(self) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM wallets ORDER BY balance DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_total_supply(self) -> float:
        cursor = self._conn.execute("SELECT COALESCE(SUM(balance), 0) FROM wallets")
        return cursor.fetchone()[0]

    def get_total_earned(self) -> float:
        cursor = self._conn.execute(
            "SELECT COALESCE(SUM(lifetime_earned), 0) FROM wallets"
        )
        return cursor.fetchone()[0]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
