"""MintService — Mint and burn tokens for expert lifecycle.

All operations audited via GeometricGovernance. Token economics
govern reward rates and spending limits per expert.
"""

from __future__ import annotations
import fnmatch
import hashlib
import json
import math
import time
import uuid
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field

from governance.engine import GeometricGovernance, BoundaryEvent, QuadraticInvariant

logger = logging.getLogger("wallet.mint")


@dataclass
class TokenEconomics:
    reward_rate: float = 0.1
    mint_bonus: float = 50.0
    min_spending_limit: float = 10.0
    max_spending_limit: float = 1000.0
    default_daily_limit: float = 100.0
    burn_penalty_rate: float = 0.02
    reward_per_composition: float = 5.0
    reward_per_discovery: float = 20.0
    coupling: float = 0.030076
    escrow_rate: float = 0.05
    citation_threshold: int = 10
    max_boost: float = 2.0
    sat_denominator: int = 200
    shell_weights: tuple = (1.0, 0.5, 0.25, 0.125)


# ── Coin Library ─────────────────────────────────────────────────────

class CoinLibrary:
    """Maps SNAP labels to coin names via label coverage indexing and glob pattern matching.
    Open and growing — coins are discovered from stable label clusters.
    """

    def __init__(self):
        self.coins: Dict[str, Dict] = {}
        self._label_index: Dict[str, Set[str]] = {}
        self._pattern_index: List[tuple] = []

    def load_from_file(self, path: str):
        """Load coin definitions from a JSON file."""
        try:
            with open(path) as f:
                data = json.load(f)
            for name, defn in data.get("coins", {}).items():
                self.register_coin(name, defn)
        except Exception as e:
            logger.warning("CoinLibrary load failed: %s", e)

    def register_coin(self, name: str, defn: dict):
        """Register a coin in the library and build label/pattern indices."""
        self.coins[name] = defn
        labels = defn.get("label_coverage", {})
        if isinstance(labels, dict):
            all_labels = labels.get("primary", []) + labels.get("secondary", [])
            patterns = labels.get("patterns", [])
        else:
            all_labels = defn.get("label_patterns", [])
            patterns = [l for l in all_labels if "*" in l]
            all_labels = [l for l in all_labels if "*" not in l]

        for label in all_labels:
            self._label_index.setdefault(label, set()).add(name)

        for pattern in patterns:
            self._pattern_index.append((pattern, name))

    def match_labels(self, snap_labels: List[str]) -> Dict[str, List[str]]:
        """Given SNAP labels, return {coin_name: [matched_labels]}."""
        matches: Dict[str, List[str]] = {}
        for label in snap_labels:
            if label in self._label_index:
                for coin_name in self._label_index[label]:
                    matches.setdefault(coin_name, []).append(label)
            for pattern, coin_name in self._pattern_index:
                if fnmatch.fnmatch(label, pattern):
                    if label not in matches.setdefault(coin_name, []):
                        matches[coin_name].append(label)
        if "MERIT" not in matches:
            matches["MERIT"] = ["*"]
        return matches

    def find_uncovered(self, snap_labels: List[str]) -> List[str]:
        """Find labels that don't match any coin (except MERIT)."""
        covered = set()
        for label in snap_labels:
            if label in self._label_index:
                covered.add(label)
            else:
                for pattern, _ in self._pattern_index:
                    if fnmatch.fnmatch(label, pattern):
                        covered.add(label)
                        break
        return [l for l in snap_labels if l not in covered]

    def propose_coin(self, name: str, domain: str, meaning: str, earn_by: str,
                     label_patterns: List[str], proposed_by: str = "") -> dict:
        """Propose a new coin. Returns a proposal for governance review."""
        return {
            "name": name, "domain": domain, "meaning": meaning,
            "earn_by": earn_by, "label_patterns": label_patterns,
            "confidence": "EMBRYONIC", "proposed_by": proposed_by,
            "proposed_at": time.time(), "status": "proposed",
        }

    def summary(self) -> dict:
        by_confidence = {}
        for name, defn in self.coins.items():
            conf = defn.get("confidence", "UNKNOWN")
            by_confidence.setdefault(conf, []).append(name)
        return {
            "total_coins": len(self.coins),
            "by_confidence": {k: len(v) for k, v in by_confidence.items()},
            "indexed_labels": len(self._label_index),
            "patterns": len(self._pattern_index),
        }


