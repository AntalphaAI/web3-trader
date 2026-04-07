#!/usr/bin/env python3
"""
Hyperliquid Client - CLOB Trading for AI Agents

Supports two signing modes:
  1. Agent Wallet (recommended) — agent key signs on behalf of owner
  2. Direct key — private key signs directly

Usage:
    from hl_client import HyperliquidClient, create_client

    # Read-only
    client = HyperliquidClient()

    # Agent wallet mode (recommended for production)
    client = HyperliquidClient(
        private_key="0xAgentKey...",
        account_address="0xOwnerAddress..."
    )

    # Direct key mode
    client = HyperliquidClient(private_key="0xPrivateKey...")
"""

import json
import time
import math
import requests
from typing import Optional, List, Dict, Any, Tuple

# ── Constants ────────────────────────────────────────────────────────

MAINNET_API = "https://api.hyperliquid.xyz"
TESTNET_API = "https://api.hyperliquid-testnet.xyz"

TIF_GTC = "Gtc"    # Good-til-Cancel
TIF_IOC = "Ioc"    # Immediate-or-Cancel
TIF_ALO = "Alo"    # Add-Liquidity-Only (post-only)

# Minimum order value on Hyperliquid
MIN_ORDER_VALUE_USD = 10.0


# ── Client ───────────────────────────────────────────────────────────

