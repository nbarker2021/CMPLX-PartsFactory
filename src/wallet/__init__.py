"""Expert Wallet & Mint Service — Economic layer for expert operations."""

from .wallet import ExpertWallet
from .mint import MintService, TokenEconomics, CoinLibrary
from .economy import EconomyService, StakingPool, ExpertListing
from .receipts import ReceiptLedger

wallet = ExpertWallet()
try:
    wallet.connect()
except Exception:
    pass