class MintService:
    """Mint/burn/reward service for token operations.

    Wave 0.3: ``governance`` parameter is now optional. Per the user's
    2026-05-17 decision: "just let the main governance handle that and
    drop the stale needs." When ``governance=None`` (the new default),
    MintService skips invariant registration + boundary-event recording
    + operation validation — receipts still flow through the unified
    receipt port via ``BoundaryEvent.generate_receipt`` (Wave 0.4).

    Existing callers that pass a governance instance still work — the
    governance-side effects (audit_trail, invariants) keep running for
    backwards compatibility.
    """

    def __init__(self, governance: GeometricGovernance | None = None, wallet=None,
                 coin_library: CoinLibrary = None):
        self.governance = governance
        self.wallet = wallet
        self.coin_library = coin_library or CoinLibrary()
        self.economics = TokenEconomics()
        self.mint_log: List[Dict[str, Any]] = []
        self._invariant_token = "total_supply_invariant"
        self._coin_state: Dict[str, Dict] = {}
        self._escrow_balance: float = 0.0
        self._receipt_chain: str = "0" * 32

        if self.governance is not None:
            self.governance.register_invariant(
                self._invariant_token,
                QuadraticInvariant(value=1.0, tolerance=1e-6)
            )

    def mint_tokens(self, expert_id: str, amount: float = None,
                    reason: str = "expert_creation",
                    identity_label: str = None,
                    governance_event_id: str = None) -> Dict[str, Any]:
        mint_amount = amount or self.economics.mint_bonus
        wallet = self.wallet.get_wallet(expert_id)
        is_new = wallet is None

        if is_new:
            self.wallet.create_wallet(
                expert_id, identity_label=identity_label,
                initial_balance=mint_amount
            )
        else:
            self.wallet.adjust_balance(
                expert_id, mint_amount, "mint",
                memo=f"Mint: {reason}", governance_event_id=governance_event_id,
            )

        event = BoundaryEvent(
            event_id=f"mint_{expert_id}_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            entropy_delta=mint_amount * 0.01,
            receipt_data={
                "expert_id": expert_id,
                "amount": mint_amount,
                "reason": reason,
                "is_new_expert": is_new,
            },
            boundary_type="token_mint",
        )
        receipt = event.generate_receipt()
        if self.governance is not None:
            self.governance.record_boundary_event(event)

        self.mint_log.append({
            "expert_id": expert_id,
            "amount": mint_amount,
            "reason": reason,
            "receipt": receipt,
            "timestamp": time.time(),
        })

        if self.governance is not None:
            self.governance.validate_operation(
                "mint_tokens",
                {self._invariant_token: 1.0},
            )

        logger.info("Minted %.2f tokens for %s (reason=%s)", mint_amount, expert_id, reason)
        return {
            "expert_id": expert_id,
            "amount": mint_amount,
            "reason": reason,
            "receipt": receipt,
            "is_new_expert": is_new,
        }

    def burn_tokens(self, expert_id: str, amount: float,
                    reason: str = "expert_retirement",
                    governance_event_id: str = None) -> Dict[str, Any]:
        balance = self.wallet.get_balance(expert_id)
        burn_amount = min(amount, balance)
        penalty = burn_amount * self.economics.burn_penalty_rate
        net_burn = burn_amount - penalty

        self.wallet.adjust_balance(
            expert_id, -net_burn, "burn",
            memo=f"Burn: {reason} (penalty={penalty:.2f})",
            governance_event_id=governance_event_id,
        )

        event = BoundaryEvent(
            event_id=f"burn_{expert_id}_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            entropy_delta=-burn_amount * 0.01,
            receipt_data={
                "expert_id": expert_id,
                "amount": burn_amount,
                "penalty": penalty,
                "net_burn": net_burn,
                "reason": reason,
            },
            boundary_type="token_burn",
        )
        receipt = event.generate_receipt()
        if self.governance is not None:
            self.governance.record_boundary_event(event)

        self.mint_log.append({
            "expert_id": expert_id,
            "amount": -net_burn,
            "penalty": penalty,
            "reason": reason,
            "receipt": receipt,
            "timestamp": time.time(),
        })

        logger.info("Burned %.2f tokens for %s (reason=%s)", net_burn, expert_id, reason)
        return {
            "expert_id": expert_id,
            "amount_burned": net_burn,
            "penalty": penalty,
            "reason": reason,
            "receipt": receipt,
        }

    def reward_expert(self, expert_id: str, reward_type: str,
                      quality_score: float = 1.0) -> Dict[str, Any]:
        reward_map = {
            "composition": self.economics.reward_per_composition,
            "discovery": self.economics.reward_per_discovery,
            "operation": self.economics.reward_rate,
        }
        base = reward_map.get(reward_type, self.economics.reward_rate)
        amount = base * quality_score
        tx = self.wallet.adjust_balance(
            expert_id, amount, "earn",
            memo=f"Reward: {reward_type} (quality={quality_score:.2f})",
        )
        event = BoundaryEvent(
            event_id=f"reward_{expert_id}_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            entropy_delta=amount * 0.005,
            receipt_data={
                "expert_id": expert_id,
                "amount": amount,
                "reward_type": reward_type,
                "quality_score": quality_score,
            },
            boundary_type="token_reward",
        )
        receipt = event.generate_receipt()
        if self.governance is not None:
            self.governance.record_boundary_event(event)

        logger.info("Rewarded %.2f tokens to %s (type=%s)", amount, expert_id, reward_type)
        return {
            "expert_id": expert_id,
            "amount": amount,
            "reward_type": reward_type,
            "quality_score": quality_score,
            "tx_id": tx.tx_id,
            "receipt": receipt,
        }

    def set_economics(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self.economics, key):
                setattr(self.economics, key, value)
        logger.info("Token economics updated: %s", kwargs)

    def get_economics(self) -> Dict[str, Any]:
        return {
            "reward_rate": self.economics.reward_rate,
            "mint_bonus": self.economics.mint_bonus,
            "min_spending_limit": self.economics.min_spending_limit,
            "max_spending_limit": self.economics.max_spending_limit,
            "default_daily_limit": self.economics.default_daily_limit,
            "burn_penalty_rate": self.economics.burn_penalty_rate,
            "reward_per_composition": self.economics.reward_per_composition,
            "reward_per_discovery": self.economics.reward_per_discovery,
            "coupling": self.economics.coupling,
            "escrow_rate": self.economics.escrow_rate,
            "citation_threshold": self.economics.citation_threshold,
            "max_boost": self.economics.max_boost,
            "sat_denominator": self.economics.sat_denominator,
        }

    def get_mint_history(self, expert_id: str = None,
                         limit: int = 50) -> List[Dict[str, Any]]:
        if expert_id:
            return [m for m in self.mint_log if m["expert_id"] == expert_id][-limit:]
        return self.mint_log[-limit:]

    def get_mint_log_size(self) -> int:
        return len(self.mint_log)

    # ── TMN2 Integration: Label-based minting ─────────────────────

    def mint_from_labels(self, agent_id: str, snap_labels: List[str],
                         quality: float = 0.5, source: str = "",
                         epoch: int = 0) -> Dict[str, Any]:
        """Mint coins from SNAP labels using the coin library.
        Every matching coin gets credited. Everything earns MERIT at minimum."""
        if not snap_labels:
            return {"minted": [], "total_value": 0, "note": "no labels provided"}

        matches = self.coin_library.match_labels(snap_labels)
        minted = []
        total_value = 0.0
        econ = self.economics

        for coin_name, matched_labels in matches.items():
            self._init_coin(coin_name)
            coin = self._coin_state[coin_name]

            label_factor = min(len(matched_labels) / 5.0, 2.0)
            base_amount = quality * econ.coupling * label_factor
            weighted = base_amount * econ.shell_weights[coin.get("shell", 0)]

            if coin["citations"] >= econ.citation_threshold:
                boost = min(math.log(coin["citations"] / econ.citation_threshold), econ.max_boost)
                weighted *= (1 + boost)

            escrow_fee = weighted * econ.escrow_rate
            net = weighted - escrow_fee
            self._escrow_balance += escrow_fee

            self.wallet.adjust_balance(
                agent_id, net, "earn",
                memo=f"Mint: {coin_name} from labels (epoch={epoch})",
            )

            coin["mint_count"] += 1
            coin["saturation"] = coin["mint_count"] / econ.sat_denominator

            total_value += net
            minted.append({
                "coin": coin_name, "amount": round(net, 6),
                "shell": coin["shell"], "matched_labels": len(matched_labels),
            })

        receipt = self._receipt("mint", {
            "agent": agent_id, "coins": len(minted),
            "value": round(total_value, 6), "epoch": epoch,
        })

        uncovered = self.coin_library.find_uncovered(snap_labels)

        self.mint_log.append({
            "agent_id": agent_id, "minted": len(minted),
            "total_value": total_value, "source": source,
            "epoch": epoch, "timestamp": time.time(),
        })

        return {
            "minted": sorted(minted, key=lambda x: x["amount"], reverse=True),
            "total_value": round(total_value, 6),
            "coins_earned": len(minted),
            "labels_processed": len(snap_labels),
            "uncovered_labels": len(uncovered),
            "receipt": receipt,
        }

    def mint_direct(self, agent_id: str, coin_type: str, amount: float,
                    source: str = "") -> Dict[str, Any]:
        """Direct mint — for bootstrap wallets, bounty rewards, etc."""
        self._init_coin(coin_type)
        coin = self._coin_state[coin_type]

        escrow_fee = amount * self.economics.escrow_rate
        net = amount - escrow_fee
        self._escrow_balance += escrow_fee

        self.wallet.adjust_balance(
            agent_id, net, "earn",
            memo=f"Direct mint: {coin_type} ({source})",
        )

        coin["mint_count"] += 1
        coin["saturation"] = coin["mint_count"] / self.economics.sat_denominator

        receipt = self._receipt("mint_direct", {"agent": agent_id, "coin": coin_type, "amount": net})
        return {
            "coin": coin_type, "amount": round(net, 6),
            "shell": coin["shell"], "receipt": receipt,
        }

    # ── TMN2 Integration: Governance pipeline ─────────────────────

    def propose_coin(self, name: str, domain: str, meaning: str, earn_by: str,
                     label_patterns: List[str] = None,
                     proposed_by: str = "") -> Dict[str, Any]:
        """Propose a new coin. Returns a proposal for governance review."""
        name_upper = name.upper()
        if name_upper in self.coin_library.coins:
            return {"error": f"Coin {name_upper} already exists"}
        return self.coin_library.propose_coin(
            name_upper, domain, meaning, earn_by,
            label_patterns or [], proposed_by,
        )

    def register_coin(self, name: str, domain: str, meaning: str, earn_by: str,
                      label_patterns: List[str] = None,
                      proposed_by: str = "") -> Dict[str, Any]:
        """Register an approved coin in the library."""
        name_upper = name.upper()
        if name_upper in self.coin_library.coins:
            return {"error": f"Coin {name_upper} already exists"}

        defn = {
            "domain": domain, "meaning": meaning, "earn_by": earn_by,
            "confidence": "EMERGING", "label_patterns": label_patterns or [],
            "registered_by": proposed_by, "registered_at": time.time(),
        }
        self.coin_library.register_coin(name_upper, defn)
        self._init_coin(name_upper, 0)
        receipt = self._receipt("coin_registered", {"name": name_upper, "domain": domain})
        logger.info("NEW COIN REGISTERED: %s — %s", name_upper, domain)
        return {
            "name": name_upper, "status": "registered",
            "receipt": receipt, "library_size": len(self.coin_library.coins),
        }

    # ── TMN2 Integration: Ticker & market data ───────────────────

    def ticker(self) -> List[Dict[str, Any]]:
        """Exchange rate / ticker for all coins."""
        coins = []
        for name, state in sorted(self._coin_state.items()):
            supply = state["mint_count"]
            exchange_rate = 1.0 / (1.0 + supply / 100.0)
            value = (state["weight"] * exchange_rate *
                     math.log(state["citations"] + 2) / (1 + state["saturation"]))
            coins.append({
                "coin": name, "shell": state["shell"], "supply": supply,
                "saturation": round(state["saturation"], 3),
                "ticker_value": round(value, 6),
                "confidence": self.coin_library.coins.get(name, {}).get("confidence", "UNKNOWN"),
            })
        return coins

    # ── TMN2 Integration: Status queries ──────────────────────────

    def get_escrow_balance(self) -> float:
        return round(self._escrow_balance, 4)

    def get_coin_state(self, coin_name: str = None) -> Dict[str, Any]:
        if coin_name:
            return self._coin_state.get(coin_name.upper(), {})
        return dict(self._coin_state)

    def get_coin_library(self) -> CoinLibrary:
        return self.coin_library

    # ── Internal helpers ──────────────────────────────────────────

    def _init_coin(self, name: str, shell: int = 0):
        if name not in self._coin_state:
            self._coin_state[name] = {
                "name": name, "shell": shell, "mint_count": 0,
                "citations": 0, "saturation": 0.0,
                "weight": self.economics.shell_weights[shell] if shell < len(self.economics.shell_weights) else 0.125,
            }

    def _receipt(self, op: str, data: dict) -> str:
        payload = json.dumps({
            "op": op, "data": data,
            "prev": self._receipt_chain, "ts": time.time(),
        }, sort_keys=True, default=str)
        self._receipt_chain = hashlib.sha256(payload.encode()).hexdigest()[:32]
        return self._receipt_chain
