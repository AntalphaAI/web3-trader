#!/usr/bin/env python3
"""
Basic tests for ZeroExClient
Run with: python3 -m pytest tests/test_zeroex_client.py -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from zeroex_client import ZeroExClient, TOKENS


class TestTokenAddresses(unittest.TestCase):
    """Test token address lookup"""
    
    def test_known_tokens(self):
        """Test that known tokens have valid addresses"""
        for symbol, address in TOKENS.items():
            self.assertTrue(address.startswith("0x"), f"{symbol} address should start with 0x")
            self.assertEqual(len(address), 42, f"{symbol} address should be 42 chars")
    
    def test_get_token_address(self):
        """Test token address retrieval"""
        client = ZeroExClient(api_key="test_key")
        
        # Test case insensitive
        self.assertEqual(
            client.get_token_address("usdt"),
            client.get_token_address("USDT")
        )
        
        # Test unknown token
        with self.assertRaises(ValueError):
            client.get_token_address("UNKNOWN")


class TestDecimals(unittest.TestCase):
    """Test token decimals"""
    
    def test_token_decimals(self):
        """Test that tokens have correct decimals"""
        client = ZeroExClient(api_key="test_key")
        
        # Stablecoins use 6 decimals
        self.assertEqual(client._get_decimals("USDT"), 6)
        self.assertEqual(client._get_decimals("USDC"), 6)
        
        # ETH and ERC20s use 18
        self.assertEqual(client._get_decimals("ETH"), 18)
        self.assertEqual(client._get_decimals("DAI"), 18)
        
        # WBTC uses 8
        self.assertEqual(client._get_decimals("WBTC"), 8)


class TestIntegration(unittest.TestCase):
    """Integration tests (require valid API key)"""
    
    @unittest.skipIf(not os.environ.get("ZEROEX_API_KEY"), "Requires ZEROEX_API_KEY")
    def test_get_price(self):
        """Test price query"""
        client = ZeroExClient(api_key=os.environ["ZEROEX_API_KEY"])
        result = client.get_price("USDT", "ETH", 1000)
        
        self.assertIn("from_token", result)
        self.assertIn("to_token", result)
        self.assertIn("price", result)
        self.assertGreater(result["price"], 0)
    
    @unittest.skipIf(not os.environ.get("ZEROEX_API_KEY"), "Requires ZEROEX_API_KEY")
    def test_get_quote(self):
        """Test quote with transaction data"""
        client = ZeroExClient(api_key=os.environ["ZEROEX_API_KEY"])
        result = client.get_quote("USDT", "ETH", 100, taker="0x0000000000000000000000000000000000000001")
        
        self.assertIn("tx", result)
        self.assertIn("to", result["tx"])
        self.assertIn("data", result["tx"])
        self.assertTrue(result["tx"]["data"].startswith("0x"))


if __name__ == "__main__":
    unittest.main()
