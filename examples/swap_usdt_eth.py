#!/usr/bin/env python3
"""
Example: Query price and build a USDT → ETH swap transaction

Usage:
    python3 examples/swap_usdt_eth.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from zeroex_client import create_client

def main():
    # Create client from config
    client = create_client()
    
    # Query price
    print("💱 Querying price for 1000 USDT → ETH...\n")
    price = client.get_price("USDT", "ETH", 1000)
    
    print(f"   From: {price['from_amount']:,.2f} {price['from_token']}")
    print(f"   To:   {price['to_amount']:,.6f} {price['to_token']}")
    print(f"   Price: 1 {price['from_token']} = {price['price']:,.6f} {price['to_token']}")
    print(f"   Impact: {price['estimated_price_impact']*100:.3f}%")
    print(f"   Gas: ~{price['estimated_gas']:,}\n")
    
    # Get full quote with transaction data
    print("🛣️  Getting optimal route...\n")
    quote = client.get_quote(
        "USDT", "ETH", 1000,
        taker="0x0000000000000000000000000000000000000001"  # Replace with your wallet
    )
    
    print(f"   Guaranteed Price: {quote['guaranteed_price']}")
    print(f"   Route Sources:")
    for source in quote.get("sources", []):
        proportion = float(source.get("proportion", 0)) * 100
        if proportion > 0:
            print(f"     • {source.get('name', 'Unknown')}: {proportion:.1f}%")
    print()
    
    # Transaction data
    tx = quote["tx"]
    print("📦 Transaction Data (for review):")
    print(f"   To: {tx['to']}")
    print(f"   Data: {tx['data'][:64]}...")
    print(f"   Gas: {tx['gas']:,}")
    print()
    print("   ⚠️  Review above and sign with your wallet!")
    print()

if __name__ == "__main__":
    main()
