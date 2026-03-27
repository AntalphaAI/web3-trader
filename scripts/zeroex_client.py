#!/usr/bin/env python3
"""
Antalpha AI Client - DEX Aggregator powered by Antalpha AI
Docs: https://docs.0x.org/swap-api/quickstart

Endpoint: GET https://api.0x.org/swap/allowance-holder/{price|quote}
Headers: 0x-api-key, 0x-version: v2
"""

import os
import json
import requests
from typing import Optional, Dict, Any

# Token addresses (Ethereum Mainnet)
TOKENS = {
    "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "DAI": "0x6b175474e89094c44da98b954eedeac495271d0f",
    "ETH": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    "LINK": "0x514910771af9ca656af840dff83e8264ecf986ca",
    "UNI": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
}

# ETH native token must be swapped as WETH on 0x API
ETH_NATIVE = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"

CHAIN_IDS = {
    "ethereum": 1,
}

# Default taker address for price queries (dummy address)
DEFAULT_TAKER = "0x70a9f34f9b34c64957b9c401a97bfed35b95049e"


class ZeroExClient:
    def __init__(self, api_key: str, chain_id: int = 1):
        self.api_key = api_key
        self.chain_id = chain_id
        # Antalpha AI - DEX Aggregator endpoint
        # Using allowance-holder mode: native ETH sells include value in tx
        # This produces cleaner EIP-681 links than permit2 mode
        self.base_url = "https://api.0x.org/swap/allowance-holder"
        self.session = requests.Session()
        self.session.headers.update({
            "0x-api-key": api_key,
            "0x-version": "v2",
            "Accept": "application/json",
        })
    
    def _resolve_token(self, symbol: str) -> str:
        """Resolve token symbol to address.
        
        allowance-holder mode: native ETH address is accepted directly.
        This allows the API to return proper value field for ETH sells.
        """
        symbol = symbol.upper()
        if symbol not in TOKENS:
            raise ValueError(f"Unsupported token: {symbol}. Supported: {list(TOKENS.keys())}")
        return TOKENS[symbol]
    
    def get_token_address(self, symbol: str) -> str:
        """Get token address by symbol (original, not resolved)"""
        symbol = symbol.upper()
        if symbol not in TOKENS:
            raise ValueError(f"Unsupported token: {symbol}. Supported: {list(TOKENS.keys())}")
        return TOKENS[symbol]
    
    def get_price(self, from_token: str, to_token: str, amount: float,
                  taker: Optional[str] = None) -> Dict[str, Any]:
        """
        Get indicative price for a swap.
        
        Args:
            from_token: Source token symbol (e.g., "USDT")
            to_token: Target token symbol (e.g., "ETH")
            amount: Amount of source token (human readable, e.g., 1000)
            taker: Optional taker wallet address
            
        Returns:
            Price info including buyAmount, gas, route
        """
        sell_address = self._resolve_token(from_token)
        buy_address = self._resolve_token(to_token)
        
        from_decimals = self._get_decimals(from_token)
        sell_amount = int(amount * (10 ** from_decimals))
        
        # GET request with query parameters
        params = {
            "chainId": self.chain_id,
            "sellToken": sell_address,
            "buyToken": buy_address,
            "sellAmount": str(sell_amount),
            "taker": taker or DEFAULT_TAKER,
        }
        
        response = self.session.get(f"{self.base_url}/price", params=params)
        response.raise_for_status()
        data = response.json()
        
        to_decimals = self._get_decimals(to_token)
        buy_amount = float(data["buyAmount"]) / (10 ** to_decimals)
        price = buy_amount / amount if amount > 0 else 0
        
        return {
            "from_token": from_token.upper(),
            "to_token": to_token.upper(),
            "from_amount": amount,
            "to_amount": buy_amount,
            "price": price,
            "gas": int(data.get("gas", 0)),
            "gas_price_wei": data.get("gasPrice", "0"),
            "route": data.get("route", {}),
            "fees": data.get("fees", {}),
            "liquidity_available": data.get("liquidityAvailable", False),
            "min_buy_amount": float(data.get("minBuyAmount", 0)) / (10 ** to_decimals),
            "raw": data,
        }
    
    def get_quote(self, from_token: str, to_token: str, amount: float, 
                  taker: Optional[str] = None) -> Dict[str, Any]:
        """
        Get firm quote with transaction data for a swap.
        
        Args:
            from_token: Source token symbol
            to_token: Target token symbol
            amount: Amount of source token (human readable)
            taker: Taker wallet address (required for quote)
            
        Returns:
            Full quote including transaction data
        """
        sell_address = self._resolve_token(from_token)
        buy_address = self._resolve_token(to_token)
        
        from_decimals = self._get_decimals(from_token)
        sell_amount = int(amount * (10 ** from_decimals))
        
        if not taker:
            raise ValueError("taker (wallet address) is required for quote")
        
        # GET request with query parameters
        params = {
            "chainId": self.chain_id,
            "sellToken": sell_address,
            "buyToken": buy_address,
            "sellAmount": str(sell_amount),
            "taker": taker,
        }
        
        response = self.session.get(f"{self.base_url}/quote", params=params)
        response.raise_for_status()
        data = response.json()
        
        to_decimals = self._get_decimals(to_token)
        buy_amount = float(data["buyAmount"]) / (10 ** to_decimals)
        price = buy_amount / amount if amount > 0 else 0
        
        # Extract transaction data
        tx = data.get("transaction", {})
        
        return {
            "from_token": from_token.upper(),
            "to_token": to_token.upper(),
            "from_amount": amount,
            "to_amount": buy_amount,
            "price": price,
            "min_buy_amount": float(data.get("minBuyAmount", 0)) / (10 ** to_decimals),
            "gas": int(tx.get("gas", data.get("gas", 0))),
            "gas_price_wei": tx.get("gasPrice", data.get("gasPrice", "0")),
            "tx": {
                "to": tx.get("to", ""),
                "data": tx.get("data", ""),
                "value": tx.get("value", "0"),
                "gas": int(tx.get("gas", 0)),
                "gasPrice": tx.get("gasPrice", "0"),
            },
            "route": data.get("route", {}),
            "fees": data.get("fees", {}),
            "liquidity_available": data.get("liquidityAvailable", False),
            "raw": data,
        }
    
    def get_gas_info(self) -> Dict[str, Any]:
        """Get current gas prices by querying a price endpoint"""
        try:
            # Use a simple price query to get gas info
            params = {
                "chainId": self.chain_id,
                "sellToken": TOKENS["USDC"],
                "buyToken": TOKENS["WETH"],
                "sellAmount": "1000000",  # 1 USDC
                "taker": DEFAULT_TAKER,
            }
            response = self.session.get(f"{self.base_url}/price", params=params)
            response.raise_for_status()
            data = response.json()
            gas_price = int(data.get("gasPrice", 0))
            return {
                "gas_price_wei": gas_price,
                "gas_price_gwei": gas_price / 1e9,
                "estimated_gas": int(data.get("gas", 0)),
            }
        except Exception:
            return {
                "gas_price_wei": 0,
                "gas_price_gwei": 0,
                "estimated_gas": 0,
                "error": "Failed to fetch gas info",
            }
    
    def _get_decimals(self, token: str) -> int:
        """Get token decimals by symbol"""
        decimals_map = {
            "USDT": 6,
            "USDC": 6,
            "DAI": 18,
            "ETH": 18,
            "WETH": 18,
            "WBTC": 8,
            "LINK": 18,
            "UNI": 18,
        }
        return decimals_map.get(token.upper(), 18)


def load_config() -> Dict[str, Any]:
    """Load user configuration"""
    import yaml
    
    config_paths = [
        os.path.expanduser("~/.web3-trader/config.yaml"),
        "references/config.yaml",
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                return yaml.safe_load(f)
    
    raise FileNotFoundError(
        "Config not found. Copy references/config.example.yaml to ~/.web3-trader/config.yaml"
    )


def create_client() -> ZeroExClient:
    """Create ZeroExClient from user config"""
    config = load_config()
    api_key = config.get("api_keys", {}).get("zeroex")
    
    if not api_key or api_key == "YOUR_0X_API_KEY":
        raise ValueError(
            "Missing Antalpha AI API key. Set it in ~/.web3-trader/config.yaml\n"
            "Get your key from https://dashboard.0x.org"
        )
    
    chain_name = config.get("chains", {}).get("default", "ethereum")
    chain_id = CHAIN_IDS.get(chain_name, 1)
    
    return ZeroExClient(api_key=api_key, chain_id=chain_id)
