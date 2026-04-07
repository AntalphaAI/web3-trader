#!/usr/bin/env python3
"""
Tests for Hyperliquid client - read-only operations (no private key needed).
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from hl_client import HyperliquidClient, create_client


def test_price():
    """Test getting a single price."""
    client = create_client()
    price = client.get_price("ETH")
    assert price is not None, "ETH price should not be None"
    assert price > 0, f"ETH price should be positive, got {price}"
    print(f"✅ ETH price: ${price:,.2f}")


def test_all_mids():
    """Test getting all mid prices."""
    client = create_client()
    mids = client.get_all_mids()
    assert isinstance(mids, dict), "allMids should return a dict"
    assert "BTC" in mids, "BTC should be in mids"
    assert "ETH" in mids, "ETH should be in mids"
    print(f"✅ allMids: {len(mids)} coins")


def test_perp_meta():
    """Test getting perpetual metadata."""
    client = create_client()
    meta = client.get_perp_meta()
    assert "universe" in meta, "meta should contain 'universe'"
    assert len(meta["universe"]) > 100, f"Should have >100 perp assets, got {len(meta['universe'])}"
    btc = meta["universe"][0]
    assert btc["name"] == "BTC", "First asset should be BTC"
    assert int(btc["maxLeverage"]) == 40, "BTC max leverage should be 40"
    print(f"✅ Perp meta: {len(meta['universe'])} assets")


def test_spot_meta():
    """Test getting spot metadata."""
    client = create_client()
    spot = client.get_spot_meta()
    assert "tokens" in spot, "spotMeta should contain 'tokens'"
    assert len(spot["tokens"]) > 50, f"Should have >50 spot tokens, got {len(spot['tokens'])}"
    print(f"✅ Spot meta: {len(spot['tokens'])} tokens")


def test_l2_book():
    """Test getting order book."""
    client = create_client()
    book = client.get_l2_book("ETH")
    assert "levels" in book, "l2Book should contain 'levels'"
    assert len(book["levels"]) == 2, "Should have bids and asks"
    assert len(book["levels"][0]) > 0, "Should have bids"
    assert len(book["levels"][1]) > 0, "Should have asks"
    best_bid = float(book["levels"][0][0]["px"])
    best_ask = float(book["levels"][1][0]["px"])
    assert best_bid < best_ask, f"Bid ({best_bid}) should be < ask ({best_ask})"
    print(f"✅ ETH book: bid={best_bid}, ask={best_ask}, spread={best_ask-best_bid:.2f}")


def test_user_state():
    """Test getting user state (perp account)."""
    client = create_client()
    # Use a known address (Dean's)
    state = client.get_user_state("0x81f9c401B0821B6E0a16BC7B1dF0F647F36211Dd")
    assert "marginSummary" in state, "Should contain marginSummary"
    assert "assetPositions" in state, "Should contain assetPositions"
    print(f"✅ User state: accountValue={state['marginSummary']['accountValue']}")


def test_spot_state():
    """Test getting spot account state."""
    client = create_client()
    state = client.get_spot_state("0x81f9c401B0821B6E0a16BC7B1dF0F647F36211Dd")
    assert "balances" in state, "Should contain balances"
    print(f"✅ Spot state: {len(state['balances'])} balances")


def test_open_orders():
    """Test getting open orders."""
    client = create_client()
    orders = client.get_open_orders("0x81f9c401B0821B6E0a16BC7B1dF0F647F36211Dd")
    assert isinstance(orders, list), "Should return a list"
    print(f"✅ Open orders: {len(orders)}")


def test_user_fills():
    """Test getting user fills."""
    client = create_client()
    fills = client.get_user_fills("0x81f9c401B0821B6E0a16BC7B1dF0F647F36211Dd")
    assert isinstance(fills, list), "Should return a list"
    print(f"✅ User fills: {len(fills)}")


def test_funding_rates():
    """Test getting funding rates."""
    client = create_client()
    meta, ctxs = client.get_perp_meta_and_contexts()
    assert len(ctxs) > 0, "Should have asset contexts"
    assert "funding" in ctxs[0], "Should have funding rate"
    print(f"✅ Funding rates: {len(ctxs)} assets")


def test_account_summary():
    """Test the account summary helper."""
    client = create_client()
    summary = client.get_account_summary("0x81f9c401B0821B6E0a16BC7B1dF0F647F36211Dd")
    assert "perp" in summary
    assert "positions" in summary
    assert "spot_balances" in summary
    assert "open_orders_count" in summary
    print(f"✅ Account summary: OK")


def test_asset_index():
    """Test asset index lookup."""
    client = create_client()
    btc_idx = client.get_asset_index("BTC")
    eth_idx = client.get_asset_index("ETH")
    assert btc_idx == 0, f"BTC should be index 0, got {btc_idx}"
    assert eth_idx == 1, f"ETH should be index 1, got {eth_idx}"
    print(f"✅ Asset index: BTC={btc_idx}, ETH={eth_idx}")


if __name__ == "__main__":
    tests = [
        test_price,
        test_all_mids,
        test_perp_meta,
        test_spot_meta,
        test_l2_book,
        test_user_state,
        test_spot_state,
        test_open_orders,
        test_user_fills,
        test_funding_rates,
        test_account_summary,
        test_asset_index,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("🎉 All tests passed!")
    sys.exit(1 if failed > 0 else 0)
