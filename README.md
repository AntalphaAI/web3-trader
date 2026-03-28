# 🔄 Web3 Trader Skill v1.0.3

> **AI-Native DEX Trading Tool | Zero Custody | Multi-Wallet | Cyberpunk UI**
>
> Powered by Antalpha AI DEX Aggregator

---

## Features

- 💱 Real-time DEX quotes and optimal routing via Antalpha AI Aggregator
- 🌐 Cyberpunk-style swap pages (Matrix rain animation + scanline effects)
- 📱 4 major wallets: MetaMask, OKX Web3, Trust Wallet, TokenPocket
- ⚡ Auto-execute in wallet dApp browser (2s countdown → direct signature popup)
- 📷 QR code generation with cyberpunk theme (cyan dots on dark background)
- 🔒 Zero custody — private keys never leave the user's wallet
- 🤖 MCP remote mode — one `swap-full` call does quote + page hosting

## Architecture

```
┌──────────────┐    MCP JSON-RPC    ┌──────────────────────────────┐
│  AI Agent    │ ──────────────────► │  Antalpha MCP Server          │
│  (OpenClaw)  │  swap-full          │  mcp-skills.ai.antalpha.com   │
│              │ ◄────────────────── │                                │
│              │  quote + preview_url │  ├─ 0x API ── DEX Aggregation │
└──────┬───────┘                     │  ├─ Page Gen ── Cyberpunk HTML │
       │                             │  └─ Hosting ── URL + QR        │
       │  send preview_url + QR      └────────────────────────────────┘
       ▼
┌──────────────┐   click/scan    ┌────────────────────┐
│  User        │ ──────────────► │  Hosted Swap Page   │
│  (mobile/PC) │                 │  (Cyberpunk UI)     │
└──────────────┘                 └────────┬───────────┘
                                          │ eth_sendTransaction
                                          ▼
                                 ┌────────────────────┐
                                 │  Wallet App         │
                                 │  Sign & Broadcast   │
                                 └────────────────────┘
```

## Quick Start

### MCP Remote Mode (Recommended)

No local setup needed. The AI agent calls the Antalpha MCP Server directly:

```
MCP Server: https://mcp-skills.ai.antalpha.com/mcp
```

Available MCP Tools:

| Tool | Description |
|------|-------------|
| `swap-full` | **One-shot**: quote + generate page + host → returns URL + QR |
| `swap-quote` | Get DEX aggregated quote |
| `swap-create-page` | Generate and host a cyberpunk swap page |
| `swap-tokens` | List supported tokens |
| `swap-gas` | Current gas price |

### Local CLI Mode (Fallback)

```bash
# Install dependencies
pip install requests web3 qrcode pillow

# Configure API key
cp references/config.example.yaml ~/.web3-trader/config.yaml

# Query price
python3 scripts/trader_cli.py price --from ETH --to USDT --amount 0.1

# Generate swap page
python3 scripts/trader_cli.py swap-page --from ETH --to USDT --amount 0.1 \
  --wallet 0xYourAddress -o swap.html --json
```

## Supported Tokens (Ethereum Mainnet)

| Category | Tokens |
|----------|--------|
| Stablecoins | USDT, USDC, DAI |
| Native/Wrapped | ETH, WETH, WBTC |
| DeFi | LINK, UNI |

## Supported Wallets

| Wallet | Deeplink Protocol | Status |
|--------|-------------------|--------|
| 🦊 MetaMask | `metamask.app.link/dapp/` | ✅ Verified |
| 💎 OKX Web3 | `okx://wallet/dapp/details` | ✅ Verified |
| 🛡️ Trust Wallet | `link.trustwallet.com/open_url` | ✅ Verified |
| 📱 TokenPocket | `tpdapp://open` | ✅ Verified |

## Project Structure

```
├── SKILL.md                 # Full skill spec (read by AI agent)
├── MCP_REQUIREMENTS.md      # MCP server requirements doc
├── DEPLOYMENT.md            # Server deployment guide
├── README.md                # This file
├── requirements.txt         # Python dependencies
├── scripts/
│   ├── trader_cli.py        # CLI entry point
│   ├── zeroex_client.py     # Antalpha AI API client
│   └── swap_page_gen.py     # Cyberpunk swap page generator
├── references/
│   ├── config.example.yaml  # Config template
│   ├── SECURITY.md          # Security documentation
│   └── ANTALPHA_MCP_SERVER_SPEC.md
├── examples/
│   └── swap_usdt_eth.py     # Example script
└── tests/
    └── test_zeroex_client.py
```

## Security

| Layer | Protection |
|-------|-----------|
| Private Keys | **Zero contact** — skill never holds, transmits, or stores any private key |
| Transaction Data | Generated by 0x Protocol with MEV protection (anti-sandwich) |
| Slippage | Configurable max slippage (default 0.5%), `minBuyAmount` enforced on-chain |
| Review | User sees full transaction details in wallet before signing |
| Swap Pages | Self-contained HTML, no backend communication, no cookies, no tracking |

## Changelog

### v1.0.3 (2026-03-28)
- Fix: `metadata` changed from multi-line YAML to single-line JSON (OpenClaw parser requirement)
- Fix: remove `ZEROEX_API_KEY` from `requires.env` (MCP mode doesn't need it; was causing load-time gating)
- Enhance: `description` now covers swap/兑换/卖出/买入/sell/buy/DEX trigger keywords for better intent matching

### v1.0.2 (2026-03-27)
- Agent behavior: no verbose output, only swap preview + QR code image
- QR code generated from MCP `preview_url` and sent as image attachment
- Updated message template with routing info

### v1.0.1 (2026-03-27)
- Antalpha MCP Server integration (`mcp-skills.ai.antalpha.com/mcp`)
- `swap-full` one-shot: quote + page generation + server hosting
- Swap pages hosted on trusted Antalpha domain
- Agent no longer needs local 0x API key

### v1.0.0 (2026-03-27)
- Cyberpunk swap pages (Matrix rain + scanline effects)
- 4 wallet support: MetaMask, OKX Web3, Trust Wallet, TokenPocket
- Auto-execute in wallet dApp browser (2s countdown)
- QR code generation (cyan on dark theme)
- Full CLI toolchain (price/route/build-tx/export/swap-page/gas/tokens)

## License

MIT

---

*Powered by Antalpha AI*
