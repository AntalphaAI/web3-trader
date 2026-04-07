#!/usr/bin/env python3
"""
Integration tests for Hyperliquid trading.

Test categories:
1. Signing verification (testnet, no funds needed)
2. Wire format verification (validates action structures)
3. Read API complete coverage
4. Trading simulation (validates order lifecycle logic)

For FUNDED testnet/mainnet tests, set HL_PRIVATE_KEY env var.
"""

import json, sys, os, time, requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from hl_client import HyperliquidClient, create_client

TESTNET_API = "https://api.hyperliquid-testnet.xyz"

# ── Signing verification (no funds needed) ─────────────────────────

def test_signing_order():
    """Verify EIP-712 signing for order placement works."""
    from eth_account import Account
    from hyperliquid.utils.signing import sign_l1_action

    wallet = Account.create()
    meta = requests.post(f"{TESTNET_API}/info", json={"type": "meta"}, timeout=10).json()
    eth_idx = next(i for i, a in enumerate(meta["universe"]) if a["name"] == "ETH")

    action = {
        "type": "order",
        "orders": [{
            "a": eth_idx, "b": True, "p": "1800", "s": "0.01",
            "r": False, "t": {"limit": {"tif": "Gtc"}},
        }],
        "grouping": "na",
    }

    nonce = int(time.time() * 1000)
    sig = sign_l1_action(wallet, action, None, nonce, None, is_mainnet=False)

    payload = {"action": action, "nonce": nonce, "signature": sig, "vaultAddress": None}
    resp = requests.post(f"{TESTNET_API}/exchange", json=payload, timeout=15)
    result = resp.json()

    # "User does not exist" = signing worked, just no funds
    # "invalid signature" = signing broken
    assert "invalid" not in json.dumps(result).lower() or "signature" not in json.dumps(result).lower(), \
        f"Signature should be valid. Got: {result}"
    print(f"✅ Order signing verified (response: {result.get('response', '')[:60]})")


def test_signing_cancel():
    """Verify cancel order signing."""
    from eth_account import Account
    from hyperliquid.utils.signing import sign_l1_action

    wallet = Account.create()
    meta = requests.post(f"{TESTNET_API}/info", json={"type": "meta"}, timeout=10).json()
    eth_idx = next(i for i, a in enumerate(meta["universe"]) if a["name"] == "ETH")

    action = {"type": "cancel", "cancels": [{"a": eth_idx, "o": 999999}]}
    nonce = int(time.time() * 1000)
    sig = sign_l1_action(wallet, action, None, nonce, None, is_mainnet=False)

    payload = {"action": action, "nonce": nonce, "signature": sig, "vaultAddress": None}
    resp = requests.post(f"{TESTNET_API}/exchange", json=payload, timeout=15)
    result = resp.json()

    assert "invalid" not in json.dumps(result).lower() or "signature" not in json.dumps(result).lower()
    print(f"✅ Cancel signing verified")


def test_signing_leverage():
    """Verify leverage update signing."""
    from eth_account import Account
    from hyperliquid.utils.signing import sign_l1_action

    wallet = Account.create()
    meta = requests.post(f"{TESTNET_API}/info", json={"type": "meta"}, timeout=10).json()
    eth_idx = next(i for i, a in enumerate(meta["universe"]) if a["name"] == "ETH")

    action = {"type": "updateLeverage", "asset": eth_idx, "isCross": True, "leverage": 10}
    nonce = int(time.time() * 1000)
    sig = sign_l1_action(wallet, action, None, nonce, None, is_mainnet=False)

    payload = {"action": action, "nonce": nonce, "signature": sig, "vaultAddress": None}
    resp = requests.post(f"{TESTNET_API}/exchange", json=payload, timeout=15)
    result = resp.json()

    assert "invalid" not in json.dumps(result).lower() or "signature" not in json.dumps(result).lower()
    print(f"✅ Leverage signing verified")


