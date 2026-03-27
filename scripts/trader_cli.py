#!/usr/bin/env python3
"""
Web3 Trader CLI - DEX Trading for AI Agents

Usage:
    python3 trader_cli.py price --from USDT --to ETH --amount 1000
    python3 trader_cli.py route --from USDT --to ETH --amount 1000
    python3 trader_cli.py build-tx --from USDT --to ETH --amount 1000 --wallet 0x...
    python3 trader_cli.py export --from USDT --to ETH --amount 1000 --wallet 0x...
    python3 trader_cli.py gas
    python3 trader_cli.py tokens
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zeroex_client import create_client, TOKENS


def cmd_price(args):
    """Query token price"""
    client = create_client()
    result = client.get_price(
        from_token=args.from_token,
        to_token=args.to_token,
        amount=args.amount,
    )
    
    if args.json:
        out = {k: v for k, v in result.items() if k != "raw"}
        print(json.dumps(out, indent=2, default=str))
    else:
        print(f"\n💱 Price Quote")
        print(f"   {result['from_amount']:,.2f} {result['from_token']} → {result['to_amount']:,.6f} {result['to_token']}")
        print(f"   Price: 1 {result['from_token']} = {result['price']:,.8f} {result['to_token']}")
        print(f"   Min Buy: {result['min_buy_amount']:,.6f} {result['to_token']}")
        print(f"   Gas: ~{result['gas']:,} ({float(result['gas_price_wei'])/1e9:.2f} Gwei)")
        print(f"   Liquidity: {'✅ Available' if result['liquidity_available'] else '❌ Unavailable'}")
        
        route = result.get("route", {})
        fills = route.get("fills", [])
        if fills:
            print(f"\n   Route:")
            for fill in fills:
                bps = int(fill.get("proportionBps", 0))
                print(f"     • {fill.get('source', 'Unknown')}: {bps/100:.1f}%")
        print()


def cmd_route(args):
    """Get optimal swap route"""
    client = create_client()
    result = client.get_price(
        from_token=args.from_token,
        to_token=args.to_token,
        amount=args.amount,
    )
    
    if args.json:
        out = {k: v for k, v in result.items() if k != "raw"}
        print(json.dumps(out, indent=2, default=str))
    else:
        print(f"\n🛣️  Optimal Route")
        print(f"   {result['from_amount']:,.2f} {result['from_token']} → {result['to_amount']:,.6f} {result['to_token']}")
        print(f"   Price: 1 {result['from_token']} = {result['price']:,.8f} {result['to_token']}")
        print(f"   Min Buy: {result['min_buy_amount']:,.6f} {result['to_token']}")
        print(f"   Gas: ~{result['gas']:,} ({float(result['gas_price_wei'])/1e9:.2f} Gwei)")
        
        route = result.get("route", {})
        fills = route.get("fills", [])
        tokens = route.get("tokens", [])
        
        if fills:
            print(f"\n   Route Sources:")
            for fill in fills:
                bps = int(fill.get("proportionBps", 0))
                print(f"     • {fill.get('source', 'Unknown')}: {bps/100:.1f}%")
        
        if tokens:
            print(f"\n   Tokens in Route:")
            for t in tokens:
                print(f"     • {t.get('symbol', 'Unknown')} ({t.get('address', '')[:10]}...)")
        
        fees = result.get("fees", {})
        zex_fee = fees.get("zeroExFee", {})
        if zex_fee:
            fee_amount = int(zex_fee.get("amount", 0))
            print(f"\n   0x Fee: {fee_amount} ({zex_fee.get('type', '')})")
        print()


def cmd_build_tx(args):
    """Build transaction data"""
    client = create_client()
    result = client.get_quote(
        from_token=args.from_token,
        to_token=args.to_token,
        amount=args.amount,
        taker=args.wallet,
    )
    
    tx = result["tx"]
    
    if args.json:
        out = {k: v for k, v in result.items() if k != "raw"}
        print(json.dumps(out, indent=2, default=str))
    else:
        print(f"\n📦 Transaction Data")
        print(f"   ⚠️  Review and sign with your wallet\n")
        print(f"   Swap: {result['from_amount']:,.2f} {result['from_token']} → {result['to_amount']:,.6f} {result['to_token']}")
        print(f"   Min Buy: {result['min_buy_amount']:,.6f} {result['to_token']}")
        print(f"   Price: 1 {result['from_token']} = {result['price']:,.8f} {result['to_token']}")
        print(f"\n   To: {tx['to']}")
        print(f"   Value: {tx['value']} wei")
        print(f"   Gas: {tx['gas']:,}")
        print(f"   Gas Price: {float(tx['gasPrice'])/1e9:.2f} Gwei")
        print(f"   Data: {tx['data'][:66]}...")
        print()


def cmd_export(args):
    """Export EIP-681 payment link"""
    client = create_client()
    result = client.get_quote(
        from_token=args.from_token,
        to_token=args.to_token,
        amount=args.amount,
        taker=args.wallet,
    )
    
    tx = result["tx"]
    to_address = tx["to"]
    
    # Build EIP-681 URL with chain_id (EIP-681 spec: ethereum:<address>@<chainId>?...)
    chain_id = getattr(args, 'chain_id', 1) or 1  # Default: Ethereum mainnet
    eip681_url = f"ethereum:{to_address}@{chain_id}"
    query_parts = []
    if tx.get("value") and tx["value"] != "0":
        query_parts.append(f"value={tx['value']}")
    if tx.get("gas"):
        query_parts.append(f"gasLimit={tx['gas']}")
    if tx.get("data"):
        query_parts.append(f"data={tx['data']}")
    if query_parts:
        eip681_url += "?" + "&".join(query_parts)
    
    # Also build a compact URL (without data) for QR code scanning
    # MetaMask mobile QR scanner has trouble with very long data fields
    compact_parts = []
    if tx.get("value") and tx["value"] != "0":
        compact_parts.append(f"value={tx['value']}")
    if tx.get("gas"):
        compact_parts.append(f"gasLimit={tx['gas']}")
    compact_url = f"ethereum:{to_address}@{chain_id}"
    if compact_parts:
        compact_url += "?" + "&".join(compact_parts)
    
    if args.json:
        quote_data = {k: v for k, v in result.items() if k != "raw"}
        output = {
            "eip681_url": eip681_url,
            "compact_url": compact_url,
            "quote": quote_data,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"\n🔗 EIP-681 Payment Link")
        print(f"   Swap: {result['from_amount']:,.2f} {result['from_token']} → {result['to_amount']:,.6f} {result['to_token']}")
        print(f"\n   Full:    {eip681_url[:100]}...")
        print(f"   Compact: {compact_url}")
        print(f"\n   Full link: paste into MetaMask browser or dApp")
        print(f"   Compact link: for QR code scanning\n")


def cmd_swap_page(args):
    """Generate a swap page HTML + QR code image"""
    client = create_client()
    result = client.get_quote(
        from_token=args.from_token,
        to_token=args.to_token,
        amount=args.amount,
        taker=args.wallet,
    )
    
    tx = result["tx"]
    quote = {
        "from_token": result["from_token"],
        "to_token": result["to_token"],
        "from_amount": result["from_amount"],
        "to_amount": result["to_amount"],
        "min_buy_amount": result["min_buy_amount"],
        "price": result["price"],
    }
    
    from swap_page_gen import generate_swap_page
    
    # Generate HTML with optional hosted URL for embedded QR
    hosted_url = getattr(args, "url", None)
    html = generate_swap_page(tx, quote, hosted_url=hosted_url)
    
    # Determine output path
    out_path = args.output or os.path.join(os.getcwd(), "swap_page.html")
    with open(out_path, "w") as f:
        f.write(html)
    
    # Generate standalone QR code image if hosted URL is provided
    qr_path = None
    if hosted_url:
        try:
            import qrcode
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=3,
            )
            qr.add_data(hosted_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#00ffaa", back_color="#0a0e14")
            qr_path = out_path.replace(".html", "_qr.png")
            img.save(qr_path)
        except ImportError:
            pass
    
    if args.json:
        output = {
            "html_path": out_path,
            "html_size": len(html),
            "quote": quote,
            "tx_to": tx["to"],
            "tx_value": tx["value"],
            "tx_gas": tx["gas"],
            "wallets_supported": ["MetaMask", "OKX Web3", "Trust Wallet", "TokenPocket"],
        }
        if hosted_url:
            output["hosted_url"] = hosted_url
        if qr_path:
            output["qr_image_path"] = qr_path
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"\n⚡ Swap Page Generated (Cyberpunk UI)")
        print(f"   File: {out_path}")
        print(f"   Size: {len(html):,} bytes")
        print(f"   Swap: {result['from_amount']:,.4f} {result['from_token']} → {result['to_amount']:,.4f} {result['to_token']}")
        print(f"   Price: 1 {result['from_token']} ≈ ${result['price']:,.2f}")
        print(f"   Wallets: MetaMask, OKX Web3, Trust Wallet, TokenPocket")
        if qr_path:
            print(f"   QR Code: {qr_path}")
        if hosted_url:
            print(f"   URL: {hosted_url}")
        print(f"\n   To use:")
        print(f"   1. Host this file on a public URL (or use cloudflared tunnel)")
        print(f"   2. Scan the QR code with any supported wallet")
        print(f"   3. Confirm the swap in your wallet")
        print()


def cmd_gas(args):
    """Get gas prices"""
    client = create_client()
    gas_info = client.get_gas_info()
    
    if args.json:
        print(json.dumps(gas_info, indent=2, default=str))
    else:
        print(f"\n⛽ Gas Prices (Ethereum)")
        print(f"   Gas Price: {gas_info['gas_price_gwei']:.2f} Gwei")
        print(f"   Estimated Gas: {gas_info['estimated_gas']:,}")
        est_cost_eth = gas_info['gas_price_wei'] * gas_info['estimated_gas'] / 1e18
        print(f"   Est. Cost: {est_cost_eth:.6f} ETH")
        print()


def cmd_tokens(args):
    """List supported tokens"""
    if args.json:
        print(json.dumps(TOKENS, indent=2))
    else:
        print(f"\n🪙 Supported Tokens (Ethereum)")
        for symbol, address in sorted(TOKENS.items()):
            print(f"   {symbol:8} {address}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Web3 Trader - DEX Trading for AI Agents",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Price
    p = subparsers.add_parser("price", help="Query token price")
    p.add_argument("--from", dest="from_token", required=True)
    p.add_argument("--to", dest="to_token", required=True)
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--json", action="store_true")
    
    # Route
    p = subparsers.add_parser("route", help="Get optimal route")
    p.add_argument("--from", dest="from_token", required=True)
    p.add_argument("--to", dest="to_token", required=True)
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--json", action="store_true")
    
    # Build-tx
    p = subparsers.add_parser("build-tx", help="Build transaction")
    p.add_argument("--from", dest="from_token", required=True)
    p.add_argument("--to", dest="to_token", required=True)
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--wallet", required=True)
    p.add_argument("--json", action="store_true")
    
    # Export
    p = subparsers.add_parser("export", help="Export EIP-681 link")
    p.add_argument("--from", dest="from_token", required=True)
    p.add_argument("--to", dest="to_token", required=True)
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--wallet", required=True)
    p.add_argument("--json", action="store_true")
    
    # Swap Page
    p = subparsers.add_parser("swap-page", help="Generate swap page HTML")
    p.add_argument("--from", dest="from_token", required=True)
    p.add_argument("--to", dest="to_token", required=True)
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--wallet", required=True)
    p.add_argument("--output", "-o", help="Output HTML file path")
    p.add_argument("--url", help="Hosted URL (embeds QR code in page + generates QR image)")
    p.add_argument("--json", action="store_true")
    
    # Gas
    p = subparsers.add_parser("gas", help="Get gas prices")
    p.add_argument("--json", action="store_true")
    
    # Tokens
    p = subparsers.add_parser("tokens", help="List tokens")
    p.add_argument("--json", action="store_true")
    
    args = parser.parse_args()
    
    cmds = {
        "price": cmd_price,
        "route": cmd_route,
        "build-tx": cmd_build_tx,
        "export": cmd_export,
        "swap-page": cmd_swap_page,
        "gas": cmd_gas,
        "tokens": cmd_tokens,
    }
    
    if args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
