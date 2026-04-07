#!/usr/bin/env python3
"""
Hyperliquid CLI - CLOB Trading Commands for AI Agents

Supports Agent Wallet mode (recommended) and direct key mode.

Environment variables:
    HL_PRIVATE_KEY      — Agent key or direct private key
    HL_ACCOUNT_ADDRESS  — Owner address (enables agent mode)

Usage:
    # Read-only (no key needed)
    python3 hl_cli.py price ETH
    python3 hl_cli.py prices
    python3 hl_cli.py book ETH
    python3 hl_cli.py account 0x...
    python3 hl_cli.py orders 0x...
    python3 hl_cli.py positions 0x...
    python3 hl_cli.py fills 0x...
    python3 hl_cli.py meta
    python3 hl_cli.py funding

    # Trading (requires key)
    python3 hl_cli.py limit-order ETH buy 3000 0.1
    python3 hl_cli.py market-order ETH buy 0.1
    python3 hl_cli.py close ETH
    python3 hl_cli.py cancel ETH 12345
    python3 hl_cli.py leverage ETH 10
    python3 hl_cli.py tp-sl ETH tp sell 3200 0.1
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_client import create_client
from hl_risk import (
    load_config as load_risk_config,
    assess_trade,
    check_balance_sufficient,
    check_fill_after_failure,
    format_risk_assessment,
    format_risk_preview,
    format_recovery_result,
    cmd_risk_config,
)


def cmd_price(args):
    """Get price for a single coin."""
    client = create_client(testnet=args.testnet)
    price = client.get_price(args.coin)
    if price is None:
        print(f"❌ Unknown coin: {args.coin}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        print(json.dumps({"coin": args.coin, "price": price}))
    else:
        print(f"💰 {args.coin}: ${price:,.2f}")


def cmd_prices(args):
    """Get prices for top coins."""
    client = create_client(testnet=args.testnet)
    mids = client.get_all_mids()
    top_coins = ["BTC", "ETH", "SOL", "DOGE", "HYPE", "ARB", "OP", "AVAX", "MATIC", "LINK"]
    results = {}
    for coin in top_coins:
        if coin in mids:
            results[coin] = float(mids[coin])
    if args.json:
        print(json.dumps(results))
    else:
        print("💰 Top Prices:")
        for coin, px in results.items():
            print(f"   {coin:>6}: ${px:>12,.2f}")


def cmd_book(args):
    """Get order book for a coin."""
    client = create_client(testnet=args.testnet)
    book = client.get_l2_book(args.coin)
    bids = book["levels"][0][:args.depth]
    asks = book["levels"][1][:args.depth]
    if args.json:
        print(json.dumps({"coin": args.coin, "bids": bids, "asks": asks}))
    else:
        print(f"\n📖 {args.coin} Order Book (top {args.depth}):")
        print(f"{'BIDS':>30}  |  {'ASKS':<30}")
        print(f"{'Price':>15} {'Size':>13}  |  {'Price':<15} {'Size':<13}")
        print("-" * 62)
        for i in range(min(len(bids), len(asks))):
            b = bids[i] if i < len(bids) else {"px": "", "sz": ""}
            a = asks[i] if i < len(asks) else {"px": "", "sz": ""}
            print(f"  {b['px']:>13} {b['sz']:>13}  |  {a['px']:<13} {a['sz']:<13}")


def cmd_account(args):
    """Get account summary."""
    client = create_client(testnet=args.testnet)
    address = args.address or _resolve_address(args)
    if args.json:
        summary = client.get_account_summary(address)
        print(json.dumps(summary, indent=2))
    else:
        print(client.format_account_summary(address))


def cmd_orders(args):
    """Get open orders."""
    client = create_client(testnet=args.testnet)
    address = args.address or _resolve_address(args)
    orders = client.get_open_orders(address)
    if args.json:
        print(json.dumps(orders, indent=2))
    else:
        if not orders:
            print("📋 No open orders")
            return
        print(f"📋 Open Orders ({len(orders)}):")
        for o in orders:
            side = "🟢 BUY" if o.get("side") == "B" else "🔴 SELL"
            print(f"   {o.get('coin')} {side} | Price: {o.get('limitPx')} | "
                  f"Size: {o.get('sz')} | OID: {o.get('oid')}")


def cmd_positions(args):
    """Get open positions."""
    client = create_client(testnet=args.testnet)
    address = args.address or _resolve_address(args)
    state = client.get_user_state(address)
    positions = [
        p["position"] for p in state.get("assetPositions", [])
        if float(p["position"].get("szi", "0")) != 0
    ]
    if args.json:
        print(json.dumps(positions, indent=2))
    else:
        if not positions:
            print("📈 No open positions")
            return
        print(f"📈 Open Positions ({len(positions)}):")
        for p in positions:
            direction = "🟢 LONG" if float(p["szi"]) > 0 else "🔴 SHORT"
            pnl = float(p.get("unrealizedPnl", 0))
            pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
            print(f"   {p['coin']} {direction}")
            print(f"      Size: {p['szi']} | Entry: ${float(p.get('entryPx', 0)):,.2f} | PnL: {pnl_str}")
            if p.get("liquidationPx"):
                print(f"      ⚠️ Liq: ${float(p['liquidationPx']):,.2f} | "
                      f"Leverage: {p.get('leverage', {}).get('value', '?')}x")


def cmd_fills(args):
    """Get recent trade fills."""
    client = create_client(testnet=args.testnet)
    address = args.address or _resolve_address(args)
    fills = client.get_user_fills(address)
    if args.json:
        print(json.dumps(fills[:args.limit], indent=2))
    else:
        if not fills:
            print("📋 No recent fills")
            return
        print(f"📋 Recent Fills (last {min(len(fills), args.limit)}):")
        for f in fills[:args.limit]:
            side = "🟢 BUY" if f.get("side") == "B" else "🔴 SELL"
            ts = f.get("time", 0)
            time_str = ""
            if ts:
                import datetime
                time_str = datetime.datetime.fromtimestamp(ts / 1000).strftime("%m-%d %H:%M")
            print(f"   {time_str} {f.get('coin')} {side} | "
                  f"Px: {f.get('px')} | Sz: {f.get('sz')} | Fee: {f.get('fee', '?')}")


def cmd_limit_order(args):
    """Place a limit order with risk control."""
    client = _create_trading_client(args)
    is_buy = args.side.lower() in ("buy", "b", "long")

    # Risk assessment
    ra = assess_trade(size=args.size, price=args.price)
    if not args.skip_risk and ra.requires_confirmation > 0:
        preview = format_risk_preview(
            "Limit Order", args.coin,
            "BUY" if is_buy else "SELL",
            args.size, args.price, ra,
        )
        print(preview, file=sys.stderr)
        if not args.confirm:
            print(json.dumps({
                "status": "confirmation_required",
                "risk_level": ra.level.value,
                "confirms_needed": ra.requires_confirmation,
                "estimated_usd": ra.estimated_usd,
                "reasons": ra.reasons,
            }))
            return
    elif not args.skip_risk:
        print(format_risk_assessment(ra), file=sys.stderr)

    # Balance pre-check
    if not args.skip_balance_check:
        sufficient, msg = check_balance_sufficient(
            client, args.coin, args.size, args.price,
        )
        if not sufficient:
            print(msg, file=sys.stderr)
            if args.json:
                print(json.dumps({"status": "insufficient_balance", "message": msg}))
            sys.exit(1)

    # Execute
    try:
        result = client.place_limit_order(
            coin=args.coin,
            is_buy=is_buy,
            price=args.price,
            size=args.size,
            tif=args.tif,
            reduce_only=args.reduce_only,
        )
    except Exception as e:
        # Failure recovery: check if it actually filled
        was_filled, fill_info = check_fill_after_failure(
            client, args.coin, args.size, is_buy,
        )
        print(format_recovery_result(was_filled, fill_info), file=sys.stderr)
        if was_filled:
            if args.json:
                print(json.dumps({"status": "filled_despite_error", "fill": fill_info}))
            return
        raise

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_order_result(result, "Limit", "BUY" if is_buy else "SELL", args.coin, args.size, args.price)


def cmd_market_order(args):
    """Place a market order with risk control."""
    client = _create_trading_client(args)
    is_buy = args.side.lower() in ("buy", "b", "long")

    # Get current price for risk assessment
    price = client.get_price(args.coin) or 0

    # Risk assessment
    ra = assess_trade(size=args.size, price=price)
    if not args.skip_risk and ra.requires_confirmation > 0:
        preview = format_risk_preview(
            "Market Order", args.coin,
            "BUY" if is_buy else "SELL",
            args.size, price, ra,
        )
        print(preview, file=sys.stderr)
        if not args.confirm:
            print(json.dumps({
                "status": "confirmation_required",
                "risk_level": ra.level.value,
                "confirms_needed": ra.requires_confirmation,
                "estimated_usd": ra.estimated_usd,
                "reasons": ra.reasons,
            }))
            return
    elif not args.skip_risk:
        print(format_risk_assessment(ra), file=sys.stderr)

    # Balance pre-check
    if not args.skip_balance_check:
        sufficient, msg = check_balance_sufficient(
            client, args.coin, args.size, price,
        )
        if not sufficient:
            print(msg, file=sys.stderr)
            if args.json:
                print(json.dumps({"status": "insufficient_balance", "message": msg}))
            sys.exit(1)

    # Execute
    try:
        result = client.place_market_order(
            coin=args.coin,
            is_buy=is_buy,
            size=args.size,
            slippage=args.slippage,
        )
    except Exception as e:
        was_filled, fill_info = check_fill_after_failure(
            client, args.coin, args.size, is_buy,
        )
        print(format_recovery_result(was_filled, fill_info), file=sys.stderr)
        if was_filled:
            if args.json:
                print(json.dumps({"status": "filled_despite_error", "fill": fill_info}))
            return
        raise

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        side_str = "BUY" if is_buy else "SELL"
        status = result.get("response", {}).get("data", {}).get("statuses", [{}])[0]
        if "filled" in status:
            fill = status["filled"]
            print(f"✅ Market {side_str} {args.size} {args.coin} — Filled @ ${float(fill.get('avgPx', 0)):,.2f}")
        elif "error" in status:
            print(f"❌ {status['error']}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"📋 {json.dumps(result)}")


def cmd_close(args):
    """Close an existing position at market price."""
    client = _create_trading_client(args)
    result = client.close_position(coin=args.coin, slippage=args.slippage)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = result.get("response", {}).get("data", {}).get("statuses", [{}])[0]
        if "filled" in status:
            fill = status["filled"]
            print(f"✅ Closed {args.coin} position — {fill.get('totalSz')} @ ${float(fill.get('avgPx', 0)):,.2f}")
        elif "error" in status:
            print(f"❌ {status['error']}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"📋 {json.dumps(result)}")


def cmd_modify_order(args):
    """Modify an existing order (change price and/or size)."""
    client = _create_trading_client(args)
    is_buy = args.side.lower() in ("buy", "b", "long")

    # Risk assessment on the new values
    ra = assess_trade(size=args.size, price=args.price)
    if not args.skip_risk and ra.requires_confirmation > 0:
        preview = format_risk_preview(
            "Modify Order", args.coin,
            "BUY" if is_buy else "SELL",
            args.size, args.price, ra,
            extra={"OID": str(args.oid)},
        )
        print(preview, file=sys.stderr)
        if not args.confirm:
            print(json.dumps({
                "status": "confirmation_required",
                "risk_level": ra.level.value,
                "confirms_needed": ra.requires_confirmation,
                "estimated_usd": ra.estimated_usd,
            }))
            return
    elif not args.skip_risk:
        print(format_risk_assessment(ra), file=sys.stderr)

    result = client.modify_order(
        coin=args.coin,
        oid=args.oid,
        is_buy=is_buy,
        price=args.price,
        size=args.size,
        tif=args.tif,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        side_str = "BUY" if is_buy else "SELL"
        print(f"✅ Modified {args.coin} OID:{args.oid} → {side_str} {args.size} @ ${args.price:,.2f}")


def cmd_cancel(args):
    """Cancel an order."""
    client = _create_trading_client(args)
    result = client.cancel_order(args.coin, args.oid)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = result.get("response", {}).get("data", {}).get("statuses", [""])[0]
        if status == "success":
            print(f"✅ Cancelled {args.coin} OID: {args.oid}")
        else:
            print(f"📋 {json.dumps(result)}")


def cmd_leverage(args):
    """Set leverage for a coin."""
    client = _create_trading_client(args)
    result = client.update_leverage(
        coin=args.coin,
        leverage=args.leverage,
        is_cross=not args.isolated,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        mode = "isolated" if args.isolated else "cross"
        print(f"✅ {args.coin} leverage set to {args.leverage}x ({mode})")


def cmd_tp_sl(args):
    """Place a take-profit or stop-loss order with risk control."""
    client = _create_trading_client(args)
    is_buy = args.side.lower() in ("buy", "b", "long")

    # TP/SL are risk-reducing, assess at trigger price
    ra = assess_trade(size=args.size, price=args.trigger_price, is_close=True)
    if not args.skip_risk:
        print(format_risk_assessment(ra), file=sys.stderr)

    result = client.place_trigger_order(
        coin=args.coin,
        is_buy=is_buy,
        size=args.size,
        trigger_px=args.trigger_price,
        tpsl=args.type,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        type_str = "Take-Profit" if args.type == "tp" else "Stop-Loss"
        side_str = "BUY" if is_buy else "SELL"
        print(f"✅ {type_str} {side_str} {args.size} {args.coin} @ trigger ${args.trigger_price:,.2f}")


def cmd_meta(args):
    """Show available perp assets."""
    client = create_client(testnet=args.testnet)
    meta = client.get_perp_meta()
    universe = meta["universe"]
    if args.json:
        print(json.dumps(universe, indent=2))
    else:
        print(f"📊 Perpetual Assets ({len(universe)}):")
        print(f"{'Coin':>8} {'MaxLev':>7} {'SzDecimals':>11}")
        print("-" * 28)
        for asset in universe[:30]:
            print(f"{asset['name']:>8} {asset.get('maxLeverage', '?'):>7}x {asset.get('szDecimals', '?'):>11}")
        if len(universe) > 30:
            print(f"   ... and {len(universe) - 30} more")


def cmd_funding(args):
    """Show funding rates for top assets."""
    client = create_client(testnet=args.testnet)
    meta, ctxs = client.get_perp_meta_and_contexts()
    universe = meta["universe"]

    results = []
    for i, ctx in enumerate(ctxs):
        if i >= len(universe):
            break
        funding = float(ctx.get("funding", "0"))
        oi = float(ctx.get("openInterest", "0"))
        mark = float(ctx.get("markPx", "0"))
        results.append({
            "coin": universe[i]["name"],
            "funding_1h": funding,
            "funding_8h": funding * 8,
            "funding_annual": funding * 8 * 365,
            "open_interest": oi,
            "mark_price": mark,
        })

    results.sort(key=lambda x: abs(x["funding_annual"]), reverse=True)

    if args.json:
        print(json.dumps(results[:20], indent=2))
    else:
        print(f"📊 Funding Rates (top 20 by magnitude):")
        print(f"{'Coin':>8} {'1h Rate':>10} {'Annual':>10} {'OI ($)':>15} {'Mark':>12}")
        print("-" * 58)
        for r in results[:20]:
            annual_pct = r["funding_annual"] * 100
            oi_usd = r["open_interest"] * r["mark_price"]
            print(
                f"{r['coin']:>8} {r['funding_1h']*100:>9.4f}% "
                f"{annual_pct:>9.1f}% "
                f"${oi_usd:>13,.0f} "
                f"${r['mark_price']:>10,.2f}"
            )


# ── Helpers ──────────────────────────────────────────────────────────

def _resolve_address(args) -> str:
    """Resolve account address from env or args."""
    addr = os.environ.get("HL_ACCOUNT_ADDRESS")
    if addr:
        return addr
    key = getattr(args, "key", None) or os.environ.get("HL_PRIVATE_KEY")
    if key:
        from eth_account import Account
        return Account.from_key(key).address
    print("❌ No address provided. Use positional arg or set HL_ACCOUNT_ADDRESS", file=sys.stderr)
    sys.exit(1)


def _create_trading_client(args):
    """Create a client for write operations."""
    key = getattr(args, "key", None)
    owner = getattr(args, "owner", None)
    return create_client(
        testnet=args.testnet,
        private_key=key,
        account_address=owner,
    )


def _print_order_result(result, order_type, side, coin, size, price):
    """Print formatted order result."""
    status = result.get("response", {}).get("data", {}).get("statuses", [{}])[0]
    if "resting" in status:
        oid = status["resting"]["oid"]
        print(f"✅ {order_type} {side} {size} {coin} @ ${price:,.2f} — OID: {oid}")
    elif "filled" in status:
        fill = status["filled"]
        print(f"✅ {order_type} {side} {size} {coin} — Filled @ ${float(fill.get('avgPx', 0)):,.2f}")
    elif "error" in status:
        print(f"❌ {status['error']}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"📋 {json.dumps(result)}")


# ── Main ─────────────────────────────────────────────────────────────

def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--testnet", action="store_true", help="Use testnet")
    common.add_argument("--json", action="store_true", help="JSON output")
    common.add_argument("--key", help="Private key (agent or direct). Default: HL_PRIVATE_KEY env")
    common.add_argument("--owner", help="Owner address for agent mode. Default: HL_ACCOUNT_ADDRESS env")
    common.add_argument("--confirm", action="store_true", help="Skip risk confirmation prompt (pre-confirmed)")
    common.add_argument("--skip-risk", action="store_true", dest="skip_risk", help="Bypass risk control entirely")
    common.add_argument("--skip-balance-check", action="store_true", dest="skip_balance_check", help="Skip balance pre-check")

    parser = argparse.ArgumentParser(
        description="Hyperliquid CLI - CLOB Trading for AI Agents",
        parents=[common],
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Read-only commands ---

    p = subparsers.add_parser("price", parents=[common], help="Get price for a coin")
    p.add_argument("coin", help="Coin name (e.g. ETH, BTC)")

    subparsers.add_parser("prices", parents=[common], help="Get top coin prices")

    p = subparsers.add_parser("book", parents=[common], help="Get order book")
    p.add_argument("coin")
    p.add_argument("--depth", type=int, default=10)

    p = subparsers.add_parser("account", parents=[common], help="Get account summary")
    p.add_argument("address", nargs="?", help="Address (default: from env)")

    p = subparsers.add_parser("orders", parents=[common], help="Get open orders")
    p.add_argument("address", nargs="?")

    p = subparsers.add_parser("positions", parents=[common], help="Get open positions")
    p.add_argument("address", nargs="?")

    p = subparsers.add_parser("fills", parents=[common], help="Get recent fills")
    p.add_argument("address", nargs="?")
    p.add_argument("--limit", type=int, default=20)

    subparsers.add_parser("meta", parents=[common], help="Show available perp assets")
    subparsers.add_parser("funding", parents=[common], help="Show funding rates")

    # --- Trading commands ---

    p = subparsers.add_parser("limit-order", parents=[common], help="Place a limit order")
    p.add_argument("coin")
    p.add_argument("side", choices=["buy", "sell", "b", "s", "long", "short"])
    p.add_argument("price", type=float)
    p.add_argument("size", type=float)
    p.add_argument("--tif", default="Gtc", choices=["Gtc", "Ioc", "Alo"])
    p.add_argument("--reduce-only", action="store_true")

    p = subparsers.add_parser("market-order", parents=[common], help="Place a market order")
    p.add_argument("coin")
    p.add_argument("side", choices=["buy", "sell", "b", "s", "long", "short"])
    p.add_argument("size", type=float)
    p.add_argument("--slippage", type=float, default=0.01)

    p = subparsers.add_parser("close", parents=[common], help="Close a position at market")
    p.add_argument("coin")
    p.add_argument("--slippage", type=float, default=0.01)

    p = subparsers.add_parser("modify-order", parents=[common], help="Modify an existing order")
    p.add_argument("coin")
    p.add_argument("oid", type=int, help="Order ID to modify")
    p.add_argument("side", choices=["buy", "sell", "b", "s", "long", "short"])
    p.add_argument("price", type=float, help="New price")
    p.add_argument("size", type=float, help="New size")
    p.add_argument("--tif", default="Gtc", choices=["Gtc", "Ioc", "Alo"])

    p = subparsers.add_parser("cancel", parents=[common], help="Cancel an order")
    p.add_argument("coin")
    p.add_argument("oid", type=int)

    p = subparsers.add_parser("leverage", parents=[common], help="Set leverage")
    p.add_argument("coin")
    p.add_argument("leverage", type=int)
    p.add_argument("--isolated", action="store_true")

    p = subparsers.add_parser("tp-sl", parents=[common], help="Place take-profit / stop-loss")
    p.add_argument("coin")
    p.add_argument("type", choices=["tp", "sl"])
    p.add_argument("side", choices=["buy", "sell"])
    p.add_argument("trigger_price", type=float)
    p.add_argument("size", type=float)

    # --- Risk Config ---
    p = subparsers.add_parser("risk-config", parents=[common], help="View/edit risk control thresholds")
    p.add_argument("--show", action="store_true", help="Show current config (default when no other flags)")
    p.add_argument("--reset", action="store_true", help="Reset to defaults")
    p.add_argument("--small", type=float, metavar="USD", help="Set small-trade threshold (auto-execute below this)")
    p.add_argument("--medium", type=float, metavar="USD", help="Set medium-trade threshold (double-confirm above this)")
    p.add_argument("--leverage", type=int, metavar="X", help="Set high-leverage threshold (double-confirm at or above)")
    p.add_argument("--enable", type=lambda x: x.lower() in ("true", "1", "yes"), metavar="BOOL",
                   help="Enable/disable risk control")
    p.add_argument("--auto-small", type=lambda x: x.lower() in ("true", "1", "yes"), metavar="BOOL",
                   dest="auto_small", help="Auto-execute small trades")

    args = parser.parse_args()

    cmd_map = {
        "price": cmd_price,
        "prices": cmd_prices,
        "book": cmd_book,
        "account": cmd_account,
        "orders": cmd_orders,
        "positions": cmd_positions,
        "fills": cmd_fills,
        "limit-order": cmd_limit_order,
        "market-order": cmd_market_order,
        "modify-order": cmd_modify_order,
        "close": cmd_close,
        "cancel": cmd_cancel,
        "leverage": cmd_leverage,
        "tp-sl": cmd_tp_sl,
        "meta": cmd_meta,
        "funding": cmd_funding,
        "risk-config": cmd_risk_config,
    }

    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