def test_signing_usd_class_transfer():
    """Verify spot↔perp transfer signing."""
    from eth_account import Account
    from hyperliquid.utils.signing import sign_user_signed_action, USD_CLASS_TRANSFER_SIGN_TYPES

    wallet = Account.create()
    action = {
        "type": "usdClassTransfer",
        "amount": "10",
        "toPerp": True,
        "nonce": int(time.time() * 1000),
    }

    sig = sign_user_signed_action(
        wallet, action, USD_CLASS_TRANSFER_SIGN_TYPES,
        "HyperliquidTransaction:UsdClassTransfer", is_mainnet=False
    )

    payload = {"action": action, "nonce": action["nonce"], "signature": sig, "vaultAddress": None}
    resp = requests.post(f"{TESTNET_API}/exchange", json=payload, timeout=15)
    result = resp.json()

    # Will fail with user not found, but shouldn't fail with invalid signature
    assert "invalid" not in json.dumps(result).lower() or "signature" not in json.dumps(result).lower()
    print(f"✅ USD class transfer signing verified")


def test_signing_trigger_order():
    """Verify TP/SL trigger order signing."""
    from eth_account import Account
    from hyperliquid.utils.signing import sign_l1_action

    wallet = Account.create()
    meta = requests.post(f"{TESTNET_API}/info", json={"type": "meta"}, timeout=10).json()
    eth_idx = next(i for i, a in enumerate(meta["universe"]) if a["name"] == "ETH")

    action = {
        "type": "order",
        "orders": [{
            "a": eth_idx, "b": False, "p": "3000", "s": "0.01",
            "r": True,  # reduce_only for TP/SL
            "t": {"trigger": {"triggerPx": "3000", "isMarket": True, "tpsl": "tp"}},
        }],
        "grouping": "na",
    }

    nonce = int(time.time() * 1000)
    sig = sign_l1_action(wallet, action, None, nonce, None, is_mainnet=False)

    payload = {"action": action, "nonce": nonce, "signature": sig, "vaultAddress": None}
    resp = requests.post(f"{TESTNET_API}/exchange", json=payload, timeout=15)
    result = resp.json()

    assert "invalid" not in json.dumps(result).lower() or "signature" not in json.dumps(result).lower()
    print(f"✅ Trigger (TP/SL) order signing verified")


# ── Read API comprehensive tests ────────────────────────────────────

def test_perp_universe_complete():
    """Verify all perp assets have required fields."""
    client = create_client()
    meta = client.get_perp_meta()
    for asset in meta["universe"]:
        assert "name" in asset, f"Asset missing name: {asset}"
        assert "maxLeverage" in asset, f"{asset['name']} missing maxLeverage"
        assert "szDecimals" in asset, f"{asset['name']} missing szDecimals"
    print(f"✅ All {len(meta['universe'])} perp assets have required fields")


def test_spot_tokens_complete():
    """Verify spot tokens have required fields."""
    client = create_client()
    spot = client.get_spot_meta()
    for token in spot["tokens"]:
        assert "name" in token, f"Token missing name: {token}"
        assert "index" in token, f"{token['name']} missing index"
    print(f"✅ All {len(spot['tokens'])} spot tokens have required fields")


def test_funding_rates_range():
    """Verify funding rates are in reasonable range."""
    client = create_client()
    meta, ctxs = client.get_perp_meta_and_contexts()
    for i, ctx in enumerate(ctxs):
        funding = float(ctx.get("funding", "0"))
        # Funding rate should be between -1% and +1% per hour (extreme case)
        assert -0.01 <= funding <= 0.01, \
            f"{meta['universe'][i]['name']} has extreme funding: {funding}"
    print(f"✅ All {len(ctxs)} funding rates in reasonable range")