class HyperliquidClient:
    """
    Hyperliquid API client with agent wallet support.

    Read-only operations work without any key.
    Write operations require private_key.
    For agent mode, also set account_address to the owner's address.

    Agent wallets can: place/cancel/modify orders, set leverage, set TP/SL.
    Agent wallets CANNOT: transfer funds (usdClassTransfer), withdraw, or send assets.
    """

    def __init__(
        self,
        testnet: bool = False,
        private_key: Optional[str] = None,
        account_address: Optional[str] = None,
        vault_address: Optional[str] = None,
    ):
        self.base_url = TESTNET_API if testnet else MAINNET_API
        self.testnet = testnet
        self.private_key = private_key
        self.account_address = account_address  # Owner address for agent mode
        self.vault_address = vault_address
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        # SDK exchange object (lazy-initialized)
        self._exchange = None

        # Metadata caches
        self._perp_meta: Optional[Dict] = None
        self._spot_meta: Optional[Dict] = None

    def _get_exchange(self):
        """Get or create the SDK Exchange object."""
        if self._exchange is not None:
            return self._exchange

        if self.private_key is None:
            raise RuntimeError(
                "Write operations require a private key. "
                "Set private_key (agent key or direct key) on the client."
            )

        from hyperliquid.exchange import Exchange
        from hyperliquid.utils import constants
        from eth_account import Account

        wallet = Account.from_key(self.private_key)
        api_url = constants.TESTNET_API_URL if self.testnet else constants.MAINNET_API_URL

        self._exchange = Exchange(
            wallet,
            api_url,
            account_address=self.account_address,
            vault_address=self.vault_address,
        )
        return self._exchange

    @property
    def is_agent_mode(self) -> bool:
        """True if running in agent wallet mode."""
        return self.account_address is not None

    @property
    def effective_address(self) -> Optional[str]:
        """The address whose account is being operated on."""
        if self.account_address:
            return self.account_address
        if self.private_key:
            from eth_account import Account
            return Account.from_key(self.private_key).address
        return None

    # ── Info API (read-only) ─────────────────────────────────────────

    def _info(self, payload: Dict) -> Any:
        """POST /info"""
        resp = self.session.post(f"{self.base_url}/info", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_perp_meta(self) -> Dict:
        if self._perp_meta is None:
            self._perp_meta = self._info({"type": "meta"})
        return self._perp_meta

    def get_spot_meta(self) -> Dict:
        if self._spot_meta is None:
            self._spot_meta = self._info({"type": "spotMeta"})
        return self._spot_meta

    def get_perp_meta_and_contexts(self) -> Tuple[Dict, List[Dict]]:
        result = self._info({"type": "metaAndAssetCtxs"})
        return result[0], result[1]

    def get_asset_index(self, coin: str) -> Optional[int]:
        """Get the index of an asset in the perpetuals universe by coin name."""
        meta = self.get_perp_meta()
        for i, asset in enumerate(meta.get("universe", [])):
            if asset.get("name") == coin:
                return i
        return None

    def get_all_mids(self) -> Dict[str, str]:
        return self._info({"type": "allMids"})

    def get_price(self, coin: str) -> Optional[float]:
        mids = self.get_all_mids()
        if coin in mids:
            return float(mids[coin])
        return None

    def get_l2_book(self, coin: str, n_sig_figs: int = 5) -> Dict:
        return self._info({"type": "l2Book", "coin": coin, "nSigFigs": n_sig_figs})

    def get_user_state(self, address: str) -> Dict:
        return self._info({"type": "clearinghouseState", "user": address})

    def get_spot_state(self, address: str) -> Dict:
        return self._info({"type": "spotClearinghouseState", "user": address})

    def get_open_orders(self, address: str) -> List[Dict]:
        return self._info({"type": "openOrders", "user": address})

    def get_user_fills(self, address: str) -> List[Dict]:
        return self._info({"type": "userFills", "user": address})

    def get_order_status(self, address: str, oid: int) -> Dict:
        return self._info({"type": "orderStatus", "user": address, "oid": oid})

    def get_candles(self, coin: str, interval: str = "1h", lookback: int = 100) -> List[Dict]:
        return self._info({
            "type": "candleSnapshot",
            "req": {"coin": coin, "interval": interval, "startTime": int((time.time() - lookback * 3600) * 1000)}
        })

    # ── Exchange API (requires signing) ──────────────────────────────

    def place_limit_order(
        self,
        coin: str,
        is_buy: bool,
        price: float,
        size: float,
        tif: str = TIF_GTC,
        reduce_only: bool = False,
    ) -> Dict:
        """Place a limit order. Works with both agent and direct keys."""
        exchange = self._get_exchange()
        order_type = {"limit": {"tif": tif}}
        return exchange.order(coin, is_buy, size, price, order_type, reduce_only=reduce_only)

    def place_market_order(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        slippage: float = 0.01,
    ) -> Dict:
        """Place a market order (aggressive limit with slippage)."""
        exchange = self._get_exchange()
        return exchange.market_open(coin, is_buy, size, slippage=slippage)

    def close_position(
        self,
        coin: str,
        slippage: float = 0.01,
    ) -> Dict:
        """Close an existing position at market price."""
        exchange = self._get_exchange()
        return exchange.market_close(coin, slippage=slippage)

    def cancel_order(self, coin: str, oid: int) -> Dict:
        exchange = self._get_exchange()
        return exchange.cancel(coin, oid)

    def cancel_order_by_cloid(self, coin: str, cloid: str) -> Dict:
        exchange = self._get_exchange()
        return exchange.cancel_by_cloid(coin, cloid)

    def modify_order(
        self,
        coin: str,
        oid: int,
        is_buy: bool,
        price: float,
        size: float,
        tif: str = TIF_GTC,
    ) -> Dict:
        """Atomically modify an existing order."""
        exchange = self._get_exchange()
        order_type = {"limit": {"tif": tif}}
        return exchange.modify_order(oid, coin, is_buy, size, price, order_type)

    def update_leverage(
        self,
        coin: str,
        leverage: int,
        is_cross: bool = True,
    ) -> Dict:
        exchange = self._get_exchange()
        return exchange.update_leverage(leverage, coin, is_cross)

    def update_isolated_margin(self, coin: str, amount: float) -> Dict:
        exchange = self._get_exchange()
        return exchange.update_isolated_margin(amount, coin)

    def place_trigger_order(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        trigger_px: float,
        tpsl: str = "tp",
    ) -> Dict:
        """Place a take-profit or stop-loss trigger order."""
        exchange = self._get_exchange()
        trigger = {"triggerPx": str(trigger_px), "isMarket": True, "tpsl": tpsl}
        order_type_obj = {"trigger": trigger}
        return exchange.order(coin, is_buy, size, trigger_px, order_type_obj, reduce_only=True)

    def usd_class_transfer(self, amount: float, to_perp: bool = True) -> Dict:
        """
        Transfer USDC between spot and perp.
        ⚠️ NOT available in agent mode — requires owner's direct signature.
        """
        if self.is_agent_mode:
            raise RuntimeError(
                "usdClassTransfer requires the owner's direct signature. "
                "Agent wallets cannot perform fund transfers. "
                "Use the browser transfer page instead."
            )
        exchange = self._get_exchange()
        return exchange.usd_class_transfer(amount, to_perp)

    # ── Convenience ──────────────────────────────────────────────────

    def get_account_summary(self, address: str) -> Dict:
        """Comprehensive account summary."""
        perp_state = self.get_user_state(address)
        spot_state = self.get_spot_state(address)
        open_orders = self.get_open_orders(address)

        margin = perp_state.get("marginSummary", {})
        positions = [
            p["position"] for p in perp_state.get("assetPositions", [])
            if float(p["position"].get("szi", "0")) != 0
        ]

        return {
            "perp": {
                "account_value": margin.get("accountValue", "0"),
                "total_margin_used": margin.get("totalMarginUsed", "0"),
                "total_ntl_pos": margin.get("totalNtlPos", "0"),
                "total_raw_usd": margin.get("totalRawUsd", "0"),
                "withdrawable": perp_state.get("withdrawable", "0"),
            },
            "positions": [
                {
                    "coin": p.get("coin"),
                    "size": p.get("szi"),
                    "entry_price": p.get("entryPx"),
                    "unrealized_pnl": p.get("unrealizedPnl"),
                    "leverage": p.get("leverage", {}).get("value"),
                    "liquidation_px": p.get("liquidationPx"),
                    "margin_used": p.get("marginUsed"),
                }
                for p in positions
            ],
            "spot_balances": [
                b for b in spot_state.get("balances", [])
                if float(b.get("total", "0")) > 0
            ],
            "open_orders_count": len(open_orders),
            "open_orders": open_orders[:10],
        }

    def format_account_summary(self, address: str) -> str:
        summary = self.get_account_summary(address)
        perp = summary["perp"]

        lines = [
            f"💰 Account Summary for {address[:10]}...",
            f"",
            f"📊 Perp Account:",
            f"   Account Value: ${float(perp['account_value']):,.2f}",
            f"   Margin Used: ${float(perp['total_margin_used']):,.2f}",
            f"   Withdrawable: ${float(perp['withdrawable']):,.2f}",
        ]

        if summary["positions"]:
            lines.append(f"\n📈 Open Positions ({len(summary['positions'])}):")
            for pos in summary["positions"]:
                direction = "LONG" if float(pos["size"]) > 0 else "SHORT"
                pnl = float(pos["unrealized_pnl"]) if pos["unrealized_pnl"] else 0
                pnl_emoji = "🟢" if pnl >= 0 else "🔴"
                lines.append(
                    f"   {pos['coin']} {direction} | Size: {pos['size']} | "
                    f"Entry: ${float(pos['entry_price']):,.2f} | "
                    f"{pnl_emoji} PnL: ${pnl:,.2f}"
                )
                if pos.get("liquidation_px"):
                    lines.append(f"      ⚠️ Liq Price: ${float(pos['liquidation_px']):,.2f}")
        else:
            lines.append("\n📈 No open positions")

        if summary["spot_balances"]:
            lines.append(f"\n🪙 Spot Balances:")
            for bal in summary["spot_balances"]:
                lines.append(f"   {bal.get('coin', '?')}: {bal['total']}")

        lines.append(f"\n📋 Open Orders: {summary['open_orders_count']}")
        for order in summary.get("open_orders", [])[:5]:
            side = "BUY" if order.get("side") == "B" else "SELL"
            lines.append(
                f"   {order.get('coin')} {side} | "
                f"Price: {order.get('limitPx')} | Size: {order.get('sz')}"
            )

        return "\n".join(lines)


# ── Module-level convenience ─────────────────────────────────────────

def create_client(
    testnet: bool = False,
    private_key: Optional[str] = None,
    account_address: Optional[str] = None,
) -> HyperliquidClient:
    """
    Create a HyperliquidClient.

    Reads from environment if not provided:
      - HL_PRIVATE_KEY: agent key or direct key
      - HL_ACCOUNT_ADDRESS: owner address (enables agent mode)
    """
    import os
    if private_key is None:
        private_key = os.environ.get("HL_PRIVATE_KEY")
    if account_address is None:
        account_address = os.environ.get("HL_ACCOUNT_ADDRESS")
    return HyperliquidClient(
        testnet=testnet,
        private_key=private_key,
        account_address=account_address,
    )
