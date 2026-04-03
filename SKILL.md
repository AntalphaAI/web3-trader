# web3-trader v1.2 — Smart Swap

> DEX swap + Smart Swap (Dutch auction) trading skill for AI agents. Zero custody, zero gas on Smart Swap orders.

## Features

### ⚡ Instant Swap (Market Order)
- Best-price DEX swap via 0x aggregator
- 50 supported tokens on Ethereum mainnet
- EIP-681 QR code for mobile wallet signing
- Multi-wallet support: MetaMask, OKX Web3, Trust, TokenPocket

### 🧠 Smart Swap (Dutch Auction)
- **What it is**: A price-guaranteed swap powered by 1inch Fusion
- **How it works**: Your order is auctioned from a high price downward; the first resolver (professional market maker) to accept fills the trade
- **User sets a floor price**: The trade will never execute below your minimum acceptable price (`auctionEnd`)
- **Zero gas**: Resolvers pay the gas, not the user
- **Auto-expire**: If no resolver fills within the auction window (3–10 min), the order expires — no funds lost
- **Not a limit order**: This is NOT a CEX-style limit order that sits on an orderbook indefinitely. It's a time-boxed Dutch auction.

### Product Positioning
| Feature | Instant Swap | Smart Swap |
|---------|-------------|------------|
| Price | Market price | ≥ Floor price (may get better) |
| Speed | Instant | 3–10 minutes |
| Gas | User pays | Resolver pays (zero gas) |
| Cancel | N/A | Auto-expires |
| Use case | "Swap now at market" | "Swap now, but guarantee me ≥ X" |

## MCP Tools

| Tool | Description |
|------|-------------|
| `swap-quote` | Get indicative swap price (no commitment) |
| `swap-full` | Get firm quote with full transaction data |
| `swap-tokens` | List supported tokens |
| `swap-gas` | Get current gas price |
| `smart-swap-create` | Create a Smart Swap order (Fusion Dutch auction) |
| `smart-swap-list` | List Smart Swap orders for a wallet |
| `smart-swap-status` | Check order status by hash |
| `smart-swap-cancel` | Check cancellation status / options |

## Supported Tokens (50)

ETH, WETH, USDT, USDC, DAI, WBTC, STETH, WSTETH, UNI, LINK, AAVE, MKR, LDO, ARB, OP, MATIC, SHIB, PEPE, APE, DYDX, SNX, CRV, COMP, BAL, 1INCH, ENS, RPL, CBETH, RETH, SFRXETH, FRXETH, LUSD, GHO, PYUSD, TUSD, PAXG, FXS, RNDR, GRT, FET, OCEAN, IMX, SAND, MANA, AXS, GALA, MASK, SSV, PENDLE, EIGEN

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ZEROEX_API_KEY` | Yes | 0x API key for swap quotes |
| `ONEINCH_API_KEY` | Yes | 1inch API key for Smart Swap (Fusion) |
| `WEB3_TRADER_DEFAULT_CHAIN_ID` | No | Default chain (1 = Ethereum) |
| `WEB3_TRADER_DEFAULT_SLIPPAGE_BPS` | No | Default slippage in basis points |
| `SWAP_HOST_BASE_URL` | No | Public base URL for hosted signing pages |
| `WEB3_TRADER_HTML_OUTPUT_DIR` | No | Directory for generated HTML pages |
| `WEB3_TRADER_PUBLIC_BASE_URL` | No | Public URL prefix for signing page links |

## Smart Swap — How It Works (Dutch Auction)

```
Traditional Limit Order:  You set price → Order sits on book → Someone fills → Cancel anytime
Smart Swap (Fusion):      System starts high → Price drops → First resolver fills → Auto-expires
```

1. User requests a Smart Swap with a floor price
2. 1inch Fusion creates an auction starting above market price
3. Price decreases over 3–10 minutes toward the floor price
4. A resolver (market maker) fills the order when profitable
5. User receives ≥ floor price — often better due to auction competition
6. If unfilled by expiry, order auto-cancels — no funds lost, no gas spent

## Architecture

```
Agent ──MCP──▶ smart-swap-create ──▶ 1inch Fusion Quoter
                    │                      │
                    ▼                      ▼
              Signing Page (HTML)    EIP-712 Typed Data
                    │
                    ▼
              User signs in wallet
                    │
                    ▼
              1inch Fusion Relayer ──▶ Resolver network ──▶ On-chain settlement
```

## Signing Page

- Self-contained HTML, zero external dependencies
- Cyberpunk UI theme
- 4 wallet support: MetaMask, OKX, Trust, TokenPocket
- Auto-detect DApp browser or show deeplinks
- Steps: Connect → Approve (if needed) → Sign → Submit
- USDT-compatible: handles approve(0) before approve(max)

## Version History

- **v1.2** (2026-04-03): Smart Swap (Fusion Dutch auction), 50 tokens, USDT approve fix, QR in tool response
- **v1.1**: Limit order prototype (1inch Fusion + Orderbook)
- **v1.0**: Market swap via 0x aggregator