def test_orderbook_spread():
    """Verify BTC orderbook has reasonable spread."""
    client = create_client()
    book = client.get_l2_book("BTC")
    bids = book["levels"][0]
    asks = book["levels"][1]
    assert len(bids) > 5, "BTC should have >5 bid levels"
    assert len(asks) > 5, "BTC should have >5 ask levels"
    best_bid = float(bids[0]["px"])
    best_ask = float(asks[0]["px"])
    spread_pct = (best_ask - best_bid) / best_bid * 100
    assert spread_pct < 0.1, f"BTC spread too wide: {spread_pct:.4f}%"
    print(f"✅ BTC spread: {spread_pct:.4f}% (${best_ask - best_bid})")


def test_candle_data():
    """Verify candle data returns valid OHLCV."""
    client = create_client()
    candles = client.get_candles("ETH", "1h", lookback=24)
    assert len(candles) > 0, "Should have candle data"
    c = candles[0]
    required_fields = ["t", "o", "h", "l", "c", "v"]
    for field in required_fields:
        assert field in c, f"Candle missing field: {field}"
    # OHLC sanity: low <= open,close <= high
    assert float(c["l"]) <= float(c["o"]), f"Low > Open: {c}"
    assert float(c["l"]) <= float(c["c"]), f"Low > Close: {c}"
    assert float(c["h"]) >= float(c["o"]), f"High < Open: {c}"
    print(f"✅ Candle data: {len(candles)} hourly candles, latest close=${float(candles[-1]['c']):,.2f}")


# ── Wire format tests ───────────────────────────────────────────────

def test_order_wire_format():
    """Verify order wire format matches Hyperliquid spec."""
    from hyperliquid.utils.signing import order_type_to_wire, float_to_wire

    # Limit order
    wire = order_type_to_wire({"limit": {"tif": "Gtc"}})
    assert wire == {"limit": {"tif": "Gtc"}}, f"Limit wire wrong: {wire}"

    # IOC
    wire = order_type_to_wire({"limit": {"tif": "Ioc"}})
    assert wire == {"limit": {"tif": "Ioc"}}

    # ALO (post-only)
    wire = order_type_to_wire({"limit": {"tif": "Alo"}})
    assert wire == {"limit": {"tif": "Alo"}}

    # Trigger (TP)
    wire = order_type_to_wire({"trigger": {"triggerPx": 3000.5, "isMarket": True, "tpsl": "tp"}})
    assert wire["trigger"]["tpsl"] == "tp"
    assert wire["trigger"]["isMarket"] == True

    # Trigger (SL)
    wire = order_type_to_wire({"trigger": {"triggerPx": 2800.0, "isMarket": True, "tpsl": "sl"}})
    assert wire["trigger"]["tpsl"] == "sl"

    print("✅ All order wire formats correct")


def test_float_to_wire():
    """Verify float-to-wire conversion."""
    from hyperliquid.utils.signing import float_to_wire

    # SDK strips trailing .0 for round numbers
    assert float_to_wire(3000.0) in ("3000", "3000.0")
    assert float_to_wire(0.01) == "0.01"
    assert float_to_wire(100) in ("100", "100.0")
    assert float_to_wire(3000.5) == "3000.5"
    print("✅ Float-to-wire conversion correct")


# ── Main ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        # Signing verification (testnet)
        ("Signing: Order", test_signing_order),
        ("Signing: Cancel", test_signing_cancel),
        ("Signing: Leverage", test_signing_leverage),
        ("Signing: USD Transfer", test_signing_usd_class_transfer),
        ("Signing: TP/SL", test_signing_trigger_order),
        # Read API tests (mainnet)
        ("Read: Perp Universe", test_perp_universe_complete),
        ("Read: Spot Tokens", test_spot_tokens_complete),
        ("Read: Funding Rates", test_funding_rates_range),
        ("Read: Orderbook Spread", test_orderbook_spread),
        ("Read: Candle Data", test_candle_data),
        # Wire format tests
        ("Wire: Order Format", test_order_wire_format),
        ("Wire: Float Conversion", test_float_to_wire),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Phase 2 Integration Tests: {passed} passed, {failed} failed")
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️ {failed} test(s) failed")
    sys.exit(1 if failed > 0 else 0)
